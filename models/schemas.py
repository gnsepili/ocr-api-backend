"""
Pydantic Models and JSON Schemas - V5 (Flexible Validation)
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field

# --- A generic model for the {"value": ...} structure ---
class FieldValue(BaseModel):
    value: Optional[Any] = None

# --- Sub-models using the FieldValue structure ---

class BasicInformation(BaseModel):
    bank_name: Optional[FieldValue] = None
    account_name: Optional[FieldValue] = None
    account_number: Optional[FieldValue] = None
    ifsc_code: Optional[FieldValue] = None
    start_date: Optional[FieldValue] = None
    end_date: Optional[FieldValue] = None
    account_address: Optional[FieldValue] = None
    opening_balance: Optional[FieldValue] = None
    closing_balance: Optional[FieldValue] = None

class TransactionItem(BaseModel):
    date: Optional[FieldValue] = None
    description: Optional[FieldValue] = None
    debit: Optional[FieldValue] = None
    credit: Optional[FieldValue] = None
    balance: Optional[FieldValue] = None
    category: Optional[FieldValue] = None
    merchant_name: Optional[FieldValue] = None

class ExtractedData(BaseModel):
    basic_information: Optional[BasicInformation] = None # Allow this to be optional
    transactions: Optional[List[TransactionItem]] = None # Allow this to be optional

# --- Main API Request/Response Models ---

class OCRResponse(BaseModel):
    status: str
    data: Optional[Union[ExtractedData, Dict[str, Any]]] = None
    schema_used: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_ms: int
    pages_processed: int
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str = "OCR Microservice"
    version: str = "1.0.0"

# --- Revamped Default JSON Schema for Gemini ---
DEFAULT_SCHEMAS = {
    "bank_statement": {
        "type": "object",
        "properties": {
            "basic_information": {
                "type": ["object", "null"],
                "properties": {
                    "bank_name": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                    "account_name": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                    "account_number": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                    "ifsc_code": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                    "start_date": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"], "description": "YYYY-MM-DD format"}}},
                    "end_date": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"], "description": "YYYY-MM-DD format"}}},
                    "account_address": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                    "opening_balance": {"type": ["object", "null"], "properties": {"value": {"type": ["number", "null"]}}},
                    "closing_balance": {"type": ["object", "null"], "properties": {"value": {"type": ["number", "null"]}}}
                }
            },
            "transactions": {
                "type": ["array", "null"], # FIX: Allow the list of transactions to be null
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"], "description": "YYYY-MM-DD format"}}},
                        "description": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"]}}},
                        "debit": {"type": ["object", "null"], "properties": {"value": {"type": ["number", "null"], "description": "Withdrawal amount. Use null if it is a deposit."}}},
                        "credit": {"type": ["object", "null"], "properties": {"value": {"type": ["number", "null"], "description": "Deposit amount. Use null if it is a withdrawal."}}},
                        "balance": {"type": ["object", "null"], "properties": {"value": {"type": ["number", "null"]}}},
                        "category": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"], "description": "Categorize: e.g., 'Salary', 'Transfer', 'Interest', etc."}}},
                        "merchant_name": {"type": ["object", "null"], "properties": {"value": {"type": ["string", "null"], "description": "The merchant or person's name."}}}
                    }
                }
            }
        },
        "required": ["basic_information", "transactions"]
    },
    # ... other schemas ...
}
