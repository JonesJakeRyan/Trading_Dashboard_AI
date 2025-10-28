# Unified CSV Template v1

## Overview
Standardized format for manual trade entry or custom broker exports. This is the canonical format used internally after normalization.

## Required Headers

| Column Name | Data Type | Format | Required | Notes |
|-------------|-----------|--------|----------|-------|
| symbol | TEXT | Uppercase | Yes | Stock ticker |
| side | TEXT | BUY/SELL | Yes | Trade direction (uppercase) |
| quantity | DECIMAL | Positive number | Yes | Number of shares |
| price | DECIMAL | Positive number | Yes | Price per share in USD |
| executed_at | TIMESTAMP | ISO 8601 | Yes | Execution timestamp with timezone |
| account_id | TEXT | Any | No | Account identifier (optional) |
| notes | TEXT | Any | No | Additional notes (optional) |

## Header Requirements

**Exact header names required (case-sensitive):**
- symbol
- side
- quantity
- price
- executed_at

**Optional headers:**
- account_id
- notes

## Side Values

- **BUY** - Opens or adds to long position, or covers short position
- **SELL** - Closes long position or opens short position

## Date Format

**Required:** ISO 8601 with timezone
- Format: `YYYY-MM-DDTHH:MM:SS±HH:MM`
- Example: `2024-01-15T10:30:00-05:00` (EST)
- Example: `2024-01-15T15:30:00+00:00` (UTC)

## Validation Rules

1. **symbol:**
   - Must be 1-5 uppercase letters
   - No special characters except hyphens
   - Regex: `^[A-Z]{1,5}(-[A-Z])?$`

2. **side:**
   - Must be exactly "BUY" or "SELL" (uppercase)
   - No variations accepted

3. **quantity:**
   - Must be positive decimal
   - Supports fractional shares
   - Minimum: 0.000001
   - Maximum: 1,000,000

4. **price:**
   - Must be positive decimal
   - Minimum: $0.01
   - Maximum: $100,000.00
   - Precision: 2 decimal places

5. **executed_at:**
   - Must be valid ISO 8601 with timezone
   - Cannot be future date
   - Must be within last 10 years
   - Timezone required

6. **account_id (optional):**
   - Any string up to 100 characters
   - Used for grouping trades

7. **notes (optional):**
   - Any string up to 500 characters
   - Not used in calculations

## Sample CSV

```csv
symbol,side,quantity,price,executed_at,account_id,notes
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00,ACCT001,Initial position
AAPL,SELL,100,155.00,2024-01-20T14:00:00-05:00,ACCT001,Closed for profit
TSLA,BUY,50,200.00,2024-01-22T09:45:00-05:00,ACCT001,
TSLA,SELL,50,210.00,2024-01-25T15:30:00-05:00,ACCT001,
SPY,SELL,200,450.00,2024-02-01T11:00:00-05:00,ACCT001,Short position
SPY,BUY,200,445.00,2024-02-05T13:00:00-05:00,ACCT001,Covered short
QQQ,BUY,75.5,380.00,2024-02-10T10:00:00-05:00,ACCT001,Fractional shares
```

## Error Messages

### Missing Required Column
```json
{
  "error": "validation_failed",
  "message": "Missing required columns",
  "checklist": [
    "✓ symbol column found",
    "✗ side column not found (found 'Side' instead - must be lowercase)",
    "✓ quantity column found",
    "✓ price column found",
    "✓ executed_at column found"
  ]
}
```

### Invalid Symbol Format
```json
{
  "error": "validation_failed",
  "message": "Invalid data in row 3",
  "details": {
    "row": 3,
    "column": "symbol",
    "value": "apple",
    "issue": "Symbol must be uppercase letters only (e.g., AAPL)"
  }
}
```

### Missing Timezone
```json
{
  "error": "validation_failed",
  "message": "Invalid data in row 5",
  "details": {
    "row": 5,
    "column": "executed_at",
    "value": "2024-01-15 10:30:00",
    "issue": "Timestamp must include timezone (e.g., 2024-01-15T10:30:00-05:00)"
  }
}
```

## Internal Normalization

All broker formats are normalized to this unified format:

```python
{
    "trade_id": "uuid-generated",
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 100.0,
    "price": 150.00,
    "executed_at": "2024-01-15T10:30:00-05:00",
    "account_id": "ACCT001",
    "notes": "Initial position"
}
```

## Notes

- This format is used internally after parsing broker CSVs
- Users can manually create CSVs in this format
- All timestamps converted to UTC internally for storage
- Displayed in EST for user interface
- Fractional shares fully supported
- No fees or commissions in MVP
