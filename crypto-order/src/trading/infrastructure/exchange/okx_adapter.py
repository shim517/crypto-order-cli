# Read https://www.okx.com/docs-v5/en/#overview-demo-trading-services for demo.
import asyncio
import base64
import hmac
import hashlib
import json
import logging
import aiohttp
from decimal import Decimal
from datetime import datetime, timezone
import urllib.parse

from trading.domain.model.exceptions import MarketNotFoundException
from trading.domain.model.order import Order, Market, OrderSide
from trading.domain.model.order import Symbol
from trading.domain.model.order import OrderStatus
from trading.domain.model.order import Price
from trading.domain.model.exchange import ExchangeAdapter
from trading.domain.model.order import Market


class OKXAdapter(ExchangeAdapter):

    def __init__(self, config: dict, logger: logging.Logger):
        self.__api_key = config["api_key"]
        self.__api_secret = config["api_secret"]
        self.__api_passphrase = config["api_passphrase"]
        self.__is_simulated = config.get("is_simulated", True)
        self.__base_url = config.get("base_url", "https://www.okx.com")
        self.__logger = logger

    def __symbol_to_okx_inst_id(self, symbol: Symbol) -> str:
        return f"{symbol.base}-{symbol.quote}"

    def _generate_signature(self, timestamp, method, request_path, params) -> str:
        # https://www.okx.com/web3/build/docs/waas/rest-authentication#signature
        if method == "GET" and params:
            # For GET, parameters are appended as query string
            query_string = "?" + urllib.parse.urlencode(params)
            pre_hash = timestamp + method + request_path + query_string
        elif method == "POST" and params:
            # For POST, parameters are converted to JSON string
            pre_hash = timestamp + method + request_path + json.dumps(params)
        else:
            pre_hash = timestamp + method + request_path
        signature = hmac.new(
            self.__api_secret.encode("utf-8"), pre_hash.encode("utf-8"), hashlib.sha256
        ).digest()
        encoded_signature = base64.b64encode(signature).decode("utf-8")

        return encoded_signature

    def _map_okx_state_to_order_status(self, state: str) -> OrderStatus:
        # Map OKX order state to OrderStatus
        # See state in https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-details
        state_mapping = {
            "canceled": OrderStatus.FAILED,
            "live": OrderStatus.PENDING,
            "partially_filled": OrderStatus.PENDING,
            "filled": OrderStatus.FILLED,
            "mmp_canceled": OrderStatus.FAILED,
        }
        return state_mapping.get(state, OrderStatus.FAILED)

    async def get_market(self, symbol: Symbol) -> Market:
        # Top of the book: read https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-ticker
        async with aiohttp.ClientSession() as session:
            url = f"{self.__base_url}/api/v5/market/ticker"
            inst_id = self.__symbol_to_okx_inst_id(symbol=symbol)
            params = {"instId": inst_id}
            self.__logger.debug(f"Getting market data for {inst_id} from OKX")

            async with session.get(url, params=params) as response:
                self.__logger.debug(f"Response status: {response.status}")
                response.raise_for_status()
                _data = await response.json()
                if not (_data.get("code") == "0" and len(_data["data"]) > 0):
                    raise MarketNotFoundException(
                        f"Failed to get market data: {_data.get('msg')}"
                    )

                data = _data["data"][0]
                self.__logger.debug(f"Market data: {data}")

                return Market(
                    exchange_id="okx",
                    symbol=symbol,
                    best_bid=Price(
                        amount=Decimal(data["bidPx"]), timestamp=datetime.now()
                    ),
                    best_ask=Price(
                        amount=Decimal(data["askPx"]), timestamp=datetime.now()
                    ),
                )

    async def place_order(self, order):
        # place order API: https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-order
        async with aiohttp.ClientSession() as session:
            requeust_path = "/api/v5/trade/order"
            url = f"{self.__base_url}{requeust_path}"
            inst_id = self.__symbol_to_okx_inst_id(symbol=order.symbol)
            body = {
                "instId": inst_id,
                "tdMode": "cash",
                "side": "buy" if order.side == OrderSide.BUY else OrderSide.SELL,
                "ordType": "market",
                "sz": str(order.quantity),
            }
            self.__logger.debug(f"Placing order {body} on OKX")
            timestamp_iso = (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )
            headers = {
                "OK-ACCESS-KEY": self.__api_key,
                "OK-ACCESS-TIMESTAMP": timestamp_iso,
                "OK-ACCESS-PASSPHRASE": self.__api_passphrase,
                "OK-ACCESS-SIGN": self._generate_signature(
                    timestamp_iso, "POST", requeust_path, body
                ),
                "Content-Type": "application/json",  # POST requests need this header
            }
            if self.__is_simulated:
                headers["x-simulated-trading"] = "1"

            async with session.post(
                url, headers=headers, data=json.dumps(body)
            ) as response:
                self.__logger.debug(f"Response status: {response.status}")
                response.raise_for_status()
                _data = await response.json()
                if not (_data.get("code") == "0" and len(_data["data"]) > 0):
                    raise ValueError(f"Failed to place order: {_data.get('msg')}")

                data = _data["data"][0]
                self.__logger.debug(f"Order response: {data}")
                # NOTE: unlike Binance, create order API in OKX doesn't return the order status.
                await asyncio.sleep(0.5)
                # TODO: Error handling
                return await self.get_order_details(
                    order_id=data["ordId"], inst_id=inst_id
                )

    async def get_order_details(self, order_id: str, inst_id: str) -> Order:
        # https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-details
        async with aiohttp.ClientSession() as session:
            request_path = "/api/v5/trade/order"
            url = f"{self.__base_url}{request_path}"

            # Parameters for the request
            params = {"instId": inst_id, "ordId": order_id}

            # Get ISO timestamp
            timestamp = (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            )

            # Generate signature for GET request with params
            signature = self._generate_signature(timestamp, "GET", request_path, params)

            headers = {
                "OK-ACCESS-KEY": self.__api_key,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.__api_passphrase,
                "OK-ACCESS-SIGN": signature,
            }

            # Add simulated trading header if enabled
            if self.__is_simulated:
                headers["x-simulated-trading"] = "1"

            try:
                async with session.get(url, headers=headers, params=params) as response:
                    self.__logger.debug(f"Response status: {response.status}")
                    data = await response.json()
                    self.__logger.debug(f"Response: {data}")
                    response.raise_for_status()

                    # Check if the request was successful
                    if data.get("code") == "0" and len(data["data"]) > 0:
                        order_data = data["data"][0]

                        # Parse the symbol from instId
                        symbol_parts = order_data["instId"].split("-")
                        symbol = Symbol(base=symbol_parts[0], quote=symbol_parts[1])

                        # Determine order side
                        side = (
                            OrderSide.BUY
                            if order_data["side"] == "buy"
                            else OrderSide.SELL
                        )

                        status = self._map_okx_state_to_order_status(
                            order_data.get("state", "")
                        )

                        # cTime is unix timestamp format in milliseconds, e.g. 1597026383085
                        created_time = datetime.fromtimestamp(
                            int(order_data.get("cTime", "0")) / 1000
                        )

                        return Order(
                            id=order_data["ordId"],
                            symbol=symbol,
                            side=side,
                            quantity=Decimal(order_data.get("sz", "0")),
                            status=status,
                            created_at=created_time,
                            exchange_id="okx",
                            filled_price=(
                                Decimal(order_data.get("avgPx", "0"))
                                if order_data.get("avgPx")
                                else None
                            ),
                        )
                    else:
                        error_msg = f"Failed to get order details: {data.get('msg', 'Unknown error')}"
                        self.__logger.error(error_msg)
                        raise Exception(error_msg)

            except Exception as e:
                self.__logger.error(f"Error getting order details: {str(e)}")
                raise e
