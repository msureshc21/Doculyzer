# Visual Demo Guide

## Quick Start

Both servers should now be running:
- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs

## Demo Flow

### Step 1: View API Documentation

Open http://localhost:8000/docs in your browser to see:
- All available endpoints
- Interactive API testing
- Request/response schemas

### Step 2: Check Health

```bash
curl http://localhost:8000/api/v1/health
```

### Step 3: Upload a Document

**Using the API:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@test_document.pdf" \
  -F "description=Test document"
```

**Response includes:**
- Document ID
- File path
- Upload status
- Text extraction status

### Step 4: View Extracted Facts

```bash
# List all facts
curl http://localhost:8000/api/v1/facts

# Get specific fact
curl http://localhost:8000/api/v1/facts/company_name

# Get fact with history
curl http://localhost:8000/api/v1/facts/company_name/history
```

### Step 5: Auto-Fill a PDF

```bash
curl -X POST "http://localhost:8000/api/v1/autofill/autofill" \
  -F "file=@form.pdf" \
  -F "generate_preview=true"
```

**Response includes:**
- Fields detected
- Fields matched
- Fields filled
- Explanations for each field
- Path to filled PDF preview

### Step 6: View Frontend

Open http://localhost:5173 in your browser to see:
- Current frontend UI
- Backend connection status

## Testing Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. List Documents
```bash
curl http://localhost:8000/api/v1/documents
```

### 3. List Facts
```bash
curl http://localhost:8000/api/v1/facts
```

### 4. Detect PDF Fields
```bash
curl -X POST "http://localhost:8000/api/v1/autofill/detect-fields" \
  -F "file=@form.pdf"
```

## Frontend UI

The frontend is available at http://localhost:5173

Current features:
- Backend health status indicator
- Welcome message

**TODO:** Add UI components for:
- Document upload
- Fact viewing
- Auto-fill interface
- Explanation display

## Troubleshooting

### Backend not responding?
```bash
# Check if running
lsof -ti:8000

# Check logs (if running in terminal)
# Look for errors in the uvicorn output
```

### Frontend not loading?
```bash
# Check if running
lsof -ti:5173

# Check browser console for errors
```

### Database errors?
- Make sure PostgreSQL is running (or use SQLite for testing)
- Check DATABASE_URL in backend/.env

## Next Steps for Full Demo

1. **Upload a document** with company information
2. **View extracted fields** in the database
3. **See facts** in the Memory Graph
4. **Upload a PDF form** to auto-fill
5. **View explanations** for each filled field
6. **Download filled PDF** preview

