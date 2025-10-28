# Webull CSV Template v1

## Overview
Webull export format for stock trades (equities and ETFs only).

## Required Headers

| Column Name | Data Type | Format | Required | Notes |
|-------------|-----------|--------|----------|-------|
| Symbol | TEXT | Uppercase | Yes | Stock ticker (e.g., AAPL, SPY) |
| Action | TEXT | BUY/SELL | Yes | Trade direction |
| Quantity | DECIMAL | Positive number | Yes | Number of shares |
| Price | DECIMAL | Positive number | Yes | Price per share in USD |
| Time | TIMESTAMP | YYYY-MM-DD HH:MM:SS | Yes | Execution time (EST assumed) |
| Account | TEXT | Any | No | Account identifier |

## Header Aliases

The parser accepts these variations:
- **Symbol:** Ticker, Stock Symbol, Symbol
- **Action:** Side, Type, Action
- **Quantity:** Qty, Shares, Quantity
- **Price:** Price, Fill Price, Execution Price
- **Time:** Time, Date, Execution Time, Filled Time

## Side Mapping

- **BUY:** Buy, BUY, buy, B
- **SELL:** Sell, SELL, sell, S, Short Sell, SELL_SHORT

## Date Format

- Primary: `YYYY-MM-DD HH:MM:SS` (e.g., 2024-01-15 10:30:00)
- Alternative: `MM/DD/YYYY HH:MM:SS` (e.g., 01/15/2024 10:30:00)
- Timezone: EST assumed if not specified

## Validation Rules

1. **Symbol:**
   - Must be 1-5 uppercase letters
   - No special characters except hyphens (for preferred stocks)
   - Examples: AAPL, SPY, BRK-B

2. **Action:**
   - Must be BUY or SELL (case-insensitive)
   - Short sells mapped to SELL

3. **Quantity:**
   - Must be positive decimal
   - No zero or negative quantities
   - Maximum: 1,000,000 shares per trade

4. **Price:**
   - Must be positive decimal
   - Minimum: $0.01
   - Maximum: $100,000 per share

5. **Time:**
   - Must be valid timestamp
   - Cannot be future date
   - Must be within last 10 years

## Sample CSV

```csv
Symbol,Action,Quantity,Price,Time,Account
AAPL,BUY,100,150.00,2024-01-15 10:30:00,Account123
AAPL,SELL,100,155.00,2024-01-20 14:00:00,Account123
TSLA,BUY,50,200.00,2024-01-22 09:45:00,Account123
TSLA,SELL,50,210.00,2024-01-25 15:30:00,Account123
SPY,Short Sell,200,450.00,2024-02-01 11:00:00,Account123
SPY,BUY,200,445.00,2024-02-05 13:00:00,Account123
```

## Error Messages

### Missing Required Column
```json
{
  "error": "validation_failed",
  "message": "Missing required column: Symbol",
  "checklist": [
    "✗ Symbol column not found",
    "✓ Action column found",
    "✓ Quantity column found",
    "✓ Price column found",
    "✓ Time column found"
  ]
}
```

### Invalid Data Type
```json
{
  "error": "validation_failed",
  "message": "Invalid data in row 3",
  "details": {
    "row": 3,
    "column": "Quantity",
    "value": "-50",
    "issue": "Quantity must be positive"
  }
}
```

## Notes

- Webull exports typically include additional columns (fees, order ID, etc.) which are ignored in MVP
- Partial fills on same day are treated as separate trades
- After-hours trades included
- Options trades will be rejected with clear error message
