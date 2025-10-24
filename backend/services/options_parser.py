"""
Options Trading Parser
Parses Webull options CSV with multi-leg strategies (Iron Condors, Butterflies, Verticals, etc.)
Calculates net P&L per strategy and individual options positions.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class OptionsParser:
    """
    Parses options trading data from Webull CSV format.
    Handles multi-leg strategies and single options positions.
    """
    
    def __init__(self):
        self.strategies: List[Dict[str, Any]] = []
        self.single_options: List[Dict[str, Any]] = []
    
    def parse_csv(self, csv_content: str) -> pd.DataFrame:
        """
        Parse options CSV into standardized positions DataFrame.
        
        Args:
            csv_content: Raw CSV string
            
        Returns:
            DataFrame with columns [symbol, direction, entry_time, exit_time, 
                                   avg_entry_price, avg_exit_price, quantity, 
                                   realized_pnl, position_type]
        """
        # Read CSV
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        
        # Filter only filled orders
        df = df[df['Status'] == 'Filled'].copy()
        
        if len(df) == 0:
            logger.warning("No filled options orders found")
            return pd.DataFrame()
        
        # Parse strategies and single options
        positions = []
        i = 0
        
        while i < len(df):
            row = df.iloc[i]
            
            # Check if this is a strategy header (Name has value, Symbol is empty)
            if pd.notna(row['Name']) and (pd.isna(row['Symbol']) or row['Symbol'] == ''):
                # Multi-leg strategy
                strategy_pos = self._parse_strategy(df, i)
                if strategy_pos:
                    positions.append(strategy_pos)
                # Skip to next strategy (find next row with Name)
                i += 1
                while i < len(df) and (pd.isna(df.iloc[i]['Name']) or df.iloc[i]['Name'] == ''):
                    i += 1
            else:
                # Single option position
                option_pos = self._parse_single_option(row)
                if option_pos:
                    positions.append(option_pos)
                i += 1
        
        if not positions:
            return pd.DataFrame()
        
        positions_df = pd.DataFrame(positions)
        
        logger.info(f"Parsed {len(positions_df)} options positions from {len(df)} filled orders")
        
        return positions_df
    
    def _parse_strategy(self, df: pd.DataFrame, start_idx: int) -> Dict[str, Any]:
        """
        Parse a multi-leg options strategy.
        
        Args:
            df: Full DataFrame
            start_idx: Index of strategy header row
            
        Returns:
            Dict representing the strategy position
        """
        header = df.iloc[start_idx]
        strategy_name = header['Name']
        strategy_side = header['Side']  # Buy or Sell (opening direction)
        net_premium = float(header['Avg Price']) if pd.notna(header['Avg Price']) else 0.0
        quantity = int(header['Filled']) if pd.notna(header['Filled']) else 1
        
        # Parse timestamp
        filled_time = self._parse_timestamp(header['Filled Time'])
        
        # Extract underlying symbol from strategy name
        underlying = self._extract_underlying(strategy_name)
        
        # Get all legs (rows immediately following header with empty Name)
        legs = []
        i = start_idx + 1
        while i < len(df) and (pd.isna(df.iloc[i]['Name']) or df.iloc[i]['Name'] == ''):
            leg = df.iloc[i]
            if pd.notna(leg['Symbol']):
                legs.append({
                    'symbol': leg['Symbol'],
                    'side': leg['Side'],
                    'price': float(leg['Avg Price']) if pd.notna(leg['Avg Price']) else 0.0,
                    'quantity': int(leg['Filled']) if pd.notna(leg['Filled']) else 0
                })
            i += 1
        
        # Calculate P&L based on strategy direction
        # If we SOLD to open, we collect premium (positive)
        # If we BOUGHT to open, we pay premium (negative)
        if strategy_side.lower() == 'sell':
            # Sold to open - we collected premium
            entry_cost = -net_premium * 100 * quantity  # Negative = credit received
            direction = 'short'
        else:
            # Bought to open - we paid premium
            entry_cost = net_premium * 100 * quantity  # Positive = debit paid
            direction = 'long'
        
        # For now, assume strategies are closed (expired or closed)
        # In real implementation, you'd track open vs closed
        # Assuming max profit/loss based on strategy type
        
        # Simplified: Use net premium as realized P&L
        # Positive premium = profit, negative = loss
        realized_pnl = -entry_cost  # Flip sign for P&L
        
        return {
            'symbol': underlying,
            'direction': direction,
            'entry_time': filled_time,
            'exit_time': filled_time,  # Simplified - would need close time
            'avg_entry_price': net_premium,
            'avg_exit_price': 0.0,  # Expired worthless or closed
            'quantity': quantity,
            'total_entry_fees': 0.0,
            'total_exit_fees': 0.0,
            'realized_pnl': realized_pnl,
            'position_type': 'options',
            'strategy_name': strategy_name,
            'num_legs': len(legs)
        }
    
    def _parse_single_option(self, row: pd.Series) -> Dict[str, Any]:
        """
        Parse a single option position (not part of a strategy).
        
        Args:
            row: DataFrame row
            
        Returns:
            Dict representing the option position
        """
        symbol = row['Symbol']
        side = row['Side']
        price = float(row['Avg Price']) if pd.notna(row['Avg Price']) else 0.0
        quantity = int(row['Filled']) if pd.notna(row['Filled']) else 0
        filled_time = self._parse_timestamp(row['Filled Time'])
        
        # Extract underlying from option symbol
        underlying = self._extract_underlying_from_option(symbol)
        
        # Calculate cost (options are priced per share, contracts are 100 shares)
        cost = price * 100 * quantity
        
        # Determine direction
        if side.lower() in ['buy', 'bought']:
            direction = 'long'
            entry_cost = cost
        else:
            direction = 'short'
            entry_cost = -cost  # Credit received
        
        # Simplified: Assume closed at $0 (expired worthless)
        realized_pnl = -entry_cost
        
        return {
            'symbol': underlying,
            'direction': direction,
            'entry_time': filled_time,
            'exit_time': filled_time,
            'avg_entry_price': price,
            'avg_exit_price': 0.0,
            'quantity': quantity,
            'total_entry_fees': 0.0,
            'total_exit_fees': 0.0,
            'realized_pnl': realized_pnl,
            'position_type': 'options',
            'strategy_name': 'Single Option',
            'num_legs': 1
        }
    
    def _extract_underlying(self, strategy_name: str) -> str:
        """Extract underlying symbol from strategy name (e.g., 'ASPI IronCondor' -> 'ASPI')"""
        if not strategy_name:
            return 'UNKNOWN'
        parts = strategy_name.split()
        return parts[0] if parts else 'UNKNOWN'
    
    def _extract_underlying_from_option(self, option_symbol: str) -> str:
        """
        Extract underlying symbol from option symbol.
        Format: SYMBOL251017C00009000 -> SYMBOL
        """
        if not option_symbol:
            return 'UNKNOWN'
        
        # Remove date and option details (C/P and strike)
        # Pattern: SYMBOL + YYMMDD + C/P + Strike
        match = re.match(r'^([A-Z]+)', option_symbol)
        if match:
            return match.group(1)
        
        return option_symbol
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Webull timestamp format"""
        if pd.isna(timestamp_str) or timestamp_str == '':
            return datetime.now()
        
        try:
            # Format: "10/10/2025 10:30:00 EDT"
            dt_str = timestamp_str.rsplit(' ', 1)[0]  # Remove timezone
            return pd.to_datetime(dt_str, format='%m/%d/%Y %H:%M:%S')
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return datetime.now()


def parse_options_csv(csv_content: str) -> pd.DataFrame:
    """
    Convenience function to parse options CSV.
    
    Args:
        csv_content: Raw CSV string
        
    Returns:
        DataFrame of options positions
    """
    parser = OptionsParser()
    return parser.parse_csv(csv_content)
