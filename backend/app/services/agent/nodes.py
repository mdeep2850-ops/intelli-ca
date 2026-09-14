import logging
import hashlib
import json
from typing import Dict, Any, TypedDict, List
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.llm import llm_service
from app.services.rag import rag_service
from app.schemas.rag import Citation
from app.schemas.agent import IntentOutput, ValidatorOutput
from app.services.agent.tools import TOOL_REGISTRY
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    limit: int
    filters: dict | None
    
    # Orchestration & Safety
    route_history: List[str]
    step_count: int
    next_action: str
    tool_name: str | None
    extracted_parameters: dict
    state_hashes: List[str]
    
    # Accumulated Data
    retrieved_context: str
    citations: List[Citation]
    tool_outputs: List[Dict[str, Any]]
    
    # Outputs
    final_response: str
    errors: List[str]
    is_valid: bool

def _compute_state_hash(action: str, tool_name: str | None, params: dict) -> str:
    # Stable deterministic hash of the semantic action intent
    state_str = f"{action}_{tool_name}_{json.dumps(params, sort_keys=True)}"
    return hashlib.sha256(state_str.encode()).hexdigest()

async def supervisor_node(state: AgentState) -> AgentState:
    logger.info("Running Supervisor...")
    state["step_count"] = state.get("step_count", 0) + 1
    
    # 1. Max Step Check
    if state["step_count"] > settings.MAX_AGENT_STEPS:
        state["next_action"] = "error"
        state["errors"].append(f"Maximum agent steps ({settings.MAX_AGENT_STEPS}) reached.")
        return state

    # 2. Determine Next Action via LLM
    try:
        llm_with_struct = llm_service.llm.with_structured_output(IntentOutput)
        sys_msg = SystemMessage(content=(
            "You are the Supervisor for a CA/CMA assistant. Your job is to orchestrate workers to fulfill the user's query.\n"
            "Review the current context and tool outputs, and decide the next action.\n"
            "Actions available: 'rag' (for document retrieval), 'calculate' (for financial math), 'finish' (if you have enough info to answer or if no further tools will help), 'error' (if you cannot proceed).\n"
            "If requesting 'calculate', extract parameters and specify tool_name.\n"
            "Available financial tools: 'calculate_revenue', 'calculate_expenses', 'calculate_gross_profit', 'calculate_net_profit', 'calculate_net_profit_margin', 'calculate_working_capital', 'calculate_current_ratio', 'calculate_debt_to_equity', 'calculate_tax'.\n"
            "Select ONLY the tools required by the user's request and the financial evidence available. Do not sequentially invoke all tools blindly.\n"
            "If requesting 'rag', you can provide an optional 'search_query' parameter to search specifically.\n"
            "Do NOT request the same tool with the exact same parameters repeatedly. If the retrieved context and calculations are sufficient, choose 'finish'."
        ))
        
        prompt_parts = [f"User Query: {state['query']}"]
        if state.get("retrieved_context"):
            excerpt = state['retrieved_context'][:1500]
            prompt_parts.append(f"Retrieved Context (excerpt):\n{excerpt}")
        if state.get("tool_outputs"):
            import json
            prompt_parts.append(f"Tool Outputs:\n{json.dumps(state['tool_outputs'])}")
            
        user_msg = HumanMessage(content="\n".join(prompt_parts))
        result: IntentOutput = await llm_with_struct.ainvoke([sys_msg, user_msg])
        
        next_action = result.next_action
        tool_name = result.tool_name
        extracted_params = result.tool_parameters
        
    except Exception as e:
        logger.error(f"Supervisor LLM failed: {e}")
        state["next_action"] = "error"
        state["errors"].append(f"Supervisor LLM failed: {str(e)}")
        return state

    # 3. Repeated-State Loop Detection
    current_hash = _compute_state_hash(
        next_action, 
        tool_name,
        extracted_params
    )
    
    if current_hash in state.get("state_hashes", []):
        logger.warning(f"Infinite loop detected for action {next_action}. Forcing finish.")
        state["next_action"] = "finish"
        state["errors"].append("Intercepted repeated state loop. Forcing finish.")
        return state
        
    state["state_hashes"].append(current_hash)
    state["next_action"] = next_action
    state["tool_name"] = tool_name
    state["extracted_parameters"] = extracted_params
    state["route_history"].append(next_action)
    
    return state

def rag_node(state: AgentState) -> AgentState:
    logger.info("Running RAG node...")
    try:
        params = state.get("extracted_parameters", {})
        search_query = params.get("search_query", state["query"])
        
        context_text, citations, is_sufficient = rag_service.retrieve_context(
            query=search_query, limit=state["limit"], filters=state["filters"]
        )
        if not is_sufficient:
            state["errors"].append("RAG returned insufficient information.")
            
        if context_text:
            existing_context = state.get("retrieved_context", "")
            if context_text not in existing_context:
                state["retrieved_context"] = existing_context + "\n" + context_text if existing_context else context_text
                
                existing_cit_keys = {(c.document_id, c.chunk_id) for c in state.get("citations", [])}
                for c in citations:
                    if (c.document_id, c.chunk_id) not in existing_cit_keys:
                        state["citations"].append(c)
                        existing_cit_keys.add((c.document_id, c.chunk_id))
    except Exception as e:
        logger.error(f"RAG node failed: {e}")
        state["errors"].append(f"RAG node failed: {str(e)}")
        
    return state

