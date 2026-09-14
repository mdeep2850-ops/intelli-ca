from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session as DBSession
from fastapi.concurrency import run_in_threadpool
from app.core.database import get_db
from app.core.config import settings
from app.schemas.document import DocumentResponse
from app.services.document import save_document, get_document, get_documents
from app.services.extraction.processor import process_document
from app.models.document import Document
from app.core.logger import logger

router = APIRouter()

ALLOWED_TYPES = [
    "application/pdf", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]

ALLOWED_EXTENSIONS = [".pdf", ".docx", ".xlsx"]

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    # Validate extension
    filename = file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Invalid file extension. Only PDF, DOCX, and XLSX are allowed.")

    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type. Only PDF, DOCX, and XLSX are allowed.")
    
    # Read file size securely
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes.")
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        # Use threadpool for disk I/O and sync DB
        document = await run_in_threadpool(save_document, db, file, file_size)
        return document
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process file upload.")

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(skip: int = 0, limit: int = 100, db: DBSession = Depends(get_db)):
    docs = await run_in_threadpool(get_documents, db, skip, limit)
    return docs

from typing import Dict, Any
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    filters: Dict[str, Any] | None = None

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: float

@router.post("/search", response_model=list[SearchResult])
async def search_documents_endpoint(request: SearchRequest):
    from app.services.retrieval import retrieval_service
    
    try:
        results = await run_in_threadpool(
            retrieval_service.search_client_documents, 
            request.query, 
            request.limit, 
            request.filters
        )
        out = []
        for r in results:
            out.append(SearchResult(
                content=r["content"],
                metadata=r["metadata"],
                distance=r["distance"]
            ))
        return out
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed.")

@router.get("/{document_id}", response_model=DocumentResponse)
async def retrieve_document(document_id: int, db: DBSession = Depends(get_db)):
    doc = await run_in_threadpool(get_document, db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}")
async def delete_document_endpoint(document_id: int, db: DBSession = Depends(get_db)):
    from app.services.document import delete_document
    success = await run_in_threadpool(delete_document, db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@router.post("/{document_id}/process")
async def process_document_endpoint(document_id: int, db: DBSession = Depends(get_db)):
    # We must ensure the document exists first to avoid vague 500s
    doc = await run_in_threadpool(get_document, db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    success = await run_in_threadpool(process_document, db, document_id)
    if not success:
        # Check if doc exists again in case it was deleted
        doc_after = await run_in_threadpool(get_document, db, document_id)
        if not doc_after:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(status_code=500, detail="Document processing failed.")
        
    return {"message": "Document processed successfully", "document_id": document_id}
