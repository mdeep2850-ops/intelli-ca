from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any
from app.models.document import ProcessingStatus

class DocumentResponse(BaseModel):
    id: int
    user_id: int | None = None
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    processing_status: ProcessingStatus

    model_config = ConfigDict(from_attributes=True)

class DocumentElementCreate(BaseModel):
    element_type: str
    content: str
    metadata_: dict[str, Any]

class DocumentElementResponse(BaseModel):
    id: int
    document_id: int
    element_type: str
    content: str
    metadata_: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
