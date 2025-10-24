"""
Position Tracker Service
Implements average-cost position accounting for accurate P&L tracking.
Tracks running positions per symbol with average cost basis.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a running position with average cost"""
    symbol: str
    quantity: float
    avg_cost: float
    direction: str  # 'long' or 'short'
    entry_time: datetime
    total_fees: float
    
    def is_closed(self) -> bool:
        """Check if position is fully closed"""
        return abs(self.quantity) < 0.01


@dataclass
class ClosedPosition:
    """Represents a completed round-trip position"""
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    avg_entry_price: float
    avg_exit_price: float
    quantity: float
    total_entry_fees: float
    total_exit_fees: float
    realized_pnl: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'avg_entry_price': self.avg_entry_price,
            'avg_exit_price': self.avg_exit_price,
            'quantity': self.quantity,
            'total_entry_fees': self.total_entry_fees,
            'total_exit_fees': self.total_exit_fees,
            'realized_pnl': self.realized_pnl,
            'hold_time_days': (self.exit_time - self.entry_time).total_seconds() / 86400
        }


class PositionTracker:
    """
    Tracks positions using average-cost accounting.
    Counts trades as complete round-trips (position goes to 0).
    """
    
    def __init__(self, dead_zone: float = 0.50):
        """
        Initialize position tracker.
        
        Args:
            dead_zone: Minimum P&L to count as win (below this = loss)
        """
        self.positions: Dict[str, Position] = {}  # {symbol: Position}
        self.closed_positions: List[ClosedPosition] = []
        self.dead_zone = dead_zone
        
    def process_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process orders and track positions with average cost.
        
        Args:
            df: DataFrame with columns [Symbol, Side, Quantity, Price, Fees, Date]
            
        Returns:
            DataFrame of closed positions
        """
        # Reset state
        self.positions = {}
        self.closed_positions = []
        
        # Sort chronologically
        df = df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
        
        # Process each order
        for idx, row in df.iterrows():
            self._process_order(
                symbol=row['Symbol'],
                side=str(row['Side']).lower(),
                quantity=row['Quantity'],
                price=row['Price'],
                fees=row['Fees'],
                timestamp=row['Date']
            )
        
        # Convert closed positions to DataFrame
        if not self.closed_positions:
            return pd.DataFrame()
        
        positions_data = [pos.to_dict() for pos in self.closed_positions]
        positions_df = pd.DataFrame(positions_data)
        
        logger.info(f"Tracked {len(self.closed_positions)} closed positions from {len(df)} orders")
        logger.info(f"Open positions remaining: {len(self.positions)}")
        
        return positions_df
    
    def _process_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime
    ):
        """Process a single order and update position"""
        
        # Determine if this is opening or closing
        if side in ['buy', 'bought']:
            self._handle_buy(symbol, quantity, price, fees, timestamp)
        elif side in ['sell', 'sold', 'sell to close']:
            self._handle_sell(symbol, quantity, price, fees, timestamp)
        elif side in ['short', 'sell short']:
            self._handle_short(symbol, quantity, price, fees, timestamp)
        elif side in ['buy to cover', 'cover']:
            self._handle_cover(symbol, quantity, price, fees, timestamp)
    
    def _handle_buy(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime
    ):
        """Handle buy order (open long or close short)"""
        
        if symbol not in self.positions:
            # Open new long position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                direction='long',
                entry_time=timestamp,
                total_fees=fees
            )
        else:
            pos = self.positions[symbol]
            
            if pos.direction == 'short':
                # Closing short position
                self._close_position(symbol, quantity, price, fees, timestamp, 'short')
            else:
                # Adding to long position - update average cost
                total_cost = (pos.avg_cost * pos.quantity) + (price * quantity)
                total_qty = pos.quantity + quantity
                pos.avg_cost = total_cost / total_qty
                pos.quantity = total_qty
                pos.total_fees += fees
    
    def _handle_sell(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime
    ):
        """Handle sell order (close long or open short)"""
        
        if symbol not in self.positions:
            # Open new short position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                direction='short',
                entry_time=timestamp,
                total_fees=fees
            )
        else:
            pos = self.positions[symbol]
            
            if pos.direction == 'long':
                # Closing long position
                self._close_position(symbol, quantity, price, fees, timestamp, 'long')
            else:
                # Adding to short position - update average cost
                total_cost = (pos.avg_cost * pos.quantity) + (price * quantity)
                total_qty = pos.quantity + quantity
                pos.avg_cost = total_cost / total_qty
                pos.quantity = total_qty
                pos.total_fees += fees
    
    def _handle_short(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime
    ):
        """Handle short order (open short position)"""
        self._handle_sell(symbol, quantity, price, fees, timestamp)
    
    def _handle_cover(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: datetime
    ):
        """Handle cover order (close short position)"""
        self._handle_buy(symbol, quantity, price, fees, timestamp)
    
    def _close_position(
        self,
        symbol: str,
        quantity: float,
        exit_price: float,
        exit_fees: float,
        exit_time: datetime,
        direction: str
    ):
        """Close position (partial or full) and calculate realized P&L"""
        
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        
        # Determine quantity to close
        qty_to_close = min(quantity, pos.quantity)
        
        # Calculate proportional fees
        fee_ratio = qty_to_close / pos.quantity if pos.quantity > 0 else 0
        entry_fees = pos.total_fees * fee_ratio
        
        # Calculate realized P&L
        if direction == 'long':
            # Long: profit = (exit - entry) * qty - fees
            raw_pnl = (exit_price - pos.avg_cost) * qty_to_close
        else:
            # Short: profit = (entry - exit) * qty - fees
            raw_pnl = (pos.avg_cost - exit_price) * qty_to_close
        
        realized_pnl = raw_pnl - entry_fees - exit_fees
        
        # Apply dead zone
        if abs(realized_pnl) < self.dead_zone:
            realized_pnl = -abs(realized_pnl)  # Treat as loss
        
        # Check if position is fully closed
        if qty_to_close >= pos.quantity:
            # Full close - create closed position record
            closed_pos = ClosedPosition(
                symbol=symbol,
                direction=direction,
                entry_time=pos.entry_time,
                exit_time=exit_time,
                avg_entry_price=pos.avg_cost,
                avg_exit_price=exit_price,
                quantity=pos.quantity,
                total_entry_fees=pos.total_fees,
                total_exit_fees=exit_fees,
                realized_pnl=realized_pnl
            )
            self.closed_positions.append(closed_pos)
            
            # Remove position
            del self.positions[symbol]
        else:
            # Partial close - update position
            pos.quantity -= qty_to_close
            pos.total_fees -= entry_fees
            
            # Still record the partial close as a closed position
            closed_pos = ClosedPosition(
                symbol=symbol,
                direction=direction,
                entry_time=pos.entry_time,
                exit_time=exit_time,
                avg_entry_price=pos.avg_cost,
                avg_exit_price=exit_price,
                quantity=qty_to_close,
                total_entry_fees=entry_fees,
                total_exit_fees=exit_fees,
                realized_pnl=realized_pnl
            )
            self.closed_positions.append(closed_pos)
    
    def get_open_positions(self) -> pd.DataFrame:
        """Return DataFrame of currently open positions"""
        if not self.positions:
            return pd.DataFrame()
        
        open_pos = []
        for symbol, pos in self.positions.items():
            open_pos.append({
                'symbol': symbol,
                'direction': pos.direction,
                'quantity': pos.quantity,
                'avg_cost': pos.avg_cost,
                'entry_time': pos.entry_time,
                'total_fees': pos.total_fees
            })
        
        return pd.DataFrame(open_pos)
