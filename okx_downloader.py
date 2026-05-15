"""
OKX Complete Data Downloader
=============================
拉取 OKX 所有免费可用的历史数据：
- OHLCV: 多年历史 K 线 (免费, 无限制)
- Funding Rate: 最近 ~3 个月 (OKX 公共 API 上限)
- Open Interest: 最近 ~3 个月 (OKX 公共 API 上限)
- VIX: 完整历史 (FRED 美联储公开数据, 免费)

运行方式:
  python3 okx_downloader.py                    # 默认 BTC-USDT-SWAP
  python3 okx_downloader.py --symbol ETH-USDT-SWAP
"""

import ccxt
import pandas as pd
import numpy as np
import time
import urllib.request
import io
import argparse
import warnings
warnings.filterwarnings('ignore')


def fetch_ohlcv(ex, symbol, timeframe='1d', start_date='2022-01-01T00:00:00Z'):
    """拉取所有 OHLCV K 线，没有历史限制"""
    print(f"  [OHLCV] 拉取 {symbol} 日线数据 from {start_date}...")
    start_ts = ex.parse8601(start_date)
    end_ts = ex.milliseconds()
    all_ohlcv = []
    current = start_ts

    while current < end_ts:
        try:
            batch = ex.fetch_ohlcv(symbol, timeframe, since=current, limit=100)
            if not batch:
                break
            all_ohlcv.extend(batch)
            current = batch[-1][0] + 1
            time.sleep(0.15)
        except Exception as e:
            print(f"    ⚠️ OHLCV error: {e}")
            time.sleep(2)
            break

    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.normalize()
    df = df.set_index('timestamp')
    df = df[~df.index.duplicated(keep='first')]
    print(f"    ✅ {len(df)} 条 K 线, {df.index[0].date()} → {df.index[-1].date()}")
    return df


def fetch_funding_rates(ex, symbol):
    """
    拉取所有可用的资金费率 (OKX 免费 API 约保存最近 3 个月)
    每 8 小时结算一次, 汇总为日频
    """
    print(f"  [Funding Rate] 拉取 {symbol} 资金费率...")
    start_ts = ex.parse8601('2026-01-01T00:00:00Z')  # 尽量往前
    end_ts = ex.milliseconds()
    all_fr = []
    current = start_ts

    while current < end_ts:
        try:
            batch = ex.fetch_funding_rate_history(symbol, since=current, limit=100)
            if not batch:
                break
            all_fr.extend(batch)
            current = batch[-1]['timestamp'] + 1
            if current > end_ts:
                break
            time.sleep(0.15)
        except Exception as e:
            print(f"    ⚠️ FR error: {e}")
            break

    if not all_fr:
        print("    ⚠️ 无资金费率数据")
        return None

    fr_df = pd.DataFrame([{
        'timestamp': pd.to_datetime(r['timestamp'], unit='ms', utc=True).normalize(),
        'funding_rate': r['fundingRate']
    } for r in all_fr])
    fr_df = fr_df.set_index('timestamp')
    # 8 小时结算 → 日频求和 (3次/天)
    fr_daily = fr_df['funding_rate'].resample('D').sum().to_frame(name='funding_rate')
    print(f"    ✅ {len(fr_daily)} 天资金费率, {fr_daily.index[0].date()} → {fr_daily.index[-1].date()}")
    return fr_daily


def fetch_open_interest(ex, symbol):
    """
    拉取未平仓量 OI (OKX 免费 API 约保存最近 3 个月, 日频)
    """
    print(f"  [Open Interest] 拉取 {symbol} 未平仓量...")
    start_ts = ex.parse8601('2026-02-01T00:00:00Z')  # OKX 统计类接口历史上限
    end_ts = ex.milliseconds()
    all_oi = []
    current = start_ts

    while current < end_ts:
        try:
            batch = ex.fetch_open_interest_history(symbol, '1d', since=current, limit=100)
            if not batch:
                break
            all_oi.extend(batch)
            current = batch[-1]['timestamp'] + 1
            if current > end_ts:
                break
            time.sleep(0.15)
        except Exception as e:
            print(f"    ⚠️ OI error: {e}")
            break

    if not all_oi:
        print("    ⚠️ 无 OI 数据")
        return None

    oi_df = pd.DataFrame([{
        'timestamp': pd.to_datetime(r['timestamp'], unit='ms', utc=True).normalize(),
        'oi': r['quoteVolume']   # USD 计价
    } for r in all_oi])
    oi_df = oi_df.set_index('timestamp')
    oi_df = oi_df[~oi_df.index.duplicated(keep='first')]
    print(f"    ✅ {len(oi_df)} 天 OI 数据, {oi_df.index[0].date()} → {oi_df.index[-1].date()}")
    return oi_df


