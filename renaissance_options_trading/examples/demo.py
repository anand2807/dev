"""
Renaissance Options Trading System - Demo Script
Demonstrates the key features of the trading system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.data.market_data import MarketDataManager
from src.utils.greeks import GreeksCalculator
from src.strategies.volatility_strategies import DirectionalVolatilityStrategy, RiskManager
from src.portfolio.portfolio_manager import PortfolioManager
from src.backtesting.backtest_engine import run_quick_backtest


def demo_market_analysis():
    """Demonstrate market analysis capabilities"""
    print("🔍 MARKET ANALYSIS DEMO")
    print("=" * 50)
    
    # Initialize components
    market_data_manager = MarketDataManager()
    greeks_calculator = GreeksCalculator()
    
    # Initialize strategy
    strategy = DirectionalVolatilityStrategy(
        market_data_manager,
        greeks_calculator
    )
    
    # Analyze market regime
    print("Analyzing current market regime...")
    market_regime = strategy.analyze_market_regime()
    
    print(f"Volatility Regime: {market_regime['volatility_regime'].value}")
    print(f"Market Direction: {market_regime['market_direction'].value}")
    print(f"Current Volatility: {market_regime['current_volatility']:.2%}")
    print(f"Put-Call Ratio: {market_regime['pcr']:.2f}")
    print(f"Underlying Price: ₹{market_regime['underlying_price']:,.2f}")
    
    # Generate trading signals
    print("\nGenerating trading signals...")
    signals = strategy.generate_trading_signals()
    
    print(f"Generated {len(signals)} trading signals:")
    for i, signal in enumerate(signals, 1):
        print(f"\nSignal {i}:")
        print(f"  Strategy: {signal.strategy}")
        print(f"  Action: {signal.action} {signal.option_type}")
        print(f"  Strike: ₹{signal.strike}")
        print(f"  Confidence: {signal.confidence:.1%}")
        print(f"  Expected Profit: ₹{signal.expected_profit:,.2f}")
        print(f"  Reasoning: {signal.reasoning}")


def demo_greeks_calculation():
    """Demonstrate Greeks calculation"""
    print("\n🔢 GREEKS CALCULATION DEMO")
    print("=" * 50)
    
    calculator = GreeksCalculator()
    
    # Example option parameters
    S = 18000  # Current NIFTY price
    K = 18100  # Strike price
    T = 30/365  # 30 days to expiry
    sigma = 0.15  # 15% volatility
    
    print(f"Option Parameters:")
    print(f"  Underlying Price: ₹{S:,.2f}")
    print(f"  Strike Price: ₹{K:,.2f}")
    print(f"  Time to Expiry: {T*365:.0f} days")
    print(f"  Volatility: {sigma:.1%}")
    
    # Calculate Greeks for call option
    call_greeks = calculator.calculate_all_greeks(S, K, T, sigma, 'call')
    
    print(f"\nCall Option Greeks:")
    print(f"  Price: ₹{call_greeks['price']:.2f}")
    print(f"  Delta: {call_greeks['delta']:.4f}")
    print(f"  Gamma: {call_greeks['gamma']:.6f}")
    print(f"  Theta: ₹{call_greeks['theta']:.2f} per day")
    print(f"  Vega: ₹{call_greeks['vega']:.2f} per 1% vol change")
    print(f"  Rho: ₹{call_greeks['rho']:.2f} per 1% rate change")
    
    # Calculate Greeks for put option
    put_greeks = calculator.calculate_all_greeks(S, K, T, sigma, 'put')
    
    print(f"\nPut Option Greeks:")
    print(f"  Price: ₹{put_greeks['price']:.2f}")
    print(f"  Delta: {put_greeks['delta']:.4f}")
    print(f"  Gamma: {put_greeks['gamma']:.6f}")
    print(f"  Theta: ₹{put_greeks['theta']:.2f} per day")
    print(f"  Vega: ₹{put_greeks['vega']:.2f} per 1% vol change")
    print(f"  Rho: ₹{put_greeks['rho']:.2f} per 1% rate change")


def demo_portfolio_management():
    """Demonstrate portfolio management"""
    print("\n💼 PORTFOLIO MANAGEMENT DEMO")
    print("=" * 50)
    
    # Initialize components
    market_data_manager = MarketDataManager()
    greeks_calculator = GreeksCalculator()
    risk_manager = RiskManager()
    
    # Initialize portfolio with ₹1,00,000
    portfolio_manager = PortfolioManager(
        initial_capital=100000,
        market_data_manager=market_data_manager,
        greeks_calculator=greeks_calculator,
        risk_manager=risk_manager
    )
    
    print(f"Initial Portfolio Value: ₹{portfolio_manager.current_capital:,.2f}")
    print(f"Cash Balance: ₹{portfolio_manager.cash_balance:,.2f}")
    
    # Create a sample trading signal
    from src.strategies.volatility_strategies import TradingSignal
    
    sample_signal = TradingSignal(
        strategy="demo",
        action="BUY",
        option_type="CALL",
        strike=18100,
        expiry="2024-08-29",
        quantity=1,
        confidence=0.75,
        reasoning="Demo signal for testing",
        expected_profit=500,
        max_loss=1000,
        timestamp=datetime.now()
    )
    
    # Process the signal
    print(f"\nProcessing sample signal: {sample_signal.option_type} {sample_signal.strike}")
    order_id = portfolio_manager.process_signal(sample_signal)
    
    if order_id:
        print(f"✅ Signal executed successfully! Order ID: {order_id}")
        
        # Update positions
        portfolio_manager.update_positions()
        
        # Get portfolio summary
        summary = portfolio_manager.get_portfolio_summary()
        
        print(f"\nUpdated Portfolio Summary:")
        print(f"  Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
        print(f"  Cash Balance: ₹{summary['cash_balance']:,.2f}")
        print(f"  Total P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"  Open Positions: {summary['num_positions']}")
        
        # Display portfolio Greeks
        portfolio_greeks = summary.get('portfolio_greeks', {})
        if portfolio_greeks:
            print(f"\nPortfolio Greeks:")
            print(f"  Delta: {portfolio_greeks.get('total_delta', 0):.2f}")
            print(f"  Gamma: {portfolio_greeks.get('total_gamma', 0):.2f}")
            print(f"  Theta: ₹{portfolio_greeks.get('total_theta', 0):.2f}")
            print(f"  Vega: ₹{portfolio_greeks.get('total_vega', 0):.2f}")
    else:
        print("❌ Signal execution failed")


def demo_backtesting():
    """Demonstrate backtesting capabilities"""
    print("\n📊 BACKTESTING DEMO")
    print("=" * 50)
    
    # Run a quick backtest
    start_date = "2024-01-01"
    end_date = "2024-03-31"
    initial_capital = 100000
    
    print(f"Running backtest from {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_capital:,.2f}")
    print("This may take a moment...")
    
    try:
        result = run_quick_backtest(start_date, end_date, initial_capital)
        
        print(f"\n📈 BACKTEST RESULTS:")
        print(f"  Final Capital: ₹{result.final_capital:,.2f}")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Annualized Return: {result.annualized_return:.2%}")
        print(f"  Maximum Drawdown: {result.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Best Trade: ₹{result.best_trade:,.2f}")
        print(f"  Worst Trade: ₹{result.worst_trade:,.2f}")
        
        if result.total_return > 0:
            print("🎉 Strategy was profitable!")
        else:
            print("📉 Strategy had losses - consider parameter optimization")
            
    except Exception as e:
        print(f"❌ Backtest failed: {e}")


def demo_risk_management():
    """Demonstrate risk management features"""
    print("\n⚠️ RISK MANAGEMENT DEMO")
    print("=" * 50)
    
    risk_manager = RiskManager()
    
    print(f"Risk Management Parameters:")
    print(f"  Max Portfolio Risk: {risk_manager.max_portfolio_risk:.1%}")
    print(f"  Max Single Position Risk: {risk_manager.max_single_position_risk:.1%}")
    
    # Example position sizing
    from src.strategies.volatility_strategies import TradingSignal
    
    signal = TradingSignal(
        strategy="demo",
        action="BUY",
        option_type="CALL",
        strike=18100,
        expiry="2024-08-29",
        quantity=2,
        confidence=0.8,
        reasoning="High confidence signal",
        expected_profit=1000,
        max_loss=2000,
        timestamp=datetime.now()
    )
    
    portfolio_value = 100000
    position_size = risk_manager.calculate_position_size(signal, portfolio_value)
    
    print(f"\nPosition Sizing Example:")
    print(f"  Signal Max Loss: ₹{signal.max_loss:,.2f}")
    print(f"  Portfolio Value: ₹{portfolio_value:,.2f}")
    print(f"  Recommended Position Size: {position_size} lots")
    print(f"  Risk per Position: {(signal.max_loss * position_size / portfolio_value):.2%}")
    
    # Validate signal
    is_valid = risk_manager.validate_signal(signal, [])
    print(f"  Signal Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")


def main():
    """Run all demos"""
    print("🏛️ RENAISSANCE OPTIONS TRADING SYSTEM - DEMO")
    print("=" * 60)
    print("This demo showcases the key features of the trading system")
    print("=" * 60)
    
    try:
        # Run all demo functions
        demo_market_analysis()
        demo_greeks_calculation()
        demo_portfolio_management()
        demo_risk_management()
        demo_backtesting()
        
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Next steps:")
        print("1. Run 'python main.py --mode dashboard' to launch the web interface")
        print("2. Run 'python main.py --mode analysis' for live market analysis")
        print("3. Run 'python main.py --mode backtest' for historical testing")
        print("4. Customize config.json for your trading preferences")
        print("5. Paper trade before going live!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("Please check your installation and try again.")


if __name__ == "__main__":
    main()