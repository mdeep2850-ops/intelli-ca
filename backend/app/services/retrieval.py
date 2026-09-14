from typing import List, Dict, Any
from app.services.embedding import get_embedding_service
from app.services.vector_store import vector_store

class RetrievalService:
    def __init__(self):
        self.embedding_service = get_embedding_service()

    def search_client_documents(self, query: str, limit: int = 5, filters: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        query_emb = self.embedding_service.embed_query(query)
        
        results = vector_store.search(
            collection_name="client_documents",
            query_embedding=query_emb,
            n_results=limit,
            where=filters
        )
        
        out = []
        if results and results.get("documents") and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
            
            for i in range(len(docs)):
                out.append({
                    "content": docs[i],
                    "metadata": metas[i],
                    "distance": dists[i]
                })
                
        return out

retrieval_service = RetrievalService()
