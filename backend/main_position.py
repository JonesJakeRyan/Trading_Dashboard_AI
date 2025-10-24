"""
Trading Performance Dashboard API - Position-Based Accounting
Uses average-cost position tracking for accurate P&L calculation.
Implements proper Sharpe ratio and drawdown metrics.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import pandas as pd
import re

from services.trade_parser import parse_csv
from services.position_tracker import PositionTracker
from services.position_metrics import PositionMetrics, sanitize_for_json
from services.options_parser import parse_options_csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Performance Dashboard API",
    version="3.0.0",
    description="Position-based accounting with average cost tracking"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Trading Performance Dashboard API",
        "version": "3.0.0",
        "features": [
            "Position-based accounting",
            "Average cost tracking",
            "Proper Sharpe ratio calculation",
            "Accurate drawdown metrics",
            "Dead zone for small P&L",
            "Win rate by position or day"
        ]
    }


@app.post("/api/upload")
async def upload_trades(
    file: UploadFile = File(...),
    file_type: str = Query('auto', regex='^(auto|stocks|options)$'),
    win_rate_mode: str = Query('position', regex='^(position|day)$'),
    dead_zone: float = Query(0.50, ge=0, le=10),
    starting_equity: float = Query(10000, gt=0)
):
    """
    Upload and analyze trading CSV file using position accounting.
    
    Args:
        file: CSV file with order data
        file_type: 'auto', 'stocks', or 'options' (auto-detects by default)
        win_rate_mode: 'position' or 'day' for win rate calculation
        dead_zone: Minimum P&L to count as win (default $0.50)
        starting_equity: Starting capital for Sharpe/drawdown (default $10,000)
    
    Process:
    1. Parse CSV and standardize columns
    2. Track positions with average cost basis
    3. Calculate realized P&L on position closes
    4. Compute performance metrics with proper risk calculations
    
    Returns:
        JSON with summary, win_loss, risk, per_symbol, and timeseries data
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Auto-detect file type if needed
        detected_type = file_type
        if file_type == 'auto':
            detected_type = _detect_file_type(content_str)
            logger.info(f"Auto-detected file type: {detected_type}")
        
        # Parse based on file type
        if detected_type == 'options':
            logger.info(f"Parsing options CSV file: {file.filename}")
            positions_df = parse_options_csv(content_str)
            total_orders = len(positions_df)
        else:
            # Stock orders
            logger.info(f"Parsing stock CSV file: {file.filename}")
            orders_df = parse_csv(content_str)
            
            if len(orders_df) == 0:
                raise HTTPException(status_code=400, detail="No valid orders found in CSV")
            
            # Track positions with average cost
            logger.info(f"Tracking positions from {len(orders_df)} orders (dead zone: ${dead_zone})...")
            tracker = PositionTracker(dead_zone=dead_zone)
            positions_df = tracker.process_orders(orders_df)
            total_orders = len(orders_df)
        
        if len(positions_df) == 0:
            logger.warning("No closed positions found")
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "file_type": detected_type,
                "total_orders": total_orders,
                "closed_positions": 0,
                "message": "No closed positions found.",
                "metrics": PositionMetrics(positions_df, starting_equity).calculate_all_metrics(win_rate_mode)
            })
        
        # Calculate performance metrics
        logger.info(f"Calculating metrics for {len(positions_df)} closed positions...")
        metrics_calculator = PositionMetrics(positions_df, starting_equity)
        metrics = metrics_calculator.calculate_all_metrics(win_rate_mode=win_rate_mode)
        
        # Sanitize for JSON
        metrics = sanitize_for_json(metrics)
        
        logger.info(f"Successfully analyzed {file.filename}")
        logger.info(f"  - File type: {detected_type}")
        logger.info(f"  - Total orders: {total_orders}")
        logger.info(f"  - Closed positions: {len(positions_df)}")
        logger.info(f"  - Total P&L: ${metrics['summary']['total_pnl']:.2f}")
        logger.info(f"  - Win Rate ({win_rate_mode}): {metrics['win_loss']['win_rate']:.1f}%")
        logger.info(f"  - Expectancy: ${metrics['summary']['expectancy']:.2f}")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "file_type": detected_type,
            "total_orders": total_orders,
            "closed_positions": len(positions_df),
            "settings": {
                "win_rate_mode": win_rate_mode,
                "dead_zone": dead_zone,
                "starting_equity": starting_equity
            },
            "metrics": metrics
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _detect_file_type(csv_content: str) -> str:
    """
    Auto-detect if CSV is stocks or options based on content.
    
    Args:
        csv_content: Raw CSV string
        
    Returns:
        'stocks' or 'options'
    """
    # Check for options-specific patterns
    lines = csv_content.split('\n')
    
    # Look for strategy names in first column (IronCondor, Butterfly, etc.)
    for line in lines[1:10]:  # Check first few data rows
        if any(keyword in line for keyword in ['IronCondor', 'IronButterfly', 'Vertical', 'Straddle', 'Strangle']):
            return 'options'
        # Check for option symbols (contain expiration dates)
        if re.search(r'[A-Z]+\d{6}[CP]\d{8}', line):
            return 'options'
    
    return 'stocks'


