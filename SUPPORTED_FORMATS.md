# 📋 Supported CSV Formats

The Trading Performance Dashboard automatically detects and parses CSV files from multiple brokers.

## ✅ Supported Brokers

### 1. **Webull**
- **Format**: Order Records Export
- **Key Columns**: 
  - `Filled Time` → Date
  - `Symbol` → Symbol
  - `Filled` → Quantity
  - `Avg Price` → Price (automatically removes @ symbol)
  - `Side` → Side (Buy/Sell/Short)
  - `Status` → Filters for "Filled" only
  
**Example:**
```csv
Name,Symbol,Side,Status,Filled,Total Qty,Price,Avg Price,Time-in-Force,Placed Time,Filled Time
SOUNDHOUND AI INC,SOUN,Buy,Filled,10,10,@16.53,16.53,DAY,09/19/2025 13:31:39 EDT,09/19/2025 13:31:39 EDT
Walmart,WMT,Short,Filled,40,40,@102.84,102.84,DAY,09/19/2025 11:31:27 EDT,09/19/2025 11:36:41 EDT
```

### 2. **TD Ameritrade**
- **Format**: Transaction History
- **Key Columns**:
  - `Date` or `Execution Time` → Date
  - `Symbol` or `Ticker` → Symbol
  - `Qty` or `Quantity` → Quantity
  - `Price` or `Execution Price` → Price
  - `Action` or `Side` → Side
  - `Commission` → Fees

### 3. **Interactive Brokers**
- **Format**: Trade Confirmation
- **Key Columns**:
  - `Date/Time` → Date
  - `Symbol` → Symbol
  - `Quantity` → Quantity
  - `Price` → Price
  - `Buy/Sell` → Side
  - `Commission` → Fees

### 4. **Generic Format**
Any CSV with these columns will work:
- `Date` (required)
- `Symbol` (required)
- `Quantity` (required)
- `Price` (required)
- `Side` (required) - Buy/Sell
- `Fees` (optional) - defaults to 0
- `Realized_PnL` (optional) - auto-calculated if missing

## 🔄 Column Name Variations

The parser automatically recognizes these variations:

| Standard | Accepted Variations |
|----------|-------------------|
| **Date** | date, datetime, time, Filled Time, Placed Time |
| **Symbol** | symbol, ticker, Ticker |
| **Quantity** | quantity, qty, Qty, Filled, Total Qty |
| **Price** | price, execution_price, Avg Price |
| **Side** | side, action, Action, type |
| **Fees** | fees, commission, Commission |
| **Realized_PnL** | realized_pnl, pnl, PnL, profit_loss, P&L, Profit/Loss |

## 🧹 Automatic Data Cleaning

The system automatically:
- ✅ Filters out cancelled/unfilled orders
- ✅ Removes @ and $ symbols from prices
- ✅ Converts dates to standard format
- ✅ Removes duplicate rows
- ✅ Handles missing data
- ✅ Calculates P&L if not provided
- ✅ Recognizes "Short" as a sell-side transaction

## 📊 P&L Calculation

If your CSV doesn't include P&L, it's calculated as:
- **Buy**: `-1 × (Price × Quantity + Fees)`
- **Sell/Short**: `Price × Quantity - Fees`

## ⚠️ Important Notes

1. **Filled Orders Only**: Cancelled or pending orders are automatically filtered out
2. **Date Format**: Any standard date format is supported (MM/DD/YYYY, YYYY-MM-DD, etc.)
3. **Short Positions**: "Short" is treated as a sell transaction
4. **Fees**: If not provided, defaults to $0
5. **Minimum Data**: At least Date, Symbol, Quantity, Price, and Side are required

## 🧪 Testing Your CSV

Before uploading, ensure your CSV has:
1. A header row with column names
2. At least one filled/completed trade
3. Valid numeric values for quantity and price
4. Recognizable date format

## 🐛 Troubleshooting

### "Missing required columns" Error
- Check that your CSV has: Date, Symbol, Quantity, Price, Side
- Column names are case-insensitive
- See variations table above

### "No valid trades found" Error
- Ensure you have at least one filled/completed trade
- Check for cancelled orders (they're filtered out)
- Verify numeric fields contain valid numbers

### Price Parsing Issues
- Remove currency symbols manually if needed
- Ensure decimal separator is a period (.)
- Check for extra spaces or special characters

## 📝 Example Generic CSV

```csv
Date,Symbol,Quantity,Price,Side,Fees,Realized_PnL
2024-01-05,AAPL,100,185.50,Buy,1.00,-18551.00
2024-01-08,AAPL,100,189.25,Sell,1.00,18923.00
2024-01-10,TSLA,50,238.45,Buy,1.00,-11923.50
2024-01-15,TSLA,50,245.80,Sell,1.00,12289.00
```

## 🚀 Future Broker Support

Planning to add support for:
- Robinhood
- E*TRADE
- Charles Schwab
- Fidelity
- Alpaca

---

**Need help?** Check the main README.md or contact support.
