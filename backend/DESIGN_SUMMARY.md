# Company Memory Graph - Design Summary

## Overview

The database schema implements a **two-layer architecture** for managing company information:

1. **Raw Layer** (`extracted_fields`): Stores initial extractions from documents
2. **Canonical Layer** (`company_facts`): Stores authoritative, verified facts

## Key Design Decisions

### 1. Separation of Raw and Canonical Data

**Why**: Raw extractions may have errors, low confidence, or conflicts. The canonical layer represents the "single source of truth" after processing, merging, and validation.

**Implementation**:
- `extracted_fields` table stores all raw extractions (multiple per document)
- `company_facts` table stores one fact per `fact_key` (UNIQUE constraint)
- Facts can be derived from multiple extractions or user edits

### 2. Complete Audit Trail

**Why**: Track every change to company facts for compliance, debugging, and user trust.

**Implementation**:
- `fact_history` table records every change (immutable append-only log)
- Tracks: old/new values, confidence changes, who changed it, when, and why
- Change types: `extraction`, `user_edit`, `system_update`, `merge`, `deprecate`

### 3. Source Tracking

**Why**: Users need to verify facts by checking source documents.

**Implementation**:
- `company_facts.source_document_id` → links to original document
- `company_facts.source_field_id` → links to specific extraction
- `fact_history.source_document_id` → tracks document that triggered change
- Foreign keys maintain referential integrity

### 4. Confidence Scores at Every Level

**Why**: Different extraction methods have different reliability. Users need to see confidence to make informed decisions.

**Implementation**:
- `extracted_fields.confidence`: Raw extraction confidence (0.0-1.0)
- `company_facts.confidence`: Overall fact confidence (may be higher after validation)
- `fact_history`: Tracks confidence changes over time
- CHECK constraints ensure valid ranges

### 5. User Edit Support

**Why**: Users must be able to correct errors and override system extractions.

**Implementation**:
- `company_facts.last_edited_by`: Tracks who made the edit
- `company_facts.edit_count`: Number of manual edits
- `fact_history.change_type='user_edit'`: Distinguishes user edits from extractions
- `fact_history.reason`: Allows users to add notes explaining edits

### 6. Historical Value Tracking

**Why**: Need to see how facts evolved over time and potentially revert changes.

**Implementation**:
- `fact_history.old_value` / `new_value`: Complete before/after tracking
- `fact_history.changed_at`: Timestamp for timeline queries
- Index on `(fact_id, changed_at)` for efficient history retrieval
- Relationship: `CompanyFact.history` provides ordered list of changes

## Schema Files

- **SQL Schema**: `schema.sql` - Raw PostgreSQL DDL
- **ORM Models**: `app/models/*.py` - SQLAlchemy models
- **Documentation**: `docs/DATABASE_SCHEMA.md` - Detailed design docs

## Data Flow Example

```
1. Document uploaded → `documents` table
2. AI extracts fields → `extracted_fields` table (confidence: 0.85)
3. System creates fact → `company_facts` table (fact_key='company_name')
4. History entry → `fact_history` (change_type='extraction')
5. User edits fact → `company_facts.fact_value` updated, `edit_count++`
6. History entry → `fact_history` (change_type='user_edit', reason='Corrected typo')
```

## Indexes for Performance

- `documents.filename`: Fast document lookup
- `extracted_fields(document_id, field_name)`: Composite index for field queries
- `company_facts.fact_key`: UNIQUE index for canonical fact lookup
- `fact_history(fact_id, changed_at)`: Efficient history timeline queries

## Extensibility

The schema is designed to be extended:
- Add new fact categories via `fact_category` field
- Support fact relationships (future: fact_relationships table)
- Add user authentication (future: link `last_edited_by` to users table)
- Support multiple companies (future: add `company_id` foreign key)

