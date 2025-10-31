"""
Metrics calculator for daily P&L series and aggregate statistics.

Converts closed lots into:
- Daily P&L series (EST timezone, continuous with zero-filled gaps)
- Aggregate metrics (total P&L, win rate, profit factor, etc.)
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date, timedelta
from collections import defaultdict
import pytz

from app.models.trade import ClosedLot
from app.models.metrics import PerDayPnL, Aggregate

logger = logging.getLogger(__name__)

# EST timezone
EST = pytz.timezone('America/New_York')


class MetricsCalculator:
    """
    Calculate daily P&L series and aggregate metrics from closed lots.
    """
    
    def __init__(self, account_id: Optional[str] = None):
        self.account_id = account_id
    
    def generate_daily_pnl_series(
        self,
        closed_lots: List[ClosedLot],
        fill_gaps: bool = True
    ) -> List[PerDayPnL]:
        """
        Generate daily P&L series from closed lots.
        
        Args:
            closed_lots: List of ClosedLot objects
            fill_gaps: If True, fill missing dates with zero P&L for continuous chart
        
        Returns:
            List of PerDayPnL objects sorted by date ASC
        """
        if not closed_lots:
            logger.info("No closed lots to process")
            return []
        
        logger.info(f"Generating daily P&L series from {len(closed_lots)} closed lots")
        
        # Group lots by date (EST)
        daily_lots: Dict[date, List[ClosedLot]] = defaultdict(list)
        
        for lot in closed_lots:
            # Convert close timestamp to EST date
            close_dt_est = lot.close_executed_at.astimezone(EST)
            close_date = close_dt_est.date()
            daily_lots[close_date].append(lot)
        
        # Calculate daily P&L
        daily_pnl_dict: Dict[date, Tuple[Decimal, int]] = {}
        
        for day, lots in daily_lots.items():
            daily_total = sum(
                Decimal(str(lot.realized_pnl)) for lot in lots
            )
            daily_pnl_dict[day] = (daily_total, len(lots))
        
        # Get date range
        if not daily_pnl_dict:
            return []
        
        min_date = min(daily_pnl_dict.keys())
        max_date = max(daily_pnl_dict.keys())
        
        # Fill gaps if requested
        if fill_gaps:
            current_date = min_date
            while current_date <= max_date:
                if current_date not in daily_pnl_dict:
                    daily_pnl_dict[current_date] = (Decimal('0'), 0)
                current_date += timedelta(days=1)
        
        # Create PerDayPnL objects with cumulative P&L
        sorted_dates = sorted(daily_pnl_dict.keys())
        cumulative_pnl = Decimal('0')
        per_day_pnl_list = []
        
        for day in sorted_dates:
            daily_total, lots_count = daily_pnl_dict[day]
            cumulative_pnl += daily_total
            
            per_day_pnl = PerDayPnL(
                account_id=self.account_id,
                date=day,
                daily_pnl=daily_total.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                cumulative_pnl=cumulative_pnl.quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                lots_closed=lots_count
            )
            per_day_pnl_list.append(per_day_pnl)
        
        logger.info(
            f"Generated {len(per_day_pnl_list)} daily P&L records "
            f"from {min_date} to {max_date}"
        )
        
        return per_day_pnl_list
    
    def calculate_aggregates(
        self,
        closed_lots: List[ClosedLot],
        per_day_pnl: List[PerDayPnL]
    ) -> Aggregate:
        """
        Calculate aggregate metrics from closed lots and daily P&L.
        
        Args:
            closed_lots: List of ClosedLot objects
            per_day_pnl: List of PerDayPnL objects
        
        Returns:
            Aggregate object with calculated metrics
        """
        if not closed_lots:
            logger.info("No closed lots - returning empty aggregates")
            return Aggregate(account_id=self.account_id)
        
        logger.info(f"Calculating aggregates from {len(closed_lots)} closed lots")
        
        # Basic totals
        total_pnl = sum(Decimal(str(lot.realized_pnl)) for lot in closed_lots)
        total_lots = len(closed_lots)
        
        # Win/Loss analysis
        winning_lots = [lot for lot in closed_lots if lot.realized_pnl > 0]
        losing_lots = [lot for lot in closed_lots if lot.realized_pnl < 0]
        
        total_gains = sum(
            (Decimal(str(lot.realized_pnl)) for lot in winning_lots),
            Decimal('0')
        )
        total_losses = sum(
            (Decimal(str(lot.realized_pnl)) for lot in losing_lots),
            Decimal('0')
        )
        
        # Calculate ratios
        win_rate = None
        if total_lots > 0:
            win_rate = Decimal(len(winning_lots)) / Decimal(total_lots)
        
        profit_factor = None
        if total_losses < 0:
            profit_factor = total_gains / abs(total_losses)
        
        avg_gain = None
        if winning_lots:
            avg_gain = total_gains / Decimal(len(winning_lots))
            logger.info(f"Average gain calculated: ${avg_gain} from {len(winning_lots)} winning lots")
        
        avg_loss = None
        if losing_lots:
            avg_loss = total_losses / Decimal(len(losing_lots))
            logger.info(f"Average loss calculated: ${avg_loss} from {len(losing_lots)} losing lots")
        
        # Best/Worst symbol
        symbol_pnl: Dict[str, Decimal] = defaultdict(Decimal)
        for lot in closed_lots:
            symbol_pnl[lot.symbol] += Decimal(str(lot.realized_pnl))
        
        best_symbol = None
        best_symbol_pnl = None
        worst_symbol = None
        worst_symbol_pnl = None
        
        if symbol_pnl:
            best_symbol = max(symbol_pnl.items(), key=lambda x: x[1])
            worst_symbol = min(symbol_pnl.items(), key=lambda x: x[1])
            best_symbol_pnl = best_symbol[1]
            worst_symbol_pnl = worst_symbol[1]
            best_symbol = best_symbol[0]
            worst_symbol = worst_symbol[0]
        
        # Best/Worst weekday
        weekday_pnl: Dict[str, Decimal] = defaultdict(Decimal)
        weekday_names = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        
        for lot in closed_lots:
            close_dt_est = lot.close_executed_at.astimezone(EST)
            weekday_name = weekday_names[close_dt_est.weekday()]
            weekday_pnl[weekday_name] += Decimal(str(lot.realized_pnl))
        
        best_weekday = None
        best_weekday_pnl = None
        worst_weekday = None
        worst_weekday_pnl = None
        
        if weekday_pnl:
            best_weekday = max(weekday_pnl.items(), key=lambda x: x[1])
            worst_weekday = min(weekday_pnl.items(), key=lambda x: x[1])
            best_weekday_pnl = best_weekday[1]
            worst_weekday_pnl = worst_weekday[1]
            best_weekday = best_weekday[0]
            worst_weekday = worst_weekday[0]
        
        # Date range
        first_trade_date = None
        last_trade_date = None
        if per_day_pnl:
            first_trade_date = per_day_pnl[0].date
            last_trade_date = per_day_pnl[-1].date
        
        # Count total trades (not just closed lots)
        # For now, use closed lots * 2 as approximation
        # In production, this would query normalized_trades table
        total_trades = total_lots * 2
        
        aggregate = Aggregate(
            account_id=self.account_id,
            total_realized_pnl=total_pnl.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ),
            total_lots_closed=total_lots,
            total_trades=total_trades,
            winning_lots=len(winning_lots),
            losing_lots=len(losing_lots),
            total_gains=total_gains.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ),
            total_losses=total_losses.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ),
            win_rate=win_rate.quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            ) if win_rate else None,
            profit_factor=profit_factor.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if profit_factor else None,
            average_gain=avg_gain.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if avg_gain else None,
            average_loss=avg_loss.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if avg_loss else None,
            best_symbol=best_symbol,
            best_symbol_pnl=best_symbol_pnl.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if best_symbol_pnl else None,
            worst_symbol=worst_symbol,
            worst_symbol_pnl=worst_symbol_pnl.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if worst_symbol_pnl else None,
            best_weekday=best_weekday,
            best_weekday_pnl=best_weekday_pnl.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if best_weekday_pnl else None,
            worst_weekday=worst_weekday,
            worst_weekday_pnl=worst_weekday_pnl.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ) if worst_weekday_pnl else None,
            first_trade_date=first_trade_date,
            last_trade_date=last_trade_date
        )
        
        logger.info(
            f"Aggregates calculated - Total P&L: ${aggregate.total_realized_pnl}, "
            f"Win Rate: {aggregate.win_rate}, Profit Factor: {aggregate.profit_factor}"
        )
        
        return aggregate
