"""
Prompt templates for LLM-based field extraction.
"""
from typing import Dict, Any


# List of fields we want to extract
EXTRACTION_FIELDS = [
    {
        "name": "company_name",
        "description": "The legal name of the company",
        "type": "text",
        "examples": ["Acme Corporation", "Tech Solutions Inc.", "ABC Company LLC"]
    },
    {
        "name": "ein",
        "description": "Employer Identification Number (EIN) or Tax ID",
        "type": "text",
        "examples": ["12-3456789", "12-3456789", "98-7654321"]
    },
    {
        "name": "address_line_1",
        "description": "Street address (first line)",
        "type": "address",
        "examples": ["123 Main Street", "456 Business Blvd", "789 Corporate Way"]
    },
    {
        "name": "address_line_2",
        "description": "Street address (second line, optional)",
        "type": "address",
        "examples": ["Suite 100", "Floor 5", "Building B"]
    },
    {
        "name": "city",
        "description": "City name",
        "type": "text",
        "examples": ["New York", "San Francisco", "Chicago"]
    },
    {
        "name": "state",
        "description": "State abbreviation or full name",
        "type": "text",
        "examples": ["NY", "California", "TX"]
    },
    {
        "name": "zip_code",
        "description": "ZIP or postal code",
        "type": "text",
        "examples": ["10001", "94102", "60601"]
    },
    {
        "name": "phone",
        "description": "Phone number",
        "type": "text",
        "examples": ["(555) 123-4567", "555-123-4567", "+1-555-123-4567"]
    },
    {
        "name": "email",
        "description": "Email address",
        "type": "text",
        "examples": ["contact@company.com", "info@example.org"]
    },
    {
        "name": "website",
        "description": "Company website URL",
        "type": "text",
        "examples": ["https://www.company.com", "www.example.org"]
    },
    {
        "name": "incorporation_date",
        "description": "Date of incorporation",
        "type": "date",
        "examples": ["2020-01-15", "January 15, 2020", "01/15/2020"]
    },
    {
        "name": "state_of_incorporation",
        "description": "State where company is incorporated",
        "type": "text",
        "examples": ["Delaware", "DE", "California", "CA"]
    }
]


def build_extraction_prompt(document_text: str) -> str:
    """
    Build the prompt for LLM field extraction.
    
    Args:
        document_text: The parsed text from the document
        
    Returns:
        Formatted prompt string
    """
    fields_description = "\n".join([
        f"- {field['name']}: {field['description']} (type: {field['type']})"
        for field in EXTRACTION_FIELDS
    ])
    
    prompt = f"""You are an expert at extracting structured information from business documents.

Your task is to extract company information from the following document text and return it as structured JSON.

Fields to extract:
{fields_description}

Instructions:
1. Read through the document text carefully
2. Extract values for each field that appears in the document
3. For each extracted field, provide:
   - field_name: The name of the field
   - value: The extracted value (normalized/cleaned)
   - confidence: Your confidence score (0.0 to 1.0) based on how clear and unambiguous the value is
   - source_span: The exact text span where you found the value, including:
     - start: Character position where the span starts
     - end: Character position where the span ends
     - text: The actual text from the document
   - field_type: The type of field (text, number, date, address)
   - notes: Optional notes about the extraction (e.g., "Found in header", "Unclear formatting")

4. Only extract fields that are clearly present in the document
5. If a field is not found, do not include it in the output
6. Be precise with source spans - they should match the exact text in the document
7. Normalize values (e.g., dates to YYYY-MM-DD format, phone numbers to consistent format)

Document text:
{document_text}

Return your response as a JSON object with this structure:
{{
  "fields": [
    {{
      "field_name": "company_name",
      "value": "Acme Corporation",
      "confidence": 0.95,
      "source_span": {{
        "start": 0,
        "end": 16,
        "text": "Acme Corporation"
      }},
      "field_type": "text",
      "notes": "Found in document header"
    }}
  ],
  "extraction_method": "llm"
}}

Important: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON."""
    
    return prompt


def get_field_definitions() -> list[Dict[str, Any]]:
    """
    Get the list of field definitions for extraction.
    
    Returns:
        List of field definition dictionaries
    """
    return EXTRACTION_FIELDS

