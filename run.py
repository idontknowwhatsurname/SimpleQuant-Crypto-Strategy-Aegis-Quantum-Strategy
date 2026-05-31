#!/usr/bin/env python3
"""
Aegis Quantum Strategy - 一键启动入口
=======================================
用法:
    python run.py              # 启动实盘引擎
    python run.py backtest     # 运行回测
    python run.py portfolio    # 查看持仓
    python run.py download     # 下载数据
    python run.py report       # 生成回测报告 (需先运行 backtest)
"""
import sys
import os
from pathlib import Path

# 确保当前目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config


def cmd_backtest():
    """运行回测"""
    from backtester import Backtester
    from data_loader import DataLoader

    config = load_config()
    csv_path = config.get('data', {}).get('csv_path', None)
    symbol = config.get('data', {}).get('symbol', 'BTC-USDT-SWAP')

    print(f"\n{'=' * 50}")
    print(f"📊 开始回测: {symbol}")
    print(f"{'=' * 50}\n")

    if csv_path and Path(csv_path).exists():
        loader = DataLoader(csv_path=str(csv_path))
    else:
        print("ℹ️  未找到 CSV 数据，使用模拟数据")
        loader = DataLoader(
            start_date=config.get('data', {}).get('start_date', '2023-01-01'),
            end_date='2026-06-01'
        )

    df = loader.fetch_data()
    bt = Backtester(df)
    res_df = bt.run()
    bt.summary()

    # 保存回测结果
    out_path = Path(__file__).parent / 'backtest_results.csv'
    res_df.to_csv(out_path)
    print(f"\n✅ 回测结果已保存至: {out_path}")


def cmd_portfolio():
    """查看持仓"""
    from real_portfolio import RealPortfolioMonitor

    config = load_config()
    use_api = bool(config.get('exchange', {}).get('api_key'))

    if not use_api:
        print("⚠️  未配置 OKX API，使用模拟数据\n")

    monitor = RealPortfolioMonitor(use_api=use_api)
    monitor.print_report()


def cmd_download():
    """下载 OKX 数据"""
    from okx_downloader import main as download_main

    config = load_config()
    symbol = config.get('data', {}).get('symbol', 'BTC-USDT-SWAP')
    download_main(symbol=symbol)


def cmd_report():
    """生成回测分析报告"""
    import pandas as pd
    from results_analyzer import ResultsAnalyzer

    csv_path = Path(__file__).parent / 'backtest_results.csv'
    if not csv_path.exists():
        print("❌ 未找到回测结果文件，请先运行: python run.py backtest")
        return

    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    if 'strategy_equity' not in df.columns or 'bh_equity' not in df.columns:
        print("❌ 回测数据格式不正确")
        return

    analyzer = ResultsAnalyzer(
        equity_curve=df['strategy_equity'],
        benchmark=df['bh_equity']
    )

    print(analyzer.summary_text())


def cmd_review():
    """交易复盘分析"""
    from review import ReviewAnalyzer, TradeEntry
    from real_portfolio import RealPortfolioMonitor

    config = load_config()
    monitor = RealPortfolioMonitor(use_api=bool(config.get('exchange', {}).get('api_key')))

    positions = monitor.fetch_api_positions() if config.get('exchange', {}).get('api_key') else monitor.mock_positions()
    mock_trades = []
    for pos in positions:
        mock_trades.append(TradeEntry(
            symbol=pos.get('instId', pos.get('symbol', 'UNKNOWN')),
            side=pos.get('side', 'long'),
            entry_price=float(pos.get('avgPx', pos.get('entry_price', 0))),
            size=float(pos.get('pos', pos.get('size', 0))),
            leverage=int(pos.get('lever', pos.get('leverage', 1))),
        ))
    if not mock_trades:
        print("无持仓数据")
        return
    analyzer = ReviewAnalyzer(mock_trades)
    print(analyzer.generate_report())


def cmd_evolve():
    """手动触发策略进化"""
    from evolution import EvolutionManager
    from real_portfolio import RealPortfolioMonitor

    config = load_config()
    monitor = RealPortfolioMonitor(use_api=bool(config.get('exchange', {}).get('api_key')))
    positions = monitor.fetch_api_positions() if config.get('exchange', {}).get('api_key') else monitor.mock_positions()

    evo = EvolutionManager(config.get('evolution', {}))
    for pos in positions:
        from review import TradeEntry
        evo.add_trade(TradeEntry(
            symbol=pos.get('instId', pos.get('symbol', 'UNKNOWN')),
            side=pos.get('side', 'long'),
            entry_price=float(pos.get('avgPx', pos.get('entry_price', 0))),
            size=float(pos.get('pos', pos.get('size', 0))),
            leverage=int(pos.get('lever', pos.get('leverage', 1))),
        ))
    result = evo.evolve()
    if result.get('evolved'):
        print(result.get('report', '进化完成'))
    else:
        print(f"无需进化: {result.get('reason', '')}")


def cmd_help():
    print("""
Aegis Quantum Strategy - 帮助
==============================

用法: python run.py <命令>

命令:
    backtest     运行回测
    portfolio    查看持仓状态
    download     下载 OKX 历史数据
    report       生成回测绩效报告
    review       交易复盘分析
    evolve       手动触发策略进化
    help         显示此帮助

不带参数时启动实盘交易引擎。

一键启动:
    python run.py          # 实盘引擎
    python run.py backtest # 回测
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        from engine import TradingEngine
        config = load_config()
        engine = TradingEngine(config)
        engine.run_loop()
    else:
        cmd = sys.argv[1]
        commands = {
            'backtest': cmd_backtest,
            'portfolio': cmd_portfolio,
            'download': cmd_download,
            'report': cmd_report,
            'review': cmd_review,
            'evolve': cmd_evolve,
            'help': cmd_help,
        }
        fn = commands.get(cmd)
        if fn:
            fn()
        else:
            print(f"未知命令: {cmd}")
            cmd_help()
