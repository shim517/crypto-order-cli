import pytest
from decimal import Decimal
from datetime import datetime

from src.trading.domain.model.order import Symbol, Price, Market


class TestSymbol:
    def test_symbol_string_representation(self):
        symbol = Symbol(base="BTC", quote="USDT")
        assert str(symbol) == "BTCUSDT"

    @pytest.mark.parametrize(
        "symbol1,symbol2,expected",
        [
            pytest.param(
                Symbol(base="BTC", quote="USDT"), Symbol(base="BTC", quote="USDT"), True
            ),
            pytest.param(
                Symbol(base="BTC", quote="USDT"),
                Symbol(base="ETH", quote="USDT"),
                False,
            ),
        ],
    )
    def test_symbol_equality(self, symbol1, symbol2, expected):
        assert (symbol1 == symbol2) == expected


class TestPrice:

    @pytest.mark.parametrize(
        "price1,price2,expected",
        [
            pytest.param(Decimal("100.00"), Decimal("101.00"), True),
            pytest.param(Decimal("101.00"), Decimal("100.00"), False),
            pytest.param(Decimal("100.00"), Decimal("100.00"), False),
        ],
    )
    def test_price_comparison(self, price1, price2, expected):
        now = datetime.now()
        price1 = Price(amount=price1, timestamp=now)
        price2 = Price(amount=price2, timestamp=now)
        assert (price1 < price2) == expected

    def test_price_immutability(self):
        price = Price(amount=Decimal("100.00"), timestamp=datetime.now())
        with pytest.raises(AttributeError):
            price.amount = Decimal("200.00")


class TestMarket:
    def test_market_price_validity(self, symbol):
        now = datetime.now()
        market = Market(
            exchange_id="binance",
            symbol=symbol,
            best_bid=Price(amount=Decimal("100.00"), timestamp=now),
            best_ask=Price(amount=Decimal("101.00"), timestamp=now),
        )

        assert market.is_price_valid()

    def test_market_invalid_price_when_bid_higher_than_ask(self, symbol):
        now = datetime.now()
        market = Market(
            exchange_id="binance",
            symbol=symbol,
            best_bid=Price(amount=Decimal("101.00"), timestamp=now),
            best_ask=Price(amount=Decimal("100.00"), timestamp=now),
        )

        assert not market.is_price_valid()

    def test_market_invalid_price_when_prices_missing(self, symbol):
        market = Market(
            exchange_id="binance", symbol=symbol, best_bid=None, best_ask=None
        )

        assert not market.is_price_valid()
