"""
交易所基类 - 定义所有交易所必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd


class ExchangeBase(ABC):
    """交易所抽象基类"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "base"

    @abstractmethod
    def get_name(self) -> str:
        """返回交易所名称"""

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str = '4H',
                    limit: int = 100) -> pd.DataFrame:
        """获取 K 线数据"""

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> dict:
        """获取实时行情"""

    @abstractmethod
    def fetch_funding_rate(self, symbol: str) -> float:
        """获取资金费率"""

    @abstractmethod
    def fetch_open_interest(self, symbol: str) -> float:
        """获取未平仓量"""

    @abstractmethod
    def place_order(self, symbol: str, side: str, size: float,
                    order_type: str = 'market', price: float = None,
                    lever: int = 1, reduce_only: bool = False) -> dict:
        """下单"""

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """撤单"""

    @abstractmethod
    def get_positions(self, symbol: str = None) -> List[dict]:
        """获取持仓"""

    @abstractmethod
    def get_balance(self, ccy: str = 'USDT') -> float:
        """获取余额"""

    @abstractmethod
    def get_account_summary(self) -> dict:
        """获取账户总览"""

    @abstractmethod
    def download_historical_data(self, symbol: str, start_date: str,
                                 end_date: str) -> pd.DataFrame:
        """下载历史数据"""

    def get_market_regime_indicators(self, symbol: str) -> dict:
        """获取市场状态判断所需指标"""
        df = self.fetch_ohlcv(symbol, timeframe='1d', limit=200)
        if df is None or len(df) < 50:
            return {}
        close = df['close'].values
        sma20 = pd.Series(close).rolling(20).mean().values[-1]
        sma50 = pd.Series(close).rolling(50).mean().values[-1]
        sma200 = pd.Series(close).rolling(200).mean().values[-1] if len(close) >= 200 else sma50
        returns = pd.Series(close).pct_change().dropna()
        vol = returns.tail(20).std()
        return {
            'price': close[-1],
            'sma20': sma20,
            'sma50': sma50,
            'sma200': sma200,
            'volatility': vol,
            'above_sma20': close[-1] > sma20,
            'above_sma50': close[-1] > sma50,
            'sma20_above_sma50': sma20 > sma50,
        }
