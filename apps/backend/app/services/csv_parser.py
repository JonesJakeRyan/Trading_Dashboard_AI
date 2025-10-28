"""
CSV parsing service for broker templates
Handles Webull, Robinhood, and Unified CSV formats
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from io import StringIO
import pytz

logger = logging.getLogger(__name__)

# Timezone for EST
EST = pytz.timezone("America/New_York")


class CSVParserError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class CSVParser:
    """Parser for different broker CSV formats"""
    
    # Header mappings for each template
    WEBULL_HEADERS = {
        "symbol": ["Symbol", "Ticker", "Stock Symbol"],
        "side": ["Action", "Side", "Type"],
        "quantity": ["Filled", "Quantity", "Qty", "Shares"],
        "price": ["Avg Price", "Price", "Fill Price", "Execution Price"],
        "executed_at": ["Filled Time", "Time", "Date", "Execution Time"],
        "account_id": ["Account"],
    }
    
    ROBINHOOD_HEADERS = {
        "symbol": ["Symbol", "Instrument", "Ticker"],
        "side": ["Side", "Action", "Type"],
        "quantity": ["Shares", "Quantity", "Qty"],
        "price": ["Price", "Average Price", "Fill Price"],
        "executed_at": ["Date", "Time", "Executed At", "Timestamp"],
        "account_id": ["Account"],
    }
    
    UNIFIED_HEADERS = {
        "symbol": ["symbol"],
        "side": ["side"],
        "quantity": ["quantity"],
        "price": ["price"],
        "executed_at": ["executed_at"],
        "account_id": ["account_id"],
        "notes": ["notes"],
    }
    
    # Side mappings
    SIDE_MAPPINGS = {
        "buy": "BUY",
        "BUY": "BUY",
        "Buy": "BUY",
        "B": "BUY",
        "b": "BUY",
        "sell": "SELL",
        "SELL": "SELL",
        "Sell": "SELL",
        "S": "SELL",
        "s": "SELL",
        "Short": "SELL",
        "short": "SELL",
        "Short Sell": "SELL",
        "short sell": "SELL",
        "SELL_SHORT": "SELL",
        "sell short": "SELL",
        "Sell Short": "SELL",
    }
    
    def __init__(self, template: str):
        """
        Initialize parser with template type
        
        Args:
            template: One of 'webull_v1', 'robinhood_v1', 'unified_v1'
        """
        self.template = template
        self.header_map = self._get_header_map()
        logger.info(f"Initialized CSV parser for template: {template}")
    
    def _get_header_map(self) -> Dict[str, List[str]]:
        """Get header mapping for current template"""
        if self.template == "webull_v1":
            return self.WEBULL_HEADERS
        elif self.template == "robinhood_v1":
            return self.ROBINHOOD_HEADERS
        elif self.template == "unified_v1":
            return self.UNIFIED_HEADERS
        else:
            raise CSVParserError(f"Unknown template: {self.template}")
    
    def parse(self, csv_content: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse CSV content and return normalized trades
        
        Args:
            csv_content: CSV file content as string
            
        Returns:
            Tuple of (successful_trades, errors)
        """
        logger.info(f"Starting CSV parse with template: {self.template}")
        
        try:
            # Read CSV
            df = pd.read_csv(StringIO(csv_content))
            logger.info(f"Read CSV with {len(df)} rows and columns: {list(df.columns)}")
            
            # Validate headers
            validation_result = self._validate_headers(df.columns.tolist())
            if not validation_result["valid"]:
                raise CSVParserError(validation_result["message"])
            
            # Normalize column names
            df = self._normalize_columns(df)
            
            # Parse each row
            trades = []
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    trade = self._parse_row(row, idx + 2)  # +2 for header and 0-index
                    trades.append(trade)
                except Exception as e:
                    logger.warning(f"Error parsing row {idx + 2}: {str(e)}")
                    errors.append({
                        "row": idx + 2,
                        "error": str(e),
                        "data": row.to_dict()
                    })
            
            logger.info(f"Parsed {len(trades)} trades successfully, {len(errors)} errors")
            return trades, errors
            
        except pd.errors.EmptyDataError:
            raise CSVParserError("CSV file is empty")
        except pd.errors.ParserError as e:
            raise CSVParserError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during CSV parse: {str(e)}", exc_info=True)
            raise CSVParserError(f"Failed to parse CSV: {str(e)}")
    
    def _validate_headers(self, columns: List[str]) -> Dict:
        """Validate that required headers are present"""
        required_fields = ["symbol", "side", "quantity", "price", "executed_at"]
        checklist = []
        missing = []
        
        for field in required_fields:
            possible_headers = self.header_map.get(field, [])
            found = any(col in columns for col in possible_headers)
            
            if found:
                checklist.append(f"✓ {field} column found")
            else:
                checklist.append(f"✗ {field} column not found")
                missing.append(field)
        
        if missing:
            return {
                "valid": False,
                "message": f"Missing required columns: {', '.join(missing)}",
                "checklist": checklist
            }
        
        return {"valid": True, "checklist": checklist}
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to unified format"""
        rename_map = {}
        
        for unified_name, possible_names in self.header_map.items():
            for col in df.columns:
                if col in possible_names:
                    rename_map[col] = unified_name
                    break
        
        df = df.rename(columns=rename_map)
        logger.debug(f"Normalized columns: {rename_map}")
        return df
    
    def _parse_row(self, row: pd.Series, row_num: int) -> Dict:
        """Parse a single row into normalized trade format"""
        try:
            # Extract and validate symbol
            symbol = str(row["symbol"]).strip().upper()
            if not symbol or symbol == "NAN":
                raise ValueError(f"Symbol is required in row {row_num}")
            
            # Extract and normalize side
            side_raw = str(row["side"]).strip()
            side = self.SIDE_MAPPINGS.get(side_raw)
            if not side:
                raise ValueError(
                    f"Invalid side value '{side_raw}' in row {row_num}. "
                    f"Must be one of: {', '.join(set(self.SIDE_MAPPINGS.keys()))}"
                )
            
            # Extract and validate quantity
            quantity = float(row["quantity"])
            if quantity <= 0:
                raise ValueError(f"Quantity must be positive in row {row_num}, got {quantity}")
            if quantity > 1000000:
                raise ValueError(f"Quantity exceeds maximum (1,000,000) in row {row_num}")
            
            # Extract and validate price (strip @ symbol if present)
            price_str = str(row["price"]).strip().replace("@", "").replace("$", "")
            price = float(price_str)
            if price <= 0:
                raise ValueError(f"Price must be positive in row {row_num}, got {price}")
            if price > 100000:
                raise ValueError(f"Price exceeds maximum ($100,000) in row {row_num}")
            
            # Parse timestamp
            executed_at = self._parse_timestamp(row["executed_at"], row_num)
            
            # Optional fields
            account_id = None
            if "account_id" in row and pd.notna(row["account_id"]):
                account_id = str(row["account_id"]).strip()
            
            notes = None
            if "notes" in row and pd.notna(row["notes"]):
                notes = str(row["notes"]).strip()
            
            return {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "executed_at": executed_at.isoformat(),
                "account_id": account_id,
                "notes": notes,
            }
            
        except KeyError as e:
            raise ValueError(f"Missing required field {e} in row {row_num}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data in row {row_num}: {str(e)}")
    
    def _parse_timestamp(self, timestamp_str: str, row_num: int) -> datetime:
        """Parse timestamp string to datetime with timezone"""
        if pd.isna(timestamp_str):
            raise ValueError(f"Timestamp is required in row {row_num}")
        
        timestamp_str = str(timestamp_str).strip()
        
        # Strip timezone suffixes (EST, EDT, PST, etc.) - we'll add EST back later
        for tz_suffix in [' EST', ' EDT', ' PST', ' PDT', ' CST', ' CDT', ' MST', ' MDT']:
            if timestamp_str.endswith(tz_suffix):
                timestamp_str = timestamp_str[:-len(tz_suffix)].strip()
                break
        
        # Try different formats
        formats = [
            "%m/%d/%Y %H:%M:%S",  # Webull format: 10/24/2025 12:17:43
            "%Y-%m-%d %H:%M:%S",  # Standard format
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 with timezone
            "%Y-%m-%dT%H:%M:%S",  # ISO 8601 without timezone
        ]
        
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            # Try pandas parser as fallback
            try:
                dt = pd.to_datetime(timestamp_str)
                dt = dt.to_pydatetime()
            except Exception:
                raise ValueError(
                    f"Could not parse timestamp '{timestamp_str}' in row {row_num}. "
                    "Expected format: YYYY-MM-DD HH:MM:SS or ISO 8601"
                )
        
        # Add timezone if not present (assume EST)
        if dt.tzinfo is None:
            dt = EST.localize(dt)
        
        return dt
