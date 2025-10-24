# 📈 Options Trading Support

## Overview

The Trading Performance Dashboard now supports **options trading analysis** with automatic detection and combined P&L calculation for both stocks and options.

---

## 🎯 Features

### ✅ Supported Options Strategies

1. **Iron Condors** - 4-leg neutral strategy
2. **Iron Butterflies** - 4-leg neutral strategy  
3. **Vertical Spreads** - 2-leg directional strategy
4. **Straddles** - 2-leg volatility strategy
5. **Single Options** - Individual calls/puts

### ✅ Capabilities

- **Auto-detection** of file type (stocks vs options)
- **Multi-leg strategy** parsing
- **Net P&L calculation** per strategy
- **Combined metrics** for stocks + options
- **Position-based accounting** for all trades

---

## 📊 How It Works

### Options CSV Format

Your Webull options CSV has a hierarchical structure:

```csv
Name,Symbol,Side,Status,Filled,Total Qty,Price,Avg Price,...
ASPI Vertical,,Sell,Filled,2,2,@1.13,1.13,...
,ASPI251017C00009000,Sell,Filled,2,2,@1.75,1.75,...
,ASPI251017C00012500,Buy,Filled,2,2,@0.620,0.620,...
```

**Structure**:
1. **Header row**: Strategy name, net premium, direction
2. **Leg rows**: Individual option contracts (empty Name field)

---

## 🔧 API Usage

### 1. Upload Options Only

```bash
# Auto-detect (recommended)
curl -X POST http://localhost:8002/api/upload \
  -F "file=@Webull_Orders_Records_Options.csv"

# Explicit type
curl -X POST "http://localhost:8002/api/upload?file_type=options" \
  -F "file=@Webull_Orders_Records_Options.csv"
```

**Response**:
```json
{
  "success": true,
  "filename": "Webull_Orders_Records_Options.csv",
  "file_type": "options",
  "total_orders": 23,
  "closed_positions": 23,
  "metrics": {
    "summary": {
      "total_pnl": 159.0,
      "expectancy": 6.91
    }
  }
}
```

---

### 2. Upload Stocks Only

```bash
curl -X POST http://localhost:8002/api/upload \
  -F "file=@Webull_Orders_Records.csv"
```

**Response**:
```json
{
  "file_type": "stocks",
  "total_orders": 1106,
  "closed_positions": 287,
  "metrics": {
    "summary": {
      "total_pnl": 1328.78
    }
  }
}
```

---

### 3. Upload Both (Combined Analysis) 🎯

```bash
curl -X POST http://localhost:8002/api/upload/combined \
  -F "stocks_file=@Webull_Orders_Records.csv" \
  -F "options_file=@Webull_Orders_Records_Options.csv"
```

**Response**:
```json
{
  "success": true,
  "stocks_file": "Webull_Orders_Records.csv",
  "options_file": "Webull_Orders_Records_Options.csv",
  "total_stock_orders": 1106,
  "total_options_orders": 23,
  "total_positions": 310,
  "breakdown": {
    "stocks_pnl": 1328.78,
    "options_pnl": 159.0,
    "combined_pnl": 1487.78
  },
  "metrics": {
    "summary": {
      "total_pnl": 1487.78,
      "expectancy": 12.45
    }
  }
}
```

---

## 📈 P&L Calculation

### Multi-Leg Strategies

**Example: Iron Condor**

```
Strategy: SKYT IronCondor
Direction: SELL (to open)
Net Premium: $2.40

Legs:
- Buy  SKYT251003C00023500 @ $0.08
- Sell SKYT251003C00018000 @ $2.53
- Sell SKYT251003P00017500 @ $0.08
- Buy  SKYT251003P00013000 @ $0.13

Net Credit: $2.40 × 100 = $240
P&L: $240 (assuming expired worthless)
```

**Formula**:
```python
if direction == 'SELL':
    # Sold to open - collected premium
    pnl = net_premium × 100 × quantity
else:
    # Bought to open - paid premium
    pnl = -net_premium × 100 × quantity
```

---

### Single Options

**Example: Call Option**

```
Symbol: SOUN250919C00015500
Side: Buy
Price: $0.52
Quantity: 1

Cost: $0.52 × 100 = $52
P&L: -$52 (assuming expired worthless)
```

---

## 🎨 Strategy Types

### Iron Condor
```
Structure: Sell OTM call spread + Sell OTM put spread
Max Profit: Net credit received
Max Loss: Width of spread - net credit
```

### Iron Butterfly
```
Structure: Sell ATM call + Sell ATM put + Buy OTM call + Buy OTM put
Max Profit: Net credit received
Max Loss: Width of wings - net credit
```

### Vertical Spread
```
Structure: Buy option + Sell option (same type, different strikes)
Debit Spread: Pay to open (bullish call, bearish put)
Credit Spread: Collect to open (bearish call, bullish put)
```

### Straddle
```
Structure: Buy ATM call + Buy ATM put
Max Profit: Unlimited
Max Loss: Total premium paid
```

---

## 📊 Metrics

### Options-Specific Fields

```json
{
  "symbol": "ASPI",
  "position_type": "options",
  "strategy_name": "ASPI Vertical",
  "num_legs": 2,
  "realized_pnl": 113.0
}
```

### Combined Metrics

When uploading both stocks and options:

```json
{
  "breakdown": {
    "stocks_pnl": 1328.78,
    "options_pnl": 159.0,
    "combined_pnl": 1487.78
  },
  "metrics": {
    "summary": {
      "total_pnl": 1487.78,
      "win_rate": 62.5,
      "expectancy": 12.45,
      "sharpe_ratio": 2.18
    }
  }
}
```

