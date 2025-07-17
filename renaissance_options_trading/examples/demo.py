#!/usr/bin/env python3
"""
Renaissance Options Trading System - Demo Script
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from data.market_data import MarketDataManager
from utils.greeks import GreeksCalculator
from strategies.volatility_strategies import DirectionalVolatilityStrategy
from portfolio.portfolio_manager import PortfolioManager

def main():
    print("🏛️ Renaissance Options Trading System - Demo")
    print("=" * 50)
    
    # Initialize components
    market_data = MarketDataManager()
    greeks_calc = GreeksCalculator()
    strategy = DirectionalVolatilityStrategy({'confidence_threshold': 0.6})
    portfolio = PortfolioManager(100000, {'max_positions': 20, 'risk_per_trade': 0.02})
    
    # Demo market analysis
    print("\n📊 Market Analysis:")
    current_price = market_data.get_current_price("NIFTY")
    print(f"Current NIFTY Price: ₹{current_price:.2f}")
    
    # Demo option chain
    option_chain = market_data.get_option_chain("NIFTY")
    if option_chain:
        pcr = market_data.calculate_pcr(option_chain)
        print(f"Put-Call Ratio: {pcr:.2f}")
    
    # Demo Greeks calculation
    print("\n🧮 Greeks Calculation:")
    greeks = greeks_calc.calculate_all_greeks(
        S=current_price, K=current_price, T=0.08, sigma=0.15, option_type='CALL'
    )
    print(f"ATM Call Greeks: Delta={greeks['delta']:.3f}, Gamma={greeks['gamma']:.3f}")
    
    # Demo signal generation
    print("\n🎯 Signal Generation:")
    signals = strategy.generate_signals(option_chain, current_price)
    if signals:
        for signal in signals:
            print(f"Signal: {signal['type'].upper()} {signal['strike']} (Confidence: {signal['confidence']:.2f})")
    else:
        print("No signals generated")
    
    # Demo portfolio
    print("\n💼 Portfolio Status:")
    summary = portfolio.get_portfolio_summary()
    print(f"Capital: ₹{summary['current_capital']:,.2f}")
    print(f"Active Positions: {summary['active_positions']}")
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    main()