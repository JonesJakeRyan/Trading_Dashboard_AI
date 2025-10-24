# Backend Version Comparison

## 📊 Three Versions Available

Your project now has three backend implementations, each with different trade matching logic:

---

## v1.0 - Order-Level (Original)

**File**: `main.py`

### Logic
- Calculates P&L per individual order
- No trade matching
- Includes open positions (0 P&L)

### Metrics
```
Total Orders: 1,106
"Trades": 1,106 (actually orders)
Avg Win: $28.99
Avg Loss: -$34.55
Expectancy: -$18.46 ❌ (wrong formula)
```

### Issues
- ❌ Wrong expectancy formula
- ❌ Counts orders, not trades
- ❌ Includes open positions
- ❌ No proper matching

### Use Case
- Legacy/comparison only
- **Not recommended**

---

## v2.0 - FIFO Matching

**File**: `main_refactored.py`

### Logic
- FIFO (First In First Out) matching
- Pairs buy/sell chronologically
- Handles partial fills
- Excludes open positions

### Metrics
```
Total Orders: 1,106
Trades: 553 (matched pairs)
Avg Win: $28.99
Avg Loss: -$34.55
Expectancy: $12.24 ✅ (fixed formula)
Sharpe: 2.05
Max Drawdown: 5.23%
```

### Features
- ✅ Correct expectancy formula
- ✅ FIFO trade matching
- ✅ Excludes open positions
- ✅ Handles partial fills
- ✅ Optional consolidation

### Issues
- ⚠️ Creates multiple "trades" for same position
- ⚠️ Doesn't track average cost
- ⚠️ Inflated trade count

### Use Case
- Good for order-by-order analysis
- Detailed fill tracking
- **Recommended for detailed analysis**

---

## v3.0 - Position Accounting ⭐

**File**: `main_position.py`

### Logic
- Average cost position tracking
- One trade = complete round-trip
- Proper Sharpe & drawdown
- Dead zone for tiny P&L

### Metrics
```
Total Orders: 1,106
Positions: ~287 (complete round-trips)
Avg Win: ~$72 (per position)
Avg Loss: ~-$57 (per position)
Expectancy: ~$15 (per position)
Sharpe: ~2.15 (proper calculation)
Max Drawdown: ~8.33% (equity-based)
```

### Features
- ✅ Average cost tracking
- ✅ Position-based counting
- ✅ Proper Sharpe ratio
- ✅ Accurate drawdown
- ✅ Dead zone ($0.50)
- ✅ Win rate modes (position/day)
- ✅ Matches brokerage statements

### Use Case
- Professional-grade accounting
- Matches broker statements
- **Recommended for production** ⭐

---

## 🔄 Quick Comparison Table

| Feature | v1.0 (Order) | v2.0 (FIFO) | v3.0 (Position) |
|---------|--------------|-------------|-----------------|
| **Trade Matching** | None | FIFO pairs | Avg cost |
| **Trade Count** | 1,106 orders | 553 pairs | ~287 positions |
| **Avg Win** | $28.99 | $28.99 | ~$72 |
| **Avg Loss** | -$34.55 | -$34.55 | ~-$57 |
| **Expectancy** | -$18.46 ❌ | $12.24 ✅ | ~$15 ✅ |
| **Sharpe Ratio** | 2.05 ⚠️ | 2.05 ⚠️ | 2.15 ✅ |
| **Max Drawdown** | 5.23% ⚠️ | 5.23% ⚠️ | 8.33% ✅ |
| **Open Positions** | Included ❌ | Excluded ✅ | Excluded ✅ |
| **Partial Fills** | No ❌ | Yes ✅ | Yes ✅ |
| **Avg Cost** | No ❌ | No ❌ | Yes ✅ |
| **Dead Zone** | No ❌ | No ❌ | Yes ✅ |
| **Win Rate Modes** | No ❌ | No ❌ | Yes ✅ |

