from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


# Points
# - Hides domain complexity so the depandants don't need to create domain models. e.g., symbol is str. side is str.
# - maintain invariant checks in the DTO class.


@dataclass(frozen=True)
class OrderDTO:
    """Data Transfer Object for orders"""

    symbol: str
    side: str
    quantity: Decimal
    exchange_id: Optional[str] = None
    order_id: Optional[str] = None
    status: Optional[str] = None
    filled_price: Optional[Decimal] = None
    error: Optional[str] = None

    def __post_init__(self):
        """Validate DTO fields after initialization"""
        if self.side.lower() not in ("buy", "sell"):
            raise ValueError(f"Side must be 'buy' or 'sell': {self.side}")

        if self.quantity <= Decimal("0"):
            raise ValueError("Quantity must be positive")
