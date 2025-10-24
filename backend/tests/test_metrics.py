"""
Unit tests for metrics calculation.
Tests win rate, expectancy, Sharpe ratio, drawdown, etc.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.metrics import MetricsCalculator

EASTERN_TZ = 'America/New_York'


def create_trade(symbol, pnl, entry_offset_days=0, close_offset_days=1):
    """Helper to create a trade record."""
    base_time = pd.Timestamp('2025-01-15 09:30:00', tz=EASTERN_TZ)
    entry_time = base_time + timedelta(days=entry_offset_days)
    close_time = base_time + timedelta(days=close_offset_days)
    
    return {
        'symbol': symbol,
        'underlying': symbol,
        'asset_type': 'equity',
        'direction': 'long',
        'qty_closed': 100.0,
        'avg_entry': 100.0,
        'avg_exit': 100.0 + pnl,
        'entry_time': entry_time,
        'close_time': close_time,
        'pnl': pnl,
        'multiplier': 1.0
    }


class TestMetricsCalculator:
    """Test suite for MetricsCalculator."""
    
    def test_total_pnl(self):
        """Test total P&L calculation."""
        trades = pd.DataFrame([
            create_trade('AAPL', 500.0),
            create_trade('TSLA', -200.0),
            create_trade('MSFT', 300.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_summary_metrics()
        
        assert metrics['total_pnl'] == 600.0
    
    def test_win_rate(self):
        """Test win rate calculation."""
        trades = pd.DataFrame([
            create_trade('A', 100.0),
            create_trade('B', 200.0),
            create_trade('C', -50.0),
            create_trade('D', 150.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_win_loss_metrics()
        
        # 3 winners out of 4 = 75%
        assert metrics['win_rate'] == 75.0
    
    def test_avg_win_avg_loss(self):
        """Test average win and average loss."""
        trades = pd.DataFrame([
            create_trade('A', 100.0),
            create_trade('B', 200.0),
            create_trade('C', -50.0),
            create_trade('D', -100.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_win_loss_metrics()
        
        # Avg win: (100 + 200) / 2 = 150
        assert metrics['avg_win'] == 150.0
        
        # Avg loss: (-50 + -100) / 2 = -75
        assert metrics['avg_loss'] == -75.0
    
    def test_expectancy(self):
        """Test expectancy calculation."""
        trades = pd.DataFrame([
            create_trade('A', 100.0),
            create_trade('B', 200.0),
            create_trade('C', -50.0),
            create_trade('D', -100.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_summary_metrics()
        
        # Win rate: 50% (2 out of 4)
        # Avg win: 150, Avg loss: -75
        # Expectancy: 0.5 * 150 + 0.5 * (-75) = 37.5
        assert abs(metrics['expectancy'] - 37.5) < 0.01
    
    def test_profit_factor(self):
        """Test profit factor calculation."""
        trades = pd.DataFrame([
            create_trade('A', 300.0),
            create_trade('B', 200.0),
            create_trade('C', -100.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_win_loss_metrics()
        
        # Profit factor: 500 / 100 = 5.0
        assert metrics['profit_factor'] == 5.0
    
    def test_max_drawdown(self):
        """Test maximum drawdown calculation."""
        # Create trades that produce a drawdown
        trades = pd.DataFrame([
            create_trade('A', 1000.0, 0, 1),   # Equity: 11000
            create_trade('B', -500.0, 1, 2),   # Equity: 10500
            create_trade('C', -300.0, 2, 3),   # Equity: 10200
            create_trade('D', 200.0, 3, 4)     # Equity: 10400
        ])
        
        calc = MetricsCalculator(trades, starting_equity=10000)
        metrics = calc.get_risk_metrics()
        
        # Max equity: 11000
        # Min equity after peak: 10200
        # Drawdown: (10200 / 11000 - 1) * 100 = -7.27%
        expected_dd = (10200 / 11000 - 1) * 100
        assert abs(metrics['max_drawdown_pct'] - expected_dd) < 0.1
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        # Create consistent daily returns
        trades = []
        for i in range(20):
            trades.append(create_trade('TEST', 100.0, i, i))
        
        trades_df = pd.DataFrame(trades)
        
        calc = MetricsCalculator(trades_df, starting_equity=10000)
        metrics = calc.get_summary_metrics()
        
        # Should have a positive Sharpe ratio
        assert metrics['sharpe_ratio'] > 0
    
    def test_avg_hold_days(self):
        """Test average hold length calculation."""
        trades = pd.DataFrame([
            create_trade('A', 100.0, 0, 1),   # 1 day
            create_trade('B', 200.0, 0, 3),   # 3 days
            create_trade('C', 150.0, 0, 2)    # 2 days
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_risk_metrics()
        
        # Avg: (1 + 3 + 2) / 3 = 2 days
        assert abs(metrics['avg_hold_days'] - 2.0) < 0.01
    
    def test_total_trades(self):
        """Test total trades count."""
        trades = pd.DataFrame([
            create_trade('A', 100.0),
            create_trade('B', -50.0),
            create_trade('C', 200.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_risk_metrics()
        
        assert metrics['total_trades'] == 3
    
    def test_daily_aggregation(self):
        """Test daily P&L aggregation."""
        # Multiple trades on same day
        base_time = pd.Timestamp('2025-01-15 09:30:00', tz=EASTERN_TZ)
        
        trades = pd.DataFrame([
            {
                'symbol': 'A',
                'underlying': 'A',
                'asset_type': 'equity',
                'direction': 'long',
                'qty_closed': 100.0,
                'avg_entry': 100.0,
                'avg_exit': 105.0,
                'entry_time': base_time,
                'close_time': base_time + timedelta(hours=1),
                'pnl': 500.0,
                'multiplier': 1.0
            },
            {
                'symbol': 'B',
                'underlying': 'B',
                'asset_type': 'equity',
                'direction': 'long',
                'qty_closed': 100.0,
                'avg_entry': 100.0,
                'avg_exit': 103.0,
                'entry_time': base_time,
                'close_time': base_time + timedelta(hours=2),
                'pnl': 300.0,
                'multiplier': 1.0
            }
        ])
        
        calc = MetricsCalculator(trades)
        daily_pnl = calc._get_daily_pnl()
        
        # Should aggregate to single day
        assert len(daily_pnl) == 1
        assert daily_pnl.iloc[0] == 800.0
    
    def test_timeseries_output(self):
        """Test timeseries output format."""
        trades = pd.DataFrame([
            create_trade('A', 100.0, 0, 1),
            create_trade('B', 200.0, 1, 2)
        ])
        
        calc = MetricsCalculator(trades, starting_equity=10000)
        timeseries = calc.get_timeseries()
        
        assert len(timeseries) == 2
        
        # First day
        assert timeseries[0]['daily_pnl'] == 100.0
        assert timeseries[0]['equity'] == 10100.0
        
        # Second day
        assert timeseries[1]['daily_pnl'] == 200.0
        assert timeseries[1]['equity'] == 10300.0
    
    def test_empty_trades(self):
        """Test metrics with no trades."""
        trades = pd.DataFrame()
        
        calc = MetricsCalculator(trades)
        metrics = calc.calculate_all_metrics()
        
        assert metrics['summary']['total_pnl'] == 0.0
        assert metrics['win_loss']['win_rate'] == 0.0
        assert metrics['risk']['total_trades'] == 0
        assert len(metrics['timeseries']) == 0
    
    def test_all_winners(self):
        """Test metrics with 100% win rate."""
        trades = pd.DataFrame([
            create_trade('A', 100.0),
            create_trade('B', 200.0),
            create_trade('C', 150.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_win_loss_metrics()
        
        assert metrics['win_rate'] == 100.0
        assert metrics['avg_win'] == 150.0
        assert metrics['avg_loss'] == 0.0  # No losers
    
    def test_all_losers(self):
        """Test metrics with 0% win rate."""
        trades = pd.DataFrame([
            create_trade('A', -100.0),
            create_trade('B', -200.0),
            create_trade('C', -150.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_win_loss_metrics()
        
        assert metrics['win_rate'] == 0.0
        assert metrics['avg_win'] == 0.0  # No winners
        assert metrics['avg_loss'] == -150.0
    
    def test_nan_safe_sharpe(self):
        """Test Sharpe ratio with insufficient data."""
        # Single trade - not enough for std calculation
        trades = pd.DataFrame([
            create_trade('A', 100.0)
        ])
        
        calc = MetricsCalculator(trades)
        metrics = calc.get_summary_metrics()
        
        # Should return 0.0 instead of NaN
        assert metrics['sharpe_ratio'] == 0.0
    
    def test_drawdown_never_below_minus_100(self):
        """Test that drawdown never goes below -100%."""
        # Create extreme loss scenario
        trades = pd.DataFrame([
            create_trade('A', -15000.0)  # Lose more than starting equity
        ])
        
        calc = MetricsCalculator(trades, starting_equity=10000)
        metrics = calc.get_risk_metrics()
        
        # Drawdown should be capped at -100%
        assert metrics['max_drawdown_pct'] >= -100.0


class TestTimezoneHandling:
    """Test timezone-aware date operations."""
    
    def test_eastern_timezone_aggregation(self):
        """Test that daily aggregation uses Eastern timezone."""
        # Create trades at different times but same Eastern date
        base_time = pd.Timestamp('2025-01-15 23:00:00', tz='UTC')
        
        trades = pd.DataFrame([
            {
                'symbol': 'A',
                'underlying': 'A',
                'asset_type': 'equity',
                'direction': 'long',
                'qty_closed': 100.0,
                'avg_entry': 100.0,
                'avg_exit': 105.0,
                'entry_time': base_time,
                'close_time': base_time,  # 6 PM Eastern (same day)
                'pnl': 500.0,
                'multiplier': 1.0
            },
            {
                'symbol': 'B',
                'underlying': 'B',
                'asset_type': 'equity',
                'direction': 'long',
                'qty_closed': 100.0,
                'avg_entry': 100.0,
                'avg_exit': 103.0,
                'entry_time': base_time + timedelta(hours=2),
                'close_time': base_time + timedelta(hours=2),  # 8 PM Eastern (same day)
                'pnl': 300.0,
                'multiplier': 1.0
            }
        ])
        
        calc = MetricsCalculator(trades)
        daily_pnl = calc._get_daily_pnl()
        
        # Should aggregate to single Eastern date
        assert len(daily_pnl) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
