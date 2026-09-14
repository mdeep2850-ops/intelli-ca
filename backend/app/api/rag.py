from fastapi import APIRouter, HTTPException
from app.schemas.rag import RAGQuery, RAGResponse
from app.services.rag import rag_service

router = APIRouter()

@router.post("/query", response_model=RAGResponse)
async def query_rag(request: RAGQuery):
    try:
        return await rag_service.query(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
