"""
Average-Cost Position Accounting Engine
Implements round-trip trade tracking with volume-weighted entry/exit prices.
No fees are included in P&L calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Rounding precision
QTY_DECIMALS = 4
PRICE_DECIMALS = 2


@dataclass
class Position:
    """Represents an open position with average cost tracking."""
    pos_qty: float = 0.0  # Signed quantity (+ long, - short)
    avg_cost: float = 0.0  # Average cost basis
    entry_time: Optional[datetime] = None  # When position first opened
    
    # Accumulators for volume-weighted averages
    entry_notional: float = 0.0  # Sum of (price * qty) on entries
    exit_notional: float = 0.0   # Sum of (price * qty) on exits
    qty_in: float = 0.0           # Total qty entered
    qty_out: float = 0.0          # Total qty exited
    
    def is_flat(self) -> bool:
        """Check if position is flat (zero quantity)."""
        return abs(self.pos_qty) < 1e-8


@dataclass
class RoundTripTrade:
    """Represents a completed round-trip trade (flat → flat)."""
    symbol: str
    underlying: str
    asset_type: str
    direction: str  # 'long' or 'short'
    qty_closed: float
    avg_entry: float
    avg_exit: float
    entry_time: datetime
    close_time: datetime
    pnl: float
    multiplier: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame."""
        return {
            'symbol': self.symbol,
            'underlying': self.underlying,
            'asset_type': self.asset_type,
            'direction': self.direction,
            'qty_closed': self.qty_closed,
            'avg_entry': self.avg_entry,
            'avg_exit': self.avg_exit,
            'entry_time': self.entry_time,
            'close_time': self.close_time,
            'pnl': self.pnl,
            'multiplier': self.multiplier
        }


