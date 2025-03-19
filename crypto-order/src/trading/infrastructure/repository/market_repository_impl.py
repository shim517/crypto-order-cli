import asyncio
from typing import List, Dict, Optional, Type
import logging

from trading.domain.model.exceptions import MarketNotFoundException
from trading.domain.model.exchange import ExchangeAdapter
from trading.infrastructure.exchange.exchange_factory import ExchangeFactory
from trading.domain.repository.market_repository import MarketRepository
from trading.domain.model.order import Market, Symbol


class MarketRepositoryImpl(MarketRepository):

    def __init__(
        self,
        exchanges: Dict[str, ExchangeAdapter],
        logger: logging.Logger,
    ):
        self.exchanges = exchanges
        self.logger = logger

    async def _get_market_safe(
        self, exchange: ExchangeAdapter, symbol
    ) -> Optional[Market]:
        try:
            return await exchange.get_market(symbol)
        except MarketNotFoundException as e:
            self.logger.warning(
                f"Market not found on {exchange}: {str(e)}",
            )
            return None
        except Exception as e:
            self.logger.error(
                f"Error getting market data from {exchange}: {str(e)}",
                exc_info=True,
            )
            return None

    async def get_all_markets(self, symbol: Symbol) -> List[Market]:
        markets = []
        self.logger.debug(f"Getting markets for symbol {symbol}")
        self.logger.debug(f"Exchanges: {self.exchanges}")
        # Run all exchange queries concurrently
        results = await asyncio.gather(
            *[
                self._get_market_safe(exchange, symbol)
                for exchange in self.exchanges.values()
            ]
        )

        # Filter out None results (from failed requests)
        markets = [market for market in results if market is not None]
        self.logger.debug(f"All markets: {markets}")

        return markets
