# 🛡️ Aegis Quantum Strategy (AQS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Trading: Crypto](https://img.shields.io/badge/Trading-Crypto-green.svg)]()

**Aegis Quantum Strategy (AQS)** is a high-performance, multi-layered quantitative trading engine designed for cryptocurrency markets. It integrates macro sentiment, on-chain dynamics, and predictive modeling with a robust institutional-grade risk management framework.

---

## 🚀 Key Features

- **Multi-Layer Signal Aggregation**: Combines Macro (VIX), On-Chain (Funding/OI), and Narrative signals into a unified Z-score decision matrix.
- **Adaptive Kelly-ATR Sizing**: Dynamic position sizing based on real-time volatility (ATR) and historical win-rates (Kelly Criterion).
- **Institutional Risk Safeguards**: Multi-tier circuit breakers including VIX-halt, max drawdown protection, and cooldown periods.
- **AI-Enhanced Predictive Engine**: Real-time integration with LLMs (DeepSeek/GPT) for short-term price direction forecasting.
- **Comprehensive Reporting**: Generates interactive HTML dashboards and visual equity reports for portfolio monitoring.

---

## 📊 Architecture: The 4-Layer System

1. **L1: Macro Sentiment (35%)**: Monitors global market stress via VIX Z-scores.
2. **L2: On-Chain & Market Structure (40%)**: Analyzes Funding Rate crowding and Open Interest divergence.
3. **L3: Predictive Market Delta (15%)**: Captures momentum shifts in prediction markets (e.g., Polymarket).
4. **L4: Narrative Momentum (10%)**: Real-time sentiment analysis of market narratives.

---

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
AQS uses environment variables for security. Do not hardcode your keys.
```bash
export OKX_API_KEY="your_key"
export OKX_SECRET="your_secret"
export OKX_PASSPHRASE="your_passphrase"
export TG_TOKEN="your_telegram_bot_token"
export TG_CHAT="your_chat_id"
```

### 3. Run Backtest
```bash
python backtester.py
```

### 4. Start Live Engine
```bash
python engine.py
```

---

## 📈 Performance & Visualization
AQS automatically generates visual performance reports (`comprehensive_report.png`) and live dashboards (`dashboard.html`) to track your strategy's alpha in real-time.

---

## ⚠️ Disclaimer
*This software is for educational purposes only. Crypto trading involves significant risk. Never trade more than you can afford to lose.*

---

## 🌟 Support
If you find AQS useful, please consider giving it a ⭐ on GitHub and sharing it on X!
