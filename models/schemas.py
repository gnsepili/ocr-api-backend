"""
Pydantic Models and JSON Schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Request/Response Models
class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    model_name: str = "mistral-ocr"
    document_type: Optional[str] = "auto"
    extract_tables: bool = True
    custom_schema: Optional[str] = None

class OCRResponse(BaseModel):
    """Response model for OCR processing"""
    status: str
    data: Optional[Dict[str, Any]] = None
    schema_used: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_ms: int
    pages_processed: int
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str = "OCR Microservice"
    version: str = "1.0.0"

# Default JSON Schemas for different document types
DEFAULT_SCHEMAS = {
    "bank_statement": {
        "type": "object",
        "properties": {
            "account_info": {
                "type": "object",
                "properties": {
                    "account_holder": {"type": "string"},
                    "account_number": {"type": "string"},
                    "ifsc_code": {"type": "string"},
                    "branch": {"type": "string"},
                    "currency": {"type": "string"}
                }
            },
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "narration": {"type": "string"},
                        "withdrawal": {"type": ["string", "null"]},
                        "deposit": {"type": ["string", "null"]},
                        "balance": {"type": ["string", "null"]}
                    }
                }
            },
            "statement_summary": {
                "type": "object",
                "properties": {
                    "opening_balance": {"type": "string"},
                    "total_withdrawal": {"type": "string"},
                    "total_deposit": {"type": "string"},
                    "closing_balance": {"type": "string"}
                }
            }
        }
    },
    "invoice": {
        "type": "object",
        "properties": {
            "invoice_info": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "invoice_date": {"type": "string"},
                    "due_date": {"type": "string"}
                }
            },
            "vendor_info": {
                "type": "object",
                "properties": {
                    "vendor_name": {"type": "string"},
                    "vendor_address": {"type": "string"},
                    "vendor_phone": {"type": "string"}
                }
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "amount": {"type": "number"}
                    }
                }
            },
            "totals": {
                "type": "object",
                "properties": {
                    "subtotal": {"type": "number"},
                    "tax": {"type": "number"},
                    "grand_total": {"type": "number"}
                }
            }
        }
    },
    "receipt": {
        "type": "object",
        "properties": {
            "store_info": {
                "type": "object",
                "properties": {
                    "store_name": {"type": "string"},
                    "store_address": {"type": "string"},
                    "store_phone": {"type": "string"}
                }
            },
            "transaction_info": {
                "type": "object",
                "properties": {
                    "receipt_number": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"}
                }
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "price": {"type": "number"}
                    }
                }
            },
            "total": {"type": "number"}
        }
    }
}
