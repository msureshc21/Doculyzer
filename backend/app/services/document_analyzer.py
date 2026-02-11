"""
Document analysis service for intelligent document understanding.

This service analyzes documents to:
- Identify document type and purpose
- Understand field context
- Categorize fields appropriately
- Provide summaries for user review
"""
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FieldContext(BaseModel):
    """Context information for a form field."""
    field_name: str = Field(description="Name of the PDF form field")
    field_type: str = Field(description="Type of field (text, checkbox, dropdown, etc.)")
    label: Optional[str] = Field(None, description="Human-readable label for the field")
    context: str = Field(description="Context/description of what this field is asking for")
    category: str = Field(description="Category: 'company_current', 'company_previous', 'personal', 'other'")
    is_required: bool = Field(default=False, description="Whether field is required")
    examples: Optional[List[str]] = Field(None, description="Example values for this field")
    related_fields: Optional[List[str]] = Field(None, description="Related field names that provide context")


class DocumentAnalysis(BaseModel):
    """Analysis result for a document."""
    document_type: str = Field(description="Type of document (e.g., 'employment_application', 'tax_form', 'contract')")
    document_purpose: str = Field(description="Purpose/description of the document")
    summary: str = Field(description="Brief summary of what the document is asking for")
    fields: List[FieldContext] = Field(description="List of all form fields with context")
    total_fields: int = Field(description="Total number of form fields")
    required_fields: int = Field(description="Number of required fields")
    can_autofill: bool = Field(description="Whether any fields can be auto-filled from Memory Graph")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the document")


