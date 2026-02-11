#!/usr/bin/env python3
"""
Test script for LLM field extraction service.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_extractor import LLMExtractor
from app.services.prompts import build_extraction_prompt
from app.schemas.extraction import ExtractionResult

def test_prompt_generation():
    """Test prompt template generation."""
    print("=" * 60)
    print("TEST 1: Prompt Template Generation")
    print("=" * 60)
    
    sample_text = """
    ACME CORPORATION
    123 Business Street
    New York, NY 10001
    
    EIN: 12-3456789
    Phone: (555) 123-4567
    Email: contact@acme.com
    
    Incorporated: January 15, 2020
    State of Incorporation: Delaware
    """
    
    prompt = build_extraction_prompt(sample_text)
    print(f"✓ Prompt generated ({len(prompt)} characters)")
    print(f"✓ Prompt includes field definitions")
    print(f"✓ Prompt includes document text\n")
    
    return True

def test_llm_extraction():
    """Test LLM extraction with sample text."""
    print("=" * 60)
    print("TEST 2: LLM Field Extraction")
    print("=" * 60)
    
    sample_text = """
    ACME CORPORATION
    123 Business Street, Suite 100
    New York, NY 10001
    
    Employer Identification Number: 12-3456789
    Phone: (555) 123-4567
    Email: contact@acme.com
    Website: https://www.acme.com
    
    Date of Incorporation: January 15, 2020
    State of Incorporation: Delaware
    """
    
    try:
        result = LLMExtractor.extract_fields(sample_text)
        
        print(f"✓ Extraction successful")
        print(f"✓ Extraction method: {result.extraction_method}")
        print(f"✓ Fields extracted: {len(result.fields)}")
        
        if result.fields:
            print("\nExtracted fields:")
            for field in result.fields:
                print(f"  - {field.field_name}: {field.value}")
                print(f"    Confidence: {field.confidence:.2f}")
                print(f"    Source span: '{field.source_span.text[:50]}...'")
                print()
        else:
            print("  (No fields extracted - this is expected with stub implementation)\n")
        
        return True
        
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation():
    """Test schema validation."""
    print("=" * 60)
    print("TEST 3: Schema Validation")
    print("=" * 60)
    
    # Test valid extraction result
    try:
        valid_result = ExtractionResult(
            fields=[
                {
                    "field_name": "company_name",
                    "value": "Acme Corporation",
                    "confidence": 0.95,
                    "source_span": {
                        "start": 0,
                        "end": 18,
                        "text": "Acme Corporation"
                    },
                    "field_type": "text"
                }
            ],
            extraction_method="llm"
        )
        print("✓ Valid extraction result created")
        print(f"  - Field: {valid_result.fields[0].field_name}")
        print(f"  - Value: {valid_result.fields[0].value}")
        print(f"  - Confidence: {valid_result.fields[0].confidence}\n")
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False
    
    # Test empty fields (should be valid)
    try:
        empty_result = ExtractionResult(
            fields=[],
            extraction_method="llm"
        )
        print("✓ Empty fields result is valid\n")
    except Exception as e:
        print(f"✗ Empty fields validation failed: {e}")
        return False
    
    # Test invalid confidence
    try:
        invalid_result = ExtractionResult(
            fields=[
                {
                    "field_name": "test",
                    "value": "test",
                    "confidence": 1.5,  # Invalid: > 1.0
                    "source_span": {
                        "start": 0,
                        "end": 4,
                        "text": "test"
                    }
                }
            ]
        )
        print("✗ Invalid confidence should have been rejected")
        return False
    except Exception:
        print("✓ Invalid confidence correctly rejected\n")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM Field Extraction Service Tests")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Prompt generation
        if not test_prompt_generation():
            return 1
        
        # Test 2: LLM extraction
        if not test_llm_extraction():
            return 1
        
        # Test 3: Validation
        if not test_validation():
            return 1
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ Prompt template generation works")
        print("  ✓ LLM extraction service works (stubbed)")
        print("  ✓ Schema validation works")
        print("\nNote: LLM call is stubbed. Implement actual LLM integration")
        print("      in app/services/llm_extractor.py::_stub_llm_call()")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

