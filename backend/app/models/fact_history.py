"""
FactHistory model for tracking changes to company facts.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base


class ChangeType(str, enum.Enum):
    """Enumeration of change types for fact history."""
    EXTRACTION = "extraction"  # Initial extraction from document
    USER_EDIT = "user_edit"  # Manual user edit
    SYSTEM_UPDATE = "system_update"  # System-generated update
    MERGE = "merge"  # Merged from multiple sources
    DEPRECATE = "deprecate"  # Fact was deprecated


class FactHistory(Base):
    """
    Tracks historical changes to company facts.
    
    Maintains a complete audit trail of all changes to canonical facts,
    including who made the change, when, and what the values were.
    """
    __tablename__ = "fact_history"
    
    id = Column(Integer, primary_key=True, index=True)
    fact_id = Column(Integer, ForeignKey("company_facts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Change information
    change_type = Column(
        Enum(ChangeType, name="change_type", create_constraint=True),
        nullable=False,
        index=True
    )
    changed_by = Column(String(100), nullable=False)  # User ID or 'system'
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Value tracking
    old_value = Column(Text, nullable=True)  # Previous value (null for initial creation)
    new_value = Column(Text, nullable=False)  # New value
    
    # Confidence tracking
    old_confidence = Column(String(20), nullable=True)  # Previous confidence
    new_confidence = Column(String(20), nullable=True)  # New confidence
    
    # Change metadata
    reason = Column(Text, nullable=True)  # Reason for change (user note, system reason, etc.)
    source_document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    fact = relationship("CompanyFact", back_populates="history")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    
    # Index for time-based queries
    __table_args__ = (
        Index('idx_fact_changed_at', 'fact_id', 'changed_at'),
    )
    
    def __repr__(self):
        return f"<FactHistory(id={self.id}, fact_id={self.fact_id}, change_type='{self.change_type}')>"

