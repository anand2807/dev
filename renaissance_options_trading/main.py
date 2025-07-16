"""
Renaissance Options Trading System - Main Application
Entry point for the sophisticated options trading system
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.market_data import MarketDataManager
from src.utils.greeks import GreeksCalculator
from src.strategies.volatility_strategies import DirectionalVolatilityStrategy, RiskManager
from src.portfolio.portfolio_manager import PortfolioManager
from src.backtesting.backtest_engine import BacktestEngine, run_quick_backtest
from src.monitoring.dashboard import main as run_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RenaissanceOptionsTrader:
    """Main trading system orchestrator"""
    
    def __init__(self, initial_capital: float = 100000, config_file: str = None):
        self.initial_capital = initial_capital
        self.config = self._load_config(config_file)
        
        # Initialize components
        self.market_data_manager = MarketDataManager()
        self.greeks_calculator = GreeksCalculator()
        self.risk_manager = RiskManager()
        
        # Initialize strategy
        self.strategy = DirectionalVolatilityStrategy(
            self.market_data_manager,
            self.greeks_calculator
        )
        
        # Initialize portfolio manager
        self.portfolio_manager = PortfolioManager(
            initial_capital,
            self.market_data_manager,
            self.greeks_calculator,
            self.risk_manager
        )
        
        logger.info(f"Renaissance Options Trading System initialized with ₹{initial_capital:,.2f}")
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from file"""
        default_config = {
            "volatility_threshold": 0.15,
            "pcr_bullish_threshold": 0.8,
            "pcr_bearish_threshold": 1.2,
            "min_time_to_expiry": 7,
            "max_time_to_expiry": 45,
            "max_positions": 20,
            "max_daily_loss_pct": 2.0,
            "auto_trading": False,
            "risk_free_rate": 0.06
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        return default_config
    
    def run_analysis(self):
        """Run market analysis and generate signals"""
        logger.info("Running market analysis...")
        
        # Analyze market regime
        market_regime = self.strategy.analyze_market_regime()
        
        print("\n" + "="*60)
        print("📊 MARKET ANALYSIS REPORT")
        print("="*60)
        print(f"Timestamp: {market_regime['timestamp']}")
        print(f"Volatility Regime: {market_regime['volatility_regime'].value}")
        print(f"Market Direction: {market_regime['market_direction'].value}")
        print(f"Current Volatility: {market_regime['current_volatility']:.2%}")
        print(f"Put-Call Ratio: {market_regime['pcr']:.2f}")
        print(f"Underlying Price: ₹{market_regime['underlying_price']:,.2f}")
        print(f"Max Pain Level: ₹{market_regime['max_pain']:,.2f}")
        
        # Display chain patterns
        chain_patterns = market_regime['chain_patterns']
        print("\n🔍 Option Chain Patterns:")
        for pattern, value in chain_patterns.items():
            print(f"  • {pattern.replace('_', ' ').title()}: {value}")
        
        # Generate trading signals
        signals = self.strategy.generate_trading_signals()
        
        print(f"\n🎯 TRADING SIGNALS ({len(signals)} found)")
        print("-" * 60)
        
        if signals:
            for i, signal in enumerate(signals, 1):
                print(f"\nSignal {i}:")
                print(f"  Strategy: {signal.strategy}")
                print(f"  Action: {signal.action} {signal.option_type}")
                print(f"  Strike: ₹{signal.strike}")
                print(f"  Expiry: {signal.expiry}")
                print(f"  Confidence: {signal.confidence:.1%}")
                print(f"  Expected Profit: ₹{signal.expected_profit:,.2f}")
                print(f"  Max Loss: ₹{signal.max_loss:,.2f}")
                print(f"  Risk/Reward: {signal.expected_profit/signal.max_loss:.2f}")
                print(f"  Reasoning: {signal.reasoning}")
        else:
            print("No trading signals generated. Market conditions may not be favorable.")
        
        return signals
    
    def run_live_trading(self):
        """Run live trading session"""
        logger.info("Starting live trading session...")
        
        if not self.config.get('auto_trading', False):
            print("⚠️  Auto-trading is disabled. Enable in config to run live trading.")
            return
        
        print("\n🚀 LIVE TRADING SESSION STARTED")
        print("="*60)
        
        try:
            while True:
                # Generate and process signals
                signals = self.run_analysis()
                
                # Process each signal
                for signal in signals:
                    order_id = self.portfolio_manager.process_signal(signal)
                    if order_id:
                        print(f"✅ Signal executed: {order_id}")
                    else:
                        print(f"❌ Signal rejected: {signal.strategy}")
                
                # Update positions
                self.portfolio_manager.update_positions()
                
                # Check risk limits
                risk_status = self.portfolio_manager.check_risk_limits()
                if risk_status['any_limit_exceeded']:
                    print("🚨 Risk limits exceeded! Closing all positions...")
                    self.portfolio_manager.close_all_positions("risk_limit")
                    break
                
                # Display portfolio status
                self._display_portfolio_status()
                
                # Wait before next iteration (in real trading, this would be event-driven)
                import time
                time.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            print("\n🛑 Trading session stopped by user")
            self.portfolio_manager.close_all_positions("user_stop")
        except Exception as e:
            logger.error(f"Error in live trading: {e}")
            self.portfolio_manager.close_all_positions("error")
    
    def run_backtest(self, start_date: str, end_date: str):
        """Run backtesting"""
        logger.info(f"Running backtest from {start_date} to {end_date}")
        
        try:
            result = run_quick_backtest(start_date, end_date, self.initial_capital)
            
            print("\n📊 BACKTEST RESULTS")
            print("="*60)
            print(f"Period: {start_date} to {end_date}")
            print(f"Initial Capital: ₹{result.initial_capital:,.2f}")
            print(f"Final Capital: ₹{result.final_capital:,.2f}")
            print(f"Total Return: {result.total_return:.2%}")
            print(f"Annualized Return: {result.annualized_return:.2%}")
            print(f"Max Drawdown: {result.max_drawdown:.2%}")
            print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"Win Rate: {result.win_rate:.2%}")
            print(f"Profit Factor: {result.profit_factor:.2f}")
            print(f"Total Trades: {result.total_trades}")
            print(f"Best Trade: ₹{result.best_trade:,.2f}")
            print(f"Worst Trade: ₹{result.worst_trade:,.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return None
    
    def _display_portfolio_status(self):
        """Display current portfolio status"""
        summary = self.portfolio_manager.get_portfolio_summary()
        
        print(f"\n💼 Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
        print(f"💰 Cash Balance: ₹{summary['cash_balance']:,.2f}")
        print(f"📈 Total P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"📊 Total Return: {summary['total_return']:.2%}")
        print(f"📋 Open Positions: {summary['num_positions']}")
        
        # Display Greeks if available
        portfolio_greeks = summary.get('portfolio_greeks', {})
        if portfolio_greeks:
            print(f"🔢 Portfolio Delta: {portfolio_greeks.get('total_delta', 0):.2f}")
            print(f"🔢 Portfolio Gamma: {portfolio_greeks.get('total_gamma', 0):.2f}")
            print(f"🔢 Portfolio Theta: ₹{portfolio_greeks.get('total_theta', 0):.2f}")
    
    def generate_report(self):
        """Generate comprehensive trading report"""
        logger.info("Generating trading report...")
        
        # Portfolio summary
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        
        # Performance report
        perf_report = self.portfolio_manager.generate_performance_report()
        
        print("\n📋 COMPREHENSIVE TRADING REPORT")
        print("="*80)
        
        # Portfolio section
        print("\n💼 PORTFOLIO OVERVIEW")
        print("-" * 40)
        print(f"Portfolio Value: ₹{portfolio_summary['portfolio_value']:,.2f}")
        print(f"Cash Balance: ₹{portfolio_summary['cash_balance']:,.2f}")
        print(f"Total P&L: ₹{portfolio_summary['total_pnl']:,.2f}")
        print(f"Total Return: {portfolio_summary['total_return']:.2%}")
        print(f"Open Positions: {portfolio_summary['num_positions']}")
        
        # Performance section
        if 'message' not in perf_report:
            print("\n📊 PERFORMANCE METRICS")
            print("-" * 40)
            print(f"Total Trades: {perf_report['total_trades']}")
            print(f"Winning Trades: {perf_report['winning_trades']}")
            print(f"Losing Trades: {perf_report['losing_trades']}")
            print(f"Win Rate: {perf_report['win_rate']:.2%}")
            print(f"Profit Factor: {perf_report['profit_factor']:.2f}")
            print(f"Average Win: ₹{perf_report['avg_win']:,.2f}")
            print(f"Average Loss: ₹{perf_report['avg_loss']:,.2f}")
            print(f"Max Drawdown: {perf_report['max_drawdown']:.2%}")
            print(f"Sharpe Ratio: {perf_report['sharpe_ratio']:.2f}")
        
        # Current positions
        positions = portfolio_summary.get('positions', [])
        if positions:
            print(f"\n📋 CURRENT POSITIONS ({len(positions)})")
            print("-" * 40)
            for pos in positions:
                print(f"{pos['option_type']} {pos['strike']} {pos['expiry']} | "
                      f"Qty: {pos['quantity']} | P&L: ₹{pos['pnl']:,.2f}")
        
        return {
            'portfolio_summary': portfolio_summary,
            'performance_report': perf_report
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Renaissance Options Trading System')
    parser.add_argument('--mode', choices=['analysis', 'backtest', 'live', 'dashboard', 'report'], 
                       default='analysis', help='Operating mode')
    parser.add_argument('--capital', type=float, default=100000, 
                       help='Initial capital (default: 100000)')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--start-date', type=str, help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Backtest end date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Initialize trading system
    trader = RenaissanceOptionsTrader(args.capital, args.config)
    
    try:
        if args.mode == 'analysis':
            trader.run_analysis()
        
        elif args.mode == 'backtest':
            start_date = args.start_date or (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = args.end_date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            trader.run_backtest(start_date, end_date)
        
        elif args.mode == 'live':
            trader.run_live_trading()
        
        elif args.mode == 'dashboard':
            print("🚀 Starting web dashboard...")
            print("Access the dashboard at: http://localhost:8501")
            run_dashboard()
        
        elif args.mode == 'report':
            trader.generate_report()
    
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"❌ System error: {e}")
    
    print("\n🏁 Renaissance Options Trading System shutdown complete")


if __name__ == "__main__":
    main()