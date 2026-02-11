"""
CompanyFact model for storing canonical company facts.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class CompanyFact(Base):
    """
    Represents a canonical fact about the company.
    
    This is the "memory graph" - the single source of truth for company information.
    Facts are derived from extracted fields but represent the authoritative value.
    """
    __tablename__ = "company_facts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Fact identification
    fact_key = Column(String(100), nullable=False, unique=True, index=True)  # e.g., 'company_name', 'ein', 'address_line_1'
    fact_category = Column(String(50), nullable=True, index=True)  # e.g., 'company_info', 'legal', 'financial'
    
    # Canonical value
    fact_value = Column(Text, nullable=False)  # The authoritative value
    confidence = Column(Float, nullable=False)  # Overall confidence 0.0-1.0
    
    # Source tracking
    source_document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    source_field_id = Column(
        Integer,
        ForeignKey("extracted_fields.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Edit tracking
    last_edited_by = Column(String(100), nullable=True)  # User ID or 'system'
    edit_count = Column(Integer, default=0, nullable=False)  # Number of times edited
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, deprecated, merged
    
    # Relationships
    source_document = relationship(
        "Document",
        back_populates="company_facts",
        foreign_keys=[source_document_id]
    )
    source_field = relationship("ExtractedField", foreign_keys=[source_field_id])
    history = relationship(
        "FactHistory",
        back_populates="fact",
        cascade="all, delete-orphan",
        order_by="FactHistory.changed_at.desc()"
    )
    
    # Index for common queries
    __table_args__ = (
        Index('idx_category_status', 'fact_category', 'status'),
    )
    
    def __repr__(self):
        return f"<CompanyFact(id={self.id}, fact_key='{self.fact_key}', value='{self.fact_value[:50]}...')>"

