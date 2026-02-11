# Company Memory Graph Schema - Explained for New Engineers

## The Big Picture: What Problem Are We Solving?

Imagine you're building an AI assistant that helps companies fill out paperwork. The AI reads documents (like tax forms, business licenses, etc.) and extracts information like:
- Company name: "Acme Corp"
- EIN (tax ID): "12-3456789"
- Address: "123 Main St, New York, NY"

**The challenge**: 
- The AI might extract the same information from multiple documents
- Sometimes the AI makes mistakes (low confidence)
- Users need to correct errors
- We need to track where information came from
- We need to see how information changed over time

**Our solution**: A database that stores everything in layers, with a complete history.

---

## The Four Tables (Think of Them as Layers)

### Layer 1: Documents - "What Files Did We Upload?"

**Table: `documents`**

Think of this as a filing cabinet index card. It doesn't store the actual file, just information about it.

```python
# Example record:
{
    id: 1,
    filename: "tax_form_2023.pdf",
    file_path: "./uploads/tax_form_2023.pdf",
    file_type: "pdf",
    file_size: 2048000,  # 2MB
    upload_date: "2024-01-15",
    processed: "completed"  # pending → processing → completed
}
```

**Why this exists**: We need to know what documents we have, where they're stored, and whether we've processed them yet.

**Key fields**:
- `filename`: What the user called it
- `file_path`: Where we stored it on disk
- `processed`: Status of extraction (like a progress bar)

---

### Layer 2: Extracted Fields - "What Did the AI Find?"

**Table: `extracted_fields`**

This is where the AI dumps everything it finds. Think of it as a rough draft - it might have mistakes.

```python
# Example record:
{
    id: 1,
    document_id: 1,  # Links to the tax form above
    field_name: "company_name",
    value: "Acme Corp",
    confidence: 0.92,  # 92% sure this is correct
    extraction_method: "ai_model",
    page_number: 1
}
```

**Why this exists**: 
- The AI might extract "company_name" 5 times from the same document (different pages, different formats)
- We want to keep ALL extractions, even if they conflict
- Later, we'll pick the best one or merge them

**Key fields**:
- `field_name`: What type of information (like "company_name", "ein", "address")
- `value`: What the AI actually found
- `confidence`: How sure the AI is (0.0 = not sure, 1.0 = very sure)
- `document_id`: Which document this came from

**Important**: This table can have **duplicates**. Same field, same document, different values. That's okay - we'll resolve it later.

---

### Layer 3: Company Facts - "The Single Source of Truth"

**Table: `company_facts`**

This is the "memory graph" - the official, canonical information about the company. Think of it as the company's profile card.

```python
# Example record:
{
    id: 1,
    fact_key: "company_name",  # UNIQUE - only one per key!
    fact_value: "Acme Corporation",  # The official name
    confidence: 0.95,
    source_document_id: 1,  # Where we got it from
    source_field_id: 1,  # Which extraction we used
    created_at: "2024-01-15",
    updated_at: "2024-01-20",
    edit_count: 2,  # User edited it twice
    status: "active"
}
```

**Why this exists**:
- We need ONE answer to "What is the company name?"
- This is what the user sees and what we use for forms
- It's been validated, merged, or user-approved

**Key concept**: `fact_key` is **UNIQUE**. There can only be one `company_name` fact. If we extract it again, we UPDATE this record, not create a new one.

**The flow**:
1. AI extracts "Acme Corp" from document 1 → `extracted_fields` table
2. System creates fact → `company_facts` table with `fact_key="company_name"`
3. AI extracts "Acme Corporation" from document 2 → `extracted_fields` table
4. System sees conflict → Updates `company_facts` (maybe picks higher confidence, or asks user)
5. User edits to "Acme Corp Inc." → Updates `company_facts`, increments `edit_count`

---

### Layer 4: Fact History - "The Complete Story"

**Table: `fact_history`**

This is like a time machine. Every time a fact changes, we record it here. It's an **append-only log** - we never delete or modify records.

```python
# Example records (showing the timeline):

# Record 1: Initial extraction
{
    id: 1,
    fact_id: 1,  # Links to company_name fact
    change_type: "extraction",
    changed_by: "system",
    old_value: null,  # First time, so no old value
    new_value: "Acme Corp",
    changed_at: "2024-01-15"
}

# Record 2: User correction
{
    id: 2,
    fact_id: 1,
    change_type: "user_edit",
    changed_by: "user_123",
    old_value: "Acme Corp",
    new_value: "Acme Corporation",
    reason: "Full legal name",
    changed_at: "2024-01-16"
}

# Record 3: Another user edit
{
    id: 3,
    fact_id: 1,
    change_type: "user_edit",
    changed_by: "user_123",
    old_value: "Acme Corporation",
    new_value: "Acme Corp Inc.",
    reason: "Added Inc suffix",
    changed_at: "2024-01-20"
}
```

**Why this exists**:
- **Audit trail**: "Who changed what and when?"
- **Undo functionality**: "What was the value last week?"
- **Debugging**: "Why did the company name change?"
- **Compliance**: Some industries require complete change history

