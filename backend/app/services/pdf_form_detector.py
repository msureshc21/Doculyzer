"""
PDF form field detection service.

Detects form fields (AcroForm fields) in PDF documents.
"""
import logging
from typing import List, Dict, Optional
import io

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logging.warning("PyPDF2 not available - PDF form detection will be stubbed")

logger = logging.getLogger(__name__)


class PDFFormField:
    """
    Represents a form field in a PDF.
    """
    def __init__(
        self,
        field_name: str,
        field_type: str,
        value: Optional[str] = None,
        page_number: int = 0
    ):
        self.field_name = field_name
        self.field_type = field_type  # 'text', 'button', 'choice', etc.
        self.value = value
        self.page_number = page_number
    
    def __repr__(self):
        return f"PDFFormField(name='{self.field_name}', type='{self.field_type}', value='{self.value}')"


class PDFFormDetector:
    """
    Service for detecting form fields in PDF documents.
    
    TODO: Enhance with pdfplumber for better field detection:
    - pdfplumber provides better field metadata
    - Can detect field positions and sizes
    - Better handling of complex forms
    """
    
    @staticmethod
    def detect_form_fields(pdf_content: bytes) -> List[PDFFormField]:
        """
        Detect all form fields in a PDF document.
        
        Args:
            pdf_content: Binary content of the PDF file
            
        Returns:
            List of detected form fields
            
        TODO: Enhance detection:
        1. Use pdfplumber for better field detection
        2. Detect field positions and bounding boxes
        3. Detect field types more accurately
        4. Handle nested fields
        5. Detect required vs optional fields
        """
        if not PYPDF2_AVAILABLE:
            logger.warning("PyPDF2 not available - returning empty form fields")
            return []
        
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            form_fields = []
            
            # Get form fields using PyPDF2's get_form_text_fields
            # This returns a dict of field_name -> value
            try:
                text_fields = reader.get_form_text_fields()
                if text_fields:
                    for field_name, value in text_fields.items():
                        form_fields.append(PDFFormField(
                            field_name=field_name,
                            field_type="text",
                            value=value,
                            page_number=0  # PyPDF2 doesn't provide page number easily
                        ))
                    logger.info(f"Found {len(form_fields)} text form fields")
            except Exception as e:
                logger.warning(f"Could not extract text form fields: {e}")
            
            # Try to get checkboxes and other field types
            # PyPDF2's API for this is limited, but we can try
            try:
                # Access the root to find AcroForm
                if hasattr(reader, 'trailer') and reader.trailer:
                    root = reader.trailer.get('/Root', {})
                    if '/AcroForm' in root:
                        acro_form = root['/AcroForm']
                        if '/Fields' in acro_form:
                            fields_array = acro_form['/Fields']
                            # Process fields array to find checkboxes and other types
                            # This is a simplified approach - PyPDF2's field access is limited
                            logger.debug("Found AcroForm with fields")
            except Exception as e:
                logger.debug(f"Could not access AcroForm fields: {e}")
            
            # If we found fields, return them
            if form_fields:
                return form_fields
            
            # If no fields found, log a warning
            logger.warning("No form fields detected in PDF - document may not have interactive form fields")
            return []
            
        except Exception as e:
            logger.error(f"Error detecting form fields: {e}")
            return []
    
    @staticmethod
    def get_field_mapping() -> Dict[str, List[str]]:
        """
        Get mapping of common PDF field name patterns to Memory Graph fact keys.
        
        This mapping enables the system to recognize various field name formats
        used in different PDF forms and map them to standardized fact keys.
        
        Structure:
        - Key: Memory Graph fact key (canonical field name)
        - Value: List of PDF field name patterns that map to this fact key
        
        Matching Strategy:
        1. Patterns are normalized (lowercase, spaces instead of underscores/dashes)
        2. Matching is case-insensitive and handles common separators
        3. Supports exact, partial, and word-based matching
        
        Returns:
            Dictionary mapping fact keys to lists of PDF field name patterns
            
        Example:
            {
                "company_name": ["company_name", "company name", "business_name", ...],
                "ein": ["ein", "employer_id", "tax_id", ...]
            }
        """
        return {
            # Company name variations
            # Maps various ways companies name their "company name" field
            "company_name": [
                "company_name", "company name", 
                "business_name", "business name", 
                "legal_name", "legal name", 
                "entity_name", "entity name",
                "name_of_company", "name of company",
                "company", "business", "entity"
            ],
            
            # EIN (Employer Identification Number) variations
            # Maps various tax ID field names
            "ein": [
                "ein", 
                "employer_id", "employer id", 
                "tax_id", "tax id", "taxid",
                "federal_id", "federal id", 
                "fein", 
                "employer_identification_number", "employer identification number",
                "federal_tax_id", "federal tax id"
            ],
            
            # Address line 1 variations
            # Maps street address fields
            "address_line_1": [
                "address", 
                "street_address", "street address", 
                "address_line_1", "address line 1", 
                "address1", 
                "street", 
                "mailing_address", "mailing address",
                "physical_address", "physical address"
            ],
            
            # City (simple, usually consistent)
            "city": ["city"],
            
            # State/Province variations
            "state": ["state", "province"],
            
            # ZIP/Postal code variations
            "zip_code": [
                "zip", 
                "zip_code", "zip code", 
                "postal_code", "postal code",
                "zipcode", "postalcode",
                "postal"
            ],
            
            # Phone number variations
            "phone": [
                "phone", 
                "phone_number", "phone number", 
                "telephone", "tel",
                "contact_phone", "contact phone",
                "phone_num", "phone num"
            ],
            
            # Email variations
            "email": [
                "email", 
                "email_address", "email address", 
                "e_mail", "e-mail",
                "email_addr", "email addr"
            ],
            
            # Website variations
            "website": [
                "website", 
                "web_site", "web site", 
                "url", 
                "homepage"
            ],
            
            # Incorporation date variations
            "incorporation_date": [
                "incorporation_date", "incorporation date", 
                "date_of_incorporation", "date of incorporation", 
                "inc_date", "inc date",
                "date_incorporated", "date incorporated"
            ],
            
            # State of incorporation variations
            "state_of_incorporation": [
                "state_of_incorporation", "state of incorporation",
                "incorporation_state", "incorporation state", 
                "inc_state", "inc state", 
                "state_incorporated", "state incorporated",
                "incorporated_in", "incorporated in"
            ]
        }
    
    @staticmethod
    def match_field_to_fact_key(pdf_field_name: str) -> Optional[str]:
        """
        Match a PDF form field name to a Memory Graph fact key.
        
        Uses a three-tier matching strategy to handle variations:
        1. Exact match: Direct pattern match
        2. Partial match: Substring matching
        3. Word matching: Significant word overlap
        
        Args:
            pdf_field_name: Name of the PDF form field (e.g., "company_name", "employer_id")
            
        Returns:
            Matched fact key (e.g., "company_name", "ein"), or None if no match found
            
        Examples:
            - "company_name" → "company_name" (exact match)
            - "employer_id" → "ein" (pattern match)
            - "street_address" → "address_line_1" (pattern match)
            - "phone_number" → "phone" (pattern match)
            
        TODO: Enhance matching:
        1. Use fuzzy string matching (fuzzywuzzy, rapidfuzz) for typos
        2. Use ML-based field name classification
        3. Learn from user corrections
        4. Handle abbreviations and variations better
        """
        if not pdf_field_name:
            return None
        
        # Step 1: Normalize field name for matching
        # Convert to lowercase, remove underscores/dashes, trim whitespace
        normalized = pdf_field_name.lower().strip().replace("_", " ").replace("-", " ")
        
        # Get field mapping dictionary
        mapping = PDFFormDetector.get_field_mapping()
        
        # Step 2: Try exact match first (fastest, most accurate)
        # Check if normalized name is in any pattern list
        for fact_key, patterns in mapping.items():
            if normalized in patterns:
                logger.debug(f"Exact match: '{pdf_field_name}' → '{fact_key}'")
                return fact_key
        
        # Step 3: Try partial match (handles variations)
        # Check if normalized name contains any pattern, or vice versa
        for fact_key, patterns in mapping.items():
            for pattern in patterns:
                if pattern in normalized or normalized in pattern:
                    logger.debug(f"Partial match: '{pdf_field_name}' → '{fact_key}' (pattern: '{pattern}')")
                    return fact_key
        
        # Step 4: Try word-by-word matching (handles multi-word variations)
        # Split into words and check for significant overlap (2+ words)
        words = normalized.split()
        for fact_key, patterns in mapping.items():
            for pattern in patterns:
                pattern_words = pattern.split()
                # Check if at least 2 significant words match
                common_words = set(words) & set(pattern_words)
                if len(common_words) >= 2:
                    logger.debug(f"Word match: '{pdf_field_name}' → '{fact_key}' (common words: {common_words})")
                    return fact_key
        
        # No match found
        logger.debug(f"No match found for PDF field: '{pdf_field_name}' (normalized: '{normalized}')")
        return None
    
    @staticmethod
    def is_pdf(file_content: bytes) -> bool:
        """
        Check if file content is a PDF.
        
        Args:
            file_content: Binary file content
            
        Returns:
            True if file appears to be a valid PDF
        """
        return file_content.startswith(b"%PDF-")

