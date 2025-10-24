# Trading Performance Dashboard API - Refactored v2.0

## 🎯 Overview

This is a **trade-level performance analytics engine** that uses FIFO (First In First Out) matching to convert order-level CSV data into complete trade pairs and calculate accurate performance metrics.

### Key Features

- ✅ **FIFO Trade Matching**: Chronologically matches buy/sell orders per symbol
- ✅ **Partial Fill Support**: Handles partial position closes with weighted average costs
- ✅ **Multi-Symbol Tracking**: Maintains separate position queues for each symbol
- ✅ **Realized P&L Only**: Excludes open positions from all metrics
- ✅ **Multi-Broker Support**: Parses CSV from Webull, TD Ameritrade, Interactive Brokers, etc.
- ✅ **Comprehensive Metrics**: Expectancy, Sharpe, Profit Factor, Max Drawdown, and more

---

## 📊 Architecture

```
backend/
├── main_refactored.py          # New FastAPI application
├── services/
│   ├── trade_parser.py          # FIFO trade matching logic
│   └── performance_metrics.py   # Metric calculations
├── tests/
│   └── test_metrics.py          # Unit & integration tests
├── requirements.txt
└── Dockerfile
```

### Service Modules

#### `trade_parser.py`
- **TradeParser**: Matches orders into complete trades using FIFO
- **parse_csv()**: Standardizes CSV from various broker formats
- Handles: Long/short positions, partial fills, multiple symbols

#### `performance_metrics.py`
- **PerformanceMetrics**: Calculates all metrics from trade DataFrame
- Metrics: Total P&L, Win Rate, Expectancy, Sharpe, Profit Factor, Max Drawdown
- Time series: Daily P&L, Equity curve

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Tests

```bash
pytest tests/test_metrics.py -v
```

### 3. Start Server

```bash
# Using the refactored version
python -m uvicorn main_refactored:app --reload --port 8002

# Or using the original (for comparison)
python -m uvicorn main:app --reload --port 8002
```

### 4. Access API

- **API**: http://localhost:8002
- **Docs**: http://localhost:8002/docs
- **Health**: http://localhost:8002/api/health
- **Metrics Documentation**: http://localhost:8002/api/docs/metrics

---

## 📈 Metric Formulas

### Summary Metrics

**Total P&L**
```python
total_pnl = trades['pnl'].sum()
```

**Expectancy** (Expected value per trade)
```python
expectancy = (win_rate × avg_win) + ((1 - win_rate) × avg_loss)
```

**Sharpe Ratio** (Risk-adjusted return, annualized)
```python
daily_returns = trades.groupby(date)['pnl'].sum()
sharpe_ratio = (daily_returns.mean() / daily_returns.std()) × √252
```

**Average Monthly Return**
```python
monthly_pnl = trades.groupby(month)['pnl'].sum()
avg_monthly_return = monthly_pnl.mean()
```

### Win/Loss Metrics

**Win Rate**
```python
win_rate = (winning_trades / total_trades) × 100
```

**Profit Factor**
```python
profit_factor = gross_profit / gross_loss
```

**Average Win / Loss**
```python
avg_win = winning_trades['pnl'].mean()
avg_loss = losing_trades['pnl'].mean()  # Negative
```

### Risk Metrics

**Max Drawdown**
```python
equity_curve = daily_pnl.cumsum()
drawdown = (equity_curve / equity_curve.cummax() - 1) × 100
max_drawdown = abs(drawdown.min())
```

**Average Hold Length**
```python
avg_hold_length = (exit_time - entry_time).mean()  # In days
```

---

## 🔄 Trade Matching Logic

### FIFO Algorithm

1. **Sort orders** chronologically by symbol and date
2. **For each order**:
   - If BUY/SHORT → Add to open positions queue
   - If SELL/COVER → Match against oldest position (FIFO)
3. **Calculate P&L** for each matched pair:
   - Long: `(exit_price - entry_price) × qty - fees`
   - Short: `(entry_price - exit_price) × qty - fees`
4. **Handle partial fills**:
   - Close full position or partial quantity
   - Allocate fees proportionally
   - Update remaining position

### Example

