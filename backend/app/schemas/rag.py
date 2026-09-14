from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class RAGQuery(BaseModel):
    query: str
    limit: int = 5
    filters: Optional[Dict[str, Any]] = None

class Citation(BaseModel):
    document_id: Union[str, int]
    chunk_id: Optional[str] = None
    filename: Optional[str] = None
    relevance_score: Optional[float] = None
    content_snippet: Optional[str] = None

class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
