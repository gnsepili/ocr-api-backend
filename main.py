"""
Simple OCR Microservice - Modular Implementation
Extracts text and tables from PDFs using Mistral OCR + LLM for structured data
"""

import json
import logging
import time
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv

# Import modular components
from services.ocr_service import MistralOCRService
from services.llm_service import MistralLLMService
from services.gemini_service import GeminiService
from models.schemas import OCRResponse, HealthResponse, DEFAULT_SCHEMAS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE_MB = 50

# FastAPI App
app = FastAPI(
    title="Simple OCR Microservice",
    description="Extract text and tables from PDFs using Mistral OCR",
    version="1.0.0"
)

# Initialize services
import os
mistral_api_key = os.getenv("MISTRAL_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not mistral_api_key:
    raise RuntimeError("MISTRAL_API_KEY environment variable is required")

ocr_service = MistralOCRService(mistral_api_key)
llm_service = MistralLLMService(mistral_api_key)
gemini_service = GeminiService(gemini_api_key) if gemini_api_key else None

# API Endpoints
@app.post("/ocr/process", response_model=OCRResponse)
async def process_document(
    file: UploadFile = File(...),
    model_name: str = Form("mistral-ocr"),
    document_type: str = Form("auto"),
    extract_tables: bool = Form(True),
    custom_schema: Optional[str] = Form(None)
):
    """
    Process a PDF document and extract structured data

    - **file**: PDF file to process
    - **model_name**: OCR model (currently only 'mistral-ocr' supported)
    - **document_type**: Document type ('bank_statement', 'invoice', 'receipt', 'auto', 'custom')
    - **extract_tables**: Whether to extract tables
    - **custom_schema**: Custom JSON schema as string (for document_type='custom')
    """

    start_time = time.time()

    try:
        # Validate file
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read file content
        file_content = await file.read()

        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"
            )

        # Route processing based on model_name
        if model_name.startswith("gemini"):
            # Use Gemini for direct processing
            if not gemini_service:
                raise HTTPException(status_code=500, detail="Gemini API key not configured")

            # Determine schema to use
            schema_used = "raw"
            target_schema = None

            if document_type == "custom" and custom_schema:
                try:
                    target_schema = json.loads(custom_schema)
                    schema_used = "custom"
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid custom schema JSON")
            elif document_type in DEFAULT_SCHEMAS:
                target_schema = DEFAULT_SCHEMAS[document_type]
                schema_used = document_type
            elif document_type == "auto":
                # For Gemini, we'll let it auto-detect during processing
                target_schema = DEFAULT_SCHEMAS["bank_statement"]  # Default fallback
                schema_used = "auto"

            # Process with Gemini
            if not target_schema:
                raise HTTPException(status_code=400, detail="Schema is required for Gemini processing")

            gemini_result = await gemini_service.process_document_with_schema(
                file_content, target_schema, document_type
            )

            processing_time = int((time.time() - start_time) * 1000)

            return OCRResponse(
                status="success",
                data=gemini_result["structured_data"],
                schema_used=schema_used,
                confidence_score=gemini_result["confidence"],
                processing_time_ms=processing_time,
                pages_processed=gemini_result["pages_processed"]
            )

        else:
            # Use default Mistral approach
            # Step 1: Extract text using OCR
            ocr_result = await ocr_service.extract_text_and_tables(file_content)
            extracted_text = ocr_result["text"]

            # Step 2: Determine schema to use
            schema_used = "raw"
            target_schema = None

            if document_type == "custom" and custom_schema:
                try:
                    target_schema = json.loads(custom_schema)
                    schema_used = "custom"
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid custom schema JSON")
            elif document_type in DEFAULT_SCHEMAS:
                target_schema = DEFAULT_SCHEMAS[document_type]
                schema_used = document_type
            elif document_type == "auto":
                # Auto-detect document type (simplified - could be enhanced)
                if "account" in extracted_text.lower() and "statement" in extracted_text.lower():
                    target_schema = DEFAULT_SCHEMAS["bank_statement"]
                    schema_used = "bank_statement"
                elif "invoice" in extracted_text.lower():
                    target_schema = DEFAULT_SCHEMAS["invoice"]
                    schema_used = "invoice"
                elif "receipt" in extracted_text.lower():
                    target_schema = DEFAULT_SCHEMAS["receipt"]
                    schema_used = "receipt"
                else:
                    schema_used = "raw"

            # Step 3: Extract structured data if schema is available
            structured_data = None
            if target_schema:
                llm_result = await llm_service.extract_structured_data(
                    extracted_text, target_schema, document_type
                )
                structured_data = llm_result["structured_data"]

            processing_time = int((time.time() - start_time) * 1000)

            # Step 4: Return response
            if structured_data:
                return OCRResponse(
                    status="success",
                    data=structured_data,
                    schema_used=schema_used,
                    confidence_score=ocr_result["confidence"],
                    processing_time_ms=processing_time,
                    pages_processed=ocr_result["pages_processed"]
                )
            else:
                # Return raw text if no structured extraction
                return OCRResponse(
                    status="success",
                    data={
                        "extracted_text": extracted_text,
                        "tables": ocr_result["tables"] if ocr_result["tables"] else None
                    },
                    schema_used="raw",
                    confidence_score=ocr_result["confidence"],
                    processing_time_ms=processing_time,
                    pages_processed=ocr_result["pages_processed"]
                )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return OCRResponse(
            status="error",
            error=str(e),
            processing_time_ms=processing_time,
            pages_processed=0
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not mistral_api_key:
        return HealthResponse(status="unhealthy")

    # Simple API key validation
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10),
            headers={"Authorization": f"Bearer {mistral_api_key}"}
        ) as client:
            response = await client.get("https://api.mistral.ai/v1/models")
            if response.status_code == 200:
                return HealthResponse(status="healthy")
            else:
                return HealthResponse(status="unhealthy")
    except:
        return HealthResponse(status="unhealthy")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Simple OCR Microservice",
        "version": "1.0.0",
        "description": "Extract text and tables from PDFs using Mistral OCR",
        "endpoints": {
            "POST /ocr/process": "Process PDF document",
            "GET /health": "Health check",
            "GET /": "This information"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
