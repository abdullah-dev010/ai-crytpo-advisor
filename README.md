# AI Crypto Advisor

An intelligent cryptocurrency trading advisor powered by AI, featuring LSTM-based price predictions, sentiment analysis, and automated trading signals.

## 🚀 Features

### Core Functionality
- **Real-time Market Analysis**: Live price data from CoinGecko API
- **AI Price Forecasting**: LSTM neural networks predict 24-hour price movements
- **Sentiment Analysis**: News-based market mood detection using VADER
- **Automated Trading Signals**: BUY/SELL recommendations with confidence levels
- **Risk Management**: Dynamic stop-loss and take-profit calculations
- **Portfolio Tracking**: Manage holdings, track P&L, and ROI

### Dashboard Tabs
1. **📊 Market Overview**: Price charts, AI forecasts, sentiment gauges, RSI indicators
2. **🎯 Trade Advisor**: Signal generation, position sizing, entry/exit levels
3. **💼 Portfolio**: Asset management, holdings tracking, performance metrics
4. **📜 History**: Trade journal, execution logs, P&L analysis
5. **🧪 Backtest**: Strategy performance testing, capital growth curves
6. **🧠 Insights**: Fear & Greed Index, economic calendar, market intelligence

### Supported Assets
- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- Binance Coin (BNB)
- Ripple (XRP)
- Cardano (ADA)
- Dogecoin (DOGE)
- Avalanche (AVAX)
- Polkadot (DOT)
- Shiba Inu (SHIB)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Setup Steps

1. **Clone or Download the Repository**
   ```bash
   git clone <repository-url>
   cd ai-crypto-advisor
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate Virtual Environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run Initial Setup**
   ```bash
   python src/data_collection.py
   python src/model_training.py
   ```

## 🚀 Usage

### Quick Start
Use the provided batch file for Windows:
```bash
run_app.bat
```

Or run manually:
```bash
streamlit run main_dashboard.py
```

### Manual Execution Steps

1. **Data Collection**
   ```bash
   python src/data_collection.py
   ```
   Fetches historical price data for all supported cryptocurrencies.

2. **Model Training**
   ```bash
   python src/model_training.py
   ```
   Trains LSTM models for price prediction.

3. **Launch Dashboard**
   ```bash
   streamlit run main_dashboard.py
   ```
   Opens the web interface at `http://localhost:8501`

## 📊 How It Works

### AI Prediction Engine
- **LSTM Models**: Trained on 365 days of historical data
- **Technical Indicators**: RSI, EMA for signal confirmation
- **Sentiment Integration**: News headlines analyzed for market mood
- **Signal Locking**: Prevents signal spam with 4-hour lock mechanism

### Risk Management
- **Position Sizing**: Dynamic allocation based on asset type and signal strength
- **Stop Loss**: Automatic risk limits (2-4% based on volatility)
- **Take Profit**: 3% target levels with trailing stops

### Backtesting
- **Strategy Simulation**: Historical performance testing
- **Asset-Specific Logic**: Different strategies for major coins vs. altcoins
- **Performance Metrics**: ROI, win rate, capital growth visualization

## 📁 Project Structure

```
├── main_dashboard.py          # Main Streamlit application
├── run_app.bat               # Windows launcher script
├── signal_lock.json          # Signal locking mechanism
├── data/                     # Historical data and portfolio
│   ├── *_historical_prices.csv
│   ├── portfolio.csv
│   ├── trade_history.csv
│   └── tweets_news.csv
├── models/                   # Trained AI models
│   ├── lstm_model_*.h5
│   └── scaler_*.pkl
└── src/                      # Source code
    ├── advisor_logic.py      # Core AI logic and predictions
    ├── data_collection.py    # API data fetching
    ├── model_training.py     # LSTM model training
    └── test_model.py         # Model validation
```

## 🔧 Configuration

### API Keys
- **NewsAPI**: Update `NEWS_API_KEY` in `advisor_logic.py`
- **CoinGecko**: No API key required (free tier)

### Model Parameters
- **Look Back**: 60 days for LSTM input
- **Training Epochs**: 20 epochs per model
- **Update Interval**: 60 minutes for data refresh

### Risk Settings
- **Lock Duration**: 4 hours between signals
- **Position Sizes**: 12-20% based on asset volatility
- **Stop Loss**: 1.5-4% trailing stops

## ⚠️ Disclaimer

This application is for educational and informational purposes only. Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor. Past performance does not guarantee future results. Always conduct your own research and consider consulting with a qualified financial advisor before making investment decisions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request



## 🆘 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the troubleshooting section in the dashboard
- Ensure all dependencies are properly installed

---

**Built with ❤️ using Streamlit, TensorFlow, and Python**
