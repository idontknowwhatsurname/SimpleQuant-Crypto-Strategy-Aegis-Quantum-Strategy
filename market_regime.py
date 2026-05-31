"""
市场状态识别模块 (Market Regime Detector)
识别当前市场处于什么状态，自动切换策略类型

输出:
    regime: "bull_market" / "bear_market" / "range_market" / "volatile"
    confidence: 0.0 - 1.0
"""
import numpy as np
import pandas as pd


class MarketRegimeDetector:
    """
    市场状态识别器
    基于多时间框架的价格行为和波动率特征判断市场状态
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        # 趋势判断参数
        self.sma_fast = self.config.get('sma_fast', 20)
        self.sma_slow = self.config.get('sma_slow', 50)
        self.sma_trend = self.config.get('sma_trend', 200)
        # 波动率判断参数
        self.vol_window = self.config.get('vol_window', 20)
        self.vol_high_thresh = self.config.get('vol_high_thresh', 0.04)  # 日波动率 > 4% = 高波动
        self.vol_low_thresh = self.config.get('vol_low_thresh', 0.015)   # 日波动率 < 1.5% = 低波动
        # 状态平滑
        self.history = []

    def detect(self, df: pd.DataFrame) -> dict:
        """
        识别市场状态

        Args:
            df: 包含 'close', 'high', 'low', 'volume' 的 DataFrame

        Returns:
            {
                'regime': str,
                'confidence': float,
                'trend': float,       # 趋势方向 (-1 ~ 1)
                'volatility': float,  # 波动率
                'strength': float,    # 趋势强度
                'detail': str         # 判断理由
            }
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # 计算均线
        sma_fast = pd.Series(close).rolling(self.sma_fast).mean().values
        sma_slow = pd.Series(close).rolling(self.sma_slow).mean().values
        sma_trend = pd.Series(close).rolling(self.sma_trend).mean().values

        # 当前值
        current_price = close[-1]
        current_sma_fast = sma_fast[-1]
        current_sma_slow = sma_slow[-1]
        current_sma_trend = sma_trend[-1] if not np.isnan(sma_trend[-1]) else current_sma_slow

        # 波动率
        daily_returns = pd.Series(close).pct_change().dropna()
        volatility = daily_returns.tail(self.vol_window).std()

        # 趋势方向
        trend_direction = np.sign(current_price / current_sma_trend - 1) if current_sma_trend > 0 else 0
        trend_strength = abs(current_price / current_sma_trend - 1)
        trend_aligned = (current_sma_fast > current_sma_slow) == (current_price > current_sma_trend)

        # 趋势强度评分 (0~1)
        if trend_aligned:
            trend_force = min(trend_strength / 0.3, 1.0)
        else:
            trend_force = 0.0

        # 价格在均线之间的位置
        if current_sma_fast > current_sma_slow:
            # 多头排列
            above_fast = current_price > current_sma_fast
            above_slow = current_price > current_sma_slow
            above_trend = current_price > current_sma_trend
            bullish_count = sum([above_fast, above_slow, above_trend])
            bearish_count = 0
        else:
            # 空头排列
            above_fast = current_price > current_sma_fast
            above_slow = current_price > current_sma_slow
            above_trend = current_price > current_sma_trend
            bullish_count = sum([above_fast, above_slow, above_trend])
            bearish_count = 3 - bullish_count

        # 波动率状态
        vol_ratio = volatility / self.vol_low_thresh if self.vol_low_thresh > 0 else 1.0

        # 状态判断
        if bullish_count >= 2 and trend_force > 0.3 and vol_ratio < 2.0:
            regime = "bull_market"
            confidence = min(trend_force, 1.0) * 0.7 + (vol_ratio < 1.5) * 0.3
            detail = "多头排列，趋势向上，波动率正常"
        elif bearish_count >= 2 and trend_force > 0.3:
            regime = "bear_market"
            confidence = min(trend_force, 1.0) * 0.7 + (vol_ratio > 1.0) * 0.3
            detail = "空头排列，趋势向下，波动率较高"
        elif vol_ratio > 2.5:
            regime = "volatile"
            confidence = min(vol_ratio / 5.0, 1.0)
            detail = "高波动环境，无明显趋势方向"
        else:
            regime = "range_market"
            confidence = max(0.5, 1.0 - trend_force * 2)
            detail = "价格在均线附近震荡，无明显趋势"

        # 记录历史
        result = {
            'regime': regime,
            'confidence': round(confidence, 2),
            'trend': round(trend_direction * trend_force, 2),
            'volatility': round(volatility, 4),
            'strength': round(trend_force, 2),
            'detail': detail,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
        }
        self.history.append(result)
        return result

    def get_recommended_strategy(self, regime: str) -> str:
        """根据市场状态推荐策略类型"""
        recommendations = {
            "bull_market": "趋势跟踪策略: 回调买入，移动止盈",
            "bear_market": "防御策略: 降低仓位，只做反弹或空仓",
            "range_market": "网格策略: 高抛低吸，严格止损",
            "volatile": "观望策略: 减小仓位，等待趋势明朗",
        }
        return recommendations.get(regime, "正常策略")

    def get_position_multiplier(self, regime: str, confidence: float) -> float:
        """根据市场状态返回仓位乘数"""
        multipliers = {
            "bull_market": 1.0,
            "bear_market": 0.3,
            "range_market": 0.6,
            "volatile": 0.4,
        }
        base = multipliers.get(regime, 0.5)
        return base * confidence
