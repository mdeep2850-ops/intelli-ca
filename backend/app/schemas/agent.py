from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from app.schemas.rag import Citation

class AgentQuery(BaseModel):
    query: str
    limit: int = 5
    filters: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    used_tools: List[str] = []
    intent: str

class IntentOutput(BaseModel):
    next_action: Literal["rag", "calculate", "finish", "error"] = Field(description="The next action to take.")
    tool_name: Optional[str] = Field(default=None, description="The name of the tool to execute if next_action is 'calculate'.")
    tool_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters extracted for the tool. For RAG, you can provide a 'search_query' here to query a specific topic.")

class ValidatorOutput(BaseModel):
    is_valid: bool = Field(description="Whether the response is fully grounded and valid.")
    reason: str = Field(description="Reason for validation failure or success.")
