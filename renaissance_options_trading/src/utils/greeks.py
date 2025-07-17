"""
Options Greeks Calculator
Implements Black-Scholes model and Greeks calculations for Indian options
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize_scalar
from typing import Dict, Tuple
import math
from datetime import datetime, timedelta


class GreeksCalculator:
    """Calculate all Greeks for options using Black-Scholes model"""
    
    def __init__(self, risk_free_rate: float = 0.06):
        self.risk_free_rate = risk_free_rate
        
    def black_scholes_price(self, S: float, K: float, T: float, r: float, 
                           sigma: float, option_type: str = 'call') -> float:
        """
        Calculate Black-Scholes option price
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility
            option_type: 'call' or 'put'
        """
        if T <= 0:
            if option_type.lower() == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)
                
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        return max(price, 0)
    
    def calculate_delta(self, S: float, K: float, T: float, r: float, 
                       sigma: float, option_type: str = 'call') -> float:
        """Calculate Delta (price sensitivity to underlying)"""
        if T <= 0:
            if option_type.lower() == 'call':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
                
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, 
                       sigma: float) -> float:
        """Calculate Gamma (rate of change of Delta)"""
        if T <= 0:
            return 0.0
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    def calculate_theta(self, S: float, K: float, T: float, r: float, 
                       sigma: float, option_type: str = 'call') -> float:
        """Calculate Theta (time decay)"""
        if T <= 0:
            return 0.0
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * norm.cdf(d2))
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * norm.cdf(-d2))
            
        return theta / 365  # Convert to daily theta
    
    def calculate_vega(self, S: float, K: float, T: float, r: float, 
                      sigma: float) -> float:
        """Calculate Vega (sensitivity to volatility)"""
        if T <= 0:
            return 0.0
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change in volatility
    
    def calculate_rho(self, S: float, K: float, T: float, r: float, 
                     sigma: float, option_type: str = 'call') -> float:
        """Calculate Rho (sensitivity to interest rate)"""
        if T <= 0:
            return 0.0
            
        d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() == 'call':
            return K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    def calculate_all_greeks(self, S: float, K: float, T: float, 
                           sigma: float, option_type: str = 'call',
                           r: float = None) -> Dict[str, float]:
        """Calculate all Greeks for an option"""
        if r is None:
            r = self.risk_free_rate
            
        greeks = {
            'price': self.black_scholes_price(S, K, T, r, sigma, option_type),
            'delta': self.calculate_delta(S, K, T, r, sigma, option_type),
            'gamma': self.calculate_gamma(S, K, T, r, sigma),
            'theta': self.calculate_theta(S, K, T, r, sigma, option_type),
            'vega': self.calculate_vega(S, K, T, r, sigma),
            'rho': self.calculate_rho(S, K, T, r, sigma, option_type)
        }
        
        return greeks
    
    def implied_volatility(self, market_price: float, S: float, K: float, 
                          T: float, option_type: str = 'call', 
                          r: float = None) -> float:
        """Calculate implied volatility using Brent's method"""
        if r is None:
            r = self.risk_free_rate
            
        def objective(sigma):
            try:
                theoretical_price = self.black_scholes_price(S, K, T, r, sigma, option_type)
                return abs(theoretical_price - market_price)
            except:
                return float('inf')
        
        try:
            result = minimize_scalar(objective, bounds=(0.01, 5.0), method='bounded')
            return result.x if result.success else 0.2  # Default to 20% if optimization fails
        except:
            return 0.2


