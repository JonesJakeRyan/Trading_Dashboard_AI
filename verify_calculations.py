#!/usr/bin/env python3
"""
Verify P&L calculations for Webull data
"""
import pandas as pd
from collections import defaultdict

# Read the CSV
df = pd.read_csv('Webull_Orders_Records.csv')

# Filter filled orders only
df = df[df['Status'] == 'Filled'].copy()

# Clean price
df['Avg Price'] = df['Avg Price'].astype(str).str.replace('@', '').str.replace('$', '')
df['Avg Price'] = pd.to_numeric(df['Avg Price'], errors='coerce')
df['Filled'] = pd.to_numeric(df['Filled'], errors='coerce')

# Parse dates - strip timezone first
df['Filled Time'] = df['Filled Time'].astype(str).str.replace(r'\s+EDT$', '', regex=True).str.replace(r'\s+EST$', '', regex=True)
df['Filled Time'] = pd.to_datetime(df['Filled Time'], errors='coerce')
df = df.dropna(subset=['Filled Time', 'Avg Price', 'Filled'])
df = df.sort_values('Filled Time')

print(f"Total filled trades: {len(df)}")
print(f"\nDate range: {df['Filled Time'].min()} to {df['Filled Time'].max()}")

# Track positions per symbol
positions = defaultdict(list)
total_pnl = 0
symbol_pnl = defaultdict(float)

for _, row in df.iterrows():
    symbol = row['Symbol']
    qty = row['Filled']
    price = row['Avg Price']
    side = str(row['Side']).lower()
    
    if side == 'buy':
        positions[symbol].append({'qty': qty, 'price': price})
        
    elif side == 'short':
        positions[symbol].append({'qty': qty, 'price': price, 'short': True})
        
    elif side == 'sell':
        remaining = qty
        trade_pnl = 0
        
        while remaining > 0 and positions[symbol]:
            pos = positions[symbol][0]
            
            if pos['qty'] <= remaining:
                # Close entire position
                qty_close = pos['qty']
                if pos.get('short'):
                    pnl = (pos['price'] - price) * qty_close
                else:
                    pnl = (price - pos['price']) * qty_close
                
                trade_pnl += pnl
                remaining -= qty_close
                positions[symbol].pop(0)
            else:
                # Partial close
                qty_close = remaining
                if pos.get('short'):
                    pnl = (pos['price'] - price) * qty_close
                else:
                    pnl = (price - pos['price']) * qty_close
                
                trade_pnl += pnl
                positions[symbol][0]['qty'] -= qty_close
                remaining = 0
        
        symbol_pnl[symbol] += trade_pnl
        total_pnl += trade_pnl

print(f"\n{'='*60}")
print(f"TOTAL P&L: ${total_pnl:,.2f}")
print(f"{'='*60}")

print(f"\nPer-Symbol Breakdown (Top 10):")
print(f"{'Symbol':<10} {'P&L':>15} {'Trades':>10}")
print("-" * 40)

sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)
for symbol, pnl in sorted_symbols[:10]:
    num_trades = len(df[df['Symbol'] == symbol])
    print(f"{symbol:<10} ${pnl:>14,.2f} {num_trades:>10}")

# Check SERV specifically
print(f"\n{'='*60}")
print("SERV Detailed Trades:")
print(f"{'='*60}")
serv_df = df[df['Symbol'] == 'SERV'].copy()
for _, row in serv_df.iterrows():
    print(f"{row['Filled Time']}: {row['Side']:5} {row['Filled']:3.0f} @ ${row['Avg Price']:.2f}")
print(f"\nSERV Total P&L: ${symbol_pnl['SERV']:,.2f}")

# Open positions
print(f"\n{'='*60}")
print("Open Positions:")
print(f"{'='*60}")
for symbol, pos_list in positions.items():
    if pos_list:
        total_qty = sum(p['qty'] for p in pos_list)
        avg_price = sum(p['qty'] * p['price'] for p in pos_list) / total_qty
        print(f"{symbol}: {total_qty:.0f} shares @ avg ${avg_price:.2f}")
