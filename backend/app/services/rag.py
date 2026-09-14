import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.retrieval import retrieval_service
from app.services.llm import llm_service
from app.schemas.rag import RAGQuery, RAGResponse, Citation

logger = logging.getLogger(__name__)

# Configurable threshold for ChromaDB L2 distance. Lower is better.
MAX_DISTANCE_THRESHOLD = 1.0 

class RAGService:
    def retrieve_context(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> tuple[str, List[Citation], bool]:
        # 1. Retrieve Context
        results = retrieval_service.search_client_documents(
            query=query, 
            limit=limit, 
            filters=filters
        )
        
        # 2. Filter by relevance
        valid_results = []
        for res in results:
            dist = res.get("distance", 0.0)
            if dist <= MAX_DISTANCE_THRESHOLD:
                valid_results.append(res)
                
        # 3. Handle Insufficient Context
        if not valid_results:
            return "", [], False
            
        # 4. Construct Context Text
        context_parts = []
        citations = []
        
        for idx, res in enumerate(valid_results):
            content = res.get("content", "")
            meta = res.get("metadata", {})
            dist = res.get("distance")
            
            doc_id = meta.get("document_id", "Unknown")
            chunk_id = meta.get("chunk_id")
            filename = meta.get("filename", "Unknown Document")
            
            context_parts.append(f"--- Document [{idx+1}] (ID: {doc_id}, File: {filename}) ---\n{content}\n")
            
            citations.append(Citation(
                document_id=doc_id,
                chunk_id=chunk_id,
                filename=filename,
                relevance_score=dist,
                content_snippet=content[:100] + "..." if len(content) > 100 else content
            ))
            
        context_text = "\n".join(context_parts)
        return context_text, citations, True

    async def query(self, request: RAGQuery) -> RAGResponse:
        context_text, citations, is_sufficient = self.retrieve_context(
            query=request.query, limit=request.limit, filters=request.filters
        )
        
        if not is_sufficient:
            logger.info("RAG Service: No relevant context found.")
            return RAGResponse(
                answer="I do not have enough information in the uploaded documents to answer that.",
                citations=[]
            )
        
        system_instruction = (
            "You are an AI assistant for CA/CMA professionals. "
            "Answer the user's query ONLY using the provided context documents below. "
            "If the answer cannot be found in the provided context, you MUST reply exactly with: 'Insufficient information'. "
            "Do not use outside knowledge."
        )
        
        user_prompt = f"Context Documents:\n{context_text}\n\nUser Query: {request.query}"
        
        # 5. Call LLM
        try:
            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content=user_prompt)
            ]
            llm_answer = await llm_service.generate_response(messages)
            
            # Check if LLM triggered fallback
            if "insufficient information" in llm_answer.lower().strip():
                return RAGResponse(
                    answer="I do not have enough information in the uploaded documents to answer that.",
                    citations=[]
                )
                
            return RAGResponse(
                answer=llm_answer,
                citations=citations
            )
            
        except Exception as e:
            logger.error(f"LLM failure during RAG: {e}")
            raise RuntimeError("Error occurred while generating RAG response.")

rag_service = RAGService()
