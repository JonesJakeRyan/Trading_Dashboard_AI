"""
Enhanced Metrics Calculator - Advanced trading pattern analysis.

Calculates detailed metrics for AI insights:
- Holding time analysis
- Symbol concentration
- Win/loss streaks
- Trade timing patterns
- Position sizing analysis
- Risk metrics
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trade import ClosedLot
from app.models.metrics import PerDayPnL

logger = logging.getLogger(__name__)


class EnhancedMetricsCalculator:
    """Calculate advanced trading metrics for AI insights."""
    
    def __init__(self, db: Session, account_id: Optional[str] = None):
        self.db = db
        self.account_id = account_id
    
    def calculate_all_enhanced_metrics(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate all enhanced metrics from closed lots."""
        if not lots:
            return self._get_empty_metrics()
        
        logger.info(f"Calculating enhanced metrics for {len(lots)} lots")
        
        metrics = {
            **self.calculate_holding_times(lots),
            **self.calculate_symbol_concentration(lots),
            **self.calculate_streaks(lots),
            **self.calculate_timing_patterns(lots),
            **self.calculate_position_sizing(lots),
            **self.calculate_risk_metrics(lots)
        }
        
        logger.info("Enhanced metrics calculation complete")
        return metrics
    
    def calculate_holding_times(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate holding time statistics."""
        holding_times = []
        winner_times = []
        loser_times = []
        quick_flips = 0
        
        for lot in lots:
            if not lot.open_executed_at or not lot.close_executed_at:
                continue
            
            holding_time = (lot.close_executed_at - lot.open_executed_at).total_seconds() / 60  # minutes
            holding_times.append(holding_time)
            
            if lot.realized_pnl > 0:
                winner_times.append(holding_time)
            elif lot.realized_pnl < 0:
                loser_times.append(holding_time)
            
            # Quick flip = held less than 60 minutes
            if holding_time < 60:
                quick_flips += 1
        
        if not holding_times:
            return {
                "avg_holding_time_minutes": 0,
                "avg_holding_time_winners": 0,
                "avg_holding_time_losers": 0,
                "quick_flip_rate": 0
            }
        
        avg_holding = sum(holding_times) / len(holding_times)
        avg_winner_time = sum(winner_times) / len(winner_times) if winner_times else 0
        avg_loser_time = sum(loser_times) / len(loser_times) if loser_times else 0
        
        return {
            "avg_holding_time_minutes": round(avg_holding, 1),
            "avg_holding_time_winners": round(avg_winner_time, 1),
            "avg_holding_time_losers": round(avg_loser_time, 1),
            "quick_flip_rate": round(quick_flips / len(lots), 3)
        }
    
    def calculate_symbol_concentration(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate symbol concentration and diversity metrics."""
        symbol_counts = defaultdict(int)
        symbol_pnl = defaultdict(float)
        leveraged_etfs = {'TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'TNA', 'TZA', 'UDOW', 'SDOW'}
        leveraged_count = 0
        
        for lot in lots:
            symbol_counts[lot.symbol] += 1
            symbol_pnl[lot.symbol] += float(lot.realized_pnl)
            
            if lot.symbol in leveraged_etfs:
                leveraged_count += 1
        
        # Sort by trade count
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
        top_3_symbols = [s[0] for s in sorted_symbols[:3]]
        top_3_counts = [s[1] for s in sorted_symbols[:3]]
        
        # Calculate concentration ratio (top 3 / total)
        total_trades = len(lots)
        top_3_total = sum(top_3_counts)
        concentration_ratio = top_3_total / total_trades if total_trades > 0 else 0
        
        return {
            "total_unique_symbols": len(symbol_counts),
            "top_3_symbols": top_3_symbols,
            "top_3_trade_counts": top_3_counts,
            "concentration_ratio": round(concentration_ratio, 3),
            "leveraged_etf_pct": round(leveraged_count / total_trades, 3) if total_trades > 0 else 0
        }
    
    def calculate_streaks(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate win/loss streak statistics."""
        # Sort by close time
        sorted_lots = sorted(lots, key=lambda x: x.close_executed_at)
        
        current_streak = 0
        longest_win_streak = 0
        longest_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for lot in sorted_lots:
            if lot.realized_pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                current_streak = current_win_streak
                longest_win_streak = max(longest_win_streak, current_win_streak)
            elif lot.realized_pnl < 0:
                current_loss_streak += 1
                current_win_streak = 0
                current_streak = -current_loss_streak
                longest_loss_streak = max(longest_loss_streak, current_loss_streak)
            else:
                # Breakeven - reset streaks
                current_win_streak = 0
                current_loss_streak = 0
        
        return {
            "current_streak": current_streak,
            "longest_win_streak": longest_win_streak,
            "longest_loss_streak": longest_loss_streak
        }
    
    def calculate_timing_patterns(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate best/worst trading times."""
        hour_pnl = defaultdict(list)
        month_pnl = defaultdict(list)
        
        for lot in lots:
            if not lot.close_executed_at:
                continue
            
            # Hour of day (EST)
            hour = lot.close_executed_at.hour
            hour_pnl[hour].append(float(lot.realized_pnl))
            
            # Month
            month = lot.close_executed_at.month
            month_pnl[month].append(float(lot.realized_pnl))
        
        # Calculate average P&L per hour
        hour_avgs = {h: sum(pnls) / len(pnls) for h, pnls in hour_pnl.items() if pnls}
        best_hour = max(hour_avgs.items(), key=lambda x: x[1]) if hour_avgs else (0, 0)
        worst_hour = min(hour_avgs.items(), key=lambda x: x[1]) if hour_avgs else (0, 0)
        
        # Calculate average P&L per month
        month_avgs = {m: sum(pnls) / len(pnls) for m, pnls in month_pnl.items() if pnls}
        best_month = max(month_avgs.items(), key=lambda x: x[1]) if month_avgs else (0, 0)
        worst_month = min(month_avgs.items(), key=lambda x: x[1]) if month_avgs else (0, 0)
        
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        # Calculate trades per day
        if lots:
            first_trade = min(lot.close_executed_at for lot in lots if lot.close_executed_at)
            last_trade = max(lot.close_executed_at for lot in lots if lot.close_executed_at)
            days_trading = (last_trade - first_trade).days + 1
            trades_per_day = len(lots) / days_trading if days_trading > 0 else 0
        else:
            trades_per_day = 0
        
        return {
            "best_hour": f"{best_hour[0]:02d}:00-{best_hour[0]+1:02d}:00",
            "best_hour_avg_pnl": round(best_hour[1], 2),
            "worst_hour": f"{worst_hour[0]:02d}:00-{worst_hour[0]+1:02d}:00",
            "worst_hour_avg_pnl": round(worst_hour[1], 2),
            "best_month": month_names[best_month[0]] if best_month[0] > 0 else "N/A",
            "best_month_avg_pnl": round(best_month[1], 2),
            "worst_month": month_names[worst_month[0]] if worst_month[0] > 0 else "N/A",
            "worst_month_avg_pnl": round(worst_month[1], 2),
            "trades_per_day_avg": round(trades_per_day, 1)
        }
    
    def calculate_position_sizing(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate position sizing statistics."""
        quantities = [abs(float(lot.open_quantity)) for lot in lots]
        
        if not quantities:
            return {
                "avg_position_size_shares": 0,
                "position_size_std_dev": 0,
                "largest_position": 0,
                "smallest_position": 0,
                "sizing_consistency_score": 0
            }
        
        avg_size = sum(quantities) / len(quantities)
        
        # Calculate standard deviation
        variance = sum((q - avg_size) ** 2 for q in quantities) / len(quantities)
        std_dev = variance ** 0.5
        
        # Consistency score: 1 - (std_dev / avg_size), clamped to 0-1
        consistency = max(0, min(1, 1 - (std_dev / avg_size))) if avg_size > 0 else 0
        
        return {
            "avg_position_size_shares": round(avg_size, 1),
            "position_size_std_dev": round(std_dev, 1),
            "largest_position": round(max(quantities), 1),
            "smallest_position": round(min(quantities), 1),
            "sizing_consistency_score": round(consistency, 3)
        }
    
    def calculate_risk_metrics(self, lots: List[ClosedLot]) -> Dict[str, Any]:
        """Calculate risk and drawdown metrics."""
        # Get daily P&L series for drawdown calculation
        query = self.db.query(PerDayPnL).order_by(PerDayPnL.date)
        
        if self.account_id:
            query = query.filter(PerDayPnL.account_id == self.account_id)
        else:
            query = query.filter(PerDayPnL.account_id.is_(None))
        
        daily_records = query.all()
        
        if not daily_records:
            return {
                "max_drawdown": 0,
                "max_drawdown_pct": 0,
                "daily_pnl_volatility": 0
            }
        
        # Calculate max drawdown
        cumulative_pnls = [float(r.cumulative_pnl) for r in daily_records]
        daily_pnls = [float(r.daily_pnl) for r in daily_records]
        
        max_drawdown = 0
        peak = cumulative_pnls[0]
        
        for pnl in cumulative_pnls:
            if pnl > peak:
                peak = pnl
            drawdown = peak - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate volatility (std dev of daily P&L)
        avg_daily_pnl = sum(daily_pnls) / len(daily_pnls) if daily_pnls else 0
        variance = sum((p - avg_daily_pnl) ** 2 for p in daily_pnls) / len(daily_pnls) if daily_pnls else 0
        volatility = variance ** 0.5
        
        # Note: Drawdown % removed - misleading without account balance
        # Per PRD: No account balance in MVP, so only show dollar amount
        return {
            "max_drawdown": round(max_drawdown, 2),
            "daily_pnl_volatility": round(volatility, 2)
        }
    
    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            # Holding times
            "avg_holding_time_minutes": 0,
            "avg_holding_time_winners": 0,
            "avg_holding_time_losers": 0,
            "quick_flip_rate": 0,
            # Symbol concentration
            "total_unique_symbols": 0,
            "top_3_symbols": [],
            "top_3_trade_counts": [],
            "concentration_ratio": 0,
            "leveraged_etf_pct": 0,
            # Streaks
            "current_streak": 0,
            "longest_win_streak": 0,
            "longest_loss_streak": 0,
            # Timing
            "best_hour": "N/A",
            "best_hour_avg_pnl": 0,
            "worst_hour": "N/A",
            "worst_hour_avg_pnl": 0,
            "best_month": "N/A",
            "best_month_avg_pnl": 0,
            "worst_month": "N/A",
            "worst_month_avg_pnl": 0,
            "trades_per_day_avg": 0,
            # Position sizing
            "avg_position_size_shares": 0,
            "position_size_std_dev": 0,
            "largest_position": 0,
            "smallest_position": 0,
            "sizing_consistency_score": 0,
            # Risk metrics
            "max_drawdown": 0,
            "daily_pnl_volatility": 0
        }
