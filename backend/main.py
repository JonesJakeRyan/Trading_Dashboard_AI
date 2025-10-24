from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Performance Dashboard API", version="1.0.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine paths
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = BASE_DIR.parent / "frontend" / "dist"

# Mount static files if frontend build exists
if FRONTEND_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD_DIR / "assets"), name="assets")
    logger.info(f"Serving frontend from {FRONTEND_BUILD_DIR}")


class TradeAnalyzer:
    """Core analytics engine for trading performance metrics"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date')
        
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all trading metrics"""
        return {
            "performance": self.get_performance_metrics(),
            "win_loss": self.get_win_loss_metrics(),
            "risk": self.get_risk_metrics(),
            "per_symbol": self.get_per_symbol_breakdown(),
            "pnl_series": self.get_pnl_series(),
            "equity_curve": self.get_equity_curve()
        }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate overall performance metrics"""
        # Exclude open positions (trades with 0 P&L)
        closed_trades = self.df[self.df['Realized_PnL'] != 0].copy()
        
        total_pnl = closed_trades['Realized_PnL'].sum()
        
        # Calculate monthly returns
        closed_trades['YearMonth'] = closed_trades['Date'].dt.to_period('M')
        monthly_pnl = closed_trades.groupby('YearMonth')['Realized_PnL'].sum()
        avg_monthly_return = monthly_pnl.mean() if len(monthly_pnl) > 0 else 0
        
        # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
        daily_returns = closed_trades.groupby('Date')['Realized_PnL'].sum()
        sharpe_ratio = 0
        if len(daily_returns) > 1 and daily_returns.std() != 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        
        # Expectancy - FIXED: avg_loss should remain negative, then subtract it (which adds it)
        winning_trades = closed_trades[closed_trades['Realized_PnL'] > 0]
        losing_trades = closed_trades[closed_trades['Realized_PnL'] < 0]
        
        win_rate = len(winning_trades) / len(closed_trades) if len(closed_trades) > 0 else 0
        avg_win = winning_trades['Realized_PnL'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['Realized_PnL'].mean() if len(losing_trades) > 0 else 0  # Keep negative
        
        # Correct formula: (WinRate × AvgWin) + ((1 - WinRate) × AvgLoss)
        # Since avg_loss is negative, this correctly subtracts from expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            "total_pnl": round(total_pnl, 2),
            "avg_monthly_return": round(avg_monthly_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "expectancy": round(expectancy, 2)
        }
    
    def get_win_loss_metrics(self) -> Dict[str, float]:
        """Calculate win/loss statistics"""
        # Exclude open positions (trades with 0 P&L)
        closed_trades = self.df[self.df['Realized_PnL'] != 0].copy()
        
        winning_trades = closed_trades[closed_trades['Realized_PnL'] > 0]
        losing_trades = closed_trades[closed_trades['Realized_PnL'] < 0]
        
        total_trades = len(closed_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_win = winning_trades['Realized_PnL'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['Realized_PnL'].mean() if len(losing_trades) > 0 else 0
        
        total_profit = winning_trades['Realized_PnL'].sum()
        total_loss = abs(losing_trades['Realized_PnL'].sum())
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        return {
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2)
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Calculate risk-related metrics"""
        # Exclude open positions (trades with 0 P&L)
        closed_trades = self.df[self.df['Realized_PnL'] != 0].copy()
        
        # Max Drawdown
        cumulative_pnl = closed_trades.groupby('Date')['Realized_PnL'].sum().cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Average hold length (simplified - assumes each row is a closed position)
        total_trades = len(closed_trades)
        
        # Calculate date range
        if len(closed_trades) > 0:
            max_date = closed_trades['Date'].max()
            min_date = closed_trades['Date'].min()
            # Check if dates are valid (not NaT)
            if pd.notna(max_date) and pd.notna(min_date):
                date_range = (max_date - min_date).days
                avg_hold_length = date_range / total_trades if total_trades > 0 else 0
            else:
                avg_hold_length = 0
        else:
            avg_hold_length = 0
        
        return {
            "max_drawdown": round(max_drawdown, 2),
            "avg_hold_length": round(avg_hold_length, 1),
            "total_trades": total_trades
        }
    
    def get_per_symbol_breakdown(self) -> List[Dict[str, Any]]:
        """Calculate per-symbol performance"""
        symbol_stats = []
        
        for symbol in self.df['Symbol'].unique():
            symbol_df = self.df[self.df['Symbol'] == symbol]
            total_pnl = symbol_df['Realized_PnL'].sum()
            num_trades = len(symbol_df)
            
            # Calculate average return percentage (simplified)
            avg_return_pct = (total_pnl / num_trades / 100) if num_trades > 0 else 0
            
            symbol_stats.append({
                "symbol": symbol,
                "num_trades": num_trades,
                "total_pnl": round(total_pnl, 2),
                "avg_return_pct": round(avg_return_pct, 2)
            })
        
        # Sort by total P&L descending
        symbol_stats.sort(key=lambda x: x['total_pnl'], reverse=True)
        return symbol_stats
    
    def get_pnl_series(self) -> List[Dict[str, Any]]:
        """Get cumulative P&L time series"""
        daily_pnl = self.df.groupby('Date')['Realized_PnL'].sum().reset_index()
        daily_pnl['Cumulative_PnL'] = daily_pnl['Realized_PnL'].cumsum()
        
        return [
            {
                "date": row['Date'].strftime('%Y-%m-%d'),
                "daily_pnl": round(row['Realized_PnL'], 2),
                "cumulative_pnl": round(row['Cumulative_PnL'], 2)
            }
            for _, row in daily_pnl.iterrows()
        ]
    
    def get_equity_curve(self, starting_capital: float = 10000) -> List[Dict[str, Any]]:
        """Generate equity curve starting from initial capital"""
        daily_pnl = self.df.groupby('Date')['Realized_PnL'].sum().reset_index()
        daily_pnl['Equity'] = starting_capital + daily_pnl['Realized_PnL'].cumsum()
        
        return [
            {
                "date": row['Date'].strftime('%Y-%m-%d'),
                "equity": round(row['Equity'], 2)
            }
            for _, row in daily_pnl.iterrows()
        ]


