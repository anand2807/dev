"""
Greeks Calculator for Renaissance Options Trading System
Implements Black-Scholes model and Greeks calculations
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model"""
    
    def __init__(self, risk_free_rate: float = 0.065):
        self.risk_free_rate = risk_free_rate
    
    def black_scholes_call(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price"""
        try:
            if T <= 0:
                return max(0, S - K)
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            return max(0, call_price)
            
        except Exception as e:
            logger.error(f"Error in Black-Scholes call calculation: {e}")
            return 0.0
    
    def black_scholes_put(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price"""
        try:
            if T <= 0:
                return max(0, K - S)
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            return max(0, put_price)
            
        except Exception as e:
            logger.error(f"Error in Black-Scholes put calculation: {e}")
            return 0.0
    
    def calculate_delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate option delta"""
        try:
            if T <= 0:
                if option_type.upper() == 'CALL':
                    return 1.0 if S > K else 0.0
                else:
                    return -1.0 if S < K else 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            
            if option_type.upper() == 'CALL':
                return norm.cdf(d1)
            else:
                return norm.cdf(d1) - 1.0
                
        except Exception as e:
            logger.error(f"Error calculating delta: {e}")
            return 0.0
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate option gamma"""
        try:
            if T <= 0:
                return 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            return gamma
            
        except Exception as e:
            logger.error(f"Error calculating gamma: {e}")
            return 0.0
    
    def calculate_theta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate option theta (time decay)"""
        try:
            if T <= 0:
                return 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type.upper() == 'CALL':
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                        - r * K * np.exp(-r * T) * norm.cdf(d2))
            else:
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                        + r * K * np.exp(-r * T) * norm.cdf(-d2))
            
            return theta / 365  # Convert to daily theta
            
        except Exception as e:
            logger.error(f"Error calculating theta: {e}")
            return 0.0
    
    def calculate_vega(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate option vega"""
        try:
            if T <= 0:
                return 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T)
            return vega / 100  # Convert to 1% volatility change
            
        except Exception as e:
            logger.error(f"Error calculating vega: {e}")
            return 0.0
    
    def calculate_rho(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate option rho"""
        try:
            if T <= 0:
                return 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type.upper() == 'CALL':
                rho = K * T * np.exp(-r * T) * norm.cdf(d2)
            else:
                rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
            
            return rho / 100  # Convert to 1% interest rate change
            
        except Exception as e:
            logger.error(f"Error calculating rho: {e}")
            return 0.0
    
    def calculate_all_greeks(self, S: float, K: float, T: float, sigma: float, option_type: str) -> Dict[str, float]:
        """Calculate all Greeks for an option"""
        try:
            r = self.risk_free_rate
            
            # Calculate option price
            if option_type.upper() == 'CALL':
                price = self.black_scholes_call(S, K, T, r, sigma)
            else:
                price = self.black_scholes_put(S, K, T, r, sigma)
            
            # Calculate all Greeks
            greeks = {
                'price': price,
                'delta': self.calculate_delta(S, K, T, r, sigma, option_type),
                'gamma': self.calculate_gamma(S, K, T, r, sigma),
                'theta': self.calculate_theta(S, K, T, r, sigma, option_type),
                'vega': self.calculate_vega(S, K, T, r, sigma),
                'rho': self.calculate_rho(S, K, T, r, sigma, option_type)
            }
            
            return greeks
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {
                'price': 0.0, 'delta': 0.0, 'gamma': 0.0,
                'theta': 0.0, 'vega': 0.0, 'rho': 0.0
            }
    
    def calculate_implied_volatility(self, market_price: float, S: float, K: float, T: float, option_type: str) -> float:
        """Calculate implied volatility using Newton-Raphson method"""
        try:
            if T <= 0:
                return 0.0
            
            # Initial guess
            sigma = 0.2
            tolerance = 1e-6
            max_iterations = 100
            
            for i in range(max_iterations):
                if option_type.upper() == 'CALL':
                    price = self.black_scholes_call(S, K, T, self.risk_free_rate, sigma)
                else:
                    price = self.black_scholes_put(S, K, T, self.risk_free_rate, sigma)
                
                vega = self.calculate_vega(S, K, T, self.risk_free_rate, sigma)
                
                if abs(vega) < 1e-10:
                    break
                
                price_diff = price - market_price
                
                if abs(price_diff) < tolerance:
                    return sigma
                
                sigma = sigma - price_diff / (vega * 100)  # vega is per 1% change
                
                # Keep sigma positive and reasonable
                sigma = max(0.01, min(5.0, sigma))
            
            return sigma
            
        except Exception as e:
            logger.error(f"Error calculating implied volatility: {e}")
            return 0.2  # Default volatility
    
    def calculate_portfolio_greeks(self, positions: List[Dict]) -> Dict[str, float]:
        """Calculate portfolio-level Greeks"""
        try:
            portfolio_greeks = {
                'delta': 0.0, 'gamma': 0.0, 'theta': 0.0,
                'vega': 0.0, 'rho': 0.0, 'net_premium': 0.0
            }
            
            for position in positions:
                quantity = position.get('quantity', 0)
                greeks = position.get('greeks', {})
                
                # Aggregate Greeks (considering position size and direction)
                portfolio_greeks['delta'] += quantity * greeks.get('delta', 0)
                portfolio_greeks['gamma'] += quantity * greeks.get('gamma', 0)
                portfolio_greeks['theta'] += quantity * greeks.get('theta', 0)
                portfolio_greeks['vega'] += quantity * greeks.get('vega', 0)
                portfolio_greeks['rho'] += quantity * greeks.get('rho', 0)
                portfolio_greeks['net_premium'] += quantity * greeks.get('price', 0)
            
            return portfolio_greeks
            
        except Exception as e:
            logger.error(f"Error calculating portfolio Greeks: {e}")
            return {
                'delta': 0.0, 'gamma': 0.0, 'theta': 0.0,
                'vega': 0.0, 'rho': 0.0, 'net_premium': 0.0
            }
    
    def calculate_time_to_expiry(self, expiry_date: str) -> float:
        """Calculate time to expiry in years"""
        try:
            from datetime import datetime
            
            if isinstance(expiry_date, str):
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            else:
                expiry = expiry_date
            
            now = datetime.now()
            time_diff = expiry - now
            
            # Convert to years
            time_to_expiry = time_diff.total_seconds() / (365.25 * 24 * 3600)
            return max(0, time_to_expiry)
            
        except Exception as e:
            logger.error(f"Error calculating time to expiry: {e}")
            return 0.0