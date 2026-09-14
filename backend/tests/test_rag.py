import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.rag import RAGResponse

client = TestClient(app)

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.rag.llm_service.generate_response", new_callable=AsyncMock)
def test_rag_query_success(mock_generate, mock_search):
    # Mock retrieval to return valid context
    mock_search.return_value = [
        {
            "content": "Taxation rules for 2024 include a new 15% bracket.",
            "metadata": {"document_id": "doc_123", "filename": "tax_rules.pdf"},
            "distance": 0.2
        }
    ]
    
    # Mock LLM to return an answer
    mock_generate.return_value = "According to the context, there is a new 15% bracket."
    
    resp = client.post("/api/v1/rag/query", json={"query": "What are the new tax rules?", "limit": 3})
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["answer"] == "According to the context, there is a new 15% bracket."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["document_id"] == "doc_123"
    assert data["citations"][0]["relevance_score"] == 0.2
    assert "Taxation rules" in data["citations"][0]["content_snippet"]

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.rag.llm_service.generate_response", new_callable=AsyncMock)
def test_rag_insufficient_context(mock_generate, mock_search):
    # Mock retrieval to return empty context
    mock_search.return_value = []
    
    resp = client.post("/api/v1/rag/query", json={"query": "What are the new tax rules?"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "do not have enough information" in data["answer"].lower()
    assert len(data["citations"]) == 0
    mock_generate.assert_not_called()

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.rag.llm_service.generate_response", new_callable=AsyncMock)
def test_rag_low_relevance_fallback(mock_generate, mock_search):
    # Mock retrieval to return context with distance > threshold (e.g. 1.5)
    mock_search.return_value = [
        {
            "content": "Completely unrelated information about cats.",
            "metadata": {"document_id": "doc_123"},
            "distance": 1.5
        }
    ]
    
    resp = client.post("/api/v1/rag/query", json={"query": "What are the new tax rules?"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "do not have enough information" in data["answer"].lower()
    assert len(data["citations"]) == 0
    mock_generate.assert_not_called()

@patch("app.services.rag.retrieval_service.search_client_documents")
@patch("app.services.rag.llm_service.generate_response", new_callable=AsyncMock)
def test_rag_llm_fallback(mock_generate, mock_search):
    # Mock retrieval returns valid context
    mock_search.return_value = [
        {
            "content": "Taxation rules for 2024 include a new 15% bracket.",
            "metadata": {"document_id": "doc_123"},
            "distance": 0.2
        }
    ]
    
    # Mock LLM strictly following prompt and returning fallback string
    mock_generate.return_value = "Insufficient information"
    
    resp = client.post("/api/v1/rag/query", json={"query": "Tell me about space exploration."})
    assert resp.status_code == 200
    
    data = resp.json()
    assert "do not have enough information" in data["answer"].lower()
    assert len(data["citations"]) == 0
