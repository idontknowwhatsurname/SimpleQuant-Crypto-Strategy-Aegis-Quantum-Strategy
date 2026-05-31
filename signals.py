"""
STEP 2-8: 四层信号引擎
L1 宏观(35%) | L2 链上(40%) | L3 预测市场(15%) | L4 叙事(10%)
"""
import pandas as pd
import numpy as np


class Layer1MacroEngine:
    """L1 宏观层（35%）：VIX Z-Score，VIX越低越看多（负号取反）"""
    def compute(self, df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        df['vix_mean'] = df['vix'].rolling(window).mean()
        df['vix_std']  = df['vix'].rolling(window).std().replace(0, 1e-8)
        # VIX 高 → 宏观悲观 → l1_z 为负
        df['l1_z'] = -((df['vix'] - df['vix_mean']) / df['vix_std'])
        return df


class Layer2OnchainEngine:
    """
    L2 链上结构（40%）：Funding Rate Z-Score + OI 背离三条件共振。
    做空条件1: z_fr > 0.5（多头极度拥挤，阈值从2.0下调，适配上限0.0003的费率）
    做空条件2: 价格跌 + OI异常放大 + 费率为正（派发）
    做多条件:  对称反向
    l2_z 连续化：方向由 l2_signal 决定，幅度由 |z_fr| + |z_oi| 加权给出
    """
    def __init__(self, window: int = 14, z_fr_thresh: float = 0.5,
                 z_oi_thresh: float = 1.0):
        self.window      = window
        self.z_fr_thresh = z_fr_thresh
        self.z_oi_thresh = z_oi_thresh

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        w = self.window

        # — Funding Rate Z-Score — (修复 z_fr median=0 导致的 std 极小值爆炸问题)
        fr_roll     = df['funding_rate'].rolling(w)
        fr_std      = fr_roll.std().replace(0, np.nan).fillna(0.0001) # 设置最小方差保护
        df['z_fr_raw']  = (df['funding_rate'] - fr_roll.mean()) / fr_std
        # EMA smoothing to reduce noise
        df['z_fr'] = df['z_fr_raw'].ewm(span=5, adjust=False).mean()

        # — OI 变化率 Z-Score —
        df['oi_change'] = df['oi'].pct_change()
        oi_roll         = df['oi_change'].rolling(w)
        oi_std          = oi_roll.std().replace(0, np.nan).fillna(0.001)
        df['z_oi_raw']      = (df['oi_change'] - oi_roll.mean()) / oi_std
        # EMA smoothing for OI Z-Score
        df['z_oi'] = df['z_oi_raw'].ewm(span=5, adjust=False).mean()

        # — 三条件共振 → 离散方向信号 —
        df['l2_signal'] = 0
        short_c1 = df['z_fr'] > self.z_fr_thresh
        short_c2 = ((df['ret_24h'] < -0.02) &
                    (df['z_oi']   > self.z_oi_thresh) &
                    (df['funding_rate'] > 0))
        long_c1  = df['z_fr'] < -self.z_fr_thresh
        long_c2  = ((df['ret_24h'] > 0.02) &
                    (df['z_oi']   > self.z_oi_thresh) &
                    (df['funding_rate'] < 0))
        df.loc[short_c1 | short_c2, 'l2_signal'] = -1
        df.loc[long_c1  | long_c2,  'l2_signal'] =  1
                # 连续化 L2 Z-Score 计算，使用平滑后的 z_fr 与 z_oi
        fr_contrib = -df['z_fr'] * 1.5
        oi_contrib = df['z_oi'].abs() * df['l2_signal'] * 2.0
        df['l2_z'] = fr_contrib * 0.6 + oi_contrib * 0.4
        return df
class Layer3PolymarketEngine:
    """L3 预测市场（15%）：不看概率绝对值，看概率突变的 Z-Score"""
    def compute(self, df: pd.DataFrame,
                delta_window: int = 3, z_window: int = 14) -> pd.DataFrame:
        # Ensure poly_prob exists; if missing, fill with neutral 0.5 probability
        if 'poly_prob' not in df.columns:
            df['poly_prob'] = 0.5
        df['poly_delta'] = df['poly_prob'].diff(delta_window).fillna(0)
        roll = df['poly_delta'].rolling(z_window)
        # 修复 poly_prob 全为0.5导致 poly_delta=0、l3_z=NaN 的问题，设置 std 底限
        poly_std = roll.std().replace(0, np.nan).fillna(0.01)
        df['l3_z'] = (df['poly_delta'] - roll.mean()) / poly_std
        return df


class SignalAggregator:
    """
    STEP 8-10: 聚合 + L4同向激活 + tanh映射 + 目标波动率对齐 + 动态回调因子
    返回 (target_exposure, raw_z)
    """
    def __init__(self, target_vol: float = 0.50, config: dict = None, base_weights: dict = None):
        default_weights = {'L1': 0.35, 'L2': 0.40, 'L3': 0.15, 'L4': 0.10}
        self.base_weights = base_weights if base_weights is not None else default_weights
        self.dynamic_weighting = True
        self.weight_alpha = 0.5
        self.weights = self.base_weights.copy()
        self.recent_z_buffer = []
        self.target_vol = target_vol
        self.config = config or {
            'vix_circuit_breaker': 40,
            'vix_risk_threshold': 30,
            'vix_risk_multiplier': 0.3,
            'pullback_long': {'severe': (-0.12, 0.35),
                             'moderate': (-0.08, 0.60),
                             'mild': (-0.02, 1.10)},
            'pullback_short': {'severe': (-0.10, 0.45),
                              'moderate': (-0.06, 0.70),
                              'mild': (-0.02, 1.05)}
        }

    def _pullback_factor(self, direction: float, dd: float, vix: float) -> float:
        c = self.config
        if direction > 0:
            if vix > c['vix_risk_threshold']:
                return c['vix_risk_multiplier']
            if dd < c['pullback_long']['severe'][0]:
                return c['pullback_long']['severe'][1]
            if dd < c['pullback_long']['moderate'][0]:
                return c['pullback_long']['moderate'][1]
            if dd < c['pullback_long']['mild'][0]:
                return c['pullback_long']['mild'][1]
        elif direction < 0:
            if dd < c['pullback_short']['severe'][0]:
                return c['pullback_short']['severe'][1]
            if dd < c['pullback_short']['moderate'][0]:
                return c['pullback_short']['moderate'][1]
            if dd > c['pullback_short']['mild'][0]:
                return c['pullback_short']['mild'][1]
            return 0.90
        return 1.0

    def compute(self, l1_z: float, l2_z: float, l3_z: float, l4_z: float,
                vix: float, btc_vol: float, dd_from_high: float):
        c = self.config

        # VIX 熔断
        if vix > c['vix_circuit_breaker']:
            return 0.0, 0.0

        risk_mult = c['vix_risk_multiplier'] if vix > c['vix_risk_threshold'] else 1.0

        # STEP 8: L4 同向激活（前三层都朝同一方向才启用叙事层）
        signs    = [np.sign(l1_z), np.sign(l2_z), np.sign(l3_z)]
        l4_active = l4_z if (all(s > 0 for s in signs) or
                              all(s < 0 for s in signs)) else 0.0

        # 更新最近的 Z‑score 缓冲区（用于动态加权）
        self.recent_z_buffer.append((l1_z, l2_z, l3_z))
        if len(self.recent_z_buffer) > 100:
            self.recent_z_buffer.pop(0)

        # 若开启动态加权，则根据最近窗口的 Z‑score 波动重新计算权重
        if self.dynamic_weighting:
            recent_window = 30
            if len(self.recent_z_buffer) >= recent_window:
                arr = np.array(self.recent_z_buffer[-recent_window:])
                # 计算每层 Z‑score 的波动幅度（绝对值的标准差）
                vol_factors = np.std(np.abs(arr), axis=0)
                # 根据波动放大基础权重 (1 + alpha * volatility)
                scaled = {
                    k: self.base_weights[k] * (1 + self.weight_alpha * vf)
                    for k, vf in zip(['L1', 'L2', 'L3'], vol_factors)
                }
                total = sum(scaled.values()) + self.base_weights['L4']
                self.weights = {k: v / total for k, v in scaled.items()}
                self.weights['L4'] = self.base_weights['L4'] / total
            else:
                self.weights = self.base_weights.copy()
        else:
            self.weights = self.base_weights.copy()

        # STEP 9: 加权聚合（使用可能已经更新的 self.weights）
        raw_z    = (self.weights['L1'] * l1_z +
                    self.weights['L2'] * l2_z +
                    self.weights['L3'] * l3_z +
                    self.weights['L4'] * l4_active)
        strength = np.tanh(raw_z)          # 映射到 [-1, 1]

        # STEP 10: 回调因子 + 目标波动率对齐
        pb         = self._pullback_factor(np.sign(strength), dd_from_high, vix)
        vol_scalar = self.target_vol / max(btc_vol, 0.20)

        return strength * vol_scalar * risk_mult * pb, raw_z
