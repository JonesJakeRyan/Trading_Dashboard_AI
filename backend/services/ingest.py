"""
CSV Ingestion Module
Normalizes Webull equity and options CSVs into a unified fills DataFrame.
Uses US/Eastern timezone for all date operations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple
import logging
import re
from io import StringIO

logger = logging.getLogger(__name__)

# US/Eastern timezone
EASTERN_TZ = 'America/New_York'


def parse_webull_equities_csv(csv_content: str) -> pd.DataFrame:
    """
    Parse Webull equities CSV into normalized fills.
    
    Returns DataFrame with columns:
        asset_type, symbol, underlying, side, qty, price, filled_time, multiplier
    """
    df = pd.read_csv(StringIO(csv_content))
    
    # Filter only filled orders
    df = df[df['Status'] == 'Filled'].copy()
    
    if len(df) == 0:
        return pd.DataFrame(columns=['asset_type', 'symbol', 'underlying', 'side', 
                                     'qty', 'price', 'filled_time', 'multiplier'])
    
    # Parse filled time - handle both "Filled Time" and variations
    time_col = 'Filled Time' if 'Filled Time' in df.columns else None
    if time_col is None:
        # Try to find the time column
        for col in df.columns:
            if 'filled' in col.lower() and 'time' in col.lower():
                time_col = col
                break
    
    if time_col is None:
        logger.error(f"Could not find filled time column. Available columns: {df.columns.tolist()}")
        return pd.DataFrame(columns=['asset_type', 'symbol', 'underlying', 'side', 
                                     'qty', 'price', 'filled_time', 'multiplier'])
    
    # Parse timestamp - remove timezone suffix first
    df['filled_time'] = df[time_col].astype(str).str.replace(r'\s+[A-Z]{3,4}$', '', regex=True)
    df['filled_time'] = pd.to_datetime(df['filled_time'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
    
    # Make timezone aware (Eastern)
    df['filled_time'] = df['filled_time'].dt.tz_localize(EASTERN_TZ, ambiguous='NaT', nonexistent='NaT')
    
    # Drop rows with invalid timestamps
    df = df.dropna(subset=['filled_time'])
    
    # Normalize side
    df['side'] = df['Side'].str.lower().map({
        'buy': 'buy',
        'bought': 'buy',
        'sell': 'sell',
        'sold': 'sell',
        'sell to close': 'sell',
        'short': 'short',
        'sell short': 'short',
        'buy to cover': 'cover',
        'cover': 'cover'
    })
    
    # Extract data
    fills = pd.DataFrame({
        'asset_type': 'equity',
        'symbol': df['Symbol'],
        'underlying': df['Symbol'],  # For equities, underlying = symbol
        'side': df['side'],
        'qty': df['Filled'].astype(float),
        'price': df['Avg Price'].astype(float),
        'filled_time': df['filled_time'],
        'multiplier': 1.0
    })
    
    # Drop any remaining NaN rows
    fills = fills.dropna(subset=['side', 'qty', 'price'])
    
    logger.info(f"Parsed {len(fills)} equity fills from {len(df)} orders")
    
    return fills


def parse_webull_options_csv(csv_content: str) -> pd.DataFrame:
    """
    Parse Webull options CSV into normalized fills.
    Handles multi-leg strategies by processing individual legs.
    
    Returns DataFrame with columns:
        asset_type, symbol, underlying, side, qty, price, filled_time, multiplier
    """
    df = pd.read_csv(StringIO(csv_content))
    
    # Filter only filled orders
    df = df[df['Status'] == 'Filled'].copy()
    
    if len(df) == 0:
        return pd.DataFrame(columns=['asset_type', 'symbol', 'underlying', 'side', 
                                     'qty', 'price', 'filled_time', 'multiplier'])
    
    fills_list = []
    
    for idx, row in df.iterrows():
        # Skip strategy headers (Name has value, Symbol is empty)
        if pd.notna(row['Name']) and (pd.isna(row['Symbol']) or row['Symbol'] == ''):
            continue
        
        # Process individual option contracts
        if pd.notna(row['Symbol']) and row['Symbol'] != '':
            # Parse filled time - handle column name variations
            time_col = 'Filled Time' if 'Filled Time' in df.columns else None
            if time_col is None:
                for col in df.columns:
                    if 'filled' in col.lower() and 'time' in col.lower():
                        time_col = col
                        break
            
            if time_col is None or pd.isna(row[time_col]):
                continue
            
            # Parse timestamp - remove timezone suffix
            time_str = str(row[time_col]).strip()
            time_str = time_str.split(' EDT')[0].split(' EST')[0].split(' PDT')[0].split(' PST')[0]
            filled_time = pd.to_datetime(time_str, format='%m/%d/%Y %H:%M:%S', errors='coerce')
            
            if pd.isna(filled_time):
                continue
            
            # Make timezone aware
            filled_time = filled_time.tz_localize(EASTERN_TZ, ambiguous='NaT', nonexistent='NaT')
            
            if pd.isna(filled_time):
                continue
            
            # Extract underlying from option symbol
            underlying = extract_underlying_from_option_symbol(row['Symbol'])
            
            # Normalize side
            side_map = {
                'buy': 'buy',
                'bought': 'buy',
                'sell': 'sell',
                'sold': 'sell',
                'sell to close': 'sell',
                'short': 'short',
                'sell short': 'short',
                'buy to cover': 'cover',
                'cover': 'cover'
            }
            side = side_map.get(str(row['Side']).lower(), None)
            
            if side is None:
                continue
            
            # Get quantity and price
            qty = float(row['Filled']) if pd.notna(row['Filled']) else 0
            price = float(row['Avg Price']) if pd.notna(row['Avg Price']) else 0
            
            if qty <= 0 or price < 0:
                continue
            
            fills_list.append({
                'asset_type': 'option',
                'symbol': row['Symbol'],
                'underlying': underlying,
                'side': side,
                'qty': qty,
                'price': price,
                'filled_time': filled_time,
                'multiplier': 100.0  # Standard options multiplier
            })
    
    if not fills_list:
        return pd.DataFrame(columns=['asset_type', 'symbol', 'underlying', 'side', 
                                     'qty', 'price', 'filled_time', 'multiplier'])
    
    fills = pd.DataFrame(fills_list)
    
    logger.info(f"Parsed {len(fills)} option fills")
    
    return fills


def extract_underlying_from_option_symbol(option_symbol: str) -> str:
    """
    Extract underlying ticker from option symbol.
    Format: SYMBOL + YYMMDD + C/P + Strike
    Example: AAPL251017C00180000 -> AAPL
    """
    if not option_symbol:
        return 'UNKNOWN'
    
    # Match letters at the start
    match = re.match(r'^([A-Z]+)', option_symbol)
    if match:
        return match.group(1)
    
    return option_symbol


def filter_ytd(fills: pd.DataFrame) -> pd.DataFrame:
    """
    Filter fills to YTD (Year-To-Date) in Eastern timezone.
    YTD = from Jan 1 00:00:00 America/New_York to now.
    """
    if len(fills) == 0:
        return fills
    
    # Get current time in Eastern
    now_eastern = pd.Timestamp.now(tz=EASTERN_TZ)
    
    # Start of year in Eastern
    ytd_start = pd.Timestamp(year=now_eastern.year, month=1, day=1, 
                             hour=0, minute=0, second=0, tz=EASTERN_TZ)
    
    # Filter
    ytd_fills = fills[
        (fills['filled_time'] >= ytd_start) & 
        (fills['filled_time'] <= now_eastern)
    ].copy()
    
    logger.info(f"Filtered to YTD: {len(ytd_fills)} fills from {len(fills)} total")
    
    return ytd_fills


def ingest_csvs(
    equities_csv: Optional[str] = None,
    options_csv: Optional[str] = None,
    ytd_only: bool = False
) -> pd.DataFrame:
    """
    Ingest and normalize both equity and options CSVs.
    
    Args:
        equities_csv: Raw CSV string for equities
        options_csv: Raw CSV string for options
        ytd_only: DEPRECATED - Do not use. Filtering should happen after accounting.
        
    Returns:
        Normalized fills DataFrame sorted by filled_time
        
    Note:
        YTD filtering is intentionally NOT applied here. The accounting engine
        needs full history to correctly compute P&L for positions opened before
        YTD but closed during YTD. Filter completed trades by close_time after
        accounting instead.
    """
    fills_list = []
    
    # Parse equities
    if equities_csv:
        try:
            equity_fills = parse_webull_equities_csv(equities_csv)
            if len(equity_fills) > 0:
                fills_list.append(equity_fills)
                logger.info(f"Added {len(equity_fills)} equity fills")
        except Exception as e:
            logger.error(f"Failed to parse equities CSV: {e}")
    
    # Parse options
    if options_csv:
        try:
            option_fills = parse_webull_options_csv(options_csv)
            if len(option_fills) > 0:
                fills_list.append(option_fills)
                logger.info(f"Added {len(option_fills)} option fills")
        except Exception as e:
            logger.error(f"Failed to parse options CSV: {e}")
    
    # Combine
    if not fills_list:
        logger.warning("No fills found in any CSV")
        return pd.DataFrame(columns=['asset_type', 'symbol', 'underlying', 'side', 
                                     'qty', 'price', 'filled_time', 'multiplier'])
    
    all_fills = pd.concat(fills_list, ignore_index=True)
    
    # DO NOT filter YTD here - accounting needs full history!
    # Positions opened last year but closed this year need their entry legs.
    # Filter trades by close_time after accounting instead.
    
    # Sort chronologically
    all_fills = all_fills.sort_values('filled_time').reset_index(drop=True)
    
    logger.info(f"Total normalized fills: {len(all_fills)}")
    
    return all_fills
