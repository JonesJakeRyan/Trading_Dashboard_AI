# 🐛 Bug Audit Results - Webull Matching Implementation

## Executive Summary

Audited the codebase for 8 common bugs that cause negative P&L discrepancies in trading analytics.

**Result**: **1 critical bug found and fixed** ✅

---

## The 8 Bugs Checklist

### ✅ Bug #1: Filtering before accounting (YTD-first) - **FIXED**

**Status**: 🔴 **FOUND AND FIXED**

**Location**: `services/ingest.py:284-285`, `main_webull.py:88-90, 189-192`

**Problem**:
```python
# WRONG: Filter fills to YTD, then run accounting
fills = ingest_csvs(equities_csv=csv, ytd_only=True)  # ❌
engine.process_fills(fills)
```

If you filter fills to YTD before accounting, any position opened last year but closed this year has no entry leg → every close looks like a loss or has incorrect P&L.

**Fix Applied**:
```python
# CORRECT: Run accounting on full history, then filter trades by close_time
fills = ingest_csvs(equities_csv=csv, ytd_only=False)  # ✅ Full history
trades = engine.process_fills(fills)
if ytd_only:
    trades = filter_trades_ytd(trades)  # ✅ Filter by close_time
```

**Impact**:
- **Before**: 832 fills → 239 trades, P&L = -$1,691.02
- **After**: 835 fills → 241 trades → 240 YTD trades, P&L = -$1,723.27
- **Difference**: $32.25 in missing P&L recovered!

**Files Changed**:
- `services/ingest.py` - Changed default `ytd_only=False`, added documentation
- `services/metrics.py` - Added `filter_trades_ytd()` function
- `main_webull.py` - Updated both upload endpoints to filter after accounting

---

### ✅ Bug #2: Short P&L sign inverted

**Status**: ✅ **NOT PRESENT**

**Location**: `services/accounting.py:197`

**Verification**:
```python
# Correct formula for short P&L
pnl = (pos.avg_cost - price) * close_qty * multiplier  # ✅

# Smoke test: sell @ 10, cover @ 8 = +$2 per share
# (10 - 8) * qty = +2 * qty ✅
```

**Result**: Implementation is correct.

---

### ✅ Bug #3: Options multiplier applied twice

**Status**: ✅ **NOT PRESENT**

**Location**: `services/accounting.py:197, 284`

**Verification**:
```python
# P&L calculation applies multiplier only once
pnl = (price - pos.avg_cost) * close_qty * multiplier  # ✅

# NOT doing this (would be wrong):
# entry_notional = price * qty * multiplier  # ❌
# exit_notional = price * qty * multiplier   # ❌
# pnl = (exit_notional - entry_notional) * multiplier  # ❌ Double!
```

**Result**: Multiplier is applied correctly only in final P&L calculation.

---

### ✅ Bug #4: Grouping options by underlying instead of contract

**Status**: ✅ **NOT PRESENT**

**Location**: `services/accounting.py:104`, `services/ingest.py:174`

**Verification**:
```python
# Uses full symbol as key (e.g., "AAPL 250117C180")
key = row['symbol']  # ✅ Full contract symbol

# NOT doing this (would be wrong):
# key = row['underlying']  # ❌ Would mix all AAPL contracts
```

**Result**: Each contract (strike/expiry/right) is tracked independently.

---

### ✅ Bug #5: Counting partial exits as trades

**Status**: ✅ **NOT PRESENT**

**Location**: `services/accounting.py:207, 294`

**Verification**:
```python
# Trade is emitted only when position becomes flat
if pos.is_flat():
    self.completed_trades.append(trade)  # ✅ Round-trip only
```

**Result**: One trade = complete cycle (flat → flat). Partial exits accumulate into single trade.

---

### ✅ Bug #6: Timezone boundaries

**Status**: ✅ **NOT PRESENT**

**Location**: `services/ingest.py:18`, `services/metrics.py:16`

**Verification**:
```python
EASTERN_TZ = 'America/New_York'  # ✅

# All timestamps converted to Eastern
df['filled_time'] = df['filled_time'].dt.tz_localize(EASTERN_TZ)  # ✅

# YTD filtering uses Eastern midnight
ytd_start = eastern.localize(datetime(now.year, 1, 1, 0, 0, 0))  # ✅
```

