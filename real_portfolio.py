import pandas as pd

class RealPortfolioMonitor:
    """
    实盘仓位监控模块，专门针对当前对冲混合仓位设计：
    1. DOGE 永续空单 (12x, 马丁格尔, 有强制平仓风险)
    2. BTC 现货多头 (安全资产)
    """
    def __init__(self):
        # 初始化真实持仓
        self.portfolio = {
            'BASE_STRATEGY_A': {
                'asset': 'STRAT_ASSET_1',
                'type': 'perp',
                'direction': -1,
                'margin_usdt': 100.00, # Masked
                'leverage': 10,
                'unrealized_pnl': 5.50, # Masked
                'strategy': 'hedged_martingale'
            },
            'CORE_HOLDING_B': {
                'asset': 'STRAT_ASSET_2',
                'type': 'spot',
                'direction': 1,
                'value_usdt': 500.00, # Masked
                'amount': 0.01        # Masked
            },
            'liquidity_reserve': 250.00 # Masked
        }
        self.total_equity = self.calculate_equity()

    def calculate_equity(self):
        """计算总资产净值"""
        eq = self.portfolio['free_usdt']
        eq += self.portfolio['BTC_long_spot']['value_usdt']
        eq += self.portfolio['DOGE_short_12x']['margin_usdt'] + self.portfolio['DOGE_short_12x']['unrealized_pnl']
        return eq

    def risk_assessment(self):
        """
        核心风控评估：
        由于 DOGE 是 12x 空单，名义敞口被放大12倍。一旦 DOGE 突然暴涨，极易爆仓。
        这里评估整体对冲有效性与单一敞口爆仓风险。
        """
        doge_pos = self.portfolio['DOGE_short_12x']
        btc_pos = self.portfolio['BTC_long_spot']
        
        doge_notional = doge_pos['margin_usdt'] * doge_pos['leverage'] # ~1182 USDT 空头敞口
        btc_notional = btc_pos['value_usdt']                           # ~659 USDT 多头敞口
        
        net_exposure = btc_notional - doge_notional # 净敞口为负，整体偏空
        
        assessment = {
            'total_equity': self.total_equity,
            'doge_notional': doge_notional,
            'btc_notional': btc_notional,
            'net_exposure': net_exposure,
            'margin_ratio': doge_pos['margin_usdt'] / self.total_equity,
            'free_margin_ratio': self.portfolio['free_usdt'] / self.total_equity,
        }
        
        if doge_notional > btc_notional * 1.5:
            assessment['status'] = 'HIGH_RISK'
            assessment['recommendation'] = (
                "⚠️ 严重警告：DOGE 空头名义敞口（~$1182）远超 BTC 现货多头敞口（~$659）。"
                "作为马丁格尔策略，DOGE 若出现单边拉升将导致连环爆仓。"
                f"建议将闲置的 {self.portfolio['free_usdt']} USDT 划转至合约账户增加保证金，或立即减仓 1/3 的 DOGE 空单以降低杠杆风险。"
            )
        elif doge_notional > btc_notional:
            assessment['status'] = 'WARNING'
            assessment['recommendation'] = "整体敞口偏空，对冲不足。需密切关注 DOGE 独立行情。"
        else:
            assessment['status'] = 'HEDGED'
            assessment['recommendation'] = "仓位已形成有效对冲。BTC 现货足以覆盖空头敞口风险。"
            
        return assessment

    def print_report(self):
        assess = self.risk_assessment()
        print("="*50)
        print("🛡️ 实盘级混合仓位监控报告")
        print("="*50)
        print(f"总净值: {assess['total_equity']:.2f} USDT")
        print(f"空闲资金: {self.portfolio['free_usdt']:.2f} USDT ({assess['free_margin_ratio']:.1%})")
        print("-" * 50)
        print(f"🐶 DOGE 12x 空头名义敞口: ${assess['doge_notional']:.2f} (浮盈: +${self.portfolio['DOGE_short_12x']['unrealized_pnl']:.2f})")
        print(f"🟠 BTC 现货多头名义敞口: ${assess['btc_notional']:.2f}")
        print(f"⚖️ 投资组合净敞口: ${assess['net_exposure']:.2f} (负值为偏空)")
        print("-" * 50)
        print(f"🚨 风险评级: {assess['status']}")
        print(f"💡 建议: {assess['recommendation']}")
        print("="*50)

if __name__ == "__main__":
    monitor = RealPortfolioMonitor()
    monitor.print_report()