class DocumentAnalyzer:
    """
    Service for analyzing documents and understanding their structure and context.
    
    TODO: Integrate with LLM for intelligent document analysis:
    - Use LLM to understand document type
    - Analyze field context and relationships
    - Identify ambiguous fields that need user clarification
    """
    
    @staticmethod
    def analyze_document(
        pdf_content: bytes,
        extracted_text: Optional[str] = None,
        form_fields: Optional[List[Dict[str, Any]]] = None
    ) -> DocumentAnalysis:
        """
        Analyze a document to understand its structure and field context.
        
        Uses ML models when available, falls back to heuristics otherwise.
        
        Args:
            pdf_content: Binary PDF content
            extracted_text: Extracted text from PDF (optional)
            form_fields: List of detected form fields (optional)
            
        Returns:
            DocumentAnalysis with document type, purpose, and field contexts
        """
        logger.info("Analyzing document...")
        
        # Try to use ML models, fall back to heuristics
        try:
            from app.services.ml_models import get_document_classifier, get_field_analyzer
            
            analysis = DocumentAnalyzer._ml_analysis(
                pdf_content=pdf_content,
                extracted_text=extracted_text,
                form_fields=form_fields
            )
            logger.info("Document analysis completed using ML models")
            return analysis
        except ImportError:
            logger.info("ML models not available, using heuristic analysis")
            analysis = DocumentAnalyzer._stub_analysis(pdf_content, extracted_text, form_fields)
            return analysis
        except Exception as e:
            logger.warning(f"ML analysis failed: {e}, falling back to heuristics")
            analysis = DocumentAnalyzer._stub_analysis(pdf_content, extracted_text, form_fields)
            return analysis
    
    @staticmethod
    def _ml_analysis(
        pdf_content: bytes,
        extracted_text: Optional[str],
        form_fields: Optional[List[Dict[str, Any]]]
    ) -> DocumentAnalysis:
        """
        ML-powered document analysis using transformer models.
        
        Uses:
        - Document type classifier (DistilBERT)
        - Field context analyzer (BERT NER)
        
        Args:
            pdf_content: Binary PDF content
            extracted_text: Extracted text from PDF
            form_fields: List of detected form fields
            
        Returns:
            DocumentAnalysis with ML-enhanced understanding
        """
        from app.services.ml_models import get_document_classifier, get_field_analyzer
        from app.services.pdf_form_detector import PDFFormDetector
        
        # Detect form fields if not provided
        if form_fields is None:
            detected_fields = PDFFormDetector.detect_form_fields(pdf_content)
            form_fields = [
                {
                    "field_name": f.field_name,
                    "field_type": f.field_type,
                    "value": f.value
                }
                for f in detected_fields
            ]
        
        # Get ML model instances
        classifier = get_document_classifier()
        field_analyzer = get_field_analyzer()
        
        # Classify document type using ML
        field_names = [f.get("field_name", "") for f in form_fields]
        doc_type_result = classifier.classify_document(
            text=extracted_text or "",
            field_names=field_names
        )
        document_type = doc_type_result["document_type"]
        doc_confidence = doc_type_result.get("confidence", 0.8)
        
        logger.info(f"ML classified document as '{document_type}' (confidence: {doc_confidence:.2%})")
        
        # Analyze each field with ML
        field_contexts = []
        all_field_names = [f.get("field_name", "") for f in form_fields]
        
        for field in form_fields:
            field_name = field.get("field_name", "")
            field_type = field.get("field_type", "text")
            
            # Use ML to analyze field context
            context_result = field_analyzer.analyze_field_context(
                field_name=field_name,
                surrounding_text=extracted_text,
                all_fields=all_field_names
            )
            
            # Create FieldContext from ML analysis
            field_context = FieldContext(
                field_name=field_name,
                field_type=field_type,
                label=field_name.replace("_", " ").title(),
                context=context_result["context"],
                category=context_result["category"],
                is_required=DocumentAnalyzer._check_if_required(field_name),
                examples=None,
                related_fields=None
            )
            
            field_contexts.append(field_context)
            logger.debug(f"ML analyzed field '{field_name}': category={context_result['category']}")
        
        # Generate summary
        summary = DocumentAnalyzer._generate_summary(
            document_type=document_type,
            fields=field_contexts,
            extracted_text=extracted_text
        )
        
        # Add ML confidence info to summary
        if doc_confidence < 0.7:
            summary += f" (Note: Document type classification confidence: {doc_confidence:.0%})"
        
        return DocumentAnalysis(
            document_type=document_type,
            document_purpose=f"Document classified as {document_type.replace('_', ' ')} using ML analysis",
            summary=summary,
            fields=field_contexts,
            total_fields=len(field_contexts),
            required_fields=sum(1 for f in field_contexts if f.is_required),
            can_autofill=any(f.category == "company_current" for f in field_contexts),
            warnings=[] if doc_confidence >= 0.7 else [f"Low confidence in document type classification ({doc_confidence:.0%})"]
        )
    
    @staticmethod
    def _stub_analysis(
        pdf_content: bytes,
        extracted_text: Optional[str],
        form_fields: Optional[List[Dict[str, Any]]]
    ) -> DocumentAnalysis:
        """
        Stub implementation of document analysis.
        
        TODO: Replace with LLM-based analysis that:
        1. Reads document text
        2. Identifies document type
        3. Understands field context
        4. Categorizes fields appropriately
        """
        # Detect form fields if not provided
        if form_fields is None:
            from app.services.pdf_form_detector import PDFFormDetector
            detected_fields = PDFFormDetector.detect_form_fields(pdf_content)
            form_fields = [
                {
                    "field_name": f.field_name,
                    "field_type": f.field_type,
                    "value": f.value
                }
                for f in detected_fields
            ]
        
        # Analyze fields with context
        field_contexts = []
        for field in form_fields:
            context = DocumentAnalyzer._analyze_field_context(
                field_name=field.get("field_name", ""),
                field_type=field.get("field_type", "text"),
                extracted_text=extracted_text
            )
            field_contexts.append(context)
        
        # Determine document type heuristically
        document_type = DocumentAnalyzer._detect_document_type(
            form_fields=form_fields,
            extracted_text=extracted_text
        )
        
        # Generate summary
        summary = DocumentAnalyzer._generate_summary(
            document_type=document_type,
            fields=field_contexts,
            extracted_text=extracted_text
        )
        
        return DocumentAnalysis(
            document_type=document_type,
            document_purpose=f"Document appears to be a {document_type.replace('_', ' ')}",
            summary=summary,
            fields=field_contexts,
            total_fields=len(field_contexts),
            required_fields=sum(1 for f in field_contexts if f.is_required),
            can_autofill=any(f.category == "company_current" for f in field_contexts),
            warnings=[]
        )
    
    @staticmethod
    def _analyze_field_context(
        field_name: str,
        field_type: str,
        extracted_text: Optional[str]
    ) -> FieldContext:
        """
        Analyze a single field to understand its context (heuristic fallback).
        
        This is used when ML models are not available.
        """
        field_name_lower = field_name.lower()
        
        # Heuristic analysis - categorize fields
        category = "other"
        context = f"Field: {field_name}"
        label = field_name.replace("_", " ").title()
        
        # Check for previous/previous employer context
        if any(word in field_name_lower for word in ["previous", "prior", "former", "past", "old"]):
            category = "company_previous"
            context = f"Previous employer/company information: {field_name}"
        # Check for current company context
        elif any(word in field_name_lower for word in ["company", "employer", "business", "organization"]):
            if "current" in field_name_lower or "present" in field_name_lower:
                category = "company_current"
            else:
                # Ambiguous - could be current or previous
                category = "company_current"  # Default, but should ask user
                context = f"Company information (context unclear - may be current or previous): {field_name}"
        # Personal information
        elif any(word in field_name_lower for word in ["name", "address", "phone", "email", "ssn", "dob", "birth"]):
            category = "personal"
            context = f"Personal information: {field_name}"
        # Checkboxes
        elif field_type == "checkbox":
            context = f"Checkbox: {field_name}"
        
        # Determine if required (heuristic)
        is_required = DocumentAnalyzer._check_if_required(field_name)
        
        return FieldContext(
            field_name=field_name,
            field_type=field_type,
            label=label,
            context=context,
            category=category,
            is_required=is_required
        )
    
    @staticmethod
    def _check_if_required(field_name: str) -> bool:
        """Check if a field is required based on its name."""
        field_name_lower = field_name.lower()
        return any(word in field_name_lower for word in ["required", "mandatory", "*"])
    
    @staticmethod
    def _detect_document_type(
        form_fields: List[Dict[str, Any]],
        extracted_text: Optional[str]
    ) -> str:
        """
        Detect the type of document (heuristic fallback).
        
        This is used when ML models are not available.
        """
        field_names = " ".join([f.get("field_name", "").lower() for f in form_fields])
        text_sample = (extracted_text or "")[:500].lower()
        
        combined = f"{field_names} {text_sample}"
        
        # Heuristic detection
        if any(word in combined for word in ["employment", "job", "application", "resume"]):
            return "employment_application"
        elif any(word in combined for word in ["tax", "irs", "w-2", "1099"]):
            return "tax_form"
        elif any(word in combined for word in ["contract", "agreement", "terms"]):
            return "contract"
        elif any(word in combined for word in ["license", "permit", "registration"]):
            return "license_application"
        else:
            return "general_form"
    
    @staticmethod
    def _generate_summary(
        document_type: str,
        fields: List[FieldContext],
        extracted_text: Optional[str]
    ) -> str:
        """
        Generate a human-readable summary of the document.
        
        TODO: Use LLM to generate comprehensive summary.
        """
        field_categories = {}
        for field in fields:
            cat = field.category
            field_categories[cat] = field_categories.get(cat, 0) + 1
        
        summary_parts = [
            f"This appears to be a {document_type.replace('_', ' ')}.",
            f"It contains {len(fields)} form fields."
        ]
        
        if field_categories.get("company_current"):
            summary_parts.append(f"{field_categories['company_current']} field(s) asking for current company information.")
        if field_categories.get("company_previous"):
            summary_parts.append(f"{field_categories['company_previous']} field(s) asking for previous employer information.")
        if field_categories.get("personal"):
            summary_parts.append(f"{field_categories['personal']} field(s) asking for personal information.")
        
        return " ".join(summary_parts)
    
    @staticmethod
    def match_field_to_memory_graph(
        field_context: FieldContext,
        db
    ) -> Optional[Dict[str, Any]]:
        """
        Match a field context to Memory Graph facts, considering context.
        
        Args:
            field_context: Context information for the field
            db: Database session
            
        Returns:
            Dict with fact_key, fact, and confidence, or None if no match
        """
        from app.services.memory_graph import MemoryGraphService
        from app.services.pdf_form_detector import PDFFormDetector
        
        # Only match company_current fields to Memory Graph
        if field_context.category != "company_current":
            return None
        
        # Try to match field name to fact key
        fact_key = PDFFormDetector.match_field_to_fact_key(field_context.field_name)
        
        if not fact_key:
            return None
        
        # Get fact from Memory Graph
        fact = MemoryGraphService.get_fact(fact_key, db)
        
        if not fact:
            return None
        
        return {
            "fact_key": fact_key,
            "fact": fact,
            "confidence": fact.confidence,
            "match_quality": "good" if fact.confidence >= 0.9 else "moderate"
        }