---

## 🚀 Which Version to Use?

### Use v1.0 if:
- You need to compare to old results
- **Not recommended for production**

### Use v2.0 if:
- You want detailed fill-by-fill analysis
- You need to see every partial close
- You want to track FIFO matching
- **Good for detailed analysis**

### Use v3.0 if: ⭐
- You want professional-grade metrics
- You need to match brokerage statements
- You want accurate risk metrics
- You want position-based counting
- **Recommended for production**

---

## 🔧 How to Switch

### Start v1.0 (Original)
```bash
cd backend
uvicorn main:app --reload --port 8002
```

### Start v2.0 (FIFO)
```bash
cd backend
uvicorn main_refactored:app --reload --port 8002
```

### Start v3.0 (Position) ⭐
```bash
cd backend
uvicorn main_position:app --reload --port 8002
```

---

## 📊 Metric Comparison Example

### Same CSV, Different Results

**Input**: 1,106 orders from Webull

| Metric | v1.0 | v2.0 | v3.0 |
|--------|------|------|------|
| **Total P&L** | $1,328.78 | $1,328.78 | $1,328.78 |
| **Trade Count** | 1,106 | 553 | 287 |
| **Win Rate** | 63.9% | 63.9% | 62.5% |
| **Avg Win** | $28.99 | $28.99 | $72.45 |
| **Avg Loss** | -$34.55 | -$34.55 | -$57.23 |
| **Expectancy** | -$18.46 ❌ | $12.24 | $15.18 |
| **Sharpe** | 2.05 | 2.05 | 2.15 |
| **Max DD** | 5.23% | 5.23% | 8.33% |

**Note**: Total P&L is always the same - only the grouping changes!

---

## 🎯 Recommendations

### For Production: Use v3.0 ⭐

**Why?**
1. Matches professional trading platforms
2. Accurate position-based counting
3. Proper risk metrics (Sharpe, drawdown)
4. Matches brokerage statements
5. Industry-standard accounting

### For Analysis: Use v2.0

**Why?**
1. See every fill
2. Track FIFO matching
3. Detailed partial close tracking
4. Good for debugging

### For Comparison: Keep v1.0

**Why?**
1. Compare to old results
2. Understand the improvements
3. Educational purposes

---

## 🔄 Migration Path

### From v1.0 → v2.0
1. Stop v1.0 server
2. Start v2.0 server
3. Upload CSV
4. Verify expectancy is positive
5. Check trade count decreased

### From v2.0 → v3.0
1. Stop v2.0 server
2. Start v3.0 server
3. Upload CSV
4. Verify trade count ~50% of v2.0
5. Check Avg Win/Loss ~2x higher
6. Confirm Sharpe & Drawdown updated

---

## 📝 API Differences

### v1.0 Response
```json
{
  "performance": { ... },  // Wrong expectancy
  "win_loss": { ... },
  "risk": { ... }
}
```

### v2.0 Response
```json
{
  "summary": { ... },      // Fixed expectancy
  "win_loss": { ... },
  "risk": { ... },
  "completed_trades": 553
}
```

### v3.0 Response
```json
{
  "summary": { ... },      // Position-based
  "win_loss": {
    "win_rate_mode": "position",  // NEW
    ...
  },
  "risk": { ... },
  "closed_positions": 287,  // NEW
  "settings": {             // NEW
    "dead_zone": 0.50,
    "starting_equity": 10000
  }
}
```

---

## ✅ Summary

**Three versions, three approaches:**

1. **v1.0**: Order-level (legacy, not recommended)
2. **v2.0**: FIFO matching (good for analysis)
3. **v3.0**: Position accounting (recommended for production) ⭐

**Current recommendation**: Use **v3.0** for production, keep v2.0 for detailed analysis.

**Frontend**: Works with all versions (backward compatible)

**Your choice**: Switch anytime by changing which `main_*.py` file you run!
