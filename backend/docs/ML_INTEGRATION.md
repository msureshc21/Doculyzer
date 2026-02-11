# PyTorch/ML Integration Guide

This document explains how PyTorch and transformer models can enhance the AI Paperwork Co-pilot system.

## Overview

We've created ML model wrappers that can replace heuristic/stub implementations with intelligent, learned models. The system gracefully falls back to heuristics if ML models aren't available.

## Available ML Models

### 1. Document Type Classifier (`DocumentTypeClassifier`)

**Purpose**: Automatically classify document types (employment application, tax form, contract, etc.)

**Model**: Uses DistilBERT (lightweight transformer) for text classification

**Usage**:
```python
from app.services.ml_models import get_document_classifier

classifier = get_document_classifier()
result = classifier.classify_document(
    text=extracted_text,
    field_names=form_field_names
)
# Returns: {"document_type": "employment_application", "confidence": 0.95, ...}
```

**Benefits**:
- More accurate than keyword matching
- Learns from document patterns
- Can be fine-tuned on your specific document types

### 2. Field Context Analyzer (`FieldContextAnalyzer`)

**Purpose**: Understand field context to distinguish "previous employer" vs "current company"

**Model**: Uses BERT-based NER (Named Entity Recognition) to understand field meaning

**Usage**:
```python
from app.services.ml_models import get_field_analyzer

analyzer = get_field_analyzer()
result = analyzer.analyze_field_context(
    field_name="company_name",
    surrounding_text="Previous employer company name",
    all_fields=all_field_names
)
# Returns: {"category": "company_previous", "context": "...", ...}
```

**Benefits**:
- Understands context, not just keywords
- Distinguishes ambiguous fields
- Uses document structure for better categorization

### 3. Company Info Extractor (`CompanyInfoExtractor`)

**Purpose**: Extract structured company information from unstructured text

**Model**: Uses BERT-based NER to extract organizations, locations, dates

**Usage**:
```python
from app.services.ml_models import get_company_extractor

extractor = get_company_extractor()
result = extractor.extract_company_info(document_text)
# Returns: {"organizations": [...], "locations": [...], "dates": [...]}
```

**Benefits**:
- Extracts entities even from unstructured text
- Can find company info in paragraphs, not just form fields
- More robust than regex patterns

## Installation

### Option 1: Full ML Support (Recommended for Production)

```bash
pip install torch transformers accelerate
```

This installs:
- PyTorch (deep learning framework)
- Transformers (Hugging Face library for pre-trained models)
- Accelerate (for efficient model loading)

**Note**: PyTorch can be large (~2GB). Consider using CPU-only version:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers accelerate
```

### Option 2: CPU-Only (Lighter)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers accelerate
```

### Option 3: No ML (Current State)

The system works without ML models - it uses heuristics as fallback.

## Integration Points

### 1. Document Analyzer Integration

Update `app/services/document_analyzer.py`:

```python
from app.services.ml_models import get_document_classifier, get_field_analyzer

class DocumentAnalyzer:
    @staticmethod
    def analyze_document(...):
        # Use ML classifier
        classifier = get_document_classifier()
        doc_type_result = classifier.classify_document(text, field_names)
        
        # Use ML field analyzer
        analyzer = get_field_analyzer()
        for field in fields:
            context_result = analyzer.analyze_field_context(
                field_name=field['field_name'],
                surrounding_text=extracted_text,
                all_fields=[f['field_name'] for f in fields]
            )
```

### 2. LLM Extractor Integration

Update `app/services/llm_extractor.py`:

```python
from app.services.ml_models import get_company_extractor

class LLMExtractor:
    @staticmethod
    def extract_fields(document_text: str):
        # Use ML extractor as pre-processing
        extractor = get_company_extractor()
        ml_extracted = extractor.extract_company_info(document_text)
        
        # Combine with LLM extraction
        # ...
```

## Fine-Tuning Models (Advanced)

For best results, fine-tune models on your specific document types:

### 1. Prepare Training Data

```python
# Example training data format
training_data = [
    {
        "text": "Employment Application Form...",
        "fields": ["name", "previous_employer", "current_company"],
        "document_type": "employment_application"
    },
    # ... more examples
]
```

### 2. Fine-Tune Document Classifier

```python
from transformers import Trainer, TrainingArguments

# Fine-tune DistilBERT on your data
# See: https://huggingface.co/docs/transformers/training
```

### 3. Fine-Tune Field Context Analyzer

Create a custom NER model fine-tuned on form fields:
- Label fields as "company_current", "company_previous", "personal", etc.
- Train on your document dataset

## Performance Considerations

### Model Loading

Models are loaded lazily (on first use) to avoid startup delays.

### Caching

Consider caching model predictions for frequently seen documents.

### GPU vs CPU

- **CPU**: Slower but works everywhere (~1-2 seconds per document)
- **GPU**: Much faster (~0.1-0.2 seconds per document) but requires CUDA

### Model Size

- **DistilBERT**: ~260MB (lightweight)
- **BERT-base**: ~440MB (more accurate)
- **RoBERTa**: ~500MB (best accuracy)

## Future Enhancements

1. **Custom Fine-Tuned Models**: Train on your specific document types
2. **Multi-Modal Models**: Use vision transformers for PDF layout understanding
3. **Field Detection**: Use object detection models to find form fields in PDFs
4. **Confidence Calibration**: Better confidence scores from models
5. **Active Learning**: Learn from user corrections

## Example: Full Integration

```python
# In document_analyzer.py
from app.services.ml_models import (
    get_document_classifier,
    get_field_analyzer
)

def analyze_document(pdf_content, extracted_text, form_fields):
    # 1. Classify document type with ML
    classifier = get_document_classifier()
    doc_type_result = classifier.classify_document(
        text=extracted_text or "",
        field_names=[f['field_name'] for f in form_fields]
    )
    
    # 2. Analyze each field with ML
    analyzer = get_field_analyzer()
    field_contexts = []
    for field in form_fields:
        context_result = analyzer.analyze_field_context(
            field_name=field['field_name'],
            surrounding_text=extracted_text,
            all_fields=[f['field_name'] for f in form_fields]
        )
        field_contexts.append(context_result)
    
    # 3. Return enhanced analysis
    return DocumentAnalysis(
        document_type=doc_type_result['document_type'],
        fields=field_contexts,
        # ...
    )
```

## Troubleshooting

### Models Not Loading

Check if transformers library is installed:
```bash
python -c "import transformers; print(transformers.__version__)"
```

### Out of Memory

Use smaller models or CPU-only:
```python
# In ml_models.py, use smaller models
model_name = "distilbert-base-uncased"  # Smaller than bert-base
```

### Slow Performance

- Use GPU if available
- Cache predictions
- Use smaller models (DistilBERT vs BERT)
- Batch process multiple documents

## Next Steps

1. **Install dependencies**: `pip install torch transformers`
2. **Test models**: Try the ML models on sample documents
3. **Integrate**: Update document_analyzer.py to use ML models
4. **Fine-tune**: Collect training data and fine-tune models
5. **Monitor**: Track accuracy improvements over heuristics