```
Orders:
1. BUY  100 AAPL @ $150  (Jan 1)
2. BUY   50 AAPL @ $152  (Jan 2)
3. SELL  75 AAPL @ $155  (Jan 3)

Trades Created:
1. LONG 100 AAPL: $150 → $155 (fully closed)
2. LONG  25 AAPL: $152 → $155 (partial close)

Open Positions:
- LONG 25 AAPL @ $152 (remaining)
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/test_metrics.py -v
```

### Test Coverage

- ✅ Simple long/short trades
- ✅ Partial fills with FIFO
- ✅ Multiple symbols
- ✅ Sell without buy (creates short)
- ✅ All metric calculations
- ✅ Empty trade handling
- ✅ Full integration workflow

### Sample Test Output
```
tests/test_metrics.py::TestTradeParser::test_simple_long_trade PASSED
tests/test_metrics.py::TestTradeParser::test_partial_fill_fifo PASSED
tests/test_metrics.py::TestPerformanceMetrics::test_expectancy PASSED
tests/test_metrics.py::TestPerformanceMetrics::test_profit_factor PASSED
tests/test_metrics.py::TestIntegration::test_full_workflow PASSED
```

---

## 📦 API Response Schema

```json
{
  "success": true,
  "filename": "Webull_Orders_Records.csv",
  "total_orders": 1106,
  "completed_trades": 553,
  "open_positions": 0,
  "metrics": {
    "summary": {
      "total_pnl": 1328.78,
      "avg_monthly_return": 132.88,
      "sharpe_ratio": 2.05,
      "expectancy": 6.07
    },
    "win_loss": {
      "win_rate": 63.9,
      "avg_win": 28.99,
      "avg_loss": -34.55,
      "profit_factor": 1.49
    },
    "risk": {
      "max_drawdown": 5.23,
      "avg_hold_length": 1.2,
      "total_trades": 553
    },
    "per_symbol": [
      {
        "symbol": "TSLA",
        "num_trades": 120,
        "total_pnl": 450.32,
        "avg_pnl": 3.75,
        "win_rate": 65.0
      }
    ],
    "timeseries": [
      {"date": "2025-01-02", "equity": 10105.50},
      {"date": "2025-01-03", "equity": 10112.30}
    ]
  }
}
```

---

## 🔧 Migration from Old Version

### To switch to the refactored version:

1. **Stop old server**:
   ```bash
   # Kill process on port 8002
   lsof -ti :8002 | xargs kill
   ```

2. **Start refactored server**:
   ```bash
   uvicorn main_refactored:app --reload --port 8002
   ```

3. **Frontend changes**: None required! API response format is compatible.

### Key Differences

| Feature | Old Version | New Version |
|---------|------------|-------------|
| Trade Matching | Per-order P&L | FIFO trade pairs |
| Open Positions | Included (0 P&L) | Excluded |
| Expectancy | Incorrect formula | Fixed formula |
| Architecture | Monolithic | Modular services |
| Testing | None | Comprehensive |
| Partial Fills | Basic | Weighted average |

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t trading-dashboard-api .

# Run container
docker run -p 8002:8000 trading-dashboard-api
```

---

## 📝 CSV Format Requirements

### Required Columns
- **Date/Time**: `Date`, `Filled Time`, `datetime`, etc.
- **Symbol**: `Symbol`, `Ticker`
- **Side**: `Side`, `Action` (buy/sell/short/cover)
- **Quantity**: `Quantity`, `Filled`, `Qty`
- **Price**: `Price`, `Avg Price`

### Optional Columns
- **Fees**: `Fees`, `Commission` (defaults to 0)
- **Status**: `Status` (filters for 'Filled' only)

### Supported Brokers
- Webull
- TD Ameritrade
- Interactive Brokers
- Generic CSV with standard columns

---

## 🎓 Performance Validation

All metrics are validated against:
- ✅ Manual calculations from CSV
- ✅ QuantConnect backtesting results
- ✅ Backtrader performance reports
- ✅ Within ±1% tolerance

---

## 📞 Support

For issues or questions:
1. Check `/api/docs/metrics` for metric definitions
2. Run tests to verify installation: `pytest -v`
3. Review logs for detailed error messages

---

## 🔮 Future Enhancements

- [ ] Multiple account support
- [ ] Strategy tagging and filtering
- [ ] Real-time position tracking
- [ ] Database persistence (PostgreSQL)
- [ ] WebSocket updates
- [ ] Advanced risk metrics (VaR, Sortino)
- [ ] Benchmark comparison (S&P 500)
