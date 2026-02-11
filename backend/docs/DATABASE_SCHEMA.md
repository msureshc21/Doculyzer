# Company Memory Graph - Database Schema Design

## Overview

The Company Memory Graph is designed to store and track company information extracted from documents, maintaining both raw extractions and canonical facts with full historical tracking.

## Design Philosophy

1. **Separation of Concerns**: Raw extractions are separate from canonical facts
2. **Audit Trail**: Complete history of all changes to facts
3. **Source Tracking**: Every fact can be traced back to its source document
4. **User Edits**: Support for manual corrections with full history
5. **Confidence Tracking**: Store confidence scores at every level

## Schema Structure

### 1. Documents Table

**Purpose**: Store metadata about uploaded documents.

**Key Fields**:
- `filename`: Original filename
- `file_path`: Storage path (abstracted via FileStorage)
- `file_type`: Document type (pdf, docx, etc.)
- `file_size`: Size in bytes
- `processed`: Status (pending, processing, completed, failed)

**Design Decisions**:
- Separate metadata from file storage (files stored via FileStorage abstraction)
- `processed` field allows tracking extraction pipeline status
- `tags` field for flexible categorization

### 2. ExtractedFields Table

**Purpose**: Store raw field extractions from documents (first layer of data).

**Key Fields**:
- `field_name`: Type of field extracted (e.g., 'company_name', 'ein')
- `value`: The extracted value
- `confidence`: Extraction confidence (0.0-1.0)
- `extraction_method`: How it was extracted (ocr, ai_model, manual)
- `context`: Surrounding text for validation

**Design Decisions**:
- **Raw Layer**: This is the "raw" extraction before it becomes canonical
- **Multiple Extractions**: Same field can be extracted multiple times from different documents
- **Context Preservation**: Store page number, bounding box, and context for traceability
- **Composite Index**: `(document_id, field_name)` for efficient lookups

### 3. CompanyFacts Table

**Purpose**: Store canonical company facts - the "memory graph" (single source of truth).

**Key Fields**:
- `fact_key`: Unique identifier (e.g., 'company_name', 'ein') - **UNIQUE constraint**
- `fact_value`: The authoritative/canonical value
- `confidence`: Overall confidence in the fact
- `source_document_id`: Original source document
- `source_field_id`: Original extracted field
- `edit_count`: Number of times manually edited
- `status`: active, deprecated, merged

**Design Decisions**:
- **Canonical Layer**: One fact per `fact_key` (UNIQUE constraint)
- **Source Tracking**: Links back to both document and extracted field
- **Edit Tracking**: `edit_count` and `last_edited_by` for user edit support
- **Status Field**: Allows deprecating/merging facts without deletion
- **Auto-update Timestamp**: `updated_at` automatically updated via trigger

### 4. FactHistory Table

**Purpose**: Complete audit trail of all changes to company facts.

**Key Fields**:
- `change_type`: extraction, user_edit, system_update, merge, deprecate
- `old_value` / `new_value`: Before and after values
- `old_confidence` / `new_confidence`: Confidence changes
- `changed_by`: User ID or 'system'
- `reason`: Optional explanation for the change

**Design Decisions**:
- **Complete History**: Never delete, only append (immutable audit log)
- **Change Types**: Enum ensures type safety and clear categorization
- **Bidirectional Tracking**: Store both old and new values for full context
- **Reason Field**: Allows users to add notes when editing
- **Time-based Index**: Efficient queries for "recent changes" or "fact timeline"

## Data Flow

```
Document Upload
    ↓
ExtractedField (raw extraction with confidence)
    ↓
CompanyFact (canonical fact - may merge multiple extractions)
    ↓
FactHistory (every change recorded)
```

## Example Use Cases

### 1. Document Upload and Extraction
1. Document uploaded → `documents` table
2. Fields extracted → `extracted_fields` table (multiple fields per document)
3. Facts created/updated → `company_facts` table
4. History entry → `fact_history` table (change_type='extraction')

### 2. User Edit
1. User edits a fact → `company_facts.fact_value` updated
2. `edit_count` incremented, `last_edited_by` set
3. History entry → `fact_history` table (change_type='user_edit', reason=user note)

### 3. Querying Facts
- Get all facts: `SELECT * FROM company_facts WHERE status='active'`
- Get fact history: `SELECT * FROM fact_history WHERE fact_id=? ORDER BY changed_at DESC`
- Find source: `SELECT d.* FROM documents d JOIN company_facts cf ON d.id=cf.source_document_id WHERE cf.fact_key=?`

## Indexes

**Performance Optimizations**:
- `documents.filename`: Fast document lookup
- `extracted_fields(document_id, field_name)`: Composite index for field queries
- `company_facts.fact_key`: UNIQUE index for canonical fact lookup
- `fact_history(fact_id, changed_at)`: Efficient history timeline queries
- `company_facts(fact_category, status)`: Category-based queries

## Future Considerations

1. **Migrations**: Use Alembic for schema versioning
2. **Soft Deletes**: Consider adding `deleted_at` for soft delete pattern
3. **Full-Text Search**: May need GIN indexes for text search on `fact_value`
4. **Partitioning**: `fact_history` could be partitioned by date for large datasets
5. **Relationships**: Consider fact-to-fact relationships (e.g., address components)

## Constraints and Validation

- `confidence` values: CHECK constraint ensures 0.0-1.0 range
- `fact_key` UNIQUE: Prevents duplicate canonical facts
- Foreign keys with CASCADE/SET NULL: Maintains referential integrity
- `change_type` ENUM: Type-safe change categorization

