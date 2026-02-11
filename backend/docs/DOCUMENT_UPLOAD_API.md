# Document Upload API Documentation

## Overview

The document upload API allows clients to upload PDF documents, which are stored locally, metadata saved to the database, text extracted (stub), and an internal event published.

## Endpoints

### POST `/api/v1/documents/upload`

Upload a PDF document.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file (required)
  - `description`: Optional text description
  - `tags`: Optional comma-separated tags

**Response:**
```json
{
  "message": "Document uploaded successfully",
  "document": {
    "id": 1,
    "filename": "example.pdf",
    "file_path": "uuid-generated-path.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "upload_date": "2024-01-15T10:30:00Z",
    "processed": "completed",
    "description": null,
    "tags": null
  },
  "text_extracted": false
}
```

**Status Codes:**
- `201 Created`: Document uploaded successfully
- `400 Bad Request`: Invalid file type, empty file, or invalid PDF
- `413 Payload Too Large`: File exceeds maximum size
- `500 Internal Server Error`: Server error during upload

### GET `/api/v1/documents/{document_id}`

Get document details by ID.

**Response:**
```json
{
  "id": 1,
  "filename": "example.pdf",
  "file_path": "uuid-generated-path.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "upload_date": "2024-01-15T10:30:00Z",
  "processed": "completed",
  "description": null,
  "tags": null
}
```

**Status Codes:**
- `200 OK`: Document found
- `404 Not Found`: Document not found

### GET `/api/v1/documents`

List all documents with pagination.

**Query Parameters:**
- `skip`: Number of documents to skip (default: 0)
- `limit`: Maximum number to return (default: 100)

**Response:**
```json
{
  "documents": [...],
  "total": 42
}
```

### DELETE `/api/v1/documents/{document_id}`

Delete a document and its associated file.

**Status Codes:**
- `204 No Content`: Document deleted successfully
- `404 Not Found`: Document not found

## Error Handling

The API includes comprehensive error handling:

1. **File Validation**:
   - Checks file extension (.pdf only)
   - Validates MIME type
   - Verifies PDF file signature
   - Checks file size limits

2. **Storage Errors**:
   - Handles file system errors gracefully
   - Rolls back database transaction if file storage fails
   - Cleans up files if database save fails

3. **Database Errors**:
   - Proper transaction rollback on errors
   - Detailed error logging

4. **Text Extraction Errors**:
   - Non-blocking: upload succeeds even if extraction fails
   - Logs warnings for debugging

## Implementation Details

### File Storage

- Files are stored using the `FileStorage` abstraction
- Unique filenames generated using UUID to prevent collisions
- Files stored in directory specified by `UPLOAD_DIR` config
- Relative paths stored in database for portability

### Text Extraction (Stub)

Currently implemented as a placeholder that:
- Validates PDF format
- Returns `None` (extraction not yet implemented)
- Logs warnings for debugging

**TODO: Implement actual extraction:**
- Use PyPDF2/pdfplumber for text-based PDFs
- Use Tesseract OCR for scanned PDFs
- Handle multi-page documents
- Return structured text with metadata

### Event Publishing

The `document_ingested` event is published after successful upload:
- Event type: `document_ingested`
- Payload includes: `document_id`, `filename`, `file_size`
- Currently logs events (TODO: implement message queue)

**TODO: Replace with proper event system:**
- Message queue (RabbitMQ, Redis)
- Event bus library
- Webhook support

## Example Usage

### Using curl

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@example.pdf" \
  -F "description=Tax form 2023" \
  -F "tags=tax,2023,important"

# Get document details
curl "http://localhost:8000/api/v1/documents/1"

# List all documents
curl "http://localhost:8000/api/v1/documents?skip=0&limit=10"

# Delete a document
curl -X DELETE "http://localhost:8000/api/v1/documents/1"
```

### Using Python requests

```python
import requests

# Upload document
with open("example.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={"file": f},
        data={"description": "Tax form 2023", "tags": "tax,2023"}
    )
    document = response.json()
    print(f"Uploaded document ID: {document['document']['id']}")

# Get document
response = requests.get(f"http://localhost:8000/api/v1/documents/{document_id}")
doc = response.json()
```

## Configuration

Environment variables (in `.env`):
- `UPLOAD_DIR`: Directory for file storage (default: `./uploads`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)

## TODOs for Future Improvements

1. **OCR Implementation**:
   - [ ] Add PyPDF2/pdfplumber for text extraction
   - [ ] Add Tesseract OCR for scanned PDFs
   - [ ] Store extracted text in database
   - [ ] Add confidence scores per page

2. **Event System**:
   - [ ] Implement message queue integration
   - [ ] Add event subscribers/handlers
   - [ ] Add event persistence for audit
   - [ ] Add retry logic for failed events

3. **Additional Features**:
   - [ ] Support for other file types (DOCX, images)
   - [ ] Async file processing
   - [ ] Progress tracking for large files
   - [ ] File versioning
   - [ ] Automatic field extraction pipeline trigger

