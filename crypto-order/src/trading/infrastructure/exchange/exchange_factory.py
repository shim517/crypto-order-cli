import logging
from .binance_adapter import BinanceAdapter
from .okx_adapter import OKXAdapter
from typing import Dict
from trading.domain.model.exchange import ExchangeAdapter


class ExchangeFactory:
    # NOTE: provides a single point for creating exchange instances implementing the "ExchangeAdapter" interface.
    @staticmethod
    def create(
        exchange_id: str, config: Dict[str, str], logger: logging.Logger
    ) -> ExchangeAdapter:
        if exchange_id == "binance":
            return BinanceAdapter(config, logger=logger)
        if exchange_id == "okx":
            return OKXAdapter(config, logger=logger)
        raise ValueError(f"Unknown exchange: {exchange_id}")

    @staticmethod
    def create_all(
        exchange_configs: Dict[str, Dict[str, str]], logger: logging.Logger
    ) -> Dict[str, ExchangeAdapter]:
        return {
            exchange_id: ExchangeFactory.create(exchange_id, config, logger)
            for exchange_id, config in exchange_configs.items()
        }
