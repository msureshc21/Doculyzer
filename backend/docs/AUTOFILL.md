# PDF Auto-Fill Service Documentation

## Overview

The PDF auto-fill service automatically fills PDF form fields using values from the Company Memory Graph, providing explainable metadata for each fill decision.

## Architecture

```
PDF Upload
    ↓
Form Field Detection
    ↓
Field Name Matching (PDF field → Memory Graph fact key)
    ↓
Value Retrieval (from Company Memory Graph)
    ↓
PDF Filling
    ↓
Explanation Metadata Generation
    ↓
Filled PDF Preview
```

## Components

### 1. PDF Form Field Detection (`pdf_form_detector.py`)

**Purpose:** Detect form fields (AcroForm fields) in PDF documents.

**Current Implementation:**
- Uses PyPDF2 for basic PDF reading
- Stubbed for development (returns empty list)
- TODO: Implement with pdfplumber for better detection

**Methods:**
- `detect_form_fields(pdf_content)`: Detects all form fields
- `match_field_to_fact_key(pdf_field_name)`: Matches PDF field names to Memory Graph fact keys
- `get_field_mapping()`: Returns mapping of common field name patterns

### 2. Field Matching

**Purpose:** Match PDF form field names to Memory Graph fact keys.

**Matching Strategy:**
1. **Exact match**: Check if normalized field name matches known patterns
2. **Partial match**: Check if field name contains known patterns
3. **Word matching**: Match significant words (2+ words in common)

**Example Mappings:**
- `"company_name"` → `company_name`
- `"employer_id"` → `ein`
- `"street_address"` → `address_line_1`
- `"phone_number"` → `phone`

### 3. Auto-Fill Service (`pdf_autofill.py`)

**Purpose:** Orchestrate the auto-fill process with explanations.

**Process:**
1. Detect form fields in PDF
2. For each field:
   - Match to Memory Graph fact key
   - Retrieve fact value
   - Generate explanation metadata
3. Fill PDF form fields
4. Generate filled PDF preview
5. Return results with explanations

### 4. Explanation Metadata

Each filled field includes:

```python
FieldExplanation {
    field_name: "company_name",  # PDF form field name
    fact_key: "company_name",     # Matched Memory Graph key
    value: "Acme Corporation",    # Value used
    confidence: 0.95,              # Confidence score
    source_document_id: 1,        # Source document ID
    source_document_name: "tax_form.pdf",  # Source document name
    reason: "User-verified value (edited 1 time(s)); Source: tax_form.pdf; Confidence: 0.95",
    matched: true                 # Whether match was successful
}
```

**Reason Components:**
- User verification status (if user-edited)
- Source document name
- Confidence score
- Extraction method

## API Endpoints

### POST `/api/v1/autofill/autofill`

Auto-fill a PDF form.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file (optional if `document_id` provided)
  - `document_id`: ID of uploaded document (optional if `file` provided)
  - `generate_preview`: Whether to generate filled PDF (default: true)

**Response:**
```json
{
  "filled_pdf_path": "previews/filled_abc123.pdf",
  "fields_detected": 8,
  "fields_matched": 6,
  "fields_filled": 6,
  "explanations": [
    {
      "field_name": "company_name",
      "fact_key": "company_name",
      "value": "Acme Corporation",
      "confidence": 0.95,
      "source_document_id": 1,
      "source_document_name": "tax_form.pdf",
      "reason": "Extracted from document; Source: tax_form.pdf; Confidence: 0.95",
      "matched": true
    }
  ],
  "success": true
}
```

### GET `/api/v1/autofill/preview/{file_path}`

Get filled PDF preview file.

**Response:**
- PDF file download

### POST `/api/v1/autofill/detect-fields`

Detect form fields in PDF (without filling).

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file

**Response:**
```json
{
  "fields_detected": 8,
  "fields": [
    {
      "name": "company_name",
      "type": "text",
      "value": null,
      "page": 0
    }
  ]
}
```

