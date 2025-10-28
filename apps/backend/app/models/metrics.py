"""
Metrics models for daily P&L and aggregates
"""
from sqlalchemy import Column, String, Numeric, Date, DateTime, Integer, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.models.base import Base


class PerDayPnL(Base):
    """
    Daily realized P&L series (EST timezone).
    One row per calendar day with trading activity.
    Continuous series with zero-filled gaps for charting.
    """
    __tablename__ = "per_day_pnl"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=True, index=True)
    
    # Calendar date (EST)
    date = Column(Date, nullable=False, index=True)
    
    # Cumulative realized P&L up to and including this date
    cumulative_pnl = Column(Numeric(precision=18, scale=2), nullable=False)
    
    # Daily realized P&L for this date
    daily_pnl = Column(Numeric(precision=18, scale=2), nullable=False)
    
    # Number of lots closed on this date
    lots_closed = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_account_date', 'account_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<PerDayPnL {self.date} cumulative=${self.cumulative_pnl}>"


class Aggregate(Base):
    """
    Aggregate metrics across all trades.
    Recalculated whenever trades are processed.
    """
    __tablename__ = "aggregates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=True, index=True, unique=True)
    
    # Total metrics
    total_realized_pnl = Column(Numeric(precision=18, scale=2), nullable=False, default=0)
    total_lots_closed = Column(Integer, nullable=False, default=0)
    total_trades = Column(Integer, nullable=False, default=0)
    
    # Win/Loss metrics
    winning_lots = Column(Integer, nullable=False, default=0)
    losing_lots = Column(Integer, nullable=False, default=0)
    total_gains = Column(Numeric(precision=18, scale=2), nullable=False, default=0)
    total_losses = Column(Numeric(precision=18, scale=2), nullable=False, default=0)
    
    # Calculated ratios
    win_rate = Column(Numeric(precision=5, scale=4), nullable=True)  # 0.0 to 1.0
    profit_factor = Column(Numeric(precision=10, scale=2), nullable=True)  # gains / abs(losses)
    average_gain = Column(Numeric(precision=18, scale=2), nullable=True)
    average_loss = Column(Numeric(precision=18, scale=2), nullable=True)
    
    # Best/Worst performance
    best_symbol = Column(String(10), nullable=True)
    best_symbol_pnl = Column(Numeric(precision=18, scale=2), nullable=True)
    worst_symbol = Column(String(10), nullable=True)
    worst_symbol_pnl = Column(Numeric(precision=18, scale=2), nullable=True)
    
    best_weekday = Column(String(10), nullable=True)  # Monday, Tuesday, etc.
    best_weekday_pnl = Column(Numeric(precision=18, scale=2), nullable=True)
    worst_weekday = Column(String(10), nullable=True)
    worst_weekday_pnl = Column(Numeric(precision=18, scale=2), nullable=True)
    
    # Date range
    first_trade_date = Column(Date, nullable=True)
    last_trade_date = Column(Date, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Aggregate total_pnl=${self.total_realized_pnl} win_rate={self.win_rate}>"
