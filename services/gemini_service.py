"""
Gemini Service Module - V3 (Advanced Analysis)
"""

import json
import logging
import asyncio
import os
from typing import Dict, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi import HTTPException
import jsonschema
import aiofiles

logger = logging.getLogger(__name__)


class GeminiService:
    _is_configured = False

    def __init__(self, api_key: str):
        if not GeminiService._is_configured:
            if api_key:
                genai.configure(api_key=api_key)
                GeminiService._is_configured = True
                logger.info("Google Generative AI client configured successfully.")
            else:
                logger.warning("GeminiService initialized without an API key.")

    async def process_document_with_schema(
        self,
        file_content: bytes,
        schema: Dict[str, Any],
        document_type: str,
        model_name: str = "gemini-2.5-flash-lite"
    ) -> Dict[str, Any]:
        if not GeminiService._is_configured:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        temp_file_path = None
        uploaded_file = None

        try:
            async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                await temp_file.write(file_content)
                temp_file_path = temp_file.name

            uploaded_file = await asyncio.to_thread(genai.upload_file, path=temp_file_path)
            logger.info(f"Uploaded file to Gemini: {uploaded_file.name}")

            prompt = self._create_prompt(schema, document_type)

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
            logger.info(f"Received raw response from Gemini API: {response.text[:500]}...")

            if not response.text:
                raise HTTPException(status_code=500, detail="Gemini returned an empty response, likely due to a content filter.")

            result = json.loads(response.text)
            self._validate_response(result, schema)

            return {
                "structured_data": result,
                "confidence": 0.9,
                "processing_notes": f"Processed with Gemini File API using model {model_name}.",
                "pages_processed": 1,
                "model_used": model_name
            }

        except jsonschema.ValidationError as e:
            logger.error(f"Gemini response failed schema validation: {e.message}")
            raise HTTPException(status_code=500, detail=f"Gemini response failed schema validation: {e.message}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Gemini. Error: {e}")
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Gemini processing: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
        finally:
            if uploaded_file:
                logger.info(f"Uploaded file {uploaded_file.name} will be auto-deleted by Gemini.")
            if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)
                logger.info(f"Deleted temp file: {temp_file_path}")

    @staticmethod
    def _create_prompt(schema: Dict[str, Any], document_type: str) -> str:
        """Constructs the prompt for the Gemini API call with enhanced instructions."""
        system_prompt = GeminiService._get_system_prompt(document_type)
        schema_str = json.dumps(schema, indent=2)
        
        # --- NEW CRITICAL INSTRUCTION ADDED HERE ---
        debit_credit_instruction = (
            "CRITICAL INSTRUCTION: The 'Withdrawal' and 'Deposit' columns in the source document can be misleading. "
            "You MUST determine if a transaction is a debit or a credit by observing the change in the 'Balance' column. "
            "If the balance decreases, it is a debit (withdrawal). If the balance increases, it is a credit (deposit). "
            "Populate the debit and credit fields in the JSON accordingly."
        )

        return (
            f"{system_prompt}\n\n{debit_credit_instruction}\n\nPlease analyze this document and extract the information according to "
            f"the following JSON schema:\n\n{schema_str}\n\nPlease adhere strictly to the schema. "
            "Do not add or remove fields. Parse monetary values as floats and dates as 'YYYY-MM-DD'. "
            "Extract every single transaction listed in the document, identify a merchant for each where possible, and assign a category."
        )

    @staticmethod
    def _validate_response(instance: Dict[str, Any], schema: Dict[str, Any]):
        try:
            jsonschema.validate(instance=instance, schema=schema)
            logger.info("Response validated against schema successfully.")
        except jsonschema.ValidationError:
            raise

    @staticmethod
    def _get_system_prompt(document_type: str) -> str:
        # This function remains the same as before
        prompts = {
            "bank_statement": "For bank statements, focus on account details, all transactions, balances, and summary information. Extract EVERY transaction.",
            "invoice": "For invoices, focus on invoice number, vendor/billing info, all line items, subtotals, taxes, and totals. Extract EVERY line item.",
            "receipt": "For receipts, focus on vendor details, transaction date/time, all purchased items, and financial totals. Extract EVERY item.",
            "default": "Extract all relevant information from the document according to the provided schema."
        }
        instruction = prompts.get(document_type, prompts["default"])
        return (
            "You are an expert document analysis AI. Your task is to extract, analyze, and categorize information from the "
            f"provided document and return it as structured JSON.\n\n{instruction}"
        )