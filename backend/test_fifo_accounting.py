#!/usr/bin/env python3
"""
Test FIFO accounting vs Average Cost
This might explain the $2,600 discrepancy with Webull
"""

from services.ingest import ingest_csvs
import pandas as pd
from datetime import datetime
from collections import deque

def fifo_accounting(fills):
    """
    Simple FIFO accounting implementation
    """
    positions = {}  # symbol -> deque of (price, qty, time)
    trades = []
    
    for idx, fill in fills.iterrows():
        symbol = fill['symbol']
        side = fill['side']
        qty = fill['qty']
        price = fill['price']
        time = fill['filled_time']
        
        if symbol not in positions:
            positions[symbol] = deque()
        
        if side in ['buy', 'cover']:
            # Opening or adding to long
            positions[symbol].append((price, qty, time, 'long'))
        
        elif side in ['sell', 'short']:
            # Check if closing or opening
            if len(positions[symbol]) > 0 and positions[symbol][0][3] == 'long':
                # Closing long position (FIFO)
                remaining = qty
                entry_times = []
                total_pnl = 0
                
                while remaining > 0 and len(positions[symbol]) > 0:
                    entry_price, entry_qty, entry_time, direction = positions[symbol][0]
                    
                    if direction != 'long':
                        break
                    
                    close_qty = min(remaining, entry_qty)
                    pnl = (price - entry_price) * close_qty
                    total_pnl += pnl
                    
                    if close_qty >= entry_qty:
                        positions[symbol].popleft()
                    else:
                        positions[symbol][0] = (entry_price, entry_qty - close_qty, entry_time, direction)
                    
                    remaining -= close_qty
                    if not entry_times:
                        entry_times.append(entry_time)
                
                if total_pnl != 0 or len(entry_times) > 0:
                    trades.append({
                        'symbol': symbol,
                        'pnl': total_pnl,
                        'close_time': time,
                        'entry_time': entry_times[0] if entry_times else time
                    })
                
                # If remaining, open short
                if remaining > 0:
                    positions[symbol].append((price, remaining, time, 'short'))
            else:
                # Opening short
                positions[symbol].append((price, qty, time, 'short'))
    
    return pd.DataFrame(trades)

# Load data
print("Loading CSV...")
with open('../Webull_Orders_Records.csv', 'r') as f:
    csv = f.read()

fills = ingest_csvs(equities_csv=csv, ytd_only=False)
print(f"Loaded {len(fills)} fills\\n")

# Run FIFO accounting
print("Running FIFO accounting...")
fifo_trades = fifo_accounting(fills)
fifo_pnl = fifo_trades['pnl'].sum() if len(fifo_trades) > 0 else 0

print(f"FIFO P&L: ${fifo_pnl:,.2f}")
print(f"FIFO Trades: {len(fifo_trades)}")
print()

# Compare to our average cost
from services.accounting import AverageCostEngine
engine = AverageCostEngine()
avg_trades = engine.process_fills(fills)
avg_pnl = avg_trades['pnl'].sum()

print(f"Average Cost P&L: ${avg_pnl:,.2f}")
print(f"Average Cost Trades: {len(avg_trades)}")
print()

print("=" * 60)
print(f"DIFFERENCE: ${fifo_pnl - avg_pnl:,.2f}")
print()

if abs(fifo_pnl - 900) < abs(avg_pnl - 900):
    print("✅ FIFO is CLOSER to Webull's $900!")
    print(f"   FIFO: ${fifo_pnl:,.2f} (diff: ${abs(fifo_pnl - 900):.2f})")
    print(f"   Avg Cost: ${avg_pnl:,.2f} (diff: ${abs(avg_pnl - 900):.2f})")
else:
    print("❌ Average Cost is closer to Webull's $900")
    print(f"   Avg Cost: ${avg_pnl:,.2f} (diff: ${abs(avg_pnl - 900):.2f})")
    print(f"   FIFO: ${fifo_pnl:,.2f} (diff: ${abs(fifo_pnl - 900):.2f})")
