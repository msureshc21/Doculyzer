"""
LLM-based field extraction service.

This service uses an LLM to extract structured fields from document text.
Currently implemented with a stubbed LLM call for development.
"""
import json
import logging
from typing import Optional
from pydantic import ValidationError

from app.schemas.extraction import ExtractionResult, ExtractedFieldOutput
from app.services.prompts import build_extraction_prompt

logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    Service for extracting structured fields from document text using LLM.
    
    TODO: Implement actual LLM integration:
    - Option 1: OpenAI API (GPT-4, GPT-3.5-turbo)
    - Option 2: Anthropic Claude API
    - Option 3: Local LLM (Ollama, llama.cpp)
    - Option 4: Azure OpenAI
    - Option 5: Google Gemini
    
    Current implementation uses a stubbed response for development.
    """
    
    @staticmethod
    def extract_fields(document_text: str) -> ExtractionResult:
        """
        Extract structured fields from document text using LLM.
        
        Args:
            document_text: The parsed text from the document
            
        Returns:
            ExtractionResult with extracted fields
            
        Raises:
            ValueError: If extraction fails or validation fails
            
        TODO: Implement actual LLM call:
        1. Build prompt using build_extraction_prompt()
        2. Call LLM API (OpenAI, Claude, etc.)
        3. Parse JSON response
        4. Validate against ExtractionResult schema
        5. Handle retries for rate limits
        6. Handle parsing errors gracefully
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        logger.info(f"Extracting fields from document text ({len(document_text)} characters)")
        
        # Build prompt
        prompt = build_extraction_prompt(document_text)
        
        # TODO: Replace with actual LLM API call
        # For now, use stubbed response
        try:
            llm_response = LLMExtractor._stub_llm_call(document_text, prompt)
            
            # Parse and validate response
            result = LLMExtractor._parse_and_validate_response(llm_response)
            
            logger.info(f"Successfully extracted {len(result.fields)} fields")
            return result
            
        except Exception as e:
            logger.error(f"Error during field extraction: {e}")
            raise ValueError(f"Field extraction failed: {e}")
    
    @staticmethod
    def _stub_llm_call(document_text: str, prompt: str) -> str:
        """
        Stubbed LLM call for development.
        
        In production, this would call an actual LLM API.
        
        Args:
            document_text: The document text
            prompt: The formatted prompt
            
        Returns:
            JSON string response (stubbed)
            
        TODO: Replace with actual LLM call:
        ```python
        import openai  # or anthropic, etc.
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            response_format={"type": "json_object"}  # If supported
        )
        return response.choices[0].message.content
        ```
        """
        logger.warning("Using stubbed LLM response - implement actual LLM call")
        
        # Simple stub: try to find some common patterns in the text
        # This is just for testing - real implementation would use actual LLM
        fields = []
        
        # Look for company name patterns
        text_lower = document_text.lower()
        if "company" in text_lower or "corporation" in text_lower or "inc" in text_lower:
            # Try to extract a potential company name (very basic stub)
            lines = document_text.split('\n')[:5]  # First few lines
            for i, line in enumerate(lines):
                if len(line.strip()) > 5 and len(line.strip()) < 100:
                    # Simple heuristic: first substantial line might be company name
                    start_pos = document_text.find(line)
                    if start_pos >= 0:
                        fields.append({
                            "field_name": "company_name",
                            "value": line.strip(),
                            "confidence": 0.6,  # Low confidence for stub
                            "source_span": {
                                "start": start_pos,
                                "end": start_pos + len(line),
                                "text": line
                            },
                            "field_type": "text",
                            "notes": "Stubbed extraction - implement actual LLM"
                        })
                        break
        
        # If no fields found, return empty result (valid according to schema)
        if not fields:
            # Return a minimal valid response
            return json.dumps({
                "fields": [],
                "extraction_method": "llm_stub"
            })
        
        return json.dumps({
            "fields": fields,
            "extraction_method": "llm_stub"
        })
    
    @staticmethod
    def _parse_and_validate_response(response_text: str) -> ExtractionResult:
        """
        Parse LLM response and validate against schema.
        
        Args:
            response_text: Raw response from LLM (should be JSON)
            
        Returns:
            Validated ExtractionResult
            
        Raises:
            ValueError: If response cannot be parsed or validated
        """
        try:
            # Try to extract JSON from response (in case LLM adds extra text)
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate against Pydantic schema
            result = ExtractionResult.model_validate(data)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except ValidationError as e:
            logger.error(f"LLM response failed schema validation: {e}")
            logger.debug(f"Response data: {data}")
            raise ValueError(f"Response validation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            raise ValueError(f"Failed to process LLM response: {e}")


# Global instance
llm_extractor = LLMExtractor()

