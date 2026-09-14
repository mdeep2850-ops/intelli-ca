import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.agent import IntentOutput, ValidatorOutput

client = TestClient(app)

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_rag_routing(mock_generate, mock_llm, mock_search):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
        
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_search.return_value = [
        {
            "content": "Taxation rules for 2024.",
            "metadata": {"document_id": "doc_1", "filename": "rules.pdf"},
            "distance": 0.1
        }
    ]
    
    mock_generate.return_value = "Based on rules, taxation applies."
    
    resp = client.post("/api/v1/agent/query", json={"query": "What are the rules?"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "taxation applies" in data["answer"].lower()
    assert len(data["citations"]) == 1
    assert data["citations"][0]["document_id"] == "doc_1"
    assert data["intent"] == "finish"
    assert mock_supervisor_struct.ainvoke.call_count == 2

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_calculate_routing(mock_generate, mock_llm, mock_search):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="calculate", tool_name="calculate_tax", tool_parameters={"income": 100000}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
        
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "The calculated tax is 15000."
    
    resp = client.post("/api/v1/agent/query", json={"query": "Calculate tax for 100000 income"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "calculate_tax" in data["used_tools"]
    assert "15000" in data["answer"]
    mock_search.assert_not_called()

@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_max_steps(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    side_effects = []
    for i in range(10):
        side_effects.append(IntentOutput(next_action="calculate", tool_name="calculate_tax", tool_parameters={"income": 100000 + i}))
    mock_supervisor_struct.ainvoke.side_effect = side_effects
    
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
        
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "Graceful fallback output."
    
    resp = client.post("/api/v1/agent/query", json={"query": "Loop me"})
    assert resp.status_code == 200
    
    data = resp.json()
    # It should hit max steps (5) and set next_action to error
    assert data["intent"] == "error"
    assert "Graceful fallback" in data["answer"] or "Unable to complete" in data["answer"].lower()

@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_repeated_state_loop(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="calculate", tool_name="calculate_tax", tool_parameters={"invalid": True}), # tool_outputs won't grow
        IntentOutput(next_action="calculate", tool_name="calculate_tax", tool_parameters={"invalid": True}), # Same hash!
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={}) # Should not be reached
    ]
    
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
        
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    mock_generate.return_value = "Synthesizer fallback."
    
    resp = client.post("/api/v1/agent/query", json={"query": "Repeat state"})
    assert resp.status_code == 200
    
    data = resp.json()
    # Loop detection forces 'finish'
    assert data["intent"] == "finish"
    assert mock_supervisor_struct.ainvoke.call_count == 2

@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_invalid_calculation(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="calculate", tool_name="calculate_tax", tool_parameters={}), # Missing 'income'
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
        
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "Missing parameters."
    
    resp = client.post("/api/v1/agent/query", json={"query": "Calculate tax without income."})
    assert resp.status_code == 200
    
    data = resp.json()
    # We should have successfully passed through calculate (which appended an error to state)
    # and then synthesized
    assert "Missing parameters" in data["answer"]

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_real_rag_loop(mock_generate, mock_llm, mock_search):
    mock_supervisor_struct = AsyncMock()
    # Provide the same action and parameters twice to simulate a real loop
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={}),
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_search.return_value = [
        {
            "content": "Tax rules.",
            "metadata": {"document_id": "doc_1"},
            "distance": 0.1
        }
    ]
    mock_generate.return_value = "Response"
    
    resp = client.post("/api/v1/agent/query", json={"query": "What rules?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "finish"
    assert mock_supervisor_struct.ainvoke.call_count == 2

@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_tool_registry_unknown_tool(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="calculate", tool_name="non_existent_tool", tool_parameters={}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "Unknown tool fallback"
    
    resp = client.post("/api/v1/agent/query", json={"query": "Use unknown tool"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "finish"

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_duplicate_rag_context(mock_generate, mock_llm, mock_search):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={"search_query": "Q1"}),
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={"search_query": "Q2"}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_search.return_value = [
        {
            "content": "Exact duplicate chunk content.",
            "metadata": {"document_id": "doc_1", "chunk_id": "chunk_1"},
            "distance": 0.1
        }
    ]
    mock_generate.return_value = "Response"
    
    resp = client.post("/api/v1/agent/query", json={"query": "Test duplicate"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert len(data["citations"]) == 1
    assert mock_search.call_count == 2
    
@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_hallucination_validator(mock_generate, mock_llm, mock_search):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="rag", tool_name=None, tool_parameters={}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=False, reason="Hallucinated claim not in context")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_search.return_value = [
        {
            "content": "Depreciation rate is 10%.",
            "metadata": {"document_id": "doc_1"},
            "distance": 0.1
        }
    ]
    mock_generate.return_value = "The depreciation rate is 25%." 
    
    resp = client.post("/api/v1/agent/query", json={"query": "What is the rate?"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "[Warning: Hallucinated claim not in context]" in data["answer"]

def test_invalid_intent_schema():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        IntentOutput(next_action="search", tool_parameters={})

@patch("app.services.agent.nodes.llm_service.llm")
@patch("app.services.agent.nodes.llm_service.generate_response", new_callable=AsyncMock)
def test_agent_missing_tool_name(mock_generate, mock_llm):
    mock_supervisor_struct = AsyncMock()
    mock_supervisor_struct.ainvoke.side_effect = [
        IntentOutput(next_action="calculate", tool_name=None, tool_parameters={}),
        IntentOutput(next_action="finish", tool_name=None, tool_parameters={})
    ]
    mock_validator_struct = AsyncMock()
    mock_validator_struct.ainvoke.return_value = ValidatorOutput(is_valid=True, reason="Valid")
    
    def with_structured_output_mock(schema):
        if schema == IntentOutput:
            return mock_supervisor_struct
        return mock_validator_struct
    mock_llm.with_structured_output.side_effect = with_structured_output_mock
    
    mock_generate.return_value = "Missing tool fallback"
    
    resp = client.post("/api/v1/agent/query", json={"query": "Calculate but forgot tool_name"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["intent"] == "finish"

from app.services.agent.nodes import tool_executor_node, AgentState

def test_agent_financial_tool_integration():
    # Setup the exact state the supervisor would produce
    state = AgentState(
        messages=[],
        query="Calculate net profit margin for 300k profit and 1.8M revenue.",
        extracted_parameters={"net_profit": 300000.0, "revenue": 1800000.0},
        tool_name="calculate_net_profit_margin",
        tool_outputs=[],
        errors=[],
        next_action="calculate",
        state_hashes=[]
    )
    
    # Run the generic executor
    updated_state = tool_executor_node(state)
    
    # Assert there are no execution errors
    assert len(updated_state["errors"]) == 0
    
    # Assert tool_outputs contains the result
    assert len(updated_state["tool_outputs"]) == 1
    output = updated_state["tool_outputs"][0]
    
    # 2. Confirm the test asserts the ACTUAL NUMERICAL RESULT returned by the tool
    # 3. Verify Revenue=1.8M, Profit=300k produces ~16.6667%
    assert output["tool"] == "calculate_net_profit_margin"
    assert output["status"] == "success"
    assert abs(output["result"] - 16.666666666666664) < 1e-9
    
    # 4. Confirm the resulting value is present in the structured state["tool_outputs"]
    assert output["params"]["net_profit"] == 300000.0
    assert output["params"]["revenue"] == 1800000.0
