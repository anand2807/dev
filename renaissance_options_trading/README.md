# 🏛️ Renaissance Options Trading System

A sophisticated algorithmic options trading system for the Indian stock market, inspired by Renaissance Technologies' quantitative approach. This system focuses on volatility-based profit maximization with minimal risk through advanced option chain analysis and directional trading strategies.

## 🌟 Features

### Core Capabilities
- **Volatility-Based Trading**: Captures market direction based on volatility patterns and option chain analysis
- **Advanced Greeks Calculation**: Real-time Delta, Gamma, Theta, Vega, and Rho calculations
- **Sophisticated Risk Management**: Portfolio-level risk controls with position sizing and exposure limits
- **Real-Time Market Analysis**: NSE/BSE market data integration with option chain analysis
- **Backtesting Engine**: Historical simulation to evaluate strategy performance
- **Interactive Dashboard**: Real-time monitoring with Streamlit-based web interface

### Trading Strategies
1. **Directional Volatility Strategy**: Captures directional movements based on market regime analysis
2. **Volatility Expansion Strategy**: Profits from volatility breakouts during low volatility periods
3. **Mean Reversion Strategy**: Contrarian approach during extreme volatility conditions
4. **Support/Resistance Bounce**: Trades based on key technical levels from option chain

### Advanced Features
- **Market Regime Detection**: Automatically identifies volatility regimes and market direction
- **Option Chain Pattern Recognition**: Detects gamma squeezes, unusual activity, and skew patterns
- **Portfolio Greeks Management**: Maintains portfolio-level Greek exposures within limits
- **Dynamic Position Sizing**: Risk-based position sizing with correlation adjustments
- **Multi-Timeframe Analysis**: Combines intraday and swing trading approaches

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd renaissance_options_trading
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure the system**:
```bash
cp config.json my_config.json
# Edit my_config.json with your preferences
```

### Basic Usage

#### 1. Market Analysis
```bash
python main.py --mode analysis
```

#### 2. Run Backtest
```bash
python main.py --mode backtest --start-date 2024-01-01 --end-date 2024-03-31
```

#### 3. Launch Dashboard
```bash
python main.py --mode dashboard
```
Then open http://localhost:8501 in your browser.

#### 4. Generate Report
```bash
python main.py --mode report --capital 100000
```

## 📊 System Architecture

```
Renaissance Options Trading System
├── Data Layer
│   ├── NSE/BSE Market Data
│   ├── Option Chain Analysis
│   └── Historical Data Management
├── Strategy Layer
│   ├── Volatility Strategies
│   ├── Signal Generation
│   └── Market Regime Detection
├── Portfolio Layer
│   ├── Position Management
│   ├── Risk Management
│   └── P&L Tracking
├── Execution Layer
│   ├── Order Management
│   ├── Greeks Calculation
│   └── Portfolio Balancing
└── Monitoring Layer
    ├── Real-time Dashboard
    ├── Performance Analytics
    └── Risk Monitoring
```

## 🎯 Trading Strategies Explained

### 1. Directional Volatility Strategy
- **Concept**: Identifies market direction using option chain analysis and volatility patterns
- **Entry**: When market shows clear directional bias with favorable volatility
- **Exit**: Profit target (30%) or stop loss (50%) or time decay (3 days to expiry)
- **Risk**: Limited to premium paid

### 2. Volatility Expansion Strategy
- **Concept**: Profits from volatility breakouts during low volatility periods
- **Entry**: Low volatility with gamma squeeze indicators
- **Exit**: Volatility expansion or time decay
- **Risk**: Premium paid for long options

### 3. Mean Reversion Strategy
- **Concept**: Contrarian approach during extreme volatility
- **Entry**: Extreme volatility with oversold/overbought conditions
- **Exit**: Mean reversion or stop loss
- **Risk**: Controlled through position sizing

### 4. Support/Resistance Bounce
- **Concept**: Trades bounces at key option chain levels
- **Entry**: Price testing major support/resistance from option chain
- **Exit**: Quick scalping approach with tight stops
- **Risk**: Small position sizes with quick exits

## 📈 Performance Metrics

The system tracks comprehensive performance metrics:

- **Return Metrics**: Total return, annualized return, risk-adjusted returns
- **Risk Metrics**: Maximum drawdown, Sharpe ratio, Sortino ratio
- **Trade Metrics**: Win rate, profit factor, average trade duration
- **Greek Metrics**: Portfolio delta, gamma, theta exposure
- **Risk Metrics**: VaR, position concentration, correlation exposure

## ⚙️ Configuration

### Key Configuration Parameters

```json
{
  "volatility_threshold": 0.15,        // Minimum volatility for trading
  "pcr_bullish_threshold": 0.8,       // PCR threshold for bullish bias
  "pcr_bearish_threshold": 1.2,       // PCR threshold for bearish bias
  "max_positions": 20,                // Maximum concurrent positions
  "max_daily_loss_pct": 2.0,         // Maximum daily loss percentage
  "risk_free_rate": 0.06,            // Risk-free rate for Greeks calculation
  "auto_trading": false               // Enable/disable auto-trading
}
```

