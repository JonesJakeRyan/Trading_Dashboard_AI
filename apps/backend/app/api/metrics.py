"""
Metrics API endpoints for retrieving P&L data and statistics.

Endpoints:
- GET /api/v1/metrics - Get aggregate metrics with optional timeframe filter
- GET /api/v1/chart - Get daily P&L series for charting
- POST /api/v1/metrics/process - Process trades through FIFO engine (internal)
"""
import logging
from typing import Optional, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import get_db
from app.models.metrics import PerDayPnL, Aggregate
from app.models.trade import ClosedLot, NormalizedTrade
from app.services.fifo_engine import FIFOEngine
from app.services.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    timeframe: Optional[str] = Query(
        None,
        description="Timeframe filter: 1D, 1W, 1M, 3M, 6M, 1Y, YTD, ALL"
    ),
    db: Session = Depends(get_db)
):
    """
    Get aggregate metrics with optional timeframe filter.
    
    Returns:
    - Total realized P&L
    - Win rate, profit factor
    - Best/worst symbols and weekdays
    - Average gain/loss
    - Date range
    """
    logger.info(f"Fetching metrics - account_id={account_id}, timeframe={timeframe}")
    
    try:
        # Get aggregate record
        query = db.query(Aggregate)
        if account_id:
            query = query.filter(Aggregate.account_id == account_id)
        else:
            query = query.filter(Aggregate.account_id.is_(None))
        
        aggregate = query.first()
        
        if not aggregate:
            logger.warning("No aggregate data found")
            return {
                "total_realized_pnl": 0,
                "total_lots_closed": 0,
                "win_rate": None,
                "profit_factor": None,
                "message": "No trading data available"
            }
        
        # Apply timeframe filter if specified
        filtered_pnl = None
        if timeframe and timeframe != "ALL":
            end_date = date.today()
            start_date = _calculate_start_date(end_date, timeframe)
            
            if start_date:
                # Recalculate metrics for timeframe
                filtered_pnl = _calculate_timeframe_metrics(
                    db, account_id, start_date, end_date
                )
        
        # Return aggregate or filtered metrics
        if filtered_pnl:
            return filtered_pnl
        
        return {
            "total_realized_pnl": float(aggregate.total_realized_pnl),
            "total_lots_closed": aggregate.total_lots_closed,
            "total_trades": aggregate.total_trades,
            "winning_lots": aggregate.winning_lots,
            "losing_lots": aggregate.losing_lots,
            "total_gains": float(aggregate.total_gains),
            "total_losses": float(aggregate.total_losses),
            "win_rate": float(aggregate.win_rate) if aggregate.win_rate else 0,
            "profit_factor": float(aggregate.profit_factor) if aggregate.profit_factor else 0,
            "average_gain": float(aggregate.average_gain) if aggregate.average_gain else 0,
            "average_loss": float(aggregate.average_loss) if aggregate.average_loss else 0,
            "best_symbol": aggregate.best_symbol,
            "best_symbol_pnl": float(aggregate.best_symbol_pnl) if aggregate.best_symbol_pnl else None,
            "worst_symbol": aggregate.worst_symbol,
            "worst_symbol_pnl": float(aggregate.worst_symbol_pnl) if aggregate.worst_symbol_pnl else None,
            "best_weekday": aggregate.best_weekday,
            "best_weekday_pnl": float(aggregate.best_weekday_pnl) if aggregate.best_weekday_pnl else None,
            "worst_weekday": aggregate.worst_weekday,
            "worst_weekday_pnl": float(aggregate.worst_weekday_pnl) if aggregate.worst_weekday_pnl else None,
            "first_trade_date": aggregate.first_trade_date.isoformat() if aggregate.first_trade_date else None,
            "last_trade_date": aggregate.last_trade_date.isoformat() if aggregate.last_trade_date else None,
        }
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error retrieving metrics"
        )


