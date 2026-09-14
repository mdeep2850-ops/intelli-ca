from langgraph.graph import StateGraph, END
from app.services.agent.nodes import (
    AgentState,
    supervisor_node,
    rag_node,
    tool_executor_node,
    synthesizer_node,
    validator_node
)

def route_from_supervisor(state: AgentState) -> str:
    action = state.get("next_action", "error")
    if action == "rag":
        return "rag_node"
    elif action == "calculate":
        return "tool_executor_node"
    elif action == "finish":
        return "synthesizer_node"
    else: # "error" or anything else
        return "synthesizer_node"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor_node", supervisor_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("tool_executor_node", tool_executor_node)
    workflow.add_node("synthesizer_node", synthesizer_node)
    workflow.add_node("validator_node", validator_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor_node")
    
    # Supervisor conditional routing
    workflow.add_conditional_edges(
        "supervisor_node",
        route_from_supervisor,
        {
            "rag_node": "rag_node",
            "tool_executor_node": "tool_executor_node",
            "synthesizer_node": "synthesizer_node"
        }
    )
    
    # Workers route back to supervisor
    workflow.add_edge("rag_node", "supervisor_node")
    workflow.add_edge("tool_executor_node", "supervisor_node")
    
    # Synthesizer to validator to END
    workflow.add_edge("synthesizer_node", "validator_node")
    workflow.add_edge("validator_node", END)
    
    # Compile
    return workflow.compile()

agent_graph = build_graph()
