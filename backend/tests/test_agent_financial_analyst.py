import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.agent import IntentOutput, ValidatorOutput
from app.services.agent.nodes import tool_executor_node, synthesizer_node, AgentState
from app.schemas.rag import Citation

client = TestClient(app)

def test_demo_scenario_deterministic():
    # Mocking the LLM completely to test the exact workflow for the Demo Scenario
    state = AgentState(
        messages=[],
        query="Analyze company",
        extracted_parameters={},
        tool_name=None,
        tool_outputs=[],
        errors=[],
        next_action="calculate",
        state_hashes=[],
        retrieved_context="",
        citations=[],
        final_response="",
        is_valid=True
    )
    
    # 1. Gross Profit
    state["tool_name"] = "calculate_gross_profit"
    state["extracted_parameters"] = {"revenue": 1800000.0, "cogs": 900000.0}
    state = tool_executor_node(state)
    assert state["tool_outputs"][-1]["result"] == 900000.0
    
    # 2. Net Profit 
    state["tool_name"] = "calculate_net_profit"
    state["extracted_parameters"] = {"gross_profit": 900000.0, "operating_expenses": 600000.0}
    state = tool_executor_node(state)
    assert state["tool_outputs"][-1]["result"] == 300000.0
    
    # 3. Net Profit Margin
    state["tool_name"] = "calculate_net_profit_margin"
    state["extracted_parameters"] = {"net_profit": 300000.0, "revenue": 1800000.0}
    state = tool_executor_node(state)
    assert abs(state["tool_outputs"][-1]["result"] - 16.666666666666664) < 1e-9

    # 4. Working Capital
    state["tool_name"] = "calculate_working_capital"
    state["extracted_parameters"] = {"current_assets": 1200000.0, "current_liabilities": 600000.0}
    state = tool_executor_node(state)
    assert state["tool_outputs"][-1]["result"] == 600000.0

    # 5. Current Ratio
    state["tool_name"] = "calculate_current_ratio"
    state["extracted_parameters"] = {"current_assets": 1200000.0, "current_liabilities": 600000.0}
    state = tool_executor_node(state)
    assert state["tool_outputs"][-1]["result"] == 2.0

    # 6. Debt to Equity
    state["tool_name"] = "calculate_debt_to_equity"
    state["extracted_parameters"] = {"total_debt": 900000.0, "shareholders_equity": 1800000.0}
    state = tool_executor_node(state)
    assert state["tool_outputs"][-1]["result"] == 0.5


def test_synthesizer_financial_analyst():
    state = AgentState(
        messages=[],
        query="Analyze company",
        extracted_parameters={},
        tool_name=None,
        tool_outputs=[
            {"tool": "calculate_net_profit_margin", "status": "success", "result": 16.666666666666664, "params": {"net_profit": 300000.0, "revenue": 1800000.0}},
            {"tool": "calculate_current_ratio", "status": "success", "result": 2.0, "params": {"current_assets": 1200000.0, "current_liabilities": 600000.0}}
        ],
        errors=[],
        next_action="finish",
        state_hashes=[],
        retrieved_context="The company's P&L shows revenue of 1.8M and 300k net profit. Balance sheet shows 1.2M current assets and 600k current liabilities.",
        citations=[Citation(document_id="doc_1", chunk_id="chunk_1", content_snippet="P&L shows...", relevance_score=0.9)],
        final_response="",
        is_valid=True
    )
    
    with patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "The company has strong profitability with a Net Profit Margin of 16.67% [doc_1]. Liquidity is healthy with a Current Ratio of 2.0 [doc_1]."
        
        import asyncio
        updated_state = asyncio.run(synthesizer_node(state))
        
        # Verify it used the LLM synthesizer correctly without crashing
        assert "16.67%" in updated_state["final_response"]
        assert "2.0" in updated_state["final_response"]
        assert "doc_1" in updated_state["final_response"]


def test_division_by_zero_safety_integration():
    state = AgentState(
        messages=[],
        query="Calculate margin",
        extracted_parameters={"net_profit": 50000.0, "revenue": 0.0},
        tool_name="calculate_net_profit_margin",
        tool_outputs=[],
        errors=[],
        next_action="calculate",
        state_hashes=[],
        retrieved_context="",
        citations=[],
        final_response="",
        is_valid=True
    )
    
    updated_state = tool_executor_node(state)
    
    assert len(updated_state["errors"]) == 1
    assert "Division by zero" in updated_state["errors"][0]
    assert updated_state["tool_outputs"][0]["status"] == "failed"


@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_mocked_rag_financial_integration(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    # Simulate supervisor deciding to use RAG, then calculate, then finish
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={"search_query": "financial health"}),
        IntentOutput(
            next_action="calculate",
            tool_name="calculate_debt_to_equity",
            tool_parameters={"total_debt": 900000.0, "shareholders_equity": 1800000.0}
        ),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "The debt-to-equity is 0.5, indicating low risk."
    
    with patch("app.services.agent.nodes.rag_service.retrieve_context") as mock_retrieve:
        mock_retrieve.return_value = ("Debt is 900k and equity is 1.8M.", [Citation(document_id="d1", chunk_id="c1", content_snippet="Debt is 900k...", relevance_score=0.9)], True)
        
        resp = client.post("/api/v1/agent/query", json={"query": "What is the leverage risk?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "0.5" in data["answer"] or "low risk" in data["answer"].lower()

from app.services.agent.nodes import supervisor_node

@patch("app.services.agent.nodes.llm_service.llm")
def test_supervisor_receives_tool_outputs_in_prompt(mock_llm):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.return_value = IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    mock_llm.with_structured_output.return_value = mock_supervisor_struct
    
    state = AgentState(
        messages=[],
        query="Calculate net profit",
        extracted_parameters={},
        tool_name=None,
        tool_outputs=[
            {"tool": "calculate_gross_profit", "status": "success", "result": 900000.0, "params": {"revenue": 1800000.0, "cogs": 900000.0}}
        ],
        errors=[],
        next_action="calculate",
        state_hashes=[],
        route_history=[],
        retrieved_context="Here is some context about the company.",
        citations=[],
        final_response="",
        is_valid=True
    )
    
    import asyncio
    asyncio.run(supervisor_node(state))
    
    # Assert the mock was called
    assert mock_supervisor_struct.ainvoke.called
    
    # Inspect the prompt passed to the LLM
    call_args = mock_supervisor_struct.ainvoke.call_args[0][0]
    
    # call_args is a list of Messages. The second one should be the HumanMessage.
    user_msg = call_args[1].content
    
    assert "900000.0" in user_msg
    assert "calculate_gross_profit" in user_msg
    assert "Retrieved Context (excerpt)" in user_msg
    assert "Here is some context" in user_msg