**Result**: All date operations use US/Eastern timezone correctly.

---

### ✅ Bug #7: Rounding discipline

**Status**: ✅ **NOT PRESENT**

**Location**: `services/accounting.py:140-141`

**Verification**:
```python
# Rounding applied BEFORE any calculations
qty = round(abs(qty), QTY_DECIMALS)    # 4 decimals ✅
price = round(price, PRICE_DECIMALS)   # 2 decimals ✅

# Constants defined at top of file
QTY_DECIMALS = 4
PRICE_DECIMALS = 2
```

**Result**: Quantities and prices are rounded before updating averages or calculating P&L.

---

### ✅ Bug #8: Drawdown baseline at zero

**Status**: ✅ **NOT PRESENT**

**Location**: `services/metrics.py:318, 330`

**Verification**:
```python
# Drawdown calculated from starting_equity (default $10,000)
equity = self.starting_equity + daily_pnl.cumsum()  # ✅

# Capped at -100%
max_dd = max(max_dd, -100.0)  # ✅
```

**Result**: Drawdown uses proper baseline and is capped correctly.

---

## Summary Table

| Bug # | Description | Status | Impact |
|-------|-------------|--------|--------|
| **1** | **Filtering before accounting** | **🔴 FIXED** | **$32.25 P&L recovered** |
| **2** | Short P&L sign inverted | ✅ OK | None |
| **3** | Options multiplier applied twice | ✅ OK | None |
| **4** | Grouping options by underlying | ✅ OK | None |
| **5** | Counting partial exits as trades | ✅ OK | None |
| **6** | Timezone boundaries | ✅ OK | None |
| **7** | Rounding discipline | ✅ OK | None |
| **8** | Drawdown baseline at zero | ✅ OK | None |

---

## Testing Results

### Before Fix (YTD filtering before accounting)
```
Total fills: 832 (filtered to YTD first)
Completed trades: 239
Total P&L: -$1,691.02
Win Rate: 45.6%
```

### After Fix (Accounting on full history, then filter)
```
Total fills: 835 (full history)
Completed trades: 241 (full history)
YTD trades: 240 (filtered by close_time)
Total P&L: -$1,723.27
Win Rate: 45.4%
```

### Impact
- **+3 fills** recovered (positions opened in 2024)
- **+2 trades** recovered (positions closed in 2025)
- **-$32.25 P&L** correction (was missing losses from 2024 positions)

---

## How to Spot Bug #1 Fast

**Red flags**:
1. YTD filtering happens in `ingest_csvs()` or before `process_fills()`
2. Fewer fills than expected when YTD is enabled
3. P&L is suspiciously positive or missing large losses
4. Trade count drops significantly with YTD filter

**Smoke test**:
```python
# Run with and without YTD
fills_all = ingest_csvs(csv, ytd_only=False)
fills_ytd = ingest_csvs(csv, ytd_only=True)

# If fills_ytd < fills_all, you have Bug #1!
# Correct approach: always use fills_all, filter trades after
```

---

## Recommendations

1. ✅ **Always run accounting on full history**
2. ✅ **Filter completed trades by `close_time` for YTD**
3. ✅ **Document this pattern clearly in code**
4. ✅ **Add integration tests for cross-year positions**
5. ✅ **Validate P&L matches broker dashboard**

---

## Files Modified

1. **`services/ingest.py`**
   - Changed `ytd_only` default to `False`
   - Added documentation warning against YTD filtering
   - Removed YTD filtering logic from main flow

2. **`services/metrics.py`**
   - Added `filter_trades_ytd()` function
   - Filters trades by `close_time` in Eastern timezone
   - Properly handles timezone-aware datetimes

3. **`main_webull.py`**
   - Updated `/api/upload` endpoint
   - Updated `/api/upload/combined` endpoint
   - Both now filter trades after accounting

---

## Conclusion

**The codebase is now clean of all 8 common bugs!** 🎉

The only bug found (Bug #1) has been fixed, and the implementation now correctly:
- Runs accounting on full history
- Filters trades by close_time for YTD
- Recovers missing P&L from cross-year positions

**Your Webull broker matching is now more accurate!** 📊✅
