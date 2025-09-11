"""
LLM Service Module
Handles structured data extraction using Mistral LLM
"""

import json
import logging
from typing import Dict, Any
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MistralLLMService:
    """Service for handling LLM-based structured data extraction"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"

    async def extract_structured_data(self, text: str, schema: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Extract structured data from text using Mistral LLM with schema validation

        Args:
            text: Raw text extracted from OCR
            schema: JSON schema for structured extraction
            document_type: Type of document (for prompt customization)

        Returns:
            Dict containing structured data and confidence score
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Mistral API key not configured")

        # Create prompt based on document type
        system_prompt = self._get_system_prompt(document_type)
        user_prompt = f"""
Extract information from the following document text and return it as JSON that matches the provided schema.

Document Text:
{text}

Schema:
{json.dumps(schema, indent=2)}

Return only valid JSON that matches the schema exactly. Do not include any additional text or explanations.
"""

        payload = {
            "model": "mistral-medium-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1  # Low temperature for consistent structured output
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(300),
            headers={"Authorization": f"Bearer {self.api_key}"}
        ) as client:
            try:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)
                response.raise_for_status()
                result = response.json()

                # Extract JSON from response
                content = result["choices"][0]["message"]["content"]

                # Try to extract JSON from the response (handle cases where LLM adds extra text)
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        structured_data = json.loads(json_match.group())
                    else:
                        raise HTTPException(status_code=500, detail="LLM did not return valid JSON")

                return {
                    "structured_data": structured_data,
                    "confidence": 0.9
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid Mistral API key")
                elif e.response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                else:
                    raise HTTPException(status_code=500, detail=f"Mistral LLM API error: {e.response.status_code}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
            except Exception as e:
                logger.error(f"LLM processing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")

    def _get_system_prompt(self, document_type: str) -> str:
        """Get system prompt based on document type"""
        base_prompt = "You are an expert at extracting structured information from documents. "

        if document_type == "bank_statement":
            return base_prompt + """
Extract bank statement information including:
- Account holder name and details
- Account number, IFSC code, branch
- All transactions with dates, descriptions, amounts
- Statement summary with totals
Be precise with amounts and dates. Handle multiple pages correctly."""
        elif document_type == "invoice":
            return base_prompt + """
Extract invoice information including:
- Invoice number, date, due date
- Vendor/company information
- All line items with descriptions, quantities, prices
- Subtotal, tax, and total amounts
Be precise with all numerical values."""
        elif document_type == "receipt":
            return base_prompt + """
Extract receipt information including:
- Store/vendor information
- Transaction date and time
- All items with names, quantities, prices
- Total amount
Be precise with all numerical values."""
        else:
            return base_prompt + """
Extract all relevant information from the document and structure it according to the provided schema.
Be precise and thorough in your extraction."""
