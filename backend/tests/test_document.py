import io
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_upload_pdf():
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "application/pdf"
    assert data["processing_status"] == "uploaded"
    assert "id" in data

def test_upload_docx():
    file_content = b"PK\x03\x04 dummy docx content"
    files = {"file": ("test.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.docx"

def test_upload_xlsx():
    file_content = b"PK\x03\x04 dummy xlsx content"
    files = {"file": ("test.xlsx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.xlsx"

def test_upload_unsupported_extension():
    file_content = b"print('hello')"
    files = {"file": ("test.py", io.BytesIO(file_content), "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]

def test_upload_unsupported_content_type():
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid content type" in response.json()["detail"]

def test_upload_oversized_file():
    original_size = settings.MAX_UPLOAD_SIZE
    settings.MAX_UPLOAD_SIZE = 10
    try:
        file_content = b"this is more than 10 bytes"
        files = {"file": ("large.pdf", io.BytesIO(file_content), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE = original_size

def test_list_documents():
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 3

def test_get_document():
    # Get the list first to find an ID
    list_response = client.get("/api/v1/documents/")
    doc_id = list_response.json()[0]["id"]
    
    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id
