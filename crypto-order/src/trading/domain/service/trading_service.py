from typing import List
import logging
from ..model.order import OrderSide, Market


class TradingService:
    """Domain service for trading operations"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def find_best_market(self, markets: List[Market], side: OrderSide) -> Market:
        """Find the best market based on order side"""
        if not markets:
            raise ValueError("No markets available")

        valid_markets = [m for m in markets if m.is_price_valid()]
        if not valid_markets:
            raise ValueError("No valid prices available")

        if not all(m.symbol == valid_markets[0].symbol for m in valid_markets):
            raise ValueError(
                f"Markets have different symbols: {set(m.symbol for m in valid_markets)}"
            )

        if side == OrderSide.BUY:
            best_market = min(valid_markets, key=lambda m: m.best_ask.amount)
            self.logger.info(
                f"Best market for BUY {best_market.symbol}: {best_market.exchange_id} with ask {best_market.best_ask.amount}"
            )
        else:
            best_market = max(valid_markets, key=lambda m: m.best_bid.amount)
            self.logger.info(
                f"Best market for SELL {best_market.symbol}: {best_market.exchange_id} with bid {best_market.best_bid.amount}"
            )
        return best_market
