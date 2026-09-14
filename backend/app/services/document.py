import os
import uuid
import shutil
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document, ProcessingStatus
from app.core.logger import logger

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def _generate_safe_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1]
    # Use uuid to prevent path traversal and collision
    return f"{uuid.uuid4().hex}{ext}"

def save_document(db: Session, file: UploadFile, file_size: int, user_id: int | None = None) -> Document:
    safe_filename = _generate_safe_filename(file.filename or "unknown.bin")
    storage_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    try:
        # Save file to disk
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Create DB record
        db_doc = Document(
            user_id=user_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            processing_status=ProcessingStatus.UPLOADED,
            storage_path=storage_path
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        logger.info(f"Document {db_doc.id} saved successfully at {storage_path}")
        return db_doc
    except Exception as e:
        logger.error(f"Failed to save document: {str(e)}")
        # Clean up file if db save fails
        if os.path.exists(storage_path):
            os.remove(storage_path)
        raise e

def get_document(db: Session, document_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100) -> list[Document]:
    return db.query(Document).offset(skip).limit(limit).all()

def delete_document(db: Session, document_id: int) -> bool:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return False
        
    try:
        from app.models.document import Chunk
        from app.services.vector_store import vector_store
        
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
        if chunks:
            chunk_ids = [c.chunk_id for c in chunks]
            vector_store.delete_chunks("client_documents", where={"chunk_id": {"$in": chunk_ids}})
            
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
            
        db.delete(doc)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        db.rollback()
        raise e
