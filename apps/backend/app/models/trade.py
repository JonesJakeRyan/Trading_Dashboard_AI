"""
Trade models for normalized trades and closed lots
"""
from sqlalchemy import Column, String, Numeric, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.models.base import Base


class NormalizedTrade(Base):
    """
    Normalized trade record after CSV parsing and validation.
    One row per trade execution.
    """
    __tablename__ = "normalized_trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    price = Column(Numeric(precision=18, scale=2), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    notes = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ingest_job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_symbol_executed_at', 'symbol', 'executed_at'),
        Index('idx_account_symbol', 'account_id', 'symbol'),
    )
    
    def __repr__(self):
        return f"<NormalizedTrade {self.symbol} {self.side} {self.quantity}@{self.price}>"


class ClosedLot(Base):
    """
    Closed position lot with realized P&L.
    Created by FIFO matching engine.
    Supports both long (BUY→SELL) and short (SELL→BUY) positions.
    """
    __tablename__ = "closed_lots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Position type
    position_type = Column(String(10), nullable=False)  # LONG or SHORT
    
    # Opening trade (BUY for long, SELL for short)
    open_trade_id = Column(UUID(as_uuid=True), nullable=False)
    open_quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    open_price = Column(Numeric(precision=18, scale=2), nullable=False)
    open_executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Closing trade (SELL for long, BUY for short)
    close_trade_id = Column(UUID(as_uuid=True), nullable=False)
    close_quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    close_price = Column(Numeric(precision=18, scale=2), nullable=False)
    close_executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Realized P&L (USD)
    # For LONG: (close_price - open_price) * quantity
    # For SHORT: (open_price - close_price) * quantity
    realized_pnl = Column(Numeric(precision=18, scale=2), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_symbol_close_date', 'symbol', 'close_executed_at'),
        Index('idx_account_close_date', 'account_id', 'close_executed_at'),
    )
    
    def __repr__(self):
        return f"<ClosedLot {self.symbol} {self.position_type} P&L=${self.realized_pnl}>"
