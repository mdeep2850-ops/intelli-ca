import chromadb
from typing import List, Dict, Any
from app.core.config import settings
import os

class VectorStore:
    def __init__(self):
        db_path = os.path.join(settings.DATA_DIR, "chroma")
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        
        self.client_collection = self.client.get_or_create_collection(
            name="client_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, collection_name: str, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]):
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, collection_name: str, query_embedding: List[float], n_results: int = 5, where: Dict[str, Any] = None):
        collection = self.client.get_or_create_collection(name=collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results

    def delete_chunks(self, collection_name: str, where: Dict[str, Any]):
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.delete(where=where)

    def get_embeddings_by_ids(self, collection_name: str, ids: List[str]) -> Dict[str, List[float]]:
        collection = self.client.get_or_create_collection(name=collection_name)
        results = collection.get(ids=ids, include=["embeddings"])
        out = {}
        if results and results.get("embeddings") is not None:
            for i, doc_id in enumerate(results["ids"]):
                out[doc_id] = results["embeddings"][i]
        return out

vector_store = VectorStore()