def calculate_realized_pnl(df: pd.DataFrame) -> pd.Series:
    """
    Calculate realized P&L by tracking positions for each symbol.
    Uses FIFO (First In First Out) method for matching buys with sells.
    """
    # Store original index
    original_index = df.index
    
    # Sort by date to process trades chronologically, keeping track of original index
    df_sorted = df.sort_values('Date').copy()
    
    # Track positions for each symbol
    positions = {}  # {symbol: [(quantity, price, fees), ...]}
    pnl_dict = {}  # {original_index: pnl_value}
    
    for idx, row in df_sorted.iterrows():
        symbol = row['Symbol']
        quantity = row['Quantity']
        price = row['Price']
        fees = row['Fees']
        side = str(row['Side']).lower()
        
        if symbol not in positions:
            positions[symbol] = []
        
        realized_pnl = 0.0
        
        if side in ['buy']:
            # Opening a long position - store it
            positions[symbol].append({
                'quantity': quantity,
                'price': price,
                'fees': fees,
                'type': 'long'
            })
            # No realized P&L on opening
            realized_pnl = 0.0
            
        elif side in ['short']:
            # Opening a short position - store it
            positions[symbol].append({
                'quantity': quantity,
                'price': price,
                'fees': fees,
                'type': 'short'
            })
            # No realized P&L on opening
            realized_pnl = 0.0
            
        elif side in ['sell', 'sold']:
            # Closing positions - match with opens using FIFO
            remaining_qty = quantity
            sell_fees_per_share = fees / quantity if quantity > 0 else 0
            
            while remaining_qty > 0 and len(positions[symbol]) > 0:
                oldest_position = positions[symbol][0]
                
                if oldest_position['quantity'] <= remaining_qty:
                    # Close entire position
                    qty_to_close = oldest_position['quantity']
                    close_fees = sell_fees_per_share * qty_to_close
                    
                    if oldest_position['type'] == 'long':
                        # Long position: profit = (sell_price - buy_price) * qty - fees
                        realized_pnl += (price - oldest_position['price']) * qty_to_close - close_fees - oldest_position['fees']
                    else:
                        # Short position: profit = (short_price - cover_price) * qty - fees
                        realized_pnl += (oldest_position['price'] - price) * qty_to_close - close_fees - oldest_position['fees']
                    
                    remaining_qty -= qty_to_close
                    positions[symbol].pop(0)
                else:
                    # Partially close position
                    qty_to_close = remaining_qty
                    close_fees = sell_fees_per_share * qty_to_close
                    proportional_open_fees = oldest_position['fees'] * (qty_to_close / oldest_position['quantity'])
                    
                    if oldest_position['type'] == 'long':
                        realized_pnl += (price - oldest_position['price']) * qty_to_close - close_fees - proportional_open_fees
                    else:
                        realized_pnl += (oldest_position['price'] - price) * qty_to_close - close_fees - proportional_open_fees
                    
                    positions[symbol][0]['quantity'] -= qty_to_close
                    positions[symbol][0]['fees'] -= proportional_open_fees
                    remaining_qty = 0
            
            # If no matching position found, treat as opening a short
            if remaining_qty > 0:
                positions[symbol].append({
                    'quantity': remaining_qty,
                    'price': price,
                    'fees': fees,
                    'type': 'short'
                })
        
        pnl_dict[idx] = realized_pnl
    
    # Return series with original index order
    result = pd.Series([pnl_dict.get(idx, 0.0) for idx in original_index], index=original_index)
    
    # Replace inf and -inf with 0, and NaN with 0
    result = result.replace([np.inf, -np.inf], 0.0)
    result = result.fillna(0.0)
    
    return result


