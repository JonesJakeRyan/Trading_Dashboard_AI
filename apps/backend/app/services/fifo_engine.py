"""
FIFO (First-In-First-Out) matching engine for calculating realized P&L.

Supports both:
- Long positions: BUY → SELL
- Short positions: SELL → BUY (sell first, buy later to close)

Uses dual-queue FIFO logic per symbol.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict, deque

from app.models.trade import NormalizedTrade, ClosedLot

logger = logging.getLogger(__name__)


class FIFOEngine:
    """
    FIFO matching engine for calculating realized P&L.
    
    Maintains separate queues for:
    - Long positions (opened by BUY, closed by SELL)
    - Short positions (opened by SELL, closed by BUY)
    """
    
    def __init__(self):
        # Per-symbol queues: {symbol: deque of (trade, remaining_qty)}
        self.long_queues: Dict[str, deque] = defaultdict(deque)
        self.short_queues: Dict[str, deque] = defaultdict(deque)
        
        # Closed lots generated
        self.closed_lots: List[ClosedLot] = []
    
    def process_trades(self, trades: List[NormalizedTrade]) -> List[ClosedLot]:
        """
        Process a list of trades and generate closed lots.
        
        Args:
            trades: List of NormalizedTrade objects, sorted by executed_at ASC
        
        Returns:
            List of ClosedLot objects with realized P&L
        """
        logger.info(f"Processing {len(trades)} trades for FIFO matching")
        
        # Reset state
        self.long_queues.clear()
        self.short_queues.clear()
        self.closed_lots.clear()
        
        # Process each trade in chronological order
        for trade in trades:
            self._process_trade(trade)
        
        logger.info(
            f"FIFO matching complete - generated {len(self.closed_lots)} closed lots"
        )
        
        return self.closed_lots
    
    def _process_trade(self, trade: NormalizedTrade):
        """Process a single trade through FIFO matching"""
        symbol = trade.symbol
        quantity = Decimal(str(trade.quantity))
        
        if trade.side == "BUY":
            # BUY can close SHORT positions or open LONG positions
            remaining = self._match_against_queue(
                trade=trade,
                quantity=quantity,
                queue=self.short_queues[symbol],
                position_type="SHORT"
            )
            
            # Any remaining quantity opens a new LONG position
            if remaining > 0:
                self.long_queues[symbol].append((trade, remaining))
                logger.debug(
                    f"Opened LONG position: {symbol} {remaining}@{trade.price}"
                )
        
        elif trade.side == "SELL":
            # SELL can close LONG positions or open SHORT positions
            remaining = self._match_against_queue(
                trade=trade,
                quantity=quantity,
                queue=self.long_queues[symbol],
                position_type="LONG"
            )
            
            # Any remaining quantity opens a new SHORT position
            if remaining > 0:
                self.short_queues[symbol].append((trade, remaining))
                logger.debug(
                    f"Opened SHORT position: {symbol} {remaining}@{trade.price}"
                )
    
    def _match_against_queue(
        self,
        trade: NormalizedTrade,
        quantity: Decimal,
        queue: deque,
        position_type: str
    ) -> Decimal:
        """
        Match a trade against an existing position queue (FIFO).
        
        Args:
            trade: The closing trade
            quantity: Quantity to match
            queue: Queue of open positions to match against
            position_type: "LONG" or "SHORT"
        
        Returns:
            Remaining unmatched quantity
        """
        remaining = quantity
        
        while remaining > 0 and queue:
            open_trade, open_qty = queue[0]
            
            # Match quantity (take minimum of remaining and open)
            match_qty = min(remaining, open_qty)
            
            # Create closed lot
            closed_lot = self._create_closed_lot(
                open_trade=open_trade,
                close_trade=trade,
                quantity=match_qty,
                position_type=position_type
            )
            self.closed_lots.append(closed_lot)
            
            # Update quantities
            remaining -= match_qty
            open_qty -= match_qty
            
            # Remove from queue if fully matched
            if open_qty == 0:
                queue.popleft()
            else:
                # Update remaining quantity in queue
                queue[0] = (open_trade, open_qty)
            
            logger.debug(
                f"Matched {position_type}: {trade.symbol} "
                f"{match_qty}@{open_trade.price}→{trade.price} "
                f"P&L=${closed_lot.realized_pnl}"
            )
        
        return remaining
    
    def _create_closed_lot(
        self,
        open_trade: NormalizedTrade,
        close_trade: NormalizedTrade,
        quantity: Decimal,
        position_type: str
    ) -> ClosedLot:
        """
        Create a closed lot with calculated realized P&L.
        
        P&L calculation:
        - LONG: (close_price - open_price) * quantity
        - SHORT: (open_price - close_price) * quantity
        """
        open_price = Decimal(str(open_trade.price))
        close_price = Decimal(str(close_trade.price))
        
        # Calculate P&L based on position type
        if position_type == "LONG":
            # Long: profit when sell price > buy price
            pnl = (close_price - open_price) * quantity
        else:  # SHORT
            # Short: profit when buy price < sell price
            pnl = (open_price - close_price) * quantity
        
        # Round to 2 decimal places (cents)
        pnl = pnl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return ClosedLot(
            account_id=open_trade.account_id,
            symbol=open_trade.symbol,
            position_type=position_type,
            open_trade_id=open_trade.id,
            open_quantity=quantity,
            open_price=open_price,
            open_executed_at=open_trade.executed_at,
            close_trade_id=close_trade.id,
            close_quantity=quantity,
            close_price=close_price,
            close_executed_at=close_trade.executed_at,
            realized_pnl=pnl
        )
    
    def get_open_positions(self) -> Dict[str, Dict]:
        """
        Get current open positions (not yet closed).
        
        Returns:
            Dict with symbol as key and position info as value
        """
        positions = {}
        
        # Long positions
        for symbol, queue in self.long_queues.items():
            if queue:
                total_qty = sum(qty for _, qty in queue)
                avg_price = sum(
                    Decimal(str(trade.price)) * qty
                    for trade, qty in queue
                ) / total_qty if total_qty > 0 else Decimal('0')
                
                positions[symbol] = {
                    "type": "LONG",
                    "quantity": total_qty,
                    "average_price": avg_price.quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    ),
                    "lots": len(queue)
                }
        
        # Short positions
        for symbol, queue in self.short_queues.items():
            if queue:
                total_qty = sum(qty for _, qty in queue)
                avg_price = sum(
                    Decimal(str(trade.price)) * qty
                    for trade, qty in queue
                ) / total_qty if total_qty > 0 else Decimal('0')
                
                if symbol in positions:
                    # Both long and short positions exist (unusual but possible)
                    positions[f"{symbol}_SHORT"] = {
                        "type": "SHORT",
                        "quantity": total_qty,
                        "average_price": avg_price.quantize(
                            Decimal('0.01'), rounding=ROUND_HALF_UP
                        ),
                        "lots": len(queue)
                    }
                else:
                    positions[symbol] = {
                        "type": "SHORT",
                        "quantity": total_qty,
                        "average_price": avg_price.quantize(
                            Decimal('0.01'), rounding=ROUND_HALF_UP
                        ),
                        "lots": len(queue)
                    }
        
        return positions
