"""
Volatility-based Trading Strategies for Renaissance Options Trading System
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DirectionalVolatilityStrategy:
    """Strategy that captures market direction using volatility patterns"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        self.profit_target = config.get('profit_target', 0.3)
        self.stop_loss = config.get('stop_loss', 0.5)
    
    def generate_signals(self, option_chain: Dict, current_price: float) -> List[Dict]:
        """Generate trading signals based on volatility analysis"""
        signals = []
        
        try:
            if not option_chain or 'calls' not in option_chain:
                return signals
            
            # Calculate PCR
            total_put_oi = sum(put['oi'] for put in option_chain['puts'])
            total_call_oi = sum(call['oi'] for call in option_chain['calls'])
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
            
            # Generate signals based on PCR
            if pcr < 0.8:  # Bullish signal
                # Find ATM call option
                atm_call = min(option_chain['calls'], 
                             key=lambda x: abs(x['strike'] - current_price))
                
                signal = {
                    'type': 'call',
                    'strike': atm_call['strike'],
                    'confidence': min(0.9, (0.8 - pcr) * 2),
                    'target_price': atm_call['price'] * (1 + self.profit_target),
                    'stop_price': atm_call['price'] * (1 - self.stop_loss),
                    'timestamp': datetime.now().isoformat()
                }
                signals.append(signal)
                
            elif pcr > 1.2:  # Bearish signal
                # Find ATM put option
                atm_put = min(option_chain['puts'], 
                            key=lambda x: abs(x['strike'] - current_price))
                
                signal = {
                    'type': 'put',
                    'strike': atm_put['strike'],
                    'confidence': min(0.9, (pcr - 1.2) * 2),
                    'target_price': atm_put['price'] * (1 + self.profit_target),
                    'stop_price': atm_put['price'] * (1 - self.stop_loss),
                    'timestamp': datetime.now().isoformat()
                }
                signals.append(signal)
            
            # Filter by confidence threshold
            signals = [s for s in signals if s['confidence'] >= self.confidence_threshold]
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals