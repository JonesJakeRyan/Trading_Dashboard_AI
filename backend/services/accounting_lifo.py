"""
LIFO (Last-In-First-Out) Position Accounting Engine
Matches Webull's broker accounting method for equities.
Equities only - options support removed.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)

# Rounding precision
QTY_DECIMALS = 4
PRICE_DECIMALS = 2


@dataclass
class Lot:
    """Represents a tax lot (FIFO queue entry)"""
    price: float
    qty: float
    time: datetime
    
    def __repr__(self):
        return f"Lot({self.qty}@${self.price:.2f})"


@dataclass
class RoundTripTrade:
    """Completed round-trip trade"""
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


class LIFOEngine:
    """
    LIFO (Last-In-First-Out) position accounting engine.
    
    Matches Webull's broker accounting for equities:
    - Last shares bought are first shares sold
    - Each close matches against newest open lots (stack/LIFO)
    - Tracks long and short positions separately
    - Equities only - options not supported
    """
    
    def __init__(self):
        self.positions: Dict[str, deque] = {}  # symbol -> deque of Lots
        self.completed_trades: List[RoundTripTrade] = []
    
    def process_fills(self, fills: pd.DataFrame) -> pd.DataFrame:
        """
        Process fills chronologically using LIFO accounting.
        
        Args:
            fills: DataFrame with columns [asset_type, symbol, underlying, side, 
                                          qty, price, filled_time, multiplier]
        
        Returns:
            DataFrame of completed round-trip trades
        """
        if len(fills) == 0:
            return pd.DataFrame()
        
        # Filter to equities only
        fills = fills[fills['asset_type'] == 'equity'].copy()
        
        if len(fills) == 0:
            logger.warning("No equity fills found (options not supported)")
            return pd.DataFrame()
        
        # Ensure chronological order
        fills = fills.sort_values('filled_time').reset_index(drop=True)
        
        # Process each fill
        for idx, row in fills.iterrows():
            self._process_fill(
                key=row['symbol'],
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
        
        logger.info(f"Completed {len(trades_df)} round-trip trades (LIFO, equities only)")
        logger.info(f"Open positions: {len([p for p in self.positions.values() if len(p) > 0])}")
        
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
        """Process a single fill using FIFO logic."""
        
        # Round quantity and price
        qty = round(abs(qty), QTY_DECIMALS)
        price = round(price, PRICE_DECIMALS)
        
        if qty <= 0:
            return
        
        # Get or create position queue
        if key not in self.positions:
            self.positions[key] = deque()
        
        queue = self.positions[key]
        
        # Determine if this is opening or closing
        if side in ['buy', 'cover']:
            self._handle_buy(queue, key, underlying, asset_type, qty, price, 
                           filled_time, multiplier)
        elif side in ['sell', 'short']:
            self._handle_sell(queue, key, underlying, asset_type, qty, price, 
                            filled_time, multiplier)
    
    def _handle_buy(
        self,
        queue: deque,
        key: str,
        underlying: str,
        asset_type: str,
        qty: float,
        price: float,
        filled_time: datetime,
        multiplier: float
    ):
        """Handle buy/cover action with FIFO."""
        
        # Check if we're covering a short position
        if len(queue) > 0:
            # Check if front of queue is short (negative qty)
            front_lot = queue[0]
            if front_lot.qty < 0:
                # Covering short position (FIFO)
                self._close_position(
                    queue, key, underlying, asset_type, 'short',
                    qty, price, filled_time, multiplier
                )
                return
        
        # Opening or adding to long position
        queue.append(Lot(price=price, qty=qty, time=filled_time))
    
    def _handle_sell(
        self,
        queue: deque,
        key: str,
        underlying: str,
        asset_type: str,
        qty: float,
        price: float,
        filled_time: datetime,
        multiplier: float
    ):
        """Handle sell/short action with FIFO."""
        
        # Check if we're closing a long position
        if len(queue) > 0:
            # Check if front of queue is long (positive qty)
            front_lot = queue[0]
            if front_lot.qty > 0:
                # Closing long position (FIFO)
                self._close_position(
                    queue, key, underlying, asset_type, 'long',
                    qty, price, filled_time, multiplier
                )
                return
        
        # Opening or adding to short position
        queue.append(Lot(price=price, qty=-qty, time=filled_time))
    
    def _close_position(
        self,
        queue: deque,
        key: str,
        underlying: str,
        asset_type: str,
        direction: str,
        qty: float,
        exit_price: float,
        close_time: datetime,
        multiplier: float
    ):
        """
        Close position using FIFO - match against oldest lots first.
        Only emit trade when position goes completely flat (matches Webull).
        """
        remaining = qty
        total_pnl = 0.0
        entry_notional = 0.0
        exit_notional = 0.0
        qty_closed = 0.0
        first_entry_time = None
        
        # LIFO: process from the END of the queue (most recent lots first)
        while remaining > 1e-8 and len(queue) > 0:
            lot = queue[-1]  # Get LAST lot (most recent)
            
            # Check direction matches
            if direction == 'long' and lot.qty < 0:
                break  # Hit a short lot, stop
            if direction == 'short' and lot.qty > 0:
                break  # Hit a long lot, stop
            
            lot_qty = abs(lot.qty)
            close_qty = min(remaining, lot_qty)
            
            # Calculate P&L for this lot
            if direction == 'long':
                pnl = (exit_price - lot.price) * close_qty * multiplier
            else:  # short
                pnl = (lot.price - exit_price) * close_qty * multiplier
            
            total_pnl += pnl
            entry_notional += lot.price * close_qty
            exit_notional += exit_price * close_qty
            qty_closed += close_qty
            
            if first_entry_time is None:
                first_entry_time = lot.time
            
            # Update or remove lot (LIFO = pop from end)
            if close_qty >= lot_qty - 1e-8:
                queue.pop()  # Remove last lot
            else:
                # Partial close - update last lot quantity
                new_qty = lot_qty - close_qty
                if direction == 'short':
                    new_qty = -new_qty
                queue[-1] = Lot(price=lot.price, qty=new_qty, time=lot.time)
            
            remaining -= close_qty
        
        # Emit trade for every close (LIFO lot matching)
        if qty_closed > 0:
            avg_entry = entry_notional / qty_closed if qty_closed > 0 else 0.0
            avg_exit = exit_notional / qty_closed if qty_closed > 0 else exit_price
            
            trade = RoundTripTrade(
                symbol=key,
                underlying=underlying,
                asset_type=asset_type,
                direction=direction,
                qty_closed=qty_closed,
                avg_entry=round(avg_entry, PRICE_DECIMALS),
                avg_exit=round(avg_exit, PRICE_DECIMALS),
                entry_time=first_entry_time,
                close_time=close_time,
                pnl=round(total_pnl, 2),
                multiplier=multiplier
            )
            self.completed_trades.append(trade)
        
        # If qty remains, open opposite position
        if remaining > 1e-8:
            new_direction = 'short' if direction == 'long' else 'long'
            new_qty = remaining if new_direction == 'long' else -remaining
            queue.append(Lot(price=exit_price, qty=new_qty, time=close_time))
    
    def get_open_positions(self) -> pd.DataFrame:
        """Return DataFrame of currently open positions."""
        open_pos = []
        
        for key, queue in self.positions.items():
            if len(queue) == 0:
                continue
            
            # Sum up all lots
            total_qty = sum(lot.qty for lot in queue)
            
            if abs(total_qty) < 1e-8:
                continue
            
            # Calculate weighted average cost
            total_cost = sum(lot.price * abs(lot.qty) for lot in queue)
            total_abs_qty = sum(abs(lot.qty) for lot in queue)
            avg_cost = total_cost / total_abs_qty if total_abs_qty > 0 else 0.0
            
            # Get earliest entry time
            entry_time = min(lot.time for lot in queue)
            
            open_pos.append({
                'symbol': key,
                'pos_qty': total_qty,
                'avg_cost': avg_cost,
                'entry_time': entry_time,
                'direction': 'long' if total_qty > 0 else 'short',
                'num_lots': len(queue)
            })
        
        if not open_pos:
            return pd.DataFrame()
        
        return pd.DataFrame(open_pos)
