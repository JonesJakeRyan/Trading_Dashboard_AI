"""
Unit tests for FIFO matching engine.

Tests cover:
- Long positions (BUY → SELL)
- Short positions (SELL → BUY)
- Partial fills
- Multiple lots
- Mixed long/short
- Edge cases
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.services.fifo_engine import FIFOEngine
from app.models.trade import NormalizedTrade


@pytest.mark.unit
class TestFIFOLongPositions:
    """Tests for long position (BUY → SELL) matching"""
    
    def test_simple_long_profit(self):
        """Test simple long position with profit"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("100"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        assert lot.symbol == "AAPL"
        assert lot.position_type == "LONG"
        assert lot.open_quantity == Decimal("100")
        assert lot.open_price == Decimal("150.00")
        assert lot.close_price == Decimal("160.00")
        # P&L = (160 - 150) * 100 = 1000
        assert lot.realized_pnl == Decimal("1000.00")
    
    def test_simple_long_loss(self):
        """Test simple long position with loss"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="BUY",
                quantity=Decimal("50"),
                price=Decimal("200.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="SELL",
                quantity=Decimal("50"),
                price=Decimal("180.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        # P&L = (180 - 200) * 50 = -1000
        assert lot.realized_pnl == Decimal("-1000.00")
    
    def test_partial_close_long(self):
        """Test partial close of long position"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("60"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        assert lot.open_quantity == Decimal("60")
        # P&L = (160 - 150) * 60 = 600
        assert lot.realized_pnl == Decimal("600.00")
        
        # Check open positions
        open_pos = engine.get_open_positions()
        assert "AAPL" in open_pos
        assert open_pos["AAPL"]["quantity"] == Decimal("40")


@pytest.mark.unit
class TestFIFOShortPositions:
    """Tests for short position (SELL → BUY) matching"""
    
    def test_simple_short_profit(self):
        """Test simple short position with profit"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("100"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        assert lot.position_type == "SHORT"
        # P&L = (160 - 150) * 100 = 1000 (profit when buy back lower)
        assert lot.realized_pnl == Decimal("1000.00")
    
    def test_simple_short_loss(self):
        """Test simple short position with loss"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="SELL",
                quantity=Decimal("50"),
                price=Decimal("180.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="BUY",
                quantity=Decimal("50"),
                price=Decimal("200.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        # P&L = (180 - 200) * 50 = -1000 (loss when buy back higher)
        assert lot.realized_pnl == Decimal("-1000.00")


@pytest.mark.unit
class TestFIFOMultipleLots:
    """Tests for FIFO matching with multiple lots"""
    
    def test_fifo_order_long(self):
        """Test that FIFO order is respected for long positions"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("155.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("150"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 2
        
        # First lot should match first BUY (FIFO)
        lot1 = closed_lots[0]
        assert lot1.open_price == Decimal("150.00")
        assert lot1.open_quantity == Decimal("100")
        # P&L = (160 - 150) * 100 = 1000
        assert lot1.realized_pnl == Decimal("1000.00")
        
        # Second lot should match partial second BUY
        lot2 = closed_lots[1]
        assert lot2.open_price == Decimal("155.00")
        assert lot2.open_quantity == Decimal("50")
        # P&L = (160 - 155) * 50 = 250
        assert lot2.realized_pnl == Decimal("250.00")
        
        # Check remaining open position
        open_pos = engine.get_open_positions()
        assert open_pos["AAPL"]["quantity"] == Decimal("50")
        assert open_pos["AAPL"]["average_price"] == Decimal("155.00")
    
    def test_multiple_symbols(self):
        """Test FIFO matching with multiple symbols"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="BUY",
                quantity=Decimal("50"),
                price=Decimal("200.00"),
                executed_at=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("100"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="TSLA",
                side="SELL",
                quantity=Decimal("50"),
                price=Decimal("210.00"),
                executed_at=datetime(2024, 1, 2, 11, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 2
        
        # Check AAPL lot
        aapl_lot = [lot for lot in closed_lots if lot.symbol == "AAPL"][0]
        assert aapl_lot.realized_pnl == Decimal("1000.00")
        
        # Check TSLA lot
        tsla_lot = [lot for lot in closed_lots if lot.symbol == "TSLA"][0]
        assert tsla_lot.realized_pnl == Decimal("500.00")


@pytest.mark.unit
class TestFIFOEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_fractional_shares(self):
        """Test FIFO with fractional shares"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("10.5"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("10.5"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        # P&L = (160 - 150) * 10.5 = 105.00
        assert lot.realized_pnl == Decimal("105.00")
    
    def test_rounding_accuracy(self):
        """Test that P&L rounding is accurate to cents"""
        engine = FIFOEngine()
        
        trades = [
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("3"),
                price=Decimal("100.33"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("3"),
                price=Decimal("100.67"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 1
        lot = closed_lots[0]
        # P&L = (100.67 - 100.33) * 3 = 0.34 * 3 = 1.02
        assert lot.realized_pnl == Decimal("1.02")
    
    def test_mixed_long_short_same_symbol(self):
        """Test mixed long and short positions on same symbol"""
        engine = FIFOEngine()
        
        trades = [
            # Open long
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                price=Decimal("150.00"),
                executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            # Close long
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("100"),
                price=Decimal("160.00"),
                executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            # Open short
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="SELL",
                quantity=Decimal("50"),
                price=Decimal("165.00"),
                executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
            # Close short
            NormalizedTrade(
                id=uuid.uuid4(),
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("50"),
                price=Decimal("155.00"),
                executed_at=datetime(2024, 1, 4, 10, 0, tzinfo=timezone.utc),
                account_id=None,
                notes=None
            ),
        ]
        
        closed_lots = engine.process_trades(trades)
        
        assert len(closed_lots) == 2
        
        # First lot: LONG
        long_lot = closed_lots[0]
        assert long_lot.position_type == "LONG"
        assert long_lot.realized_pnl == Decimal("1000.00")
        
        # Second lot: SHORT
        short_lot = closed_lots[1]
        assert short_lot.position_type == "SHORT"
        assert short_lot.realized_pnl == Decimal("500.00")