class AverageCostEngine:
    """
    Average-cost position accounting engine.
    Tracks positions per symbol and emits round-trip trades when flat.
    """
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}  # key -> Position
        self.completed_trades: List[RoundTripTrade] = []
        
    def process_fills(self, fills: pd.DataFrame) -> pd.DataFrame:
        """
        Process fills chronologically and return completed round-trip trades.
        
        Args:
            fills: DataFrame with columns [asset_type, symbol, underlying, side, 
                                          qty, price, filled_time, multiplier]
        
        Returns:
            DataFrame of completed round-trip trades
        """
        self.positions = {}
        self.completed_trades = []
        
        if len(fills) == 0:
            return pd.DataFrame()
        
        # Ensure sorted by time
        fills = fills.sort_values('filled_time').reset_index(drop=True)
        
        # Process each fill
        for idx, row in fills.iterrows():
            self._process_fill(
                key=row['symbol'],  # Use full symbol as key
                underlying=row['underlying'],
                asset_type=row['asset_type'],
                side=row['side'],
                qty=row['qty'],
                price=row['price'],
                filled_time=row['filled_time'],
                multiplier=row['multiplier']
            )
        
        # Convert to DataFrame
        if not self.completed_trades:
            logger.info("No completed round-trip trades found")
            return pd.DataFrame()
        
        trades_df = pd.DataFrame([t.to_dict() for t in self.completed_trades])
        
        logger.info(f"Completed {len(trades_df)} round-trip trades")
        logger.info(f"Open positions: {len([p for p in self.positions.values() if not p.is_flat()])}")
        
        return trades_df
    
    def _process_fill(
        self,
        key: str,
        underlying: str,
        asset_type: str,
        side: str,
        qty: float,
        price: float,
        filled_time: datetime,
        multiplier: float
    ):
        """Process a single fill and update position."""
        
        # Round quantity and price
        qty = round(abs(qty), QTY_DECIMALS)
        price = round(price, PRICE_DECIMALS)
        
        if qty <= 0:
            return
        
        # Get or create position
        if key not in self.positions:
            self.positions[key] = Position()
        
        pos = self.positions[key]
        
        # Determine action based on side and current position
        if side in ['buy', 'cover']:
            self._handle_buy(pos, key, underlying, asset_type, qty, price, 
                           filled_time, multiplier)
        elif side in ['sell', 'short']:
            self._handle_sell(pos, key, underlying, asset_type, qty, price, 
                            filled_time, multiplier)
    
    def _handle_buy(
        self,
        pos: Position,
        key: str,
        underlying: str,
        asset_type: str,
        qty: float,
        price: float,
        filled_time: datetime,
        multiplier: float
    ):
        """Handle buy/cover action."""
        
        if pos.pos_qty >= 0:
            # Long increase: adding to long or opening new long
            if pos.is_flat():
                # Opening new long position
                pos.pos_qty = qty
                pos.avg_cost = price
                pos.entry_time = filled_time
                pos.entry_notional = price * qty
                pos.exit_notional = 0.0
                pos.qty_in = qty
                pos.qty_out = 0.0
            else:
                # Adding to existing long
                new_notional = pos.avg_cost * pos.pos_qty + price * qty
                new_qty = pos.pos_qty + qty
                pos.avg_cost = new_notional / new_qty
                pos.pos_qty = new_qty
                pos.entry_notional += price * qty
                pos.qty_in += qty
        else:
            # Covering short position
            close_qty = min(qty, abs(pos.pos_qty))
            
            # Calculate P&L: (avg_cost - price) * close_qty * multiplier
            pnl = (pos.avg_cost - price) * close_qty * multiplier
            
            # Track exit
            pos.exit_notional += price * close_qty
            pos.qty_out += close_qty
            
            # Update position
            pos.pos_qty += close_qty
            
            # Check if position is now flat
            if pos.is_flat():
                # Emit round-trip trade
                avg_entry = pos.entry_notional / pos.qty_in if pos.qty_in > 0 else pos.avg_cost
                avg_exit = pos.exit_notional / pos.qty_out if pos.qty_out > 0 else price
                
                trade = RoundTripTrade(
                    symbol=key,
                    underlying=underlying,
                    asset_type=asset_type,
                    direction='short',
                    qty_closed=pos.qty_out,
                    avg_entry=round(avg_entry, PRICE_DECIMALS),
                    avg_exit=round(avg_exit, PRICE_DECIMALS),
                    entry_time=pos.entry_time,
                    close_time=filled_time,
                    pnl=round(pnl, 2),
                    multiplier=multiplier
                )
                self.completed_trades.append(trade)
                
                # Reset position
                pos.pos_qty = 0.0
                pos.avg_cost = 0.0
                pos.entry_time = None
                pos.entry_notional = 0.0
                pos.exit_notional = 0.0
                pos.qty_in = 0.0
                pos.qty_out = 0.0
            
            # If qty remains, open new long
            remaining = qty - close_qty
            if remaining > 1e-8:
                pos.pos_qty = remaining
                pos.avg_cost = price
                pos.entry_time = filled_time
                pos.entry_notional = price * remaining
                pos.exit_notional = 0.0
                pos.qty_in = remaining
                pos.qty_out = 0.0
    
    def _handle_sell(
        self,
        pos: Position,
        key: str,
        underlying: str,
        asset_type: str,
        qty: float,
        price: float,
        filled_time: datetime,
        multiplier: float
    ):
        """Handle sell/short action."""
        
        if pos.pos_qty <= 0:
            # Short increase: adding to short or opening new short
            if pos.is_flat():
                # Opening new short position
                pos.pos_qty = -qty
                pos.avg_cost = price
                pos.entry_time = filled_time
                pos.entry_notional = price * qty
                pos.exit_notional = 0.0
                pos.qty_in = qty
                pos.qty_out = 0.0
            else:
                # Adding to existing short
                new_notional = pos.avg_cost * abs(pos.pos_qty) + price * qty
                new_qty = abs(pos.pos_qty) + qty
                pos.avg_cost = new_notional / new_qty
                pos.pos_qty = -new_qty
                pos.entry_notional += price * qty
                pos.qty_in += qty
        else:
            # Closing long position
            close_qty = min(qty, pos.pos_qty)
            
            # Calculate P&L: (price - avg_cost) * close_qty * multiplier
            pnl = (price - pos.avg_cost) * close_qty * multiplier
            
            # Track exit
            pos.exit_notional += price * close_qty
            pos.qty_out += close_qty
            
            # Update position
            pos.pos_qty -= close_qty
            
            # Check if position is now flat
            if pos.is_flat():
                # Emit round-trip trade
                avg_entry = pos.entry_notional / pos.qty_in if pos.qty_in > 0 else pos.avg_cost
                avg_exit = pos.exit_notional / pos.qty_out if pos.qty_out > 0 else price
                
                trade = RoundTripTrade(
                    symbol=key,
                    underlying=underlying,
                    asset_type=asset_type,
                    direction='long',
                    qty_closed=pos.qty_out,
                    avg_entry=round(avg_entry, PRICE_DECIMALS),
                    avg_exit=round(avg_exit, PRICE_DECIMALS),
                    entry_time=pos.entry_time,
                    close_time=filled_time,
                    pnl=round(pnl, 2),
                    multiplier=multiplier
                )
                self.completed_trades.append(trade)
                
                # Reset position
                pos.pos_qty = 0.0
                pos.avg_cost = 0.0
                pos.entry_time = None
                pos.entry_notional = 0.0
                pos.exit_notional = 0.0
                pos.qty_in = 0.0
                pos.qty_out = 0.0
            
            # If qty remains, open new short
            remaining = qty - close_qty
            if remaining > 1e-8:
                pos.pos_qty = -remaining
                pos.avg_cost = price
                pos.entry_time = filled_time
                pos.entry_notional = price * remaining
                pos.exit_notional = 0.0
                pos.qty_in = remaining
                pos.qty_out = 0.0
    
    def get_open_positions(self) -> pd.DataFrame:
        """Return DataFrame of currently open positions."""
        open_pos = []
        
        for key, pos in self.positions.items():
            if not pos.is_flat():
                open_pos.append({
                    'symbol': key,
                    'pos_qty': pos.pos_qty,
                    'avg_cost': pos.avg_cost,
                    'entry_time': pos.entry_time,
                    'direction': 'long' if pos.pos_qty > 0 else 'short'
                })
        
        if not open_pos:
            return pd.DataFrame()
        
        return pd.DataFrame(open_pos)
