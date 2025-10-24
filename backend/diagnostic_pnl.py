#!/usr/bin/env python3
"""
P&L Diagnostic Script
Compare our calculations with Webull dashboard
"""

from services.ingest import ingest_csvs
from services.accounting import AverageCostEngine
from services.metrics import filter_trades_ytd, MetricsCalculator
import pandas as pd

def main():
    # Load CSV
    print("Loading Webull CSV...")
    with open('../Webull_Orders_Records.csv', 'r') as f:
        csv = f.read()
    
    # Parse
    fills = ingest_csvs(equities_csv=csv, ytd_only=False)
    print(f"✓ Loaded {len(fills)} fills")
    print(f"  Date range: {fills['filled_time'].min()} to {fills['filled_time'].max()}")
    print()
    
    # Run accounting
    engine = AverageCostEngine()
    trades = engine.process_fills(fills)
    print(f"✓ Processed {len(trades)} completed round-trip trades")
    print()
    
    # All-time P&L
    all_time_pnl = trades['pnl'].sum()
    print(f"📊 ALL-TIME P&L: ${all_time_pnl:,.2f}")
    print()
    
    # YTD P&L
    ytd_trades = filter_trades_ytd(trades)
    ytd_pnl = ytd_trades['pnl'].sum()
    print(f"📊 YTD 2025 P&L (REALIZED ONLY): ${ytd_pnl:,.2f}")
    print(f"   Based on {len(ytd_trades)} trades closed in 2025")
    print()
    
    # Open positions
    open_pos = engine.get_open_positions()
    print(f"📊 OPEN POSITIONS: {len(open_pos)}")
    if len(open_pos) > 0:
        print()
        print("   Symbol  | Qty    | Avg Cost | Direction")
        print("   " + "-" * 45)
        for idx, pos in open_pos.iterrows():
            direction = "LONG " if pos['pos_qty'] > 0 else "SHORT"
            print(f"   {pos['symbol']:7s} | {abs(pos['pos_qty']):6.1f} | ${pos['avg_cost']:7.2f} | {direction}")
        print()
        print("   ⚠️  Unrealized P&L not calculated (need current prices)")
        print()
    
    # Breakdown
    print("=" * 60)
    print("COMPARISON WITH WEBULL")
    print("=" * 60)
    print()
    print(f"Our System (Realized Only):     ${ytd_pnl:,.2f}")
    print(f"Webull Dashboard:               $974.00  ← YOUR VALUE")
    print(f"Difference:                     ${974.00 - ytd_pnl:,.2f}")
    print()
    print("Possible explanations:")
    print("  1. Webull shows TOTAL P&L (Realized + Unrealized)")
    print(f"     → Unrealized would be: ${974.00 - ytd_pnl:,.2f}")
    print("  2. Webull includes dividends/interest")
    print("  3. Webull uses different accounting (FIFO vs Avg Cost)")
    print()
    
    # Win/Loss breakdown
    winners = ytd_trades[ytd_trades['pnl'] > 0]
    losers = ytd_trades[ytd_trades['pnl'] < 0]
    
    print("=" * 60)
    print("YTD TRADE BREAKDOWN")
    print("=" * 60)
    print()
    print(f"Winners: {len(winners):3d} trades → ${winners['pnl'].sum():,.2f}")
    print(f"Losers:  {len(losers):3d} trades → ${losers['pnl'].sum():,.2f}")
    print(f"         ─────────────────────────────")
    print(f"Net:     {len(ytd_trades):3d} trades → ${ytd_pnl:,.2f}")
    print()
    print(f"Win Rate: {len(winners) / len(ytd_trades) * 100:.1f}%")
    print()
    
    # Top winners and losers
    print("Top 5 Winners:")
    for idx, trade in winners.nlargest(5, 'pnl').iterrows():
        print(f"  {trade['symbol']:6s} ${trade['pnl']:7.2f}  ({trade['close_time'].strftime('%Y-%m-%d')})")
    print()
    
    print("Top 5 Losers:")
    for idx, trade in losers.nsmallest(5, 'pnl').iterrows():
        print(f"  {trade['symbol']:6s} ${trade['pnl']:7.2f}  ({trade['close_time'].strftime('%Y-%m-%d')})")
    print()
    
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print()
    print("1. Check Webull dashboard:")
    print("   - Look for 'Realized P&L' vs 'Total P&L' toggle")
    print("   - Check if $974 includes unrealized gains")
    print()
    print("2. If Webull shows realized P&L separately:")
    print("   - Compare it to our $" + f"{ytd_pnl:,.2f}")
    print("   - If they match → our calculation is CORRECT")
    print("   - If they don't → investigate specific trades")
    print()
    print("3. Check for:")
    print("   - Dividends/interest in Webull")
    print("   - Missing trades in CSV export")
    print("   - Different cost basis method (FIFO vs Avg Cost)")
    print()

if __name__ == "__main__":
    main()
