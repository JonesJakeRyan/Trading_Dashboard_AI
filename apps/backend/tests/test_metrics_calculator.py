"""
Unit tests for metrics calculator.

Tests cover:
- Daily P&L series generation
- Gap filling for continuous charts
- Aggregate metrics calculation
- Timezone handling (EST)
"""
import pytest
from decimal import Decimal
from datetime import datetime, date, timezone
import uuid
import pytz

from app.services.metrics_calculator import MetricsCalculator
from app.models.trade import ClosedLot

EST = pytz.timezone('America/New_York')


@pytest.mark.unit
class TestDailyPnLSeries:
    """Tests for daily P&L series generation"""
    
    def test_simple_daily_pnl(self):
        """Test basic daily P&L calculation"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=False)
        
        assert len(daily_pnl) == 1
        assert daily_pnl[0].date == date(2024, 1, 2)
        assert daily_pnl[0].daily_pnl == Decimal("1000.00")
        assert daily_pnl[0].cumulative_pnl == Decimal("1000.00")
        assert daily_pnl[0].lots_closed == 1
    
    def test_multiple_lots_same_day(self):
        """Test multiple lots closed on same day"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=datetime(2024, 1, 1, 11, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("210.00"),
                close_executed_at=datetime(2024, 1, 2, 11, 0, tzinfo=EST),
                realized_pnl=Decimal("500.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=False)
        
        assert len(daily_pnl) == 1
        assert daily_pnl[0].date == date(2024, 1, 2)
        assert daily_pnl[0].daily_pnl == Decimal("1500.00")
        assert daily_pnl[0].cumulative_pnl == Decimal("1500.00")
        assert daily_pnl[0].lots_closed == 2
    
    def test_gap_filling(self):
        """Test gap filling for continuous chart"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("210.00"),
                close_executed_at=datetime(2024, 1, 5, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("500.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=True)
        
        # Should have 4 days: Jan 2, 3, 4, 5
        assert len(daily_pnl) == 4
        
        # Jan 2: 1000
        assert daily_pnl[0].date == date(2024, 1, 2)
        assert daily_pnl[0].daily_pnl == Decimal("1000.00")
        assert daily_pnl[0].cumulative_pnl == Decimal("1000.00")
        
        # Jan 3: 0 (gap filled)
        assert daily_pnl[1].date == date(2024, 1, 3)
        assert daily_pnl[1].daily_pnl == Decimal("0.00")
        assert daily_pnl[1].cumulative_pnl == Decimal("1000.00")
        
        # Jan 4: 0 (gap filled)
        assert daily_pnl[2].date == date(2024, 1, 4)
        assert daily_pnl[2].daily_pnl == Decimal("0.00")
        assert daily_pnl[2].cumulative_pnl == Decimal("1000.00")
        
        # Jan 5: 500
        assert daily_pnl[3].date == date(2024, 1, 5)
        assert daily_pnl[3].daily_pnl == Decimal("500.00")
        assert daily_pnl[3].cumulative_pnl == Decimal("1500.00")
    
    def test_cumulative_pnl(self):
        """Test cumulative P&L calculation"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("180.00"),
                close_executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("-1000.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots, fill_gaps=False)
        
        assert len(daily_pnl) == 2
        
        # Day 1: +1000
        assert daily_pnl[0].cumulative_pnl == Decimal("1000.00")
        
        # Day 2: +1000 - 1000 = 0
        assert daily_pnl[1].cumulative_pnl == Decimal("0.00")


@pytest.mark.unit
class TestAggregateMetrics:
    """Tests for aggregate metrics calculation"""
    
    def test_basic_aggregates(self):
        """Test basic aggregate calculation"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("180.00"),
                close_executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("-1000.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots)
        aggregates = calculator.calculate_aggregates(closed_lots, daily_pnl)
        
        assert aggregates.total_realized_pnl == Decimal("0.00")
        assert aggregates.total_lots_closed == 2
        assert aggregates.winning_lots == 1
        assert aggregates.losing_lots == 1
        assert aggregates.total_gains == Decimal("1000.00")
        assert aggregates.total_losses == Decimal("-1000.00")
        assert aggregates.win_rate == Decimal("0.5000")
        assert aggregates.profit_factor == Decimal("1.00")
    
    def test_best_worst_symbol(self):
        """Test best/worst symbol calculation"""
        calculator = MetricsCalculator()
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=datetime(2024, 1, 1, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=datetime(2024, 1, 2, 10, 0, tzinfo=EST),
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("180.00"),
                close_executed_at=datetime(2024, 1, 3, 10, 0, tzinfo=EST),
                realized_pnl=Decimal("-1000.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots)
        aggregates = calculator.calculate_aggregates(closed_lots, daily_pnl)
        
        assert aggregates.best_symbol == "AAPL"
        assert aggregates.best_symbol_pnl == Decimal("1000.00")
        assert aggregates.worst_symbol == "TSLA"
        assert aggregates.worst_symbol_pnl == Decimal("-1000.00")
    
    def test_best_worst_weekday(self):
        """Test best/worst weekday calculation"""
        calculator = MetricsCalculator()
        
        # Monday Jan 1, 2024
        monday = datetime(2024, 1, 1, 10, 0, tzinfo=EST)
        # Tuesday Jan 2, 2024
        tuesday = datetime(2024, 1, 2, 10, 0, tzinfo=EST)
        
        closed_lots = [
            ClosedLot(
                id=uuid.uuid4(),
                symbol="AAPL",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("100"),
                open_price=Decimal("150.00"),
                open_executed_at=monday,
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("100"),
                close_price=Decimal("160.00"),
                close_executed_at=monday,
                realized_pnl=Decimal("1000.00"),
                account_id=None
            ),
            ClosedLot(
                id=uuid.uuid4(),
                symbol="TSLA",
                position_type="LONG",
                open_trade_id=uuid.uuid4(),
                open_quantity=Decimal("50"),
                open_price=Decimal("200.00"),
                open_executed_at=tuesday,
                close_trade_id=uuid.uuid4(),
                close_quantity=Decimal("50"),
                close_price=Decimal("180.00"),
                close_executed_at=tuesday,
                realized_pnl=Decimal("-1000.00"),
                account_id=None
            ),
        ]
        
        daily_pnl = calculator.generate_daily_pnl_series(closed_lots)
        aggregates = calculator.calculate_aggregates(closed_lots, daily_pnl)
        
        assert aggregates.best_weekday == "Monday"
        assert aggregates.best_weekday_pnl == Decimal("1000.00")
        assert aggregates.worst_weekday == "Tuesday"
        assert aggregates.worst_weekday_pnl == Decimal("-1000.00")
