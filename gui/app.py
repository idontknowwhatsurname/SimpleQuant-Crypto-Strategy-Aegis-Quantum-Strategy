#!/usr/bin/env python3
"""
AIQuant Engine - Web GUI
基于 Flask 的交易系统 GUI，参考 DeepSeek-Reasonix 的设计理念
"""
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUI_ROOT = Path(__file__).resolve().parent

# 确保项目根目录在路径中
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from flask import Flask, jsonify, render_template, request
except ImportError:
    print("请先安装 Flask: pip install flask")
    sys.exit(1)

# 全局状态
engine_state = {
    'status': 'stopped',
    'start_time': None,
    'trade_count': 0,
    'evolution_count': 0,
    'last_signal': None,
    'last_regime': None,
}


def create_app() -> Flask:
    """创建 Flask 应用，兼容源码运行与打包运行。"""
    return Flask(
        __name__,
        template_folder=str(GUI_ROOT / "templates"),
        static_folder=str(GUI_ROOT / "static"),
    )


app = create_app()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html', state=engine_state)

@app.route('/api/status')
def api_status():
    """获取引擎状态"""
    return jsonify(engine_state)

@app.route('/api/start', methods=['POST'])
def api_start():
    """启动引擎"""
    global engine_state
    engine_state['status'] = 'running'
    engine_state['start_time'] = datetime.now().isoformat()
    return jsonify({'success': True, 'message': '引擎已启动'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止引擎"""
    global engine_state
    engine_state['status'] = 'stopped'
    return jsonify({'success': True, 'message': '引擎已停止'})

@app.route('/api/backtest', methods=['POST'])
def api_backtest():
    """运行回测"""
    try:
        from backtester import Backtester
        from data_loader import DataLoader
        from config_loader import load_config
        
        config = load_config()
        loader = DataLoader(
            start_date=config.get('data', {}).get('start_date', '2023-01-01'),
            end_date='2026-06-01'
        )
        df = loader.fetch_data()
        bt = Backtester(df)
        res_df = bt.run()
        
        # 提取关键指标
        metrics = {
            'total_return': float((res_df['strategy_equity'].iloc[-1] / res_df['strategy_equity'].iloc[0] - 1) * 100),
            'sharpe': float(res_df['strategy_equity'].pct_change().mean() / res_df['strategy_equity'].pct_change().std() * (365**0.5)) if len(res_df) > 1 else 0,
            'max_drawdown': float(((res_df['strategy_equity'].cummax() - res_df['strategy_equity']) / res_df['strategy_equity'].cummax()).max() * 100),
            'trade_count': int(len(res_df[res_df['position'] != 0])) if 'position' in res_df.columns else 0,
        }
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/portfolio')
def api_portfolio():
    """获取持仓信息"""
    try:
        from real_portfolio import RealPortfolioMonitor
        from config_loader import load_config
        
        config = load_config()
        use_api = bool(config.get('exchange', {}).get('api_key'))
        monitor = RealPortfolioMonitor(use_api=use_api)
        positions = monitor.fetch_api_positions() if use_api else monitor.mock_positions()
        
        return jsonify({'success': True, 'positions': positions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/review')
def api_review():
    """交易复盘分析"""
    try:
        from review import ReviewAnalyzer, TradeEntry
        from real_portfolio import RealPortfolioMonitor
        from config_loader import load_config
        
        config = load_config()
        monitor = RealPortfolioMonitor(use_api=bool(config.get('exchange', {}).get('api_key')))
        positions = monitor.fetch_api_positions() if config.get('exchange', {}).get('api_key') else mock_positions()
        
        trades = []
        for pos in positions:
            trades.append(TradeEntry(
                symbol=pos.get('instId', pos.get('symbol', 'UNKNOWN')),
                side=pos.get('side', 'long'),
                entry_price=float(pos.get('avgPx', pos.get('entry_price', 0))),
                size=float(pos.get('pos', pos.get('size', 0))),
                leverage=int(pos.get('lever', pos.get('leverage', 1))),
            ))
        
        if not trades:
            return jsonify({'success': True, 'report': '无持仓数据'})
        
        analyzer = ReviewAnalyzer(trades)
        report = analyzer.generate_report()
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/evolve', methods=['POST'])
def api_evolve():
    """手动触发策略进化"""
    try:
        from evolution import EvolutionManager
        from review import TradeEntry
        from real_portfolio import RealPortfolioMonitor
        from config_loader import load_config
        
        config = load_config()
        monitor = RealPortfolioMonitor(use_api=bool(config.get('exchange', {}).get('api_key')))
        positions = monitor.fetch_api_positions() if config.get('exchange', {}).get('api_key') else mock_positions()
        
        evo = EvolutionManager(config.get('evolution', {}))
        for pos in positions:
            evo.add_trade(TradeEntry(
                symbol=pos.get('instId', pos.get('symbol', 'UNKNOWN')),
                side=pos.get('side', 'long'),
                entry_price=float(pos.get('avgPx', pos.get('entry_price', 0))),
                size=float(pos.get('pos', pos.get('size', 0))),
                leverage=int(pos.get('lever', pos.get('leverage', 1))),
            ))
        
        result = evo.evolve()
        if result.get('evolved'):
            return jsonify({'success': True, 'report': result.get('report', '进化完成')})
        else:
            return jsonify({'success': True, 'report': f"无需进化: {result.get('reason', '')}"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/signal')
def api_signal():
    """获取当前信号"""
    try:
        from signals import SignalAggregator
        from config_loader import load_config
        
        # 这里需要实际的市场数据，简化返回
        return jsonify({
            'success': True, 
            'signal': 0.0,
            'signal_z': 0.0,
            'regime': 'unknown',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mcp/prompt', methods=['POST'])
def mcp_prompt():
    """MCP 提示栏 - 多模型兼容"""
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek')  # deepseek / openai / anthropic
    
    # 路由到对应的 AI 模型
    try:
        from ai_router import AIRouter
        from config_loader import load_config
        
        config = load_config()
        router = AIRouter(config.get('ai', {}))
        
        # 根据模型类型路由
        if model == 'deepseek':
            result = router._call_deepseek(prompt)
        elif model == 'openai':
            result = router._call_openai(prompt)
        elif model == 'anthropic':
            result = router._call_anthropic(prompt)
        else:
            result = router.route('market_analysis', {'prompt': prompt})
        
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/goal', methods=['POST'])
def goal_execute():
    """Goal 类任务规划 - 目标 → 拆解 → 执行 → 反馈"""
    data = request.json
    goal = data.get('goal', '')
    
    # 任务拆解
    tasks = [
        {'id': 1, 'name': '分析目标', 'status': 'pending', 'description': f'理解用户目标: {goal}'},
        {'id': 2, 'name': '拆解任务', 'status': 'pending', 'description': '将目标拆解为可执行的子任务'},
        {'id': 3, 'name': '执行任务', 'status': 'pending', 'description': '按顺序执行子任务'},
        {'id': 4, 'name': '验证结果', 'status': 'pending', 'description': '验证执行结果是否符合目标'},
    ]
    
    return jsonify({'success': True, 'tasks': tasks, 'goal': goal})

def mock_positions():
    """模拟持仓数据"""
    return [
        {
            'instId': 'ANTHROPIC-USDT-SWAP',
            'side': 'long',
            'avgPx': '15.27',
            'pos': '32.4',
            'lever': '5',
            'unrealizedPnl': '549.12',
        },
        {
            'instId': 'SPACEX-USDT-SWAP',
            'side': 'long',
            'avgPx': '8.92',
            'pos': '29.4',
            'lever': '5',
            'unrealizedPnl': '263.29',
        },
        {
            'instId': 'OPENAI-USDT-SWAP',
            'side': 'long',
            'avgPx': '12.45',
            'pos': '1.4',
            'lever': '5',
            'unrealizedPnl': '-14.27',
        },
    ]

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 AIQuant Engine - Web GUI")
    print("=" * 50)
    print(f"  访问地址: http://localhost:5000")
    print(f"  按 Ctrl+C 停止")
    print("=" * 50)

    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
