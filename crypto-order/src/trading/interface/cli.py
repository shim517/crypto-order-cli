import logging
import asyncio
from typing import List
import click
import functools
from decimal import Decimal

from trading.infrastructure.repository.exchange_repository_impl import (
    ExchangeRepositoryImpl,
)
from trading.domain.model.exchange import ExchangeAdapter
from trading.domain.repository.market_repository import MarketRepository
from trading.domain.service.trading_service import TradingService
from trading.application.service.trading_app_service import TradingAppService
from trading.application.dto.order_dto import OrderDTO
from trading.infrastructure.repository.market_repository_impl import (
    MarketRepositoryImpl,
)
from trading.infrastructure.exchange.exchange_factory import ExchangeFactory


def async_command(f):
    """Decorator to run async click commands"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--symbol", default="BTCUSDT", help="Trading symbol")
@click.option("--symbol-base", default="BTC", help="Trading base symbol")
@click.option("--symbol-quote", default="USDT", help="Trading quote symbol")
@click.option("--side", type=click.Choice(["buy", "sell"]), required=True)
@click.option("--quantity", type=float, required=True)
@click.option("--binance-key", envvar="BINANCE_API_KEY", help="Binance API key")
@click.option(
    "--binance-secret", envvar="BINANCE_API_SECRET", help="Binance API secret"
)
@click.option("--okx-key", envvar="OKX_API_KEY", help="OKX API key")
@click.option("--okx-secret", envvar="OKX_API_SECRET", help="OKX API secret")
@click.option(
    "--okx-api-passphrase", envvar="OKX_API_PASSPHRASE", help="OKX API passphrase"
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    help="Set the logging level",
)
@async_command
async def trade(
    symbol: str,
    side: str,
    quantity: float,
    binance_key: str,
    binance_secret: str,
    okx_key: str,
    okx_secret: str,
    okx_api_passphrase: str,
    log_level: str,
):
    """CLI interface for placing trades"""
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level.upper())

    logger.debug(
        f"Initializing trade: symbol={symbol}, side={side}, quantity={quantity}"
    )

    # Initialize application service
    exchange_configs = {
        "binance": {"api_key": binance_key, "api_secret": binance_secret},
        "okx": {
            "api_key": okx_key,
            "api_secret": okx_secret,
            "api_passphrase": okx_api_passphrase,
        },
    }
    exchanges: List[ExchangeAdapter] = ExchangeFactory.create_all(
        exchange_configs=exchange_configs, logger=logger
    )
    market_repository: MarketRepository = MarketRepositoryImpl(
        exchanges=exchanges,
        logger=logger,
    )
    trading_service = TradingService(logger=logger)

    exchange_repository = ExchangeRepositoryImpl(exchanges=exchanges, logger=logger)
    app_service = TradingAppService(
        trading_service=trading_service,
        market_repository=market_repository,
        exchange_repository=exchange_repository,
        logger=logger,
    )

    order_dto = OrderDTO(symbol=symbol, side=side, quantity=Decimal(str(quantity)))

    # Execute trade
    result = await app_service.place_market_order(order_dto)

    # Display result
    if result.status == "filled":
        click.echo(f"Order filled on {result.exchange_id} at {result.filled_price}")
    else:
        click.echo(f"Order failed: {result.error}")


if __name__ == "__main__":
    trade()
