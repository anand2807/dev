#!/usr/bin/env python3
"""
Renaissance Options Trading System - Main Application
A sophisticated algorithmic trading system for Indian options market
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from data.market_data import MarketDataManager
from utils.greeks import GreeksCalculator
from strategies.volatility_strategies import DirectionalVolatilityStrategy
from portfolio.portfolio_manager import PortfolioManager
from backtesting.backtest_engine import BacktestEngine
from monitoring.dashboard import run_dashboard

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

def load_config(config_path="config.json"):
    """Load system configuration"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)

def run_analysis_mode(config, capital):
    """Run market analysis mode"""
    logger.info("🔍 Starting Market Analysis Mode")
    
    # Initialize components
    market_data = MarketDataManager()
    greeks_calc = GreeksCalculator(risk_free_rate=config['market_data']['risk_free_rate'])
    strategy = DirectionalVolatilityStrategy(config['strategy_parameters']['directional_volatility'])
    portfolio = PortfolioManager(initial_capital=capital, config=config['risk_management'])
    
    try:
        # Analyze current market conditions
        logger.info("📊 Analyzing current market conditions...")
        
        # Get market data for NIFTY
        current_price = market_data.get_current_price("NIFTY")
        option_chain = market_data.get_option_chain("NIFTY")
        
        if current_price and option_chain:
            logger.info(f"Current NIFTY Price: ₹{current_price:.2f}")
            
            # Analyze market regime
            market_regime = market_data.detect_market_regime("NIFTY")
            logger.info(f"Market Regime: {market_regime}")
            
            # Generate trading signals
            signals = strategy.generate_signals(option_chain, current_price)
            
            if signals:
                logger.info("🎯 Trading Signals Generated:")
                for signal in signals:
                    logger.info(f"  - {signal['type'].upper()}: {signal['strike']} "
                              f"(Confidence: {signal['confidence']:.2f})")
            else:
                logger.info("⏳ No trading signals generated - waiting for better conditions")
        
        # Display portfolio status
        portfolio_status = portfolio.get_portfolio_summary()
        logger.info(f"💼 Portfolio Status: {portfolio_status}")
        
    except Exception as e:
        logger.error(f"Error in analysis mode: {e}")

def run_backtest_mode(config, start_date, end_date, capital):
    """Run backtesting mode"""
    logger.info("📈 Starting Backtesting Mode")
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine(config)
        
        # Run backtest
        results = engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital
        )
        
        # Display results
        logger.info("📊 Backtest Results:")
        logger.info(f"  Total Return: {results['total_return']:.2%}")
        logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {results['max_drawdown']:.2%}")
        logger.info(f"  Win Rate: {results['win_rate']:.2%}")
        logger.info(f"  Total Trades: {results['total_trades']}")
        
    except Exception as e:
        logger.error(f"Error in backtest mode: {e}")

def run_dashboard_mode():
    """Run dashboard mode"""
    logger.info("🚀 Starting Dashboard Mode")
    try:
        run_dashboard()
    except Exception as e:
        logger.error(f"Error in dashboard mode: {e}")

def run_report_mode(config, capital):
    """Generate comprehensive trading report"""
    logger.info("📋 Generating Trading Report")
    
    try:
        # Initialize components
        portfolio = PortfolioManager(initial_capital=capital, config=config['risk_management'])
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': capital,
            'configuration': config,
            'system_status': 'Active'
        }
        
        logger.info("📄 Trading Report Generated:")
        logger.info(f"  Portfolio Value: ₹{capital:,.2f}")
        logger.info(f"  System Status: {report['system_status']}")
        logger.info(f"  Report Time: {report['timestamp']}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Renaissance Options Trading System")
    parser.add_argument("--mode", choices=["analysis", "backtest", "dashboard", "report"], 
                       default="analysis", help="Operating mode")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    parser.add_argument("--start-date", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Backtest end date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Display banner
    print("🏛️  RENAISSANCE OPTIONS TRADING SYSTEM")
    print("=" * 50)
    print(f"Mode: {args.mode.upper()}")
    print(f"Capital: ₹{args.capital:,.2f}")
    print("=" * 50)
    
    # Route to appropriate mode
    if args.mode == "analysis":
        run_analysis_mode(config, args.capital)
    elif args.mode == "backtest":
        start_date = args.start_date or (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
        run_backtest_mode(config, start_date, end_date, args.capital)
    elif args.mode == "dashboard":
        run_dashboard_mode()
    elif args.mode == "report":
        run_report_mode(config, args.capital)

if __name__ == "__main__":
    main()