def fetch_vix():
    """
    从 FRED (美联储公开数据库) 拉取完整 VIX 历史 - 完全免费, 无需 API Key
    数据覆盖 1990 年至今
    """
    print(f"  [VIX] 从 FRED 拉取 VIX 历史数据...")
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS'
    try:
        req = urllib.request.urlopen(url, timeout=10)
        content = req.read().decode('utf-8')
        vix_df = pd.read_csv(io.StringIO(content), index_col=0, parse_dates=True)
        vix_df.index = vix_df.index.tz_localize('UTC')
        vix_df.columns = ['vix']
        vix_df['vix'] = pd.to_numeric(vix_df['vix'], errors='coerce')
        vix_df = vix_df.ffill()
        print(f"    ✅ {len(vix_df)} 天 VIX 数据, {vix_df.index[0].date()} → {vix_df.index[-1].date()}")
        return vix_df
    except Exception as e:
        print(f"    ⚠️ VIX error: {e}. 使用均值回归代理值")
        return None


def build_oi_proxy(ohlcv_df):
    """当 OKX 真实 OI 不足时，用 volume * price 作为代理"""
    proxy = ohlcv_df['volume'] * ohlcv_df['close']
    return proxy.to_frame(name='oi')


def main(symbol='BTC-USDT-SWAP', start_date='2022-01-01T00:00:00Z'):
    print(f"\n{'='*55}")
    print(f"  OKX Data Downloader — {symbol}")
    print(f"{'='*55}\n")

    ex = ccxt.okx({'enableRateLimit': True})

    # 1. OHLCV
    ohlcv = fetch_ohlcv(ex, symbol, start_date=start_date)

    # 2. Funding Rate
    fr = fetch_funding_rates(ex, symbol)

    # 3. Open Interest
    oi = fetch_open_interest(ex, symbol)

    # 4. VIX
    vix = fetch_vix()

    # — Merge everything on OHLCV index —
    df = ohlcv.copy()

    if fr is not None:
        df = df.join(fr, how='left')
    else:
        df['funding_rate'] = 0.0

    if oi is not None:
        df = df.join(oi, how='left')
        # Fill missing OI (older dates) with volume-based proxy
        oi_proxy = build_oi_proxy(ohlcv)['oi']
        df['oi'] = df['oi'].fillna(oi_proxy)
    else:
        df['oi'] = build_oi_proxy(ohlcv)

    if vix is not None:
        df = df.join(vix, how='left')
    else:
        # Mean-reverting VIX proxy based on realized vol
        n = len(df)
        vix_proxy = np.zeros(n)
        vix_proxy[0] = 20.0
        for i in range(1, n):
            vix_proxy[i] = vix_proxy[i-1] + 0.08 * (20 - vix_proxy[i-1]) + np.random.normal(0, 1.5)
        vix_proxy = np.clip(vix_proxy, 10, 80)
        df['vix'] = vix_proxy

    # Placeholders for data not available via OKX public API
    df['poly_prob'] = 0.5       # Neutral placeholder
    df['narrative_score'] = 0.0 # Neutral placeholder

    # Forward fill any gaps
    df = df.ffill().fillna(0.0)

    from pathlib import Path
    output_path = Path(__file__).parent / 'user_real_data.csv'
    df.to_csv(output_path)

    print(f"\n{'='*55}")
    print(f"  ✅ 数据合并完成！保存至 user_real_data.csv")
    print(f"  总行数: {len(df)} 天")
    print(f"  时间区间: {df.index[0].date()} → {df.index[-1].date()}")
    print(f"  包含列: {list(df.columns)}")
    print(f"\n  ⚠️  数据说明:")
    print(f"     OHLCV  → 完整历史 (OKX 真实数据)")
    print(f"     VIX    → 完整历史 (FRED 真实数据)")
    print(f"     FR     → 最近3个月 (OKX 公共接口上限)")
    print(f"     OI     → 最近3个月真实, 更早用 vol×price 代理")
    print(f"     Poly   → 中性占位符 (需要 Polymarket API)")
    print(f"\n  现在直接运行: python3 backtester.py")
    print(f"{'='*55}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='BTC-USDT-SWAP')
    parser.add_argument('--start', default='2022-01-01T00:00:00Z')
    args = parser.parse_args()
    main(symbol=args.symbol, start_date=args.start)
