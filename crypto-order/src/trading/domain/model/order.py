from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from typing import Optional
from datetime import datetime


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    FAILED = "failed"


@dataclass(frozen=True)
class Price:
    amount: Decimal
    timestamp: datetime

    def __lt__(self, other: "Price") -> bool:
        return self.amount < other.amount

    def __gt__(self, other: "Price") -> bool:
        return self.amount > other.amount

    def __eq__(self, other: "Price") -> bool:
        return self.amount == other.amount


@dataclass(frozen=True)
class Symbol:
    """Value object representing a trading symbol"""

    base: str
    quote: str

    def __str__(self) -> str:
        return f"{self.base}{self.quote}"


@dataclass(frozen=True)
class Market:
    """
    Value object representing a snapshot of market data.
    A market is value object since
    - it doesn't need to track its history of changes.
    - Compared by its attributes.
    """

    exchange_id: str
    symbol: Symbol
    best_bid: Optional[Price]
    best_ask: Optional[Price]

    def is_price_valid(self) -> bool:
        return (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_bid < self.best_ask
        )


@dataclass
class Order:
    """Aggregate root representing a trading order"""

    id: str
    symbol: Symbol
    side: OrderSide
    quantity: Decimal
    status: OrderStatus
    created_at: datetime
    exchange_id: Optional[str] = None
    filled_price: Optional[Decimal] = None
    error: Optional[str] = None

    def fill(self, exchange_id: str, price: Decimal) -> None:
        self.status = OrderStatus.FILLED
        self.exchange_id = exchange_id
        self.filled_price = price

    def fail(self, error: str) -> None:
        self.status = OrderStatus.FAILED
        self.error = error
