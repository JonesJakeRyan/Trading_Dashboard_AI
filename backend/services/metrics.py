"""
Performance Metrics Calculator
Computes summary, win/loss, risk, and timeseries metrics from completed trades.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
import logging
import pytz

logger = logging.getLogger(__name__)

# US/Eastern timezone
EASTERN_TZ = 'America/New_York'


def filter_trades_ytd(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Filter trades to YTD based on close_time in US/Eastern timezone.
    
    This is the CORRECT way to filter YTD - after accounting has run on full history.
    Positions opened last year but closed this year will have correct P&L.
    
    Args:
        trades: DataFrame of completed trades with close_time column
        
    Returns:
        Filtered trades where close_time >= Jan 1 00:00:00 Eastern
    """
    if len(trades) == 0 or 'close_time' not in trades.columns:
        return trades
    
    # Get current year start in Eastern timezone
    eastern = pytz.timezone(EASTERN_TZ)
    now = datetime.now(eastern)
    ytd_start = eastern.localize(datetime(now.year, 1, 1, 0, 0, 0))
    
    # Ensure close_time is timezone-aware
    if trades['close_time'].dt.tz is None:
        trades['close_time'] = trades['close_time'].dt.tz_localize(EASTERN_TZ)
    else:
        trades['close_time'] = trades['close_time'].dt.tz_convert(EASTERN_TZ)
    
    # Filter
    ytd_trades = trades[trades['close_time'] >= ytd_start].copy()
    
    logger.info(f"Filtered to YTD trades: {len(ytd_trades)} from {len(trades)} total (by close_time)")
    
    return ytd_trades


