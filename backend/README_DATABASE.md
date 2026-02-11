# Database Setup Guide

## Quick Start

### 1. Create PostgreSQL Database

```bash
# Using psql
createdb paperwork_copilot

# Or using SQL
psql -U postgres
CREATE DATABASE paperwork_copilot;
```

### 2. Configure Database URL

Edit `backend/.env`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/paperwork_copilot
```

### 3. Initialize Database

**Option A: Using Python (SQLAlchemy)**
```bash
cd backend
source venv/bin/activate
python -m app.db.init_db
```

**Option B: Using SQL Script**
```bash
psql -U username -d paperwork_copilot -f schema.sql
```

### 4. Verify Setup

```bash
python scripts/test_db.py
```

## Schema Overview

The database consists of 4 main tables:

1. **documents** - Uploaded document metadata
2. **extracted_fields** - Raw field extractions from documents
3. **company_facts** - Canonical company facts (memory graph)
4. **fact_history** - Complete audit trail of fact changes

See `docs/DATABASE_SCHEMA.md` for detailed design documentation.

## Using the Models

```python
from app.db.database import SessionLocal
from app.models import Document, CompanyFact

db = SessionLocal()

# Create a document
doc = Document(
    filename="example.pdf",
    file_path="./uploads/example.pdf",
    file_type="pdf",
    file_size=1024
)
db.add(doc)
db.commit()

# Query facts
facts = db.query(CompanyFact).filter(CompanyFact.status == "active").all()
```

## Next Steps

- Set up Alembic for migrations (recommended for production)
- Add database connection pooling configuration
- Implement repository pattern for data access

