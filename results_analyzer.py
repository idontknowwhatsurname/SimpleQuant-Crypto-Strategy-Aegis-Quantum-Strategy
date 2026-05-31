"""
回测结果分析器 - 提供更详细的回测绩效分析
包括：月度收益、滚动静默期、夏普比、索提诺比、信息比、Alpha/Beta 等
"""
import numpy as np
import pandas as pd
from typing import Optional


class ResultsAnalyzer:
    """回测结果深度分析"""

    def __init__(self, equity_curve: pd.Series, benchmark: pd.Series = None):
        """
        Args:
            equity_curve: 策略权益曲线
            benchmark: 基准权益曲线（如买入持有）
        """
        self.equity = equity_curve
        self.benchmark = benchmark
        self.returns = equity_curve.pct_change().dropna()
        self.bm_returns = benchmark.pct_change().dropna() if benchmark is not None else None

    def compute_all(self) -> dict:
        """计算所有绩效指标"""
        return {
            'returns': self._compute_returns(),
            'risk': self._compute_risk(),
            'ratios': self._compute_ratios(),
            'drawdown': self._compute_drawdown(),
            'monthly': self._compute_monthly(),
        }

    def _compute_returns(self) -> dict:
        total = (self.equity.iloc[-1] / self.equity.iloc[0]) - 1
        days = len(self.equity)
        ann = (1 + total) ** (365 / days) - 1 if days > 0 else 0

        result = {
            'total_return': total,
            'annual_return': ann,
            'daily_mean': self.returns.mean(),
            'daily_std': self.returns.std(),
        }

        if self.benchmark is not None:
            bm_total = (self.benchmark.iloc[-1] / self.benchmark.iloc[0]) - 1
            result['benchmark_return'] = bm_total
            result['excess_return'] = total - bm_total

        return result

    def _compute_risk(self) -> dict:
        # 最大回撤
        cummax = self.equity.cummax()
        dd = (self.equity - cummax) / cummax
        max_dd = dd.min()
        max_dd_duration = self._compute_dd_duration(dd)

        # VaR (95%)
        var_95 = np.percentile(self.returns, 5)

        # CVaR (95%)
        cvar_95 = self.returns[self.returns <= var_95].mean() if len(self.returns[self.returns <= var_95]) > 0 else 0

        # 下行标准差
        downside = self.returns[self.returns < 0]
        downside_std = downside.std() if len(downside) > 0 else 0

        return {
            'max_drawdown': max_dd,
            'max_dd_duration_days': max_dd_duration,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'downside_std': downside_std,
            'daily_volatility': self.returns.std(),
            'annual_volatility': self.returns.std() * np.sqrt(365),
        }

    def _compute_dd_duration(self, dd: pd.Series) -> int:
        """计算最长回撤持续时间（天）"""
        underwater = dd < 0
        if not underwater.any():
            return 0
        # 找到最长的连续水下时段
        groups = (underwater != underwater.shift()).cumsum()
        underwater_groups = underwater[underwater]
        if len(underwater_groups) == 0:
            return 0
        durations = underwater_groups.groupby(groups).size()
        return int(durations.max()) if len(durations) > 0 else 0

    def _compute_ratios(self) -> dict:
        rf = 0.04 / 365  # 日无风险利率

        # Sharpe
        excess = self.returns - rf
        sharpe = excess.mean() / excess.std() * np.sqrt(365) if excess.std() > 0 else 0

        # Sortino
        downside = self.returns[self.returns < rf]
        downside_std = downside.std() if len(downside) > 0 else 0.0001
        sortino = (self.returns.mean() - rf) / downside_std * np.sqrt(365) if downside_std > 0 else 0

        # Calmar
        ann_return = (1 + (self.equity.iloc[-1] / self.equity.iloc[0]) - 1) ** (365 / len(self.equity)) - 1
        dd = (self.equity / self.equity.cummax() - 1).min()
        calmar = ann_return / abs(dd) if dd != 0 else float('inf')

        # Win Rate
        wins = len(self.returns[self.returns > 0])
        total = len(self.returns)
        win_rate = wins / total if total > 0 else 0

        # Profit Factor
        gross_profit = self.returns[self.returns > 0].sum()
        gross_loss = abs(self.returns[self.returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Daily Value at Risk
        var_95 = np.percentile(self.returns, 5)

        result = {
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'win_rate': round(win_rate, 3),
            'profit_factor': round(profit_factor, 2),
            'avg_win': self.returns[self.returns > 0].mean() if len(self.returns[self.returns > 0]) > 0 else 0,
            'avg_loss': self.returns[self.returns < 0].mean() if len(self.returns[self.returns < 0]) > 0 else 0,
            'avg_daily_var_95': round(var_95, 4),
        }

        # Alpha / Beta (if benchmark exists)
        if self.bm_returns is not None:
            aligned = pd.concat([self.returns, self.bm_returns], axis=1).dropna()
            if len(aligned) > 30:
                strat_ret = aligned.iloc[:, 0]
                bm_ret = aligned.iloc[:, 1]
                cov = np.cov(strat_ret, bm_ret)
                beta = cov[0][1] / cov[1][1] if cov[1][1] > 0 else 1.0
                alpha = (strat_ret.mean() - beta * bm_ret.mean()) * 365
                result['alpha'] = round(alpha, 4)
                result['beta'] = round(beta, 2)

        return result

    def _compute_drawdown(self) -> dict:
        cummax = self.equity.cummax()
        dd = (self.equity - cummax) / cummax

        # 找出所有回撤段
        underwater = dd < 0
        peaks = cummax.copy()

        # 前5大回撤
        dd_series = dd.copy()
        top5_dd = dd_series.sort_values().head(5)
        top5 = []
        for idx, val in top5_dd.items():
            top5.append({'date': str(idx.date()) if hasattr(idx, 'date') else str(idx),
                         'dd': round(val, 4)})

        return {
            'max_drawdown': round(dd.min(), 4),
            'current_drawdown': round(dd.iloc[-1], 4) if len(dd) > 0 else 0,
            'top5_drawdowns': top5,
        }

    def _compute_monthly(self) -> dict:
        """月度收益统计"""
        monthly_returns = self.equity.resample('ME').last().pct_change().dropna()

        stats = {
            'best_month': monthly_returns.max() if len(monthly_returns) > 0 else 0,
            'worst_month': monthly_returns.min() if len(monthly_returns) > 0 else 0,
            'positive_months': len(monthly_returns[monthly_returns > 0]),
            'negative_months': len(monthly_returns[monthly_returns < 0]),
            'total_months': len(monthly_returns),
        }

        if stats['total_months'] > 0:
            stats['monthly_win_rate'] = stats['positive_months'] / stats['total_months']

        # 按年统计
        yearly = self.equity.resample('YE').last().pct_change().dropna()
        stats['yearly_returns'] = {
            str(idx.year): round(val, 4)
            for idx, val in yearly.items()
        }

        return stats

    def summary_text(self) -> str:
        """生成可读的绩效报告文本"""
        all_stats = self.compute_all()
        ret = all_stats['returns']
        risk = all_stats['risk']
        ratios = all_stats['ratios']
        dd_info = all_stats['drawdown']
        monthly = all_stats['monthly']

        lines = [
            "=" * 50,
            "📊 回测绩效报告",
            "=" * 50,
            "",
            "▎收益指标",
            f"  总收益:        {ret['total_return']:.2%}",
            f"  年化收益:      {ret['annual_return']:.2%}",
            f"  基准收益:      {ret.get('benchmark_return', 0):.2%}",
            f"  超额收益:      {ret.get('excess_return', 0):.2%}",
            "",
            "▎风险指标",
            f"  最大回撤:      {risk['max_drawdown']:.2%}",
            f"  最长回撤期:    {risk['max_dd_duration_days']} 天",
            f"  年化波动率:    {risk['annual_volatility']:.2%}",
            f"  日 VaR(95%):   {risk['var_95']:.2%}",
            f"  日 CVaR(95%):  {risk['cvar_95']:.2%}",
            "",
            "▎绩效比率",
            f"  Sharpe Ratio:  {ratios['sharpe_ratio']:.2f}",
            f"  Sortino Ratio: {ratios['sortino_ratio']:.2f}",
            f"  Calmar Ratio:  {ratios['calmar_ratio']:.2f}",
            f"  Profit Factor: {ratios['profit_factor']:.2f}",
            f"  胜率:          {ratios['win_rate']:.1%}",
        ]

        if 'alpha' in ratios:
            lines += [
                f"  Alpha:         {ratios['alpha']:.4f}",
                f"  Beta:          {ratios['beta']:.2f}",
            ]

        lines += [
            "",
            "▎月度统计",
            f"  最好月份:      {monthly['best_month']:.2%}" if monthly.get('best_month') else "",
            f"  最差月份:      {monthly['worst_month']:.2%}" if monthly.get('worst_month') else "",
            f"  月胜率:        {monthly.get('monthly_win_rate', 0):.1%}",
            f"  盈利月数:      {monthly['positive_months']}/{monthly['total_months']}",
            "",
            "▎前5大回撤",
        ]

        for item in dd_info['top5_drawdowns']:
            lines.append(f"  {item['date']}: {item['dd']:.2%}")

        lines += [
            "",
            "▎逐年收益",
        ]

        for year, ret_val in monthly.get('yearly_returns', {}).items():
            lines.append(f"  {year}: {ret_val:.2%}")

        lines += [
            "",
            "=" * 50,
        ]

        return "\n".join(lines)
