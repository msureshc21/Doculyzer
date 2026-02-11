"""
Pydantic schemas for document analysis.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
# Import types for type hints only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.document_analyzer import FieldContext, DocumentAnalysis


class FieldContextResponse(BaseModel):
    """Response schema for field context."""
    field_name: str
    field_type: str
    label: Optional[str] = None
    context: str
    category: str
    is_required: bool = False
    examples: Optional[List[str]] = None
    related_fields: Optional[List[str]] = None
    
    model_config = {"from_attributes": True}


class DocumentAnalysisResponse(BaseModel):
    """Response schema for document analysis."""
    document_type: str
    document_purpose: str
    summary: str
    fields: List[FieldContextResponse]
    total_fields: int
    required_fields: int
    can_autofill: bool
    warnings: List[str] = []


class FieldMatchSuggestion(BaseModel):
    """Suggestion for matching a field to Memory Graph."""
    field_name: str
    field_context: FieldContextResponse
    suggested_fact_key: Optional[str] = None
    suggested_value: Optional[str] = None
    confidence: float = 0.0
    match_quality: str = "none"  # "good", "moderate", "poor", "none"
    requires_confirmation: bool = True
    reason: str = ""


class DocumentFillPreview(BaseModel):
    """Preview of what will be filled in the document."""
    document_analysis: DocumentAnalysisResponse
    field_matches: List[FieldMatchSuggestion]
    fields_requiring_input: List[FieldContextResponse]
    can_proceed: bool = False


class DocumentFillRequest(BaseModel):
    """Request to fill a document with user confirmations."""
    document_id: int
    field_values: dict = Field(default_factory=dict, description="User-provided values for fields")
    confirmed_matches: List[str] = Field(default_factory=list, description="Field names user confirmed for auto-fill")
    skip_fields: List[str] = Field(default_factory=list, description="Field names to skip")

