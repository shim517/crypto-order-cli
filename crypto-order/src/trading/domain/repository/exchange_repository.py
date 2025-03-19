from abc import ABC, abstractmethod
from typing import List
from ..model.order import OrderSide, Market, Order


# Interface for Exchange Repository
class ExchangeRepository(ABC):
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        pass
