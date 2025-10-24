"""
Position-Based Performance Metrics
Calculates metrics using position accounting (average cost basis).
Implements proper Sharpe ratio and drawdown calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PositionMetrics:
    """
    Calculates performance metrics from position-based trades.
    Uses average cost accounting and proper risk metrics.
    """
    
    def __init__(self, positions_df: pd.DataFrame, starting_equity: float = 10000):
        """
        Initialize with closed positions DataFrame.
        
        Args:
            positions_df: DataFrame of closed positions
            starting_equity: Starting account balance for Sharpe/drawdown
        """
        self.positions = positions_df.copy() if len(positions_df) > 0 else pd.DataFrame()
        self.starting_equity = starting_equity
        
        if len(self.positions) > 0:
            # Ensure datetime columns
            if 'exit_time' in self.positions.columns:
                self.positions['exit_time'] = pd.to_datetime(self.positions['exit_time'])
            if 'entry_time' in self.positions.columns:
                self.positions['entry_time'] = pd.to_datetime(self.positions['entry_time'])
    
    def calculate_all_metrics(self, win_rate_mode: str = 'position') -> Dict[str, Any]:
        """
        Calculate all performance metrics.
        
        Args:
            win_rate_mode: 'position' or 'day' for win rate calculation
            
        Returns:
            Dict with summary, win_loss, risk, per_symbol, timeseries
        """
        if len(self.positions) == 0:
            return self._empty_metrics()
        
        return {
            "summary": self.get_summary_metrics(),
            "win_loss": self.get_win_loss_metrics(mode=win_rate_mode),
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
        if len(self.positions) == 0:
            return {
                "total_pnl": 0.0,
                "avg_monthly_return": 0.0,
                "sharpe_ratio": 0.0,
                "expectancy": 0.0
            }
        
        # Total P&L
        total_pnl = self.positions['realized_pnl'].sum()
        
        # Monthly returns
        self.positions['month'] = self.positions['exit_time'].dt.to_period('M')
        monthly_pnl = self.positions.groupby('month')['realized_pnl'].sum()
        avg_monthly_return = monthly_pnl.mean() if len(monthly_pnl) > 0 else 0.0
        
        # Sharpe Ratio (proper calculation)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Expectancy
        winning_positions = self.positions[self.positions['realized_pnl'] > 0]
        losing_positions = self.positions[self.positions['realized_pnl'] <= 0]
        
        win_rate = len(winning_positions) / len(self.positions) if len(self.positions) > 0 else 0.0
        avg_win = winning_positions['realized_pnl'].mean() if len(winning_positions) > 0 else 0.0
        avg_loss = losing_positions['realized_pnl'].mean() if len(losing_positions) > 0 else 0.0
        
        # Expectancy = (WinRate × AvgWin) + ((1 - WinRate) × AvgLoss)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        return {
            "total_pnl": round(total_pnl, 2),
            "avg_monthly_return": round(avg_monthly_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "expectancy": round(expectancy, 2)
        }
    
    def get_win_loss_metrics(self, mode: str = 'position') -> Dict[str, Any]:
        """
        Calculate win/loss statistics.
        
        Args:
            mode: 'position' for position-based, 'day' for daily win rate
            
        Returns:
            Dict with win_rate, avg_win, avg_loss, profit_factor, mode
        """
        if len(self.positions) == 0:
            return {
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "win_rate_mode": mode
            }
        
        if mode == 'day':
            # Daily win rate
            daily_pnl = self.positions.groupby(self.positions['exit_time'].dt.date)['realized_pnl'].sum()
            winning_days = len(daily_pnl[daily_pnl > 0])
            total_days = len(daily_pnl)
            win_rate = (winning_days / total_days * 100) if total_days > 0 else 0.0
            
            # Still use position-level avg win/loss
            winning_positions = self.positions[self.positions['realized_pnl'] > 0]
            losing_positions = self.positions[self.positions['realized_pnl'] <= 0]
        else:
            # Position win rate
            winning_positions = self.positions[self.positions['realized_pnl'] > 0]
            losing_positions = self.positions[self.positions['realized_pnl'] <= 0]
            win_rate = (len(winning_positions) / len(self.positions) * 100) if len(self.positions) > 0 else 0.0
        
        # Average Win/Loss
        avg_win = winning_positions['realized_pnl'].mean() if len(winning_positions) > 0 else 0.0
        avg_loss = losing_positions['realized_pnl'].mean() if len(losing_positions) > 0 else 0.0
        
        # Profit Factor
        total_profit = winning_positions['realized_pnl'].sum()
        total_loss = abs(losing_positions['realized_pnl'].sum())
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
        
        return {
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "win_rate_mode": mode
        }
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate risk-related metrics with proper drawdown.
        
        Returns:
            Dict with max_drawdown, avg_hold_length, total_positions
        """
        if len(self.positions) == 0:
            return {
                "max_drawdown": 0.0,
                "avg_hold_length": 0.0,
                "total_trades": 0
            }
        
        # Max Drawdown (proper calculation)
        max_drawdown = self._calculate_max_drawdown()
        
        # Average hold length (in days)
        if 'hold_time_days' in self.positions.columns:
            avg_hold_length = self.positions['hold_time_days'].mean()
        else:
            avg_hold_length = ((self.positions['exit_time'] - self.positions['entry_time']).dt.total_seconds() / 86400).mean()
        
        return {
            "max_drawdown": round(max_drawdown, 2),
            "avg_hold_length": round(avg_hold_length, 1),
            "total_trades": len(self.positions)
        }
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio using proper daily returns.
        
        Formula: Sharpe = (mean(daily_return) / std(daily_return)) × √252
        where daily_return = daily_pnl / equity_base
        """
        if len(self.positions) == 0:
            return 0.0
        
        # Get daily P&L
        daily_pnl = self.positions.groupby(self.positions['exit_time'].dt.date)['realized_pnl'].sum()
        
        if len(daily_pnl) < 2:
            return 0.0
        
        # Calculate equity curve
        equity = self.starting_equity + daily_pnl.cumsum()
        
        # Calculate daily returns as percentage
        daily_returns = daily_pnl / equity.shift(1).fillna(self.starting_equity)
        
        # Sharpe ratio
        if daily_returns.std() == 0:
            return 0.0
        
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        
        return sharpe if not np.isnan(sharpe) and not np.isinf(sharpe) else 0.0
    
    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown as percentage.
        
        Formula: drawdown = (equity / cummax(equity) - 1) × 100
        Returns value between 0% and -100%
        """
        if len(self.positions) == 0:
            return 0.0
        
        # Build daily equity curve
        daily_pnl = self.positions.groupby(self.positions['exit_time'].dt.date)['realized_pnl'].sum()
        equity = self.starting_equity + daily_pnl.cumsum()
        
        # Calculate running maximum
        running_max = equity.expanding().max()
        
        # Calculate drawdown as percentage
        drawdown = ((equity / running_max) - 1) * 100
        
        # Max drawdown is the minimum (most negative) value
        max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0.0
        
        return max_dd if not np.isnan(max_dd) and not np.isinf(max_dd) else 0.0
    
    def get_per_symbol_breakdown(self) -> List[Dict[str, Any]]:
        """
        Calculate per-symbol performance.
        
        Returns:
            List of dicts with symbol, num_positions, total_pnl, avg_pnl, win_rate
        """
        if len(self.positions) == 0:
            return []
        
        symbol_stats = []
        
        for symbol in self.positions['symbol'].unique():
            symbol_positions = self.positions[self.positions['symbol'] == symbol]
            total_pnl = symbol_positions['realized_pnl'].sum()
            num_positions = len(symbol_positions)
            
            # Win rate for this symbol
            winning = len(symbol_positions[symbol_positions['realized_pnl'] > 0])
            win_rate = (winning / num_positions * 100) if num_positions > 0 else 0.0
            
            # Average P&L per position
            avg_pnl = total_pnl / num_positions if num_positions > 0 else 0.0
            
            symbol_stats.append({
                "symbol": symbol,
                "num_trades": num_positions,
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
        if len(self.positions) == 0:
            return []
        
        daily_pnl = self.positions.groupby(self.positions['exit_time'].dt.date)['realized_pnl'].sum().reset_index()
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
    
    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """
        Generate equity curve starting from initial capital.
        
        Returns:
            List of dicts with date, equity
        """
        if len(self.positions) == 0:
            return [{"date": pd.Timestamp.now().strftime('%Y-%m-%d'), "equity": self.starting_equity}]
        
        daily_pnl = self.positions.groupby(self.positions['exit_time'].dt.date)['realized_pnl'].sum().reset_index()
        daily_pnl.columns = ['date', 'pnl']
        daily_pnl['equity'] = self.starting_equity + daily_pnl['pnl'].cumsum()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "equity": round(row['equity'], 2)
            }
            for _, row in daily_pnl.iterrows()
        ]
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when no positions exist"""
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
                "profit_factor": 0.0,
                "win_rate_mode": "position"
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
