from abc import ABC, abstractmethod
import logging
from typing import Dict, List

from trading.domain.model.exchange import ExchangeAdapter
from trading.domain.model.order import Order, Market
from trading.domain.repository.exchange_repository import ExchangeRepository


# Interface for Exchange Repository
class ExchangeRepositoryImpl(ExchangeRepository):
    def __init__(self, exchanges: Dict[str, ExchangeAdapter], logger: logging.Logger):
        self.exchanges = exchanges
        self.logger = logger

    async def place_order(self, order: Order) -> Order:
        exchange = self.exchanges.get(order.exchange_id)
        if exchange is None:
            raise ValueError(f"Exchange {order.exchange_id} not found")
        order = await exchange.place_order(order)
        return order
