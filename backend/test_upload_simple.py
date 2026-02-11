#!/usr/bin/env python3
"""
Simple test script for document upload functionality.
Tests components directly without requiring server to be running.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Use SQLite for testing (no PostgreSQL required)
os.environ["DATABASE_URL"] = "sqlite:///./test_database.db"

from app.db.database import engine, Base, SessionLocal
from app.models import Document
from app.storage.filesystem import FileStorage
import uuid

def setup_test_db():
    """Initialize test database."""
    print("Setting up test database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Test database initialized\n")

def test_file_storage():
    """Test that file storage works."""
    print("=" * 60)
    print("TEST 1: File Storage")
    print("=" * 60)
    
    test_storage = FileStorage(base_path="./test_uploads")
    test_content = b"%PDF-1.4\nTest PDF Content"
    test_path = f"test_{uuid.uuid4().hex[:8]}.pdf"
    
    # Save file
    saved_path = test_storage.save(test_content, test_path)
    assert Path(saved_path).exists(), "File should be saved"
    print(f"✓ File saved to: {saved_path}")
    
    # Verify file content
    read_content = test_storage.read(test_path)
    assert read_content == test_content, "File content should match"
    print(f"✓ File content verified ({len(read_content)} bytes)")
    
    # Cleanup
    test_storage.delete(test_path)
    print("✓ Test file cleaned up\n")
    
    return True

def test_db_record():
    """Test that database record can be created."""
    print("=" * 60)
    print("TEST 2: Database Record Creation")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Create a test document record
        test_document = Document(
            filename="test_document.pdf",
            file_path="test_path.pdf",
            file_type="pdf",
            file_size=1024,
            mime_type="application/pdf",
            description="Test document",
            tags="test,upload",
            processed="completed"
        )
        
        db.add(test_document)
        db.commit()
        db.refresh(test_document)
        
        print(f"✓ Document record created")
        print(f"  ID: {test_document.id}")
        print(f"  Filename: {test_document.filename}")
        print(f"  File type: {test_document.file_type}")
        print(f"  File size: {test_document.file_size} bytes")
        print(f"  Processed: {test_document.processed}")
        
        # Verify we can query it back
        retrieved = db.query(Document).filter(Document.id == test_document.id).first()
        assert retrieved is not None, "Document should be retrievable"
        assert retrieved.filename == "test_document.pdf", "Filename should match"
        print(f"✓ Document record verified in database\n")
        
        return test_document.id
    finally:
        db.close()

def test_full_upload_flow():
    """Test the full upload flow: file storage + DB record."""
    print("=" * 60)
    print("TEST 3: Full Upload Flow")
    print("=" * 60)
    
    # Read test PDF
    test_pdf_path = Path("../test_document.pdf")
    if not test_pdf_path.exists():
        print(f"✗ Test PDF not found at {test_pdf_path}")
        print("  Creating minimal test PDF...")
        # Create minimal PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Size 1\n>>\nstartxref\n9\n%%EOF"
        test_pdf_path = Path("./test_document.pdf")
        test_pdf_path.write_bytes(pdf_content)
    
    file_content = test_pdf_path.read_bytes()
    file_size = len(file_content)
    
    print(f"✓ Test PDF loaded ({file_size} bytes)")
    
    # Store file
    storage = FileStorage()
    storage_path = f"documents/{uuid.uuid4().hex[:8]}.pdf"
    saved_path = storage.save(file_content, storage_path)
    print(f"✓ File saved to: {saved_path}")
    
    # Create DB record
    db = SessionLocal()
    try:
        document = Document(
            filename=test_pdf_path.name,
            file_path=storage_path,
            file_type="pdf",
            file_size=file_size,
            mime_type="application/pdf",
            description="Test upload",
            tags="test",
            processed="completed"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        print(f"✓ Database record created (ID: {document.id})")
        
        # Verify file still exists
        assert Path(saved_path).exists(), "File should still exist"
        print(f"✓ File verified on disk")
        
        # Verify DB record
        retrieved = db.query(Document).filter(Document.id == document.id).first()
        assert retrieved is not None, "Document should be in database"
        assert retrieved.file_size == file_size, "File size should match"
        print(f"✓ Database record verified")
        
        print(f"\n✓ Full upload flow successful!")
        print(f"  Document ID: {document.id}")
        print(f"  File path: {saved_path}")
        print(f"  File size: {file_size} bytes\n")
        
        return document.id
    finally:
        db.close()

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Document Upload Functionality Tests")
    print("=" * 60 + "\n")
    
    # Setup
    setup_test_db()
    
    try:
        # Test 1: File storage
        test_file_storage()
        
        # Test 2: DB record creation
        doc_id = test_db_record()
        
        # Test 3: Full flow
        full_doc_id = test_full_upload_flow()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ File storage works")
        print("  ✓ Database records can be created")
        print("  ✓ Full upload flow (file + DB) works")
        print(f"\nTest document ID: {full_doc_id}")
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

