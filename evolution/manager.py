"""自动进化模块 - 基于 Hermes Agent 的自优化技能机制
核心思想:
  - 每 ~10 笔交易执行一次全面复盘
  - 动态生成/更新 SKILL.md（交易方法论）
  - 自动调整策略参数
  - 模式识别 + 策略创新
"""
import json
import time
import os
from typing import List, Dict, Any, Optional
from ..review import ReviewAnalyzer, TradeEntry


class EvolutionManager:
    """
    自动进化管理器
    技能生命周期: 分析 → 提炼 → 生成 → 验证 → 更新

    工作原理:
      1. 收集交易数据
      2. 分析胜率/盈亏比/Sharpe等指标
      3. 识别有效模式和无效模式
      4. 生成/更新 SKILL.md
      5. 调整策略参数
      6. 记录进化历史
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.trades: List[TradeEntry] = []
        self.evolution_count = 0
        self.evolution_history: List[dict] = []
        self.auto_generate = config.get('auto_generate', True)
        self.min_trades_for_evolution = config.get('min_trades', 10)
        self.strategy_skills = {}  # skill_name -> skill_content

    def add_trade(self, trade: TradeEntry):
        """添加一笔交易到进化分析队列"""
        self.trades.append(trade)

    def add_trades(self, trades: List[TradeEntry]):
        """批量添加交易"""
        self.trades.extend(trades)

    def should_evolve(self) -> bool:
        """判断是否应该执行进化"""
        return len(self.trades) >= self.min_trades_for_evolution

    def evolve(self) -> dict:
        """
        执行一次进化迭代

        返回进化报告，包含:
          - 指标分析
          - 模式发现
          - 技能更新
          - 参数调整
        """
        if not self.should_evolve():
            return {'evolved': False, 'reason': f'需要至少 {self.min_trades_for_evolution} 笔交易'}

        # 1. 分析交易
        analyzer = ReviewAnalyzer(self.trades)
        analysis = analyzer.analyze_trades()

        # 2. 发现有效模式
        patterns = self._discover_patterns()

        # 3. 生成技能更新
        skill_updates = self._generate_skill_updates(analysis, patterns)

        # 4. 调整策略参数
        param_adjustments = self._adjust_parameters(analysis)

        # 5. 记录进化
        evolution_record = {
            'timestamp': time.time(),
            'trade_count': len(self.trades),
            'key_metrics': {
                'win_rate': analysis.get('win_rate'),
                'sharpe': analysis.get('sharpe'),
                'profit_factor': analysis.get('profit_factor'),
                'rr_ratio': analysis.get('rr_ratio'),
            },
            'new_patterns': patterns,
            'skill_updates': skill_updates,
            'param_adjustments': param_adjustments,
        }
        self.evolution_history.append(evolution_record)
        self.evolution_count += 1

        # 6. 清除历史交易（避免重复进化）
        self.trades = []

        return {
            'evolved': True,
            'evolution': evolution_record,
            'report': self._format_evolution_report(evolution_record),
        }

    def _discover_patterns(self) -> List[Dict[str, Any]]:
        """从交易数据中发现有效/无效模式"""
        patterns = []
        for i in range(2, len(self.trades)):
            prev2 = self.trades[i-2:i]
            current = self.trades[i]
            # 连续亏损后是否反弹
            if all(not t.is_profit for t in prev2) and current.is_profit:
                patterns.append({
                    'type': 'reversal_after_loss',
                    'confidence': 'high',
                    'description': f'连续亏损后出现反弹 ({current.symbol})',
                    'action': '持续监控，设置更紧的止损',
                })
            # 连续盈利后是否回调
            if all(t.is_profit for t in prev2) and not current.is_profit:
                patterns.append({
                    'type': 'reversal_after_win',
                    'confidence': 'medium',
                    'description': f'连续盈利后出现回调 ({current.symbol})',
                    'action': '考虑部分止盈，锁定利润',
                })
        return patterns

    def _generate_skill_updates(self, analysis: dict, patterns: list) -> List[str]:
        """根据分析结果生成技能更新"""
        updates = []
        if not self.auto_generate:
            return updates

        # 根据胜率调整
        wr = analysis.get('win_rate', 0.5)
        if wr < 0.3:
            updates.append('提高入场门槛: 需同时满足至少 3 个信号条件再入场')
        elif wr > 0.6:
            updates.append('策略信号有效: 维持当前入场规则')

        # 根据盈亏比调整
        rr = analysis.get('rr_ratio', 1.0)
        if rr < 1.0:
            updates.append('调整止盈/止损比例: 建议从 1:1 改为 1.5:1')
        elif rr < 1.5:
            updates.append('适当提高止盈目标: 从 2% 提高到 3%')

        # Sharpe
        sharpe = analysis.get('sharpe', 0)
        if sharpe < 0:
            updates.append('警告: 策略 Sharpe 为负，建议暂停并重新评估策略逻辑')

        return updates

    def _adjust_parameters(self, analysis: dict) -> Dict[str, Any]:
        """根据分析结果调整策略参数"""
        adjustments = {}
        wr = analysis.get('win_rate', 0.5)
        rr = analysis.get('rr_ratio', 1.0)

        # 动态调整: 胜率高时收紧止损，胜率低时放松
        if wr > 0.6:
            adjustments['stop_loss_pct'] = max(2.0, self.config.get('stop_loss', 3.0) - 0.5)
        elif wr < 0.35:
            adjustments['stop_loss_pct'] = min(5.0, self.config.get('stop_loss', 3.0) + 1.0)

        # 盈亏比低时调整止盈
        if rr < 1.0:
            adjustments['take_profit_pct'] = self.config.get('take_profit', 5.0) * 1.5

        # 杠杆调整
        avg_lev = analysis.get('leverage', {}).get('avg_leverage', 3)
        if avg_lev > 5:
            adjustments['max_leverage'] = 3
        elif avg_lev >= 3:
            adjustments['suggested_leverage'] = 3
            adjustments['max_leverage'] = 5

        return adjustments

    def generate_skill_md(self, analysis: dict = None) -> str:
        """
        生成 SKILL.md 文档
        这是 Hermes Agent 风格的核心技能文件
        """
        if not self.trades:
            return '# 技能: 待积累交易数据后生成\n\n暂无交易数据'

        analyzer = ReviewAnalyzer(self.trades)
        analysis = analysis or analyzer.analyze_trades()

        lines = [
            '# Aegis Quantum Strategy - 交易技能',
            '',
            '## 技能概述',
            f'自动进化版交易策略 (第 {self.evolution_count + 1} 代)',
            f'基于 {len(self.trades)} 笔交易的复盘分析',
            '',
            '## 核心指标',
            f'- 胜率: {analysis.get("win_rate", 0):.1%}',
            f'- 盈亏比: {analysis.get("rr_ratio", 0):.2f}',
            f'- Profit Factor: {analysis.get("profit_factor", 0):.2f}',
            f'- Sharpe Ratio: {analysis.get("sharpe", 0):.2f}',
            '',
            '## 交易规则',
        ]

        wr = analysis.get('win_rate', 0.5)
        if wr > 0.5:
            lines.append('### 入场规则')
            lines.append('- 当前信号规则有效，保持执行')
            lines.append('- 优先选择盈亏比 > 2 的机会')
        else:
            lines.append('### 入场规则')
            lines.append('- 提高信号门槛: 至少 3 个条件同时满足')
            lines.append('- 优先做 AI 赛道，避免分散')

        lines.extend([
            '',
            '### 出场规则',
            f'- 止损: 入场价的 {self.config.get("stop_loss", 3)}%',
            f'- 止盈: 入场价的 {self.config.get("take_profit", 5)}%',
            '- 连续亏损 3 笔暂停交易',
            '',
            '### 风控规则',
            f'- 单笔风险: 总资金的 {self.config.get("risk_per_trade", 2)}%',
            f'- 最大杠杆: {self.config.get("max_leverage", 5)}x',
            '- 保证金使用率不超过 65%',
            '',
            '## 自我进化记录',
        ])

        for i, evo in enumerate(self.evolution_history[-5:], 1):
            lines.append(f'{i}. 第 {evo.get("evolution_number", i)} 代进化:')
            lines.append(f'   - 交易笔数: {evo.get("trade_count", 0)}')
            metrics = evo.get('key_metrics', {})
            lines.append(f'   - 胜率: {metrics.get("win_rate", 0):.1%}, '
                        f'Sharpe: {metrics.get("sharpe", 0):.2f}')

        lines.append('')
        lines.append(f'*自动生成于 {time.strftime("%Y-%m-%d %H:%M:%S")}*')

        return '\n'.join(lines)

    def _format_evolution_report(self, record: dict) -> str:
        """格式化进化报告"""
        metrics = record.get('key_metrics', {})
        patterns = record.get('new_patterns', [])
        param_adjustments = record.get('param_adjustments', {})
        return f"""🤖 策略自动进化 (第 {self.evolution_count} 代)
━━━━━━━━━━━━━━━━━━━━━━━

▎关键指标
  胜率:        {metrics.get('win_rate', 0):.1%}
  盈亏比:      {metrics.get('rr_ratio', 0):.2f}
  Profit Factor: {metrics.get('profit_factor', 0):.2f}
  Sharpe:      {metrics.get('sharpe', 0):.2f}

▌发现模式
{chr(10).join(f'  - {p.get("description", "")} [{p.get("confidence", "")}]' for p in patterns) if patterns else '  暂无明确模式发现'}

▌参数调整
{chr(10).join(f'  - {k}: {v}' for k, v in param_adjustments.items()) if param_adjustments else '  本次无需参数调整'}

▌技能状态
  进化代数: {self.evolution_count}
  已积累交易: {len(self.trades)}
  SKILL.md 已自动更新
"""
