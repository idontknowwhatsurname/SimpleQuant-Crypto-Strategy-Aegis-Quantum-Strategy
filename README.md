# 🛡️ Aegis Quantum Strategy (AQS)

**An AI-native crypto quant trading framework for Chinese-speaking developers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Trading: Crypto](https://img.shields.io/badge/Trading-Crypto-green.svg)]()

**Aegis Quantum Strategy** is an AI-native crypto quantitative trading framework. Its core differentiation is three-layer intelligence:

---

## 🧠 Core Differentiators

### 1. Multi-Model AI Router — Not Tied to a Single LLM

Market analysis uses **DeepSeek** (cheap, high-frequency), risk assessment uses **GPT** (accuracy), strategy review uses **Claude** (deep reasoning). Tasks are automatically routed to the optimal model — lowest cost for the best decision quality.

### 2. Hermes-Style Auto-Evolution — Strategies Self-Iterate While Trading

Every ~10 trades, the system automatically: reviews trades → extracts winning/losing patterns → generates/updates SKILL.md → tunes parameters. The strategy is not hard-coded — it evolves.

### 3. Four-Layer Signals + Institutional Risk Controls

Macro (VIX) + On-chain (Funding/OI) + Prediction Market (Polymarket) + Narrative signals → unified Z-score decision matrix. Overlaid with Kelly-ATR position sizing, multi-layer circuit breakers (VIX/drawdown/daily loss), and tiered position reduction.

**This is an AI trading agent that reviews and optimizes itself — not just a strategy script.**

---

## ✨ Features

- **Four-layer signal aggregation**: Macro + On-chain + Prediction market + Narrative → unified Z-score
- **Adaptive Kelly-ATR position sizing**: Dynamic sizing based on real-time ATR volatility and historical win rate
- **Institutional-grade risk management**: VIX circuit breaker, max drawdown protection, cooldown periods
- **Multi-model AI routing**: DeepSeek (default), GPT (validation), Claude (reasoning)
- **Multi-exchange support**: OKX / Binance / Gate unified abstraction
- **Multi-channel notifications**: Telegram / WeChat / Discord / QQ / Email
- **Auto-evolution**: Hermes Agent-style, self-optimizing every ~10 trades
- **Trade review system**: Sharpe / Sortino / Calmar / MDD / leverage / duration analysis
- **Comprehensive reports**: Backtest reports, live portfolio monitoring, professional review reports

---

## 📊 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  User Layer                            │
│  Telegram │ WeChat │ Discord │ QQ │ Email │ CLI       │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              AI Router (Multi-Model)                   │
│  DeepSeek (market/signal) │ GPT (risk/emergency)      │
│  Claude (strategy review)                              │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              Four-Layer Signal Engine                  │
│  L1: Macro ── VIX                                     │
│  L2: On-chain ── Funding Rate / Open Interest          │
│  L3: Prediction Market ── Polymarket                    │
│  L4: Narrative ── AI theme narrative scoring           │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              Risk Control Layer                         │
│  Kelly-ATR · ATR Stop-Loss · Circuit Breaker          │
│  Tiered Drawdown Reduction                             │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              Exchange Layer                             │
│  OKX │ Binance │ Gate.io (unified ExchangeBase)       │
└──────────────────────────────────────────────────────┘

         ▲ Auto-Evolution Loop (every ~10 trades)
  ┌──────────────────────────────────────────────────────┐
  │  Review → Pattern Discovery → SKILL.md Update       │
  │  → Parameter Tuning                                  │
  └──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/idontknowwhatsurname/SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy.git
cd SimpleQuant-Crypto-Strategy-Aegis-Quantum-Strategy

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp config.toml.example config.toml

# 4. Download data
python run.py download

# 5. Backtest
python run.py backtest

# 6. View backtest report
python run.py report

# 7. View portfolio
python run.py portfolio

# 8. Trade review
python run.py review

# 9. Manual evolution
python run.py evolve

# 10. Start live engine
python run.py
```

---

## 📁 Project Structure

```
├── engine.py               # Live trading engine (v2.0)
├── run.py                  # CLI entry point
├── signals.py              # Four-layer signal engine
├── risk_manager.py         # Risk management module
├── market_regime.py        # Market state detection
├── ai_router.py            # Multi-model AI router
├── order_executor.py       # Order executor
├── config_loader.py        # Config loader (TOML + env)
├── results_analyzer.py     # Performance analysis
├── real_portfolio.py       # Live portfolio monitor
├── backtester.py           # Backtesting engine
├── data_loader.py          # Data loader
├── okx_downloader.py       # OKX data downloader
│
├── exchange/               # Multi-exchange abstraction
│   ├── base.py             #   ExchangeBase interface
│   ├── okx.py              #   OKX implementation
│   ├── binance.py          #   Binance implementation
│   ├── gate.py             #   Gate.io implementation
│   └── factory.py          #   Exchange factory
│
├── notify/                 # Multi-channel notifications
│   ├── notifier.py         #   NotifyManager
│   └── channels/           #   Channel adapters
│       ├── telegram.py     #   Telegram
│       ├── wechat.py       #   WeChat Work
│       ├── discord.py      #   Discord
│       ├── qq.py           #   QQ Bot
│       └── email.py        #   Gmail/SMTP
│
├── review/                 # Trade review analysis
│   └── analyzer.py         #   ReviewAnalyzer
│
├── evolution/              # Auto-evolution engine
│   └── manager.py          #   EvolutionManager
│
├── config.toml.example     # Config template
└── requirements.txt        # Dependencies
```

---

## 🤖 AI Router

| Task Type | Default Model | Rationale |
|-----------|--------------|-----------|
| Market Analysis | DeepSeek | Cheap, sufficient |
| Signal Generation | DeepSeek | Cheap, high-frequency |
| Risk Assessment | GPT-4 | Accuracy-critical |
| Strategy Review | Claude | Strong reasoning |
| Emergency Decision | GPT-4 | Fast response |

---

## 🛡️ Risk Controls

| Tier | Trigger | Action |
|------|---------|--------|
| L1 | VIX > 40 | Close all, 3-day cooldown |
| L2 | Drawdown > 15% | Close all, 3-day cooldown |
| L3 | Daily loss > 5% | Close all, 3-day cooldown |
| L4 | Drawdown 3-15% | Tiered position reduction |

---

## 📝 Changelog

### v2.0.0 (2026-05-31)
- ✅ Multi-exchange abstraction (OKX / Binance / Gate)
- ✅ AI Router (DeepSeek / GPT / Claude)
- ✅ Multi-channel notifications (Telegram / WeChat / Discord / QQ / Email)
- ✅ Auto-evolution engine (Hermes-style, self-optimizing)
- ✅ Trade review system (Sharpe / win rate / leverage / duration)
- ✅ Market regime detection (bull / bear / range / volatile)
- ✅ v2.0 engine with full module integration

### v1.0.0 (2026-05-30)
- ✅ Four-layer signal engine
- ✅ Kelly-ATR position sizing
- ✅ Multi-layer circuit breakers
- ✅ OKX data downloader
- ✅ Notifications (Telegram/WeChat/Feishu)

---

## ⚠️ Disclaimer

This software is for educational and research purposes only. Cryptocurrency trading carries significant risk. Never trade more than you can afford to lose.

## 📄 License

MIT License
