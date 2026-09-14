import hashlib
import uuid
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.document import DocumentElement

class ChunkData:
    def __init__(self, text: str, metadata: Dict[str, Any], element_id: int, document_id: int, chunk_index: int):
        self.text = text
        self.metadata = metadata
        self.element_id = element_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        # Hash the content explicitly
        self.content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        # Create a unique ID for this chunk instance in SQL and Chroma
        self.chunk_id = str(uuid.uuid4())
        
        # Inject standard ChromaDB metadata
        self.metadata["chunk_id"] = self.chunk_id
        self.metadata["element_id"] = self.element_id
        self.metadata["document_id"] = self.document_id
        self.metadata["chunk_index"] = self.chunk_index

def chunk_document_element(element: DocumentElement) -> List[ChunkData]:
    chunk_size = 1000
    chunk_overlap = 200

    chunks = []
    base_metadata = dict(element.metadata_ or {})

    if element.element_type == "text":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        texts = splitter.split_text(element.content)
        for i, text in enumerate(texts):
            chunks.append(ChunkData(
                text=text, 
                metadata=dict(base_metadata), 
                element_id=element.id,
                document_id=element.document_id,
                chunk_index=i
            ))
            
    elif element.element_type == "table":
        # Keep table intact for phase 2.3
        chunks.append(ChunkData(
            text=element.content, 
            metadata=dict(base_metadata), 
            element_id=element.id,
            document_id=element.document_id,
            chunk_index=0
        ))
        
    return chunks
