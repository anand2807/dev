"""
Volatility-based Trading Strategies
Implements sophisticated volatility trading strategies for options
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from ..utils.greeks import GreeksCalculator, PortfolioGreeks, time_to_expiry
from ..data.market_data import MarketDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    STRONG_BULLISH = "strong_bullish"
    STRONG_BEARISH = "strong_bearish"


class VolatilityRegime(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class TradingSignal:
    strategy: str
    action: str  # BUY, SELL, HOLD
    option_type: str  # CALL, PUT
    strike: float
    expiry: str
    quantity: int
    confidence: float
    reasoning: str
    expected_profit: float
    max_loss: float
    timestamp: datetime


@dataclass
class Position:
    symbol: str
    option_type: str
    strike: float
    expiry: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    pnl: float
    greeks: Dict[str, float]


class DirectionalVolatilityStrategy:
    """
    Core strategy that captures directional movements based on volatility patterns
    and option chain analysis - similar to Renaissance Technologies approach
    """
    
    def __init__(self, market_data_manager: MarketDataManager, 
                 greeks_calculator: GreeksCalculator):
        self.market_data = market_data_manager
        self.greeks_calc = greeks_calculator
        self.portfolio_greeks = PortfolioGreeks(greeks_calculator)
        
        # Strategy parameters
        self.volatility_threshold = 0.15  # 15% volatility threshold
        self.pcr_bullish_threshold = 0.8
        self.pcr_bearish_threshold = 1.2
        self.min_time_to_expiry = 7  # Minimum 7 days to expiry
        self.max_time_to_expiry = 45  # Maximum 45 days to expiry
        
    def analyze_market_regime(self, symbol: str = "NIFTY") -> Dict:
        """Analyze current market regime and volatility state"""
        real_time_data = self.market_data.get_real_time_data(symbol)
        historical_data = self.market_data.get_historical_analysis(symbol, days=30)
        
        option_analysis = real_time_data.get('option_analysis', {})
        
        # Determine volatility regime
        current_vol = historical_data.get('volatility', 0.15)
        vol_regime = self._classify_volatility_regime(current_vol)
        
        # Determine market direction
        direction_bias = option_analysis.get('directional_bias', 'neutral')
        pcr = option_analysis.get('pcr', 1.0)
        trend_analysis = historical_data.get('trend_analysis', {})
        
        market_direction = self._determine_market_direction(
            direction_bias, pcr, trend_analysis
        )
        
        # Analyze option chain patterns
        chain_patterns = self._analyze_option_chain_patterns(option_analysis)
        
        return {
            'volatility_regime': vol_regime,
            'market_direction': market_direction,
            'current_volatility': current_vol,
            'pcr': pcr,
            'chain_patterns': chain_patterns,
            'underlying_price': option_analysis.get('underlying_price', 0),
            'max_pain': option_analysis.get('max_pain', 0),
            'support_resistance': option_analysis.get('support_resistance', {}),
            'timestamp': datetime.now()
        }
    
    def _classify_volatility_regime(self, current_vol: float) -> VolatilityRegime:
        """Classify current volatility regime"""
        if current_vol < 0.12:
            return VolatilityRegime.LOW
        elif current_vol < 0.20:
            return VolatilityRegime.NORMAL
        elif current_vol < 0.35:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    def _determine_market_direction(self, direction_bias: str, pcr: float, 
                                  trend_analysis: Dict) -> MarketDirection:
        """Determine overall market direction"""
        trend = trend_analysis.get('trend', 'sideways')
        
        # Combine multiple signals
        signals = []
        
        # PCR signal
        if pcr < self.pcr_bullish_threshold:
            signals.append('bullish')
        elif pcr > self.pcr_bearish_threshold:
            signals.append('bearish')
        else:
            signals.append('neutral')
        
        # Direction bias signal
        signals.append(direction_bias)
        
        # Trend signal
        if 'bullish' in trend:
            signals.append('bullish')
        elif 'bearish' in trend:
            signals.append('bearish')
        else:
            signals.append('neutral')
        
        # Determine consensus
        bullish_count = signals.count('bullish')
        bearish_count = signals.count('bearish')
        
        if bullish_count >= 2:
            return MarketDirection.STRONG_BULLISH if bullish_count == 3 else MarketDirection.BULLISH
        elif bearish_count >= 2:
            return MarketDirection.STRONG_BEARISH if bearish_count == 3 else MarketDirection.BEARISH
        else:
            return MarketDirection.NEUTRAL
    
    def _analyze_option_chain_patterns(self, option_analysis: Dict) -> Dict:
        """Analyze option chain for specific patterns"""
        patterns = {
            'gamma_squeeze': False,
            'volatility_skew': 'normal',
            'unusual_activity': False,
            'support_test': False,
            'resistance_test': False
        }
        
        # Check for gamma squeeze
        gamma_levels = option_analysis.get('gamma_levels', [])
        underlying_price = option_analysis.get('underlying_price', 0)
        
        if gamma_levels and underlying_price:
            closest_gamma_level = min(gamma_levels, key=lambda x: abs(x - underlying_price))
            if abs(closest_gamma_level - underlying_price) < underlying_price * 0.01:  # Within 1%
                patterns['gamma_squeeze'] = True
        
        # Check volatility skew
        vol_skew = option_analysis.get('volatility_skew', {})
        skew_direction = vol_skew.get('skew_direction', 'normal')
        patterns['volatility_skew'] = skew_direction
        
        # Check support/resistance tests
        sr_levels = option_analysis.get('support_resistance', {})
        key_levels = sr_levels.get('key_levels', [])
        
        if key_levels and underlying_price:
            for level in key_levels:
                if abs(level - underlying_price) < underlying_price * 0.005:  # Within 0.5%
                    if level > underlying_price:
                        patterns['resistance_test'] = True
                    else:
                        patterns['support_test'] = True
        
        return patterns
    
    def generate_trading_signals(self, symbol: str = "NIFTY") -> List[TradingSignal]:
        """Generate trading signals based on market analysis"""
        market_regime = self.analyze_market_regime(symbol)
        signals = []
        
        direction = market_regime['market_direction']
        vol_regime = market_regime['volatility_regime']
        underlying_price = market_regime['underlying_price']
        chain_patterns = market_regime['chain_patterns']
        
        if underlying_price == 0:
            logger.warning("No underlying price available")
            return signals
        
        # Strategy 1: Directional Volatility Play
        if vol_regime in [VolatilityRegime.NORMAL, VolatilityRegime.HIGH]:
            directional_signal = self._generate_directional_signal(
                direction, underlying_price, market_regime
            )
            if directional_signal:
                signals.append(directional_signal)
        
        # Strategy 2: Volatility Expansion Play
        if vol_regime == VolatilityRegime.LOW and chain_patterns['gamma_squeeze']:
            expansion_signal = self._generate_volatility_expansion_signal(
                underlying_price, market_regime
            )
            if expansion_signal:
                signals.append(expansion_signal)
        
        # Strategy 3: Mean Reversion Play
        if vol_regime == VolatilityRegime.EXTREME:
            reversion_signal = self._generate_mean_reversion_signal(
                underlying_price, market_regime
            )
            if reversion_signal:
                signals.append(reversion_signal)
        
        # Strategy 4: Support/Resistance Bounce
        if chain_patterns['support_test'] or chain_patterns['resistance_test']:
            bounce_signal = self._generate_bounce_signal(
                underlying_price, market_regime, chain_patterns
            )
            if bounce_signal:
                signals.append(bounce_signal)
        
        return signals
    
    def _generate_directional_signal(self, direction: MarketDirection, 
                                   underlying_price: float, 
                                   market_regime: Dict) -> Optional[TradingSignal]:
        """Generate directional trading signal"""
        if direction == MarketDirection.NEUTRAL:
            return None
        
        # Determine option parameters
        if direction in [MarketDirection.BULLISH, MarketDirection.STRONG_BULLISH]:
            option_type = "CALL"
            # Slightly OTM call
            strike = self._round_to_nearest_strike(underlying_price * 1.01)
            confidence = 0.8 if direction == MarketDirection.STRONG_BULLISH else 0.6
        else:
            option_type = "PUT"
            # Slightly OTM put
            strike = self._round_to_nearest_strike(underlying_price * 0.99)
            confidence = 0.8 if direction == MarketDirection.STRONG_BEARISH else 0.6
        
        # Find optimal expiry
        expiry = self._find_optimal_expiry()
        
        # Calculate expected metrics
        time_to_exp = time_to_expiry(expiry)
        current_vol = market_regime['current_volatility']
        
        greeks = self.greeks_calc.calculate_all_greeks(
            S=underlying_price,
            K=strike,
            T=time_to_exp,
            sigma=current_vol,
            option_type=option_type.lower()
        )
        
        expected_profit = greeks['price'] * 0.3  # Target 30% profit
        max_loss = greeks['price']  # Maximum loss is premium paid
        
        return TradingSignal(
            strategy="directional_volatility",
            action="BUY",
            option_type=option_type,
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=confidence,
            reasoning=f"Directional play based on {direction.value} bias with {current_vol:.1%} volatility",
            expected_profit=expected_profit,
            max_loss=max_loss,
            timestamp=datetime.now()
        )
    
    def _generate_volatility_expansion_signal(self, underlying_price: float, 
                                            market_regime: Dict) -> Optional[TradingSignal]:
        """Generate volatility expansion signal (long straddle/strangle)"""
        # For now, implement simple ATM call buying
        # Later can be extended to straddles/strangles
        
        strike = self._round_to_nearest_strike(underlying_price)
        expiry = self._find_optimal_expiry()
        
        time_to_exp = time_to_expiry(expiry)
        current_vol = market_regime['current_volatility']
        
        # Buy ATM call expecting volatility expansion
        greeks = self.greeks_calc.calculate_all_greeks(
            S=underlying_price,
            K=strike,
            T=time_to_exp,
            sigma=current_vol,
            option_type='call'
        )
        
        return TradingSignal(
            strategy="volatility_expansion",
            action="BUY",
            option_type="CALL",
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=0.7,
            reasoning="Low volatility with gamma squeeze - expecting volatility expansion",
            expected_profit=greeks['price'] * 0.5,
            max_loss=greeks['price'],
            timestamp=datetime.now()
        )
    
    def _generate_mean_reversion_signal(self, underlying_price: float, 
                                      market_regime: Dict) -> Optional[TradingSignal]:
        """Generate mean reversion signal during extreme volatility"""
        # In extreme volatility, look for mean reversion opportunities
        # This is a contrarian approach
        
        direction = market_regime['market_direction']
        
        # Contrarian approach - if market is extremely bearish, buy calls
        if direction == MarketDirection.STRONG_BEARISH:
            option_type = "CALL"
            strike = self._round_to_nearest_strike(underlying_price * 0.98)  # Slightly OTM
        elif direction == MarketDirection.STRONG_BULLISH:
            option_type = "PUT"
            strike = self._round_to_nearest_strike(underlying_price * 1.02)  # Slightly OTM
        else:
            return None
        
        expiry = self._find_optimal_expiry()
        time_to_exp = time_to_expiry(expiry)
        current_vol = market_regime['current_volatility']
        
        greeks = self.greeks_calc.calculate_all_greeks(
            S=underlying_price,
            K=strike,
            T=time_to_exp,
            sigma=current_vol,
            option_type=option_type.lower()
        )
        
        return TradingSignal(
            strategy="mean_reversion",
            action="BUY",
            option_type=option_type,
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=0.6,
            reasoning="Extreme volatility - expecting mean reversion",
            expected_profit=greeks['price'] * 0.4,
            max_loss=greeks['price'],
            timestamp=datetime.now()
        )
    
    def _generate_bounce_signal(self, underlying_price: float, 
                              market_regime: Dict, 
                              chain_patterns: Dict) -> Optional[TradingSignal]:
        """Generate bounce signal at support/resistance levels"""
        if chain_patterns['support_test']:
            # At support, expect bounce up
            option_type = "CALL"
            strike = self._round_to_nearest_strike(underlying_price * 1.005)
            reasoning = "Testing support level - expecting bounce"
        elif chain_patterns['resistance_test']:
            # At resistance, expect rejection down
            option_type = "PUT"
            strike = self._round_to_nearest_strike(underlying_price * 0.995)
            reasoning = "Testing resistance level - expecting rejection"
        else:
            return None
        
        expiry = self._find_optimal_expiry(days=14)  # Shorter expiry for bounce plays
        time_to_exp = time_to_expiry(expiry)
        current_vol = market_regime['current_volatility']
        
        greeks = self.greeks_calc.calculate_all_greeks(
            S=underlying_price,
            K=strike,
            T=time_to_exp,
            sigma=current_vol,
            option_type=option_type.lower()
        )
        
        return TradingSignal(
            strategy="support_resistance_bounce",
            action="BUY",
            option_type=option_type,
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=0.65,
            reasoning=reasoning,
            expected_profit=greeks['price'] * 0.25,
            max_loss=greeks['price'],
            timestamp=datetime.now()
        )
    
    def _round_to_nearest_strike(self, price: float) -> float:
        """Round price to nearest NIFTY strike (typically 50 point intervals)"""
        return round(price / 50) * 50
    
    def _find_optimal_expiry(self, days: int = 30) -> str:
        """Find optimal expiry date"""
        # For now, return a date 'days' from now
        # In production, this should find actual option expiry dates
        target_date = datetime.now() + timedelta(days=days)
        
        # Round to nearest Thursday (typical NIFTY expiry)
        days_ahead = 3 - target_date.weekday()  # Thursday is 3
        if days_ahead <= 0:
            days_ahead += 7
        
        expiry_date = target_date + timedelta(days=days_ahead)
        return expiry_date.strftime("%Y-%m-%d")


class AdvancedVolatilityStrategies:
    """Advanced volatility strategies for experienced traders"""
    
    def __init__(self, directional_strategy: DirectionalVolatilityStrategy):
        self.directional_strategy = directional_strategy
        self.market_data = directional_strategy.market_data
        self.greeks_calc = directional_strategy.greeks_calc
    
    def long_straddle_strategy(self, underlying_price: float, 
                             expiry: str) -> List[TradingSignal]:
        """Long straddle - profit from high volatility in either direction"""
        strike = self.directional_strategy._round_to_nearest_strike(underlying_price)
        
        signals = []
        
        # Buy ATM Call
        call_signal = TradingSignal(
            strategy="long_straddle",
            action="BUY",
            option_type="CALL",
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=0.7,
            reasoning="Long straddle - expecting high volatility movement",
            expected_profit=0,  # Will be calculated
            max_loss=0,  # Will be calculated
            timestamp=datetime.now()
        )
        
        # Buy ATM Put
        put_signal = TradingSignal(
            strategy="long_straddle",
            action="BUY",
            option_type="PUT",
            strike=strike,
            expiry=expiry,
            quantity=1,
            confidence=0.7,
            reasoning="Long straddle - expecting high volatility movement",
            expected_profit=0,  # Will be calculated
            max_loss=0,  # Will be calculated
            timestamp=datetime.now()
        )
        
        signals.extend([call_signal, put_signal])
        return signals
    
    def long_strangle_strategy(self, underlying_price: float, 
                             expiry: str) -> List[TradingSignal]:
        """Long strangle - cheaper than straddle, needs larger moves"""
        call_strike = self.directional_strategy._round_to_nearest_strike(underlying_price * 1.02)
        put_strike = self.directional_strategy._round_to_nearest_strike(underlying_price * 0.98)
        
        signals = []
        
        # Buy OTM Call
        call_signal = TradingSignal(
            strategy="long_strangle",
            action="BUY",
            option_type="CALL",
            strike=call_strike,
            expiry=expiry,
            quantity=1,
            confidence=0.65,
            reasoning="Long strangle - expecting large volatility movement",
            expected_profit=0,
            max_loss=0,
            timestamp=datetime.now()
        )
        
        # Buy OTM Put
        put_signal = TradingSignal(
            strategy="long_strangle",
            action="BUY",
            option_type="PUT",
            strike=put_strike,
            expiry=expiry,
            quantity=1,
            confidence=0.65,
            reasoning="Long strangle - expecting large volatility movement",
            expected_profit=0,
            max_loss=0,
            timestamp=datetime.now()
        )
        
        signals.extend([call_signal, put_signal])
        return signals
    
    def iron_condor_strategy(self, underlying_price: float, 
                           expiry: str) -> List[TradingSignal]:
        """Iron condor - profit from low volatility (range-bound market)"""
        # This is a more complex strategy for later implementation
        # Involves 4 options: Buy OTM Put, Sell ITM Put, Sell ITM Call, Buy OTM Call
        pass
    
    def butterfly_spread_strategy(self, underlying_price: float, 
                                expiry: str) -> List[TradingSignal]:
        """Butterfly spread - profit from minimal price movement"""
        # Another complex strategy for later implementation
        pass


class RiskManager:
    """Risk management for volatility strategies"""
    
    def __init__(self, max_portfolio_risk: float = 0.02):
        self.max_portfolio_risk = max_portfolio_risk  # 2% of portfolio
        self.max_single_position_risk = 0.005  # 0.5% per position
        
    def calculate_position_size(self, signal: TradingSignal, 
                              portfolio_value: float) -> int:
        """Calculate appropriate position size based on risk management"""
        max_loss_per_position = portfolio_value * self.max_single_position_risk
        
        if signal.max_loss > 0:
            max_quantity = int(max_loss_per_position / signal.max_loss)
            return max(1, min(max_quantity, signal.quantity))
        
        return 1
    
    def validate_signal(self, signal: TradingSignal, 
                       current_positions: List[Position]) -> bool:
        """Validate if signal should be executed based on risk rules"""
        
        # Check confidence threshold
        if signal.confidence < 0.5:
            return False
        
        # Check if we already have similar position
        for position in current_positions:
            if (position.option_type == signal.option_type and 
                abs(position.strike - signal.strike) < 100 and
                position.expiry == signal.expiry):
                return False  # Avoid duplicate positions
        
        # Check portfolio concentration
        same_strategy_positions = [p for p in current_positions 
                                 if hasattr(p, 'strategy') and 
                                 getattr(p, 'strategy') == signal.strategy]
        
        if len(same_strategy_positions) >= 3:
            return False  # Max 3 positions per strategy
        
        return True