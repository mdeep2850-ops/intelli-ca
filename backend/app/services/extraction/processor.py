import os
from sqlalchemy.orm import Session
from app.models.document import Document, ProcessingStatus, DocumentElement
from app.services.extraction.factory import get_extractor
from app.core.logger import logger

def process_document(db: Session, document_id: int) -> bool:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"Document {document_id} not found.")
        return False
        
    if doc.processing_status == ProcessingStatus.PROCESSED:
        logger.info(f"Document {document_id} is already processed.")
        return True
        
    if not os.path.exists(doc.storage_path):
        logger.error(f"Storage path {doc.storage_path} for document {document_id} does not exist.")
        doc.processing_status = ProcessingStatus.FAILED
        db.commit()
        return False

    try:
        # 1. Mark as processing
        doc.processing_status = ProcessingStatus.PROCESSING
        # Clear any existing elements if we are re-processing
        db.query(DocumentElement).filter(DocumentElement.document_id == document_id).delete()
        db.commit()
        
        # 2. Extract
        extractor = get_extractor(doc.file_type, doc.filename)
        elements_gen = extractor.extract(doc.storage_path, doc.filename)
        
        # 3. Persist
        for element_data in elements_gen:
            db_element = DocumentElement(
                document_id=document_id,
                element_type=element_data.element_type,
                content=element_data.content,
                metadata_=element_data.metadata_
            )
            db.add(db_element)
            
        # 4. Mark as processed
        doc.processing_status = ProcessingStatus.PROCESSED
        db.commit()
        logger.info(f"Document {document_id} processed successfully.")

        # 5. Index into Vector Store
        from app.services.indexing import index_document_elements
        index_document_elements(db, document_id)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        db.rollback()
        
        # In a new transaction, mark as failed
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.processing_status = ProcessingStatus.FAILED
            db.commit()
        return False