@app.post("/api/upload/combined")
async def upload_combined(
    stocks_file: UploadFile = File(None),
    options_file: UploadFile = File(None),
    win_rate_mode: str = Query('position', regex='^(position|day)$'),
    dead_zone: float = Query(0.50, ge=0, le=10),
    starting_equity: float = Query(10000, gt=0)
):
    """
    Upload both stocks and options CSVs and combine their P&L.
    
    Args:
        stocks_file: CSV file with stock orders
        options_file: CSV file with options orders
        win_rate_mode: 'position' or 'day' for win rate calculation
        dead_zone: Minimum P&L to count as win (default $0.50)
        starting_equity: Starting capital for Sharpe/drawdown (default $10,000)
    
    Returns:
        Combined metrics from both stocks and options
    """
    try:
        all_positions = []
        total_stock_orders = 0
        total_options_orders = 0
        
        # Process stocks file
        if stocks_file:
            logger.info(f"Processing stocks file: {stocks_file.filename}")
            stocks_content = await stocks_file.read()
            stocks_str = stocks_content.decode('utf-8')
            
            orders_df = parse_csv(stocks_str)
            total_stock_orders = len(orders_df)
            
            if len(orders_df) > 0:
                tracker = PositionTracker(dead_zone=dead_zone)
                stock_positions = tracker.process_orders(orders_df)
                if len(stock_positions) > 0:
                    stock_positions['source'] = 'stocks'
                    all_positions.append(stock_positions)
                    logger.info(f"  - Stock positions: {len(stock_positions)}")
        
        # Process options file
        if options_file:
            logger.info(f"Processing options file: {options_file.filename}")
            options_content = await options_file.read()
            options_str = options_content.decode('utf-8')
            
            options_positions = parse_options_csv(options_str)
            total_options_orders = len(options_positions)
            
            if len(options_positions) > 0:
                options_positions['source'] = 'options'
                all_positions.append(options_positions)
                logger.info(f"  - Options positions: {len(options_positions)}")
        
        if not all_positions:
            raise HTTPException(status_code=400, detail="No valid positions found in uploaded files")
        
        # Combine all positions
        combined_df = pd.concat(all_positions, ignore_index=True)
        
        # Calculate combined metrics
        logger.info(f"Calculating combined metrics for {len(combined_df)} total positions...")
        metrics_calculator = PositionMetrics(combined_df, starting_equity)
        metrics = metrics_calculator.calculate_all_metrics(win_rate_mode=win_rate_mode)
        
        # Sanitize for JSON
        metrics = sanitize_for_json(metrics)
        
        # Calculate breakdown by source
        stock_pnl = combined_df[combined_df['source'] == 'stocks']['realized_pnl'].sum() if 'stocks' in combined_df['source'].values else 0.0
        options_pnl = combined_df[combined_df['source'] == 'options']['realized_pnl'].sum() if 'options' in combined_df['source'].values else 0.0
        
        logger.info(f"Successfully analyzed combined files")
        logger.info(f"  - Stock orders: {total_stock_orders}, P&L: ${stock_pnl:.2f}")
        logger.info(f"  - Options orders: {total_options_orders}, P&L: ${options_pnl:.2f}")
        logger.info(f"  - Combined P&L: ${metrics['summary']['total_pnl']:.2f}")
        
        return JSONResponse(content={
            "success": True,
            "stocks_file": stocks_file.filename if stocks_file else None,
            "options_file": options_file.filename if options_file else None,
            "total_stock_orders": total_stock_orders,
            "total_options_orders": total_options_orders,
            "total_positions": len(combined_df),
            "breakdown": {
                "stocks_pnl": round(stock_pnl, 2),
                "options_pnl": round(options_pnl, 2),
                "combined_pnl": round(metrics['summary']['total_pnl'], 2)
            },
            "settings": {
                "win_rate_mode": win_rate_mode,
                "dead_zone": dead_zone,
                "starting_equity": starting_equity
            },
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error processing combined upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "services": {
            "position_tracker": "operational",
            "position_metrics": "operational",
            "options_parser": "operational"
        }
    }


@app.get("/api/docs/metrics")
async def metrics_documentation():
    """
    Documentation for all calculated metrics.
    """
    return {
        "position_accounting": {
            "method": "Average cost basis",
            "description": "Tracks running position per symbol with average entry price",
            "trade_definition": "Complete round-trip (position returns to 0)",
            "dead_zone": "P&L below threshold treated as loss (default $0.50)"
        },
        "summary_metrics": {
            "total_pnl": "Sum of all realized P&L from closed positions",
            "avg_monthly_return": "Average P&L per month",
            "sharpe_ratio": "Risk-adjusted return: (mean(daily_return) / std(daily_return)) × √252",
            "expectancy": "Expected value per position: (WinRate × AvgWin) + ((1-WinRate) × AvgLoss)"
        },
        "win_loss_metrics": {
            "win_rate": "Percentage of profitable positions (or days if mode='day')",
            "avg_win": "Average profit from winning positions",
            "avg_loss": "Average loss from losing positions (negative)",
            "profit_factor": "Gross profit ÷ Gross loss",
            "win_rate_mode": "'position' counts winning positions, 'day' counts winning days"
        },
        "risk_metrics": {
            "max_drawdown": "Maximum peak-to-trough decline: abs(min((equity / cummax(equity) - 1) × 100))",
            "avg_hold_length": "Average number of days per position",
            "total_trades": "Number of closed positions"
        },
        "formulas": {
            "long_pnl": "(exit_price - avg_entry_price) × quantity - fees",
            "short_pnl": "(avg_entry_price - exit_price) × quantity - fees",
            "avg_cost_update": "(old_cost × old_qty + new_price × new_qty) / (old_qty + new_qty)",
            "sharpe_ratio": "(mean(daily_pnl / equity) / std(daily_pnl / equity)) × √252",
            "drawdown": "(equity / cummax(equity) - 1) × 100"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
