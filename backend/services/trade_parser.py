"""
Trade Parser Service
Handles FIFO-based trade matching from order-level CSV data.
Converts raw orders into complete trade pairs (entry/exit).
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position waiting to be closed"""
    quantity: float
    price: float
    fees: float
    timestamp: datetime
    position_type: str  # 'long' or 'short'


@dataclass
class Trade:
    """Represents a complete trade (entry + exit)"""
    symbol: str
    direction: str  # 'long' or 'short'
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    entry_fees: float
    exit_fees: float
    pnl: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary"""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'entry_fees': self.entry_fees,
            'exit_fees': self.exit_fees,
            'pnl': self.pnl,
            'hold_time_days': (self.exit_time - self.entry_time).total_seconds() / 86400
        }


class TradeParser:
    """
    Parses order-level data and matches trades using FIFO logic.
    Handles partial fills and multiple entries per symbol.
    """
    
    def __init__(self):
        self.positions: Dict[str, List[Position]] = {}  # {symbol: [Position, ...]}
        self.completed_trades: List[Trade] = []
        
    def parse_orders(self, df: pd.DataFrame, consolidate_sessions: bool = True) -> pd.DataFrame:
        """
        Parse order-level DataFrame and return completed trades.
        
        Args:
            df: DataFrame with columns [Symbol, Side, Quantity, Price, Fees, Date]
            consolidate_sessions: If True, merge trades from same symbol/day into sessions
            
        Returns:
            DataFrame of completed trades with columns [symbol, direction, entry_time, 
            exit_time, entry_price, exit_price, quantity, pnl, etc.]
        """
        # Reset state
        self.positions = {}
        self.completed_trades = []
        
        # Sort by symbol and date for chronological processing
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
        
        # Convert completed trades to DataFrame
        if not self.completed_trades:
            return pd.DataFrame()
        
        trades_data = [trade.to_dict() for trade in self.completed_trades]
        trades_df = pd.DataFrame(trades_data)
        
        # Optionally consolidate trades into sessions
        if consolidate_sessions and len(trades_df) > 0:
            trades_df = self._consolidate_trade_sessions(trades_df)
        
        logger.info(f"Parsed {len(trades_df)} completed trades from {len(df)} orders")
        logger.info(f"Open positions remaining: {sum(len(pos) for pos in self.positions.values())}")
        
        return trades_df
    
    def _consolidate_trade_sessions(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Consolidate multiple partial fills into single trade sessions.
        Groups trades by symbol and day, using weighted averages for prices.
        """
        if len(trades_df) == 0:
            return trades_df
        
        # Add date column for grouping
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_time']).dt.date
        
        consolidated = []
        
        # Group by symbol and exit date
        for (symbol, exit_date), group in trades_df.groupby(['symbol', 'exit_date']):
            # Calculate weighted average prices
            total_qty = group['quantity'].sum()
            weighted_entry = (group['entry_price'] * group['quantity']).sum() / total_qty
            weighted_exit = (group['exit_price'] * group['quantity']).sum() / total_qty
            
            # Sum P&L and fees
            total_pnl = group['pnl'].sum()
            total_entry_fees = group['entry_fees'].sum()
            total_exit_fees = group['exit_fees'].sum()
            
            # Use earliest entry time and latest exit time
            entry_time = group['entry_time'].min()
            exit_time = group['exit_time'].max()
            
            # Most common direction
            direction = group['direction'].mode()[0] if len(group) > 0 else group['direction'].iloc[0]
            
            consolidated.append({
                'symbol': symbol,
                'direction': direction,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': weighted_entry,
                'exit_price': weighted_exit,
                'quantity': total_qty,
                'entry_fees': total_entry_fees,
                'exit_fees': total_exit_fees,
                'pnl': total_pnl,
                'hold_time_days': (exit_time - entry_time).total_seconds() / 86400,
                'num_fills': len(group)  # Track how many partial fills were consolidated
            })
        
        result_df = pd.DataFrame(consolidated)
        logger.info(f"Consolidated {len(trades_df)} trades into {len(result_df)} sessions")
        
        return result_df
    
    def _process_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float, 
        fees: float, 
        timestamp: datetime
    ):
        """Process a single order and match against open positions using FIFO"""
        
        if symbol not in self.positions:
            self.positions[symbol] = []
        
        if side in ['buy', 'bought']:
            # Opening a long position
            self._open_position(symbol, quantity, price, fees, timestamp, 'long')
            
        elif side in ['short', 'sell short']:
            # Opening a short position
            self._open_position(symbol, quantity, price, fees, timestamp, 'short')
            
        elif side in ['sell', 'sold', 'sell to close']:
            # Closing long positions OR opening short if no longs exist
            self._close_positions(symbol, quantity, price, fees, timestamp, 'long')
            
        elif side in ['buy to cover', 'cover']:
            # Closing short positions
            self._close_positions(symbol, quantity, price, fees, timestamp, 'short')
    
    def _open_position(
        self, 
        symbol: str, 
        quantity: float, 
        price: float, 
        fees: float, 
        timestamp: datetime,
        position_type: str
    ):
        """Add a new open position"""
        position = Position(
            quantity=quantity,
            price=price,
            fees=fees,
            timestamp=timestamp,
            position_type=position_type
        )
        self.positions[symbol].append(position)
    
    def _close_positions(
        self, 
        symbol: str, 
        quantity: float, 
        price: float, 
        fees: float, 
        timestamp: datetime,
        position_type: str
    ):
        """
        Close positions using FIFO matching.
        
        Args:
            position_type: 'long' means we're selling (closing longs), 
                          'short' means we're covering (closing shorts)
        """
        remaining_qty = quantity
        exit_fees_per_share = fees / quantity if quantity > 0 else 0
        
        # Match against open positions (FIFO - oldest first)
        while remaining_qty > 0 and len(self.positions[symbol]) > 0:
            oldest_position = self.positions[symbol][0]
            
            # Only match positions of the same type
            if oldest_position.position_type != position_type:
                # If no matching positions, treat as opening opposite position
                opposite_type = 'short' if position_type == 'long' else 'long'
                self._open_position(symbol, remaining_qty, price, fees, timestamp, opposite_type)
                break
            
            # Determine how much to close
            qty_to_close = min(remaining_qty, oldest_position.quantity)
            
            # Calculate fees for this portion
            exit_fees = exit_fees_per_share * qty_to_close
            entry_fees = oldest_position.fees * (qty_to_close / oldest_position.quantity)
            
            # Calculate P&L
            if position_type == 'long':
                # Closing long: profit = (exit - entry) * qty - fees
                pnl = (price - oldest_position.price) * qty_to_close - entry_fees - exit_fees
            else:
                # Closing short: profit = (entry - exit) * qty - fees
                pnl = (oldest_position.price - price) * qty_to_close - entry_fees - exit_fees
            
            # Create completed trade
            trade = Trade(
                symbol=symbol,
                direction=position_type,
                entry_time=oldest_position.timestamp,
                exit_time=timestamp,
                entry_price=oldest_position.price,
                exit_price=price,
                quantity=qty_to_close,
                entry_fees=entry_fees,
                exit_fees=exit_fees,
                pnl=pnl
            )
            self.completed_trades.append(trade)
            
            # Update position or remove if fully closed
            if qty_to_close >= oldest_position.quantity:
                # Fully closed - remove position
                self.positions[symbol].pop(0)
            else:
                # Partially closed - update remaining quantity and fees
                self.positions[symbol][0].quantity -= qty_to_close
                self.positions[symbol][0].fees -= entry_fees
            
            remaining_qty -= qty_to_close
        
        # If quantity remains and no positions to close, open opposite position
        if remaining_qty > 0:
            opposite_type = 'short' if position_type == 'long' else 'long'
            self._open_position(symbol, remaining_qty, price, fees, timestamp, opposite_type)
    
    def get_open_positions(self) -> pd.DataFrame:
        """Return DataFrame of currently open positions"""
        open_positions = []
        for symbol, positions in self.positions.items():
            for pos in positions:
                open_positions.append({
                    'symbol': symbol,
                    'type': pos.position_type,
                    'quantity': pos.quantity,
                    'entry_price': pos.price,
                    'entry_time': pos.timestamp,
                    'entry_fees': pos.fees
                })
        
        if not open_positions:
            return pd.DataFrame()
        
        return pd.DataFrame(open_positions)


