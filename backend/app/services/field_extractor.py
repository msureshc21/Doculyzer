"""
Field extraction service that orchestrates the extraction pipeline.

This service coordinates text extraction, LLM field extraction, and database storage.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Document, ExtractedField
from app.services.pdf_extractor import PDFExtractor
from app.services.llm_extractor import LLMExtractor
from app.services.memory_graph import MemoryGraphService

logger = logging.getLogger(__name__)


class FieldExtractor:
    """
    Orchestrates the field extraction pipeline.
    
    Steps:
    1. Extract text from document (PDF, etc.)
    2. Use LLM to extract structured fields
    3. Save extracted fields to database
    """
    
    @staticmethod
    def extract_fields_from_document(
        document_id: int,
        db: Session,
        file_content: Optional[bytes] = None
    ) -> list[ExtractedField]:
        """
        Extract fields from a document.
        
        Args:
            document_id: ID of the document in database
            file_content: Optional file content (if not provided, will read from storage)
            db: Database session
            
        Returns:
            List of created ExtractedField records
            
        TODO: Add support for:
        - Reading file from storage if file_content not provided
        - Handling different file types (not just PDF)
        - Batch processing multiple documents
        - Progress tracking for long documents
        """
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        logger.info(f"Extracting fields from document {document_id}: {document.filename}")
        
        # Step 1: Extract text from document
        if file_content is None:
            # TODO: Read file from storage
            logger.warning("file_content not provided - text extraction requires file content")
            return []
        
        extracted_text = PDFExtractor.extract_text(file_content, document.filename)
        
        if not extracted_text:
            logger.warning(f"Could not extract text from document {document_id}")
            return []
        
        # Step 2: Use LLM to extract structured fields
        try:
            extraction_result = LLMExtractor.extract_fields(extracted_text)
        except Exception as e:
            logger.error(f"LLM extraction failed for document {document_id}: {e}")
            # Update document status
            document.processed = "failed"
            db.commit()
            return []
        
        # Step 3: Save extracted fields to database
        created_fields = []
        for field_output in extraction_result.fields:
            try:
                # Find source span in original text
                source_text = field_output.source_span.text
                
                # Create ExtractedField record
                extracted_field = ExtractedField(
                    document_id=document_id,
                    field_name=field_output.field_name,
                    field_type=field_output.field_type,
                    value=field_output.value,
                    confidence=field_output.confidence,
                    extraction_method=extraction_result.extraction_method,
                    context=source_text,  # Store source text in context field
                    # TODO: Store source span positions if needed
                    # Could add JSON field for span metadata
                )
                
                db.add(extracted_field)
                created_fields.append(extracted_field)
                
            except Exception as e:
                logger.error(f"Error saving extracted field {field_output.field_name}: {e}")
                continue
        
        # Commit all fields
        if created_fields:
            db.commit()
            for field in created_fields:
                db.refresh(field)
            
            # Step 4: Process extracted fields into Company Memory Graph
            try:
                processed_facts = MemoryGraphService.process_extracted_fields(
                    document_id=document_id,
                    db=db
                )
                logger.info(f"Processed {len(processed_facts)} facts into memory graph for document {document_id}")
            except Exception as e:
                logger.error(f"Error processing fields into memory graph: {e}")
                # Don't fail the extraction if memory graph processing fails
            
            # Update document status
            document.processed = "completed"
            db.commit()
            
            logger.info(f"Successfully extracted and saved {len(created_fields)} fields for document {document_id}")
        else:
            logger.warning(f"No fields extracted for document {document_id}")
            document.processed = "completed"  # Still mark as completed even if no fields found
            db.commit()
        
        return created_fields

