import io
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.document import Document, ProcessingStatus, DocumentElement

client = TestClient(app)

def test_processor_flow(tmp_path):
    # Create a dummy docx to upload
    from docx import Document as DocxDoc
    doc = DocxDoc()
    doc.add_paragraph("Test Processor")
    
    docx_io = io.BytesIO()
    doc.save(docx_io)
    docx_io.seek(0)
    
    # 1. Upload
    response = client.post(
        "/api/v1/documents/upload", 
        files={"file": ("test.docx", docx_io, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # 2. Process
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process")
    assert process_resp.status_code == 200
    
    # 3. Verify DB Status
    db = SessionLocal()
    db_doc = db.query(Document).filter(Document.id == doc_id).first()
    assert db_doc.processing_status == ProcessingStatus.PROCESSED
    
    # 4. Verify elements
    elements = db.query(DocumentElement).filter(DocumentElement.document_id == doc_id).all()
    assert len(elements) == 1
    assert elements[0].content == "Test Processor"
    db.close()

def test_process_invalid_id():
    response = client.post("/api/v1/documents/99999/process")
    assert response.status_code == 404

def test_process_missing_file(tmp_path):
    # Upload first
    file_content = b"%PDF-1.4 dummy"
    files = {"file": ("missing.pdf", io.BytesIO(file_content), "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    doc_id = response.json()["id"]
    
    # Delete the physical file to simulate failure
    db = SessionLocal()
    db_doc = db.query(Document).filter(Document.id == doc_id).first()
    import os
    os.remove(db_doc.storage_path)
    db.close()
    
    # Try process
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process")
    assert process_resp.status_code == 500
    
    db = SessionLocal()
    db_doc = db.query(Document).filter(Document.id == doc_id).first()
    assert db_doc.processing_status == ProcessingStatus.FAILED
    db.close()