## Usage Examples

### Using File Upload

```bash
curl -X POST "http://localhost:8000/api/v1/autofill/autofill" \
  -F "file=@form.pdf" \
  -F "generate_preview=true"
```

### Using Document ID

```bash
curl -X POST "http://localhost:8000/api/v1/autofill/autofill" \
  -F "document_id=1" \
  -F "generate_preview=true"
```

### Python Example

```python
import requests

# Upload PDF and auto-fill
with open("form.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/autofill/autofill",
        files={"file": f},
        data={"generate_preview": True}
    )
    result = response.json()
    
    print(f"Fields detected: {result['fields_detected']}")
    print(f"Fields filled: {result['fields_filled']}")
    
    for explanation in result['explanations']:
        if explanation['matched']:
            print(f"{explanation['field_name']}: {explanation['value']}")
            print(f"  Reason: {explanation['reason']}")
    
    # Download filled PDF
    if result['filled_pdf_path']:
        preview_response = requests.get(
            f"http://localhost:8000/api/v1/autofill/preview/{result['filled_pdf_path']}"
        )
        with open("filled_form.pdf", "wb") as out:
            out.write(preview_response.content)
```

## Field Matching Examples

### Successful Matches

| PDF Field Name | Matched Fact Key | Match Type |
|---------------|------------------|------------|
| `company_name` | `company_name` | Exact |
| `employer_id` | `ein` | Pattern |
| `street_address` | `address_line_1` | Pattern |
| `phone_number` | `phone` | Pattern |
| `email_address` | `email` | Pattern |

### Unmatched Fields

- Fields with unusual names not in mapping
- Fields that don't correspond to company information
- Custom fields specific to the form

## Explanation Metadata

### Example Explanations

**User-Verified Value:**
```
"User-verified value (edited 2 time(s)); Source: business_license.pdf; Confidence: 1.00"
```

**System Extracted Value:**
```
"Extracted from document; Source: tax_form.pdf; Confidence: 0.92"
```

**No Match Found:**
```
"No match found for field name 'custom_field_123'"
```

**Match Found, No Value:**
```
"Fact 'website' not found in Memory Graph"
```

## Current Limitations

### Form Field Detection
- Currently stubbed (returns empty list)
- TODO: Implement with pdfplumber
- TODO: Detect field positions and types
- TODO: Handle nested fields

### PDF Filling
- Currently creates stub filled PDF
- TODO: Actually fill form fields
- TODO: Preserve form field properties
- TODO: Handle different field types (checkbox, dropdown, etc.)

### Field Matching
- Basic pattern matching
- TODO: Use fuzzy string matching
- TODO: ML-based classification
- TODO: Learn from user corrections

## Future Enhancements

1. **Better Form Detection:**
   - Use pdfplumber for robust field detection
   - Detect field positions and bounding boxes
   - Handle complex nested forms

2. **Enhanced Matching:**
   - Fuzzy string matching (fuzzywuzzy, rapidfuzz)
   - ML-based field name classification
   - Learn from user corrections

3. **Smart Filling:**
   - Validate values against field constraints
   - Handle different field types
   - Format values appropriately (dates, phone numbers, etc.)

4. **Visual Indicators:**
   - Highlight filled fields
   - Add annotations with explanations
   - Show confidence scores on PDF

5. **Batch Processing:**
   - Process multiple PDFs at once
   - Template-based filling
   - Reuse field mappings

## Error Handling

- **Invalid PDF:** Returns 400 error
- **No form fields:** Returns success with 0 fields detected
- **No matches:** Returns success with explanations showing no matches
- **Missing facts:** Returns success with explanations showing missing values
- **PDF generation failure:** Returns success but `filled_pdf_path` is null

## Configuration

No special configuration required. The service uses:
- `UPLOAD_DIR` for storing filled PDF previews
- Company Memory Graph for values
- Field mapping for name matching

