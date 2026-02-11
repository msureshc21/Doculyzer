"""
Pydantic schemas for field extraction.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TextSpan(BaseModel):
    """
    Represents a span of text in the source document.
    
    Used to track where extracted values came from.
    """
    start: int = Field(description="Start character position in source text")
    end: int = Field(description="End character position in source text")
    text: str = Field(description="The actual text span")
    
    @field_validator('end')
    def end_after_start(cls, v, info):
        """Validate that end is after start."""
        if 'start' in info.data and v <= info.data['start']:
            raise ValueError('end must be greater than start')
        return v


class ExtractedFieldOutput(BaseModel):
    """
    Represents a single extracted field with metadata.
    
    This is the output format from the LLM extraction service.
    """
    field_name: str = Field(description="Name of the field (e.g., 'company_name', 'ein')")
    value: str = Field(description="Extracted value")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0"
    )
    source_span: TextSpan = Field(description="Source text span where value was found")
    field_type: Optional[str] = Field(
        default=None,
        description="Type of field (e.g., 'text', 'number', 'date', 'address')"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or context about the extraction"
    )


class ExtractionResult(BaseModel):
    """
    Complete extraction result containing all extracted fields.
    """
    fields: list[ExtractedFieldOutput] = Field(
        default_factory=list,
        description="List of extracted fields (can be empty if no fields found)"
    )
    extraction_method: str = Field(default="llm", description="Method used for extraction")

