"""
Demo API endpoints for showcasing the dashboard with pre-loaded data.

Endpoints:
- GET /api/demo/metrics - Get demo metrics
- GET /api/demo/chart - Get demo chart data
- GET /api/demo/ai/coach - Get demo AI insights (placeholder)
"""
import logging
from typing import Optional
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/demo/metrics")
async def get_demo_metrics(
    timeframe: Optional[str] = Query("ALL", description="Timeframe filter")
):
    """
    Get demo metrics using the pre-loaded creator CSV data.
    
    This endpoint returns metrics from account_id=None (default account).
    """
    logger.info(f"Fetching demo metrics - timeframe={timeframe}")
    
    # Import here to avoid circular dependencies
    from app.database import SessionLocal
    from app.api.metrics import get_metrics
    from fastapi import Depends
    
    # Create a database session
    db = SessionLocal()
    try:
        # Call the existing metrics endpoint with no account_id filter
        result = await get_metrics(
            account_id=None,
            timeframe=timeframe,
            db=db
        )
        
        # Transform to match frontend expectations
        return {
            "metrics": {
                "cumulative_pnl": result.get("total_realized_pnl", 0),
                "total_trades": result.get("total_trades", 0),
                "win_rate": result.get("win_rate", 0),
                "avg_gain": result.get("average_gain", 0),
                "avg_loss": result.get("average_loss", 0),
                "profit_factor": result.get("profit_factor", 0),
                "best_symbol": result.get("best_symbol", "N/A"),
                "worst_symbol": result.get("worst_symbol", "N/A"),
                "best_weekday": result.get("best_weekday", "N/A"),
                "worst_weekday": result.get("worst_weekday", "N/A"),
            },
            "chart_data": []  # Will be fetched separately
        }
    finally:
        db.close()


@router.get("/demo/chart")
async def get_demo_chart(
    timeframe: Optional[str] = Query("ALL", description="Timeframe filter")
):
    """
    Get demo chart data using the pre-loaded creator CSV data.
    """
    logger.info(f"Fetching demo chart data - timeframe={timeframe}")
    
    from app.database import SessionLocal
    from app.api.metrics import get_chart_data
    
    db = SessionLocal()
    try:
        result = await get_chart_data(
            account_id=None,
            timeframe=timeframe,
            db=db
        )
        return result
    finally:
        db.close()


@router.get("/demo/ai/coach")
async def get_demo_ai_insights(
    timeframe: Optional[str] = Query("ALL", description="Timeframe filter")
):
    """
    Get demo AI insights using the AI Coach service.
    
    Uses the same AI service as the main app, providing real insights
    based on the demo dataset metrics.
    """
    logger.info(f"Fetching demo AI insights - timeframe={timeframe}")
    
    from app.database import SessionLocal
    from app.api.ai_coach import get_ai_insights
    
    db = SessionLocal()
    try:
        # Call the real AI coach endpoint with no account_id (demo data)
        result = await get_ai_insights(
            account_id=None,
            timeframe=timeframe,
            db=db
        )
        return result
    finally:
        db.close()
