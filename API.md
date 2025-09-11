# OCR API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### POST /ocr/process
Process PDF documents with OCR and extract structured data.

**Request Format:**
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Max File Size**: 50MB

**Parameters:**
- `file` (required) - PDF file to process
- `model_name` (optional) - Processing model:
  - `mistral-ocr` (default) - Mistral OCR + LLM (2-step)
  - `gemini-vision` - Gemini Vision (1-step direct)
- `document_type` (optional) - Document type:
  - `auto` (default) - Auto-detect
  - `bank_statement`, `invoice`, `receipt`, `custom`
- `custom_schema` (optional) - JSON schema string for custom extraction
- `extract_tables` (optional) - Boolean, default: true

**Examples:**
```bash
# Mistral processing (default)
curl -X POST "http://localhost:8000/ocr/process" \
  -F "file=@document.pdf" \
  -F "model_name=mistral-ocr" \
  -F "document_type=bank_statement"

# Gemini processing
curl -X POST "http://localhost:8000/ocr/process" \
  -F "file=@document.pdf" \
  -F "model_name=gemini-vision" \
  -F "document_type=invoice"
```

### GET /health
Check service health status.

### GET /
Get service information and available endpoints.

## Response Format
```json
{
  "status": "success",
  "data": { /* extracted data */ },
  "schema_used": "bank_statement",
  "confidence_score": 0.95,
  "processing_time_ms": 2500,
  "pages_processed": 5
}
```

## Document Types
- `auto` - Auto-detect document type
- `bank_statement` - Bank statements
- `invoice` - Invoices
- `receipt` - Receipts
- `custom` - Custom JSON schema
