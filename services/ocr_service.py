"""
OCR Service Module
Handles OCR processing using Mistral API
"""

import base64
import logging
from typing import Dict, Any
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MistralOCRService:
    """Service for handling OCR operations using Mistral API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"

    async def extract_text_and_tables(self, file_content: bytes) -> Dict[str, Any]:
        """
        Extract text and tables from PDF using Mistral OCR API

        Args:
            file_content: Raw PDF file bytes

        Returns:
            Dict containing extracted text, tables, and metadata
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Mistral API key not configured")

        # Prepare request payload
        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64.b64encode(file_content).decode('utf-8')}"
            }
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(300),
            headers={"Authorization": f"Bearer {self.api_key}"}
        ) as client:
            try:
                response = await client.post(f"{self.base_url}/ocr", json=payload)
                response.raise_for_status()
                result = response.json()

                # Extract text from all pages
                extracted_text = ""
                tables = []

                for page in result.get("pages", []):
                    if "markdown" in page:
                        extracted_text += page["markdown"] + "\n\n"

                    # Extract tables if available
                    if "tables" in page:
                        tables.extend(page["tables"])

                return {
                    "text": extracted_text.strip(),
                    "tables": tables,
                    "pages_processed": len(result.get("pages", [])),
                    "confidence": 0.95  # Default confidence
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid Mistral API key")
                elif e.response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                else:
                    raise HTTPException(status_code=500, detail=f"Mistral API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"OCR processing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
