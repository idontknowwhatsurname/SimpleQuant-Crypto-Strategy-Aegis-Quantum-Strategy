# 🛡️ Aegis Quantum Strategy (AQS)

**AI 原生的加密货币量化交易框架 · 面向中文开发者**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Trading: Crypto](https://img.shields.io/badge/Trading-Crypto-green.svg)]()

**Aegis Quantum Strategy** 是一个 AI 原生的加密货币量化交易框架。它的核心差异化在于三层智能：

---

## 🧠 核心差异化

### 1. 多模型 AI Router — 不绑定单一 LLM

市场分析走 **DeepSeek**（便宜高频），风险评估走 **GPT**（准确），策略复核走 **Claude**（推理深）。按任务类型自动路由，用最低成本获得最优决策质量。

### 2. Hermes 式自动进化 — 策略在交易中自我迭代

每积累 ~10 笔交易，系统自动复盘 → 提取有效/无效模式 → 生成/更新 SKILL.md 策略文档 → 调优参数。策略不是写死的，而是活着的。

### 3. 四层信号 + 机构级风控

宏观(VIX) + 链上(Funding/OI) + 预测市场(Polymarket) + 叙事信号 → 统一 Z-score 矩阵。叠加 Kelly-ATR 仓位、多层熔断（VIX/回撤/日亏损）、分级降仓，三重防护。

**这是一个会自己复盘、自己优化的 AI 交易 Agent，而不仅仅是一个策略脚本。**

---

## ✨ 特性一览

- **四层信号聚合**: 宏观 (VIX) + 链上 (Funding/OI) + 预测市场 + 叙事信号 → 统一 Z-score 决策矩阵
- **自适应 Kelly-ATR 仓位管理**: 基于实时波动率 (ATR) 和历史胜率 (Kelly 准则) 的动态仓位管理
- **机构级风控保障**: 多层熔断机制，包括 VIX 熔断、最大回撤保护、冷却期
- **多模型 AI 路由**: DeepSeek 默认（省钱），GPT 复核（准确），Claude 推理（深度）
- **多交易所支持**: OKX / Binance / Gate 统一抽象层
- **多通道通知**: Telegram / 企业微信 / Discord / QQ / 邮件
- **自动进化**: Hermes Agent 风格，每 ~10 笔交易自优化策略
- **交易复盘系统**: Sharpe / Sortino / Calmar / MDD / 杠杆分析 / 持仓时长分析
- **全面报告**: 回测绩效报告、实盘持仓监控、专业复盘报告

---

## 📊 架构

```
┌──────────────────────────────────────────────────────┐
│                    用户层                               │
│  Telegram │ 微信 │ Discord │ QQ │ 邮件 │ CLI          │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              AI Router (多模型路由)                     │
│  DeepSeek (市场/信号) │ GPT (风控/紧急) │ Claude (策略)│
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              四层信号引擎                               │
│  L1: 宏观情绪 ── VIX                                  │
│  L2: 链上结构 ── Funding Rate / Open Interest          │
│  L3: 预测市场 ── Polymarket 概率                       │
│  L4: 叙事动量 ── AI 主题叙事评分                        │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              风控层                                     │
│  Kelly-ATR 仓位 · ATR 止损 · 多层熔断 · 分级降仓       │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              交易所层                                    │
│  OKX │ Binance │ Gate.io (统一 ExchangeBase 接口)     │
└──────────────────────────────────────────────────────┘

         ▲ 自动进化循环 ▼ (每 ~10 笔交易)
  ┌──────────────────────────────────────────────────────┐
  │  复盘分析 → 模式发现 → SKILL.md 更新 → 参数调优     │
  └──────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy.git
cd SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp config.toml.example config.toml
# 编辑 config.toml 填入你的 API Key 等配置

# 4. 下载数据
python run.py download

# 5. 回测
python run.py backtest

# 6. 查看回测报告
python run.py report

# 7. 查看当前持仓
python run.py portfolio

# 8. 交易复盘分析
python run.py review

# 9. 手动触发策略进化
python run.py evolve

# 10. 启动实盘引擎
python run.py
```

### 或使用环境变量

```bash
export OKX_API_KEY="your_key"
export OKX_SECRET="your_secret"
export OKX_PASSPHRASE="your_passphrase"
export DEEPSEEK_API_KEY="your_deepseek_key"
```

---

## 📁 项目结构

```
├── engine.py               # 实盘交易引擎 (v2.0)
├── run.py                  # 一键启动入口
├── signals.py              # 四层信号引擎 (L1-L4)
├── risk_manager.py         # 风控模块 (Kelly-ATR/止损/熔断)
├── market_regime.py        # 市场状态识别 (牛/熊/震荡/高波动)
├── ai_router.py            # AI 多模型路由
├── order_executor.py       # 订单执行器
├── config_loader.py        # 配置加载器 (TOML + 环境变量)
├── results_analyzer.py     # 绩效分析 (Sharpe/Sortino/Calmar/VaR)
├── real_portfolio.py       # 实盘仓位监控
├── backtester.py           # 回测引擎
├── data_loader.py          # 数据加载器
├── okx_downloader.py       # OKX 数据下载器
│
├── exchange/               # 多交易所抽象层
│   ├── base.py             #   ExchangeBase 接口
│   ├── okx.py              #   OKX 实现
│   ├── binance.py          #   Binance 实现
│   ├── gate.py             #   Gate.io 实现
│   └── factory.py          #   交易所工厂
│
├── notify/                 # 多通道通知
│   ├── notifier.py         #   NotifyManager 统一管理器
│   └── channels/           #   各渠道适配器
│       ├── telegram.py     #   Telegram
│       ├── wechat.py       #   企业微信
│       ├── discord.py      #   Discord
│       ├── qq.py           #   QQ Bot
│       └── email.py        #   Gmail/SMTP
│
├── review/                 # 交易复盘分析
│   └── analyzer.py         #   ReviewAnalyzer
│
├── evolution/              # 自动进化引擎
│   └── manager.py          #   EvolutionManager (Hermes 风格)
│
├── config.toml.example     # 完整配置模板
└── requirements.txt        # 依赖清单
```

---

## 🤖 AI Router 任务路由

| 任务类型 | 默认模型 | 原因 |
|---------|---------|------|
| 市场分析 | DeepSeek | 便宜，日常分析够用 |
| 信号生成 | DeepSeek | 便宜，高频调用 |
| 风险评估 | GPT-4 | 准确性要求高 |
| 策略复核 | Claude | 推理能力强 |
| 紧急决策 | GPT-4 | 响应速度快 |

---

## 🛡️ 风控机制

### 多层熔断

| 层级 | 触发条件 | 动作 |
|------|---------|------|
| L1 | VIX > 40 | 全部平仓，冷却 3 天 |
| L2 | 回撤 > 15% | 全部平仓，冷却 3 天 |
| L3 | 单日亏损 > 5% | 全部平仓，冷却 3 天 |
| L4 | 回撤 3-15% | 分级降仓 |

### Kelly-ATR 仓位管理

- 使用半 Kelly 公式计算最优仓位
- ATR 止损距离反推最大仓位上限
- 动态调整，适应市场波动

---

## 🔧 开发

```bash
# 安装开发依赖
pip install -e .[test]

# 运行测试
python -m pytest tests/
```

---

## 📝 更新日志

### v2.0.0 (2026-05-31)
- ✅ 多交易所抽象层 (OKX / Binance / Gate)
- ✅ AI Router 多模型路由 (DeepSeek / GPT / Claude)
- ✅ 多通道通知 (Telegram / 微信 / Discord / QQ / 邮件)
- ✅ 自动进化引擎 (Hermes Agent 风格，每 ~10 笔交易自优化)
- ✅ 交易复盘系统 (Sharpe / 胜率 / 杠杆 / 持仓时长分析)
- ✅ 市场状态识别 (牛 / 熊 / 震荡 / 高波动)
- ✅ v2.0 实盘引擎，集成所有模块

### v1.0.0 (2026-05-30)
- ✅ 四层信号引擎 (L1-L4)
- ✅ Kelly-ATR 仓位管理
- ✅ 多层风控熔断
- ✅ OKX 数据下载器
- ✅ 通知模块 (Telegram/微信/飞书)

---

## ⚠️ 免责声明

本软件仅供教育和研究目的。加密货币交易存在重大风险。请勿交易超过您能承受损失的金额。

## 📄 许可证

MIT License
