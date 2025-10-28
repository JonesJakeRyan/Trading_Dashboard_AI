# Trading Dashboard - Assumptions & Limitations

## Calculation Methodology

### FIFO Accounting (First-In-First-Out)
- All position matching uses **FIFO** logic for both long and short positions
- Separate queues maintained per symbol for long lots and short lots
- Realized P&L calculated only when positions are closed

### Long Positions
- **BUY** opens or adds to long position
- **SELL** closes long positions (FIFO) or opens short if no long positions exist
- Realized P&L = (sell_price - buy_price) × quantity

### Short Positions
- **SELL** opens or adds to short position (when no long positions exist)
- **BUY** covers short positions (FIFO) or opens long if no short positions exist
- Realized P&L = (sell_price - buy_price) × quantity (negative quantity for shorts)

## Scope & Limitations

### Supported
- ✅ USD equities and ETFs only
- ✅ Long and short positions
- ✅ Realized P&L (closed trades only)
- ✅ Calendar day timeframes (EST timezone)
- ✅ Continuous P&L chart with no gaps

### NOT Supported (MVP)
- ❌ Options, futures, crypto, forex
- ❌ Dividends and distributions
- ❌ Trading fees and commissions
- ❌ Corporate actions (splits, mergers, spinoffs)
- ❌ Unrealized P&L (open positions)
- ❌ Time-weighted returns
- ❌ Intraday P&L (only end-of-day)
- ❌ Multi-currency conversions

## Data Requirements

### CSV Format
- Must match one of the supported broker templates:
  - Webull v1
  - Robinhood v1
  - Unified CSV v1
- All timestamps converted to EST
- Prices in USD
- Positive quantities only (side determines direction)

### Validation Rules
- Symbol must be uppercase text
- Side must be BUY or SELL
- Quantity must be positive decimal
- Price must be positive decimal
- Executed timestamp required

## Timeframe Definitions

All timeframes use **EST (America/New_York)** timezone:

- **ALL**: Minimum date → Maximum date in dataset
- **YTD**: January 1 of current year → Latest date
- **6M**: Last 182 calendar days
- **3M**: Last 91 calendar days
- **1M**: Last 30 calendar days
- **1W**: Last 7 calendar days

Market close time: **4:00 PM EST**

## Chart Behavior

### Continuous Line
- Missing trading days are filled to create continuous line
- No gaps between data points
- Cumulative P&L carried forward on non-trading days

### Color Coding
- **Green** (#16a34a): Cumulative P&L ≥ $0.00
- **Red** (#dc2626): Cumulative P&L < $0.00
- Smooth gradient transition when crossing zero

## AI Coach Insights

### Constraints
- **No specific ticker recommendations** or trade calls
- Pattern recognition only (e.g., "high concentration in tech sector")
- Risk observations (e.g., "frequent trading on Mondays with lower win rate")
- General improvement suggestions (e.g., "consider position sizing")

### Data Privacy
- Aggregated metrics only sent to OpenAI
- No raw trade data or PII transmitted
- Deterministic JSON-mode responses
- Fallback to neutral message on API failure

## Accuracy Expectations

### Target Accuracy
- ≥ 95% parity with broker-reported realized P&L
- Rounding precision: ≤ $0.01 per trade
- Cumulative error tolerance: ≤ $1.00 per 1000 trades

### Known Edge Cases
- Partial fills on same day: treated as separate trades
- After-hours trades: included in next calendar day
- Wash sales: not tracked (tax implications not calculated)

## Performance Limits

### MVP Constraints
- CSV uploads: ≤ 10 MB file size
- Trade count: optimized for ≤ 10,000 trades
- Processing time: ≤ 10 seconds for typical dataset
- Chart rendering: ≤ 5,000 data points for smooth animation

## Future Enhancements

Planned for post-MVP:
- Options support with Greeks
- Fee and dividend tracking
- Broker API integrations (OAuth)
- Multi-currency support
- Advanced analytics (Sharpe ratio, max drawdown)
- Time-weighted returns
- Tax lot tracking and wash sale detection
