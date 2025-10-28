"""
Quick test to validate win rate calculation against the creator CSV data.
"""
from app.database import SessionLocal
from app.models.metrics import Aggregate
from app.models.trade import ClosedLot

def test_win_rate():
    db = SessionLocal()
    try:
        # Get aggregate data
        aggregate = db.query(Aggregate).filter(Aggregate.account_id.is_(None)).first()
        
        if not aggregate:
            print("❌ No aggregate data found. Run ingest first.")
            return
        
        print("=" * 60)
        print("WIN RATE VALIDATION")
        print("=" * 60)
        
        # Get all closed lots
        closed_lots = db.query(ClosedLot).filter(ClosedLot.account_id.is_(None)).all()
        
        print(f"\n📊 Aggregate Metrics:")
        print(f"  Total Lots Closed: {aggregate.total_lots_closed}")
        print(f"  Winning Lots: {aggregate.winning_lots}")
        print(f"  Losing Lots: {aggregate.losing_lots}")
        print(f"  Win Rate: {aggregate.win_rate:.2f}%")
        print(f"  Total Realized P&L: ${aggregate.total_realized_pnl:,.2f}")
        
        # Manual calculation
        winning_count = 0
        losing_count = 0
        zero_count = 0
        
        for lot in closed_lots:
            if lot.realized_pnl > 0:
                winning_count += 1
            elif lot.realized_pnl < 0:
                losing_count += 1
            else:
                zero_count += 1
        
        total_lots = len(closed_lots)
        manual_win_rate = (winning_count / total_lots * 100) if total_lots > 0 else 0
        
        print(f"\n🔍 Manual Verification:")
        print(f"  Total Lots: {total_lots}")
        print(f"  Winners: {winning_count}")
        print(f"  Losers: {losing_count}")
        print(f"  Break-even: {zero_count}")
        print(f"  Calculated Win Rate: {manual_win_rate:.2f}%")
        
        # Check if they match
        if abs(aggregate.win_rate - manual_win_rate) < 0.01:
            print(f"\n✅ Win rate matches! {aggregate.win_rate:.2f}%")
        else:
            print(f"\n❌ Win rate mismatch!")
            print(f"   Database: {aggregate.win_rate:.2f}%")
            print(f"   Manual: {manual_win_rate:.2f}%")
        
        # Show some sample winning and losing trades
        print(f"\n📈 Sample Winning Trades (first 5):")
        winners = [lot for lot in closed_lots if lot.realized_pnl > 0][:5]
        for lot in winners:
            print(f"  {lot.symbol}: ${lot.realized_pnl:.2f} ({lot.quantity} shares)")
        
        print(f"\n📉 Sample Losing Trades (first 5):")
        losers = [lot for lot in closed_lots if lot.realized_pnl < 0][:5]
        for lot in losers:
            print(f"  {lot.symbol}: ${lot.realized_pnl:.2f} ({lot.quantity} shares)")
        
        print("\n" + "=" * 60)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_win_rate()