def parse_csv(content: str) -> pd.DataFrame:
    """
    Parse and standardize CSV data from various broker formats.
    
    Args:
        content: CSV file content as string
        
    Returns:
        Standardized DataFrame with columns: Date, Symbol, Quantity, Price, Side, Fees
    """
    from io import StringIO
    
    try:
        # Read CSV
        df = pd.read_csv(StringIO(content))
        
        # Column mapping for various broker formats
        column_mapping = {
            'date': 'Date', 'Date': 'Date', 'datetime': 'Date', 'time': 'Date',
            'Filled Time': 'Date', 'Placed Time': 'Date',
            'symbol': 'Symbol', 'Symbol': 'Symbol', 'ticker': 'Symbol', 'Ticker': 'Symbol',
            'quantity': 'Quantity', 'Quantity': 'Quantity', 'qty': 'Quantity', 'Qty': 'Quantity',
            'Filled': 'Quantity', 'Total Qty': 'Quantity',
            'price': 'Price', 'Price': 'Price', 'execution_price': 'Price', 'Avg Price': 'Price',
            'side': 'Side', 'Side': 'Side', 'action': 'Side', 'Action': 'Side', 'type': 'Side',
            'fees': 'Fees', 'Fees': 'Fees', 'commission': 'Fees', 'Commission': 'Fees'
        }
        
        # Filter filled orders only (Webull specific)
        if 'Status' in df.columns:
            df = df[df['Status'].str.lower() == 'filled']
        
        # Handle duplicate columns (prefer specific ones)
        if 'Price' in df.columns and 'Avg Price' in df.columns:
            df = df.drop(columns=['Price'])
        if 'Filled' in df.columns and 'Total Qty' in df.columns:
            df = df.drop(columns=['Total Qty'])
        if 'Filled Time' in df.columns and 'Placed Time' in df.columns:
            df = df.drop(columns=['Placed Time'])
        
        # Clean price fields (remove @ symbol, $ etc)
        for price_col in ['Avg Price', 'price', 'Price']:
            if price_col in df.columns:
                df[price_col] = df[price_col].astype(str).str.replace('@', '').str.replace('$', '').str.strip()
        
        # Rename columns
        df.rename(columns=column_mapping, inplace=True)
        
        # Validate required columns
        required_columns = ['Date', 'Symbol', 'Quantity', 'Price', 'Side']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Add Fees if missing
        if 'Fees' not in df.columns:
            df['Fees'] = 0.0
        
        # Clean and convert data types
        df = df.replace('', np.nan)
        df = df.dropna(subset=['Date', 'Symbol'])
        df = df.drop_duplicates()
        
        # Parse dates
        df['Date'] = df['Date'].astype(str)
        df = df[~df['Date'].isin(['nan', 'None', 'NaT', ''])]
        df['Date'] = df['Date'].str.replace(r'\s+EDT$', '', regex=True).str.replace(r'\s+EST$', '', regex=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        # Convert numeric columns
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Fees'] = pd.to_numeric(df['Fees'], errors='coerce').fillna(0)
        
        # Remove invalid rows
        df = df.dropna(subset=['Quantity', 'Price'])
        
        logger.info(f"Parsed {len(df)} valid orders from CSV")
        
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV: {str(e)}")
        raise ValueError(f"Failed to parse CSV: {str(e)}")
