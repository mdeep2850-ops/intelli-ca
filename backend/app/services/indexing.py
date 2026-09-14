from sqlalchemy.orm import Session
from app.models.document import DocumentElement, Chunk, IndexingStatus
from app.services.chunking import chunk_document_element
from app.services.embedding import get_embedding_service
from app.services.vector_store import vector_store
from app.core.logger import logger

def index_document_elements(db: Session, document_id: int):
    elements = db.query(DocumentElement).filter(
        DocumentElement.document_id == document_id,
        DocumentElement.indexing_status.in_([IndexingStatus.PENDING, IndexingStatus.FAILED])
    ).all()

    if not elements:
        return 0

    embedding_service = get_embedding_service()
    total_indexed = 0
    
    for element in elements:
        try:
            element.indexing_status = IndexingStatus.PROCESSING
            db.commit()
            
            # Clean up any existing chunks for this element (in case of a retry after partial failure)
            existing_chunks = db.query(Chunk).filter(Chunk.element_id == element.id).all()
            if existing_chunks:
                chunk_ids = [c.chunk_id for c in existing_chunks]
                vector_store.delete_chunks("client_documents", where={"chunk_id": {"$in": chunk_ids}})
                db.query(Chunk).filter(Chunk.element_id == element.id).delete()
                db.commit()

            chunks_data = chunk_document_element(element)
            if not chunks_data:
                element.indexing_status = IndexingStatus.INDEXED
                db.commit()
                continue
            
            # Check for existing hashes to prevent duplicate embeddings
            hashes = [c.content_hash for c in chunks_data]
            matched_chunks = db.query(Chunk).filter(Chunk.content_hash.in_(hashes)).all()
            hash_to_existing_id = {c.content_hash: c.chunk_id for c in matched_chunks}
            
            existing_embeddings = {}
            if hash_to_existing_id:
                emb_map = vector_store.get_embeddings_by_ids("client_documents", list(hash_to_existing_id.values()))
                for h, cid in hash_to_existing_id.items():
                    if cid in emb_map:
                        existing_embeddings[h] = emb_map[cid]
            
            # Determine which chunks actually need a new embedding API call
            texts_to_embed = []
            for c in chunks_data:
                if c.content_hash not in existing_embeddings:
                    texts_to_embed.append(c.text)
            
            new_embeddings_list = []
            if texts_to_embed:
                new_embeddings_list = embedding_service.embed_documents(texts_to_embed)
            
            text_to_embedding_map = dict(zip(texts_to_embed, new_embeddings_list))
            
            final_ids = []
            final_texts = []
            final_metas = []
            final_embs = []
            
            for c in chunks_data:
                if c.content_hash in existing_embeddings:
                    emb = existing_embeddings[c.content_hash]
                    # Ensure it is a list for Chroma
                    if hasattr(emb, "tolist"):
                        emb = emb.tolist()
                else:
                    emb = text_to_embedding_map.get(c.text)
                    
                final_ids.append(c.chunk_id)
                final_texts.append(c.text)
                final_metas.append(c.metadata)
                final_embs.append(emb)
                
            if final_ids:
                vector_store.add_chunks(
                    collection_name="client_documents",
                    ids=final_ids,
                    texts=final_texts,
                    metadatas=final_metas,
                    embeddings=final_embs
                )
            
            for c in chunks_data:
                db_chunk = Chunk(
                    id=c.chunk_id,
                    chunk_id=c.chunk_id,
                    element_id=element.id,
                    document_id=element.document_id,
                    content=c.text,
                    content_hash=c.content_hash,
                    chunk_index=c.chunk_index,
                    metadata_=c.metadata,
                    indexing_status=IndexingStatus.INDEXED
                )
                db.add(db_chunk)
                
            element.indexing_status = IndexingStatus.INDEXED
            db.commit()
            total_indexed += len(chunks_data)
            
        except Exception as e:
            logger.exception(f"Failed to index element {element.id}")
            db.rollback()
            failed_el = db.query(DocumentElement).filter(DocumentElement.id == element.id).first()
            if failed_el:
                failed_el.indexing_status = IndexingStatus.FAILED
                db.commit()
                
    return total_indexed
