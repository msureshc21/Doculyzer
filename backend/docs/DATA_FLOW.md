# Data Flow Explanation

## Complete Data Flow: Document Upload → Company Memory Graph

This document explains how data flows through the system from document upload to the final Company Memory Graph.

---

## High-Level Flow

```
User uploads PDF
    ↓
File saved to disk
    ↓
Document metadata saved (documents table)
    ↓
PDF text extracted
    ↓
LLM extracts structured fields
    ↓
Extracted fields saved (extracted_fields table)
    ↓
Memory Graph Service processes fields
    ↓
Company facts created/updated (company_facts table)
    ↓
History entries created (fact_history table)
```

---

## Step-by-Step Flow

### Step 1: Document Upload

**Endpoint:** `POST /api/v1/documents/upload`

**What happens:**
1. User uploads a PDF file
2. File is validated (type, size, PDF signature)
3. File is saved to local storage using `FileStorage.save()`
4. Document metadata is saved to `documents` table

**Data created:**
```python
Document {
    id: 1,
    filename: "tax_form_2023.pdf",
    file_path: "uploads/uuid-generated.pdf",
    file_type: "pdf",
    file_size: 2048000,
    processed: "pending"
}
```

**Storage:**
- File: `./uploads/uuid-generated.pdf` (on disk)
- Metadata: `documents` table (in database)

---

### Step 2: Text Extraction

**Service:** `PDFExtractor.extract_text()`

**What happens:**
1. PDF file content is read
2. Text is extracted from PDF (currently stubbed)
3. Extracted text is returned as a string

**Data flow:**
```
PDF bytes → PDFExtractor → Text string
```

**Example output:**
```
"ACME CORPORATION
123 Business Street
New York, NY 10001
EIN: 12-3456789
Phone: (555) 123-4567"
```

**Note:** Currently stubbed - returns `None` until OCR is implemented.

---

### Step 3: LLM Field Extraction

**Service:** `LLMExtractor.extract_fields()`

**What happens:**
1. Document text is passed to LLM extractor
2. Prompt is built with field definitions
3. LLM extracts structured fields (currently stubbed)
4. Response is validated against schema
5. Returns `ExtractionResult` with structured fields

**Data flow:**
```
Text string → Prompt Template → LLM (stubbed) → JSON → Validation → ExtractionResult
```

**Example output:**
```python
ExtractionResult {
    fields: [
        {
            field_name: "company_name",
            value: "ACME CORPORATION",
            confidence: 0.92,
            source_span: {
                start: 0,
                end: 17,
                text: "ACME CORPORATION"
            },
            field_type: "text"
        },
        {
            field_name: "ein",
            value: "12-3456789",
            confidence: 0.95,
            source_span: {
                start: 50,
                end: 60,
                text: "12-3456789"
            }
        }
    ],
    extraction_method: "llm"
}
```

**Storage:** In-memory only at this point (not yet in database)

---

### Step 4: Save Extracted Fields

**Service:** `FieldExtractor.extract_fields_from_document()`

**What happens:**
1. For each field in `ExtractionResult.fields`:
   - Create `ExtractedField` record
   - Link to document
   - Save to database
2. All fields are committed together

**Data flow:**
```
ExtractionResult.fields → ExtractedField records → Database commit
```

**Data created:**
```python
ExtractedField {
    id: 1,
    document_id: 1,
    field_name: "company_name",
    value: "ACME CORPORATION",
    confidence: 0.92,
    extraction_method: "llm",
    context: "ACME CORPORATION"  # Source text span
}

ExtractedField {
    id: 2,
    document_id: 1,
    field_name: "ein",
    value: "12-3456789",
    confidence: 0.95,
    extraction_method: "llm",
    context: "12-3456789"
}
```

**Storage:** `extracted_fields` table (in database)

**Key point:** These are RAW extractions - multiple documents can have different values for the same field.

---

### Step 5: Process into Memory Graph

**Service:** `MemoryGraphService.process_extracted_fields()`

**What happens:**
1. Get all extracted fields for the document
2. Group by `field_name` (e.g., all "company_name" fields together)
3. For each field group:
   - Pick the best extraction (highest confidence)
   - Check if canonical fact exists
   - Apply conflict resolution rules
   - Create or update fact
   - Create history entry

**Data flow:**
```
ExtractedField records → Group by field_name → Pick best → Conflict resolution → CompanyFact
```

#### Scenario A: New Fact (No Existing Fact)

**Process:**
1. No existing fact found for `field_name`
2. Create new `CompanyFact`
3. Create history entry (EXTRACTION type)

**Data created:**
```python
CompanyFact {
    id: 1,
    fact_key: "company_name",
    fact_value: "ACME CORPORATION",
    confidence: 0.92,
    source_document_id: 1,
    source_field_id: 1,
    fact_category: "company_info",
    edit_count: 0,
    status: "active"
}

FactHistory {
    id: 1,
    fact_id: 1,
    change_type: "extraction",
    old_value: null,  # First creation
    new_value: "ACME CORPORATION",
    changed_by: "system",
    reason: "Initial extraction from document"
}
```

