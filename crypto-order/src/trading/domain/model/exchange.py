from abc import ABC, abstractmethod
from .order import Order, Market, Symbol


class ExchangeAdapter(ABC):
    @abstractmethod
    async def get_market(self, symbol: Symbol) -> Market:
        pass

    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        pass
