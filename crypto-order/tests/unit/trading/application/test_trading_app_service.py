import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.trading.domain.model.order import (
    Order,
    OrderSide,
    OrderStatus,
    Market,
    Symbol,
    Price,
)
from src.trading.domain.service.trading_service import TradingService
from src.trading.domain.repository.market_repository import MarketRepository
from src.trading.domain.repository.exchange_repository import ExchangeRepository
from src.trading.application.service.trading_app_service import TradingAppService
from src.trading.application.dto.order_dto import OrderDTO

pytest_plugins = ("pytest_asyncio",)
logger = Mock()


class TestTradingAppOrderDTO:

    @pytest.mark.asyncio
    async def test_market_order_placement_with_invalid_side(self):
        with pytest.raises(ValueError):
            OrderDTO(symbol="BTCUSDT", side="invalid", quantity=Decimal("1.0"))

    @pytest.mark.asyncio
    async def test_market_order_placement_with_invalid_quantity(self):
        with pytest.raises(ValueError):
            OrderDTO(symbol="BTCUSDT", side="buy", quantity=Decimal("0.0"))


class TestTradingAppService:
    @pytest.fixture
    def mock_trading_service(self):
        return Mock(spec=TradingService)

    @pytest.fixture
    def mock_market_repository(self):
        repository = Mock(spec=MarketRepository)
        repository.get_all_markets = AsyncMock()
        repository.update_market = AsyncMock()
        return repository

    @pytest.fixture
    def mock_exchange_repository(self):
        repository = Mock(spec=ExchangeRepository)
        repository.place_order = AsyncMock()
        return repository

    @pytest.fixture
    def mock_exchanges(self):
        exchange = Mock()
        return {"binance": exchange, "okx": exchange}

    @pytest.fixture
    def app_service(
        self, mock_trading_service, mock_market_repository, mock_exchange_repository
    ):
        # NOTE: Mock all dependencies of TradingAppService to isolate the test.
        service = TradingAppService(
            trading_service=mock_trading_service,
            market_repository=mock_market_repository,
            exchange_repository=mock_exchange_repository,
            logger=logger,
        )
        return service

    @pytest.fixture
    def sample_markets(self) -> List[Market]:
        symbol = Symbol(base="BTC", quote="USDT")
        now = datetime.now()
        return [
            Market(
                exchange_id="binance",
                symbol=symbol,
                best_bid=Price(amount=Decimal("49990.00"), timestamp=now),
                best_ask=Price(amount=Decimal("50000.00"), timestamp=now),
            ),
            Market(
                exchange_id="okx",
                symbol=symbol,
                best_bid=Price(amount=Decimal("49995.00"), timestamp=now),
                best_ask=Price(amount=Decimal("50005.00"), timestamp=now),
            ),
        ]

    @pytest.mark.asyncio
    async def test_successful_market_order_placement(
        self,
        app_service,
        mock_market_repository,
        mock_trading_service,
        mock_exchange_repository,
        sample_markets,
    ):
        # Arrange
        order_dto = OrderDTO(symbol="BTCUSDT", side="buy", quantity=Decimal("1.0"))
        mock_market_repository.get_all_markets.return_value = sample_markets
        mock_trading_service.find_best_market.return_value = sample_markets[0]
        filled_order = Order(
            id="test-order-id",
            symbol=Symbol(base="BTC", quote="USDT"),
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            status=OrderStatus.FILLED,
            created_at=datetime.now(),
            exchange_id="binance",
            filled_price=Decimal("50000.00"),
        )
        mock_exchange_repository.place_order.return_value = filled_order

        # Act
        result = await app_service.place_market_order(order_dto)

        # Assert
        assert result.status == OrderStatus.FILLED.value
        assert result.exchange_id == "binance"
        assert result.order_id == "test-order-id"
        assert result.filled_price == Decimal("50000.00")
        assert result.error is None

    @pytest.mark.asyncio
    async def test_market_order_placement_with_no_markets(
        self,
        app_service,
        mock_trading_service,
    ):
        # Arrange
        order_dto = OrderDTO(symbol="BTCUSDT", side="buy", quantity=Decimal("1.0"))
        mock_trading_service.find_best_market.side_effect = ValueError(
            "No markets available"
        )

        # Act
        result = await app_service.place_market_order(order_dto)

        # Assert
        assert result.status == OrderStatus.FAILED.value
        assert "No markets available" in result.error

    @pytest.mark.asyncio
    async def test_market_order_placement_with_exchange_error(
        self,
        app_service,
        mock_exchange_repository,
    ):
        # Arrange
        order_dto = OrderDTO(symbol="BTCUSDT", side="buy", quantity=Decimal("1.0"))
        mock_exchange_repository.place_order.side_effect = Exception(
            "Exchange API error"
        )

        # Act
        result = await app_service.place_market_order(order_dto)

        # Assert
        assert result.status == OrderStatus.FAILED.value
        assert "Exchange API error" in result.error
