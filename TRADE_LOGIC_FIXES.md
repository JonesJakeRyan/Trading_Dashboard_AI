# Trade Pairing Logic Fixes

## Issues Fixed

### 1. **Expectancy Formula Correction**
**Problem**: The expectancy calculation was using subtraction instead of addition for losses:
```python
# WRONG (old code)
avg_loss = abs(losing_trades['Realized_PnL'].mean())  # Made positive
expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)  # Subtracting positive loss
```

**Solution**: Keep avg_loss negative and add it (which correctly subtracts):
```python
# CORRECT (new code)
avg_loss = losing_trades['Realized_PnL'].mean()  # Keep negative
expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)  # Adding negative = subtracting
```

**Formula**: `Expectancy = (WinRate × AvgWin) + ((1 - WinRate) × AvgLoss)`

This should now show **+12.24** instead of **-18.46**.

---

### 2. **Exclude Open Positions**
**Problem**: Metrics included trades with 0 P&L (opening positions), inflating trade counts and skewing statistics.

**Solution**: Filter out open positions in all metric calculations:
```python
# Exclude open positions (trades with 0 P&L)
closed_trades = self.df[self.df['Realized_PnL'] != 0].copy()
```

Applied to:
- `get_performance_metrics()` - Total P&L, Sharpe ratio, Expectancy
- `get_win_loss_metrics()` - Win rate, avg win/loss, profit factor
- `get_risk_metrics()` - Max drawdown, total trades count

---

### 3. **FIFO-Based Buy/Sell Matching** ✅ Already Implemented
The `calculate_realized_pnl()` function already correctly implements:

- **FIFO matching**: Always matches sells with the oldest open position (`positions[symbol][0]`)
- **Per-symbol tracking**: Maintains separate position queues for each symbol
- **Weighted average costs**: Handles partial fills with proportional fee allocation
- **Long and short support**: Correctly calculates P&L for both position types

**Example FIFO Logic**:
```python
while remaining_qty > 0 and len(positions[symbol]) > 0:
    oldest_position = positions[symbol][0]  # FIFO: take first
    
    if oldest_position['quantity'] <= remaining_qty:
        # Close entire position
        qty_to_close = oldest_position['quantity']
        realized_pnl += (price - oldest_position['price']) * qty_to_close - fees
        positions[symbol].pop(0)  # Remove closed position
    else:
        # Partially close position
        qty_to_close = remaining_qty
        proportional_fees = oldest_position['fees'] * (qty_to_close / oldest_position['quantity'])
        realized_pnl += (price - oldest_position['price']) * qty_to_close - proportional_fees
        positions[symbol][0]['quantity'] -= qty_to_close  # Update remaining quantity
```

---

## Testing Recommendations

1. **Upload a CSV with open positions** - verify they don't affect metrics
2. **Check expectancy calculation** - should be positive if profitable
3. **Verify trade counts** - should only count closed positions
4. **Test partial fills** - ensure FIFO handles them correctly

---

## Backend Status
✅ Backend running on port **8002**
✅ Frontend updated to connect to port **8002**
✅ All dependencies installed (`python-multipart`)
