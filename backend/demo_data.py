"""
Demo data endpoint - serves pre-calculated metrics from the backend CSV
"""

from services.ingest import ingest_csvs
from services.accounting_lifo import LIFOEngine
from services.metrics import MetricsCalculator, filter_trades_ytd
import logging

logger = logging.getLogger(__name__)


def get_demo_metrics(starting_equity: float = 10000.0, ytd_only: bool = True):
    """
    Load demo data from the backend CSV and return calculated metrics.
    
    Args:
        starting_equity: Starting capital for Sharpe/drawdown
        ytd_only: If True, filter to YTD only
        
    Returns:
        Dict with metrics and metadata
    """
    try:
        # Load the demo CSV (from parent directory)
        import os
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'Webull_Orders_Records.csv')
        with open(csv_path, 'r') as f:
            equities_csv = f.read()
        
        # Process
        fills = ingest_csvs(equities_csv=equities_csv, ytd_only=False)
        
        if len(fills) == 0:
            return None
        
        # Run LIFO accounting
        engine = LIFOEngine()
        trades = engine.process_fills(fills)
        
        # Filter YTD if requested
        if ytd_only and len(trades) > 0:
            trades = filter_trades_ytd(trades)
        
        if len(trades) == 0:
            return None
        
        # Calculate metrics
        calculator = MetricsCalculator(trades, starting_equity)
        metrics = calculator.calculate_all_metrics()
        
        # Add demo metadata
        return {
            "success": True,
            "is_demo": True,
            "demo_account": "Sample Trading Account",
            "total_fills": len(fills),
            "completed_trades": len(trades),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error loading demo data: {e}")
        return None
