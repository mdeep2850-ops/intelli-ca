from pydantic import BaseModel
from typing import List

class MessageCreate(BaseModel):
    content: str
    session_id: int | None = None

class MessageResponse(BaseModel):
    content: str
    role: str
    session_id: int
