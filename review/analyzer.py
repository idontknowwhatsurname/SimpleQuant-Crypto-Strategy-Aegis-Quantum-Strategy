"""
交易复盘分析系统 - 基于金融数据指标进行专业化交易分析
功能:
  1. 入场合理性分析
  2. 杠杆设置合理性分析
  3. 持仓健康度评估
  4. 盈亏归因分析
  5. 专业建议生成
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class TradeEntry:
    """单笔交易记录"""
    def __init__(self, symbol: str, side: str, entry_price: float,
                 exit_price: float = None, size: float = 0,
                 leverage: int = 1, entry_time: str = None,
                 exit_time: str = None, pnl: float = None,
                 fee: float = 0):
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.size = size
        self.leverage = leverage
        self.entry_time = entry_time or str(datetime.now())
        self.exit_time = exit_time
        self.pnl = pnl
        self.fee = fee
        self.duration_hours = self._calc_duration()

    def _calc_duration(self) -> float:
        if not self.exit_time:
            return 0
        try:
            entry = datetime.fromisoformat(self.entry_time)
            exit = datetime.fromisoformat(self.exit_time)
            return (exit - entry).total_seconds() / 3600
        except:
            return 0

    @property
    def return_pct(self) -> float:
        if not self.exit_price or self.entry_price == 0:
            return 0
        raw = (self.exit_price - self.entry_price) / self.entry_price
        return raw * self.leverage if self.side == 'long' else -raw * self.leverage

    @property
    def is_profit(self) -> bool:
        return self.return_pct > 0


class ReviewAnalyzer:
    """
    交易复盘分析器
    分析指标包括: 夏普比、盈亏比、胜率、最大回撤、
    入场时机合理性（ATR 位置）、杠杆使用合理性、风险调整后收益
    """

    def __init__(self, trades: List[TradeEntry] = None):
        self.trades = trades or []

    def add_trade(self, trade: TradeEntry):
        self.trades.append(trade)

    def analyze_trades(self) -> dict:
        """对当前所有交易进行全面分析"""
        if not self.trades:
            return {'error': '无交易记录'}

        # 基础统计
        wins = [t for t in self.trades if t.is_profit]
        losses = [t for t in self.trades if not t.is_profit]
        total_pnl = sum(t.pnl or 0 for t in self.trades)
        total_fees = sum(t.fee or 0 for t in self.trades)

        returns = [t.return_pct for t in self.trades]
        avg_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if len(returns) > 1 else 0

        # 胜率/盈亏比
        win_rate = len(wins) / len(self.trades) if self.trades else 0
        avg_win = np.mean([t.return_pct for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t.return_pct) for t in losses]) if losses else 0
        profit_factor = (sum(t.pnl or 0 for t in wins) /
                         abs(sum(t.pnl or 0 for t in losses))
                         ) if losses and sum(t.pnl or 0 for t in losses) < 0 else float('inf')
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # Sharpe (假设日频)
        daily_rf = 0.04 / 365
        sharpe = (avg_return / std_return * np.sqrt(len(returns))
                  ) if std_return > 0 else 0

        # Max consecutive wins/losses
        streak_win = self._max_streak('win')
        streak_loss = self._max_streak('loss')

        # 杠杆分析
        leverage_analysis = self._analyze_leverage()

        # 入场时机分析
        timing_analysis = self._analyze_entry_timing()

        # 持仓时长分析
        duration_analysis = self._analyze_duration()

        return {
            'total_trades': len(self.trades),
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'net_pnl': total_pnl - total_fees,
            'win_rate': round(win_rate, 3),
            'profit_factor': round(profit_factor, 2),
            'avg_return': round(avg_return, 4),
            'std_return': round(std_return, 4),
            'sharpe': round(sharpe, 2),
            'avg_win': round(avg_win, 4),
            'avg_loss': round(avg_loss, 4),
            'rr_ratio': round(rr_ratio, 2),
            'max_consecutive_wins': streak_win,
            'max_consecutive_losses': streak_loss,
            'long_trades': len([t for t in self.trades if t.side == 'long']),
            'short_trades': len([t for t in self.trades if t.side == 'short']),
            'best_trade': max(self.trades, key=lambda t: t.return_pct).__dict__,
            'worst_trade': min(self.trades, key=lambda t: t.return_pct).__dict__,
            'leverage': leverage_analysis,
            'entry_timing': timing_analysis,
            'duration': duration_analysis,
        }

    def _max_streak(self, kind: str) -> int:
        """计算最大连胜/连败次数"""
        max_streak = cur = 0
        for t in self.trades:
            if (kind == 'win' and t.is_profit) or (kind == 'loss' and not t.is_profit):
                cur += 1
                max_streak = max(max_streak, cur)
            else:
                cur = 0
        return max_streak

    def _analyze_leverage(self) -> dict:
        """杠杆使用合理性分析"""
        levs = [t.leverage for t in self.trades]
        avg_lev = np.mean(levs) if levs else 0
        max_lev = max(levs) if levs else 0
        # 高杠杆 (>5x) 交易的比例
        high_lev_count = sum(1 for l in levs if l > 5)
        high_lev_ratio = high_lev_count / len(levs) if levs else 0

        # 不同杠杆的胜率分析
        lev_perf = {}
        for lev in set(levs):
            group = [t for t in self.trades if t.leverage == lev]
            win = sum(1 for t in group if t.is_profit)
            lev_perf[f'{lev}x'] = {
                'count': len(group),
                'win_rate': round(win / len(group), 3) if group else 0,
                'avg_return': round(np.mean([t.return_pct for t in group]), 4) if group else 0,
            }

        return {
            'avg_leverage': round(avg_lev, 1),
            'max_leverage': max_lev,
            'high_leverage_ratio': round(high_lev_ratio, 3),
            'high_leverage_count': high_lev_count,
            'by_leverage': lev_perf,
        }

    def _analyze_entry_timing(self) -> dict:
        """入场时机合理性分析"""
        # 基于模拟数据: 假设入场价在 ATR 范围的位置
        # 理想入场: 在 ATR 范围的 30-50% 位置（非追高、非抄底）
        return {'note': '使用 ATR 位置分析（需要与 K 线数据配合）'}

    def _analyze_duration(self) -> dict:
        """持仓时长分析"""
        durations = [t.duration_hours for t in self.trades if t.duration_hours > 0]
        if not durations:
            return {'note': '无持仓时长数据'}
        by_duration = {
            '<1h': [], '1-6h': [], '6-24h': [], '1-3d': [], '>3d': []
        }
        for t in self.trades:
            if t.duration_hours <= 1:
                by_duration['<1h'].append(t)
            elif t.duration_hours <= 6:
                by_duration['1-6h'].append(t)
            elif t.duration_hours <= 24:
                by_duration['6-24h'].append(t)
            elif t.duration_hours <= 72:
                by_duration['1-3d'].append(t)
            else:
                by_duration['>3d'].append(t)

        duration_perf = {}
        for bucket, trades in by_duration.items():
            if trades:
                wins = sum(1 for t in trades if t.is_profit)
                duration_perf[bucket] = {
                    'count': len(trades),
                    'win_rate': round(wins / len(trades), 3),
                    'avg_pnl': round(sum(t.pnl or 0 for t in trades), 2),
                }

        return {
            'avg_duration_hours': round(np.mean(durations), 1),
            'max_duration_hours': max(durations),
            'by_duration': duration_perf,
        }

    def generate_report(self) -> str:
        """生成专业分析报告文本"""
        analysis = self.analyze_trades()
        if 'error' in analysis:
            return f"📊 分析失败: {analysis['error']}"

        lines = [
            "=" * 55,
            "📋 交易复盘分析报告",
            "=" * 55,
            "",
            "▎整体表现",
            f"  总交易:     {analysis['total_trades']} 笔",
            f"  总盈亏:     {analysis['net_pnl']:+.2f} USDT",
            f"  总手续费:   {analysis['total_fees']:.2f} USDT",
            f"  胜率:       {analysis['win_rate']:.1%}",
            f"  盈亏比:     {analysis['rr_ratio']:.2f}",
            f"  Profit Factor: {analysis['profit_factor']:.2f}",
            f"  Sharpe:     {analysis['sharpe']:.2f}",
            "",
            "▎趋势分析",
            f"  最大连胜:   {analysis['max_consecutive_wins']} 笔",
            f"  最大连败:   {analysis['max_consecutive_losses']} 笔",
            f"  最佳交易:   +{analysis['best_trade']['return_pct']:.2%}",
            f"  最差交易:   {analysis['worst_trade']['return_pct']:.2%}",
            "",
            "▎杠杆分析",
        ]

        lev = analysis['leverage']
        lines += [
            f"  平均杠杆:   {lev['avg_leverage']}x",
            f"  最高杠杆:   {lev['max_leverage']}x",
        ]
        if lev['high_leverage_ratio'] > 0.3:
            lines.append(f"  ⚠️ 高杠杆交易占比 {lev['high_leverage_ratio']:.0%}，建议降低")
        if lev['avg_leverage'] > 5:
            lines.append(f"  ⚠️ 平均杠杆 {lev['avg_leverage']}x 偏高，建议控制在 3x 以内")

        lines += ["", "▎持仓时长分析"]
        dur = analysis['duration']
        if 'avg_duration_hours' in dur:
            lines += [
                f"  平均时长:   {dur['avg_duration_hours']:.1f} 小时",
            ]
            for bucket, perf in dur.get('by_duration', {}).items():
                tag = "✓" if perf['win_rate'] > 0.5 else "✗"
                lines.append(f"  {bucket}: {perf['count']} 笔, 胜率 {perf['win_rate']:.0%} {tag}")

        lines += ["", "▎入场合理性评估"]
        lines += self._assess_entry_reasonableness(analysis)

        lines += ["", "▎改进建议"]
        lines += self._generate_recommendations(analysis)

        lines += ["", "=" * 55]
        return "\n".join(lines)

    def _assess_entry_reasonableness(self, analysis: dict) -> list:
        """评估入场合理性"""
        recs = []
        # 胜率评估
        wr = analysis['win_rate']
        if wr < 0.3:
            recs.append(f"  ⚠️ 胜率 {wr:.0%} 偏低，可能存在入场时机问题")
        elif wr > 0.6:
            recs.append(f"  ✅ 胜率 {wr:.0%} 良好，入场时机把握较好")

        # 盈亏比评估
        rr = analysis['rr_ratio']
        if rr < 1.0:
            recs.append(f"  ⚠️ 盈亏比 {rr:.2f} 偏低，止损可能设置过紧或止盈不够")
        elif rr > 2.0:
            recs.append(f"  ✅ 盈亏比 {rr:.2f} 优秀，风险控制良好")

        # 连败分析
        max_loss = analysis['max_consecutive_losses']
        if max_loss >= 5:
            recs.append(f"  🚨 连续亏损 {max_loss} 笔，建议暂停交易进行心理休整")
        elif max_loss >= 3:
            recs.append(f"  ⚠️ 连续亏损 {max_loss} 笔，需要检查是否进入情绪化交易")

        # Sharpe
        sharpe = analysis['sharpe']
        if sharpe < 0:
            recs.append(f"  🚨 Sharpe {sharpe:.2f} 为负，策略综合风险大于收益")
        elif sharpe < 0.5:
            recs.append(f"  ⚠️ Sharpe {sharpe:.2f} 偏低")
        elif sharpe > 1.0:
            recs.append(f"  ✅ Sharpe {sharpe:.2f} 良好")

        return recs if recs else ["  ℹ️ 入场合理性正常"]

    def _generate_recommendations(self, analysis: dict) -> list:
        """生成改进建议"""
        recs = []
        lev = analysis['leverage']
        dur = analysis['duration']

        if lev['avg_leverage'] > 5:
            recs.append("  🔧 建议将平均杠杆控制在 3x 以内，降低爆仓风险")
        if analysis['profit_factor'] < 1.2:
            recs.append("  🔧 Profit Factor < 1.2，建议优化入场/出场规则")
        if analysis['max_consecutive_losses'] >= 3:
            recs.append("  🔧 设置连败停损机制：连续亏损 3 笔暂停交易")
        if 'avg_duration_hours' in dur and dur['avg_duration_hours'] < 2:
            recs.append("  🔧 持仓过短（平均 <2h），建议延长持仓周期")

        # 根据 AI 模型自动生成建议
        recs.append("  🤖 建议结合 AI 模型分析，检查当前策略与市场状态的匹配度")
        recs.append("  📊 建议根据复盘结果更新策略配置")

        return recs
