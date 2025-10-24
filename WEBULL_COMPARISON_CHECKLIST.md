# 🔍 Webull P&L Comparison Checklist

## Current Discrepancy

**Our System**: -$1,723.27 YTD (realized only, no fees)  
**Webull Dashboard**: +$974.00 YTD  
**Difference**: **$2,697.27** 🚨

---

## Possible Causes (Ranked by Likelihood)

### 1. ⭐ **Webull Includes Unrealized P&L** (MOST LIKELY)

**Evidence**:
- You have **20 open positions** currently
- Our system shows **realized P&L only** (closed trades)
- Webull dashboards typically show **Total P&L = Realized + Unrealized**

**How to Check**:
1. Go to Webull → Portfolio → Positions
2. Look for "Unrealized P&L" or "Day's Gain/Loss"
3. Check if there's a toggle between "Realized" and "Total" P&L

**If this is the cause**:
- Unrealized P&L would need to be **+$2,697** to match
- This seems plausible given 20 open positions

---

### 2. **Different Accounting Method** (FIFO vs Average Cost)

**Evidence**:
- Webull might use **FIFO** (First-In-First-Out)
- We use **Average Cost**
- However, FIFO typically gives MORE negative P&L, not less

**How to Check**:
1. Go to Webull → Settings → Tax Settings
2. Look for "Cost Basis Method"
3. Check if it says "FIFO", "LIFO", or "Average Cost"

**Impact**: Unlikely to cause +$2,697 swing in the positive direction

---

### 3. **Fees/Commissions Treatment**

**Evidence**:
- Our system: **NO fees** in P&L (gross P&L)
- Webull might show: **Net P&L** (after fees)

**How to Check**:
1. Look at a single trade in Webull
2. Check if P&L shown includes or excludes fees
3. Typical fees: $0-$0.65 per trade

**Impact**: 
- 240 trades × $0.50 avg fee = **-$120** impact
- This would make Webull MORE negative, not positive
- **Not the cause**

---

### 4. **Dividends/Interest Included**

**Evidence**:
- Webull might include dividends, interest, or other income
- Our CSV only has trade fills

**How to Check**:
1. Go to Webull → Account → History
2. Look for "Dividends" or "Interest" transactions
3. Sum up YTD dividends

**Impact**: Could add hundreds of dollars if you hold dividend stocks

---

### 5. **YTD Date Range Mismatch**

**Evidence**:
- Our system: Jan 1, 2025 00:00:00 Eastern → Now
- Webull might use: Different timezone or cutoff

**How to Check**:
1. Check Webull's YTD definition
2. Look at the date range in their report

**Impact**: Minimal (maybe 1-2 trades)

---

### 6. **Options Multiplier Issue**

**Evidence**:
- You uploaded options CSV separately
- Options use 100x multiplier

**How to Check**:
1. Did you upload the options CSV?
2. Check if Webull's $974 includes options trades

**Impact**: Could be significant if options are included

---

## 🔬 Diagnostic Steps

### Step 1: Check Webull's P&L Breakdown

Go to Webull and find:
- [ ] **Realized P&L YTD**: $______
- [ ] **Unrealized P&L**: $______
- [ ] **Total P&L**: $______
- [ ] **Dividends/Interest YTD**: $______

### Step 2: Verify Our Calculation

Run this to get detailed breakdown:
```bash
cd backend
python3 -c "
from services.ingest import ingest_csvs
from services.accounting import AverageCostEngine
from services.metrics import filter_trades_ytd

with open('../Webull_Orders_Records.csv', 'r') as f:
    csv = f.read()

fills = ingest_csvs(equities_csv=csv, ytd_only=False)
engine = AverageCostEngine()
trades = engine.process_fills(fills)
ytd_trades = filter_trades_ytd(trades)

print(f'All-time P&L: \${trades[\"pnl\"].sum():.2f}')
print(f'YTD P&L: \${ytd_trades[\"pnl\"].sum():.2f}')
print(f'YTD trades: {len(ytd_trades)}')
print(f'Open positions: {len(engine.get_open_positions())}')
"
```

### Step 3: Compare Individual Trades

Pick 3-5 large trades and verify:
1. Find the trade in Webull
2. Compare entry price, exit price, quantity
3. Calculate P&L manually: (exit - entry) × qty
4. Check if it matches our system

### Step 4: Check for Missing Data

- [ ] Are all trades from Webull CSV in our system?
- [ ] Are there any trades in Webull not in the CSV?
- [ ] Did you export the full date range?

---

## 📊 Most Likely Scenario

Based on the $2,697 difference, here's what I think is happening:

**Webull Dashboard Shows**:
```
Realized P&L (closed trades):     -$1,723
Unrealized P&L (open positions):  +$2,697
─────────────────────────────────────────
Total P&L:                        +$  974  ← This is what you see
```

**Our System Shows**:
```
Realized P&L (closed trades):     -$1,723  ← This is what we calculate
Unrealized P&L:                   Not calculated
```

---

## ✅ Action Items

1. **Check Webull's "Realized vs Total" toggle**
   - Most broker dashboards have this
   - Switch to "Realized Only" view
   - Compare to our -$1,723

2. **If Webull only shows Total P&L**:
   - Calculate unrealized manually:
   - For each open position: (current_price - avg_cost) × qty
   - Sum all unrealized P&L
   - Add to our -$1,723

3. **If numbers still don't match**:
   - Export a fresh CSV with full date range
   - Check for dividends/interest in Webull
   - Verify cost basis method (FIFO vs Avg Cost)

---

## 🎯 Expected Outcome

If Webull is showing **Total P&L (Realized + Unrealized)**:
- Our **-$1,723** (realized) is CORRECT
- Webull's **+$974** (total) includes **+$2,697** unrealized
- You need **~$2,697 in unrealized gains** from your 20 open positions

**This is actually GOOD NEWS** - it means:
- Your realized trades are net negative (learning/strategy adjustment)
- Your current open positions are profitable (+$2,697 unrealized)
- Total portfolio is positive (+$974)

---

## 📝 Next Steps

**Please check Webull and report back**:
1. What does Webull show for "Realized P&L" specifically?
2. What does Webull show for "Unrealized P&L"?
3. Is there a toggle between "Realized" and "Total"?
4. Are dividends/interest included in the $974?

Once we know this, we can either:
- ✅ Confirm our calculation is correct (if Webull realized = -$1,723)
- 🔧 Fix our calculation (if Webull realized ≠ -$1,723)
- 📊 Add unrealized P&L tracking (if you want total P&L like Webull)
