"""
Trading Performance Dashboard API - Refactored
Uses modular services for trade parsing and performance metrics calculation.
All metrics are based on completed trade pairs (FIFO matched).
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from services.trade_parser import TradeParser, parse_csv
from services.performance_metrics import PerformanceMetrics, sanitize_for_json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Performance Dashboard API",
    version="2.0.0",
    description="Trade-level performance analytics with FIFO matching"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
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
        "version": "2.0.0",
        "features": [
            "FIFO trade matching",
            "Trade-level performance metrics",
            "Realized P&L only",
            "Multi-broker CSV support"
        ]
    }


@app.post("/api/upload")
async def upload_trades(file: UploadFile = File(...)):
    """
    Upload and analyze trading CSV file.
    
    Process:
    1. Parse CSV and standardize columns
    2. Match orders into complete trades using FIFO
    3. Calculate performance metrics from closed trades only
    4. Return comprehensive analytics
    
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
        
        # Step 1: Parse CSV into standardized order DataFrame
        logger.info(f"Parsing CSV file: {file.filename}")
        orders_df = parse_csv(content_str)
        
        if len(orders_df) == 0:
            raise HTTPException(status_code=400, detail="No valid orders found in CSV")
        
        # Step 2: Match orders into complete trades using FIFO
        logger.info(f"Matching {len(orders_df)} orders into trades using FIFO...")
        parser = TradeParser()
        trades_df = parser.parse_orders(orders_df)
        
        if len(trades_df) == 0:
            logger.warning("No completed trades found (all positions may be open)")
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "total_orders": len(orders_df),
                "completed_trades": 0,
                "open_positions": len(parser.get_open_positions()),
                "message": "No completed trades found. All positions may still be open.",
                "metrics": PerformanceMetrics(trades_df).calculate_all_metrics()
            })
        
        # Step 3: Calculate performance metrics
        logger.info(f"Calculating metrics for {len(trades_df)} completed trades...")
        metrics_calculator = PerformanceMetrics(trades_df)
        metrics = metrics_calculator.calculate_all_metrics()
        
        # Sanitize for JSON
        metrics = sanitize_for_json(metrics)
        
        # Get open positions info
        open_positions = parser.get_open_positions()
        
        logger.info(f"Successfully analyzed {file.filename}")
        logger.info(f"  - Total orders: {len(orders_df)}")
        logger.info(f"  - Completed trades: {len(trades_df)}")
        logger.info(f"  - Open positions: {len(open_positions)}")
        logger.info(f"  - Total P&L: ${metrics['summary']['total_pnl']:.2f}")
        logger.info(f"  - Win Rate: {metrics['win_loss']['win_rate']:.1f}%")
        logger.info(f"  - Expectancy: ${metrics['summary']['expectancy']:.2f}")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "total_orders": len(orders_df),
            "completed_trades": len(trades_df),
            "open_positions": len(open_positions),
            "metrics": metrics
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "trade_parser": "operational",
            "performance_metrics": "operational"
        }
    }


@app.get("/api/docs/metrics")
async def metrics_documentation():
    """
    Documentation for all calculated metrics.
    """
    return {
        "summary_metrics": {
            "total_pnl": "Sum of all realized P&L from closed trades",
            "avg_monthly_return": "Average P&L per month",
            "sharpe_ratio": "Risk-adjusted return (daily returns, annualized)",
            "expectancy": "Expected value per trade: (WinRate × AvgWin) + ((1-WinRate) × AvgLoss)"
        },
        "win_loss_metrics": {
            "win_rate": "Percentage of profitable trades",
            "avg_win": "Average profit from winning trades",
            "avg_loss": "Average loss from losing trades (negative)",
            "profit_factor": "Gross profit ÷ Gross loss"
        },
        "risk_metrics": {
            "max_drawdown": "Maximum peak-to-trough decline in equity (%)",
            "avg_hold_length": "Average number of days per trade",
            "total_trades": "Number of completed trade pairs"
        },
        "trade_matching": {
            "method": "FIFO (First In First Out)",
            "description": "Orders are matched chronologically per symbol",
            "partial_fills": "Supported with proportional fee allocation",
            "open_positions": "Excluded from all performance metrics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
