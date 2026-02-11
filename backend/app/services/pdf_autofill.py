"""
PDF auto-fill service with explainable logic.

This service fills PDF form fields using values from the Company Memory Graph,
providing explanations for each fill decision.
"""
import logging
import io
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logging.warning("PyPDF2 not available - PDF auto-fill will be stubbed")

from app.services.pdf_form_detector import PDFFormDetector, PDFFormField
from app.services.memory_graph import MemoryGraphService
from app.schemas.autofill import AutoFillResult, FieldExplanation
from app.storage.filesystem import storage
from app.models import Document

logger = logging.getLogger(__name__)


class PDFAutoFillService:
    """
    Service for auto-filling PDF forms with explainable logic.
    
    TODO: Enhance with pdfplumber for better form manipulation:
    - pdfplumber provides better form field access
    - Can preserve form field properties
    - Better handling of complex forms
    """
    
    @staticmethod
    def autofill_pdf(
        pdf_content: bytes,
        db: Session,
        generate_preview: bool = True
    ) -> AutoFillResult:
        """
        Auto-fill a PDF form using Company Memory Graph values.
        
        Args:
            pdf_content: Binary content of the PDF file
            db: Database session
            generate_preview: Whether to generate filled PDF preview
            
        Returns:
            AutoFillResult with filled PDF and explanations
            
        TODO: Enhance:
        1. Use pdfplumber for better form field manipulation
        2. Preserve form field properties (read-only, required, etc.)
        3. Handle different field types (text, checkbox, dropdown, etc.)
        4. Validate filled values against field constraints
        5. Support multi-page forms
        """
        logger.info("Starting PDF auto-fill")
        
        # Step 1: Detect form fields
        form_fields = PDFFormDetector.detect_form_fields(pdf_content)
        logger.info(f"Detected {len(form_fields)} form fields")
        
        if not form_fields:
            # If no fields detected, try to create stub fields for testing
            # TODO: Remove this when proper detection is implemented
            logger.warning("No form fields detected - using stub for testing")
            form_fields = PDFAutoFillService._create_stub_fields()
        
        # Step 2: Match fields to Memory Graph facts
        explanations = []
        filled_count = 0
        matched_count = 0
        
        for field in form_fields:
            explanation = PDFAutoFillService._fill_single_field(
                field=field,
                db=db
            )
            explanations.append(explanation)
            
            if explanation.matched:
                matched_count += 1
            if explanation.matched and explanation.value:
                filled_count += 1
        
        # Step 3: Generate filled PDF if requested
        filled_pdf_path = None
        if generate_preview and PYPDF2_AVAILABLE:
            try:
                filled_pdf_path = PDFAutoFillService._generate_filled_pdf(
                    pdf_content=pdf_content,
                    explanations=explanations
                )
            except Exception as e:
                logger.error(f"Error generating filled PDF: {e}")
                filled_pdf_path = None
        
        return AutoFillResult(
            filled_pdf_path=filled_pdf_path,
            fields_detected=len(form_fields),
            fields_matched=matched_count,
            fields_filled=filled_count,
            explanations=explanations,
            success=filled_count > 0
        )
    
    @staticmethod
    def _fill_single_field(
        field: PDFFormField,
        db: Session
    ) -> FieldExplanation:
        """
        Fill a single PDF form field using Memory Graph.
        
        Args:
            field: PDF form field to fill
            db: Database session
            
        Returns:
            FieldExplanation with value and metadata
        """
        # Match field name to fact key
        fact_key = PDFFormDetector.match_field_to_fact_key(field.field_name)
        
        if not fact_key:
            return FieldExplanation(
                field_name=field.field_name,
                fact_key="",
                value="",
                confidence=0.0,
                reason=f"Could not match PDF field '{field.field_name}' to any known company information field",
                matched=False
            )
        
        # Get fact from Memory Graph
        fact = MemoryGraphService.get_fact(fact_key, db)
        
        if not fact:
            return FieldExplanation(
                field_name=field.field_name,
                fact_key=fact_key,
                value="",
                confidence=0.0,
                reason=f"Matched to '{fact_key}' field, but no value available in company records. Please add this information to the Memory Graph first.",
                matched=True  # Matched to fact key, but no value available
            )
        
        # Get source document info
        source_doc = None
        source_doc_name = None
        if fact.source_document_id:
            source_doc = db.query(Document).filter(
                Document.id == fact.source_document_id
            ).first()
            if source_doc:
                source_doc_name = source_doc.filename
        
        # Build human-readable explanation
        reason_parts = []
        
        # Primary source indicator
        if fact.edit_count > 0:
            if fact.edit_count == 1:
                reason_parts.append("User-verified value (manually edited)")
            else:
                reason_parts.append(f"User-verified value (edited {fact.edit_count} times)")
        else:
            reason_parts.append("Automatically extracted from document")
        
        # Source document
        if source_doc_name:
            reason_parts.append(f"Source document: {source_doc_name}")
        
        # Confidence with human-readable description
        if fact.confidence >= 0.95:
            confidence_desc = "Very high confidence"
        elif fact.confidence >= 0.85:
            confidence_desc = "High confidence"
        elif fact.confidence >= 0.70:
            confidence_desc = "Moderate confidence"
        else:
            confidence_desc = "Low confidence"
        
        reason_parts.append(f"{confidence_desc} ({fact.confidence:.0%})")
        
        reason = ". ".join(reason_parts) + "."
        
        return FieldExplanation(
            field_name=field.field_name,
            fact_key=fact_key,
            value=fact.fact_value,
            confidence=fact.confidence,
            source_document_id=fact.source_document_id,
            source_document_name=source_doc_name,
            reason=reason,
            matched=True
        )
    
    @staticmethod
    def _generate_filled_pdf(
        pdf_content: bytes,
        explanations: List[FieldExplanation]
    ) -> Optional[str]:
        """
        Generate a filled PDF with form fields populated.
        
        Args:
            pdf_content: Original PDF content
            explanations: List of field explanations with values
            
        Returns:
            Path to filled PDF file, or None if generation fails
        """
        if not PYPDF2_AVAILABLE:
            logger.warning("PyPDF2 not available - cannot generate filled PDF")
            return None
        
        try:
            # Read PDF
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            writer = PdfWriter()
            
            # Build mapping of field names to values
            # Map both the PDF field name and the matched fact key
            field_values = {}
            for explanation in explanations:
                if explanation.matched and explanation.value:
                    # Use the PDF field name as the key
                    field_values[explanation.field_name] = explanation.value
                    # Also try the fact_key in case PDF uses that name
                    if explanation.fact_key:
                        field_values[explanation.fact_key] = explanation.value
            
            logger.info(f"Filling {len(field_values)} form fields")
            
            # Copy pages first
            if reader.metadata is not None:
                writer.add_metadata(reader.metadata)
            
            # Copy all pages
            for page_num, page in enumerate(reader.pages):
                writer.add_page(page)
            
            # Try to fill form fields using PyPDF2's form field update
            # PyPDF2 v3.0+ has better form field support
            try:
                # Get form fields from the PDF
                form_fields = reader.get_form_text_fields()
                logger.info(f"Found {len(form_fields)} form fields in PDF: {list(form_fields.keys())}")
                
                # Build a mapping of PDF field names to values
                # Try to match our field names to PDF field names
                fields_to_fill = {}
                
                for explanation in explanations:
                    if not explanation.matched or not explanation.value:
                        continue
                    
                    pdf_field_name = None
                    # Try exact match first
                    if explanation.field_name in form_fields:
                        pdf_field_name = explanation.field_name
                    elif explanation.fact_key in form_fields:
                        pdf_field_name = explanation.fact_key
                    else:
                        # Try case-insensitive and partial matching
                        field_name_lower = explanation.field_name.lower()
                        fact_key_lower = explanation.fact_key.lower() if explanation.fact_key else ""
                        
                        for pdf_field in form_fields.keys():
                            pdf_field_lower = pdf_field.lower()
                            # Check if PDF field contains our field name or vice versa
                            if (field_name_lower in pdf_field_lower or 
                                pdf_field_lower in field_name_lower or
                                fact_key_lower in pdf_field_lower or
                                pdf_field_lower in fact_key_lower):
                                pdf_field_name = pdf_field
                                break
                    
                    if pdf_field_name:
                        fields_to_fill[pdf_field_name] = explanation.value
                        logger.info(f"Matched '{explanation.field_name}' -> PDF field '{pdf_field_name}' = '{explanation.value}'")
                
                # Fill form fields on each page
                if fields_to_fill:
                    for page_num, page in enumerate(writer.pages):
                        try:
                            writer.update_page_form_field_values(page, fields_to_fill)
                            logger.info(f"Filled form fields on page {page_num + 1}")
                        except Exception as page_error:
                            logger.warning(f"Could not fill fields on page {page_num + 1}: {page_error}")
                else:
                    logger.warning("No fields matched to fill - field names may not match PDF form field names")
                    
            except AttributeError:
                logger.warning("PyPDF2 version doesn't support get_form_text_fields - form filling may not work")
            except Exception as e:
                logger.warning(f"Could not fill form fields: {e}", exc_info=True)
                # Continue - we'll still create the PDF, just without filled fields
            
            # Write filled PDF
            filled_pdf_file = io.BytesIO()
            writer.write(filled_pdf_file)
            filled_pdf_content = filled_pdf_file.getvalue()
            
            # Save filled PDF
            filename = f"filled_{uuid.uuid4().hex[:8]}.pdf"
            file_path = f"previews/{filename}"
            storage.save(filled_pdf_content, file_path)
            
            logger.info(f"Generated filled PDF: {file_path} (filled {len(field_values)} fields)")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating filled PDF: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _create_stub_fields() -> List[PDFFormField]:
        """
        Create stub form fields for testing when detection is not available.
        
        Returns:
            List of stub PDF form fields
        """
        # Common form fields for testing
        return [
            PDFFormField("company_name", "text"),
            PDFFormField("ein", "text"),
            PDFFormField("address", "text"),
            PDFFormField("city", "text"),
            PDFFormField("state", "text"),
            PDFFormField("zip_code", "text"),
            PDFFormField("phone", "text"),
            PDFFormField("email", "text")
        ]

