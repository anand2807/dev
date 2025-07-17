"""
Portfolio Manager for Renaissance Options Trading System
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Manages portfolio positions and risk"""
    
    def __init__(self, initial_capital: float, config: Dict):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.config = config
        self.positions = []
        self.trade_history = []
        
    def add_position(self, position: Dict) -> bool:
        """Add a new position to portfolio"""
        try:
            # Check position limits
            if len(self.positions) >= self.config.get('max_positions', 20):
                logger.warning("Maximum positions reached")
                return False
            
            # Calculate position size
            risk_amount = self.current_capital * self.config.get('risk_per_trade', 0.02)
            position['quantity'] = int(risk_amount / position['price'])
            position['timestamp'] = datetime.now().isoformat()
            
            self.positions.append(position)
            logger.info(f"Added position: {position['type']} {position['strike']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return False
    
    def close_position(self, position_id: int, exit_price: float) -> bool:
        """Close a position"""
        try:
            if 0 <= position_id < len(self.positions):
                position = self.positions.pop(position_id)
                
                # Calculate P&L
                pnl = (exit_price - position['price']) * position['quantity']
                self.current_capital += pnl
                
                # Record trade
                trade = {
                    'entry_price': position['price'],
                    'exit_price': exit_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'timestamp': datetime.now().isoformat()
                }
                self.trade_history.append(trade)
                
                logger.info(f"Closed position with P&L: ₹{pnl:.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
        
        return False
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        try:
            total_pnl = self.current_capital - self.initial_capital
            
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_pnl': total_pnl,
                'total_pnl_pct': (total_pnl / self.initial_capital) * 100,
                'active_positions': len(self.positions),
                'total_trades': len(self.trade_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}