---

## 🔍 Auto-Detection Logic

The system auto-detects file type by looking for:

1. **Strategy keywords**: IronCondor, IronButterfly, Vertical, Straddle
2. **Option symbols**: Pattern like `SYMBOL251017C00009000`

```python
def _detect_file_type(csv_content: str) -> str:
    if 'IronCondor' in csv_content or 'IronButterfly' in csv_content:
        return 'options'
    if re.search(r'[A-Z]+\d{6}[CP]\d{8}', csv_content):
        return 'options'
    return 'stocks'
```

---

## 🧪 Testing

### Test Options Upload

```bash
cd /path/to/project

# Upload options CSV
curl -X POST http://localhost:8002/api/upload \
  -F "file=@Webull_Orders_Records_Options.csv" \
  | python3 -m json.tool
```

**Expected Output**:
```json
{
  "file_type": "options",
  "total_orders": 23,
  "closed_positions": 23,
  "metrics": {
    "summary": {
      "total_pnl": 159.0
    }
  }
}
```

---

### Test Combined Upload

```bash
curl -X POST http://localhost:8002/api/upload/combined \
  -F "stocks_file=@Webull_Orders_Records.csv" \
  -F "options_file=@Webull_Orders_Records_Options.csv" \
  | python3 -m json.tool
```

**Expected Output**:
```json
{
  "breakdown": {
    "stocks_pnl": 1328.78,
    "options_pnl": 159.0,
    "combined_pnl": 1487.78
  }
}
```

---

## 📝 Example Strategies in Your Data

### 1. SPXW Iron Condor
```
Net Premium: $2.20 × 100 = $220
P&L: $220 ✅ (Winner)
```

### 2. ASPI Vertical Spread
```
Net Premium: $1.13 × 100 × 2 = $226
P&L: $226 ✅ (Winner)
```

### 3. WMT Iron Butterfly
```
Entry: Buy @ $0.85 × 100 = -$85
Exit: Sell @ $1.45 × 100 = $145
P&L: $60 ✅ (Winner)
```

### 4. CLSK Iron Butterfly
```
Entry: Buy @ $1.01 × 100 = -$101
Exit: Sell @ $0.97 × 100 = $97
P&L: -$4 ❌ (Loser)
```

---

## 🎯 Benefits

### 1. **Unified Analysis**
- Single dashboard for stocks + options
- Combined P&L tracking
- Holistic performance view

### 2. **Strategy Recognition**
- Automatically parses multi-leg strategies
- Calculates net P&L per strategy
- Tracks strategy performance

### 3. **Accurate Metrics**
- Position-based accounting
- Proper Sharpe ratio
- Accurate drawdown
- Win rate by strategy

---

## 🚀 Frontend Integration

### Single File Upload

The existing upload component works automatically:

```jsx
// Upload stocks or options - auto-detected
<input type="file" onChange={handleUpload} />
```

### Combined Upload (Future Enhancement)

```jsx
// Upload both files
<input type="file" name="stocks" />
<input type="file" name="options" />
<button onClick={handleCombinedUpload}>Analyze Both</button>
```

---

## 📊 Performance Summary

### Your Options Trading (23 Positions)

```
Total P&L: $159.00
Win Rate: 43.48%
Avg Win: $139.40
Avg Loss: -$95.00
Expectancy: $6.91 per position
Sharpe Ratio: 1.16
Max Drawdown: 5.17%
```

### Best Performers

1. **SPXW Iron Condor**: +$220
2. **CBRL Put**: +$100
3. **SKYT Iron Condor**: +$89

### Strategy Breakdown

- **Iron Condors**: 3 positions, $309 total
- **Verticals**: 3 positions, $226 total
- **Butterflies**: 3 positions, $55 total
- **Single Options**: 14 positions, -$431 total

---

## 🔮 Future Enhancements

### Planned Features

1. **Open position tracking** (currently assumes all closed)
2. **Greeks calculation** (delta, gamma, theta, vega)
3. **Implied volatility** tracking
4. **Strategy-specific metrics** (max profit, max loss, breakevens)
5. **Expiration tracking** (DTE at entry/exit)
6. **Assignment handling** (early exercise, ITM at expiration)

---

## ✅ Summary

**Options Support v3.0** provides:

1. ✅ **Multi-leg strategy** parsing
2. ✅ **Auto-detection** of file type
3. ✅ **Combined P&L** (stocks + options)
4. ✅ **Net premium** calculation
5. ✅ **Strategy recognition** (Iron Condor, Butterfly, etc.)
6. ✅ **Unified metrics** across all positions

**Your dashboard now handles both stocks AND options trading!** 🎉

---

## 📞 API Endpoints

### Available Endpoints

```
POST /api/upload
  - Single file upload (auto-detect or specify type)
  - Query params: file_type, win_rate_mode, dead_zone, starting_equity

POST /api/upload/combined
  - Upload both stocks and options
  - Query params: win_rate_mode, dead_zone, starting_equity

GET /api/health
  - Health check

GET /api/docs/metrics
  - Metrics documentation

GET /docs
  - Interactive API documentation (Swagger)
```

---

## 🎉 Ready to Use!

Upload your options CSV at:
```
http://localhost:5173
```

Or test via API:
```bash
curl -X POST http://localhost:8002/api/upload \
  -F "file=@Webull_Orders_Records_Options.csv"
```

**Your complete trading performance (stocks + options) in one dashboard!** 📊
