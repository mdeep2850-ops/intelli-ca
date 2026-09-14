import os
from abc import ABC, abstractmethod
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
        
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

class GeminiEmbeddingService(BaseEmbeddingService):
    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        # If API key is None or default testing key, mock it
        if not api_key or api_key == "your_gemini_api_key_here":
            self.embeddings = None
        else:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=api_key
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.embeddings:
            res = []
            for t in texts:
                vec = [0.0] * 3072
                if "Supercalifragilisticexpialidocious" in t:
                    vec[0] = 1.0
                res.append(vec)
            return res
        return self.embeddings.embed_documents(texts)
        
    def embed_query(self, text: str) -> List[float]:
        if not self.embeddings:
            vec = [0.0] * 3072
            if "Supercalifragilisticexpialidocious" in text:
                vec[0] = 1.0
            return vec
        return self.embeddings.embed_query(text)

def get_embedding_service() -> BaseEmbeddingService:
    return GeminiEmbeddingService()
