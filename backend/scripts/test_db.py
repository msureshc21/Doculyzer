#!/usr/bin/env python3
"""
Test script to verify database schema and models.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import engine, SessionLocal
from app.models import Document, ExtractedField, CompanyFact, FactHistory
from app.models.fact_history import ChangeType
from datetime import datetime


def test_database():
    """Test database connection and model creation."""
    print("Testing database connection...")
    
    # Test connection
    try:
        with engine.connect() as conn:
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    # Test model imports
    print("\nTesting model imports...")
    try:
        print(f"✓ Document model imported")
        print(f"✓ ExtractedField model imported")
        print(f"✓ CompanyFact model imported")
        print(f"✓ FactHistory model imported")
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False
    
    # Test creating a sample record
    print("\nTesting model creation...")
    db = SessionLocal()
    try:
        # Create a test document
        test_doc = Document(
            filename="test_document.pdf",
            file_path="./uploads/test_document.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf",
            processed="completed"
        )
        db.add(test_doc)
        db.commit()
        db.refresh(test_doc)
        print(f"✓ Created test document (ID: {test_doc.id})")
        
        # Create a test extracted field
        test_field = ExtractedField(
            document_id=test_doc.id,
            field_name="company_name",
            field_type="text",
            value="Test Company Inc.",
            confidence=0.95,
            extraction_method="ai_model"
        )
        db.add(test_field)
        db.commit()
        db.refresh(test_field)
        print(f"✓ Created test extracted field (ID: {test_field.id})")
        
        # Create a test company fact
        test_fact = CompanyFact(
            fact_key="company_name",
            fact_category="company_info",
            fact_value="Test Company Inc.",
            confidence=0.95,
            source_document_id=test_doc.id,
            source_field_id=test_field.id,
            last_edited_by="system"
        )
        db.add(test_fact)
        db.commit()
        db.refresh(test_fact)
        print(f"✓ Created test company fact (ID: {test_fact.id})")
        
        # Create a test history entry
        test_history = FactHistory(
            fact_id=test_fact.id,
            change_type=ChangeType.EXTRACTION,
            changed_by="system",
            old_value=None,
            new_value="Test Company Inc.",
            new_confidence="0.95",
            reason="Initial extraction from document"
        )
        db.add(test_history)
        db.commit()
        db.refresh(test_history)
        print(f"✓ Created test history entry (ID: {test_history.id})")
        
        # Test relationships
        print("\nTesting relationships...")
        assert len(test_doc.extracted_fields) == 1, "Document should have 1 extracted field"
        assert len(test_doc.company_facts) == 1, "Document should have 1 company fact"
        assert len(test_fact.history) == 1, "Fact should have 1 history entry"
        print("✓ All relationships working correctly")
        
        # Cleanup
        db.delete(test_history)
        db.delete(test_fact)
        db.delete(test_field)
        db.delete(test_doc)
        db.commit()
        print("\n✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ Model creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)

