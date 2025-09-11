"""
Gemini Service Module
Handles document processing using Google Gemini Vision API
"""

import base64
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for handling document processing using Gemini Vision API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    async def process_document_with_schema(self, file_content: bytes, schema: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Process document using Gemini Vision API with structured output

        Args:
            file_content: Raw PDF/image file bytes
            schema: JSON schema for structured extraction
            document_type: Type of document for prompt customization

        Returns:
            Dict containing structured data and metadata
        """
        if not self.api_key or not self.model:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        try:
            # Convert file to base64
            file_b64 = base64.b64encode(file_content).decode('utf-8')

            # Create prompt based on document type
            system_prompt = self._get_system_prompt(document_type)

            # Create the prompt with schema
            schema_str = json.dumps(schema, indent=2)
            prompt = f"""{system_prompt}

Please analyze this document and extract the information according to the following JSON schema:

{schema_str}

Return ONLY a valid JSON object that matches this schema exactly. Do not include any additional text or explanations.

Document: data:application/pdf;base64,{file_b64}"""

            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                )
            )

            # Extract and parse JSON from response
            response_text = response.text.strip()

            # Try to extract JSON if wrapped in other text
            try:
                # First try direct parsing
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON within the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise HTTPException(status_code=500, detail="No valid JSON found in Gemini response")

            return {
                "structured_data": result,
                "confidence": 0.9,  # Gemini doesn't provide confidence scores
                "processing_notes": "Processed using Gemini Vision API",
                "pages_processed": 1,  # Gemini processes as single unit
                "model_used": "gemini-1.5-pro"
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to parse Gemini response as JSON")
        except Exception as e:
            logger.error(f"Gemini processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Gemini processing failed: {str(e)}")

    def _get_system_prompt(self, document_type: str) -> str:
        """Get system prompt based on document type"""
        base_prompt = """You are an expert document analyzer. Extract information from the provided document image/PDF and return it as structured JSON data.

IMPORTANT: Analyze the document carefully and extract ALL relevant information. Be precise with:
- Names, dates, amounts, and numbers
- Account details and transaction information
- Contact information and addresses
- Any other structured data visible in the document

Return the extracted data in the exact JSON format specified by the schema."""

        if document_type == "bank_statement":
            return base_prompt + """

For bank statements, focus on:
- Account holder name and account details
- All transaction records with dates, descriptions, amounts
- Opening and closing balances
- Statement period and summary information
- Branch and contact details

Extract EVERY transaction visible in the statement."""
        elif document_type == "invoice":
            return base_prompt + """

For invoices, focus on:
- Invoice number, date, and due date
- Vendor/company information and billing address
- All line items with descriptions, quantities, rates, and amounts
- Subtotal, tax amounts, and total
- Payment terms and instructions

Extract EVERY line item and all financial details."""
        elif document_type == "receipt":
            return base_prompt + """

For receipts, focus on:
- Store/vendor name and location
- Receipt number and transaction date/time
- All purchased items with descriptions, quantities, and prices
- Subtotal, tax, and total amounts
- Payment method information

Extract EVERY item listed on the receipt."""
        else:
            return base_prompt + """

Extract all relevant information from the document according to the provided schema.
Be thorough and precise in your extraction."""
