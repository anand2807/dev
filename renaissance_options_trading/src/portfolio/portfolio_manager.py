"""
Portfolio Management System
Manages positions, P&L tracking, and portfolio-level risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from ..strategies.volatility_strategies import TradingSignal, Position, RiskManager
from ..utils.greeks import GreeksCalculator, PortfolioGreeks
from ..data.market_data import MarketDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class Order:
    order_id: str
    signal: TradingSignal
    status: OrderStatus
    fill_price: Optional[float] = None
    fill_time: Optional[datetime] = None
    quantity_filled: int = 0
    commission: float = 0.0


@dataclass
class Trade:
    trade_id: str
    entry_order: Order
    exit_order: Optional[Order] = None
    pnl: float = 0.0
    return_pct: float = 0.0
    holding_period: Optional[timedelta] = None
    exit_reason: str = ""


class PortfolioManager:
    """Main portfolio management class"""
    
    def __init__(self, initial_capital: float, market_data_manager: MarketDataManager,
                 greeks_calculator: GreeksCalculator, risk_manager: RiskManager):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.market_data = market_data_manager
        self.greeks_calc = greeks_calculator
        self.portfolio_greeks = PortfolioGreeks(greeks_calculator)
        self.risk_manager = risk_manager
        
        # Portfolio state
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.trades: Dict[str, Trade] = {}
        self.cash_balance = initial_capital
        
        # Performance tracking
        self.daily_pnl = []
        self.portfolio_value_history = []
        self.drawdown_history = []
        
        # Risk limits
        self.max_positions = 20
        self.max_portfolio_delta = 1000
        self.max_portfolio_gamma = 500
        self.max_daily_loss = initial_capital * 0.02  # 2% daily loss limit
        
        logger.info(f"Portfolio initialized with capital: ₹{initial_capital:,.2f}")
    
    def process_signal(self, signal: TradingSignal) -> Optional[str]:
        """Process a trading signal and create order if valid"""
        
        # Validate signal
        if not self.risk_manager.validate_signal(signal, list(self.positions.values())):
            logger.warning(f"Signal validation failed for {signal.strategy}")
            return None
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(signal, self.current_capital)
        
        if position_size == 0:
            logger.warning("Position size calculated as 0")
            return None
        
        # Create order
        order_id = self._generate_order_id()
        order = Order(
            order_id=order_id,
            signal=signal,
            status=OrderStatus.PENDING,
            quantity_filled=0
        )
        
        self.orders[order_id] = order
        
        # Simulate order execution (in real trading, this would go to broker)
        self._execute_order(order_id)
        
        return order_id
    
    def _execute_order(self, order_id: str) -> bool:
        """Simulate order execution"""
        order = self.orders[order_id]
        signal = order.signal
        
        # Get current market price (simplified - would use real market data)
        current_price = self._get_option_price(signal)
        
        if current_price is None:
            order.status = OrderStatus.REJECTED
            logger.error(f"Could not get price for {signal.option_type} {signal.strike}")
            return False
        
        # Check if we have enough cash
        total_cost = current_price * signal.quantity * 50  # NIFTY lot size
        commission = total_cost * 0.001  # 0.1% commission
        
        if total_cost + commission > self.cash_balance:
            order.status = OrderStatus.REJECTED
            logger.warning(f"Insufficient funds for order {order_id}")
            return False
        
        # Execute the order
        order.status = OrderStatus.FILLED
        order.fill_price = current_price
        order.fill_time = datetime.now()
        order.quantity_filled = signal.quantity
        order.commission = commission
        
        # Update cash balance
        self.cash_balance -= (total_cost + commission)
        
        # Create position
        position_id = self._generate_position_id()
        position = Position(
            symbol="NIFTY",
            option_type=signal.option_type,
            strike=signal.strike,
            expiry=signal.expiry,
            quantity=signal.quantity,
            entry_price=current_price,
            current_price=current_price,
            entry_time=datetime.now(),
            pnl=0.0,
            greeks={}
        )
        
        self.positions[position_id] = position
        
        # Create trade record
        trade = Trade(
            trade_id=self._generate_trade_id(),
            entry_order=order
        )
        self.trades[trade.trade_id] = trade
        
        logger.info(f"Order executed: {signal.option_type} {signal.strike} @ ₹{current_price}")
        return True
    
    def update_positions(self) -> None:
        """Update all positions with current market prices and Greeks"""
        for position_id, position in self.positions.items():
            # Get current option price
            current_price = self._get_option_price_from_position(position)
            
            if current_price is not None:
                position.current_price = current_price
                
                # Calculate P&L
                pnl_per_lot = (current_price - position.entry_price) * 50  # NIFTY lot size
                position.pnl = pnl_per_lot * position.quantity
                
                # Update Greeks
                position.greeks = self._calculate_position_greeks(position)
            
            # Check for expiry
            if self._is_position_expired(position):
                self._handle_expiry(position_id)
    
    def _get_option_price(self, signal: TradingSignal) -> Optional[float]:
        """Get current option price (simplified implementation)"""
        try:
            # Get current NIFTY price
            real_time_data = self.market_data.get_real_time_data()
            underlying_price = real_time_data.get('option_analysis', {}).get('underlying_price', 0)
            
            if underlying_price == 0:
                return None
            
            # Calculate time to expiry
            expiry_date = datetime.strptime(signal.expiry, "%Y-%m-%d")
            time_to_exp = max((expiry_date - datetime.now()).days / 365, 0.001)
            
            # Use historical volatility as proxy for implied volatility
            historical_data = self.market_data.get_historical_analysis()
            volatility = historical_data.get('volatility', 0.2)
            
            # Calculate theoretical price using Black-Scholes
            greeks = self.greeks_calc.calculate_all_greeks(
                S=underlying_price,
                K=signal.strike,
                T=time_to_exp,
                sigma=volatility,
                option_type=signal.option_type.lower()
            )
            
            return greeks['price']
            
        except Exception as e:
            logger.error(f"Error getting option price: {e}")
            return None
    
    def _get_option_price_from_position(self, position: Position) -> Optional[float]:
        """Get current price for existing position"""
        # Create a temporary signal to reuse the pricing logic
        temp_signal = TradingSignal(
            strategy="temp",
            action="BUY",
            option_type=position.option_type,
            strike=position.strike,
            expiry=position.expiry,
            quantity=position.quantity,
            confidence=1.0,
            reasoning="temp",
            expected_profit=0,
            max_loss=0,
            timestamp=datetime.now()
        )
        
        return self._get_option_price(temp_signal)
    
    def _calculate_position_greeks(self, position: Position) -> Dict[str, float]:
        """Calculate Greeks for a position"""
        try:
            real_time_data = self.market_data.get_real_time_data()
            underlying_price = real_time_data.get('option_analysis', {}).get('underlying_price', 0)
            
            if underlying_price == 0:
                return {}
            
            expiry_date = datetime.strptime(position.expiry, "%Y-%m-%d")
            time_to_exp = max((expiry_date - datetime.now()).days / 365, 0.001)
            
            historical_data = self.market_data.get_historical_analysis()
            volatility = historical_data.get('volatility', 0.2)
            
            greeks = self.greeks_calc.calculate_all_greeks(
                S=underlying_price,
                K=position.strike,
                T=time_to_exp,
                sigma=volatility,
                option_type=position.option_type.lower()
            )
            
            # Multiply by position size and lot size
            multiplier = position.quantity * 50
            for key in greeks:
                if key != 'price':
                    greeks[key] *= multiplier
            
            return greeks
            
        except Exception as e:
            logger.error(f"Error calculating position Greeks: {e}")
            return {}
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        self.update_positions()
        
        # Calculate total P&L
        total_pnl = sum(position.pnl for position in self.positions.values())
        
        # Calculate portfolio Greeks
        portfolio_positions = []
        for position in self.positions.values():
            if position.greeks:
                portfolio_positions.append({
                    'quantity': position.quantity,
                    'S': self._get_current_underlying_price(),
                    'K': position.strike,
                    'T': self._get_time_to_expiry(position.expiry),
                    'sigma': 0.2,  # Default volatility
                    'option_type': position.option_type.lower(),
                    'lot_size': 50
                })
        
        portfolio_greeks = {}
        if portfolio_positions:
            portfolio_greeks = self.portfolio_greeks.calculate_portfolio_greeks(portfolio_positions)
        
        # Calculate portfolio value
        portfolio_value = self.cash_balance + total_pnl
        
        # Calculate returns
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        
        # Risk metrics
        risk_metrics = {}
        if portfolio_positions:
            risk_metrics = self.portfolio_greeks.calculate_risk_metrics(
                portfolio_positions, self._get_current_underlying_price()
            )
        
        return {
            'timestamp': datetime.now(),
            'portfolio_value': portfolio_value,
            'cash_balance': self.cash_balance,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'num_positions': len(self.positions),
            'portfolio_greeks': portfolio_greeks,
            'risk_metrics': risk_metrics,
            'positions': [asdict(pos) for pos in self.positions.values()],
            'recent_trades': self._get_recent_trades(5)
        }
    
    def close_position(self, position_id: str, reason: str = "manual") -> bool:
        """Close a specific position"""
        if position_id not in self.positions:
            logger.error(f"Position {position_id} not found")
            return False
        
        position = self.positions[position_id]
        
        # Get current price
        current_price = self._get_option_price_from_position(position)
        
        if current_price is None:
            logger.error(f"Could not get current price for position {position_id}")
            return False
        
        # Calculate final P&L
        pnl_per_lot = (current_price - position.entry_price) * 50
        final_pnl = pnl_per_lot * position.quantity
        
        # Update cash balance
        proceeds = current_price * position.quantity * 50
        commission = proceeds * 0.001
        self.cash_balance += (proceeds - commission)
        
        # Update trade record
        trade = self._find_trade_by_position(position_id)
        if trade:
            exit_order = Order(
                order_id=self._generate_order_id(),
                signal=None,  # Exit order
                status=OrderStatus.FILLED,
                fill_price=current_price,
                fill_time=datetime.now(),
                quantity_filled=position.quantity,
                commission=commission
            )
            
            trade.exit_order = exit_order
            trade.pnl = final_pnl
            trade.return_pct = final_pnl / (position.entry_price * position.quantity * 50)
            trade.holding_period = datetime.now() - position.entry_time
            trade.exit_reason = reason
        
        # Remove position
        del self.positions[position_id]
        
        logger.info(f"Position closed: {position.option_type} {position.strike} P&L: ₹{final_pnl:.2f}")
        return True
    
    def close_all_positions(self, reason: str = "end_of_day") -> None:
        """Close all open positions"""
        position_ids = list(self.positions.keys())
        for position_id in position_ids:
            self.close_position(position_id, reason)
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """Check if portfolio is within risk limits"""
        self.update_positions()
        
        # Calculate current metrics
        total_pnl = sum(position.pnl for position in self.positions.values())
        portfolio_value = self.cash_balance + total_pnl
        
        # Daily loss check
        daily_loss = self.initial_capital - portfolio_value
        daily_loss_exceeded = daily_loss > self.max_daily_loss
        
        # Position count check
        position_count_exceeded = len(self.positions) > self.max_positions
        
        # Portfolio Greeks check
        portfolio_positions = []
        for position in self.positions.values():
            if position.greeks:
                portfolio_positions.append({
                    'quantity': position.quantity,
                    'S': self._get_current_underlying_price(),
                    'K': position.strike,
                    'T': self._get_time_to_expiry(position.expiry),
                    'sigma': 0.2,
                    'option_type': position.option_type.lower(),
                    'lot_size': 50
                })
        
        delta_exceeded = False
        gamma_exceeded = False
        
        if portfolio_positions:
            portfolio_greeks = self.portfolio_greeks.calculate_portfolio_greeks(portfolio_positions)
            delta_exceeded = abs(portfolio_greeks.get('total_delta', 0)) > self.max_portfolio_delta
            gamma_exceeded = abs(portfolio_greeks.get('total_gamma', 0)) > self.max_portfolio_gamma
        
        risk_status = {
            'daily_loss_exceeded': daily_loss_exceeded,
            'position_count_exceeded': position_count_exceeded,
            'delta_exceeded': delta_exceeded,
            'gamma_exceeded': gamma_exceeded,
            'any_limit_exceeded': any([daily_loss_exceeded, position_count_exceeded, 
                                     delta_exceeded, gamma_exceeded])
        }
        
        if risk_status['any_limit_exceeded']:
            logger.warning(f"Risk limits exceeded: {risk_status}")
        
        return risk_status
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        completed_trades = [trade for trade in self.trades.values() 
                          if trade.exit_order is not None]
        
        if not completed_trades:
            return {'message': 'No completed trades yet'}
        
        # Calculate performance metrics
        total_trades = len(completed_trades)
        winning_trades = [t for t in completed_trades if t.pnl > 0]
        losing_trades = [t for t in completed_trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(trade.pnl for trade in completed_trades)
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Calculate Sharpe ratio (simplified)
        returns = [trade.return_pct for trade in completed_trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 else 0
        
        # Calculate maximum drawdown
        portfolio_values = [self.initial_capital]
        running_pnl = 0
        for trade in completed_trades:
            running_pnl += trade.pnl
            portfolio_values.append(self.initial_capital + running_pnl)
        
        peak = portfolio_values[0]
        max_drawdown = 0
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'current_portfolio_value': self.cash_balance + sum(p.pnl for p in self.positions.values()),
            'total_return': total_pnl / self.initial_capital
        }
    
    # Helper methods
    def _generate_order_id(self) -> str:
        return f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.orders)}"
    
    def _generate_position_id(self) -> str:
        return f"POS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.positions)}"
    
    def _generate_trade_id(self) -> str:
        return f"TRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.trades)}"
    
    def _get_current_underlying_price(self) -> float:
        real_time_data = self.market_data.get_real_time_data()
        return real_time_data.get('option_analysis', {}).get('underlying_price', 18000)
    
    def _get_time_to_expiry(self, expiry: str) -> float:
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
        return max((expiry_date - datetime.now()).days / 365, 0.001)
    
    def _is_position_expired(self, position: Position) -> bool:
        expiry_date = datetime.strptime(position.expiry, "%Y-%m-%d")
        return datetime.now().date() >= expiry_date.date()
    
    def _handle_expiry(self, position_id: str) -> None:
        """Handle position expiry"""
        position = self.positions[position_id]
        
        # For simplicity, assume options expire worthless if OTM
        underlying_price = self._get_current_underlying_price()
        
        if position.option_type == "CALL":
            final_value = max(underlying_price - position.strike, 0)
        else:
            final_value = max(position.strike - underlying_price, 0)
        
        # Calculate final P&L
        final_pnl = (final_value - position.entry_price) * position.quantity * 50
        
        # Update trade record
        trade = self._find_trade_by_position(position_id)
        if trade:
            trade.pnl = final_pnl
            trade.exit_reason = "expiry"
            trade.holding_period = datetime.now() - position.entry_time
        
        # Remove position
        del self.positions[position_id]
        
        logger.info(f"Position expired: {position.option_type} {position.strike} Final P&L: ₹{final_pnl:.2f}")
    
    def _find_trade_by_position(self, position_id: str) -> Optional[Trade]:
        """Find trade record for a position"""
        # This is simplified - in practice, you'd maintain better linkage
        for trade in self.trades.values():
            if trade.exit_order is None:  # Open trade
                return trade
        return None
    
    def _get_recent_trades(self, count: int) -> List[Dict]:
        """Get recent completed trades"""
        completed_trades = [trade for trade in self.trades.values() 
                          if trade.exit_order is not None]
        
        # Sort by exit time
        completed_trades.sort(key=lambda t: t.exit_order.fill_time, reverse=True)
        
        return [asdict(trade) for trade in completed_trades[:count]]