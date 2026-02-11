"""
Pydantic schemas for PDF auto-fill functionality.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FieldExplanation(BaseModel):
    """
    Explanation metadata for a filled field.
    """
    field_name: str = Field(description="PDF form field name")
    fact_key: str = Field(description="Matched Memory Graph fact key")
    value: str = Field(description="Value used to fill the field")
    confidence: float = Field(description="Confidence score (0.0-1.0)")
    source_document_id: Optional[int] = Field(
        default=None,
        description="ID of source document in Memory Graph"
    )
    source_document_name: Optional[str] = Field(
        default=None,
        description="Name of source document"
    )
    reason: str = Field(description="Reason for selecting this value")
    matched: bool = Field(description="Whether field was successfully matched and filled")


class AutoFillResult(BaseModel):
    """
    Result of PDF auto-fill operation.
    """
    filled_pdf_path: Optional[str] = Field(
        default=None,
        description="Path to filled PDF file (if generated)"
    )
    fields_detected: int = Field(description="Number of form fields detected in PDF")
    fields_matched: int = Field(description="Number of fields matched to Memory Graph")
    fields_filled: int = Field(description="Number of fields successfully filled")
    explanations: List[FieldExplanation] = Field(
        description="Explanation for each field fill attempt"
    )
    success: bool = Field(description="Whether auto-fill was successful")


class AutoFillRequest(BaseModel):
    """
    Request for PDF auto-fill.
    """
    pdf_content: Optional[bytes] = Field(
        default=None,
        description="PDF file content (if not using document_id)"
    )
    document_id: Optional[int] = Field(
        default=None,
        description="ID of uploaded document to use as template"
    )
    generate_preview: bool = Field(
        default=True,
        description="Whether to generate filled PDF preview"
    )

