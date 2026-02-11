"""
Document model for storing uploaded document metadata.
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Document(Base):
    """
    Represents an uploaded document.
    
    Stores metadata about documents uploaded to the system,
    including file path, type, size, and upload timestamp.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(512), nullable=False, unique=True)
    file_type = Column(String(50), nullable=False)  # e.g., 'pdf', 'docx', 'txt'
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    
    # Optional fields
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Relationships
    extracted_fields = relationship(
        "ExtractedField",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    company_facts = relationship(
        "CompanyFact",
        back_populates="source_document",
        foreign_keys="CompanyFact.source_document_id"
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"

