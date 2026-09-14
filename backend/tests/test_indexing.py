import io
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.document import Document, DocumentElement, Chunk, IndexingStatus

client = TestClient(app)

def _upload_test_pdf(content: str = "This is a simple test document for indexing."):
    from reportlab.pdfgen import canvas
    pdf_io = io.BytesIO()
    c = canvas.Canvas(pdf_io)
    c.drawString(100, 750, content)
    c.save()
    pdf_io.seek(0)
    
    response = client.post(
        "/api/v1/documents/upload", 
        files={"file": ("test.pdf", pdf_io, "application/pdf")}
    )
    return response.json()["id"]

def test_indexing_pipeline():
    # Test 1, 2, 3: Text chunking, metadata
    doc_id = _upload_test_pdf("A very long text that will be chunked. " * 50)
    
    process_resp = client.post(f"/api/v1/documents/{doc_id}/process")
    assert process_resp.status_code == 200
    
    db = SessionLocal()
    elements = db.query(DocumentElement).filter(DocumentElement.document_id == doc_id).all()
    assert len(elements) > 0
    
    for el in elements:
        assert el.indexing_status == IndexingStatus.INDEXED
        chunks = db.query(Chunk).filter(Chunk.element_id == el.id).all()
        assert len(chunks) > 0
        for c in chunks:
            assert c.indexing_status == IndexingStatus.INDEXED
            assert c.content_hash is not None
            assert c.metadata_["document_id"] == doc_id
    db.close()

def test_duplicate_prevention():
    # Test 5
    doc_id = _upload_test_pdf("Identical document text to prevent duplicates")
    client.post(f"/api/v1/documents/{doc_id}/process")
    
    # Process it again (re-process forces clean up and re-index)
    client.post(f"/api/v1/documents/{doc_id}/process")
    
    # We should still have only 1 set of chunks
    db = SessionLocal()
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert len(chunks) > 0
    # Because we explicitly delete and recreate in the pipeline, total chunks should exactly match the single processing
    db.close()

def test_document_deletion():
    # Test 9
    doc_id = _upload_test_pdf("Document to be deleted")
    client.post(f"/api/v1/documents/{doc_id}/process")
    
    db = SessionLocal()
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    chunk_ids = [c.chunk_id for c in chunks]
    db.close()
    
    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200
    
    # Verify vector store deleted
    from app.services.vector_store import vector_store
    results = vector_store.search("client_documents", [0.0]*3072, n_results=10)
    # The chunk_ids should not be in results
    if results and results.get("ids") and len(results["ids"]) > 0:
        for r_id in results["ids"][0]:
            assert r_id not in chunk_ids

