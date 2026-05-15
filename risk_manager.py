"""
STEP 11-14: 执行层 + Kelly-ATR仓位管理 + 止损/止盈 + 风控熔断
"""
import numpy as np


class KellyATRSizer:
    """
    Kelly 公式计算单笔风险预算，ATR止损距离反推最大仓位上限。
    不使用 norm.cdf(z) 直接当胜率；使用滚动历史胜率（更稳健）。
    position_cap = kelly_risk_budget / (atr_stop_pct)
    """
    def __init__(self, lookback: int = 60, atr_stop_mult: float = 2.0,
                 half_kelly: float = 0.5, max_leverage: float = 3.0):
        self.lookback      = lookback
        self.atr_stop_mult = atr_stop_mult
        self.half_kelly    = half_kelly
        self.max_leverage  = max_leverage

    def compute(self, recent_returns, atr: float, price: float) -> float:
        """返回 Kelly 约束后的最大可持仓比例（绝对值上限）"""
        if len(recent_returns) < 20 or atr <= 0 or price <= 0:
            return 1.0   # 数据不足，默认允许100%仓位


        wins   = recent_returns[recent_returns > 0]
        losses = recent_returns[recent_returns < 0]
        if len(wins) == 0 or len(losses) == 0:
            return 1.0


        win_rate    = len(wins) / len(recent_returns)
        avg_win     = wins.mean()
        avg_loss    = abs(losses.mean())
        payoff      = avg_win / max(avg_loss, 1e-8)

        # Kelly: f* = p - (1-p)/b，Half-Kelly 安全化
        kelly_f     = max(win_rate - (1 - win_rate) / payoff, 0) * self.half_kelly

        # ATR 止损距离换算为仓位上限
        stop_pct    = (self.atr_stop_mult * atr) / price
        if stop_pct > 0:
            position_cap = kelly_f / stop_pct
        else:
            position_cap = kelly_f

        return float(np.clip(position_cap, 0, self.max_leverage))


class StopLossManager:
    """
    STEP 13: ATR止损 / 分级止盈系统。
    关键：用当前K线的高低价触发，不能只看收盘价（防止未来函数）。
    """
    def __init__(self, atr_stop_mult: float = 2.0, tp_levels=None):
        self.atr_stop_mult = atr_stop_mult
        # [(ATR倍数, 平仓比例)]
        self.tp_levels = tp_levels or [
            (1.5, 0.50),   # 1.5倍ATR → 平50%
            (3.0, 0.30),   # 3倍ATR → 再平30%
            (5.0, 0.20),   # 5倍ATR → 清剩余20%
        ]

    def compute_levels(self, entry_price: float, atr: float, direction: float):
        """计算止损价 + 分级止盈价列表"""
        if atr <= 0 or entry_price <= 0:
            return None, []
        stop_dist = self.atr_stop_mult * atr
        if direction > 0:
            stop_price = entry_price - stop_dist
            tp_prices  = [(entry_price + m * atr, pct) for m, pct in self.tp_levels]
        elif direction < 0:
            stop_price = entry_price + stop_dist
            tp_prices  = [(entry_price - m * atr, pct) for m, pct in self.tp_levels]
        else:
            return None, []
        return stop_price, tp_prices

    def check_triggers(self, bar_high: float, bar_low: float, direction: float,
                       stop_price, tp_prices: list):
        """
        用当前K线高低价检查是否触发止损/止盈。
        返回 (trigger_type, trigger_price, close_pct)
        trigger_type: 'stop' | 'tp1' | 'tp2' | 'tp3' | None
        """
        if stop_price is None:
            return None, None, 0.0

        # 止损优先
        if direction > 0 and bar_low <= stop_price:
            return 'stop', stop_price, 1.0
        if direction < 0 and bar_high >= stop_price:
            return 'stop', stop_price, 1.0

        # 分级止盈（只触发最近一档）
        for idx, (tp_price, close_pct) in enumerate(tp_prices):
            if direction > 0 and bar_high >= tp_price:
                return f'tp{idx+1}', tp_price, close_pct
            if direction < 0 and bar_low <= tp_price:
                return f'tp{idx+1}', tp_price, close_pct

        return None, None, 0.0


class ExecutionSplitter:
    """
    STEP 11-12: 现货/合约执行拆分。
    正敞口 → 先买现货（0~100%），超过100%用合约做多加杠杆。
    负敞口 → 保留20%战略底仓，用合约做空对冲剩余风险。
    """
    STRATEGIC_BASE = 0.20

    @staticmethod
    def split(total_exposure: float) -> dict:
        result = {
            'total_delta':      round(total_exposure, 4),
            'spot_position':    0.0,
            'futures_position': 0.0,
            'action':           '',
        }
        if total_exposure > 0:
            result['spot_position'] = round(min(total_exposure, 1.0), 4)
            if total_exposure > 1.0:
                result['futures_position'] = round(total_exposure - 1.0, 4)
                result['action'] = (f"🚀 满仓现货 + "
                                    f"{result['futures_position']:.2f}x 多单合约")
            else:
                result['action'] = f"📈 持有 {result['spot_position']*100:.0f}% 现货"
        elif total_exposure < 0:
            base = ExecutionSplitter.STRATEGIC_BASE
            result['spot_position']    = base
            result['futures_position'] = round(total_exposure - base, 4)
            result['action'] = (f"🛡️ 战略底仓20% + "
                                f"{abs(result['futures_position']):.2f}x 空单对冲")
        else:
            result['action'] = "⚖️ 信号中性，观望"
        return result


class RiskCircuitBreaker:
    """
    STEP 14: 独立于信号系统的硬保护层。
    检查顺序：冷却期 → 最大回撤熔断 → VIX熔断 → 单日巨亏 → 分级降仓
    返回 (allow_trading: bool, position_multiplier: float, reason: str)
    """
    def __init__(self, config: dict = None):
        self.config = config or {
            'drawdown_tiers':    [(-0.03, 1.0), (-0.06, 0.75),
                                  (-0.10, 0.50), (-0.15, 0.25)],
            'max_drawdown_halt': -0.15,
            'max_daily_loss':    -0.05,
            'cooldown_days':      3,
            'vix_halt':          40,
        }
        self.cooldown_remaining = 0

    def _tier_multiplier(self, dd: float) -> float:
        """按回撤深度返回仓位乘数（tiers 从轻到重排列）"""
        for tier_dd, mult in self.config['drawdown_tiers']:
            if dd > tier_dd:
                return mult
        return 0.0

    def check(self, current_equity: float, max_equity: float,
              daily_pnl_pct: float, vix: float):
        dd = (current_equity - max_equity) / max_equity if max_equity > 0 else 0.0

        # 1. 冷却期
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            return False, 0.0, f"🧊 冷却期剩余 {self.cooldown_remaining + 1} 天"

        # 2. 最大回撤熔断
        if dd <= self.config['max_drawdown_halt']:
            self.cooldown_remaining = self.config['cooldown_days']
            return False, 0.0, f"🚨 最大回撤熔断 ({dd:.2%})"

        # 3. VIX 熔断
        if vix > self.config.get('vix_halt', 40):
            self.cooldown_remaining = self.config['cooldown_days']
            return False, 0.0, f"🚨 VIX熔断 ({vix:.1f})"

        # 4. 单日巨亏
        if daily_pnl_pct <= self.config['max_daily_loss']:
            self.cooldown_remaining = self.config['cooldown_days']
            return False, 0.0, f"🚨 单日亏损熔断 ({daily_pnl_pct:.2%})"

        # 5. 分级降仓
        mult = self._tier_multiplier(dd)
        return True, mult, "✅ 正常"