#### Scenario B: Update Existing Fact (Conflict Resolution)

**Process:**
1. Existing fact found: `company_name = "Acme Corp"` (confidence: 0.75)
2. New extraction: `company_name = "ACME CORPORATION"` (confidence: 0.92)
3. Conflict resolution:
   - Confidence difference: 0.92 - 0.75 = 0.17 > 0.1 threshold
   - **Decision:** Update to new value (higher confidence wins)
4. Update `CompanyFact`
5. Create history entry (SYSTEM_UPDATE type)

**Data updated:**
```python
CompanyFact {
    id: 1,
    fact_key: "company_name",
    fact_value: "ACME CORPORATION",  # Updated
    confidence: 0.92,  # Updated
    source_document_id: 1,  # Updated
    source_field_id: 1,  # Updated
    updated_at: "2024-01-20T10:30:00Z"  # Auto-updated
}

FactHistory {
    id: 2,
    fact_id: 1,
    change_type: "system_update",
    old_value: "Acme Corp",
    new_value: "ACME CORPORATION",
    old_confidence: "0.75",
    new_confidence: "0.92",
    changed_by: "system",
    reason: "New value has significantly higher confidence (0.92 vs 0.75)"
}
```

#### Scenario C: User-Edited Fact (Protected)

**Process:**
1. Existing fact: `company_name = "Acme Corp"` (edit_count: 1, user-edited)
2. New extraction: `company_name = "ACME CORPORATION"` (confidence: 0.99)
3. Conflict resolution:
   - Check: `edit_count > 0` → **TRUE**
   - **Decision:** Do NOT update (user edits always win)
4. Fact remains unchanged
5. Create history entry (EXTRACTION type) with reason explaining why not updated

**Data (unchanged):**
```python
CompanyFact {
    id: 1,
    fact_key: "company_name",
    fact_value: "Acme Corp",  # UNCHANGED
    confidence: 1.0,  # UNCHANGED (user edits = 1.0)
    edit_count: 1,  # UNCHANGED
    last_edited_by: "user_123"  # UNCHANGED
}

FactHistory {
    id: 3,
    fact_id: 1,
    change_type: "extraction",
    old_value: "Acme Corp",
    new_value: "ACME CORPORATION",
    changed_by: "system",
    reason: "Extraction attempted but not applied: Fact has been user-edited, preserving user value"
}
```

**Storage:**
- `company_facts` table: Canonical facts (one per `fact_key`)
- `fact_history` table: Complete audit trail

---

### Step 6: User Edit

**Endpoint:** `PUT /api/v1/facts/{fact_key}`

**What happens:**
1. User submits edit request with new value
2. Find existing fact
3. Check if value actually changed (normalized comparison)
4. Update fact:
   - Set `fact_value` to new value
   - Set `confidence` to 1.0 (user edits are authoritative)
   - Increment `edit_count`
   - Set `last_edited_by` to user ID
5. Create history entry (USER_EDIT type)

**Data flow:**
```
User request → Find fact → Update fact → Create history
```

**Data updated:**
```python
CompanyFact {
    id: 1,
    fact_key: "company_name",
    fact_value: "Acme Corporation Inc",  # Updated
    confidence: 1.0,  # Set to 1.0
    edit_count: 2,  # Incremented
    last_edited_by: "user_123",
    updated_at: "2024-01-21T14:00:00Z"
}

FactHistory {
    id: 4,
    fact_id: 1,
    change_type: "user_edit",
    old_value: "Acme Corp",
    new_value: "Acme Corporation Inc",
    old_confidence: "1.0",
    new_confidence: "1.0",
    changed_by: "user_123",
    reason: "User corrected to include Inc suffix"
}
```

**Key point:** User edits have `confidence = 1.0` and are protected from future system updates.

---

## Complete Example Flow

Let's trace a complete example:

### Document 1 Upload

1. **Upload:** `business_license.pdf`
2. **Text extracted:** "ACME CORP, 123 Main St, EIN: 12-3456789"
3. **LLM extracts:**
   - `company_name: "ACME CORP"` (confidence: 0.85)
   - `ein: "12-3456789"` (confidence: 0.90)
4. **Extracted fields saved:**
   - `extracted_fields` table: 2 records
5. **Memory graph updated:**
   - `company_facts` table: 2 new facts created
   - `fact_history` table: 2 entries (EXTRACTION)

**State:**
```
company_facts:
  - company_name: "ACME CORP" (confidence: 0.85, edit_count: 0)
  - ein: "12-3456789" (confidence: 0.90, edit_count: 0)
```

### Document 2 Upload

