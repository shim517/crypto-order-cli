from typing import List
import uuid
import traceback
import logging
from datetime import datetime

from trading.domain.service.trading_service import TradingService
from trading.domain.model.order import Market, Order, OrderSide, Symbol
from trading.domain.repository.market_repository import MarketRepository
from trading.application.dto.order_dto import OrderDTO
from trading.domain.model.order import OrderStatus
from trading.domain.repository.exchange_repository import ExchangeRepository


class TradingAppService:
    """Application service for handling trading operations"""

    def __init__(
        self,
        trading_service: TradingService,
        market_repository: MarketRepository,
        exchange_repository: ExchangeRepository,
        logger: logging.Logger,
    ):
        self.trading_service = trading_service
        self.market_repository = market_repository
        self.exchange_repository = exchange_repository
        self.logger = logger

    async def place_market_order(self, order_dto: OrderDTO) -> OrderDTO:
        """Place a market order"""
        try:
            # Create domain objects from simple DTO.
            symbol = Symbol(base=order_dto.symbol[:3], quote=order_dto.symbol[3:])

            order = Order(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side=OrderSide(order_dto.side.lower()),
                quantity=order_dto.quantity,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
            )

            # Get market data
            markets: List[Market] = await self.market_repository.get_all_markets(symbol)
            self.logger.debug(f"Markets: {markets}")

            # Find best market
            best_market = self.trading_service.find_best_market(markets, order.side)
            order.exchange_id = best_market.exchange_id
            # Place order on selected exchange
            result = await self.exchange_repository.place_order(order)

            # Return DTO
            return OrderDTO(
                symbol=str(result.symbol),
                side=result.side.value,
                quantity=result.quantity,
                exchange_id=result.exchange_id,
                order_id=result.id,
                status=result.status.value,
                filled_price=result.filled_price,
                error=result.error,
            )

        except Exception as e:
            self.logger.info(traceback.format_exc())
            self.logger.error(f"An error occurred: {str(e)}")
            # Handle errors and return failed order DTO
            dto = OrderDTO(
                symbol=order_dto.symbol,
                side=order_dto.side,
                quantity=order_dto.quantity,
                status=OrderStatus.FAILED.value,
                error=str(e),
            )
            return dto
