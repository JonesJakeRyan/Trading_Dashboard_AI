"""
Trade data schemas for validation and serialization
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
import re


class TradeBase(BaseModel):
    """Base trade schema with common fields"""
    symbol: str = Field(..., min_length=1, max_length=10)
    side: Literal["BUY", "SELL"]
    quantity: Decimal = Field(..., gt=0, le=1000000)
    price: Decimal = Field(..., gt=0, le=100000)
    executed_at: datetime
    account_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format"""
        v = v.upper().strip()
        if not re.match(r"^[A-Z]{1,5}(-[A-Z])?$", v):
            raise ValueError(
                f"Invalid symbol format: {v}. Must be 1-5 uppercase letters, "
                "optionally followed by hyphen and letter (e.g., AAPL, BRK-B)"
            )
        return v

    @field_validator("executed_at")
    @classmethod
    def validate_executed_at(cls, v: datetime) -> datetime:
        """Validate execution timestamp"""
        if v > datetime.now(v.tzinfo):
            raise ValueError("Execution time cannot be in the future")
        
        # Check if within last 10 years
        ten_years_ago = datetime.now(v.tzinfo).replace(year=datetime.now().year - 10)
        if v < ten_years_ago:
            raise ValueError("Execution time must be within last 10 years")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100,
                "price": 150.00,
                "executed_at": "2024-01-15T10:30:00-05:00",
                "account_id": "ACCT001",
                "notes": "Initial position"
            }
        }


class TradeCreate(TradeBase):
    """Schema for creating a new trade"""
    pass


class TradeResponse(TradeBase):
    """Schema for trade response"""
    trade_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ValidationError(BaseModel):
    """Schema for validation error response"""
    error: str = "validation_failed"
    message: str
    checklist: Optional[list[str]] = None
    details: Optional[dict] = None


class IngestRequest(BaseModel):
    """Schema for CSV ingest request"""
    template: Literal["webull_v1", "robinhood_v1", "unified_v1"]
    account_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "template": "unified_v1",
                "account_id": "ACCT001"
            }
        }


class IngestResponse(BaseModel):
    """Schema for ingest response"""
    job_id: str
    status: Literal["processing", "completed", "failed"]
    message: str
    trades_processed: int = 0
    trades_failed: int = 0
    errors: Optional[list[ValidationError]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "message": "Successfully processed 10 trades",
                "trades_processed": 10,
                "trades_failed": 0
            }
        }
