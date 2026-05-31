"""
Aegis Quantum Strategy - 实盘交易引擎 (v2.0)
集成多交易所、AI路由、复盘分析、自动进化、多通道通知
"""
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict

from signals import Layer1MacroEngine, Layer2OnchainEngine, Layer3PolymarketEngine, SignalAggregator
from risk_manager import KellyATRSizer, StopLossManager, RiskCircuitBreaker
from market_regime import MarketRegimeDetector
from order_executor import OrderExecutor
from real_portfolio import RealPortfolioMonitor
from notify.notifier import NotifyManager
from config_loader import load_config
from exchange.factory import create_exchange, list_supported_exchanges
from ai_router import AIRouter
from evolution import EvolutionManager


class TradingEngine:
    """
    v2.0 实盘交易引擎

    循环流程:
    1. 获取最新行情数据 (多交易所)
    2. AI 辅助分析 (多模型路由)
    3. 计算四层信号
    4. 识别市场状态
    5. 风控检查
    6. Kelly-ATR 仓位计算
    7. 执行交易 (多交易所)
    8. 推送通知 (多通道)
    9. 自动进化 (每 N 笔交易)
    """

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        self.interval = self.config.get('engine', {}).get('interval_seconds', 300)

        # 1. 多交易所初始化
        self.exchanges = {}
        exchange_configs = self.config.get('exchange', {})
        if 'name' in exchange_configs:
            names = [exchange_configs['name']]
        else:
            names = exchange_configs.get('names', ['okx'])
        for name in names:
            try:
                self.exchanges[name] = create_exchange(name, exchange_configs.get(name, exchange_configs))
            except Exception as e:
                print(f"⚠️ 交易所 {name} 初始化失败: {e}")

        primary_exchange = self.exchanges.get(names[0]) if self.exchanges else None

        # 2. 交易执行器
        self.executor = OrderExecutor(
            api_key=self.config.get('exchange', {}).get('api_key'),
            secret=self.config.get('exchange', {}).get('secret'),
            passphrase=self.config.get('exchange', {}).get('passphrase'),
            demo=self.config.get('exchange', {}).get('demo', False),
        )

        # 3. 持仓监控
        self.portfolio = RealPortfolioMonitor(
            use_api=bool(self.config.get('exchange', {}).get('api_key'))
        )

        # 4. 多通道通知
        self.notifier = NotifyManager(self.config.get('notify', {}))

        # 5. AI 路由器
        ai_config = self.config.get('ai', {})
        self.ai_router = AIRouter(ai_config) if ai_config.get('api_keys', {}).get('deepseek') else None

        # 6. 自动进化管理器
        evo_config = self.config.get('evolution', {})
        self.evolution = EvolutionManager(evo_config)

        # 信号引擎
        self.l1 = Layer1MacroEngine()
        self.l2 = Layer2OnchainEngine()
        self.l3 = Layer3PolymarketEngine()
        self.aggregator = SignalAggregator(
            target_vol=self.config.get('strategy', {}).get('target_vol', 0.50)
        )

        # 风控
        self.kelly = KellyATRSizer(
            half_kelly=self.config.get('position', {}).get('half_kelly', 0.5),
            max_leverage=self.config.get('position', {}).get('max_leverage', 3.0),
        )
        self.stop_mgr = StopLossManager(
            atr_stop_mult=self.config.get('position', {}).get('atr_stop_mult', 2.0)
        )
        self.circuit_breaker = RiskCircuitBreaker({
            'vix_halt': self.config.get('risk', {}).get('vix_halt', 40),
            'max_drawdown_halt': self.config.get('risk', {}).get('max_drawdown_halt', -0.15),
            'max_daily_loss': self.config.get('risk', {}).get('max_daily_loss', -0.05),
            'cooldown_days': self.config.get('risk', {}).get('cooldown_days', 3),
        })
        self.regime_detector = MarketRegimeDetector()

        # 状态
        self.running = False
        self.current_equity = 10000.0
        self.current_exposure = 0.0
        self.recent_returns = []
        self.data_buffer = []
        self.trade_count = 0

    def fetch_market_data(self) -> Optional[pd.DataFrame]:
        """获取最新市场数据（从 OKX API）"""
        try:
            import urllib.request
            import json
            symbol = self.config.get('data', {}).get('symbol', 'BTC-USDT-SWAP')
            url = f'https://www.okx.com/api/v5/market/candles?instId={symbol}&bar=4H&limit=50'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            if 'data' not in data:
                return None

            candles = []
            for c in reversed(data['data']):
                candles.append({
                    'timestamp': pd.to_datetime(int(c[0]), unit='ms', utc=True),
                    'open': float(c[1]), 'high': float(c[2]),
                    'low': float(c[3]), 'close': float(c[4]),
                    'volume': float(c[5]),
                })

            df = pd.DataFrame(candles).set_index('timestamp')
            # 计算衍生指标
            df['returns'] = df['close'].pct_change()
            df['btc_vol_30d'] = df['returns'].rolling(30).std() * np.sqrt(365)
            tr = pd.concat([
                df['high'] - df['low'],
                (df['high'] - df['close'].shift(1)).abs(),
                (df['low'] - df['close'].shift(1)).abs()
            ], axis=1).max(axis=1)
            df['atr_14'] = tr.rolling(14).mean()
            df['high_20d'] = df['high'].rolling(20).max()
            df['dd_from_20d_high'] = (df['close'] - df['high_20d']) / df['high_20d']
            df['ret_24h'] = df['close'].pct_change(1)
            # 占位列
            for col in ['vix', 'funding_rate', 'oi', 'poly_prob', 'narrative_score']:
                if col not in df.columns:
                    df[col] = 0.0

            return df.dropna()

        except Exception as e:
            print(f"⚠️ 获取行情数据失败: {e}")
            return None

    def run_once(self) -> dict:
        """执行一轮完整的分析-交易循环"""
        result = {'timestamp': datetime.now(timezone.utc).isoformat()}

        # 1. 获取数据
        df = self.fetch_market_data()
        if df is None or len(df) < 30:
            result['error'] = '数据不足'
            return result

        row = df.iloc[-1]
        result['price'] = row['close']

        # 2. 计算信号
        df = self.l1.compute(df)
        df = self.l2.compute(df)

        signal = self.aggregator.compute(
            l1_z=row['l1_z'], l2_z=row['l2_z'],
            l3_z=0, l4_z=row['narrative_score'],
            vix=row['vix'], btc_vol=row['btc_vol_30d'],
            dd_from_high=row['dd_from_20d_high']
        )
        result['signal'] = round(signal[0], 4)
        result['signal_z'] = round(signal[1], 4)

        # 3. 市场状态识别
        regime_result = self.regime_detector.detect(df)
        result['regime'] = regime_result
        regime_mult = self.regime_detector.get_position_multiplier(
            regime_result['regime'], regime_result['confidence']
        )
        result['regime_multiplier'] = regime_mult

        # 4. AI 辅助分析 (如果配置了 AI 路由)
        ai_advice = ""
        if self.ai_router:
            try:
                market_ctx = {
                    'symbol': self.config.get('data', {}).get('symbol', 'BTC-USDT-SWAP'),
                    'price': row['close'],
                    'signal': result.get('signal', 0),
                    'regime': regime_result.get('regime', 'unknown'),
                }
                ai_advice = self.ai_router.route('market_analysis', market_ctx)
                result['ai_advice'] = ai_advice[:100] if ai_advice else ""
            except Exception as e:
                result['ai_advice'] = f"AI 分析失败: {e}"

        # 6. 风控检查
        daily_pnl = 0.0
        allow_trading, dd_mult, reason = self.circuit_breaker.check(
            self.current_equity, self.current_equity * 1.1,
            daily_pnl, row.get('vix', 20)
        )
        result['circuit_breaker'] = {'allow': allow_trading, 'reason': reason}

        if not allow_trading:
            result['action'] = 'HALT: ' + reason
            return result

        # 7. 计算目标仓位
        target_exp = signal[0] * dd_mult * regime_mult

        if target_exp != 0:
            kelly_cap = self.kelly.compute(
                np.array(self.recent_returns), row['atr_14'], row['close']
            )
            if target_exp > 0:
                target_exp = min(target_exp, kelly_cap)
            else:
                target_exp = max(target_exp, -kelly_cap)

        result['target_exposure'] = round(target_exp, 4)

        # 8. 执行交易
        if abs(target_exp) > 0.01:
            side = 'buy' if target_exp > 0 else 'sell'
            result['action'] = f'{side.upper()} 信号 (仓位: {abs(target_exp):.1%})'

            # 获取当前余额和持仓
            balance = self.executor.get_balance()
            if balance > 10 and self.config.get('exchange', {}).get('api_key'):
                inst_id = self.config.get('data', {}).get('symbol', 'BTC-USDT-SWAP')
                pos_size = abs(target_exp) * balance / row['close'] * 0.95
                if pos_size > 0:
                    order_result = self.executor.place_market_order(
                        inst_id, side, round(pos_size, 4),
                        lever=3, reduce_only=False
                    )
                    result['order'] = order_result
                    if order_result.get('success'):
                        self.trade_count += 1
                        msg = f"执行交易: {side.upper()} {inst_id} @ ${row['close']:.2f}"
                        self.notifier.send_signal(inst_id, side, row['close'], msg)
        else:
            result['action'] = '信号不足，等待'

        return result

    def run_loop(self):
        """主循环"""
        self.running = True
        print("=" * 50)
        print("🚀 Aegis Quantum Strategy - 实盘引擎启动")
        print(f"  轮询间隔: {self.interval} 秒")
        print(f"  运行模式: {'实盘' if not self.config.get('exchange', {}).get('demo') else '模拟'}")
        print("=" * 50)

        while self.running:
            try:
                result = self.run_once()
                ts = result['timestamp'][:19].replace('T', ' ')
                signal = result.get('signal', 0)
                action = result.get('action', '无操作')

                print(f"[{ts}] 信号={signal:.3f} | 状态={result.get('regime', {}).get('regime', 'N/A')} | {action}")

                if 'error' in result:
                    print(f"  ⚠️ 错误: {result['error']}")

                # 进化检查: 每 N 笔交易后自优化
                if self.trade_count > 0 and self.trade_count % 10 == 0:
                    if self.evolution.should_evolve():
                        evo_result = self.evolution.evolve()
                        print(f"🧬 策略自动进化完成 (第 {self.evolution.evolution_count} 代)")
                        self.notifier.send_report(
                            evo_result.get('report', '进化完成'),
                            title=f"策略进化 (第 {self.evolution.evolution_count} 代)"
                        )

                time.sleep(self.interval)

            except KeyboardInterrupt:
                print("\n🛑 收到停止信号")
                self.running = False
            except Exception as e:
                print(f"⚠️ 循环异常: {e}")
                time.sleep(60)

    def stop(self):
        """停止引擎"""
        self.running = False


if __name__ == "__main__":
    import sys
    config = load_config()
    engine = TradingEngine(config)

    if '--once' in sys.argv:
        result = engine.run_once()
        print(json.dumps(result, indent=2, default=str))
    else:
        engine.run_loop()
