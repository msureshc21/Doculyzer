"""
Unified document upload and auto-fill workflow API.

This endpoint combines document upload, analysis, and auto-fill into a single
intelligent workflow that:
1. Uploads the document
2. Analyzes it to understand what it's asking for
3. Matches fields to Memory Graph
4. Shows user what can be auto-filled
5. Gets user confirmation
6. Fills the document
"""
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Document
from app.schemas.document import DocumentResponse
from app.schemas.document_analysis import (
    DocumentAnalysisResponse,
    FieldContextResponse,
    FieldMatchSuggestion,
    DocumentFillPreview,
    DocumentFillRequest
)
from app.services.document_analyzer import DocumentAnalyzer
from app.services.pdf_extractor import PDFExtractor
from app.services.pdf_form_detector import PDFFormDetector
from app.services.memory_graph import MemoryGraphService
from app.storage.filesystem import storage
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-and-analyze", response_model=DocumentFillPreview)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document and analyze it to understand what it's asking for.
    
    This endpoint:
    1. Uploads the PDF
    2. Extracts text
    3. Detects form fields
    4. Analyzes document type and field context
    5. Matches fields to Memory Graph
    6. Returns preview of what can be auto-filled
    
    Args:
        file: PDF file to upload and analyze
        db: Database session
        
    Returns:
        DocumentFillPreview with analysis and field match suggestions
    """
    try:
        # Read file
        file_content = await file.read()
        
        # Validate PDF
        if not PDFExtractor.is_pdf(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not appear to be a valid PDF"
            )
        
        # Extract text
        extracted_text = PDFExtractor.extract_text(file_content, file.filename)
        
        # Detect form fields
        form_fields = PDFFormDetector.detect_form_fields(file_content)
        form_fields_dict = [
            {
                "field_name": f.field_name,
                "field_type": f.field_type,
                "value": f.value
            }
            for f in form_fields
        ]
        
        # Analyze document
        analysis = DocumentAnalyzer.analyze_document(
            pdf_content=file_content,
            extracted_text=extracted_text,
            form_fields=form_fields_dict
        )
        
        # Match fields to Memory Graph
        field_matches = []
        fields_requiring_input = []
        
        for field_context in analysis.fields:
            # Only try to match company_current fields
            if field_context.category == "company_current":
                match = DocumentAnalyzer.match_field_to_memory_graph(field_context, db)
                
                if match:
                    field_matches.append(FieldMatchSuggestion(
                        field_name=field_context.field_name,
                        field_context=field_context,
                        suggested_fact_key=match["fact_key"],
                        suggested_value=match["fact"].fact_value,
                        confidence=match["confidence"],
                        match_quality=match["match_quality"],
                        requires_confirmation=True,
                        reason=f"Matched to {match['fact_key']} from Memory Graph"
                    ))
                else:
                    # Field could be matched but no value in Memory Graph
                    field_matches.append(FieldMatchSuggestion(
                        field_name=field_context.field_name,
                        field_context=field_context,
                        requires_confirmation=False,
                        reason="Field matches Memory Graph pattern but no value available"
                    ))
            else:
                # Field requires user input (not company_current)
                fields_requiring_input.append(field_context)
        
        # Convert analysis to response
        analysis_response = DocumentAnalysisResponse(
            document_type=analysis.document_type,
            document_purpose=analysis.document_purpose,
            summary=analysis.summary,
            fields=[
                FieldContextResponse(
                    field_name=f.field_name,
                    field_type=f.field_type,
                    label=f.label,
                    context=f.context,
                    category=f.category,
                    is_required=f.is_required,
                    examples=f.examples,
                    related_fields=f.related_fields
                )
                for f in analysis.fields
            ],
            total_fields=analysis.total_fields,
            required_fields=analysis.required_fields,
            can_autofill=analysis.can_autofill,
            warnings=analysis.warnings
        )
        
        return DocumentFillPreview(
            document_analysis=analysis_response,
            field_matches=field_matches,
            fields_requiring_input=fields_requiring_input,
            can_proceed=len(field_matches) > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_and_analyze: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document: {str(e)}"
        )


@router.post("/fill-document", response_model=DocumentResponse)
async def fill_document_with_confirmation(
    request: DocumentFillRequest,
    db: Session = Depends(get_db)
):
    """
    Fill a document with user-confirmed field values.
    
    Args:
        request: Fill request with user confirmations and values
        db: Database session
        
    Returns:
        Filled document response
        
    TODO: Implement actual PDF filling with user confirmations
    """
    # Get document
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {request.document_id} not found"
        )
    
    # Read PDF
    pdf_content = storage.read(document.file_path)
    
    # TODO: Fill PDF with confirmed matches and user-provided values
    # For now, return the document
    
    return DocumentResponse.model_validate(document)

