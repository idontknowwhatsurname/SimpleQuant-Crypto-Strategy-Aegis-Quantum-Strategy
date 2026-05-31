"""交易所工厂 - 根据配置创建对应的交易所实例"""
from typing import Optional
from .base import ExchangeBase
from .okx import OKXExchange
from .binance import BinanceExchange
from .gate import GateExchange

SUPPORTED_EXCHANGES = {
    'okx': OKXExchange,
    'binance': BinanceExchange,
    'gate': GateExchange,
}


def create_exchange(name: str, config: dict = None) -> Optional[ExchangeBase]:
    """根据名称创建交易所实例"""
    cls = SUPPORTED_EXCHANGES.get(name.lower())
    if cls:
        return cls(config)
    raise ValueError(f"不支持的交易所: {name}，支持: {list(SUPPORTED_EXCHANGES.keys())}")


def list_supported_exchanges() -> list:
    """返回支持的交易所列表"""
    return list(SUPPORTED_EXCHANGES.keys())