class MetricsCalculator:
    """
    Calculates performance metrics from completed round-trip trades.
    All calculations exclude open positions.
    """
    
    def __init__(self, trades: pd.DataFrame, starting_equity: float = 10000.0):
        """
        Initialize metrics calculator.
        
        Args:
            trades: DataFrame of completed round-trip trades
            starting_equity: Starting account balance for Sharpe/drawdown
        """
        self.trades = trades.copy() if len(trades) > 0 else pd.DataFrame()
        self.starting_equity = starting_equity
        
        if len(self.trades) > 0:
            # Ensure close_time is timezone-aware Eastern
            if not pd.api.types.is_datetime64tz_dtype(self.trades['close_time']):
                self.trades['close_time'] = pd.to_datetime(self.trades['close_time'])
                if self.trades['close_time'].dt.tz is None:
                    self.trades['close_time'] = self.trades['close_time'].dt.tz_localize(EASTERN_TZ)
            
            # Convert to Eastern if different timezone
            self.trades['close_time'] = self.trades['close_time'].dt.tz_convert(EASTERN_TZ)
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all performance metrics.
        
        Returns:
            Dict with summary, win_loss, risk, timeseries, per_symbol, pnl_series, and notes
        """
        if len(self.trades) == 0:
            return self._empty_metrics()
        
        return {
            "summary": self.get_summary_metrics(),
            "win_loss": self.get_win_loss_metrics(),
            "risk": self.get_risk_metrics(),
            "efficiency": self.get_efficiency_metrics(),
            "behavioral": self.get_behavioral_metrics(),
            "per_symbol": self.get_per_symbol_breakdown(),
            "pnl_series": self.get_pnl_series(),
            "timeseries": self.get_timeseries(),
            "notes": {
                "accounting_mode": "lifo_round_trip",
                "asset_types": "equities_only",
                "timezone": EASTERN_TZ,
                "fees_included": False,
                "quantity_round_decimals": 4,
                "price_round_decimals": 2
            }
        }
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """Calculate summary performance metrics."""
        if len(self.trades) == 0:
            return {
                "total_pnl": 0.0,
                "avg_monthly_return": 0.0,
                "sharpe_ratio": 0.0,
                "expectancy": 0.0
            }
        
        # Total P&L
        total_pnl = float(self.trades['pnl'].sum())
        
        # Monthly returns
        daily_pnl = self._get_daily_pnl()
        if len(daily_pnl) > 0:
            # Resample to monthly
            monthly_pnl = daily_pnl.resample('M').sum()
            avg_monthly_return = float(monthly_pnl.mean()) if len(monthly_pnl) > 0 else 0.0
        else:
            avg_monthly_return = 0.0
        
        # Sharpe Ratio
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Expectancy
        expectancy = self._calculate_expectancy()
        
        return {
            "total_pnl": round(total_pnl, 2),
            "avg_monthly_return": round(avg_monthly_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2) if not np.isnan(sharpe_ratio) else 0.0,
            "expectancy": round(expectancy, 2) if not np.isnan(expectancy) else 0.0
        }
    
    def get_win_loss_metrics(self) -> Dict[str, float]:
        """Calculate win/loss statistics."""
        if len(self.trades) == 0:
            return {
                "total_wins": 0,
                "total_losses": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "round_trip_wins": 0,
                "round_trip_losses": 0,
                "round_trip_win_rate": 0.0
            }
        
        # Per-trade win rate (counts every close)
        wins = self.trades[self.trades['pnl'] > 0]
        losses = self.trades[self.trades['pnl'] < 0]
        
        total_wins = len(wins)
        total_losses = len(losses)
        win_rate = (total_wins / len(self.trades) * 100) if len(self.trades) > 0 else 0.0
        
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0.0
        
        total_win_amount = wins['pnl'].sum() if len(wins) > 0 else 0.0
        total_loss_amount = abs(losses['pnl'].sum()) if len(losses) > 0 else 0.0
        profit_factor = (total_win_amount / total_loss_amount) if total_loss_amount > 0 else 0.0
        
        # Round-trip win rate (aggregate by symbol, matches Webull)
        symbol_pnl = self.trades.groupby('symbol')['pnl'].sum()
        round_trip_wins = len(symbol_pnl[symbol_pnl > 0])
        round_trip_losses = len(symbol_pnl[symbol_pnl < 0])
        round_trip_total = len(symbol_pnl)
        round_trip_win_rate = (round_trip_wins / round_trip_total * 100) if round_trip_total > 0 else 0.0
        
        return {
            "total_wins": int(total_wins),
            "total_losses": int(total_losses),
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "round_trip_wins": int(round_trip_wins),
            "round_trip_losses": int(round_trip_losses),
            "round_trip_win_rate": round(round_trip_win_rate, 2)
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Calculate risk-related metrics."""
        if len(self.trades) == 0:
            return {
                "max_drawdown_pct": 0.0,
                "avg_hold_days": 0.0,
                "total_trades": 0
            }
        
        # Max drawdown
        max_dd = self._calculate_max_drawdown()
        
        # Average hold length
        if 'entry_time' in self.trades.columns:
            hold_times = (self.trades['close_time'] - self.trades['entry_time']).dt.total_seconds()
            avg_hold_days = float(hold_times.mean() / 86400) if len(hold_times) > 0 else 0.0
        else:
            avg_hold_days = 0.0
        
        return {
            "max_drawdown_pct": round(max_dd, 2),
            "avg_hold_days": round(avg_hold_days, 2),
            "total_trades": int(len(self.trades))
        }
    
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Calculate trade efficiency metrics."""
        if len(self.trades) == 0:
            return {
                "avg_hold_time_hours": 0.0,
                "avg_trade_size": 0.0,
                "avg_return_per_trade": 0.0,
                "return_skewness": 0.0,
                "pnl_volatility": 0.0
            }
        
        # Average hold time (in hours)
        if 'entry_time' in self.trades.columns and 'close_time' in self.trades.columns:
            hold_times = (self.trades['close_time'] - self.trades['entry_time']).dt.total_seconds() / 3600
            avg_hold_hours = float(hold_times.mean()) if len(hold_times) > 0 else 0.0
        else:
            avg_hold_hours = 0.0
        
        # Average trade size (notional value)
        if 'qty_closed' in self.trades.columns and 'avg_entry' in self.trades.columns:
            trade_sizes = self.trades['qty_closed'] * self.trades['avg_entry']
            avg_trade_size = float(trade_sizes.mean()) if len(trade_sizes) > 0 else 0.0
        else:
            avg_trade_size = 0.0
        
        # Average return per trade (%)
        if avg_trade_size > 0:
            avg_return_pct = (self.trades['pnl'].mean() / avg_trade_size * 100) if avg_trade_size > 0 else 0.0
        else:
            avg_return_pct = 0.0
        
        # Skewness of returns
        try:
            from scipy import stats
            returns = self.trades['pnl'].values
            skewness = float(stats.skew(returns)) if len(returns) > 2 else 0.0
        except ImportError:
            # Fallback: simple skewness calculation
            returns = self.trades['pnl'].values
            mean = returns.mean()
            std = returns.std()
            if std > 0:
                skewness = float(((returns - mean) ** 3).mean() / (std ** 3))
            else:
                skewness = 0.0
        
        # Volatility of P&L (standard deviation)
        pnl_volatility = float(self.trades['pnl'].std()) if len(self.trades) > 1 else 0.0
        
        return {
            "avg_hold_time_hours": round(avg_hold_hours, 2),
            "avg_trade_size": round(avg_trade_size, 2),
            "avg_return_per_trade": round(avg_return_pct, 2),
            "return_skewness": round(skewness, 2),
            "pnl_volatility": round(pnl_volatility, 2)
        }
    
    def get_behavioral_metrics(self) -> Dict[str, Any]:
        """Calculate behavioral trading metrics."""
        if len(self.trades) == 0:
            return {
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "avg_time_between_trades_hours": 0.0,
                "long_trade_pct": 0.0,
                "short_trade_pct": 0.0,
                "symbol_concentration_top5": 0.0,
                "unique_symbols": 0
            }
        
        # Win/loss streaks
        wins = (self.trades['pnl'] > 0).astype(int)
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for is_win in wins:
            if is_win:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        # Time between trades
        if 'close_time' in self.trades.columns:
            sorted_trades = self.trades.sort_values('close_time')
            time_diffs = sorted_trades['close_time'].diff().dt.total_seconds() / 3600
            avg_time_between = float(time_diffs.mean()) if len(time_diffs) > 1 else 0.0
        else:
            avg_time_between = 0.0
        
        # Long vs Short distribution
        if 'direction' in self.trades.columns:
            long_count = len(self.trades[self.trades['direction'] == 'long'])
            short_count = len(self.trades[self.trades['direction'] == 'short'])
            total = len(self.trades)
            long_pct = (long_count / total * 100) if total > 0 else 0.0
            short_pct = (short_count / total * 100) if total > 0 else 0.0
        else:
            long_pct = 0.0
            short_pct = 0.0
        
        # Symbol concentration (top 5 symbols as % of total P&L)
        group_col = 'underlying' if 'underlying' in self.trades.columns else 'symbol'
        symbol_pnl = self.trades.groupby(group_col)['pnl'].sum().abs()
        top5_pnl = symbol_pnl.nlargest(5).sum()
        total_pnl = symbol_pnl.sum()
        concentration = (top5_pnl / total_pnl * 100) if total_pnl > 0 else 0.0
        unique_symbols = len(symbol_pnl)
        
        return {
            "max_win_streak": int(max_win_streak),
            "max_loss_streak": int(max_loss_streak),
            "avg_time_between_trades_hours": round(avg_time_between, 2),
            "long_trade_pct": round(long_pct, 2),
            "short_trade_pct": round(short_pct, 2),
            "symbol_concentration_top5": round(concentration, 2),
            "unique_symbols": int(unique_symbols)
        }
    
    def get_per_symbol_breakdown(self) -> List[Dict[str, Any]]:
        """
        Calculate per-symbol performance breakdown.
        
        Returns:
            List of dicts with symbol, num_trades, total_pnl, avg_pnl, win_rate
        """
        if len(self.trades) == 0:
            return []
        
        symbol_stats = []
        
        # Group by underlying (for options) or symbol (for equities)
        group_col = 'underlying' if 'underlying' in self.trades.columns else 'symbol'
        
        for symbol in self.trades[group_col].unique():
            symbol_trades = self.trades[self.trades[group_col] == symbol]
            total_pnl = float(symbol_trades['pnl'].sum())
            num_trades = len(symbol_trades)
            
            # Win rate for this symbol
            winners = symbol_trades['pnl'] > 0
            win_rate = float(winners.mean() * 100) if len(symbol_trades) > 0 else 0.0
            
            # Average P&L per trade
            avg_pnl = total_pnl / num_trades if num_trades > 0 else 0.0
            
            symbol_stats.append({
                "symbol": symbol,
                "num_trades": num_trades,
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "win_rate": round(win_rate, 2)
            })
        
        # Sort by total P&L descending
        symbol_stats.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        return symbol_stats
    
    def get_pnl_series(self) -> List[Dict[str, Any]]:
        """
        Get daily P&L time series.
        
        Returns:
            List of dicts with date, daily_pnl, cumulative_pnl
        """
        if len(self.trades) == 0:
            return []
        
        daily_pnl = self._get_daily_pnl()
        
        if len(daily_pnl) == 0:
            return []
        
        # Calculate cumulative P&L
        cumulative = daily_pnl.cumsum()
        
        # Build series
        series = []
        for date, pnl in daily_pnl.items():
            series.append({
                "date": date.strftime('%Y-%m-%d'),
                "daily_pnl": round(float(pnl), 2),
                "cumulative_pnl": round(float(cumulative.loc[date]), 2)
            })
        
        return series
    
    def get_timeseries(self) -> List[Dict[str, Any]]:
        """Get daily P&L and equity timeseries."""
        if len(self.trades) == 0:
            return []
        
        daily_pnl = self._get_daily_pnl()
        
        if len(daily_pnl) == 0:
            return []
        
        # Calculate equity
        equity = self.starting_equity + daily_pnl.cumsum()
        
        # Build timeseries
        timeseries = []
        for date, pnl in daily_pnl.items():
            timeseries.append({
                "date": date.strftime('%Y-%m-%d'),
                "daily_pnl": round(float(pnl), 2),
                "equity": round(float(equity.loc[date]), 2)
            })
        
        return timeseries
    
    def _get_daily_pnl(self) -> pd.Series:
        """
        Aggregate P&L by US/Eastern market day.
        
        Returns:
            Series with DatetimeIndex (date only) and daily P&L values
        """
        if len(self.trades) == 0:
            return pd.Series(dtype=float)
        
        # Extract date in Eastern timezone
        self.trades['close_date'] = self.trades['close_time'].dt.date
        
        # Group by date and sum P&L
        daily_pnl = self.trades.groupby('close_date')['pnl'].sum()
        
        # Convert index to DatetimeIndex for resampling
        daily_pnl.index = pd.to_datetime(daily_pnl.index)
        
        return daily_pnl
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio using daily returns.
        
        Formula: Sharpe = (mean(daily_return) / std(daily_return)) × √252
        where daily_return = daily_pnl / starting_equity
        """
        daily_pnl = self._get_daily_pnl()
        
        if len(daily_pnl) < 2:
            return np.nan
        
        # Calculate daily returns as fraction of starting equity
        daily_returns = daily_pnl / self.starting_equity
        
        # Sharpe ratio
        mean_return = daily_returns.mean()
        std_return = daily_returns.std(ddof=1)
        
        if std_return == 0 or np.isnan(std_return):
            return np.nan
        
        sharpe = (mean_return / std_return) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown as percentage.
        
        Formula: drawdown = (equity / cummax(equity) - 1) × 100
        Returns value between 0 and -100
        """
        daily_pnl = self._get_daily_pnl()
        
        if len(daily_pnl) == 0:
            return 0.0
        
        # Calculate equity curve
        equity = self.starting_equity + daily_pnl.cumsum()
        
        # Calculate running maximum
        running_max = equity.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity / running_max - 1) * 100
        
        # Max drawdown is the minimum (most negative) value
        max_dd = float(drawdown.min()) if len(drawdown) > 0 else 0.0
        
        # Ensure it's not below -100%
        max_dd = max(max_dd, -100.0)
        
        return max_dd
    
    def _calculate_expectancy(self) -> float:
        """
        Calculate expectancy per trade.
        
        Formula: expectancy = (win_rate × avg_win) + ((1 - win_rate) × avg_loss)
        """
        if len(self.trades) == 0:
            return np.nan
        
        winners = self.trades['pnl'] > 0
        win_rate = winners.mean()
        
        winning_trades = self.trades.loc[winners, 'pnl']
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0.0
        
        losing_trades = self.trades.loc[~winners, 'pnl']
        avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0.0
        
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return expectancy
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when no trades exist."""
        return {
            "summary": {
                "total_pnl": 0.0,
                "avg_monthly_return": 0.0,
                "sharpe_ratio": 0.0,
                "expectancy": 0.0
            },
            "win_loss": {
                "total_wins": 0,
                "total_losses": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "round_trip_wins": 0,
                "round_trip_losses": 0,
                "round_trip_win_rate": 0.0
            },
            "risk": {
                "max_drawdown_pct": 0.0,
                "avg_hold_days": 0.0,
                "total_trades": 0
            },
            "efficiency": {
                "avg_hold_time_hours": 0.0,
                "avg_trade_size": 0.0,
                "avg_return_per_trade": 0.0,
                "return_skewness": 0.0,
                "pnl_volatility": 0.0
            },
            "behavioral": {
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "avg_time_between_trades_hours": 0.0,
                "long_trade_pct": 0.0,
                "short_trade_pct": 0.0,
                "symbol_concentration_top5": 0.0,
                "unique_symbols": 0
            },
            "per_symbol": [],
            "pnl_series": [],
            "timeseries": [],
            "notes": {
                "accounting_mode": "lifo_round_trip",
                "asset_types": "equities_only",
                "timezone": EASTERN_TZ,
                "fees_included": False,
                "quantity_round_decimals": 4,
                "price_round_decimals": 2
            }
        }
