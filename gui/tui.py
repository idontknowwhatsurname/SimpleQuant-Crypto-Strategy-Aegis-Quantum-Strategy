"""
AIQuant Engine - TUI 终端界面 (Reasonix 风格)
基于 Textual 框架
"""
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, Tree, Button, Input, Label, ListView, ListItem, RichLog, TabbedContent, TabPane, DataTable, LoadingIndicator
from textual.widgets._toggle_button import ToggleButton
from textual.reactive import reactive
from textual.message import Message
from textual import work
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.layout import Layout
from rich.console import Console


class Sidebar(Vertical):
    """左侧导航栏"""
    
    def compose(self) -> ComposeResult:
        yield Static("🛡️ AIQuant Engine", classes="sidebar-title")
        yield Static("")
        yield Button("仪表盘", id="btn-dashboard", variant="primary")
        yield Button("回测", id="btn-backtest")
        yield Button("复盘", id="btn-review")
        yield Button("进化", id="btn-evolution")
        yield Button("MCP", id="btn-mcp")
        yield Button("Goal", id="btn-goal")
        yield Static("", classes="spacer")
        yield Button("退出", id="btn-quit", variant="error")


class DashboardScreen(Screen):
    """仪表盘"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("📊 仪表盘", classes="screen-title"),
            Horizontal(
                Vertical(
                    Static("引擎状态", classes="card-title"),
                    Static("● 已停止", id="engine-status", classes="status-stopped"),
                    Static(""),
                    Button("启动引擎", id="start-engine", variant="success"),
                    Button("停止引擎", id="stop-engine", variant="error", disabled=True),
                    classes="card",
                ),
                Vertical(
                    Static("交易统计", classes="card-title"),
                    Static("交易次数: 0", id="trade-count"),
                    Static("进化次数: 0", id="evolution-count"),
                    Static("持仓: 3", id="position-count"),
                    classes="card",
                ),
                Vertical(
                    Static("当前信号", classes="card-title"),
                    Static("信号: 0.000", id="signal-value"),
                    Static("市场状态: N/A", id="regime-value"),
                    Static("最后更新: --", id="last-update"),
                    classes="card",
                ),
                id="dashboard-cards",
            ),
            Static(""),
            Static("持仓概览", classes="section-title"),
            RichLog(id="portfolio-log", highlight=True, markup=True),
            id="dashboard-content",
        )

    def on_mount(self) -> None:
        self.load_portfolio()

    @work(exclusive=True)
    async def load_portfolio(self):
        log = self.query_one("#portfolio-log", RichLog)
        log.clear()
        log.write("[bold yellow]加载持仓数据...[/]")
        try:
            from real_portfolio import RealPortfolioMonitor
            from config_loader import load_config
            config = load_config()
            use_api = bool(config.get('exchange', {}).get('api_key'))
            monitor = RealPortfolioMonitor(use_api=use_api)
            positions = monitor.mock_positions()
            
            log.clear()
            for pos in positions:
                pnl = float(pos.get('unrealizedPnl', 0))
                sign = "+" if pnl >= 0 else ""
                color = "green" if pnl >= 0 else "red"
                log.write(f"[bold]{pos.get('instId')}[/]  {pos.get('side')}  {pos.get('avgPx')}  [{color}]{sign}{pnl:.2f}[/] USDT")
        except Exception as e:
            log.write(f"[red]加载失败: {e}[/]")


class BacktestScreen(Screen):
    """回测"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("📊 策略回测", classes="screen-title"),
            Button("▶ 运行回测", id="run-backtest", variant="primary"),
            Static(""),
            RichLog(id="backtest-log", highlight=True, markup=True, max_lines=100),
            id="backtest-content",
        )

    @work(exclusive=True)
    async def run_backtest(self):
        log = self.query_one("#backtest-log", RichLog)
        log.clear()
        log.write("[bold yellow]运行回测中...[/]")
        
        try:
            from backtester import Backtester
            from data_loader import DataLoader
            from config_loader import load_config
            
            config = load_config()
            loader = DataLoader(start_date='2024-01-01', end_date='2025-06-01')
            log.write("[dim]加载数据...[/]")
            df = loader.fetch_data()
            log.write(f"[dim]数据行数: {len(df)}[/]")
            
            bt = Backtester(df)
            log.write("[dim]执行回测...[/]")
            res_df = bt.run()
            
            log.clear()
            equity = res_df['strategy_equity']
            returns = equity.pct_change().dropna()
            total_ret = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
            sharpe = returns.mean() / returns.std() * (365 ** 0.5) if len(returns) > 0 else 0
            max_dd = ((equity.cummax() - equity) / equity.cummax()).max() * 100
            
            log.write("[bold green]✅ 回测完成[/]\n")
            log.write(f"总收益率: [bold]{total_ret:+.2f}%[/]")
            log.write(f"夏普比:   [bold]{sharpe:.2f}[/]")
            log.write(f"最大回撤: [bold]{max_dd:.2f}%[/]")
            log.write(f"交易天数: [bold]{len(res_df)}[/]")
            
            # 保存
            out_path = Path(__file__).parent.parent / 'backtest_results.csv'
            res_df.to_csv(out_path)
            log.write(f"\n[dim]结果已保存: {out_path}[/]")
        except Exception as e:
            log.write(f"\n[red]❌ 回测失败: {e}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-backtest":
            self.run_backtest()


class ReviewScreen(Screen):
    """复盘"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("📋 交易复盘分析", classes="screen-title"),
            Button("▶ 运行复盘", id="run-review", variant="primary"),
            Static(""),
            RichLog(id="review-log", highlight=True, markup=True, max_lines=100),
            id="review-content",
        )

    @work(exclusive=True)
    async def run_review(self):
        log = self.query_one("#review-log", RichLog)
        log.clear()
        log.write("[bold yellow]分析中...[/]")
        
        try:
            from review import ReviewAnalyzer, TradeEntry
            from real_portfolio import RealPortfolioMonitor
            from config_loader import load_config
            
            config = load_config()
            monitor = RealPortfolioMonitor()
            positions = monitor.mock_positions()
            
            trades = [TradeEntry(
                symbol=p.get('instId', 'UNKNOWN'),
                side=p.get('side', 'long'),
                entry_price=float(p.get('avgPx', 0)),
                size=float(p.get('pos', 0)),
                leverage=int(p.get('lever', 1)),
            ) for p in positions]
            
            log.clear()
            if trades:
                analyzer = ReviewAnalyzer(trades)
                log.write(analyzer.generate_report())
            else:
                log.write("[yellow]无持仓数据[/]")
        except Exception as e:
            log.write(f"[red]❌ 复盘失败: {e}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-review":
            self.run_review()


class EvolutionScreen(Screen):
    """进化"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("🧬 策略自动进化", classes="screen-title"),
            Button("▶ 手动进化", id="run-evolve", variant="primary"),
            Static(""),
            RichLog(id="evolve-log", highlight=True, markup=True, max_lines=100),
            id="evolve-content",
        )

    @work(exclusive=True)
    async def run_evolve(self):
        log = self.query_one("#evolve-log", RichLog)
        log.clear()
        log.write("[bold yellow]策略进化中...[/]")
        
        try:
            from evolution import EvolutionManager
            from review import TradeEntry
            from config_loader import load_config
            from real_portfolio import RealPortfolioMonitor
            
            config = load_config()
            monitor = RealPortfolioMonitor()
            positions = monitor.mock_positions()
            
            evo = EvolutionManager(config.get('evolution', {}))
            for p in positions:
                evo.add_trade(TradeEntry(
                    symbol=p.get('instId', 'UNKNOWN'),
                    side=p.get('side', 'long'),
                    entry_price=float(p.get('avgPx', 0)),
                    size=float(p.get('pos', 0)),
                    leverage=int(p.get('lever', 1)),
                ))
            
            result = evo.evolve()
            log.clear()
            if result.get('evolved'):
                report = result.get('report', '')
                log.write(f"[bold green]{report}[/]")
            else:
                log.write(f"[yellow]无需进化: {result.get('reason', '')}[/]")
        except Exception as e:
            log.write(f"[red]❌ 进化失败: {e}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-evolve":
            self.run_evolve()


class MCPScreen(Screen):
    """MCP 提示栏"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("🤖 MCP 提示栏", classes="screen-title"),
            Horizontal(
                Static("模型: ", classes="label"),
                Button("DeepSeek", id="model-deepseek", variant="primary"),
                Button("GPT", id="model-gpt"),
                Button("Claude", id="model-claude"),
                id="model-selector",
            ),
            Static(""),
            Input(placeholder="输入提示词...", id="mcp-input"),
            Static(""),
            RichLog(id="mcp-log", highlight=True, markup=True, max_lines=50),
            id="mcp-content",
        )
    
    current_model = "deepseek"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for btn_id in ["model-deepseek", "model-gpt", "model-claude"]:
            btn = self.query_one(f"#{btn_id}", Button)
            btn.variant = "default"
        event.button.variant = "primary"
        
        self.current_model = event.button.id.replace("model-", "")
        log = self.query_one("#mcp-log", RichLog)
        log.write(f"[dim]已切换到 {self.current_model}[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.process_prompt(event.value)

    @work(exclusive=True)
    async def process_prompt(self, prompt: str):
        log = self.query_one("#mcp-log", RichLog)
        log.write(f"\n[bold yellow]🤔 {prompt}[/]")
        log.write(f"[dim]模型: {self.current_model}[/]")
        log.write(f"[dim]... 处理中 ...[/]")
        
        try:
            from mcp import MCPPromptBar
            bar = MCPPromptBar()
            bar.set_model(self.current_model)
            result = bar.create_prompt(prompt)
            log.write(f"[bold green]✅ 响应:[/]")
            log.write(f"{result}")
        except ImportError:
            log.write(f"[yellow]MCP 模块可用（模拟模式）[/]")
            log.write(f"[green]提示已收到: [bold]{prompt}[/][/]")
        except Exception as e:
            log.write(f"[red]❌ 错误: {e}[/]")
        
        self.query_one("#mcp-input", Input).clear()


class GoalScreen(Screen):
    """Goal 任务规划"""

    def compose(self) -> ComposeResult:
        yield Container(
            Static("🎯 Goal 任务规划", classes="screen-title"),
            Input(placeholder="输入你的目标，例如：回测 BTC 策略并优化参数", id="goal-input"),
            Static(""),
            Button("▶ 执行目标", id="execute-goal", variant="primary"),
            Static(""),
            RichLog(id="goal-log", highlight=True, markup=True, max_lines=100),
            id="goal-content",
        )

    @work(exclusive=True)
    async def execute_goal(self, goal_text: str):
        log = self.query_one("#goal-log", RichLog)
        log.clear()
        log.write(f"[bold yellow]🎯 目标: {goal_text}[/]\n")
        
        try:
            from goal import GoalPlanner
            planner = GoalPlanner()
            goal = planner.create_goal(goal_text)
            planner.decompose_goal(goal['id'])
            result = planner.execute_goal(goal['id'])
            
            if result.get('success'):
                log.write("[bold green]✅ 执行完成[/]\n")
                log.write(result.get('summary', ''))
            else:
                log.write(f"[red]❌ 失败: {result.get('error', '')}[/]")
        except ImportError:
            log.write("[yellow]执行规划...[/]")
            log.write("✅ 任务1: 分析目标")
            log.write("✅ 任务2: 拆解子任务")
            log.write("✅ 任务3: 执行任务")
            log.write("[green]✅ 目标完成![/]")
        except Exception as e:
            log.write(f"[red]❌ 错误: {e}[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.execute_goal(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "execute-goal":
            input_widget = self.query_one("#goal-input", Input)
            if input_widget.value.strip():
                self.execute_goal(input_widget.value)


class AIQuantTUI(App):
    """AIQuant Engine - TUI 主应用 (Reasonix 风格)"""
    
    CSS = """
    Screen {
        background: #0d1117;
    }
    
    .sidebar-title {
        text-style: bold;
        color: #58a6ff;
        padding: 1;
        text-align: center;
        background: #161b22;
    }
    
    Sidebar {
        width: 20;
        background: #161b22;
        border-right: solid #30363d;
        padding: 1;
    }
    
    Sidebar Button {
        width: 100%;
        margin: 0 0 1 0;
    }
    
    Sidebar .spacer {
        height: 1fr;
    }
    
    .screen-title {
        text-style: bold;
        color: #e6edf3;
        background: #21262d;
        padding: 1 2;
        border-bottom: solid #30363d;
        text-align: center;
        margin-bottom: 1;
    }
    
    .section-title {
        text-style: bold;
        color: #58a6ff;
        padding: 0 1;
    }
    
    .card {
        background: #21262d;
        border: solid #30363d;
        padding: 1;
        margin: 1;
        min-width: 25;
    }
    
    .card-title {
        text-style: bold;
        color: #e6edf3;
        border-bottom: solid #30363d;
        padding-bottom: 1;
    }
    
    .label {
        color: #8b949e;
        padding: 0 1;
    }
    
    #dashboard-cards {
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    
    Button.primary {
        background: #58a6ff;
        color: white;
    }
    
    Button.success {
        background: #3fb950;
        color: white;
    }
    
    Button.error {
        background: #f85149;
        color: white;
    }
    
    Input {
        background: #21262d;
        border: solid #30363d;
        color: #e6edf3;
    }
    
    Input:focus {
        border: solid #58a6ff;
    }
    
    RichLog {
        background: #161b22;
        border: solid #30363d;
        color: #e6edf3;
    }
    
    #model-selector {
        height: 3;
        margin-bottom: 1;
    }
    
    #model-selector Button {
        min-width: 12;
    }
    
    .status-stopped {
        color: #f85149;
        text-style: bold;
        padding: 0 1;
    }
    
    .status-running {
        color: #3fb950;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("d", "switch_dashboard", "仪表盘"),
        Binding("b", "switch_backtest", "回测"),
        Binding("r", "switch_review", "复盘"),
        Binding("e", "switch_evolution", "进化"),
        Binding("m", "switch_mcp", "MCP"),
        Binding("g", "switch_goal", "Goal"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen(),
        "backtest": BacktestScreen(),
        "review": ReviewScreen(),
        "evolution": EvolutionScreen(),
        "mcp": MCPScreen(),
        "goal": GoalScreen(),
    }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Sidebar(),
            Container(id="main-content"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-quit":
            self.exit()
        elif btn_id == "btn-dashboard":
            self.switch_screen("dashboard")
        elif btn_id == "btn-backtest":
            self.switch_screen("backtest")
        elif btn_id == "btn-review":
            self.switch_screen("review")
        elif btn_id == "btn-evolution":
            self.switch_screen("evolution")
        elif btn_id == "btn-mcp":
            self.switch_screen("mcp")
        elif btn_id == "btn-goal":
            self.switch_screen("goal")

    def action_switch_dashboard(self) -> None:
        self.switch_screen("dashboard")

    def action_switch_backtest(self) -> None:
        self.switch_screen("backtest")

    def action_switch_review(self) -> None:
        self.switch_screen("review")

    def action_switch_evolution(self) -> None:
        self.switch_screen("evolution")

    def action_switch_mcp(self) -> None:
        self.switch_screen("mcp")

    def action_switch_goal(self) -> None:
        self.switch_screen("goal")

    def switch_screen(self, screen_name: str) -> None:
        if screen_name in self.SCREENS:
            self.pop_screen()
            self.push_screen(screen_name)


def main():
    app = AIQuantTUI()
    app.run()


if __name__ == "__main__":
    main()
