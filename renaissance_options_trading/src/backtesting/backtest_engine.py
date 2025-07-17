"""
Backtesting Engine for Options Trading Strategies
Simulates historical trading to evaluate strategy performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns

from ..strategies.volatility_strategies import DirectionalVolatilityStrategy, TradingSignal
from ..portfolio.portfolio_manager import PortfolioManager
from ..utils.greeks import GreeksCalculator
from ..data.market_data import MarketDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: timedelta
    best_trade: float
    worst_trade: float
    daily_returns: List[float]
    equity_curve: List[float]
    trade_log: List[Dict]


class HistoricalDataSimulator:
    """Simulates historical market conditions for backtesting"""
    
    def __init__(self):
        self.current_date = None
        self.nifty_data = pd.DataFrame()
        self.volatility_data = pd.DataFrame()
        
    def load_historical_data(self, start_date: datetime, end_date: datetime) -> bool:
        """Load historical NIFTY data for backtesting"""
        try:
            # In a real implementation, this would load actual historical data
            # For now, we'll generate synthetic data
            
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate synthetic NIFTY price data
            np.random.seed(42)  # For reproducible results
            
            initial_price = 18000
            returns = np.random.normal(0.0005, 0.015, len(date_range))  # Daily returns
            
            prices = [initial_price]
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            self.nifty_data = pd.DataFrame({
                'Date': date_range,
                'Open': prices,
                'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'Close': prices,
                'Volume': np.random.randint(100000, 1000000, len(date_range))
            })
            
            # Calculate rolling volatility
            self.nifty_data['Returns'] = self.nifty_data['Close'].pct_change()
            self.nifty_data['Volatility'] = self.nifty_data['Returns'].rolling(20).std() * np.sqrt(252)
            
            logger.info(f"Loaded historical data from {start_date} to {end_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return False
    
    def get_market_data_for_date(self, date: datetime) -> Dict:
        """Get market data for a specific date"""
        if self.nifty_data.empty:
            return {}
        
        # Find the closest date
        date_diff = abs(self.nifty_data['Date'] - date)
        closest_idx = date_diff.idxmin()
        
        row = self.nifty_data.iloc[closest_idx]
        
        # Simulate option chain data
        underlying_price = row['Close']
        volatility = row['Volatility'] if not pd.isna(row['Volatility']) else 0.15
        
        # Generate synthetic option chain analysis
        option_analysis = {
            'underlying_price': underlying_price,
            'pcr': np.random.uniform(0.7, 1.3),  # Random PCR
            'max_pain': underlying_price + np.random.uniform(-200, 200),
            'volatility_skew': {'skew_direction': np.random.choice(['call', 'put'])},
            'directional_bias': self._determine_synthetic_bias(row),
            'support_resistance': {
                'key_levels': [underlying_price + i*50 for i in range(-4, 5)],
                'strongest_level': underlying_price
            },
            'gamma_levels': [underlying_price + i*100 for i in range(-2, 3)]
        }
        
        return {
            'nifty_data': row.to_dict(),
            'option_analysis': option_analysis,
            'volatility': volatility,
            'timestamp': date
        }
    
    def _determine_synthetic_bias(self, row: pd.Series) -> str:
        """Determine synthetic directional bias based on price action"""
        if 'Returns' in row and not pd.isna(row['Returns']):
            if row['Returns'] > 0.01:
                return 'bullish'
            elif row['Returns'] < -0.01:
                return 'bearish'
        return 'neutral'


class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.data_simulator = HistoricalDataSimulator()
        
        # Initialize components (will be set during backtest)
        self.market_data_manager = None
        self.greeks_calculator = None
        self.strategy = None
        self.portfolio_manager = None
        
    def run_backtest(self, start_date: datetime, end_date: datetime,
                    strategy_params: Dict = None) -> BacktestResult:
        """Run complete backtest"""
        
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Load historical data
        if not self.data_simulator.load_historical_data(start_date, end_date):
            raise ValueError("Failed to load historical data")
        
        # Initialize components
        self._initialize_components(strategy_params or {})
        
        # Run day-by-day simulation
        current_date = start_date
        trade_log = []
        equity_curve = [self.initial_capital]
        daily_returns = []
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_pnl = self._simulate_trading_day(current_date, trade_log)
                
                # Update equity curve
                current_equity = equity_curve[-1] + daily_pnl
                equity_curve.append(current_equity)
                
                # Calculate daily return
                daily_return = daily_pnl / equity_curve[-2] if equity_curve[-2] != 0 else 0
                daily_returns.append(daily_return)
            
            current_date += timedelta(days=1)
        
        # Calculate final results
        final_capital = equity_curve[-1]
        
        # Calculate performance metrics
        result = self._calculate_performance_metrics(
            start_date, end_date, final_capital, daily_returns, 
            equity_curve, trade_log
        )
        
        logger.info(f"Backtest completed. Final capital: ₹{final_capital:,.2f}")
        logger.info(f"Total return: {result.total_return:.2%}")
        
        return result
    
    def _initialize_components(self, strategy_params: Dict):
        """Initialize trading components for backtesting"""
        
        # Create mock market data manager for backtesting
        class MockMarketDataManager:
            def __init__(self, data_simulator):
                self.data_simulator = data_simulator
                self.current_date = None
            
            def get_real_time_data(self, symbol="NIFTY"):
                return self.data_simulator.get_market_data_for_date(self.current_date)
            
            def get_historical_analysis(self, symbol="NIFTY", days=30):
                # Return simplified historical analysis
                return {
                    'volatility': 0.15,
                    'trend_analysis': {'trend': 'sideways'},
                    'support_resistance_historical': {
                        'resistance_levels': [],
                        'support_levels': []
                    }
                }
        
        self.market_data_manager = MockMarketDataManager(self.data_simulator)
        self.greeks_calculator = GreeksCalculator()
        
        # Initialize strategy with parameters
        self.strategy = DirectionalVolatilityStrategy(
            self.market_data_manager, 
            self.greeks_calculator
        )
        
        # Apply strategy parameters
        for param, value in strategy_params.items():
            if hasattr(self.strategy, param):
                setattr(self.strategy, param, value)
        
        # Initialize portfolio manager
        from ..strategies.volatility_strategies import RiskManager
        risk_manager = RiskManager()
        
        self.portfolio_manager = PortfolioManager(
            self.initial_capital,
            self.market_data_manager,
            self.greeks_calculator,
            risk_manager
        )
    
    def _simulate_trading_day(self, date: datetime, trade_log: List[Dict]) -> float:
        """Simulate one trading day"""
        
        # Set current date for data simulation
        self.market_data_manager.current_date = date
        
        # Update positions with current market prices
        self.portfolio_manager.update_positions()
        
        # Check risk limits
        risk_status = self.portfolio_manager.check_risk_limits()
        if risk_status['any_limit_exceeded']:
            # Close all positions if risk limits exceeded
            self.portfolio_manager.close_all_positions("risk_limit_exceeded")
            return 0
        
        # Generate trading signals
        signals = self.strategy.generate_trading_signals()
        
        # Process signals
        for signal in signals:
            order_id = self.portfolio_manager.process_signal(signal)
            if order_id:
                trade_log.append({
                    'date': date,
                    'signal': signal,
                    'order_id': order_id
                })
        
        # Check for position exits (simplified exit logic)
        self._check_position_exits(date, trade_log)
        
        # Calculate daily P&L
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        daily_pnl = portfolio_summary['total_pnl']
        
        return daily_pnl
    
    def _check_position_exits(self, date: datetime, trade_log: List[Dict]):
        """Check if any positions should be exited"""
        
        positions_to_close = []
        
        for position_id, position in self.portfolio_manager.positions.items():
            # Exit conditions
            should_exit = False
            exit_reason = ""
            
            # 1. Profit target (30% profit)
            if position.pnl > position.entry_price * position.quantity * 50 * 0.3:
                should_exit = True
                exit_reason = "profit_target"
            
            # 2. Stop loss (50% loss)
            elif position.pnl < -position.entry_price * position.quantity * 50 * 0.5:
                should_exit = True
                exit_reason = "stop_loss"
            
            # 3. Time decay (close 3 days before expiry)
            elif self._days_to_expiry(position.expiry) <= 3:
                should_exit = True
                exit_reason = "time_decay"
            
            # 4. Volatility regime change (simplified)
            elif self._volatility_regime_changed():
                should_exit = True
                exit_reason = "regime_change"
            
            if should_exit:
                positions_to_close.append((position_id, exit_reason))
        
        # Close positions
        for position_id, reason in positions_to_close:
            if self.portfolio_manager.close_position(position_id, reason):
                trade_log.append({
                    'date': date,
                    'action': 'close_position',
                    'position_id': position_id,
                    'reason': reason
                })
    
    def _days_to_expiry(self, expiry: str) -> int:
        """Calculate days to expiry"""
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
        current_date = self.market_data_manager.current_date
        return (expiry_date - current_date).days
    
    def _volatility_regime_changed(self) -> bool:
        """Check if volatility regime has changed (simplified)"""
        # This is a placeholder - in practice, you'd implement more sophisticated logic
        return np.random.random() < 0.05  # 5% chance of regime change
    
    def _calculate_performance_metrics(self, start_date: datetime, end_date: datetime,
                                     final_capital: float, daily_returns: List[float],
                                     equity_curve: List[float], trade_log: List[Dict]) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        
        # Basic metrics
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        days = (end_date - start_date).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # Risk metrics
        if daily_returns:
            daily_returns_array = np.array(daily_returns)
            sharpe_ratio = np.mean(daily_returns_array) / np.std(daily_returns_array) * np.sqrt(252) if np.std(daily_returns_array) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Trade statistics
        completed_trades = [trade for trade in self.portfolio_manager.trades.values() 
                          if trade.exit_order is not None]
        
        total_trades = len(completed_trades)
        winning_trades = [t for t in completed_trades if t.pnl > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit factor
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = sum(t.pnl for t in completed_trades if t.pnl < 0)
        profit_factor = abs(total_wins / total_losses) if total_losses != 0 else float('inf')
        
        # Trade duration
        if completed_trades:
            avg_duration = np.mean([t.holding_period.total_seconds() / 3600 / 24 
                                  for t in completed_trades if t.holding_period])
            avg_trade_duration = timedelta(days=avg_duration)
        else:
            avg_trade_duration = timedelta(0)
        
        # Best and worst trades
        best_trade = max([t.pnl for t in completed_trades]) if completed_trades else 0
        worst_trade = min([t.pnl for t in completed_trades]) if completed_trades else 0
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_duration=avg_trade_duration,
            best_trade=best_trade,
            worst_trade=worst_trade,
            daily_returns=daily_returns,
            equity_curve=equity_curve,
            trade_log=trade_log
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown"""
        if len(equity_curve) < 2:
            return 0
        
        peak = equity_curve[0]
        max_drawdown = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def plot_results(self, result: BacktestResult, save_path: str = None):
        """Plot backtest results"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Backtest Results', fontsize=16)
        
        # Equity curve
        dates = pd.date_range(start=result.start_date, periods=len(result.equity_curve), freq='D')
        axes[0, 0].plot(dates, result.equity_curve)
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value (₹)')
        axes[0, 0].grid(True)
        
        # Daily returns distribution
        if result.daily_returns:
            axes[0, 1].hist(result.daily_returns, bins=50, alpha=0.7)
            axes[0, 1].set_title('Daily Returns Distribution')
            axes[0, 1].set_xlabel('Daily Return')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].grid(True)
        
        # Drawdown
        equity_array = np.array(result.equity_curve)
        peak_array = np.maximum.accumulate(equity_array)
        drawdown_array = (peak_array - equity_array) / peak_array
        
        axes[1, 0].fill_between(dates, drawdown_array, alpha=0.3, color='red')
        axes[1, 0].set_title('Drawdown')
        axes[1, 0].set_ylabel('Drawdown %')
        axes[1, 0].grid(True)
        
        # Performance metrics text
        metrics_text = f"""
        Total Return: {result.total_return:.2%}
        Annualized Return: {result.annualized_return:.2%}
        Max Drawdown: {result.max_drawdown:.2%}
        Sharpe Ratio: {result.sharpe_ratio:.2f}
        Win Rate: {result.win_rate:.2%}
        Profit Factor: {result.profit_factor:.2f}
        Total Trades: {result.total_trades}
        """
        
        axes[1, 1].text(0.1, 0.5, metrics_text, transform=axes[1, 1].transAxes,
                        fontsize=10, verticalalignment='center')
        axes[1, 1].set_title('Performance Metrics')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def optimize_parameters(self, start_date: datetime, end_date: datetime,
                          param_ranges: Dict) -> Dict:
        """Optimize strategy parameters using grid search"""
        
        logger.info("Starting parameter optimization...")
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(param_ranges)
        
        best_result = None
        best_params = None
        best_sharpe = -float('inf')
        
        for i, params in enumerate(param_combinations):
            logger.info(f"Testing parameter set {i+1}/{len(param_combinations)}: {params}")
            
            try:
                result = self.run_backtest(start_date, end_date, params)
                
                # Use Sharpe ratio as optimization metric
                if result.sharpe_ratio > best_sharpe:
                    best_sharpe = result.sharpe_ratio
                    best_result = result
                    best_params = params
                    
            except Exception as e:
                logger.error(f"Error testing parameters {params}: {e}")
                continue
        
        logger.info(f"Optimization completed. Best Sharpe ratio: {best_sharpe:.2f}")
        logger.info(f"Best parameters: {best_params}")
        
        return {
            'best_params': best_params,
            'best_result': best_result,
            'best_sharpe': best_sharpe
        }
    
    def _generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Generate all combinations of parameters for optimization"""
        
        import itertools
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        combinations = []
        for combo in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)
        
        return combinations


# Utility functions for backtesting
def run_quick_backtest(start_date: str, end_date: str, initial_capital: float = 100000) -> BacktestResult:
    """Run a quick backtest with default parameters"""
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    engine = BacktestEngine(initial_capital)
    result = engine.run_backtest(start_dt, end_dt)
    
    return result


def compare_strategies(strategies: Dict[str, Dict], start_date: str, end_date: str) -> pd.DataFrame:
    """Compare multiple strategy configurations"""
    
    results = []
    
    for strategy_name, params in strategies.items():
        logger.info(f"Testing strategy: {strategy_name}")
        
        try:
            result = run_quick_backtest(start_date, end_date)
            
            results.append({
                'Strategy': strategy_name,
                'Total Return': result.total_return,
                'Annualized Return': result.annualized_return,
                'Max Drawdown': result.max_drawdown,
                'Sharpe Ratio': result.sharpe_ratio,
                'Win Rate': result.win_rate,
                'Profit Factor': result.profit_factor,
                'Total Trades': result.total_trades
            })
            
        except Exception as e:
            logger.error(f"Error testing {strategy_name}: {e}")
    
    return pd.DataFrame(results)