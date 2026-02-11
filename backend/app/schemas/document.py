"""
Pydantic schemas for document API endpoints.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    """Response schema for document operations."""
    id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    upload_date: datetime
    processed: str
    description: Optional[str] = None
    tags: Optional[str] = None
    
    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    message: str
    document: DocumentResponse
    text_extracted: bool = Field(default=False, description="Whether text was successfully extracted")


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""
    documents: list[DocumentResponse]
    total: int

