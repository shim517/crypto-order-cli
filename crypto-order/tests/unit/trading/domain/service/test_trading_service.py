import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock

from src.trading.domain.service.trading_service import TradingService
from src.trading.domain.model.order import OrderSide, Market, Symbol, Price

logger = Mock()


class TestTradingService:

    @pytest.mark.parametrize(
        ["markets", "side", "expected"],
        [
            pytest.param(
                [
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("100.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("101.00"), timestamp=datetime.now()
                        ),
                    )
                ],
                OrderSide.BUY,
                Market(
                    exchange_id="binance",
                    symbol=Symbol(base="BTC", quote="USDT"),
                    best_bid=Price(amount=Decimal("100.00"), timestamp=datetime.now()),
                    best_ask=Price(amount=Decimal("101.00"), timestamp=datetime.now()),
                ),
            ),
            pytest.param(
                [
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("100.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("101.00"), timestamp=datetime.now()
                        ),
                    ),
                    Market(
                        exchange_id="okx",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("90.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("102.00"), timestamp=datetime.now()
                        ),
                    ),
                ],
                OrderSide.BUY,
                Market(
                    exchange_id="binance",
                    symbol=Symbol(base="BTC", quote="USDT"),
                    best_bid=Price(amount=Decimal("100.00"), timestamp=datetime.now()),
                    best_ask=Price(amount=Decimal("101.00"), timestamp=datetime.now()),
                ),
            ),
            pytest.param(
                [
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("100.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("101.00"), timestamp=datetime.now()
                        ),
                    )
                ],
                OrderSide.SELL,
                Market(
                    exchange_id="binance",
                    symbol=Symbol(base="BTC", quote="USDT"),
                    best_bid=Price(amount=Decimal("100.00"), timestamp=datetime.now()),
                    best_ask=Price(amount=Decimal("101.00"), timestamp=datetime.now()),
                ),
            ),
        ],
    )
    def test_find_best_market(self, markets, side, expected):
        service = TradingService(logger=logger)
        assert service.find_best_market(markets, side) == expected

    def test_find_best_market_no_markets(self):
        service = TradingService(logger=logger)
        with pytest.raises(ValueError):
            service.find_best_market(markets=[], side=OrderSide.BUY)

    def test_find_best_market_no_valid_prices(self):
        service = TradingService(logger=logger)
        with pytest.raises(ValueError):
            service.find_best_market(
                [
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=None,
                        best_ask=None,
                    )
                ],
                side=OrderSide.BUY,
            )

    def test_find_best_market_different_symbol_markets(self):
        service = TradingService(logger=logger)
        with pytest.raises(ValueError):
            service.find_best_market(
                [
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="BTC", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("100.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("101.00"), timestamp=datetime.now()
                        ),
                    ),
                    Market(
                        exchange_id="binance",
                        symbol=Symbol(base="ETH", quote="USDT"),
                        best_bid=Price(
                            amount=Decimal("100.00"), timestamp=datetime.now()
                        ),
                        best_ask=Price(
                            amount=Decimal("101.00"), timestamp=datetime.now()
                        ),
                    ),
                ],
                side=OrderSide.BUY,
            )
