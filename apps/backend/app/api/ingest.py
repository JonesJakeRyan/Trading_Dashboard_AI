"""
CSV ingest API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.trade import IngestRequest, IngestResponse, ValidationError
from app.services.csv_parser import CSVParser, CSVParserError
from app.services.fifo_engine import FIFOEngine
from app.services.metrics_calculator import MetricsCalculator
from app.models.trade import NormalizedTrade, ClosedLot
from app.models.metrics import PerDayPnL, Aggregate
from app.database import get_db

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=IngestResponse)
async def ingest_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    template: str = Form(..., description="Template type: webull_v1, robinhood_v1, or unified_v1"),
    account_id: Optional[str] = Form(None, description="Optional account identifier"),
    db: Session = Depends(get_db),
):
    """
    Upload and parse a CSV file of trades
    
    Supported templates:
    - webull_v1: Webull export format
    - robinhood_v1: Robinhood export format
    - unified_v1: Standardized format
    
    Returns job ID and processing status
    """
    job_id = str(uuid.uuid4())
    
    logger.info(
        f"CSV ingest started - job_id={job_id}, template={template}, "
        f"file={file.filename}, content_type={file.content_type}"
    )
    
    # Validate template
    valid_templates = ["webull_v1", "robinhood_v1", "unified_v1"]
    if template not in valid_templates:
        logger.warning(f"Invalid template: {template}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template. Must be one of: {', '.join(valid_templates)}"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV (.csv extension required)"
        )
    
    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Check file size (10 MB limit)
        if len(content) > 10 * 1024 * 1024:
            logger.warning(f"File too large: {len(content)} bytes")
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 10 MB limit"
            )
        
        logger.info(f"File read successfully: {len(content)} bytes")
        
        # Parse CSV
        parser = CSVParser(template=template)
        trades_data, errors = parser.parse(csv_content)
        
        # Log results
        logger.info(
            f"CSV parsing complete - job_id={job_id}, "
            f"trades_processed={len(trades_data)}, trades_failed={len(errors)}"
        )
        
        # If all trades failed, return error
        if len(trades_data) == 0 and len(errors) > 0:
            error_messages = [
                ValidationError(
                    message=f"Row {err['row']}: {err['error']}",
                    details=err
                )
                for err in errors[:5]  # Limit to first 5 errors
            ]
            
            return IngestResponse(
                job_id=job_id,
                status="failed",
                message=f"All {len(errors)} trades failed validation",
                trades_processed=0,
                trades_failed=len(errors),
                errors=error_messages
            )
        
        # Save trades to database
        logger.info(f"Saving {len(trades_data)} trades to database")
        
        normalized_trades = []
        for trade_data in trades_data:
            trade = NormalizedTrade(
                account_id=account_id,
                symbol=trade_data["symbol"],
                side=trade_data["side"],
                quantity=trade_data["quantity"],
                price=trade_data["price"],
                executed_at=datetime.fromisoformat(trade_data["executed_at"]),
                notes=trade_data.get("notes"),
                ingest_job_id=uuid.UUID(job_id)
            )
            normalized_trades.append(trade)
            db.add(trade)
        
        db.commit()
        logger.info(f"Saved {len(normalized_trades)} trades to database")
        
        # Process through FIFO engine
        logger.info("Running FIFO matching engine")
        fifo_engine = FIFOEngine()
        closed_lots = fifo_engine.process_trades(normalized_trades)
        
        # Clear existing closed lots for this account
        db.query(ClosedLot).filter(
            ClosedLot.account_id == account_id if account_id else ClosedLot.account_id.is_(None)
        ).delete()
        
        # Save closed lots
        for lot in closed_lots:
            db.add(lot)
        db.commit()
        logger.info(f"Saved {len(closed_lots)} closed lots")
        
        # Calculate and save metrics
        logger.info("Calculating metrics")
        calculator = MetricsCalculator(account_id=account_id)
        daily_pnl_series = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=True)
        aggregate = calculator.calculate_aggregates(closed_lots, daily_pnl_series)
        
        # Clear existing metrics
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
        
        logger.info(
            f"Metrics calculated - Total P&L: ${aggregate.total_realized_pnl}, "
            f"Win Rate: {aggregate.win_rate}"
        )
        
        # Return success with any partial errors
        return IngestResponse(
            job_id=job_id,
            status="completed",
            message=f"Successfully processed {len(trades_data)} trades, "
                    f"generated {len(closed_lots)} closed lots" + 
                    (f" ({len(errors)} failed)" if errors else ""),
            trades_processed=len(trades_data),
            trades_failed=len(errors),
            errors=[
                ValidationError(
                    message=f"Row {err['row']}: {err['error']}",
                    details={"row": err["row"], "error": err["error"]}
                )
                for err in errors[:5]  # Limit to first 5 errors
            ] if errors else None
        )
        
    except CSVParserError as e:
        logger.error(f"CSV parsing error - job_id={job_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except UnicodeDecodeError:
        logger.error(f"File encoding error - job_id={job_id}")
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"Unexpected error during ingest - job_id={job_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during file processing: {str(e)}"
        )


@router.get("/templates")
async def list_templates():
    """
    List available CSV templates with documentation
    """
    return {
        "templates": [
            {
                "id": "webull_v1",
                "name": "Webull v1",
                "description": "Webull export format for stock trades",
                "documentation": "/specs/broker_templates/webull_v1.md",
                "sample": "/specs/broker_templates/samples/webull_sample.csv"
            },
            {
                "id": "robinhood_v1",
                "name": "Robinhood v1",
                "description": "Robinhood export format for stock trades",
                "documentation": "/specs/broker_templates/robinhood_v1.md",
                "sample": "/specs/broker_templates/samples/robinhood_sample.csv"
            },
            {
                "id": "unified_v1",
                "name": "Unified v1",
                "description": "Standardized format for manual entry or custom exports",
                "documentation": "/specs/broker_templates/unified_v1.md",
                "sample": "/specs/broker_templates/samples/unified_sample.csv"
            }
        ]
    }
