"""
PDF auto-fill API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models import Document
from app.schemas.autofill import AutoFillResult, AutoFillRequest
from app.services.pdf_autofill import PDFAutoFillService
from app.services.pdf_form_detector import PDFFormDetector
from app.storage.filesystem import storage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/autofill", response_model=AutoFillResult)
async def autofill_pdf(
    file: Optional[UploadFile] = File(None),
    document_id: Optional[int] = None,
    generate_preview: bool = True,
    db: Session = Depends(get_db)
):
    """
    Auto-fill a PDF form using Company Memory Graph values.
    
    Either provide a file upload or specify a document_id of an uploaded document.
    
    Args:
        file: PDF file to fill (optional if document_id provided)
        document_id: ID of uploaded document to use (optional if file provided)
        generate_preview: Whether to generate filled PDF preview
        db: Database session
        
    Returns:
        AutoFillResult with filled PDF path and explanations
        
    Raises:
        HTTPException: If neither file nor document_id provided, or if processing fails
    """
    pdf_content = None
    
    # Get PDF content from either file upload or document_id
    if file:
        pdf_content = await file.read()
    elif document_id:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found"
            )
        
        # Read file from storage
        try:
            pdf_content = storage.read(document.file_path)
        except Exception as e:
            logger.error(f"Error reading document file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read document file"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'file' or 'document_id' must be provided"
        )
    
    # Validate PDF
    if not PDFFormDetector.is_pdf(pdf_content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid PDF"
        )
    
    # Perform auto-fill
    try:
        result = PDFAutoFillService.autofill_pdf(
            pdf_content=pdf_content,
            db=db,
            generate_preview=generate_preview
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error during auto-fill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-fill failed: {str(e)}"
        )


@router.get("/preview/{file_path:path}")
async def get_filled_pdf_preview(
    file_path: str
):
    """
    Get filled PDF preview file.
    
    Args:
        file_path: Path to filled PDF file (relative to storage)
        
    Returns:
        PDF file response
        
    Raises:
        HTTPException: If file not found
    """
    try:
        # Security: Ensure path is within previews directory
        if not file_path.startswith("previews/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid file path"
            )
        
        # Check if file exists
        if not storage.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Filled PDF not found"
            )
        
        # Read file
        file_content = storage.read(file_path)
        
        # Return file
        return FileResponse(
            path=storage.base_path / file_path,
            media_type="application/pdf",
            filename=file_path.split("/")[-1]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving filled PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve filled PDF"
        )


@router.post("/detect-fields")
async def detect_form_fields(
    file: UploadFile = File(...)
):
    """
    Detect form fields in a PDF (without filling).
    
    Useful for debugging and understanding PDF structure.
    
    Args:
        file: PDF file to analyze
        
    Returns:
        List of detected form fields
    """
    pdf_content = await file.read()
    
    if not PDFFormDetector.is_pdf(pdf_content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid PDF"
        )
    
    fields = PDFFormDetector.detect_form_fields(pdf_content)
    
    return {
        "fields_detected": len(fields),
        "fields": [
            {
                "name": field.field_name,
                "type": field.field_type,
                "value": field.value,
                "page": field.page_number
            }
            for field in fields
        ]
    }