def tool_executor_node(state: AgentState) -> AgentState:
    logger.info("Running Tool Executor...")
    params = state.get("extracted_parameters", {})
    tool_name = state.get("tool_name")
    
    if tool_name:
        tool = TOOL_REGISTRY.get(tool_name)
        if tool:
            try:
                result = tool.execute(params)
                state["tool_outputs"].append({"tool": tool.name, "status": "success", "result": result, "params": params})
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                err_msg = f"Tool execution failed: {str(e)}"
                state["errors"].append(err_msg)
                state["tool_outputs"].append({"tool": tool.name, "status": "failed", "error": err_msg, "params": params})
        else:
            err_msg = f"Tool '{tool_name}' not found in registry."
            state["errors"].append(err_msg)
            state["tool_outputs"].append({"tool": tool_name, "status": "failed", "error": err_msg, "params": params})
    else:
        err_msg = "Missing required tool_name for tool execution."
        state["errors"].append(err_msg)
        state["tool_outputs"].append({"tool": "unknown", "status": "failed", "error": err_msg, "params": params})
        
    return state

async def synthesizer_node(state: AgentState) -> AgentState:
    logger.info("Running Synthesizer...")
    
    # Graceful degradation if max steps or critical error
    if state["next_action"] == "error" and not state["retrieved_context"] and not state["tool_outputs"]:
        err_msg = state["errors"][-1] if state["errors"] else "Unknown error occurred."
        state["final_response"] = f"I apologize, but I was unable to complete the request. Reason: {err_msg}"
        return state

    system_instruction = (
        "You are a Financial Analyst AI assistant for CA/CMA professionals. "
        "Synthesize a final financial analysis based ONLY on the retrieved context and deterministic tool outputs provided. "
        "Interpret the tool outputs to highlight profitability strength/weakness, liquidity position, and leverage/risk. "
        "Do not invent facts, financial figures, or calculations. "
        "Preserve tool output figures exactly as provided and cite the retrieved document evidence naturally. "
        "If a required financial value is unavailable or a tool failed, explicitly state that the metric could not be calculated. "
        "If you do not have enough information to form an analysis, clearly state that you cannot answer."
    )
    
    prompt_parts = []
    if state.get("retrieved_context"):
        prompt_parts.append(f"Retrieved Context:\n{state['retrieved_context']}")
    if state.get("tool_outputs"):
        prompt_parts.append(f"Tool Outputs:\n{json.dumps(state['tool_outputs'])}")
    if state.get("errors"):
        prompt_parts.append(f"Execution Errors (for context):\n{json.dumps(state['errors'])}")
        
    prompt_parts.append(f"User Query: {state['query']}")
    user_prompt = "\n\n".join(prompt_parts)
    
    try:
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_prompt)
        ]
        llm_answer = await llm_service.generate_response(messages)
        state["final_response"] = llm_answer
    except Exception as e:
        logger.error(f"Synthesizer failed: {e}")
        state["errors"].append(f"Synthesizer failed: {str(e)}")
        state["final_response"] = "An error occurred while generating the final response."
        
    return state

async def validator_node(state: AgentState) -> AgentState:
    logger.info("Running Validator...")
    
    if not state.get("final_response"):
        state["final_response"] = "System error: Response generation yielded an empty result."
        state["errors"].append("Final response was empty.")
        state["is_valid"] = False
        return state
        
    # Programmatic check 1: If RAG was used and context exists, we expect the response to not be entirely empty and to contain some information.
    # A true traceability check requires parsing the output for citation markers if the project uses them.
    if state.get("retrieved_context") and not state.get("citations"):
        state["errors"].append("Programmatic Validator: Context retrieved but citations list is empty.")
        state["is_valid"] = False
        return state
        

    # LLM Semantic Grounding Check
    system_instruction = (
        "You are a strict Validator for a CA/CMA assistant.\n"
        "Your task is to evaluate the provided 'Generated Response' against the 'Retrieved Context' and 'Tool Outputs'.\n"
        "Criteria for validity:\n"
        "1. All factual claims must be supported by the Retrieved Context.\n"
        "2. All numerical claims or calculations must match the Tool Outputs exactly.\n"
        "3. The response must not hallucinate or invent information.\n"
        "4. If the response correctly states it cannot answer due to lack of info, it is valid.\n"
        "If the response violates any of these, set is_valid to false and explain the reason."
    )
    
    prompt_parts = []
    if state.get("retrieved_context"):
        prompt_parts.append(f"Retrieved Context:\n{state['retrieved_context']}")
    if state.get("tool_outputs"):
        prompt_parts.append(f"Tool Outputs:\n{json.dumps(state['tool_outputs'])}")
    prompt_parts.append(f"Generated Response:\n{state['final_response']}")
    
    user_prompt = "\n\n".join(prompt_parts)
    
    try:
        llm_with_struct = llm_service.llm.with_structured_output(ValidatorOutput)
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_prompt)
        ]
        result: ValidatorOutput = await llm_with_struct.ainvoke(messages)
        
        state["is_valid"] = result.is_valid
        if not result.is_valid:
            state["errors"].append(f"Validation failed: {result.reason}")
            # Append validation warning to response
            state["final_response"] += f"\n\n[Warning: {result.reason}]"
    except Exception as e:
        logger.error(f"Validator failed: {e}")
        state["errors"].append(f"Validator failed: {str(e)}")
        # If validator fails, we fail open for now but flag it
        state["is_valid"] = False
        
    return state
