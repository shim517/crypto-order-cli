import pytest
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict

# Add src directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.trading.domain.model.order import (
    Order,
    OrderSide,
    OrderStatus,
    Market,
    Symbol,
    Price,
)
from src.trading.domain.repository.market_repository import MarketRepository
# from src.trading.

# from trading.infrastructure.exchange.okx_adapter import OKXAdapter


@pytest.fixture
def symbol() -> Symbol:
    return Symbol(base="BTC", quote="USDT")


@pytest.fixture
def price() -> Price:
    return Price(amount=Decimal("50000.00"), timestamp=datetime.now())


@pytest.fixture
def market(symbol: Symbol, price: Price) -> Market:
    return Market(
        exchange_id="binance",
        symbol=symbol,
        best_bid=price,
        best_ask=Price(
            amount=price.amount + Decimal("10.00"), timestamp=price.timestamp
        ),
    )


@pytest.fixture
def order(symbol: Symbol) -> Order:
    return Order(
        id="test-order-id",
        symbol=symbol,
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        status=OrderStatus.PENDING,
        created_at=datetime.now(),
    )


@pytest.fixture
def exchange_configs() -> Dict[str, Dict[str, str]]:
    return {
        "binance": {
            "api_key": "test-api-key",
            "api_secret": "test-api-secret",
            "base_url": "https://api.binance.com",
        },
        "okx": {
            "api_key": "test-api-key",
            "api_secret": "test-api-secret",
            "base_url": "https://www.okx.com",
        },
    }


class MockMarketRepository(MarketRepository):
    async def get_all_markets(self, symbol: Symbol) -> list[Market]:
        return []

    async def update_market(self, market: Market) -> None:
        pass


@pytest.fixture
def mock_market_repository() -> MarketRepository:
    return MockMarketRepository()
