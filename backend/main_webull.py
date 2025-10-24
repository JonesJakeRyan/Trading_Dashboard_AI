"""
Trading Performance Dashboard API - Webull Broker Matching
Uses average-cost position accounting to match Webull's broker dashboard.
No fees are included in P&L calculations.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from typing import Dict, Any

from services.ingest import ingest_csvs
from services.accounting_lifo import LIFOEngine
from services.metrics import MetricsCalculator, filter_trades_ytd
from demo_data import get_demo_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Performance Dashboard API - Webull Match",
    version="6.0.0",
    description="LIFO position accounting for equities matching Webull broker dashboard (realized P&L only, no fees)"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://www.jonesdatasoftware.com",
        "https://jonesdatasoftware.com",
        "https://*.railway.app",
        "*"  # Allow all for now, restrict later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "trading-dashboard-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "Trading Performance Dashboard API - Webull Match",
        "version": "6.0.0",
        "features": [
            "LIFO position accounting",
            "Round-trip trade tracking",
            "US/Eastern timezone for all date operations",
            "No fees in P&L calculations",
            "Matches Webull broker dashboard metrics",
            "YTD filtering",
            "Equities only (options removed)"
        ]
    }


@app.get("/api/demo")
async def get_demo():
    """
    Get demo metrics from pre-loaded backend CSV.
    This endpoint serves as a demonstration of the dashboard.
    """
    try:
        demo_data = get_demo_metrics(starting_equity=10000.0, ytd_only=True)
        
        if demo_data is None:
            raise HTTPException(status_code=500, detail="Failed to load demo data")
        
        return JSONResponse(content=demo_data)
        
    except Exception as e:
        logger.error(f"Error in demo endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_trades(
    file: UploadFile = File(...),
    starting_equity: float = Query(10000, gt=0),
    ytd_only: bool = Query(True)
):
    """
    Upload and analyze single CSV file (equities or options).
    
    Args:
        file: CSV file with trade data
        starting_equity: Starting capital for Sharpe/drawdown (default $10,000)
        ytd_only: If True, filter to YTD only (default True)
    
    Returns:
        JSON with summary, win_loss, risk, timeseries, and notes
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Determine file type by filename
        is_options = 'option' in file.filename.lower()
        
        # Ingest CSV (NO YTD filtering - accounting needs full history!)
        logger.info(f"Processing {'options' if is_options else 'equities'} file: {file.filename}")
        
        if is_options:
            fills = ingest_csvs(options_csv=content_str, ytd_only=False)
        else:
            fills = ingest_csvs(equities_csv=content_str, ytd_only=False)
        
        if len(fills) == 0:
            raise HTTPException(status_code=400, detail="No valid fills found in CSV")
        
        # Process fills through accounting engine (full history)
        logger.info(f"Processing {len(fills)} fills through LIFO accounting engine...")
        engine = LIFOEngine()
        trades = engine.process_fills(fills)
        
        # NOW filter trades by close_time if YTD requested
        if ytd_only and len(trades) > 0:
            trades = filter_trades_ytd(trades)
        
        if len(trades) == 0:
            logger.warning("No completed round-trip trades found")
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "total_fills": len(fills),
                "completed_trades": 0,
                "message": "No completed round-trip trades. All positions may still be open.",
                "metrics": MetricsCalculator(trades, starting_equity).calculate_all_metrics()
            })
        
        # Calculate metrics
        logger.info(f"Calculating metrics for {len(trades)} completed trades...")
        calculator = MetricsCalculator(trades, starting_equity)
        metrics = calculator.calculate_all_metrics()
        
        logger.info(f"Successfully analyzed {file.filename}")
        logger.info(f"  - Total fills: {len(fills)}")
        logger.info(f"  - Completed trades: {len(trades)}")
        logger.info(f"  - Total P&L: ${metrics['summary']['total_pnl']:.2f}")
        logger.info(f"  - Win Rate: {metrics['win_loss']['win_rate']:.1f}%")
        logger.info(f"  - Expectancy: ${metrics['summary']['expectancy']:.2f}")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "total_fills": len(fills),
            "completed_trades": len(trades),
            "settings": {
                "starting_equity": starting_equity,
                "ytd_only": ytd_only
            },
            "metrics": metrics
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/upload/combined")
async def upload_combined(
    equities_file: UploadFile = File(None),
    options_file: UploadFile = File(None),
    starting_equity: float = Query(10000, gt=0),
    ytd_only: bool = Query(True)
):
    """
    Upload both equities and options CSVs for combined analysis.
    
    Args:
        equities_file: CSV file with equity trades
        options_file: CSV file with options trades
        starting_equity: Starting capital for Sharpe/drawdown (default $10,000)
        ytd_only: If True, filter to YTD only (default True)
    
    Returns:
        Combined metrics from both equities and options
    """
    try:
        if not equities_file and not options_file:
            raise HTTPException(status_code=400, detail="At least one file must be provided")
        
        # Read files
        equities_csv = None
        options_csv = None
        
        if equities_file:
            if not equities_file.filename.endswith('.csv'):
                raise HTTPException(status_code=400, detail="Equities file must be CSV")
            content = await equities_file.read()
            equities_csv = content.decode('utf-8')
            logger.info(f"Loaded equities file: {equities_file.filename}")
        
        if options_file:
            if not options_file.filename.endswith('.csv'):
                raise HTTPException(status_code=400, detail="Options file must be CSV")
            content = await options_file.read()
            options_csv = content.decode('utf-8')
            logger.info(f"Loaded options file: {options_file.filename}")
        
        # Ingest both CSVs (NO YTD filtering - accounting needs full history!)
        fills = ingest_csvs(
            equities_csv=equities_csv,
            options_csv=options_csv,
            ytd_only=False
        )
        
        if len(fills) == 0:
            raise HTTPException(status_code=400, detail="No valid fills found in uploaded files")
        
        # Count by asset type
        equity_fills = len(fills[fills['asset_type'] == 'equity'])
        option_fills = len(fills[fills['asset_type'] == 'option'])
        
        # Process fills through accounting engine (full history)
        logger.info(f"Processing {len(fills)} total fills ({equity_fills} equity, {option_fills} option)...")
        engine = LIFOEngine()
        trades = engine.process_fills(fills)
        
        # NOW filter trades by close_time if YTD requested
        if ytd_only and len(trades) > 0:
            trades = filter_trades_ytd(trades)
        
        if len(trades) == 0:
            logger.warning("No completed round-trip trades found")
            return JSONResponse(content={
                "success": True,
                "equities_file": equities_file.filename if equities_file else None,
                "options_file": options_file.filename if options_file else None,
                "total_fills": len(fills),
                "equity_fills": equity_fills,
                "option_fills": option_fills,
                "completed_trades": 0,
                "message": "No completed round-trip trades. All positions may still be open.",
                "metrics": MetricsCalculator(trades, starting_equity).calculate_all_metrics()
            })
        
        # Calculate breakdown by asset type
        equity_pnl = float(trades[trades['asset_type'] == 'equity']['pnl'].sum()) if 'equity' in trades['asset_type'].values else 0.0
        option_pnl = float(trades[trades['asset_type'] == 'option']['pnl'].sum()) if 'option' in trades['asset_type'].values else 0.0
        
        # Calculate metrics
        logger.info(f"Calculating metrics for {len(trades)} completed trades...")
        calculator = MetricsCalculator(trades, starting_equity)
        metrics = calculator.calculate_all_metrics()
        
        logger.info(f"Successfully analyzed combined files")
        logger.info(f"  - Equity fills: {equity_fills}, P&L: ${equity_pnl:.2f}")
        logger.info(f"  - Option fills: {option_fills}, P&L: ${option_pnl:.2f}")
        logger.info(f"  - Combined P&L: ${metrics['summary']['total_pnl']:.2f}")
        
        return JSONResponse(content={
            "success": True,
            "equities_file": equities_file.filename if equities_file else None,
            "options_file": options_file.filename if options_file else None,
            "total_fills": len(fills),
            "equity_fills": equity_fills,
            "option_fills": option_fills,
            "completed_trades": len(trades),
            "breakdown": {
                "equity_pnl": round(equity_pnl, 2),
                "option_pnl": round(option_pnl, 2),
                "combined_pnl": round(metrics['summary']['total_pnl'], 2)
            },
            "settings": {
                "starting_equity": starting_equity,
                "ytd_only": ytd_only
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
        "version": "4.0.0",
        "services": {
            "ingest": "operational",
            "accounting": "operational",
            "metrics": "operational"
        },
        "accounting_mode": "average_cost_round_trip",
        "timezone": "America/New_York",
        "fees_included": False
    }


@app.post("/api/ai-suggestions")
async def get_ai_suggestions(payload: Dict[str, Any] = Body(...)):
    """
    Generate AI-powered trading suggestions based on metrics and trade data.
    """
    try:
        metrics = payload.get('metrics', {})
        
        # Get OpenAI API key from environment
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            return JSONResponse(content={
                "suggestions": "⚠️ OpenAI API key not configured. Set OPENAI_API_KEY environment variable to enable AI suggestions.\n\nBased on your metrics:\n• Win Rate: Consider analyzing your losing trades to identify patterns\n• Hold Time: Review if your average hold time aligns with your strategy\n• Diversification: Evaluate your symbol concentration for risk management"
            })
        
        # Get per-symbol breakdown for detailed analysis
        per_symbol = metrics.get('per_symbol', [])
        
        # Get top winners and losers
        sorted_symbols = sorted(per_symbol, key=lambda x: x.get('total_pnl', 0), reverse=True)
        top_winners = sorted_symbols[:5] if len(sorted_symbols) >= 5 else sorted_symbols
        top_losers = sorted_symbols[-5:] if len(sorted_symbols) >= 5 else []
        
        # Format symbol data
        winners_str = "\n".join([
            f"  • {s['symbol']}: ${s['total_pnl']:.2f} ({s['num_trades']} trades, {s.get('win_rate', 0):.0f}% win rate)"
            for s in top_winners
        ])
        
        losers_str = "\n".join([
            f"  • {s['symbol']}: ${s['total_pnl']:.2f} ({s['num_trades']} trades, {s.get('win_rate', 0):.0f}% win rate)"
            for s in top_losers
        ])
        
        # Prepare comprehensive analysis for OpenAI
        summary = f"""
PERFORMANCE OVERVIEW:
- Total P&L: ${metrics.get('summary', {}).get('total_pnl', 0):.2f}
- Win Rate: {metrics.get('win_loss', {}).get('round_trip_win_rate', 0):.1f}% ({metrics.get('win_loss', {}).get('round_trip_wins', 0)}W / {metrics.get('win_loss', {}).get('round_trip_losses', 0)}L)
- Average Win: ${metrics.get('win_loss', {}).get('avg_win', 0)} vs Average Loss: ${metrics.get('win_loss', {}).get('avg_loss', 0)}
- Profit Factor: {metrics.get('win_loss', {}).get('profit_factor', 0):.2f}
- Max Drawdown: {metrics.get('risk', {}).get('max_drawdown_pct', 0):.2f}%

TRADING BEHAVIOR:
- Average Hold Time: {metrics.get('efficiency', {}).get('avg_hold_time_hours', 0) / 24:.1f} days
- Average Trade Size: ${metrics.get('efficiency', {}).get('avg_trade_size', 0):,.0f}
- Return Skewness: {metrics.get('efficiency', {}).get('return_skewness', 0):.2f} (negative = loss-heavy)
- Win Streak: {metrics.get('behavioral', {}).get('max_win_streak', 0)} | Loss Streak: {metrics.get('behavioral', {}).get('max_loss_streak', 0)}
- Position Bias: {metrics.get('behavioral', {}).get('long_trade_pct', 0):.0f}% Long / {metrics.get('behavioral', {}).get('short_trade_pct', 0):.0f}% Short
- Diversification: {metrics.get('behavioral', {}).get('unique_symbols', 0)} symbols (Top 5 = {metrics.get('behavioral', {}).get('symbol_concentration_top5', 0):.0f}% of P&L)

TOP 5 WINNING SYMBOLS:
{winners_str}

TOP 5 LOSING SYMBOLS:
{losers_str}
"""
        
        # Call OpenAI API with more specific instructions
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert quantitative trading coach. Analyze the trading data and provide 4-6 SPECIFIC, ACTIONABLE recommendations.

REQUIREMENTS:
- Be extremely concise (max 2 sentences per point)
- Use concrete numbers from the data
- Provide specific examples using actual symbols
- Focus on highest-impact improvements
- Format as bullet points with bold headers

Example format:
• **Cut Losses Faster**: Your avg loss ($X) is 2x your avg win. Set hard stops at -Y% on symbols like ABC.
• **Double Down on XYZ**: 80% win rate with $X profit - increase position size by 50%."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this trading performance and provide specific, actionable recommendations:\n\n{summary}"
                }
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        suggestions = response.choices[0].message.content
        
        return JSONResponse(content={"suggestions": suggestions})
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        return JSONResponse(content={
            "suggestions": f"📊 Quick Analysis:\n\n• Focus on improving your win rate ({metrics.get('win_loss', {}).get('round_trip_win_rate', 0):.1f}%)\n• Review your risk management - max drawdown is {metrics.get('risk', {}).get('max_drawdown_pct', 0):.1f}%\n• Consider your position sizing and diversification strategy\n• Analyze your best performing symbols for patterns"
        })


@app.get("/api/docs/accounting")
async def accounting_documentation():
    """
    Documentation for accounting methodology.
    """
    return {
        "accounting_mode": "average_cost_round_trip",
        "description": "Tracks positions using average cost basis and emits trades only on full round-trips (flat → flat)",
        "timezone": "America/New_York",
        "fees_included": False,
        "rounding": {
            "quantity_decimals": 4,
            "price_decimals": 2
        },
        "position_tracking": {
            "long_increase": "new_avg = (avg_cost × pos_qty + price × qty) / (pos_qty + qty)",
            "long_decrease": "pnl = (price - avg_cost) × close_qty × multiplier",
            "short_increase": "new_avg = (avg_cost × |pos_qty| + price × qty) / (|pos_qty| + qty)",
            "short_decrease": "pnl = (avg_cost - price) × close_qty × multiplier"
        },
        "trade_definition": "One trade = complete position cycle returning to zero (flat → flat)",
        "options": {
            "multiplier": 100,
            "underlying_extraction": "Parsed from option symbol",
            "contract_grouping": "By full option symbol (includes expiry, strike, right)"
        },
        "metrics": {
            "total_pnl": "Sum of all realized P&L from closed trades",
            "win_rate": "Percentage of trades with pnl > 0",
            "expectancy": "(win_rate × avg_win) + ((1 - win_rate) × avg_loss)",
            "sharpe_ratio": "(mean(daily_return) / std(daily_return)) × √252",
            "max_drawdown": "abs(min((equity / cummax(equity) - 1) × 100))"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
