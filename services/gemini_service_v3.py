"""
Hybrid Gemini Service Module - PDF + EasyOCR approach
Combines visual PDF understanding with precise coordinate data
"""

import json
import logging
import asyncio
import os
import tempfile
from typing import Dict, Any, List

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi import HTTPException
import jsonschema
import aiofiles
from services.easyocr_service import EasyOCRService

logger = logging.getLogger(__name__)


class HybridGeminiService:
    """Hybrid Gemini service that combines PDF upload with EasyOCR coordinate data."""
    
    _is_configured = False

    def __init__(self, api_key: str):
        if not HybridGeminiService._is_configured:
            if api_key:
                genai.configure(api_key=api_key)
                HybridGeminiService._is_configured = True
                logger.info("Google Generative AI client configured successfully.")
            else:
                logger.warning("HybridGeminiService initialized without an API key.")
        
        # Initialize EasyOCR service
        self.ocr_service = EasyOCRService()

    async def process_document_hybrid(
        self,
        file_content: bytes,
        schema: Dict[str, Any],
        document_type: str,
        model_name: str = "gemini-2.5-flash-lite"
    ) -> Dict[str, Any]:
        """
        Process document using hybrid PDF + EasyOCR approach.
        
        Args:
            file_content: PDF file content as bytes
            schema: JSON schema for validation
            document_type: Type of document (e.g., 'bank_statement')
            model_name: Gemini model to use
            
        Returns:
            Structured data with coordinates directly from Gemini
        """
        if not HybridGeminiService._is_configured:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        temp_file_path = None
        uploaded_file = None

        try:
            # Step 1: Extract OCR coordinate data
            logger.info("Extracting OCR coordinate data with EasyOCR...")
            ocr_data = await self.ocr_service.process_pdf_for_llm(file_content)
            
            # Step 2: Upload PDF to Gemini
            logger.info("Uploading PDF to Gemini...")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            uploaded_file = await asyncio.to_thread(genai.upload_file, path=temp_file_path)
            logger.info(f"Uploaded PDF to Gemini: {uploaded_file.name}")
            
            # Step 3: Create hybrid prompt with OCR coordinate data
            prompt = self._create_hybrid_prompt(ocr_data, schema, document_type)
            
            # Step 4: Send PDF + prompt to Gemini
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"response_mime_type": "application/json"},
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            response = await asyncio.to_thread(model.generate_content, [prompt, uploaded_file])
            logger.info(f"Received response from Gemini API")

            if not response.text:
                raise HTTPException(status_code=500, detail="Gemini returned an empty response")

            # Step 5: Parse and validate response
            result = self._extract_json_from_response(response.text)
            self._validate_response(result, schema)

            return {
                "structured_data": result,
                "confidence": 0.95,  # Higher confidence due to hybrid approach
                "processing_notes": f"Processed with hybrid PDF + EasyOCR approach using {model_name}. Coordinates provided directly by Gemini.",
                "pages_processed": ocr_data["document_info"]["total_pages"],
                "model_used": model_name,
                "ocr_stats": {
                    "total_text_elements": ocr_data["document_info"]["total_text_elements"],
                    "pages": ocr_data["document_info"]["total_pages"]
                },
                "approach": "hybrid_pdf_easyocr"
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Gemini: {e}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from Gemini: {e}")
        except jsonschema.ValidationError as e:
            logger.error(f"Gemini response failed schema validation: {e.message}")
            raise HTTPException(status_code=500, detail=f"Schema validation failed: {e.message}")
        except Exception as e:
            logger.error(f"Error in hybrid Gemini processing: {e}")
            raise HTTPException(status_code=500, detail=f"Processing error: {e}")
        finally:
            # Cleanup
            if uploaded_file:
                logger.info(f"Uploaded file {uploaded_file.name} will be auto-deleted by Gemini.")
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Deleted temp file: {temp_file_path}")

    def _create_hybrid_prompt(self, ocr_data: Dict[str, Any], schema: Dict[str, Any], document_type: str) -> str:
        """Create hybrid prompt that leverages both PDF visual context and OCR coordinate data."""
        
        system_prompt = self._get_system_prompt(document_type)
        schema_str = json.dumps(schema, indent=2)
        
        # Create coordinate reference for Gemini
        coordinate_info = self._format_coordinate_info(ocr_data)
        total_coordinates = len(ocr_data["text_with_coordinates"])
        total_pages = ocr_data["document_info"]["total_pages"]
        
        hybrid_prompt = f"""
{system_prompt}

HYBRID PROCESSING WITH COMPLETE COORDINATE COVERAGE:
You have access to both the visual PDF document and {total_coordinates} precise coordinate references from EasyOCR across {total_pages} pages.

CRITICAL PROCESSING INSTRUCTIONS:
1. **PROCESS ALL {total_coordinates} COORDINATES**: Every coordinate reference below must be considered and processed
2. **COMPLETE DOCUMENT EXTRACTION**: Extract ALL transactions, amounts, dates from ALL pages (1-{total_pages})
3. **NO DATA LEFT BEHIND**: Ensure comprehensive extraction across the entire document
4. **EXHAUSTIVE TRANSACTION EXTRACTION**: Extract EVERY single transaction from ALL pages, not just the first few

OCR COORDINATE INTELLIGENCE:
5. **OCR Splitting Behavior**: The coordinates come from image-based asymmetric OCR that may split single phrases:
   - Single phrase "PRAKASH MAHENDRA SHUKLA" might appear as 3 separate coordinates
   - Amount "29,293.00" might be split as "29," and "293.00"
   - Transaction descriptions may be fragmented across multiple coordinates
   - Dates like "15-05-2024" might be split into parts

6. **SMART MERGING REQUIRED**: When extracting values, intelligently merge related coordinate elements:
   - Combine horizontally adjacent text on same line (similar Y coordinates ±10 pixels)
   - Merge logically related fragments (names, amounts, descriptions)
   - Use combined bounding box: [leftmost_x, topmost_y, rightmost_x, bottommost_y]
   - For split amounts: "29," + "293.00" = 29293.00 with merged coordinates

EASYOCR COORDINATE REFERENCE ({total_coordinates} elements across {total_pages} pages):
{coordinate_info}

EXTRACTION TASK:
Extract structured information according to this JSON schema:

{schema_str}

MANDATORY OBJECT FORMAT - EVERY FIELD MUST FOLLOW THIS EXACT FORMAT:
Each field must be an object with: value, position, confidence, review_required

COORDINATE MERGING EXAMPLES:
- If you find "29," at [1397, 1283, 1420, 1319] and "293.00" at [1425, 1283, 1531, 1319]
  -> Merge to: "value": 29293.0, "position": [1397, 1283, 1531, 1319]
- If you find "PRAKASH" at [58, 218, 150, 250] and "MAHENDRA" at [155, 218, 280, 250] and "SHUKLA" at [285, 218, 380, 250]
  -> Merge to: "value": "PRAKASH MAHENDRA SHUKLA", "position": [58, 218, 380, 250]

PROCESSING VERIFICATION CHECKLIST:
- ✓ Verify you've processed coordinates from ALL pages (1-{total_pages})
- ✓ Ensure ALL transactions are extracted, not just the first few
- ✓ Double-check that later pages (3, 4, 5) are fully processed
- ✓ Confirm transaction count matches what's visible in the document
- ✓ Validate that coordinate merging was applied for split text

EXAMPLES OF CORRECT FORMAT:
- String field: "account_name": {{"value": "PRAKASH MAHENDRA SHUKLA", "position": [58, 218, 380, 250], "confidence": 1.0, "review_required": false}}
- Number field: "credit": {{"value": 29293.0, "position": [1397, 1283, 1531, 1319], "confidence": 1.0, "review_required": false}}
- Empty field: "debit": {{"value": null, "position": [], "confidence": 1.0, "review_required": false}}

NEVER return direct values like "balance": 29293.0 - this is WRONG!
ALWAYS return object format like "balance": {{"value": 29293.0, "position": [coordinates], "confidence": 1.0, "review_required": false}}

Return only valid JSON matching the schema with merged coordinates included.
"""
        
        return hybrid_prompt

    def _format_coordinate_info(self, ocr_data: Dict[str, Any]) -> str:
        """Format coordinate information for the hybrid prompt - includes ALL coordinates."""
        coord_lines = []
        
        # Include ALL elements for complete document coverage
        for i, element in enumerate(ocr_data["text_with_coordinates"]):
            text = element["text"]
            bbox = element["bbox"]
            page = element["page"]
            confidence = element["confidence"]
            
            coord_lines.append(f'[{i+1:03d}] "{text}" -> Page {page}, Box [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}], Confidence: {confidence:.2f}')
        
        return "\n".join(coord_lines)

    @staticmethod
    def _extract_json_from_response(response_text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response, handling extra content after JSON."""
        try:
            # First try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            response_text = response_text.strip()
            
            # Look for JSON content between braces
            start_idx = response_text.find('{')
            if start_idx == -1:
                raise json.JSONDecodeError("No JSON object found in response", response_text, 0)
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(response_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count != 0:
                raise json.JSONDecodeError("Unmatched braces in JSON", response_text, start_idx)
            
            # Extract and parse the JSON portion
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)

    @staticmethod
    def _validate_response(instance: Dict[str, Any], schema: Dict[str, Any]):
        """Validate response against schema."""
        try:
            jsonschema.validate(instance=instance, schema=schema)
            logger.info("Response validated against schema successfully.")
        except jsonschema.ValidationError:
            raise

    @staticmethod
    def _get_system_prompt(document_type: str) -> str:
        """Get system prompt based on document type."""
        prompts = {
            "bank_statement": "You are an expert at extracting information from bank statements with precise coordinate mapping. You have access to both the visual PDF and EasyOCR coordinate data. Focus on account details, all transactions, balances, and summary information. Extract EVERY transaction with accurate amounts, dates, and coordinates.",
            "invoice": "You are an expert at extracting information from invoices with precise coordinate mapping. You have access to both the visual PDF and EasyOCR coordinate data. Focus on invoice number, vendor/billing info, all line items, subtotals, taxes, and totals. Extract EVERY line item with coordinates.",
            "receipt": "You are an expert at extracting information from receipts with precise coordinate mapping. You have access to both the visual PDF and EasyOCR coordinate data. Focus on vendor details, transaction date/time, all purchased items, and financial totals. Extract EVERY item with coordinates.",
            "default": "You are an expert document analysis AI with access to both visual PDF content and precise EasyOCR coordinate data. Extract all relevant information according to the provided schema with accurate coordinate mapping."
        }
        instruction = prompts.get(document_type, prompts["default"])
        return f"HYBRID PDF + EASYOCR ANALYSIS:\n\n{instruction}"
