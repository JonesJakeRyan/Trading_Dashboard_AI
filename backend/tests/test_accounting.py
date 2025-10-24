"""
Unit tests for average-cost accounting engine.
Tests various scenarios including partial fills, flips, and options.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.accounting import AverageCostEngine, Position

# Test timezone
EASTERN_TZ = 'America/New_York'


def create_fill(symbol, side, qty, price, time_offset_hours=0, asset_type='equity', multiplier=1.0):
    """Helper to create a fill record."""
    base_time = pd.Timestamp('2025-01-15 09:30:00', tz=EASTERN_TZ)
    filled_time = base_time + timedelta(hours=time_offset_hours)
    
    return {
        'asset_type': asset_type,
        'symbol': symbol,
        'underlying': symbol.split('|')[0] if '|' in symbol else symbol,
        'side': side,
        'qty': qty,
        'price': price,
        'filled_time': filled_time,
        'multiplier': multiplier
    }


class TestAverageCostEngine:
    """Test suite for AverageCostEngine."""
    
    def test_simple_long_round_trip(self):
        """Test basic long position: buy → sell → flat."""
        fills = pd.DataFrame([
            create_fill('AAPL', 'buy', 100, 150.00, 0),
            create_fill('AAPL', 'sell', 100, 155.00, 1)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        trade = trades.iloc[0]
        
        assert trade['symbol'] == 'AAPL'
        assert trade['direction'] == 'long'
        assert trade['qty_closed'] == 100.0
        assert trade['avg_entry'] == 150.00
        assert trade['avg_exit'] == 155.00
        assert trade['pnl'] == 500.00  # (155 - 150) * 100
    
    def test_simple_short_round_trip(self):
        """Test basic short position: short → cover → flat."""
        fills = pd.DataFrame([
            create_fill('TSLA', 'short', 50, 200.00, 0),
            create_fill('TSLA', 'cover', 50, 195.00, 1)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        trade = trades.iloc[0]
        
        assert trade['symbol'] == 'TSLA'
        assert trade['direction'] == 'short'
        assert trade['qty_closed'] == 50.0
        assert trade['avg_entry'] == 200.00
        assert trade['avg_exit'] == 195.00
        assert trade['pnl'] == 250.00  # (200 - 195) * 50
    
    def test_multiple_entries_average_cost(self):
        """Test average cost calculation with multiple entries."""
        fills = pd.DataFrame([
            create_fill('MSFT', 'buy', 100, 300.00, 0),
            create_fill('MSFT', 'buy', 50, 310.00, 1),
            create_fill('MSFT', 'sell', 150, 320.00, 2)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        trade = trades.iloc[0]
        
        # Average entry: (100*300 + 50*310) / 150 = 303.33
        expected_avg_entry = (100 * 300 + 50 * 310) / 150
        assert abs(trade['avg_entry'] - expected_avg_entry) < 0.01
        
        # P&L: (320 - 303.33) * 150 = 2500
        expected_pnl = (320 - expected_avg_entry) * 150
        assert abs(trade['pnl'] - expected_pnl) < 0.01
    
    def test_partial_closes(self):
        """Test partial position closes creating multiple trades."""
        fills = pd.DataFrame([
            create_fill('GOOGL', 'buy', 100, 140.00, 0),
            create_fill('GOOGL', 'sell', 60, 145.00, 1),
            create_fill('GOOGL', 'sell', 40, 150.00, 2)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        # Should create 2 trades (one for each partial close)
        assert len(trades) == 2
        
        # First partial close
        trade1 = trades.iloc[0]
        assert trade1['qty_closed'] == 60.0
        assert trade1['pnl'] == (145 - 140) * 60  # 300
        
        # Second partial close
        trade2 = trades.iloc[1]
        assert trade2['qty_closed'] == 40.0
        assert trade2['pnl'] == (150 - 140) * 40  # 400
    
    def test_flip_long_to_short(self):
        """Test flipping from long to short in single transaction."""
        fills = pd.DataFrame([
            create_fill('NVDA', 'buy', 100, 500.00, 0),
            create_fill('NVDA', 'sell', 150, 510.00, 1),  # Close 100 long, open 50 short
            create_fill('NVDA', 'cover', 50, 505.00, 2)   # Close 50 short
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 2
        
        # First trade: long position
        long_trade = trades.iloc[0]
        assert long_trade['direction'] == 'long'
        assert long_trade['qty_closed'] == 100.0
        assert long_trade['pnl'] == (510 - 500) * 100  # 1000
        
        # Second trade: short position
        short_trade = trades.iloc[1]
        assert short_trade['direction'] == 'short'
        assert short_trade['qty_closed'] == 50.0
        assert short_trade['pnl'] == (510 - 505) * 50  # 250
    
    def test_options_multiplier(self):
        """Test options with 100x multiplier."""
        fills = pd.DataFrame([
            create_fill('AAPL|AAPL250117C180', 'buy', 1, 5.00, 0, 
                       asset_type='option', multiplier=100.0),
            create_fill('AAPL|AAPL250117C180', 'sell', 1, 7.50, 1, 
                       asset_type='option', multiplier=100.0)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        trade = trades.iloc[0]
        
        assert trade['asset_type'] == 'option'
        assert trade['multiplier'] == 100.0
        # P&L: (7.50 - 5.00) * 1 * 100 = 250
        assert trade['pnl'] == 250.00
    
    def test_no_completed_trades_open_position(self):
        """Test that open positions don't create trades."""
        fills = pd.DataFrame([
            create_fill('AMD', 'buy', 100, 120.00, 0),
            create_fill('AMD', 'buy', 50, 125.00, 1)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        # No completed trades (position still open)
        assert len(trades) == 0
        
        # Check open positions
        open_pos = engine.get_open_positions()
        assert len(open_pos) == 1
        assert open_pos.iloc[0]['symbol'] == 'AMD'
        assert open_pos.iloc[0]['pos_qty'] == 150.0
    
    def test_rounding_precision(self):
        """Test quantity and price rounding."""
        fills = pd.DataFrame([
            create_fill('TEST', 'buy', 100.123456, 99.999, 0),
            create_fill('TEST', 'sell', 100.123456, 100.001, 1)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        trade = trades.iloc[0]
        
        # Quantity should be rounded to 4 decimals
        assert trade['qty_closed'] == 100.1235
        
        # Prices should be rounded to 2 decimals
        assert trade['avg_entry'] == 100.00
        assert trade['avg_exit'] == 100.00
    
    def test_same_day_multiple_round_trips(self):
        """Test multiple complete round trips on same day."""
        fills = pd.DataFrame([
            create_fill('SPY', 'buy', 100, 450.00, 0),
            create_fill('SPY', 'sell', 100, 452.00, 1),
            create_fill('SPY', 'buy', 100, 451.00, 2),
            create_fill('SPY', 'sell', 100, 453.00, 3)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 2
        
        # First round trip
        assert trades.iloc[0]['pnl'] == (452 - 450) * 100  # 200
        
        # Second round trip
        assert trades.iloc[1]['pnl'] == (453 - 451) * 100  # 200
    
    def test_volume_weighted_exit_price(self):
        """Test volume-weighted exit price calculation."""
        fills = pd.DataFrame([
            create_fill('QQQ', 'buy', 100, 400.00, 0),
            create_fill('QQQ', 'sell', 40, 405.00, 1),
            create_fill('QQQ', 'sell', 60, 410.00, 2)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        # Should have 2 trades (partial closes)
        assert len(trades) == 2
        
        # Check that each trade has correct exit price
        assert trades.iloc[0]['avg_exit'] == 405.00
        assert trades.iloc[1]['avg_exit'] == 410.00


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_quantity_ignored(self):
        """Test that zero quantity fills are ignored."""
        fills = pd.DataFrame([
            create_fill('TEST', 'buy', 0, 100.00, 0),
            create_fill('TEST', 'buy', 100, 100.00, 1),
            create_fill('TEST', 'sell', 100, 105.00, 2)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        assert len(trades) == 1
        assert trades.iloc[0]['pnl'] == 500.00
    
    def test_negative_price_ignored(self):
        """Test that negative prices are handled."""
        fills = pd.DataFrame([
            create_fill('TEST', 'buy', 100, -10.00, 0),  # Invalid
            create_fill('TEST', 'buy', 100, 100.00, 1),
            create_fill('TEST', 'sell', 100, 105.00, 2)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        # Should only process valid fills
        assert len(trades) == 1
    
    def test_chronological_sorting(self):
        """Test that fills are processed in chronological order."""
        fills = pd.DataFrame([
            create_fill('TEST', 'sell', 100, 105.00, 2),  # Out of order
            create_fill('TEST', 'buy', 100, 100.00, 0)
        ])
        
        engine = AverageCostEngine()
        trades = engine.process_fills(fills)
        
        # Should sort and process correctly
        assert len(trades) == 1
        assert trades.iloc[0]['pnl'] == 500.00


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
