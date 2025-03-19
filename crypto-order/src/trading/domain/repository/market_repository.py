from abc import ABC, abstractmethod
from typing import List
from ..model.order import OrderSide, Market, Symbol


# Interface for Market Repository
class MarketRepository(ABC):
    @abstractmethod
    async def get_all_markets(self, symbol: Symbol) -> List[Market]:
        pass