def sanitize_for_json(obj):
    """Recursively sanitize data structure for JSON serialization"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, (np.integer, np.floating)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return 0.0
        return val
    else:
        return obj


def parse_csv(content: str) -> pd.DataFrame:
    """Parse and standardize CSV data from various broker formats"""
    try:
        # Try to read CSV
        df = pd.read_csv(StringIO(content))
        
        # Standardize column names (handle different broker formats)
        column_mapping = {
            # Common variations
            'date': 'Date',
            'Date': 'Date',
            'datetime': 'Date',
            'time': 'Date',
            'Filled Time': 'Date',  # Webull
            'Placed Time': 'Date',  # Webull fallback
            'symbol': 'Symbol',
            'Symbol': 'Symbol',
            'ticker': 'Symbol',
            'Ticker': 'Symbol',
            'quantity': 'Quantity',
            'Quantity': 'Quantity',
            'qty': 'Quantity',
            'Qty': 'Quantity',
            'Filled': 'Quantity',  # Webull
            'Total Qty': 'Quantity',  # Webull fallback
            'price': 'Price',
            'Price': 'Price',
            'execution_price': 'Price',
            'Avg Price': 'Price',  # Webull
            'side': 'Side',
            'Side': 'Side',
            'action': 'Side',
            'Action': 'Side',
            'type': 'Side',
            'fees': 'Fees',
            'Fees': 'Fees',
            'commission': 'Fees',
            'Commission': 'Fees',
            'realized_pnl': 'Realized_PnL',
            'Realized_PnL': 'Realized_PnL',
            'pnl': 'Realized_PnL',
            'PnL': 'Realized_PnL',
            'profit_loss': 'Realized_PnL',
            'P&L': 'Realized_PnL',
            'Profit/Loss': 'Realized_PnL'
        }
        
        # Filter out cancelled/unfilled orders (Webull specific)
        if 'Status' in df.columns:
            df = df[df['Status'].str.lower() == 'filled']
        
        # For Webull: Drop duplicate columns that map to the same target
        # Use Avg Price instead of Price (which has @ symbol)
        if 'Price' in df.columns and 'Avg Price' in df.columns:
            df = df.drop(columns=['Price'])
        # Use Filled instead of Total Qty
        if 'Filled' in df.columns and 'Total Qty' in df.columns:
            df = df.drop(columns=['Total Qty'])
        # Use Filled Time instead of Placed Time
        if 'Filled Time' in df.columns and 'Placed Time' in df.columns:
            df = df.drop(columns=['Placed Time'])
        
        # Clean price fields BEFORE renaming - remove @ symbol and other non-numeric characters
        for price_col in ['Avg Price', 'price', 'Price']:
            if price_col in df.columns:
                df[price_col] = df[price_col].astype(str).str.replace('@', '').str.replace('$', '').str.strip()
        
        # Rename columns
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure required columns exist
        required_columns = ['Date', 'Symbol', 'Quantity', 'Price', 'Side']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}. Available columns: {list(df.columns)}")
        
        # Add optional columns if missing
        if 'Fees' not in df.columns:
            df['Fees'] = 0
        
        # Clean data - remove empty strings and None values
        df = df.replace('', np.nan)
        df = df.dropna(subset=['Date', 'Symbol'])
        df = df.drop_duplicates()
        
        # Convert types FIRST before calculating P&L
        # Convert Date to string first to handle mixed types, then parse
        df['Date'] = df['Date'].astype(str)
        # Remove rows with 'nan' or 'None' strings
        df = df[~df['Date'].isin(['nan', 'None', 'NaT', ''])]
        # Parse dates - strip timezone info from string before parsing
        df['Date'] = df['Date'].str.replace(r'\s+EDT$', '', regex=True).str.replace(r'\s+EST$', '', regex=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Remove any rows where date parsing failed
        df = df.dropna(subset=['Date'])
        
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Fees'] = pd.to_numeric(df['Fees'], errors='coerce').fillna(0)
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['Date'])
        
        # Calculate P&L if not provided (after type conversion)
        if 'Realized_PnL' not in df.columns:
            df['Realized_PnL'] = calculate_realized_pnl(df)
        else:
            df['Realized_PnL'] = pd.to_numeric(df['Realized_PnL'], errors='coerce')
        
        # Remove rows with invalid numeric data
        df = df.dropna(subset=['Quantity', 'Price', 'Realized_PnL'])
        
        return df
        
    except Exception as e:
        import traceback
        logger.error(f"Error parsing CSV: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Failed to parse CSV: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "trading-dashboard-api"}


@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {"status": "online", "service": "Trading Performance Dashboard API"}


@app.post("/api/upload")
async def upload_trades(file: UploadFile = File(...)):
    """
    Upload and analyze trading CSV file
    Returns comprehensive analytics and metrics
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse CSV
        df = parse_csv(content_str)
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="No valid trades found in CSV")
        
        # Analyze trades
        analyzer = TradeAnalyzer(df)
        metrics = analyzer.calculate_all_metrics()
        
        # Sanitize metrics to ensure JSON compliance
        metrics = sanitize_for_json(metrics)
        
        logger.info(f"Successfully analyzed {len(df)} trades from {file.filename}")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "total_rows": len(df),
            "metrics": metrics
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/filter")
async def filter_trades(
    file: UploadFile = File(...),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: Optional[str] = None
):
    """
    Filter trades by date range and/or symbol
    """
    try:
        # Read and parse file
        content = await file.read()
        content_str = content.decode('utf-8')
        df = parse_csv(content_str)
        
        # Apply filters
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        if symbol:
            df = df[df['Symbol'].str.upper() == symbol.upper()]
        
        if len(df) == 0:
            return JSONResponse(content={
                "success": True,
                "message": "No trades match the filter criteria",
                "metrics": None
            })
        
        # Analyze filtered data
        analyzer = TradeAnalyzer(df)
        metrics = analyzer.calculate_all_metrics()
        
        return JSONResponse(content={
            "success": True,
            "total_rows": len(df),
            "metrics": metrics
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo")
async def get_demo():
    """
    Get demo metrics from pre-loaded sample CSV.
    This endpoint serves as a demonstration of the dashboard.
    """
    try:
        import os
        logger.info("Demo endpoint called")
        
        # Try to find the demo CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'Webull_Orders_Records.csv')
        if not os.path.exists(csv_path):
            # Try parent directory
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'Webull_Orders_Records.csv')
        
        if not os.path.exists(csv_path):
            logger.error(f"Demo CSV not found at {csv_path}")
            raise HTTPException(status_code=404, detail="Demo data file not found")
        
        # Read and process the CSV
        with open(csv_path, 'r') as f:
            content_str = f.read()
        
        df = parse_csv(content_str)
        
        if len(df) == 0:
            raise HTTPException(status_code=500, detail="No valid trades found in demo data")
        
        # Analyze trades
        analyzer = TradeAnalyzer(df)
        metrics = analyzer.calculate_all_metrics()
        
        # Sanitize metrics to ensure JSON compliance
        metrics = sanitize_for_json(metrics)
        
        logger.info(f"Successfully analyzed {len(df)} demo trades")
        
        return JSONResponse(content={
            "success": True,
            "is_demo": True,
            "demo_account": "Sample Trading Account",
            "total_rows": len(df),
            "metrics": metrics
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in demo endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Catch-all route to serve React frontend for client-side routing.
    This should be the last route defined.
    """
    if FRONTEND_BUILD_DIR.exists():
        # Serve index.html for all non-API routes
        index_path = FRONTEND_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    # If no frontend build, return 404
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
