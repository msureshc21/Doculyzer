"""
ExtractedField model for storing raw field extractions from documents.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class ExtractedField(Base):
    """
    Represents a field extracted from a document.
    
    Stores raw extraction results with confidence scores.
    This is the first layer of data - before it becomes a canonical fact.
    """
    __tablename__ = "extracted_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Field identification
    field_name = Column(String(100), nullable=False, index=True)  # e.g., 'company_name', 'ein', 'address'
    field_type = Column(String(50), nullable=True)  # e.g., 'text', 'number', 'date', 'address'
    
    # Extracted value
    value = Column(Text, nullable=False)  # The extracted value as string
    confidence = Column(Float, nullable=False)  # Confidence score 0.0-1.0
    
    # Extraction metadata
    extraction_method = Column(String(50), nullable=True)  # e.g., 'ocr', 'ai_model', 'manual'
    extraction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Context information
    page_number = Column(Integer, nullable=True)  # For multi-page documents
    bounding_box = Column(String(100), nullable=True)  # JSON string of coordinates if available
    context = Column(Text, nullable=True)  # Surrounding text context
    
    # Relationships
    document = relationship("Document", back_populates="extracted_fields")
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_document_field', 'document_id', 'field_name'),
    )
    
    def __repr__(self):
        return f"<ExtractedField(id={self.id}, field_name='{self.field_name}', confidence={self.confidence})>"

