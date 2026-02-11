#!/usr/bin/env python3
"""
Test script for document upload functionality.
Tests: upload, file storage, and database record creation.
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
from app.core.config import settings
import requests
import time

def setup_test_db():
    """Initialize test database."""
    print("Setting up test database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Test database initialized")

def cleanup_test_db():
    """Clean up test database file."""
    db_file = Path("test_database.db")
    if db_file.exists():
        db_file.unlink()
        print("✓ Test database cleaned up")

def test_file_storage():
    """Test that file storage works."""
    print("\n1. Testing file storage...")
    test_storage = FileStorage(base_path="./test_uploads")
    test_content = b"test file content"
    test_path = "test_file.pdf"
    
    # Save file
    saved_path = test_storage.save(test_content, test_path)
    assert Path(saved_path).exists(), "File should be saved"
    print(f"   ✓ File saved to: {saved_path}")
    
    # Read file
    read_content = test_storage.read(test_path)
    assert read_content == test_content, "File content should match"
    print("   ✓ File read successfully")
    
    # Cleanup
    test_storage.delete(test_path)
    print("   ✓ File deleted")
    
    return True

def test_upload_endpoint():
    """Test the upload endpoint."""
    print("\n2. Testing upload endpoint...")
    
    # Wait for server to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
            if response.status_code == 200:
                print("   ✓ Server is running")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(1)
                continue
            else:
                print("   ✗ Server is not running. Please start it with: uvicorn main:app --reload")
                return False
    
    # Upload test PDF
    test_pdf_path = Path("../test_document.pdf")
    if not test_pdf_path.exists():
        print(f"   ✗ Test PDF not found at {test_pdf_path}")
        return False
    
    with open(test_pdf_path, "rb") as f:
        files = {"file": ("test_document.pdf", f, "application/pdf")}
        data = {"description": "Test document", "tags": "test,upload"}
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✓ Upload successful")
                print(f"   ✓ Document ID: {result['document']['id']}")
                print(f"   ✓ Filename: {result['document']['filename']}")
                return result['document']['id']
            else:
                print(f"   ✗ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Request failed: {e}")
            return None

def test_file_saved(document_id: int):
    """Test that file was saved to disk."""
    print("\n3. Testing file saved to disk...")
    
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print("   ✗ Document not found in database")
            return False
        
        # Check if file exists in storage
        storage = FileStorage()
        full_path = Path(storage.base_path) / document.file_path
        
        if full_path.exists():
            file_size = full_path.stat().st_size
            print(f"   ✓ File exists at: {full_path}")
            print(f"   ✓ File size: {file_size} bytes")
            print(f"   ✓ Matches DB record: {file_size == document.file_size}")
            return True
        else:
            print(f"   ✗ File not found at: {full_path}")
            return False
    finally:
        db.close()

def test_db_record(document_id: int):
    """Test that database record was created."""
    print("\n4. Testing database record...")
    
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if document:
            print(f"   ✓ Document record found")
            print(f"   ✓ ID: {document.id}")
            print(f"   ✓ Filename: {document.filename}")
            print(f"   ✓ File type: {document.file_type}")
            print(f"   ✓ File size: {document.file_size} bytes")
            print(f"   ✓ File path: {document.file_path}")
            print(f"   ✓ Processed: {document.processed}")
            print(f"   ✓ Description: {document.description}")
            print(f"   ✓ Tags: {document.tags}")
            return True
        else:
            print(f"   ✗ Document record not found")
            return False
    finally:
        db.close()

def main():
    """Run all tests."""
    print("=" * 60)
    print("Document Upload Functionality Tests")
    print("=" * 60)
    
    # Setup
    setup_test_db()
    
    try:
        # Test 1: File storage
        if not test_file_storage():
            print("\n✗ File storage test failed")
            return 1
        
        # Test 2: Upload endpoint
        document_id = test_upload_endpoint()
        if not document_id:
            print("\n✗ Upload endpoint test failed")
            return 1
        
        # Test 3: File saved
        if not test_file_saved(document_id):
            print("\n✗ File saved test failed")
            return 1
        
        # Test 4: DB record
        if not test_db_record(document_id):
            print("\n✗ Database record test failed")
            return 1
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        cleanup_test_db()

if __name__ == "__main__":
    sys.exit(main())