@router.get("/chart")
async def get_chart_data(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    timeframe: Optional[str] = Query(
        None,
        description="Timeframe filter: 1D, 1W, 1M, 3M, 6M, 1Y, YTD, ALL"
    ),
    db: Session = Depends(get_db)
):
    """
    Get daily P&L series for charting.
    
    Returns array of:
    - date: Calendar date (EST)
    - daily_pnl: P&L for that day
    - cumulative_pnl: Running total P&L
    - lots_closed: Number of lots closed that day
    """
    logger.info(f"Fetching chart data - account_id={account_id}, timeframe={timeframe}")
    
    try:
        # Build query
        query = db.query(PerDayPnL).order_by(PerDayPnL.date)
        
        if account_id:
            query = query.filter(PerDayPnL.account_id == account_id)
        else:
            query = query.filter(PerDayPnL.account_id.is_(None))
        
        # Apply timeframe filter
        if timeframe and timeframe != "ALL":
            end_date = date.today()
            start_date = _calculate_start_date(end_date, timeframe)
            
            if start_date:
                query = query.filter(PerDayPnL.date >= start_date)
        
        daily_pnl_records = query.all()
        
        if not daily_pnl_records:
            logger.warning("No chart data found")
            return {
                "data": [],
                "message": "No trading data available"
            }
        
        # Format for frontend
        chart_data = [
            {
                "date": record.date.isoformat(),
                "daily_pnl": float(record.daily_pnl),
                "cumulative_pnl": float(record.cumulative_pnl),
                "lots_closed": record.lots_closed
            }
            for record in daily_pnl_records
        ]
        
        logger.info(f"Returning {len(chart_data)} chart data points")
        
        return {
            "data": chart_data,
            "start_date": daily_pnl_records[0].date.isoformat(),
            "end_date": daily_pnl_records[-1].date.isoformat(),
            "total_days": len(chart_data)
        }
    
    except Exception as e:
        logger.error(f"Error fetching chart data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error retrieving chart data"
        )


@router.post("/metrics/process")
async def process_trades(
    account_id: Optional[str] = Query(None, description="Account ID to process"),
    db: Session = Depends(get_db)
):
    """
    Process all normalized trades through FIFO engine and update metrics.
    
    This is typically called after CSV ingest to recalculate all metrics.
    """
    logger.info(f"Processing trades for account_id={account_id}")
    
    try:
        # Fetch all normalized trades
        query = db.query(NormalizedTrade).order_by(NormalizedTrade.executed_at)
        
        if account_id:
            query = query.filter(NormalizedTrade.account_id == account_id)
        else:
            query = query.filter(NormalizedTrade.account_id.is_(None))
        
        trades = query.all()
        
        if not trades:
            logger.warning("No trades found to process")
            return {
                "status": "no_data",
                "message": "No trades found to process"
            }
        
        logger.info(f"Processing {len(trades)} trades")
        
        # Run FIFO engine
        fifo_engine = FIFOEngine()
        closed_lots = fifo_engine.process_trades(trades)
        
        logger.info(f"FIFO engine generated {len(closed_lots)} closed lots")
        
        # Clear existing closed lots for this account
        delete_query = db.query(ClosedLot)
        if account_id:
            delete_query = delete_query.filter(ClosedLot.account_id == account_id)
        else:
            delete_query = delete_query.filter(ClosedLot.account_id.is_(None))
        delete_query.delete()
        
        # Save new closed lots
        for lot in closed_lots:
            db.add(lot)
        db.flush()
        
        # Calculate metrics
        calculator = MetricsCalculator(account_id=account_id)
        daily_pnl_series = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=True)
        aggregate = calculator.calculate_aggregates(closed_lots, daily_pnl_series)
        
        logger.info(f"Generated {len(daily_pnl_series)} daily P&L records")
        
        # Clear existing metrics for this account
        db.query(PerDayPnL).filter(
            PerDayPnL.account_id == account_id if account_id else PerDayPnL.account_id.is_(None)
        ).delete()
        
        db.query(Aggregate).filter(
            Aggregate.account_id == account_id if account_id else Aggregate.account_id.is_(None)
        ).delete()
        
        # Save new metrics
        for daily_pnl in daily_pnl_series:
            db.add(daily_pnl)
        
        db.add(aggregate)
        db.commit()
        
        logger.info("Metrics processing complete")
        
        return {
            "status": "success",
            "trades_processed": len(trades),
            "lots_closed": len(closed_lots),
            "daily_records": len(daily_pnl_series),
            "total_pnl": float(aggregate.total_realized_pnl),
            "win_rate": float(aggregate.win_rate) if aggregate.win_rate else None
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing trades: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing trades: {str(e)}"
        )


