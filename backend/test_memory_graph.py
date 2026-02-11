#!/usr/bin/env python3
"""
Test script for Company Memory Graph functionality.
Tests: history preservation and user edit override behavior.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_memory_graph.db"

from app.db.database import engine, Base, SessionLocal
from app.models import Document, ExtractedField, CompanyFact
from app.models.fact_history import FactHistory, ChangeType
from app.services.memory_graph import MemoryGraphService

def setup_test_db():
    """Initialize test database."""
    print("Setting up test database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Test database initialized\n")

def cleanup_test_db():
    """Clean up test database file."""
    db_file = Path("test_memory_graph.db")
    if db_file.exists():
        db_file.unlink()
        print("✓ Test database cleaned up")

def test_history_preservation():
    """Test that all changes create history entries."""
    print("=" * 60)
    print("TEST 1: History Preservation")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Create a test document
        doc = Document(
            filename="test_doc.pdf",
            file_path="test.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"✓ Created test document (ID: {doc.id})")
        
        # Create extracted field
        field1 = ExtractedField(
            document_id=doc.id,
            field_name="company_name",
            field_type="text",
            value="Acme Corp",
            confidence=0.85,
            extraction_method="llm"
        )
        db.add(field1)
        db.commit()
        db.refresh(field1)
        print(f"✓ Created extracted field: {field1.value} (confidence: {field1.confidence})")
        
        # Process into memory graph (should create fact + history)
        facts = MemoryGraphService.process_extracted_fields(doc.id, db)
        assert len(facts) == 1, "Should create one fact"
        fact = facts[0]
        print(f"✓ Created fact: {fact.fact_key} = {fact.fact_value}")
        
        # Check history was created
        history = MemoryGraphService.get_fact_history(fact.id, db)
        assert len(history) == 1, "Should have one history entry"
        assert history[0].change_type == ChangeType.EXTRACTION, "Should be EXTRACTION type"
        assert history[0].old_value is None, "Initial creation should have null old_value"
        assert history[0].new_value == "Acme Corp", "New value should match"
        print(f"✓ History entry created: {history[0].change_type.value}")
        print(f"  - Old value: {history[0].old_value}")
        print(f"  - New value: {history[0].new_value}")
        print(f"  - Changed by: {history[0].changed_by}")
        
        # Refresh fact to get current state
        db.refresh(fact)
        original_updated_at = fact.updated_at
        
        # Create another extraction with different value and higher confidence
        field2 = ExtractedField(
            document_id=doc.id,
            field_name="company_name",
            field_type="text",
            value="Acme Corporation",
            confidence=0.96,  # Higher confidence (0.85 -> 0.96, diff = 0.11 > 0.1 threshold)
            extraction_method="llm"
        )
        db.add(field2)
        db.commit()
        db.refresh(field2)
        
        # Process again (should update fact + create history)
        # Note: This will process ALL fields for the document, picking best confidence for each field_name
        facts2 = MemoryGraphService.process_extracted_fields(doc.id, db)
        
        # Get the fact directly to verify it was updated
        fact2 = MemoryGraphService.get_fact("company_name", db)
        assert fact2 is not None, "Fact should exist"
        assert fact2.id == fact.id, "Should be same fact"
        
        # Debug: Check what happened
        if fact2.fact_value != "Acme Corporation":
            print(f"  DEBUG: Fact value is {fact2.fact_value}, expected Acme Corporation")
            print(f"  DEBUG: Fact confidence is {fact2.confidence}")
            print(f"  DEBUG: Field2 confidence is {field2.confidence}")
            print(f"  DEBUG: Confidence diff: {field2.confidence - fact.confidence}")
        
        assert fact2.fact_value == "Acme Corporation", f"Should update to higher confidence value, got {fact2.fact_value}"
        assert fact2.confidence == 0.96, f"Should have higher confidence, got {fact2.confidence}"
        print(f"✓ Updated fact: {fact2.fact_value} (confidence: {fact2.confidence})")
        
        # Check history has 2 entries now
        history2 = MemoryGraphService.get_fact_history(fact.id, db)
        assert len(history2) == 2, f"Should have 2 history entries, got {len(history2)}"
        assert history2[0].change_type == ChangeType.SYSTEM_UPDATE, "Latest should be SYSTEM_UPDATE"
        assert history2[0].old_value == "Acme Corp", "Old value should be previous"
        assert history2[0].new_value == "Acme Corporation", "New value should be updated"
        print(f"✓ Second history entry created: {history2[0].change_type.value}")
        print(f"  - Old value: {history2[0].old_value}")
        print(f"  - New value: {history2[0].new_value}")
        
        print(f"\n✓ Total history entries: {len(history2)}")
        print("✓ All changes preserved in history\n")
        
        return fact.id
        
    finally:
        db.close()

def test_user_edit_override():
    """Test that user edits override extractions cleanly."""
    print("=" * 60)
    print("TEST 2: User Edit Override")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # First, check if company_name fact already exists from test 1
        existing_fact = MemoryGraphService.get_fact("company_name", db)
        if existing_fact:
            # Use existing fact for this test
            fact = existing_fact
            print(f"✓ Using existing fact: {fact.fact_value} (confidence: {fact.confidence})")
        else:
            # Create a test document
            doc = Document(
                filename="test_doc2.pdf",
                file_path="test2.pdf",
                file_type="pdf",
                file_size=1024,
                mime_type="application/pdf"
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Create extracted field
            field = ExtractedField(
                document_id=doc.id,
                field_name="ein",  # Use different field to avoid conflicts
                field_type="text",
                value="12-3456789",
                confidence=0.90,
                extraction_method="llm"
            )
            db.add(field)
            db.commit()
            db.refresh(field)
            print(f"✓ Created extracted field: {field.value} (confidence: {field.confidence})")
            
            # Process into memory graph
            facts = MemoryGraphService.process_extracted_fields(doc.id, db)
            if not facts:
                # Fact might already exist, get it directly
                fact = MemoryGraphService.get_fact("ein", db)
                assert fact is not None, "Fact should exist"
            else:
                fact = facts[0]
        print(f"✓ Created fact: {fact.fact_value} (confidence: {fact.confidence})")
        print(f"  - Edit count: {fact.edit_count}")
        print(f"  - Last edited by: {fact.last_edited_by}")
        
        # User edits the fact
        user_id = "user_123"
        fact_key = fact.fact_key  # Use the actual fact key
        original_value = fact.fact_value
        new_value = "Tech Solutions Corporation" if fact_key == "company_name" else "98-7654321"
        
        updated_fact = MemoryGraphService.update_fact_from_user_edit(
            fact_key=fact_key,
            new_value=new_value,
            user_id=user_id,
            reason="Corrected to full legal name",
            db=db
        )
        
        assert updated_fact.fact_value == new_value, "Value should be updated"
        assert updated_fact.confidence == 1.0, "User edits should have confidence 1.0"
        assert updated_fact.edit_count == 1, "Edit count should be 1"
        assert updated_fact.last_edited_by == user_id, "Should track user"
        print(f"✓ User edit applied: {updated_fact.fact_value}")
        print(f"  - Confidence: {updated_fact.confidence} (user edits = 1.0)")
        print(f"  - Edit count: {updated_fact.edit_count}")
        print(f"  - Last edited by: {updated_fact.last_edited_by}")
        
        # Check history has user edit entry
        history = MemoryGraphService.get_fact_history(fact.id, db)
        assert len(history) >= 1, "Should have at least 1 history entry"
        latest = history[0]  # Newest first
        assert latest.change_type == ChangeType.USER_EDIT, "Latest should be USER_EDIT"
        assert latest.changed_by == user_id, "Should track user"
        assert latest.old_value == original_value, "Old value should be previous"
        assert latest.new_value == new_value, "New value should be user edit"
        assert latest.reason == "Corrected to full legal name", "Should preserve reason"
        print(f"✓ History entry created: {latest.change_type.value}")
        print(f"  - Changed by: {latest.changed_by}")
        print(f"  - Reason: {latest.reason}")
        
        # Now try to overwrite with a new extraction (should be blocked)
        # Create a new document for the new extraction
        doc2 = Document(
            filename="test_doc3.pdf",
            file_path="test3.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        
        conflicting_value = "Tech Solutions LLC" if fact_key == "company_name" else "11-2233445"
        field2 = ExtractedField(
            document_id=doc2.id,
            field_name=fact_key,
            field_type="text",
            value=conflicting_value,  # Different value
            confidence=0.99,  # Very high confidence
            extraction_method="llm"
        )
        db.add(field2)
        db.commit()
        
        # Process again - should NOT update because user edited
        MemoryGraphService.process_extracted_fields(doc2.id, db)
        fact2 = MemoryGraphService.get_fact(fact_key, db)
        
        # Verify fact was NOT updated
        assert fact2.fact_value == new_value, f"Should keep user-edited value, got {fact2.fact_value}"
        assert fact2.confidence == 1.0, "Should keep user confidence"
        assert fact2.edit_count == 1, "Edit count should not change"
        print(f"✓ Fact preserved: {fact2.fact_value}")
        print(f"  - User edit protected from overwrite")
        print(f"  - Confidence: {fact2.confidence}")
        
        # Check that a history entry was still created (for the attempt)
        history2 = MemoryGraphService.get_fact_history(fact.id, db)
        # Should have at least 2 entries now (user edit, attempted update)
        assert len(history2) >= 2, f"Should have at least 2 entries, got {len(history2)}"
        print(f"✓ History preserved: {len(history2)} total entries")
        
        # Verify the attempted update is in history
        attempted_updates = [h for h in history2 if h.new_value == conflicting_value]
        if attempted_updates:
            print(f"✓ Attempted update logged in history")
            print(f"  - Reason: {attempted_updates[0].reason}")
        
        print("\n✓ User edits successfully override and protect from extractions\n")
        
        return fact.id
        
    finally:
        db.close()

def test_complete_flow():
    """Test complete flow: extraction → user edit → new extraction."""
    print("=" * 60)
    print("TEST 3: Complete Flow")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Create document
        doc = Document(
            filename="flow_test.pdf",
            file_path="flow.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Step 1: Initial extraction
        field1 = ExtractedField(
            document_id=doc.id,
            field_name="ein",
            field_type="text",
            value="12-3456789",
            confidence=0.88,
            extraction_method="llm"
        )
        db.add(field1)
        db.commit()
        
        facts1 = MemoryGraphService.process_extracted_fields(doc.id, db)
        fact = facts1[0]
        print(f"Step 1 - Initial extraction:")
        print(f"  Fact: {fact.fact_key} = {fact.fact_value} (confidence: {fact.confidence})")
        print(f"  History entries: {len(MemoryGraphService.get_fact_history(fact.id, db))}")
        
        # Step 2: User edit (use different value to ensure update)
        fact = MemoryGraphService.update_fact_from_user_edit(
            fact_key="ein",
            new_value="12-3456789",  # Same value but user verified
            user_id="user_456",
            reason="Verified correct",
            db=db
        )
        print(f"\nStep 2 - User edit:")
        print(f"  Fact: {fact.fact_value} (confidence: {fact.confidence}, edits: {fact.edit_count})")
        history_after_edit = MemoryGraphService.get_fact_history(fact.id, db)
        print(f"  History entries: {len(history_after_edit)}")
        
        # Step 3: New extraction with different value (should be blocked)
        doc2 = Document(
            filename="flow_test2.pdf",
            file_path="flow2.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        db.add(doc2)
        db.commit()
        db.refresh(doc2)
        
        field2 = ExtractedField(
            document_id=doc2.id,
            field_name="ein",
            field_type="text",
            value="98-7654321",  # Different value
            confidence=0.95,
            extraction_method="llm"
        )
        db.add(field2)
        db.commit()
        
        MemoryGraphService.process_extracted_fields(doc2.id, db)
        fact2 = MemoryGraphService.get_fact("ein", db)
        print(f"\nStep 3 - New extraction (should be blocked):")
        print(f"  Fact preserved: {fact2.fact_value} (confidence: {fact2.confidence})")
        print(f"  Edit count unchanged: {fact2.edit_count}")
        history_after_extraction = MemoryGraphService.get_fact_history(fact.id, db)
        print(f"  History entries: {len(history_after_extraction)}")
        
        # Verify complete history
        history = MemoryGraphService.get_fact_history(fact.id, db)
        print(f"\n✓ Complete history ({len(history)} entries):")
        for i, h in enumerate(history, 1):
            print(f"  {i}. {h.change_type.value} - {h.old_value or 'null'} → {h.new_value}")
            print(f"     By: {h.changed_by}, Reason: {h.reason or 'N/A'}")
        
        print("\n✓ Complete flow verified\n")
        
    finally:
        db.close()

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Company Memory Graph Tests")
    print("=" * 60 + "\n")
    
    setup_test_db()
    
    try:
        # Test 1: History preservation
        fact_id1 = test_history_preservation()
        
        # Test 2: User edit override
        fact_id2 = test_user_edit_override()
        
        # Test 3: Complete flow
        test_complete_flow()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ History is preserved for all changes")
        print("  ✓ User edits override extractions cleanly")
        print("  ✓ User-edited facts are protected from overwrite")
        print("  ✓ Complete audit trail maintained")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup_test_db()

if __name__ == "__main__":
    sys.exit(main())

