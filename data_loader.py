"""
STEP 1: 数据基础层
支持真实CSV导入或高级拟真Mock数据（含4个市场周期：牛市→崩盘→底部震荡→复苏）
"""
import pandas as pd
import numpy as np
import os

class DataLoader:
    def __init__(self, start_date="2021-01-01", end_date="2024-06-01", csv_path=None):
        self.start_date = start_date
        self.end_date = end_date
        self.csv_path = csv_path

    def fetch_data(self):
        if self.csv_path and os.path.exists(self.csv_path):
            print(f"✅ Loading real data from {self.csv_path}")
            df = pd.read_csv(self.csv_path, index_col=0, parse_dates=True)
            return self._compute_features(df)
        return self._generate_mock_data()

    def _generate_mock_data(self):
        print(f"⚙️  Generating regime-based mock data: {self.start_date} → {self.end_date}")
        dates = pd.date_range(self.start_date, self.end_date, freq='D')
        n = len(dates)
        np.random.seed(42)

        # --- BTC价格：4个明确的牛熊周期 ---
        p1, p2, p3 = int(n*0.30), int(n*0.45), int(n*0.70)
        mu = np.zeros(n); sigma = np.zeros(n)
        mu[:p1] = 0.003;  sigma[:p1] = 0.025    # 牛市
        mu[p1:p2] = -0.005; sigma[p1:p2] = 0.045  # 崩盘
        mu[p2:p3] = 0.0005; sigma[p2:p3] = 0.020  # 底部震荡
        mu[p3:] = 0.002;  sigma[p3:] = 0.028    # 复苏

        returns = np.random.normal(mu, sigma)
        price = 30000 * np.cumprod(1 + returns)
        intraday_range = np.abs(returns) + np.random.exponential(0.008, n)
        high = price * (1 + intraday_range * 0.6)
        low = price * (1 - intraday_range * 0.4)

        # --- VIX：均值回归 + 崩盘时飙升 ---
        vix = np.zeros(n); vix[0] = 18
        vix_target = np.full(n, 18.0)
        vix_target[p1:p2] = 35; vix_target[p2:p3] = 22
        for i in range(1, n):
            vix[i] = vix[i-1] + 0.08*(vix_target[i] - vix[i-1]) + np.random.normal(0, 1.5)
        # VIX尖峰
        for d in np.random.choice(range(p1, p2), size=5, replace=False):
            vix[d] += np.random.uniform(10, 20)
        vix = np.clip(vix, 10, 80)

        # --- Funding Rate & OI: 基于历史模式的模拟 ---
        # 注意：原版使用未来收益注入"完美预测 Alpha"，存在前视偏差
        # 修正版：使用滞后相关性 + 随机扰动，更接近真实市场
        fr = np.random.normal(0.0001, 0.0003, n)
        oi = np.zeros(n); oi[0] = 5e9
        
        # 计算历史收益（不使用未来数据）
        hist_returns = pd.Series(price).pct_change(1).fillna(0).values
        
        for i in range(1, n):
            # OI 正常漂移
            drift = 0.001 if i < p1 else (-0.003 if i < p2 else 0.0005)
            oi[i] = oi[i-1] * (1 + drift + np.random.normal(0, 0.01))
            
            # Funding Rate 与过去 3 天收益弱相关（滞后关系，无前视偏差）
            if i >= 3:
                past_3d_return = (price[i-1] - price[i-4]) / price[i-4]
                # 过去涨 → FR 被推高（多头拥挤）
                fr[i] = fr[i-1] + past_3d_return * 0.001 + np.random.normal(0, 0.0002)
                # OI 与 FR 同向
                if abs(past_3d_return) > 0.03:
                    oi[i] = oi[i-1] * (1 + np.random.uniform(0.02, 0.08))
            else:
                fr[i] = fr[i-1] + np.random.normal(0, 0.0002)
        
        fr = np.clip(fr, -0.01, 0.01)
        oi = np.maximum(oi, 1e9)

        # --- Polymarket 概率：均值回归 + 偶发突变 ---
        # 注意：原版使用未来收益注入完美预测，存在前视偏差
        # 修正版：使用均值回归 + 随机事件驱动
        poly = np.zeros(n); poly[0] = 0.5
        for i in range(1, n):
            # 均值回归
            mean_revert = (0.5 - poly[i-1]) * 0.02
            # 随机扰动
            noise = np.random.normal(0, 0.03)
            # 偶发突变事件（约 2% 概率）
            if np.random.random() < 0.02:
                shock = np.random.choice([-0.15, 0.15])
            else:
                shock = 0
            poly[i] = np.clip(poly[i-1] + mean_revert + noise + shock, 0.02, 0.98)

        # --- 主观叙事评分 ---
        narrative = np.clip(np.random.normal(0, 0.3, n), -1, 1)

        df = pd.DataFrame({
            'open': np.roll(price, 1), 'high': high, 'low': low, 'close': price,
            'volume': np.random.lognormal(22, 0.5, n),
            'vix': vix, 'funding_rate': fr, 'oi': oi,
            'poly_prob': poly, 'narrative_score': narrative
        }, index=dates)
        df.iloc[0, df.columns.get_loc('open')] = 30000
        return self._compute_features(df)

    def _compute_features(self, df):
        """统一计算所有衍生特征"""
        df['returns'] = df['close'].pct_change()
        df['btc_vol_30d'] = df['returns'].rolling(30).std() * np.sqrt(365)

        # ATR (14天)
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift(1)).abs(),
            (df['low'] - df['close'].shift(1)).abs()
        ], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()

        # 20日高点回撤
        df['high_20d'] = df['high'].rolling(20).max()
        df['dd_from_20d_high'] = (df['close'] - df['high_20d']) / df['high_20d']

        # 价格动量
        df['ret_24h'] = df['close'].pct_change(1)
        df['sma_20'] = df['close'].rolling(20).mean()

        # 填充缺失列
        for col in ['funding_rate', 'oi', 'poly_prob', 'narrative_score', 'vix']:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        return df.dropna().copy()
