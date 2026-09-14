from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class IndexingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)  # Nullable since auth is pending
    filename = Column(String, index=True)
    file_type = Column(String)
    file_size = Column(Integer)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    storage_path = Column(String)

    elements = relationship("DocumentElement", back_populates="document", cascade="all, delete-orphan")

class DocumentElement(Base):
    __tablename__ = "document_elements"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    element_type = Column(String) # e.g., "text", "table"
    content = Column(Text)
    metadata_ = Column("metadata", JSON) # JSON field for structured source information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    indexing_status = Column(SQLEnum(IndexingStatus), default=IndexingStatus.PENDING)

    document = relationship("Document", back_populates="elements")
    chunks = relationship("Chunk", back_populates="element", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, index=True) # database primary key, hash id
    chunk_id = Column(String, index=True) # ID stored in ChromaDB
    element_id = Column(Integer, ForeignKey("document_elements.id", ondelete="CASCADE"), index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content = Column(Text)
    content_hash = Column(String, index=True)
    chunk_index = Column(Integer)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    indexing_status = Column(SQLEnum(IndexingStatus), default=IndexingStatus.PENDING)

    element = relationship("DocumentElement", back_populates="chunks")
