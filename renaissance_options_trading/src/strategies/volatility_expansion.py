"""
Volatility Expansion Strategy for Renaissance Options Trading System
Captures profit from volatility breakouts and expansions
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VolatilityExpansionStrategy:
    """Strategy that profits from volatility expansion using straddles/strangles"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.low_vol_threshold = config.get('low_vol_threshold', 0.12)
        self.expansion_threshold = config.get('expansion_threshold', 0.25)
        self.profit_target = config.get('profit_target', 0.4)
        self.stop_loss = config.get('stop_loss', 0.6)
        
    def detect_low_volatility_regime(self, option_chain: Dict) -> bool:
        """Detect if market is in low volatility regime"""
        try:
            if not option_chain or 'calls' not in option_chain:
                return False
            
            # Calculate average implied volatility
            call_ivs = [call['iv'] for call in option_chain['calls'] if 'iv' in call]
            put_ivs = [put['iv'] for put in option_chain['puts'] if 'iv' in put]
            
            if not call_ivs or not put_ivs:
                return False
            
            avg_iv = np.mean(call_ivs + put_ivs)
            return avg_iv < self.low_vol_threshold
            
        except Exception as e:
            logger.error(f"Error detecting low volatility regime: {e}")
            return False
    
    def find_optimal_straddle_strikes(self, option_chain: Dict, spot_price: float) -> List[Dict]:
        """Find optimal strikes for straddle positions"""
        try:
            signals = []
            
            if not self.detect_low_volatility_regime(option_chain):
                return signals
            
            # Find ATM and nearby strikes
            strikes_to_check = []
            for call in option_chain['calls']:
                strike = call['strike']
                if abs(strike - spot_price) <= spot_price * 0.05:  # Within 5% of spot
                    strikes_to_check.append(strike)
            
            for strike in strikes_to_check:
                # Find corresponding call and put
                call_option = next((c for c in option_chain['calls'] if c['strike'] == strike), None)
                put_option = next((p for p in option_chain['puts'] if p['strike'] == strike), None)
                
                if call_option and put_option:
                    # Calculate straddle cost and breakeven points
                    straddle_cost = call_option['price'] + put_option['price']
                    upper_breakeven = strike + straddle_cost
                    lower_breakeven = strike - straddle_cost
                    
                    # Calculate expected profit potential
                    profit_potential = self._calculate_straddle_profit_potential(
                        strike, straddle_cost, spot_price, option_chain
                    )
                    
                    if profit_potential > 0.3:  # Minimum 30% profit potential
                        signal = {
                            'type': 'straddle',
                            'strike': strike,
                            'call_price': call_option['price'],
                            'put_price': put_option['price'],
                            'total_cost': straddle_cost,
                            'upper_breakeven': upper_breakeven,
                            'lower_breakeven': lower_breakeven,
                            'profit_potential': profit_potential,
                            'confidence': min(0.9, profit_potential),
                            'timestamp': datetime.now().isoformat()
                        }
                        signals.append(signal)
            
            # Sort by profit potential
            signals.sort(key=lambda x: x['profit_potential'], reverse=True)
            return signals[:3]  # Return top 3 signals
            
        except Exception as e:
            logger.error(f"Error finding straddle strikes: {e}")
            return []
    
    def find_optimal_strangle_strikes(self, option_chain: Dict, spot_price: float) -> List[Dict]:
        """Find optimal strikes for strangle positions"""
        try:
            signals = []
            
            if not self.detect_low_volatility_regime(option_chain):
                return signals
            
            # Find OTM call and put strikes
            otm_calls = [c for c in option_chain['calls'] if c['strike'] > spot_price * 1.02]
            otm_puts = [p for p in option_chain['puts'] if p['strike'] < spot_price * 0.98]
            
            # Sort by distance from spot
            otm_calls.sort(key=lambda x: x['strike'])
            otm_puts.sort(key=lambda x: x['strike'], reverse=True)
            
            # Try different combinations
            for call in otm_calls[:5]:  # Check top 5 OTM calls
                for put in otm_puts[:5]:  # Check top 5 OTM puts
                    strangle_cost = call['price'] + put['price']
                    
                    # Calculate breakeven points
                    upper_breakeven = call['strike'] + strangle_cost
                    lower_breakeven = put['strike'] - strangle_cost
                    
                    # Calculate profit potential
                    profit_potential = self._calculate_strangle_profit_potential(
                        call['strike'], put['strike'], strangle_cost, spot_price, option_chain
                    )
                    
                    if profit_potential > 0.25:  # Minimum 25% profit potential
                        signal = {
                            'type': 'strangle',
                            'call_strike': call['strike'],
                            'put_strike': put['strike'],
                            'call_price': call['price'],
                            'put_price': put['price'],
                            'total_cost': strangle_cost,
                            'upper_breakeven': upper_breakeven,
                            'lower_breakeven': lower_breakeven,
                            'profit_potential': profit_potential,
                            'confidence': min(0.8, profit_potential),
                            'timestamp': datetime.now().isoformat()
                        }
                        signals.append(signal)
            
            # Sort by profit potential
            signals.sort(key=lambda x: x['profit_potential'], reverse=True)
            return signals[:2]  # Return top 2 signals
            
        except Exception as e:
            logger.error(f"Error finding strangle strikes: {e}")
            return []
    
    def _calculate_straddle_profit_potential(self, strike: float, cost: float, 
                                           spot_price: float, option_chain: Dict) -> float:
        """Calculate profit potential for straddle"""
        try:
            # Estimate potential price movements based on historical volatility
            expected_move = spot_price * 0.15  # Assume 15% potential move
            
            # Calculate profit at expected move levels
            upside_profit = max(0, (spot_price + expected_move) - strike - cost)
            downside_profit = max(0, strike - (spot_price - expected_move) - cost)
            
            max_profit = max(upside_profit, downside_profit)
            return max_profit / cost if cost > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating straddle profit potential: {e}")
            return 0
    
    def _calculate_strangle_profit_potential(self, call_strike: float, put_strike: float,
                                           cost: float, spot_price: float, option_chain: Dict) -> float:
        """Calculate profit potential for strangle"""
        try:
            # Estimate potential price movements
            expected_move = spot_price * 0.12  # Assume 12% potential move
            
            # Calculate profit at expected move levels
            upside_profit = max(0, (spot_price + expected_move) - call_strike - cost)
            downside_profit = max(0, put_strike - (spot_price - expected_move) - cost)
            
            max_profit = max(upside_profit, downside_profit)
            return max_profit / cost if cost > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating strangle profit potential: {e}")
            return 0
    
    def generate_signals(self, option_chain: Dict, current_price: float) -> List[Dict]:
        """Generate volatility expansion signals"""
        try:
            all_signals = []
            
            # Generate straddle signals
            straddle_signals = self.find_optimal_straddle_strikes(option_chain, current_price)
            all_signals.extend(straddle_signals)
            
            # Generate strangle signals
            strangle_signals = self.find_optimal_strangle_strikes(option_chain, current_price)
            all_signals.extend(strangle_signals)
            
            # Filter by confidence and return best signals
            filtered_signals = [s for s in all_signals if s['confidence'] >= 0.4]
            filtered_signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            return filtered_signals[:3]  # Return top 3 signals
            
        except Exception as e:
            logger.error(f"Error generating volatility expansion signals: {e}")
            return []
    
    def calculate_position_sizing(self, signal: Dict, available_capital: float, 
                                risk_per_trade: float) -> int:
        """Calculate optimal position size for volatility expansion trades"""
        try:
            risk_amount = available_capital * risk_per_trade
            position_cost = signal['total_cost']
            
            if position_cost <= 0:
                return 0
            
            # Calculate maximum quantity based on risk
            max_quantity = int(risk_amount / position_cost)
            
            # Apply additional constraints
            min_quantity = 1
            max_quantity_limit = 10  # Maximum 10 lots per signal
            
            return max(min_quantity, min(max_quantity, max_quantity_limit))
            
        except Exception as e:
            logger.error(f"Error calculating position sizing: {e}")
            return 1