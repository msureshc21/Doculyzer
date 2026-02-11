# LLM-Based Field Extraction Service

## Overview

The LLM-based field extraction service extracts structured company information from document text using a Large Language Model. It takes parsed document text as input and returns structured JSON with extracted fields, confidence scores, and source text spans.

## Architecture

```
Document Text
    ↓
Prompt Template (build_extraction_prompt)
    ↓
LLM Service (LLMExtractor)
    ↓
Schema Validation (ExtractionResult)
    ↓
Extracted Fields (saved to database)
```

## Components

### 1. Extraction Schemas (`app/schemas/extraction.py`)

**TextSpan**: Represents a span of text in the source document
- `start`: Start character position
- `end`: End character position
- `text`: The actual text span

**ExtractedFieldOutput**: Single extracted field with metadata
- `field_name`: Name of the field (e.g., 'company_name', 'ein')
- `value`: Extracted value
- `confidence`: Confidence score (0.0 to 1.0)
- `source_span`: TextSpan showing where value was found
- `field_type`: Type of field (text, number, date, address)
- `notes`: Optional notes about extraction

**ExtractionResult**: Complete extraction result
- `fields`: List of ExtractedFieldOutput
- `extraction_method`: Method used (e.g., 'llm', 'llm_stub')

### 2. Prompt Template (`app/services/prompts.py`)

The prompt template includes:
- List of fields to extract with descriptions
- Instructions for extraction
- Format requirements (JSON)
- Example output structure

**Supported Fields**:
- `company_name`: Legal name of company
- `ein`: Employer Identification Number
- `address_line_1`, `address_line_2`: Street address
- `city`, `state`, `zip_code`: Location information
- `phone`, `email`, `website`: Contact information
- `incorporation_date`: Date of incorporation
- `state_of_incorporation`: State where incorporated

### 3. LLM Extractor Service (`app/services/llm_extractor.py`)

**LLMExtractor.extract_fields(document_text: str) -> ExtractionResult**

Process:
1. Build prompt using `build_extraction_prompt()`
2. Call LLM API (currently stubbed)
3. Parse JSON response
4. Validate against ExtractionResult schema
5. Return validated result

**Current Implementation**: Stubbed for development
- Returns basic extraction based on simple heuristics
- Logs warning about stub usage
- TODO comments indicate where to add actual LLM call

### 4. Field Extractor Orchestrator (`app/services/field_extractor.py`)

**FieldExtractor.extract_fields_from_document()**

Orchestrates the full pipeline:
1. Extract text from document (PDF, etc.)
2. Use LLM to extract structured fields
3. Save extracted fields to database as `ExtractedField` records

## Usage

### Basic Usage

```python
from app.services.llm_extractor import LLMExtractor

document_text = """
ACME CORPORATION
123 Business Street
New York, NY 10001
EIN: 12-3456789
"""

result = LLMExtractor.extract_fields(document_text)

for field in result.fields:
    print(f"{field.field_name}: {field.value}")
    print(f"  Confidence: {field.confidence}")
    print(f"  Source: {field.source_span.text}")
```

### Integration with Document Upload

The field extraction is automatically triggered during document upload:

```python
# In documents.py upload endpoint
if text_extracted and extracted_text:
    extracted_fields = FieldExtractor.extract_fields_from_document(
        document_id=document.id,
        db=db,
        file_content=file_content
    )
```

## Output Format

```json
{
  "fields": [
    {
      "field_name": "company_name",
      "value": "Acme Corporation",
      "confidence": 0.95,
      "source_span": {
        "start": 0,
        "end": 18,
        "text": "Acme Corporation"
      },
      "field_type": "text",
      "notes": "Found in document header"
    },
    {
      "field_name": "ein",
      "value": "12-3456789",
      "confidence": 0.98,
      "source_span": {
        "start": 50,
        "end": 60,
        "text": "12-3456789"
      },
      "field_type": "text",
      "notes": null
    }
  ],
  "extraction_method": "llm"
}
```

## Validation

The service validates:
- **JSON Structure**: Response must be valid JSON
- **Schema Compliance**: Must match ExtractionResult schema
- **Confidence Range**: Must be between 0.0 and 1.0
- **Text Span Validity**: End position must be after start position
- **Field Types**: Must match expected types

## Error Handling

- **Empty Text**: Raises ValueError if document text is empty
- **JSON Parse Errors**: Logged and raised as ValueError
- **Validation Errors**: Logged with details, raised as ValueError
- **LLM API Errors**: Should be handled with retries (TODO)

## TODOs for Production

### LLM Integration

Replace `_stub_llm_call()` in `llm_extractor.py` with actual LLM API call:

**Option 1: OpenAI**
```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert at extracting structured data."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1,
    response_format={"type": "json_object"}  # If supported
)
return response.choices[0].message.content
```

**Option 2: Anthropic Claude**
```python
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}]
)
return message.content[0].text
```

**Option 3: Local LLM (Ollama)**
```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    }
)
return response.json()["response"]
```

### Additional Improvements

1. **Retry Logic**: Add retries for rate limits and transient errors
2. **Streaming**: Support streaming responses for long documents
3. **Chunking**: Split long documents into chunks for processing
4. **Caching**: Cache extraction results for identical documents
5. **Cost Tracking**: Track API usage and costs
6. **Fallback**: Use rule-based extraction if LLM fails
7. **Confidence Calibration**: Improve confidence score accuracy
8. **Multi-language**: Support documents in different languages

## Testing

Run the test script:
```bash
cd backend
source venv/bin/activate
python test_extraction.py
```

Tests cover:
- Prompt template generation
- LLM extraction (stubbed)
- Schema validation
- Error handling

## Configuration

Environment variables (future):
- `LLM_PROVIDER`: openai, anthropic, ollama, etc.
- `LLM_MODEL`: Model name (e.g., gpt-4, claude-3-opus)
- `LLM_API_KEY`: API key for LLM provider
- `LLM_TEMPERATURE`: Temperature setting (default: 0.1)
- `LLM_MAX_TOKENS`: Maximum tokens in response

## Example: Adding a New Field

1. Add field definition to `app/services/prompts.py`:
```python
{
    "name": "dba_name",
    "description": "Doing Business As name",
    "type": "text",
    "examples": ["Acme DBA", "Trade Name Inc."]
}
```

2. The prompt will automatically include it
3. LLM will extract it if found in document
4. Field will be saved to database

## Performance Considerations

- **Latency**: LLM calls can take 1-10 seconds depending on provider
- **Cost**: Each extraction costs API credits (track usage)
- **Rate Limits**: Implement rate limiting and queuing for high volume
- **Caching**: Cache results for identical document text