class PortfolioGreeks:
    """Calculate portfolio-level Greeks"""
    
    def __init__(self, greeks_calculator: GreeksCalculator):
        self.calculator = greeks_calculator
        
    def calculate_portfolio_greeks(self, positions: list) -> Dict[str, float]:
        """
        Calculate portfolio Greeks
        
        Args:
            positions: List of position dictionaries with keys:
                - quantity: Number of contracts
                - S: Underlying price
                - K: Strike price
                - T: Time to expiration
                - sigma: Volatility
                - option_type: 'call' or 'put'
        """
        portfolio_greeks = {
            'total_delta': 0,
            'total_gamma': 0,
            'total_theta': 0,
            'total_vega': 0,
            'total_rho': 0,
            'net_premium': 0
        }
        
        for position in positions:
            quantity = position['quantity']
            greeks = self.calculator.calculate_all_greeks(
                S=position['S'],
                K=position['K'],
                T=position['T'],
                sigma=position['sigma'],
                option_type=position['option_type']
            )
            
            # Multiply by quantity and lot size (typically 50 for NIFTY)
            lot_size = position.get('lot_size', 50)
            multiplier = quantity * lot_size
            
            portfolio_greeks['total_delta'] += greeks['delta'] * multiplier
            portfolio_greeks['total_gamma'] += greeks['gamma'] * multiplier
            portfolio_greeks['total_theta'] += greeks['theta'] * multiplier
            portfolio_greeks['total_vega'] += greeks['vega'] * multiplier
            portfolio_greeks['total_rho'] += greeks['rho'] * multiplier
            portfolio_greeks['net_premium'] += greeks['price'] * multiplier
            
        return portfolio_greeks
    
    def calculate_risk_metrics(self, positions: list, underlying_price: float) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        portfolio_greeks = self.calculate_portfolio_greeks(positions)
        
        # Calculate potential P&L for different scenarios
        scenarios = {
            'up_1_percent': underlying_price * 1.01,
            'up_2_percent': underlying_price * 1.02,
            'down_1_percent': underlying_price * 0.99,
            'down_2_percent': underlying_price * 0.98
        }
        
        scenario_pnl = {}
        for scenario_name, new_price in scenarios.items():
            price_change = new_price - underlying_price
            
            # Approximate P&L using Delta and Gamma
            delta_pnl = portfolio_greeks['total_delta'] * price_change
            gamma_pnl = 0.5 * portfolio_greeks['total_gamma'] * (price_change ** 2)
            
            scenario_pnl[scenario_name] = delta_pnl + gamma_pnl
        
        # Calculate maximum risk
        max_loss = min(scenario_pnl.values())
        max_gain = max(scenario_pnl.values())
        
        return {
            'max_potential_loss': max_loss,
            'max_potential_gain': max_gain,
            'daily_theta_decay': portfolio_greeks['total_theta'],
            'volatility_exposure': portfolio_greeks['total_vega'],
            'delta_exposure': portfolio_greeks['total_delta'],
            'scenario_pnl': scenario_pnl
        }


class VolatilityAnalyzer:
    """Analyze volatility patterns and predict future volatility"""
    
    def __init__(self):
        pass
        
    def calculate_realized_volatility(self, price_data: pd.DataFrame, 
                                    window: int = 20) -> pd.Series:
        """Calculate realized volatility"""
        returns = np.log(price_data['Close'] / price_data['Close'].shift(1))
        return returns.rolling(window=window).std() * np.sqrt(252)
    
    def calculate_garch_volatility(self, returns: pd.Series) -> pd.Series:
        """Calculate GARCH volatility (simplified implementation)"""
        # This is a simplified GARCH(1,1) implementation
        # For production, consider using arch library
        
        alpha = 0.1  # ARCH parameter
        beta = 0.85  # GARCH parameter
        omega = 0.01  # Long-term variance
        
        variance = pd.Series(index=returns.index, dtype=float)
        variance.iloc[0] = returns.var()
        
        for i in range(1, len(returns)):
            variance.iloc[i] = (omega + 
                              alpha * returns.iloc[i-1]**2 + 
                              beta * variance.iloc[i-1])
        
        return np.sqrt(variance * 252)  # Annualized volatility
    
    def volatility_cone(self, price_data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Create volatility cone analysis"""
        returns = np.log(price_data['Close'] / price_data['Close'].shift(1))
        
        periods = [5, 10, 20, 30, 60, 90]
        percentiles = [10, 25, 50, 75, 90]
        
        cone_data = {}
        
        for period in periods:
            vol_series = returns.rolling(window=period).std() * np.sqrt(252)
            cone_data[f'{period}d'] = vol_series.quantile([p/100 for p in percentiles])
        
        return cone_data
    
    def volatility_surface(self, option_data: pd.DataFrame) -> pd.DataFrame:
        """Create implied volatility surface"""
        # This would typically require option market data
        # Placeholder implementation
        strikes = option_data['strike'].unique()
        expiries = option_data['expiry'].unique()
        
        surface = pd.DataFrame(index=strikes, columns=expiries)
        
        for strike in strikes:
            for expiry in expiries:
                subset = option_data[(option_data['strike'] == strike) & 
                                   (option_data['expiry'] == expiry)]
                if not subset.empty:
                    surface.loc[strike, expiry] = subset['implied_vol'].mean()
        
        return surface.astype(float)


def time_to_expiry(expiry_date: str) -> float:
    """Calculate time to expiry in years"""
    if isinstance(expiry_date, str):
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
    else:
        expiry = expiry_date
        
    now = datetime.now()
    days_to_expiry = (expiry - now).days
    
    # Account for trading days (approximately 252 trading days per year)
    return max(days_to_expiry / 365, 0.001)  # Minimum 0.001 to avoid division by zero


def moneyness(spot_price: float, strike_price: float) -> str:
    """Determine option moneyness"""
    ratio = spot_price / strike_price
    
    if ratio > 1.02:
        return "ITM"  # In the money
    elif ratio < 0.98:
        return "OTM"  # Out of the money
    else:
        return "ATM"  # At the money