1. **Upload:** `tax_form.pdf`
2. **Text extracted:** "ACME CORPORATION, 123 Main Street, EIN: 12-3456789"
3. **LLM extracts:**
   - `company_name: "ACME CORPORATION"` (confidence: 0.95)
   - `ein: "12-3456789"` (confidence: 0.92)
4. **Extracted fields saved:**
   - `extracted_fields` table: 2 more records
5. **Memory graph updated:**
   - `company_name` fact updated (0.95 > 0.85)
   - `ein` fact NOT updated (0.92 < 0.90, but similar - newer wins? Actually, lower confidence, so no update)
   - `fact_history` table: 1 new entry (SYSTEM_UPDATE for company_name)

**State:**
```
company_facts:
  - company_name: "ACME CORPORATION" (confidence: 0.95, edit_count: 0)  # Updated
  - ein: "12-3456789" (confidence: 0.90, edit_count: 0)  # Unchanged
```

### User Edits Company Name

1. **User request:** Update `company_name` to "Acme Corporation Inc"
2. **Fact updated:**
   - Value: "Acme Corporation Inc"
   - Confidence: 1.0
   - Edit count: 1
3. **History entry created:** USER_EDIT type

**State:**
```
company_facts:
  - company_name: "Acme Corporation Inc" (confidence: 1.0, edit_count: 1)  # User-edited
  - ein: "12-3456789" (confidence: 0.90, edit_count: 0)
```

### Document 3 Upload (After User Edit)

1. **Upload:** `annual_report.pdf`
2. **LLM extracts:** `company_name: "ACME CORP"` (confidence: 0.99)
3. **Memory graph processing:**
   - Existing fact found (user-edited)
   - Conflict resolution: `edit_count > 0` → **DO NOT UPDATE**
   - History entry created with reason

**State:**
```
company_facts:
  - company_name: "Acme Corporation Inc" (confidence: 1.0, edit_count: 1)  # PROTECTED
  - ein: "12-3456789" (confidence: 0.90, edit_count: 0)

fact_history (for company_name):
  1. EXTRACTION: null → "ACME CORP"
  2. SYSTEM_UPDATE: "ACME CORP" → "ACME CORPORATION"
  3. USER_EDIT: "ACME CORPORATION" → "Acme Corporation Inc"
  4. EXTRACTION: "Acme Corporation Inc" → "ACME CORP" (attempted, not applied)
```

---

## Data Transformations

### Layer 1: Raw Document
- **Format:** PDF bytes
- **Storage:** File system
- **Table:** `documents` (metadata only)

### Layer 2: Extracted Text
- **Format:** Plain text string
- **Storage:** In-memory (temporary)
- **Source:** PDF extraction

### Layer 3: Structured Fields
- **Format:** `ExtractionResult` (Pydantic model)
- **Storage:** In-memory (temporary)
- **Source:** LLM extraction

### Layer 4: Extracted Fields (Database)
- **Format:** `ExtractedField` records
- **Storage:** `extracted_fields` table
- **Characteristics:** Multiple per document, can have conflicts

### Layer 5: Canonical Facts (Memory Graph)
- **Format:** `CompanyFact` records
- **Storage:** `company_facts` table
- **Characteristics:** One per `fact_key`, single source of truth

### Layer 6: History
- **Format:** `FactHistory` records
- **Storage:** `fact_history` table
- **Characteristics:** Immutable, append-only, complete audit trail

---

## Key Design Decisions

### Why Two Layers (Extracted Fields + Facts)?

**Extracted Fields:**
- Preserve all raw extractions
- Allow debugging and validation
- Support multiple values per field

**Canonical Facts:**
- Single source of truth
- Resolved conflicts
- User-verified values

### Why History Table?

- Complete audit trail
- Can see how values evolved
- Can potentially revert changes
- Compliance and debugging

### Why Conflict Resolution?

- Multiple documents may have different values
- Need automated way to pick best value
- User edits take precedence
- Clear rules prevent ambiguity

---

## Query Examples

### Get All Facts
```python
facts = MemoryGraphService.get_all_facts(db)
# Returns: List of CompanyFact (canonical values)
```

### Get Fact History
```python
history = MemoryGraphService.get_fact_history(fact_id, db)
# Returns: List of FactHistory (newest first)
# Shows: All changes, who made them, when, why
```

### Get Source Document
```python
fact = MemoryGraphService.get_fact("company_name", db)
document = fact.source_document  # Original document
extracted_field = fact.source_field  # Original extraction
```

---

## Summary

**Data flows in one direction:**
1. Document → Text → Structured Fields → Extracted Fields (raw)
2. Extracted Fields → Memory Graph Service → Company Facts (canonical)
3. Every change → History Entry (audit trail)

**Key principles:**
- **Raw layer:** Preserve everything (extracted_fields)
- **Canonical layer:** Single source of truth (company_facts)
- **History layer:** Complete audit trail (fact_history)
- **User edits:** Always win, never overwritten
- **Conflict resolution:** Clear rules, logged decisions

This design ensures data integrity, traceability, and user control.

