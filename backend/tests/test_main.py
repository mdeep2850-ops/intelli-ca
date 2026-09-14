from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "project": "Intelli-CA"}

@patch("app.api.chat.llm_service.generate_response", new_callable=AsyncMock)
def test_chat_endpoint_no_session(mock_generate):
    mock_generate.return_value = "Mocked LLM response"
    
    response = client.post("/api/v1/chat", json={"content": "Hello!"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Mocked LLM response"
    assert data["role"] == "assistant"
    assert "session_id" in data
    assert isinstance(data["session_id"], int)
    
    # Verify the LLM was called with the right history (just 1 message)
    mock_generate.assert_called_once()
    messages = mock_generate.call_args[0][0]
    assert len(messages) == 1
    assert messages[0].content == "Hello!"
    assert messages[0].type == "human"

@patch("app.api.chat.llm_service.generate_response", new_callable=AsyncMock)
def test_chat_endpoint_with_session_and_history(mock_generate):
    mock_generate.return_value = "First response"
    
    # 1. Create session
    resp1 = client.post("/api/v1/chat", json={"content": "Hi there"})
    session_id = resp1.json()["session_id"]
    
    # 2. Continue session
    mock_generate.return_value = "Second response"
    resp2 = client.post("/api/v1/chat", json={"content": "How are you?", "session_id": session_id})
    assert resp2.json()["content"] == "Second response"
    
    # 3. Verify history was passed to the LLM
    # The last call to mock_generate should have 3 messages: Human, AI, Human
    messages = mock_generate.call_args[0][0]
    assert len(messages) == 3
    assert messages[0].content == "Hi there"
    assert messages[0].type == "human"
    assert messages[1].content == "First response"
    assert messages[1].type == "ai"
    assert messages[2].content == "How are you?"
    assert messages[2].type == "human"

@patch("app.api.chat.llm_service.generate_response", new_callable=AsyncMock)
def test_chat_endpoint_llm_failure(mock_generate):
    mock_generate.side_effect = RuntimeError("LLM is down")
    
    response = client.post("/api/v1/chat", json={"content": "Will this fail?"})
    assert response.status_code == 500
    assert response.json()["detail"] == "LLM is down"
