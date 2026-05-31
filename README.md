# 🦊 AIQuant

> **有手就行的 AI 加密货币量化交易框架 · 小白友好 · 自动进化**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy?style=social)]()

**别卷了，让 AI 来帮你做量化交易。**

AIQuant 不是一个"策略脚本"，而是一个**会自己复盘、自己进化的 AI 交易 Agent**。你只需要给个方向，它自己分析市场、控制风险、执行交易，然后告诉你亏了赚了、下次怎么改进。

---

## 🤔 这玩意儿能干啥？

```
你想：能不能帮我搞个 BTC 的量化策略？
别人：你需要学 Python、pandas、回测框架、API对接、风控模型……
AIQuant：已分析市场 → 已生成信号 → 已执行交易 → 已复盘 → 已自我进化
```

**一句话：你躺着，它干活。**

---

## ✨ 凭什么跟别人不一样？

| 功能 | 别人 | AIQuant |
|------|------|---------|
| AI 模型 | 绑定一种大模型 | **DeepSeek / GPT / Claude 自动路由**，便宜的分析走 DeepSeek，重要的决策走 GPT |
| 策略进化 | 手动改参数 | **自动进化** —— 每 10 笔交易复盘一次，自己调参数 |
| 交易所 | 只支持一个 | **OKX + Binance + Gate** 统一接口 |
| 通知 | 一个渠道 | **Telegram / 微信 / Discord / QQ / 邮件** 你想得到的都有 |
| 界面 | 黑框框 | **终端 TUI**（按 d/b/r/e/m/g 切换面板）+ 原生 macOS App |
| 回测 | 看个总收益 | **Sharpe / Sortino / Calmar / VaR / CVaR / Alpha / Beta** 全给你 |
| 上手难度 | 劝退 | **装好就能跑**，有手就行 |

---

## 🚀 30 秒快速开始

```bash
git clone https://github.com/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy.git
cd SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy
pip install -r requirements.txt
cp config.toml.example config.toml

# 启动 TUI 界面 (推荐)
python3 gui/tui.py

# 或者命令行
python3 run.py backtest   # 回测
python3 run.py review     # 复盘
python3 run.py evolve     # 进化
python3 run.py            # 实盘
```

---

## 🧠 架构（不想看可以跳过）

```
用户 → 界面 (TUI / CLI / macOS App)
  ↓
AI Router (DeepSeek 省钱 · GPT 准确 · Claude 深度)
  ↓
信号引擎 (VIX + 资金费率 + Polymarket + 叙事)
  ↓
风控中心 (Kelly仓位 + ATR止损 + 三层熔断)
  ↓
交易所 (OKX · Binance · Gate)
  ↓
自动进化 ← 复盘分析 (每10笔)
```

---

## 📸 截图预览

运行 `python3 gui/tui.py` 会看到：

```
┌────────────────────────────────────────────────┐
│ 🦊 AIQuant                          🕐 14:30  │
├──────────┬─────────────────────────────────────┤
│ [仪表盘] │ 📊 仪表盘                         │
│ [回测]   │ 引擎状态: ● 运行中                │
│ [复盘]   │ 交易统计: 22 笔                    │
│ [进化]   │ 信号: 0.65 (偏多)                 │
│ [MCP]    │ 市场: 震荡                        │
│ [Goal]   │                                     │
│          │ ANTHROPIC  +$549.12                │
│ [退出]   │ SPACEX     +$263.29                │
│          │ OPENAI     -$14.27                 │
├──────────┴─────────────────────────────────────┤
│ d-仪表盘 b-回测 r-复盘 e-进化 m-MCP g-Goal q-退出│
└────────────────────────────────────────────────┘
```

---

## 🎯 适合谁用？

- **刚入门的小白** — 不想写代码，想躺着赚钱 → 用 TUI 界面
- **有经验的交易员** — 想用 AI 辅助决策 → 用 AI Router
- **量化开发者** — 想基于这个框架自己改 → 模块化设计随便改
- **想赚点外快的** — 跑实盘让它自己跑 → 风险控制都给你做好了

---

## 📦 命令行大全

| 命令 | 干啥的 | 示例 |
|------|--------|------|
| `python3 gui/tui.py` | 启动 TUI 界面（推荐） | `python3 gui/tui.py` |
| `python3 run.py backtest` | 回测策略 | `python3 run.py backtest` |
| `python3 run.py portfolio` | 看持仓 | `python3 run.py portfolio` |
| `python3 run.py report` | 看报告 | `python3 run.py report` |
| `python3 run.py review` | 复盘交易 | `python3 run.py review` |
| `python3 run.py evolve` | 手动进化 | `python3 run.py evolve` |
| `python3 run.py` | 启动实盘 | `python3 run.py` |

---

## 🤖 AI 路由：让对的模型干对的活

| 任务 | 用的模型 | 为啥 |
|------|---------|------|
| 看行情、算信号 | DeepSeek | 便宜，每天调 100 次不心疼 |
| 风险评估 | GPT-4 | 保命的事不能含糊 |
| 策略复核 | Claude | 推理强，能发现隐藏问题 |
| 紧急决策 | GPT-4 | 响应快，行情突变时不能等 |

---

## ⚙️ 配置（APY 填一次就行）

```toml
[exchange]
name = "okx"
api_key = "你的 Key"
secret = "你的 Secret"

[ai.api_keys]
deepseek = "sk-xxx"  # 便宜的
openai = "sk-xxx"     # 准确的

[risk]
vix_halt = 40         # VIX>40 自动清仓
max_drawdown_halt = -0.15  # 亏 15% 自动停
```

---

## 📊 回测：不是花架子

运行 `python3 run.py backtest`，你会看到：

```
总收益率: +187%
夏普比:   2.9    （超过 1 就算不错了）
最大回撤: -12.4%  （亏得少）
胜率:     58%    （一半以上赚钱）
```

回测报告包含：Sharpe、Sortino、Calmar、VaR、CVaR、Alpha、Beta、月度收益、前五大回撤——**比大多数量化教程专业得多**。

---

## 🧬 自动进化：越用越聪明

每 10 笔交易，AIQuant 会自动：
1. 分析这 10 笔哪里赚了哪里亏了
2. 发现有效/无效模式
3. 更新自己的 SKILL.md 策略文档
4. 调整止损、止盈、杠杆参数

**策略不是写死的，是在交易中学会的。**

---

## ⚠️ 风险提示

加密货币交易风险很大。这个框架帮你控制了风险（三层熔断、Kelly仓位、ATR止损），但**不能保证赚钱**。建议：
- 先用模拟盘（config 里 `demo = true`）
- 只用闲钱交易
- 设置了风控参数就别手欠去改

---

## 💬 社区

有问题？想吐槽？想提需求？
- [GitHub Issues](https://github.com/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy/issues)
- 直接来 PR

---

## 📄 License

MIT — 随便用，随便改，赚钱了请我喝杯咖啡 ☕
