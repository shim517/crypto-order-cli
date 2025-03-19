from enum import Enum
import hmac
import hashlib
import logging
import time
from typing import Dict

import aiohttp
from decimal import Decimal
from datetime import datetime

from trading.domain.model.order import Order, Market
from trading.domain.model.order import Symbol
from trading.domain.model.order import OrderStatus
from trading.domain.model.order import Price
from trading.domain.model.exchange import ExchangeAdapter
from trading.domain.model.exceptions import MarketNotFoundException

# It is recommended to use a small recvWindow of 5000 or less! The max cannot go beyond 60,000!
# Ref: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#signed-endpoint-examples-for-post-apiv3order


class BinanceAdapter(ExchangeAdapter):

    class OrderStatus(Enum):
        """
        Order status is defined on https://developers.binance.com/docs/binance-spot-api-docs/enums#order-status-status.
        """

        NEW = "NEW"
        PENDING_NEW = "PENDING_NEW"
        PARTIALLY_FILLED = "PARTIALLY_FILLED"
        FILLED = "FILLED"
        CANCELED = "CANCELED"
        PENDING_CANCEL = "PENDING_CANCEL"
        REJECTED = "REJECTED"
        EXPIRED = "EXPIRED"
        EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"

    def __init__(self, config: Dict[str, str], logger: logging.Logger):
        self.__api_key = config["api_key"]
        self.__api_secret = config["api_secret"]
        self.__base_url = config.get("base_url", "https://testnet.binance.vision")
        self.__logger = logger

    def __map_order_status(self, status: "BinanceAdapter.OrderStatus") -> OrderStatus:
        mapping = {
            self.OrderStatus.NEW: OrderStatus.PENDING,
            self.OrderStatus.PENDING_NEW: OrderStatus.PENDING,
            self.OrderStatus.PARTIALLY_FILLED: OrderStatus.PENDING,
            self.OrderStatus.FILLED: OrderStatus.FILLED,
            self.OrderStatus.CANCELED: OrderStatus.FAILED,
            self.OrderStatus.PENDING_CANCEL: OrderStatus.PENDING,
            self.OrderStatus.REJECTED: OrderStatus.FAILED,
            self.OrderStatus.EXPIRED: OrderStatus.FAILED,
            self.OrderStatus.EXPIRED_IN_MATCH: OrderStatus.FAILED,
        }
        return mapping.get(status, OrderStatus.FAILED)

    def _generate_signature(self, query_string: str) -> str:
        # NOTE: See https://developers.binance.com/docs/binance-spot-api-docs/rest-api/endpoint-security-type for more details
        return hmac.new(
            self.__api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def get_market(self, symbol: Symbol) -> Market:
        async with aiohttp.ClientSession() as session:
            url = f"{self.__base_url}/api/v3/ticker/bookTicker"
            params = {"symbol": str(symbol)}
            self.__logger.debug(f"Getting market data for {symbol} from Binance")

            async with session.get(url, params=params) as response:
                self.__logger.debug(f"Response status: {response.status}")
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    if e.status == 400:
                        raise MarketNotFoundException(f"Market {symbol} not found")
                    raise e

                data = await response.json()
                self.__logger.debug(f"Market data: {data}")

                return Market(
                    exchange_id="binance",
                    symbol=symbol,
                    best_bid=Price(
                        amount=Decimal(data["bidPrice"]), timestamp=datetime.now()
                    ),
                    best_ask=Price(
                        amount=Decimal(data["askPrice"]), timestamp=datetime.now()
                    ),
                )

    async def place_order(self, order: Order) -> Order:
        endpoint = "/api/v3/order"
        timestamp = int(time.time() * 1000)
        params = {
            "symbol": str(order.symbol),
            "side": order.side.value.upper(),
            "type": "MARKET",
            "quantity": order.quantity,
            "timestamp": timestamp,
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        self.__logger.debug(f"Query string: {query_string}")

        # NOTE: Generate signature and add to params.
        # Ref: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/endpoint-security-type
        params["signature"] = self._generate_signature(query_string)

        # NOTE: Put the API key in X-MBX-APIKEY header.
        # Ref: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/endpoint-security-type
        headers = {"X-MBX-APIKEY": self.__api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.__base_url}{endpoint}", headers=headers, data=params
                ) as response:
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        if e.status == 400:
                            self.__logger.info(f"Order failed: {await response.text()}")
                            return Order(
                                id=order.id,
                                symbol=order.symbol,
                                side=order.side,
                                quantity=order.quantity,
                                status=OrderStatus.FAILED,
                                created_at=datetime.now(),
                                exchange_id="binance",
                            )
                        raise e

                    data = await response.json()
                    self.__logger.debug(f"Order response: {data}")
                    fills = data.get("fills", [])
                    filled_price = (
                        Decimal(fills[0]["price"]) if len(fills) > 0 else None
                    )

                    return Order(
                        id=data["orderId"],
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        status=self.__map_order_status(
                            self.OrderStatus(data["status"])
                        ),
                        filled_price=filled_price,
                        created_at=datetime.now(),
                        exchange_id="binance",
                    )
        except Exception as e:
            self.__logger.error(f"Error placing Binance market order: {str(e)}")
            raise
