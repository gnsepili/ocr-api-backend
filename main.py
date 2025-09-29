"""
Simple OCR Microservice - Gemini Only
Extracts text and tables from PDFs using Gemini + EasyOCR hybrid approach
"""

import logging
import time
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import modular components
from services.gemini_service_v3 import HybridGeminiService
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
    title="OCR Microservice",
    description="Extract structured data from PDFs using Gemini AI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini service
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is required")

gemini_service = HybridGeminiService(gemini_api_key)

# API Endpoints
@app.post("/ocr/process", response_model=OCRResponse)
async def process_document(file: UploadFile = File(...)):
    """
    Process a PDF document and extract structured data.
    Uses Gemini AI with EasyOCR for precise coordinate mapping.
    """
    start_time = time.time()

    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB"
            )

        logger.info(f"Processing file: {file.filename} ({file_size_mb:.2f}MB)")

        # Use bank statement schema by default
        schema = DEFAULT_SCHEMAS["bank_statement"]
        
        # Process with Gemini hybrid approach
        gemini_result = await gemini_service.process_document_hybrid(
            file_content, 
            schema, 
            document_type="bank_statement"
        )
        
        # Parse the response into ExtractedData model
        from models.schemas import ExtractedData
        structured_data = ExtractedData(**gemini_result["structured_data"])

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Processing complete in {processing_time}ms")

        return OCRResponse(
            status="success",
            data=structured_data,
            schema_used="bank_statement",
            confidence_score=gemini_result["confidence"],
            processing_time_ms=processing_time,
            pages_processed=gemini_result["pages_processed"]
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"An unhandled error occurred: {e}", exc_info=True)
        return OCRResponse(
            status="error",
            error=str(e),
            processing_time_ms=processing_time,
            pages_processed=0
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "OCR Microservice",
        "version": "2.0.0",
        "description": "Extract structured data from PDFs using Gemini AI",
        "endpoints": {
            "process": "/ocr/process (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
