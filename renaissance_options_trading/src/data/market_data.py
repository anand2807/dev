"""
Market Data Manager for Renaissance Options Trading System
Handles NSE/BSE data integration and option chain analysis
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Manages market data retrieval and processing"""
    
    def __init__(self):
        self.cache = {}
        self.last_update = {}
        
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if symbol == "NIFTY":
                # Use NIFTY 50 index
                ticker = yf.Ticker("^NSEI")
                data = ticker.history(period="1d", interval="1m")
                if not data.empty:
                    return float(data['Close'].iloc[-1])
            
            # For other symbols, try direct lookup
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
                
        except Exception as e:
            logger.warning(f"Failed to fetch price for {symbol}: {e}")
            
        # Return simulated price for demo
        return self._get_simulated_price(symbol)
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Generate simulated price for demo purposes"""
        base_prices = {
            "NIFTY": 19500.0,
            "BANKNIFTY": 44000.0,
            "RELIANCE": 2400.0,
            "TCS": 3200.0
        }
        
        base_price = base_prices.get(symbol, 1000.0)
        # Add some random variation
        variation = np.random.normal(0, 0.01)
        return base_price * (1 + variation)
    
    def get_option_chain(self, symbol: str, expiry: Optional[str] = None) -> Dict:
        """Get option chain data"""
        try:
            # For demo purposes, generate simulated option chain
            current_price = self.get_current_price(symbol)
            return self._generate_simulated_option_chain(symbol, current_price, expiry)
            
        except Exception as e:
            logger.error(f"Failed to fetch option chain for {symbol}: {e}")
            return {}
    
    def _generate_simulated_option_chain(self, symbol: str, spot_price: float, expiry: Optional[str] = None) -> Dict:
        """Generate simulated option chain for demo"""
        if not expiry:
            expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Generate strikes around current price
        strikes = []
        base_strike = round(spot_price / 50) * 50  # Round to nearest 50
        for i in range(-10, 11):
            strikes.append(base_strike + i * 50)
        
        calls = []
        puts = []
        
        for strike in strikes:
            # Simulate option prices using basic intrinsic + time value
            call_intrinsic = max(0, spot_price - strike)
            put_intrinsic = max(0, strike - spot_price)
            
            # Add time value (simplified)
            time_value = max(10, abs(strike - spot_price) * 0.1)
            
            call_price = call_intrinsic + time_value
            put_price = put_intrinsic + time_value
            
            # Simulate volumes and OI
            call_volume = np.random.randint(100, 10000)
            put_volume = np.random.randint(100, 10000)
            call_oi = np.random.randint(1000, 50000)
            put_oi = np.random.randint(1000, 50000)
            
            calls.append({
                'strike': strike,
                'price': call_price,
                'volume': call_volume,
                'oi': call_oi,
                'iv': 0.15 + np.random.normal(0, 0.05)
            })
            
            puts.append({
                'strike': strike,
                'price': put_price,
                'volume': put_volume,
                'oi': put_oi,
                'iv': 0.15 + np.random.normal(0, 0.05)
            })
        
        return {
            'symbol': symbol,
            'spot_price': spot_price,
            'expiry': expiry,
            'calls': calls,
            'puts': puts,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_pcr(self, option_chain: Dict) -> float:
        """Calculate Put-Call Ratio"""
        try:
            total_put_oi = sum(put['oi'] for put in option_chain['puts'])
            total_call_oi = sum(call['oi'] for call in option_chain['calls'])
            
            if total_call_oi > 0:
                return total_put_oi / total_call_oi
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating PCR: {e}")
            return 1.0
    
    def find_max_pain(self, option_chain: Dict) -> float:
        """Find max pain level"""
        try:
            strikes = [call['strike'] for call in option_chain['calls']]
            max_pain_values = []
            
            for strike in strikes:
                total_pain = 0
                
                # Calculate pain for calls
                for call in option_chain['calls']:
                    if call['strike'] < strike:
                        total_pain += call['oi'] * (strike - call['strike'])
                
                # Calculate pain for puts
                for put in option_chain['puts']:
                    if put['strike'] > strike:
                        total_pain += put['oi'] * (put['strike'] - strike)
                
                max_pain_values.append((strike, total_pain))
            
            # Find strike with minimum pain
            max_pain_strike = min(max_pain_values, key=lambda x: x[1])[0]
            return max_pain_strike
            
        except Exception as e:
            logger.error(f"Error calculating max pain: {e}")
            return option_chain.get('spot_price', 0)
    
    def detect_market_regime(self, symbol: str) -> str:
        """Detect current market regime"""
        try:
            # Get recent price data
            current_price = self.get_current_price(symbol)
            option_chain = self.get_option_chain(symbol)
            
            if not option_chain:
                return "UNKNOWN"
            
            # Calculate volatility indicators
            pcr = self.calculate_pcr(option_chain)
            
            # Simple regime detection based on PCR
            if pcr < 0.8:
                return "BULLISH"
            elif pcr > 1.2:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return "UNKNOWN"
    
    def get_support_resistance_levels(self, symbol: str) -> Dict[str, List[float]]:
        """Identify support and resistance levels from option chain"""
        try:
            option_chain = self.get_option_chain(symbol)
            if not option_chain:
                return {"support": [], "resistance": []}
            
            # Find strikes with high OI
            call_oi = [(call['strike'], call['oi']) for call in option_chain['calls']]
            put_oi = [(put['strike'], put['oi']) for put in option_chain['puts']]
            
            # Sort by OI and get top levels
            call_oi.sort(key=lambda x: x[1], reverse=True)
            put_oi.sort(key=lambda x: x[1], reverse=True)
            
            resistance_levels = [strike for strike, _ in call_oi[:3]]
            support_levels = [strike for strike, _ in put_oi[:3]]
            
            return {
                "support": support_levels,
                "resistance": resistance_levels
            }
            
        except Exception as e:
            logger.error(f"Error finding support/resistance: {e}")
            return {"support": [], "resistance": []}
    
    def calculate_implied_volatility_surface(self, symbol: str) -> pd.DataFrame:
        """Calculate implied volatility surface"""
        try:
            option_chain = self.get_option_chain(symbol)
            if not option_chain:
                return pd.DataFrame()
            
            # Create IV surface data
            data = []
            spot_price = option_chain['spot_price']
            
            for call in option_chain['calls']:
                moneyness = call['strike'] / spot_price
                data.append({
                    'strike': call['strike'],
                    'moneyness': moneyness,
                    'iv': call['iv'],
                    'type': 'CALL'
                })
            
            for put in option_chain['puts']:
                moneyness = put['strike'] / spot_price
                data.append({
                    'strike': put['strike'],
                    'moneyness': moneyness,
                    'iv': put['iv'],
                    'type': 'PUT'
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error calculating IV surface: {e}")
            return pd.DataFrame()