# Robinhood CSV Template v1

## Overview
Robinhood export format for stock trades (equities and ETFs only).

## Required Headers

| Column Name | Data Type | Format | Required | Notes |
|-------------|-----------|--------|----------|-------|
| Symbol | TEXT | Uppercase | Yes | Stock ticker |
| Side | TEXT | buy/sell | Yes | Trade direction (lowercase) |
| Shares | DECIMAL | Positive number | Yes | Number of shares |
| Price | DECIMAL | Positive number | Yes | Average price per share in USD |
| Date | TIMESTAMP | ISO 8601 | Yes | Execution timestamp |
| Activity Type | TEXT | Any | No | Trade type descriptor |

## Header Aliases

The parser accepts these variations:
- **Symbol:** Instrument, Ticker, Symbol
- **Side:** Side, Action, Type
- **Shares:** Shares, Quantity, Qty
- **Price:** Price, Average Price, Fill Price
- **Date:** Date, Time, Executed At, Timestamp

## Side Mapping

- **BUY:** buy, Buy, BUY, b
- **SELL:** sell, Sell, SELL, s, sell short, Sell Short

## Date Format

- Primary: ISO 8601 with timezone (e.g., `2024-01-15T10:30:00-05:00`)
- Alternative: `YYYY-MM-DD HH:MM:SS` (EST assumed)
- Robinhood typically exports in ISO 8601 format

## Validation Rules

1. **Symbol:**
   - Must be 1-5 uppercase letters
   - No special characters except hyphens
   - Examples: AAPL, QQQ, BRK-A

2. **Side:**
   - Must be buy or sell (case-insensitive)
   - Short positions mapped to SELL

3. **Shares:**
   - Must be positive decimal
   - Supports fractional shares (e.g., 0.5 shares)
   - Maximum: 1,000,000 shares per trade

4. **Price:**
   - Must be positive decimal
   - Minimum: $0.01
   - Maximum: $100,000 per share

5. **Date:**
   - Must be valid ISO 8601 or standard timestamp
   - Cannot be future date
   - Must be within last 10 years

## Sample CSV

```csv
Symbol,Side,Shares,Price,Date,Activity Type
AAPL,buy,100,150.00,2024-01-15T10:30:00-05:00,Buy
AAPL,sell,100,155.00,2024-01-20T14:00:00-05:00,Sell
TSLA,buy,50.5,200.00,2024-01-22T09:45:00-05:00,Buy
TSLA,sell,50.5,210.00,2024-01-25T15:30:00-05:00,Sell
SPY,sell,200,450.00,2024-02-01T11:00:00-05:00,Sell Short
SPY,buy,200,445.00,2024-02-05T13:00:00-05:00,Buy to Cover
```

## Error Messages

### Missing Required Column
```json
{
  "error": "validation_failed",
  "message": "Missing required column: Shares",
  "checklist": [
    "✓ Symbol column found",
    "✓ Side column found",
    "✗ Shares column not found",
    "✓ Price column found",
    "✓ Date column found"
  ]
}
```

### Invalid Side Value
```json
{
  "error": "validation_failed",
  "message": "Invalid data in row 5",
  "details": {
    "row": 5,
    "column": "Side",
    "value": "transfer",
    "issue": "Side must be 'buy' or 'sell'. Found: transfer"
  }
}
```

## Notes

- Robinhood supports fractional shares (handled in MVP)
- Exports include dividends and other activities (filtered out in MVP)
- Crypto trades will be rejected with clear error message
- Options trades will be rejected with clear error message
- Date format includes timezone information
