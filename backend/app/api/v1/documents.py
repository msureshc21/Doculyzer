"""
Document upload and management API endpoints.
"""
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentListResponse
from app.storage.filesystem import storage
from app.services.pdf_extractor import PDFExtractor
from app.services.events import publish_document_ingested
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_MIME_TYPES = {"application/pdf"}


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file object
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type if provided
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )


def generate_file_path(filename: str) -> str:
    """
    Generate a unique file path for storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Relative file path within storage directory
    """
    # Generate unique filename to avoid collisions
    file_ext = Path(filename).suffix
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}{file_ext}"
    
    # Organize by date (optional: can organize differently)
    # For now, store directly in uploads directory
    return safe_filename


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    tags: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document.
    
    This endpoint:
    1. Validates the uploaded file
    2. Stores the file locally
    3. Saves document metadata to database
    4. Extracts text from PDF (stub implementation)
    5. Publishes document_ingested event
    
    Args:
        file: PDF file to upload
        description: Optional description of the document
        tags: Optional comma-separated tags
        db: Database session
        
    Returns:
        DocumentUploadResponse with document details
        
    Raises:
        HTTPException: If upload fails or file is invalid
    """
    try:
        # Validate file
        validate_file(file)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Validate PDF format
        if not PDFExtractor.is_pdf(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not appear to be a valid PDF"
            )
        
        # Generate storage path
        storage_path = generate_file_path(file.filename)
        
        # Store file
        try:
            full_path = storage.save(file_content, storage_path)
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file to storage"
            )
        
        # Extract text from PDF (stub)
        text_extracted = False
        extracted_text = None
        try:
            extracted_text = PDFExtractor.extract_text(file_content, file.filename)
            text_extracted = extracted_text is not None
            
        except Exception as e:
            logger.warning(f"Text extraction failed for {file.filename}: {e}")
            # Don't fail the upload if text extraction fails
            # Document is still saved, just without extracted text
        
        # Determine file type from extension
        file_ext = Path(file.filename).suffix.lower().lstrip(".")
        mime_type = file.content_type or f"application/{file_ext}"
        
        # Save document metadata to database
        try:
            document = Document(
                filename=file.filename,
                file_path=storage_path,  # Store relative path
                file_type=file_ext,
                file_size=file_size,
                mime_type=mime_type,
                description=description,
                tags=tags,
                processed="completed" if text_extracted else "pending"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
        except Exception as e:
            logger.error(f"Error saving document to database: {e}")
            # Rollback database transaction
            db.rollback()
            # Try to clean up stored file
            try:
                storage.delete(storage_path)
            except Exception:
                pass
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document metadata to database"
            )
        
        # Publish document_ingested event
        try:
            publish_document_ingested(
                document_id=document.id,
                filename=document.filename,
                file_size=document.file_size
            )
        except Exception as e:
            # Log but don't fail the request if event publishing fails
            logger.warning(f"Failed to publish document_ingested event: {e}")
        
        # Extract fields if text was extracted
        fields_extracted = 0
        if text_extracted and extracted_text:
            try:
                from app.services.field_extractor import FieldExtractor
                extracted_fields = FieldExtractor.extract_fields_from_document(
                    document_id=document.id,
                    db=db,
                    file_content=file_content
                )
                fields_extracted = len(extracted_fields)
                logger.info(f"Extracted {fields_extracted} fields from document {document.id}")
            except Exception as e:
                logger.warning(f"Field extraction failed for document {document.id}: {e}")
                # Don't fail the upload if field extraction fails
        
        return DocumentUploadResponse(
            message="Document uploaded successfully",
            document=DocumentResponse.model_validate(document),
            text_extracted=text_extracted
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during document upload"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get document by ID.
    
    Args:
        document_id: ID of the document
        db: Database session
        
    Returns:
        Document details
        
    Raises:
        HTTPException: If document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all documents.
    
    Args:
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        db: Database session
        
    Returns:
        List of documents with total count
    """
    total = db.query(Document).count()
    documents = db.query(Document).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a document and its associated file.
    
    Args:
        document_id: ID of the document to delete
        db: Database session
        
    Raises:
        HTTPException: If document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Delete file from storage
    try:
        storage.delete(document.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file {document.file_path}: {e}")
        # Continue with database deletion even if file deletion fails
    
    # Delete from database (cascade will handle related records)
    db.delete(document)
    db.commit()
    
    return None
