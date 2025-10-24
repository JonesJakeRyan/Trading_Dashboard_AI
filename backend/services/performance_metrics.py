"""
Performance Metrics Service
Calculates all trading performance metrics from completed trades.
All calculations are based on closed trade pairs only.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Calculates comprehensive trading performance metrics from trade-level data.
    All metrics are based on realized P&L from closed trades only.
    """
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        Initialize with completed trades DataFrame.
        
        Args:
            trades_df: DataFrame with columns [symbol, pnl, entry_time, exit_time, etc.]
        """
        self.trades = trades_df.copy() if len(trades_df) > 0 else pd.DataFrame()
        
        if len(self.trades) > 0:
            # Ensure datetime columns
            if 'exit_time' in self.trades.columns:
                self.trades['exit_time'] = pd.to_datetime(self.trades['exit_time'])
            if 'entry_time' in self.trades.columns:
                self.trades['entry_time'] = pd.to_datetime(self.trades['entry_time'])
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all performance metrics"""
        if len(self.trades) == 0:
            return self._empty_metrics()
        
        return {
            "summary": self.get_summary_metrics(),
            "win_loss": self.get_win_loss_metrics(),
            "risk": self.get_risk_metrics(),
            "per_symbol": self.get_per_symbol_breakdown(),
            "timeseries": self.get_equity_curve(),
            "pnl_series": self.get_pnl_series()
        }
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """
        Calculate summary performance metrics.
        
        Returns:
            Dict with total_pnl, avg_monthly_return, sharpe_ratio, expectancy
        """
        if len(self.trades) == 0:
            return {
                "total_pnl": 0.0,
                "avg_monthly_return": 0.0,
                "sharpe_ratio": 0.0,
                "expectancy": 0.0
            }
        
        # Total P&L
        total_pnl = self.trades['pnl'].sum()
        
        # Monthly returns
        self.trades['month'] = self.trades['exit_time'].dt.to_period('M')
        monthly_pnl = self.trades.groupby('month')['pnl'].sum()
        avg_monthly_return = monthly_pnl.mean() if len(monthly_pnl) > 0 else 0.0
        
        # Sharpe Ratio (daily)
        daily_pnl = self.trades.groupby(self.trades['exit_time'].dt.date)['pnl'].sum()
        sharpe_ratio = 0.0
        if len(daily_pnl) > 1 and daily_pnl.std() != 0:
            sharpe_ratio = (daily_pnl.mean() / daily_pnl.std()) * np.sqrt(252)
        
        # Expectancy
        winning_trades = self.trades[self.trades['pnl'] > 0]
        losing_trades = self.trades[self.trades['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(self.trades) if len(self.trades) > 0 else 0.0
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0  # Negative
        
        # Expectancy = (WinRate × AvgWin) + ((1 - WinRate) × AvgLoss)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            "total_pnl": round(total_pnl, 2),
            "avg_monthly_return": round(avg_monthly_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "expectancy": round(expectancy, 2)
        }
    
    def get_win_loss_metrics(self) -> Dict[str, float]:
        """
        Calculate win/loss statistics.
        
        Returns:
            Dict with win_rate, avg_win, avg_loss, profit_factor
        """
        if len(self.trades) == 0:
            return {
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0
            }
        
        winning_trades = self.trades[self.trades['pnl'] > 0]
        losing_trades = self.trades[self.trades['pnl'] < 0]
        
        # Win Rate (percentage)
        win_rate = (len(winning_trades) / len(self.trades) * 100) if len(self.trades) > 0 else 0.0
        
        # Average Win/Loss
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0
        
        # Profit Factor
        total_profit = winning_trades['pnl'].sum()
        total_loss = abs(losing_trades['pnl'].sum())
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
        
        return {
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2)
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate risk-related metrics.
        
        Returns:
            Dict with max_drawdown, avg_hold_length, total_trades
        """
        if len(self.trades) == 0:
            return {
                "max_drawdown": 0.0,
                "avg_hold_length": 0.0,
                "total_trades": 0
            }
        
        # Max Drawdown
        daily_pnl = self.trades.groupby(self.trades['exit_time'].dt.date)['pnl'].sum()
        cumulative_pnl = daily_pnl.cumsum()
        running_max = cumulative_pnl.expanding().max()
        
        # Calculate drawdown percentage
        drawdown = ((cumulative_pnl - running_max) / running_max.replace(0, 1)) * 100
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0.0
        
        # Average hold length (in days)
        if 'hold_time_days' in self.trades.columns:
            avg_hold_length = self.trades['hold_time_days'].mean()
        else:
            avg_hold_length = ((self.trades['exit_time'] - self.trades['entry_time']).dt.total_seconds() / 86400).mean()
        
        return {
            "max_drawdown": round(max_drawdown, 2),
            "avg_hold_length": round(avg_hold_length, 1),
            "total_trades": len(self.trades)
        }
    
    def get_per_symbol_breakdown(self) -> List[Dict[str, Any]]:
        """
        Calculate per-symbol performance.
        
        Returns:
            List of dicts with symbol, num_trades, total_pnl, avg_return_pct
        """
        if len(self.trades) == 0:
            return []
        
        symbol_stats = []
        
        for symbol in self.trades['symbol'].unique():
            symbol_trades = self.trades[self.trades['symbol'] == symbol]
            total_pnl = symbol_trades['pnl'].sum()
            num_trades = len(symbol_trades)
            
            # Win rate for this symbol
            winning = len(symbol_trades[symbol_trades['pnl'] > 0])
            win_rate = (winning / num_trades * 100) if num_trades > 0 else 0.0
            
            # Average return per trade
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
        
        daily_pnl = self.trades.groupby(self.trades['exit_time'].dt.date)['pnl'].sum().reset_index()
        daily_pnl.columns = ['date', 'daily_pnl']
        daily_pnl['cumulative_pnl'] = daily_pnl['daily_pnl'].cumsum()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "daily_pnl": round(row['daily_pnl'], 2),
                "cumulative_pnl": round(row['cumulative_pnl'], 2)
            }
            for _, row in daily_pnl.iterrows()
        ]
    
    def get_equity_curve(self, starting_capital: float = 10000) -> List[Dict[str, Any]]:
        """
        Generate equity curve starting from initial capital.
        
        Args:
            starting_capital: Initial account balance
            
        Returns:
            List of dicts with date, equity
        """
        if len(self.trades) == 0:
            return [{"date": pd.Timestamp.now().strftime('%Y-%m-%d'), "equity": starting_capital}]
        
        daily_pnl = self.trades.groupby(self.trades['exit_time'].dt.date)['pnl'].sum().reset_index()
        daily_pnl.columns = ['date', 'pnl']
        daily_pnl['equity'] = starting_capital + daily_pnl['pnl'].cumsum()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "equity": round(row['equity'], 2)
            }
            for _, row in daily_pnl.iterrows()
        ]
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when no trades exist"""
        return {
            "summary": {
                "total_pnl": 0.0,
                "avg_monthly_return": 0.0,
                "sharpe_ratio": 0.0,
                "expectancy": 0.0
            },
            "win_loss": {
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0
            },
            "risk": {
                "max_drawdown": 0.0,
                "avg_hold_length": 0.0,
                "total_trades": 0
            },
            "per_symbol": [],
            "timeseries": [],
            "pnl_series": []
        }


def sanitize_for_json(obj):
    """Recursively sanitize data structure for JSON serialization"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, (np.integer, np.floating)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return 0.0
        return val
    else:
        return obj