**Key concept**: This is **immutable**. Once a record is created, it never changes. We only add new records.

**Change types**:
- `extraction`: AI found it in a document
- `user_edit`: Human manually changed it
- `system_update`: System merged/updated automatically
- `merge`: Combined multiple extractions
- `deprecate`: Fact is no longer valid

---

## How They Work Together: A Real Example

Let's trace what happens when a user uploads a business license:

### Step 1: Document Upload
```python
# User uploads "business_license.pdf"
Document created:
  id: 5
  filename: "business_license.pdf"
  processed: "pending"
```

### Step 2: AI Extraction
```python
# AI processes the document and finds:
ExtractedField #1:
  document_id: 5
  field_name: "company_name"
  value: "Acme Corp"
  confidence: 0.88

ExtractedField #2:
  document_id: 5
  field_name: "ein"
  value: "12-3456789"
  confidence: 0.95

ExtractedField #3:
  document_id: 5
  field_name: "address"
  value: "123 Main St"
  confidence: 0.82
```

### Step 3: Create/Update Facts
```python
# System checks: Do we already have a "company_name" fact?
# Yes! Existing fact has value "Acme Corporation" (confidence 0.92)

# Decision: New extraction has lower confidence (0.88 < 0.92)
# Action: Keep existing fact, but record the new extraction in history

FactHistory created:
  fact_id: 1  # The existing company_name fact
  change_type: "extraction"
  old_value: "Acme Corporation"
  new_value: "Acme Corporation"  # No change, but we recorded the attempt
  reason: "New extraction from business_license.pdf had lower confidence"
```

### Step 4: User Edits
```python
# User sees the fact and corrects it:
CompanyFact updated:
  fact_key: "company_name"
  fact_value: "Acme Corp Inc."  # Changed!
  edit_count: 3  # Incremented
  last_edited_by: "user_123"

FactHistory created:
  fact_id: 1
  change_type: "user_edit"
  old_value: "Acme Corporation"
  new_value: "Acme Corp Inc."
  reason: "User corrected to include Inc suffix"
  changed_by: "user_123"
```

---

## Common Questions

### Q: Why not just store the final fact? Why keep extracted_fields?

**A**: Because:
- We might extract the same field multiple times (different pages, formats)
- We need to see all attempts to debug low confidence
- Users might want to see "the AI found X, Y, and Z - which is correct?"
- We can merge multiple extractions to increase confidence

### Q: What if two documents have different company names?

**A**: The system can:
1. Pick the one with higher confidence
2. Ask the user to choose
3. Create both as separate facts (if they're actually different - e.g., "legal_name" vs "dba_name")
4. Mark one as deprecated

### Q: Can I delete a fact?

**A**: You can mark it as `status="deprecated"` but the history remains. This preserves the audit trail.

### Q: What's the difference between `extracted_fields.confidence` and `company_facts.confidence`?

**A**: 
- `extracted_fields.confidence`: How sure the AI was when it extracted this specific value
- `company_facts.confidence`: Overall confidence after validation, merging, or user approval

Example:
- AI extracts "Acme" with 0.7 confidence → `extracted_fields`
- User confirms it's correct → `company_facts` confidence becomes 1.0 (user verified)

---

## Database Relationships (The Connections)

```
documents (1) ──→ (many) extracted_fields
    │                      │
    │                      │ (source_field_id)
    │                      ↓
    │              company_facts (1) ──→ (many) fact_history
    │                      ↑
    └──────────────────────┘ (source_document_id)
```

**Translation**:
- One document can have many extracted fields
- One document can be the source for many company facts
- One extracted field can become one company fact
- One company fact can have many history entries (every change)

---

## Indexes: Making Queries Fast

Think of indexes like a book's index - they help you find things quickly.

**Important indexes**:
- `documents.filename`: Find a document by name (fast!)
- `extracted_fields(document_id, field_name)`: "Show me all 'company_name' fields from document 5"
- `company_facts.fact_key`: Find a fact instantly (UNIQUE index)
- `fact_history(fact_id, changed_at)`: "Show me the history of company_name, newest first"

Without indexes, the database would scan every row (slow!). With indexes, it jumps straight to the right row (fast!).

---

## Summary: The Mental Model

1. **Documents** = Filing cabinet (what files we have)
2. **Extracted Fields** = Rough notes (everything the AI found, might be messy)
3. **Company Facts** = Official record (the clean, verified information)
4. **Fact History** = Time machine (every change, forever)

**The flow**: Document → Extract → Create/Update Fact → Record History

**The key insight**: We keep everything (raw extractions + history) so we can always trace back, debug, and understand how we got to the current state.

---

## Next Steps for You

1. **Look at the models**: Open `app/models/*.py` and see how they're defined
2. **Run the test**: `python scripts/test_db.py` to see it in action
3. **Try a query**: Use the models to create/read/update facts
4. **Read the code**: The models have comments explaining each field

Remember: This schema is designed to be **extensible**. As you learn more, you'll see how easy it is to add new fields, relationships, or features!