### Strategy Parameters

Each strategy has configurable parameters:
- **Confidence Threshold**: Minimum confidence for signal execution
- **Profit Target**: Target profit percentage
- **Stop Loss**: Maximum loss percentage
- **Time Decay**: Days before expiry to exit

### Risk Management

- **Position Sizing**: Fixed risk or volatility-based sizing
- **Portfolio Limits**: Maximum delta, gamma, theta exposure
- **Correlation Limits**: Maximum correlation between positions
- **Drawdown Controls**: Stop trading on excessive losses

## 🔧 Advanced Usage

### Custom Strategy Development

```python
from src.strategies.volatility_strategies import DirectionalVolatilityStrategy

class MyCustomStrategy(DirectionalVolatilityStrategy):
    def generate_custom_signals(self):
        # Implement your custom logic
        pass
```

### Backtesting with Custom Parameters

```python
from src.backtesting.backtest_engine import BacktestEngine

engine = BacktestEngine(initial_capital=100000)
result = engine.run_backtest(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    strategy_params={
        'volatility_threshold': 0.12,
        'pcr_bullish_threshold': 0.75
    }
)
```

### Parameter Optimization

```python
param_ranges = {
    'volatility_threshold': [0.10, 0.15, 0.20],
    'pcr_bullish_threshold': [0.7, 0.8, 0.9],
    'pcr_bearish_threshold': [1.1, 1.2, 1.3]
}

optimization_result = engine.optimize_parameters(
    start_date, end_date, param_ranges
)
```

## 📱 Dashboard Features

### Real-Time Monitoring
- **Portfolio Overview**: Current positions, P&L, Greeks
- **Market Analysis**: Real-time option chain analysis
- **Trading Signals**: Live signal generation and execution
- **Risk Dashboard**: Real-time risk monitoring

### Interactive Charts
- **Equity Curve**: Portfolio performance over time
- **Greek Exposure**: Portfolio Greek evolution
- **Volatility Analysis**: Market volatility patterns
- **Trade Analysis**: Individual trade performance

### Controls
- **Position Management**: Close positions, adjust sizes
- **Risk Controls**: Emergency stops, limit adjustments
- **Strategy Controls**: Enable/disable strategies
- **Parameter Tuning**: Real-time parameter adjustments

## 🛡️ Risk Management

### Portfolio-Level Controls
- **Maximum Positions**: Limit concurrent positions
- **Delta Exposure**: Control directional risk
- **Gamma Exposure**: Manage convexity risk
- **Theta Decay**: Monitor time decay exposure
- **Vega Risk**: Control volatility sensitivity

### Position-Level Controls
- **Position Sizing**: Risk-based sizing algorithms
- **Stop Losses**: Automatic loss limitation
- **Profit Targets**: Systematic profit taking
- **Time Stops**: Exit before excessive decay

### System-Level Controls
- **Daily Loss Limits**: Stop trading on large losses
- **Drawdown Controls**: Reduce size during drawdowns
- **Correlation Limits**: Avoid concentrated risks
- **Volatility Filters**: Adjust to market conditions

## 📊 Backtesting

### Historical Simulation
- **Data Quality**: Uses NSE historical data
- **Realistic Execution**: Includes slippage and commissions
- **Multiple Timeframes**: Daily and intraday backtesting
- **Walk-Forward Analysis**: Out-of-sample testing

### Performance Analysis
- **Statistical Metrics**: Comprehensive performance statistics
- **Risk Analysis**: Drawdown, VaR, stress testing
- **Trade Analysis**: Win/loss analysis, holding periods
- **Sensitivity Analysis**: Parameter sensitivity testing

### Optimization
- **Grid Search**: Systematic parameter optimization
- **Genetic Algorithms**: Advanced optimization methods
- **Cross-Validation**: Robust parameter selection
- **Overfitting Prevention**: Out-of-sample validation

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning Integration**: ML-based signal generation
- **Multi-Asset Support**: Stocks, commodities, currencies
- **Advanced Strategies**: Iron condors, butterflies, calendars
- **Real-Time Execution**: Broker API integration
- **Mobile App**: iOS/Android trading app

### Advanced Analytics
- **Regime Detection**: Advanced market regime identification
- **Sentiment Analysis**: News and social media sentiment
- **Flow Analysis**: Institutional flow detection
- **Volatility Forecasting**: Advanced volatility models

## ⚠️ Disclaimer

This system is for educational and research purposes. Options trading involves substantial risk and is not suitable for all investors. Past performance does not guarantee future results. Always:

- **Paper Trade First**: Test strategies before live trading
- **Understand Risks**: Options can expire worthless
- **Use Proper Position Sizing**: Never risk more than you can afford to lose
- **Stay Informed**: Keep up with market conditions and regulations
- **Seek Professional Advice**: Consult with financial advisors

## 📞 Support

For questions, issues, or contributions:
- **Documentation**: Check this README and code comments
- **Issues**: Report bugs and feature requests
- **Discussions**: Join community discussions
- **Contributions**: Submit pull requests for improvements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for the Indian options trading community**

*"In God we trust. In data we verify."* - Renaissance Technologies Philosophy