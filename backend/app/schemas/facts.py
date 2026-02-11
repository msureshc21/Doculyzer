"""
Pydantic schemas for company facts API endpoints.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class FactResponse(BaseModel):
    """Response schema for a company fact."""
    id: int
    fact_key: str
    fact_category: Optional[str] = None
    fact_value: str
    confidence: float
    source_document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_edited_by: Optional[str] = None
    edit_count: int
    status: str
    
    model_config = {"from_attributes": True}


class FactCreateRequest(BaseModel):
    """Request schema for creating a fact manually."""
    fact_key: str = Field(description="Key of the fact (e.g., 'company_name', 'ein')")
    fact_value: str = Field(description="Value for the fact")
    fact_category: Optional[str] = Field(default=None, description="Category of the fact")


class FactUpdateRequest(BaseModel):
    """Request schema for updating a fact."""
    value: str = Field(description="New value for the fact")
    reason: Optional[str] = Field(default=None, description="Reason for the update")


class FactHistoryResponse(BaseModel):
    """Response schema for fact history entry."""
    id: int
    change_type: str
    changed_by: str
    changed_at: datetime
    old_value: Optional[str] = None
    new_value: str
    old_confidence: Optional[str] = None
    new_confidence: Optional[str] = None
    reason: Optional[str] = None
    source_document_id: Optional[int] = None
    
    model_config = {"from_attributes": True}


class FactListResponse(BaseModel):
    """Response schema for listing facts."""
    facts: List[FactResponse]
    total: int


class FactWithHistoryResponse(BaseModel):
    """Response schema for fact with its history."""
    fact: FactResponse
    history: List[FactHistoryResponse]


class MissingFactsResponse(BaseModel):
    """Response schema for missing facts detection."""
    missing_facts: List[str] = Field(description="List of fact keys that are missing from Memory Graph")
    suggested_fields: List[dict] = Field(description="Suggested fields with descriptions")
    
    model_config = {"from_attributes": True}
