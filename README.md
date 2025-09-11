# OCR Document Processing System

A modular OCR application that extracts text and structured data from PDF documents using multiple AI providers (Mistral and Gemini).

## Architecture

The application is organized into focused modules:

- **main.py** - FastAPI application with API endpoints and model routing
- **services/ocr_service.py** - Handles OCR processing with Mistral API
- **services/llm_service.py** - Handles structured data extraction with Mistral LLM
- **services/gemini_service.py** - Handles direct document processing with Gemini Vision
- **models/schemas.py** - Pydantic models and JSON schemas for different document types

## Features

- **Dual AI Provider Support** - Choose between Mistral (OCR + LLM) or Gemini (Direct Vision)
- **PDF Processing** - Extract text from PDF documents using advanced OCR
- **Structured Data Extraction** - Convert unstructured text to structured JSON
- **Document Type Support** - Bank statements, invoices, receipts, and custom schemas
- **REST API** - FastAPI backend for programmatic access
- **Model Selection** - Route processing based on `model_name` parameter

## Setup

### Prerequisites
- Python 3.8+
- Mistral AI API key (required)
- Google Gemini API key (optional, for Gemini processing)

### Installation

1. **Configure API keys:**
   Edit `.env` file and add your API keys:
   ```
   MISTRAL_API_KEY=your_mistral_key_here
   GEMINI_API_KEY=your_gemini_key_here  # Optional
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

**Start the API server:**
```bash
python main.py
```
The API will be available at `http://localhost:8000`

## API Usage

### Process Document with Mistral (Default)
```bash
curl -X POST "http://localhost:8000/ocr/process" \
  -F "file=@document.pdf" \
  -F "model_name=mistral-ocr" \
  -F "document_type=bank_statement"
```

### Process Document with Gemini
```bash
curl -X POST "http://localhost:8000/ocr/process" \
  -F "file=@document.pdf" \
  -F "model_name=gemini-vision" \
  -F "document_type=bank_statement"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Model Selection

The `model_name` parameter determines which processing approach to use:

- **mistral-ocr** (default) - Uses Mistral OCR + Mistral LLM (2-step process)
- **gemini-vision** - Uses Gemini Vision for direct processing (1-step process)
- **gemini-1.5-pro** - Alternative Gemini model

## Document Types

- **auto** - Auto-detect document type
- **bank_statement** - Extract account info, transactions, and summary
- **invoice** - Extract invoice details, line items, and totals
- **receipt** - Extract store info, items, and total
- **custom** - Use custom JSON schema for extraction

## Processing Approaches

### Mistral Approach (OCR + LLM)
1. **OCR Step**: Extract text from PDF using Mistral OCR
2. **LLM Step**: Structure the extracted text using Mistral LLM
3. **Pros**: Proven accuracy, detailed text extraction
4. **Cons**: Requires 2 API calls, potentially slower

### Gemini Approach (Direct Vision)
1. **Single Step**: Process document directly with Gemini Vision API
2. **Pros**: Faster (1 API call), better context understanding
3. **Cons**: May require more specific prompts for complex schemas

## Modularization Benefits

- **Clean Separation** - Each service has a single responsibility
- **Easy Maintenance** - Changes isolated to specific modules
- **Provider Flexibility** - Easy to add new AI providers
- **Better Testing** - Individual modules can be tested independently
- **Code Reusability** - Services can be reused across different implementations

## License

MIT License