def _calculate_start_date(end_date: date, timeframe: str) -> Optional[date]:
    """Calculate start date based on timeframe"""
    if timeframe == "1D":
        return end_date - timedelta(days=1)
    elif timeframe == "1W":
        return end_date - timedelta(weeks=1)
    elif timeframe == "1M":
        return end_date - timedelta(days=30)
    elif timeframe == "3M":
        return end_date - timedelta(days=90)
    elif timeframe == "6M":
        return end_date - timedelta(days=180)
    elif timeframe == "1Y":
        return end_date - timedelta(days=365)
    elif timeframe == "YTD":
        return date(end_date.year, 1, 1)
    return None


def _calculate_timeframe_metrics(
    db: Session,
    account_id: Optional[str],
    start_date: date,
    end_date: date
) -> dict:
    """Calculate metrics for a specific timeframe"""
    # Query closed lots in timeframe
    query = db.query(ClosedLot).filter(
        and_(
            ClosedLot.close_executed_at >= datetime.combine(start_date, datetime.min.time()),
            ClosedLot.close_executed_at <= datetime.combine(end_date, datetime.max.time())
        )
    )
    
    if account_id:
        query = query.filter(ClosedLot.account_id == account_id)
    else:
        query = query.filter(ClosedLot.account_id.is_(None))
    
    lots = query.all()
    
    if not lots:
        return {
            "total_realized_pnl": 0,
            "total_lots_closed": 0,
            "message": f"No data for timeframe {start_date} to {end_date}"
        }
    
    # Calculate metrics for this timeframe
    calculator = MetricsCalculator(account_id=account_id)
    daily_pnl = calculator.generate_daily_pnl_series(lots, fill_gaps=False)
    aggregate = calculator.calculate_aggregates(lots, daily_pnl)
    
    return {
        "total_realized_pnl": float(aggregate.total_realized_pnl),
        "total_lots_closed": aggregate.total_lots_closed,
        "total_trades": aggregate.total_trades,
        "winning_lots": aggregate.winning_lots,
        "losing_lots": aggregate.losing_lots,
        "total_gains": float(aggregate.total_gains),
        "total_losses": float(aggregate.total_losses),
        "win_rate": float(aggregate.win_rate) if aggregate.win_rate else None,
        "profit_factor": float(aggregate.profit_factor) if aggregate.profit_factor else None,
        "average_gain": float(aggregate.average_gain) if aggregate.average_gain else None,
        "average_loss": float(aggregate.average_loss) if aggregate.average_loss else None,
        "best_symbol": aggregate.best_symbol,
        "best_symbol_pnl": float(aggregate.best_symbol_pnl) if aggregate.best_symbol_pnl else None,
        "worst_symbol": aggregate.worst_symbol,
        "worst_symbol_pnl": float(aggregate.worst_symbol_pnl) if aggregate.worst_symbol_pnl else None,
        "best_weekday": aggregate.best_weekday,
        "best_weekday_pnl": float(aggregate.best_weekday_pnl) if aggregate.best_weekday_pnl else None,
        "worst_weekday": aggregate.worst_weekday,
        "worst_weekday_pnl": float(aggregate.worst_weekday_pnl) if aggregate.worst_weekday_pnl else None,
        "first_trade_date": aggregate.first_trade_date.isoformat() if aggregate.first_trade_date else None,
        "last_trade_date": aggregate.last_trade_date.isoformat() if aggregate.last_trade_date else None,
        "timeframe": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }
