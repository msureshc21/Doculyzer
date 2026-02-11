# Company Memory Graph Service

## Overview

The Company Memory Graph service maintains canonical company facts by processing extracted fields, resolving conflicts, and tracking complete history of all changes.

## Architecture

```
Extracted Fields (from documents)
    ↓
Memory Graph Service
    ↓
Conflict Resolution
    ↓
Company Facts (canonical)
    ↓
Fact History (audit trail)
```

## Conflict Resolution Rules

The service uses a clear priority system for resolving conflicts:

### Priority Order

1. **User Edits (Highest Priority)**
   - User-edited facts are never overwritten by system extractions
   - User edits have confidence = 1.0
   - Tracked with `edit_count` and `last_edited_by`

2. **Higher Confidence Wins**
   - If confidence difference > 0.1, higher confidence wins
   - Example: 0.95 vs 0.80 → 0.95 wins

3. **Newer Extraction Wins (Tie-Breaker)**
   - If confidence difference < 0.1, newer extraction wins
   - Example: 0.85 vs 0.82 → newer wins

4. **First Extraction Wins (Final Tie-Breaker)**
   - If same confidence and date, first extraction wins

### Examples

**Example 1: Higher Confidence**
```
Existing: company_name = "Acme Corp" (confidence: 0.75)
New:      company_name = "Acme Corporation" (confidence: 0.95)
Result:   Update to "Acme Corporation" (confidence difference: 0.20 > 0.1)
```

**Example 2: Similar Confidence, Newer Wins**
```
Existing: ein = "12-3456789" (confidence: 0.85, date: 2024-01-15)
New:      ein = "12-3456789" (confidence: 0.82, date: 2024-01-20)
Result:   Keep existing (newer has lower confidence, but difference < 0.1)
Actually: Update to new (newer extraction wins when confidence similar)
```

**Example 3: User Edit Protection**
```
Existing: company_name = "Acme Corp" (edit_count: 1, user-edited)
New:      company_name = "Acme Corporation" (confidence: 0.99)
Result:   Keep "Acme Corp" (user edits always win)
```

## Service Methods

### `process_extracted_fields(document_id, db)`

Processes all extracted fields from a document and updates the memory graph.

**Process:**
1. Get all extracted fields for the document
2. Group by field_name
3. For each field, pick best extraction (highest confidence)
4. Create or update canonical fact
5. Create history entries

**Returns:** List of created/updated CompanyFact records

### `update_fact_from_user_edit(fact_key, new_value, user_id, reason, db)`

Updates a fact from a user edit. User edits always take precedence.

**Process:**
1. Find existing fact
2. Check if value changed (normalized comparison)
3. Update fact with new value
4. Set confidence to 1.0 (user edits are authoritative)
5. Increment edit_count
6. Create history entry with change_type=USER_EDIT

**Returns:** Updated CompanyFact

### `get_fact(fact_key, db)`

Gets a canonical fact by key.

**Returns:** CompanyFact or None

### `get_all_facts(db, category=None)`

Gets all active canonical facts, optionally filtered by category.

**Returns:** List of CompanyFact records

### `get_fact_history(fact_id, db)`

Gets complete history for a fact (newest first).

**Returns:** List of FactHistory records

## History Tracking

Every change to a fact creates a history entry:

- **EXTRACTION**: Initial extraction from document
- **SYSTEM_UPDATE**: System updated fact (conflict resolution)
- **USER_EDIT**: User manually edited fact
- **MERGE**: Merged from multiple sources (future)
- **DEPRECATE**: Fact was deprecated (future)

History entries include:
- Old and new values
- Old and new confidence scores
- Who made the change
- When it changed
- Reason for change
- Source document (if applicable)

## API Endpoints

### GET `/api/v1/facts`

List all active company facts.

**Query Parameters:**
- `category`: Optional category filter

**Response:**
```json
{
  "facts": [...],
  "total": 42
}
```

### GET `/api/v1/facts/{fact_key}`

Get a specific fact by key.

**Response:**
```json
{
  "id": 1,
  "fact_key": "company_name",
  "fact_value": "Acme Corporation",
  "confidence": 0.95,
  ...
}
```

### GET `/api/v1/facts/{fact_key}/history`

Get a fact with its complete history.

**Response:**
```json
{
  "fact": {...},
  "history": [
    {
      "change_type": "extraction",
      "old_value": null,
      "new_value": "Acme Corp",
      "changed_at": "2024-01-15T10:00:00Z",
      ...
    },
    {
      "change_type": "user_edit",
      "old_value": "Acme Corp",
      "new_value": "Acme Corporation",
      "changed_at": "2024-01-16T14:30:00Z",
      ...
    }
  ]
}
```

### PUT `/api/v1/facts/{fact_key}`

Update a fact from a user edit.

**Request:**
```json
{
  "value": "New Company Name",
  "reason": "Corrected legal name"
}
```

**Response:**
```json
{
  "id": 1,
  "fact_key": "company_name",
  "fact_value": "New Company Name",
  "confidence": 1.0,
  "edit_count": 1,
  ...
}
```

## Integration

The memory graph service is automatically called after field extraction:

```python
# In field_extractor.py
extracted_fields = ...  # Extract fields
MemoryGraphService.process_extracted_fields(document_id, db)
```

This ensures that every document upload automatically updates the memory graph.

## Fact Categories

Facts are automatically categorized:

- `company_info`: company_name, dba_name
- `legal`: ein, tax_id, incorporation_date, state_of_incorporation
- `location`: address_line_1, address_line_2, city, state, zip_code
- `contact`: phone, email, website

## Normalization

Values are normalized for comparison:
- Converted to lowercase
- Stripped of whitespace
- Used to detect if values are actually different

This prevents unnecessary updates when values are semantically identical.

## Error Handling

- **Fact not found**: Raises ValueError (caught by API, returns 404)
- **Database errors**: Logged and re-raised
- **Validation errors**: Logged with details

## Future Enhancements

1. **Merge Strategy**: Merge multiple extractions into single fact
2. **Confidence Calibration**: Improve confidence score accuracy
3. **Field Relationships**: Link related facts (e.g., address components)
4. **Validation Rules**: Validate facts against known patterns (EIN format, etc.)
5. **Bulk Operations**: Process multiple documents in batch
6. **Fact Deprecation**: Mark facts as deprecated when superseded

