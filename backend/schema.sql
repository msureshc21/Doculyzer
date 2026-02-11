-- Company Memory Graph Database Schema
-- PostgreSQL schema for AI Paperwork Co-pilot

-- Documents table: Stores uploaded document metadata
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL UNIQUE,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed VARCHAR(20) NOT NULL DEFAULT 'pending',
    description TEXT,
    tags VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_processed ON documents(processed);
CREATE INDEX idx_documents_upload_date ON documents(upload_date);

-- ExtractedFields table: Stores raw field extractions from documents
CREATE TABLE IF NOT EXISTS extracted_fields (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(50),
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    extraction_method VARCHAR(50),
    extraction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    page_number INTEGER,
    bounding_box VARCHAR(100),
    context TEXT
);

CREATE INDEX idx_extracted_fields_document_id ON extracted_fields(document_id);
CREATE INDEX idx_extracted_fields_field_name ON extracted_fields(field_name);
CREATE INDEX idx_document_field ON extracted_fields(document_id, field_name);

-- CompanyFacts table: Stores canonical company facts (the "memory graph")
CREATE TABLE IF NOT EXISTS company_facts (
    id SERIAL PRIMARY KEY,
    fact_key VARCHAR(100) NOT NULL UNIQUE,
    fact_category VARCHAR(50),
    fact_value TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    source_document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    source_field_id INTEGER REFERENCES extracted_fields(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_edited_by VARCHAR(100),
    edit_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE INDEX idx_company_facts_fact_key ON company_facts(fact_key);
CREATE INDEX idx_company_facts_category ON company_facts(fact_category);
CREATE INDEX idx_company_facts_source_document ON company_facts(source_document_id);
CREATE INDEX idx_category_status ON company_facts(fact_category, status);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update updated_at on company_facts
CREATE TRIGGER update_company_facts_updated_at
    BEFORE UPDATE ON company_facts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- FactHistory table: Tracks all changes to company facts
CREATE TYPE change_type AS ENUM ('extraction', 'user_edit', 'system_update', 'merge', 'deprecate');

CREATE TABLE IF NOT EXISTS fact_history (
    id SERIAL PRIMARY KEY,
    fact_id INTEGER NOT NULL REFERENCES company_facts(id) ON DELETE CASCADE,
    change_type change_type NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_value TEXT,
    new_value TEXT NOT NULL,
    old_confidence VARCHAR(20),
    new_confidence VARCHAR(20),
    reason TEXT,
    source_document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL
);

CREATE INDEX idx_fact_history_fact_id ON fact_history(fact_id);
CREATE INDEX idx_fact_history_change_type ON fact_history(change_type);
CREATE INDEX idx_fact_history_changed_at ON fact_history(changed_at);
CREATE INDEX idx_fact_changed_at ON fact_history(fact_id, changed_at);

-- Comments for documentation
COMMENT ON TABLE documents IS 'Stores metadata for uploaded documents';
COMMENT ON TABLE extracted_fields IS 'Stores raw field extractions from documents with confidence scores';
COMMENT ON TABLE company_facts IS 'Canonical company facts - the single source of truth (memory graph)';
COMMENT ON TABLE fact_history IS 'Complete audit trail of all changes to company facts';

COMMENT ON COLUMN extracted_fields.confidence IS 'Confidence score from 0.0 (low) to 1.0 (high)';
COMMENT ON COLUMN company_facts.fact_key IS 'Unique identifier for the fact type (e.g., company_name, ein)';
COMMENT ON COLUMN company_facts.fact_value IS 'The canonical/authoritative value for this fact';
COMMENT ON COLUMN fact_history.change_type IS 'Type of change: extraction, user_edit, system_update, merge, or deprecate';

