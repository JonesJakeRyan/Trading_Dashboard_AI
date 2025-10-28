"""
AI Coach API endpoint for generating insights using OpenAI.

Endpoints:
- GET /api/v1/ai/coach - Generate AI insights based on metrics
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.metrics import Aggregate
from app.models.trade import ClosedLot
from app.services.ai_coach_service import AICoachService
from app.services.enhanced_metrics import EnhancedMetricsCalculator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ai/coach")
async def get_ai_insights(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    timeframe: Optional[str] = Query("ALL", description="Timeframe filter"),
    db: Session = Depends(get_db)
):
    """
    Generate AI coaching insights based on trading metrics.
    
    Returns:
    - summary: Brief overview of performance
    - pattern_insights: Observable patterns in trading behavior
    - risk_notes: Risk observations and triggers
    - top_actions: Recommended actions (no ticker advice)
    """
    logger.info(f"AI Coach request - account_id={account_id}, timeframe={timeframe}")
    
    try:
        # Get aggregate metrics
        query = db.query(Aggregate)
        if account_id:
            query = query.filter(Aggregate.account_id == account_id)
        else:
            query = query.filter(Aggregate.account_id.is_(None))
        
        aggregate = query.first()
        
        if not aggregate:
            logger.warning("No aggregate data found for AI insights")
            raise HTTPException(
                status_code=404,
                detail="No trading data available for AI analysis"
            )
        
        # Get closed lots for enhanced metrics
        lots_query = db.query(ClosedLot)
        if account_id:
            lots_query = lots_query.filter(ClosedLot.account_id == account_id)
        else:
            lots_query = lots_query.filter(ClosedLot.account_id.is_(None))
        
        closed_lots = lots_query.all()
        
        # Calculate enhanced metrics
        enhanced_calc = EnhancedMetricsCalculator(db, account_id)
        enhanced_metrics = enhanced_calc.calculate_all_enhanced_metrics(closed_lots)
        
        # Build comprehensive metrics dict for AI service
        metrics = {
            # Basic metrics
            "cumulative_pnl": float(aggregate.total_realized_pnl),
            "total_trades": aggregate.total_trades,
            "win_rate": float(aggregate.win_rate) * 100 if aggregate.win_rate else 0,
            "profit_factor": float(aggregate.profit_factor) if aggregate.profit_factor else 0,
            "avg_gain": float(aggregate.average_gain) if aggregate.average_gain else 0,
            "avg_loss": float(aggregate.average_loss) if aggregate.average_loss else 0,
            "best_symbol": aggregate.best_symbol or "N/A",
            "worst_symbol": aggregate.worst_symbol or "N/A",
            "best_weekday": aggregate.best_weekday or "N/A",
            "worst_weekday": aggregate.worst_weekday or "N/A",
            # Enhanced metrics
            **enhanced_metrics
        }
        
        # Generate insights using AI service
        ai_service = AICoachService()
        insights = ai_service.generate_insights(metrics)
        
        # Convert to dict for JSON response
        return insights.model_dump()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error generating AI insights"
        )
