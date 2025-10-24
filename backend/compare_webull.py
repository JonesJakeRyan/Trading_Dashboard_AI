#!/usr/bin/env python3
"""
Detailed comparison to help identify the $675 discrepancy
"""

from services.ingest import ingest_csvs
from services.accounting_fifo import FIFOEngine
from services.metrics import filter_trades_ytd
import pandas as pd

# Load CSV
print("Loading CSV...")
with open('../Webull_Orders_Records.csv', 'r') as f:
    csv = f.read()

fills = ingest_csvs(equities_csv=csv, ytd_only=False)
engine = FIFOEngine()
trades = engine.process_fills(fills)
ytd_trades = filter_trades_ytd(trades)

print(f"Total fills: {len(fills)}")
print(f"All-time trades: {len(trades)}")
print(f"YTD trades: {len(ytd_trades)}")
print()

# Calculate P&L
all_time_pnl = trades['pnl'].sum()
ytd_pnl = ytd_trades['pnl'].sum()

print(f"All-time P&L: ${all_time_pnl:,.2f}")
print(f"YTD P&L: ${ytd_pnl:,.2f}")
print()

# Webull comparison
webull_pnl = 900  # User reported value
diff = ytd_pnl - webull_pnl

print("=" * 60)
print("WEBULL COMPARISON")
print("=" * 60)
print(f"Our YTD P&L:        ${ytd_pnl:,.2f}")
print(f"Webull YTD P&L:     ${webull_pnl:,.2f}")
print(f"Difference:         ${diff:,.2f}")
print(f"Difference %:       {abs(diff)/abs(webull_pnl)*100:.1f}%")
print()

# Check if the difference could be fees
avg_fee_per_trade = abs(diff) / len(ytd_trades)
print(f"If difference is fees: ${avg_fee_per_trade:.2f} per trade")
print()

# Breakdown by direction
long_trades = ytd_trades[ytd_trades['direction'] == 'long']
short_trades = ytd_trades[ytd_trades['direction'] == 'short']

print("=" * 60)
print("BREAKDOWN BY DIRECTION")
print("=" * 60)
print(f"Long trades:  {len(long_trades):3d} → ${long_trades['pnl'].sum():,.2f}")
print(f"Short trades: {len(short_trades):3d} → ${short_trades['pnl'].sum():,.2f}")
print()

# Check for any anomalies
print("=" * 60)
print("ANOMALY CHECK")
print("=" * 60)

# Very large wins/losses
large_wins = ytd_trades[ytd_trades['pnl'] > 200]
large_losses = ytd_trades[ytd_trades['pnl'] < -200]

print(f"Trades with P&L > $200: {len(large_wins)}")
if len(large_wins) > 0:
    print(large_wins[['symbol', 'pnl', 'qty_closed', 'avg_entry', 'avg_exit']])
print()

print(f"Trades with P&L < -$200: {len(large_losses)}")
if len(large_losses) > 0:
    print(large_losses[['symbol', 'pnl', 'qty_closed', 'avg_entry', 'avg_exit']])
print()

# Monthly breakdown
ytd_trades['month'] = pd.to_datetime(ytd_trades['close_time']).dt.to_period('M')
monthly = ytd_trades.groupby('month')['pnl'].agg(['sum', 'count'])
print("=" * 60)
print("MONTHLY BREAKDOWN")
print("=" * 60)
print(monthly)
print()

print("=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)
print()
print("1. Check Webull's 'Realized P&L' specifically (not Total P&L)")
print("2. Verify Webull's trade count - is it 348 or different?")
print("3. Check if Webull includes:")
print("   - Dividends/interest")
print("   - Fees (would make it MORE negative)")
print("   - Partial fills as separate trades")
print("4. Export a fresh CSV with full date range")
print("5. Check Webull's cost basis method setting")
print()
print(f"Current difference: ${abs(diff):,.2f} ({abs(diff)/abs(webull_pnl)*100:.1f}%)")
print()

# Suggest next steps based on difference
if abs(diff) < 100:
    print("✅ Difference < $100 - likely rounding or fees")
elif abs(diff) < 500:
    print("⚠️  Difference $100-500 - check for missing trades or fees")
else:
    print("🚨 Difference > $500 - fundamental accounting mismatch")
    print("   Possible causes:")
    print("   - Different cost basis method")
    print("   - Missing/extra trades in CSV")
    print("   - Webull includes unrealized P&L")
    print("   - Date range mismatch")
