from fastapi import APIRouter, HTTPException
from app.schemas.agent import AgentQuery, AgentResponse
from app.services.agent.graph import agent_graph

router = APIRouter()

@router.post("/query", response_model=AgentResponse)
async def query_agent(request: AgentQuery):
    try:
        initial_state = {
            "query": request.query,
            "limit": request.limit,
            "filters": request.filters,
            "route_history": [],
            "step_count": 0,
            "next_action": "",
            "tool_name": None,
            "extracted_parameters": {},
            "state_hashes": [],
            "retrieved_context": "",
            "citations": [],
            "tool_outputs": [],
            "final_response": "",
            "errors": [],
            "is_valid": False
        }
        
        # Invoke LangGraph state machine
        final_state = await agent_graph.ainvoke(initial_state)
        
        used_tools = [t["tool"] for t in final_state.get("tool_outputs", [])]
        
        return AgentResponse(
            answer=final_state["final_response"],
            citations=final_state.get("citations", []),
            used_tools=used_tools,
            intent=final_state.get("next_action", "general")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
