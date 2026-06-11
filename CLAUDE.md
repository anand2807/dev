# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

Two independent projects live at the root:

- `renaissance_options_trading/` — the main project: a Python-based algorithmic options trading system for the Indian market (NSE/BSE).
- `agenticai/` — a small, standalone set of marketing/email utilities (Jupyter notebook + two Python mailer scripts). No shared code with the main project.

All work below refers to `renaissance_options_trading/` unless otherwise noted.

## Commands

All commands must be run from inside `renaissance_options_trading/`.

```bash
# Install dependencies
pip install -r requirements.txt

# Run market analysis (default mode)
python main.py --mode analysis

# Run a backtest over a date range
python main.py --mode backtest --start-date 2024-01-01 --end-date 2024-03-31

# Launch the Streamlit dashboard (http://localhost:8501)
python main.py --mode dashboard
# or directly:
python run_dashboard.py

# Generate a performance report
python main.py --mode report --capital 100000

# Full system demo (no live data required)
python examples/demo.py

# Run tests
pytest

# Format code
black .
```

Custom capital and config file can be passed to any mode:
```bash
python main.py --mode analysis --capital 500000 --config my_config.json
```

## Architecture

The system is structured in five layers, each in its own `src/` subdirectory. Components are wired together by `RenaissanceOptionsTrader` in `main.py`, which is the only place that instantiates and connects everything.

**Data** (`src/data/market_data.py`) — `MarketDataManager` is the single entry point for all market data. It fetches from NSEPy (primary) and YFinance (fallback), parses the NSE option chain, and exposes helpers like `get_option_chain()`, `get_historical_data()`, and `calculate_put_call_ratio()`.

**Analytics** (`src/utils/greeks.py`) — `GreeksCalculator` implements Black-Scholes pricing and all five Greeks (Delta, Gamma, Theta, Vega, Rho) plus implied volatility via `scipy.optimize`. `PortfolioGreeks` aggregates Greeks across positions. `risk_free_rate` defaults to 0.06 (RBI repo rate).

**Strategy** (`src/strategies/volatility_strategies.py`) — `DirectionalVolatilityStrategy` is the core strategy class. It calls `MarketDataManager` to determine the current `VolatilityRegime` and `MarketDirection` (both `Enum`s), then generates a list of `TradingSignal` dataclasses. `RiskManager` is a separate class that computes position sizes. The three other strategies (Volatility Expansion, Mean Reversion, Support/Resistance Bounce) extend or compose the core class.

**Portfolio** (`src/portfolio/portfolio_manager.py`) — `PortfolioManager` receives `TradingSignal` objects via `process_signal()`, manages open `Position` and `Order` objects, runs `update_positions()` on each cycle, and enforces portfolio-level risk limits via `check_risk_limits()`. It holds cash balance and computes P&L independently of the strategy layer.

**Monitoring** (`src/monitoring/dashboard.py`) — Streamlit app that pulls live data from `MarketDataManager` and `PortfolioManager` on each refresh. It is launched by `run_dashboard()` from `main.py` or directly via `run_dashboard.py`.

### Data flow

```
MarketDataManager
       │
       ▼
DirectionalVolatilityStrategy  →  TradingSignal[]
                                        │
                                        ▼
                               PortfolioManager  →  Position / Order / Trade
                                        │
                                        ▼
                               Dashboard (read-only consumer)
```

### Import paths

`main.py` appends `src/` to `sys.path` so top-level scripts can import with `from src.X.Y import Z`. Inside `src/`, modules use relative imports (`from ..utils.greeks import GreeksCalculator`).

## Configuration

`config.json` at the project root is the default config; override with `--config <file>`. `RenaissanceOptionsTrader._load_config()` deep-merges a user file on top of hardcoded defaults, so partial configs work.

Key defaults to know:

| Key | Default | Notes |
|-----|---------|-------|
| `auto_trading` | `false` | Live trading is disabled by default; must be explicitly enabled |
| `max_daily_loss_pct` | `2.0` | Circuit breaker — halts all trading |
| `risk_free_rate` | `0.06` | RBI repo rate; used in all Black-Scholes calculations |
| `lot_size` | `50` | NSE standard lot size for Nifty |
| `commission_rate` | `0.001` | Applied in backtesting |
| `market_hours` | `09:15–15:30` | NSE session |

Strategy-level `confidence_threshold`, `profit_target`, and `stop_loss` live under `strategy_parameters.<strategy_name>` in the config.

## Key Conventions

- **Dataclasses for data transfer**: `TradingSignal`, `Position`, `Order`, `Trade` are all `@dataclass`. Do not pass raw dicts between layers.
- **Enums for states**: `MarketDirection`, `VolatilityRegime`, `OrderStatus` are `Enum`s. Use `.value` when displaying/printing.
- **Logging**: Every module creates its own `logger = logging.getLogger(__name__)`. The root logger writes to both `trading_system.log` and stdout (configured in `main.py`).
- **Type hints**: All public methods are fully annotated. Maintain this when adding code.
- **No broker integration**: Execution is simulated. `PortfolioManager.process_signal()` creates paper orders; there is no live broker API.
