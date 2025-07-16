"""
Market Data Handler for NSE/BSE Options Data
Handles real-time and historical data fetching, option chain analysis
"""

import pandas as pd
import numpy as np
import yfinance as yf
from nsepy import get_history, get_expiry_date
from nsepy.derivatives import get_expiry_date as get_option_expiry
import requests
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NSEDataProvider:
    """NSE Data Provider for real-time and historical data"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
    def get_nifty_data(self, days: int = 30) -> pd.DataFrame:
        """Get historical NIFTY data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Using yfinance for NIFTY data
            nifty = yf.Ticker("^NSEI")
            data = nifty.history(start=start_date, end=end_date)
            
            if data.empty:
                # Fallback to nsepy
                data = get_history(symbol="NIFTY", start=start_date, end=end_date, index=True)
                
            return data
        except Exception as e:
            logger.error(f"Error fetching NIFTY data: {e}")
            return pd.DataFrame()
    
    def get_option_chain(self, symbol: str = "NIFTY") -> Dict:
        """Get current option chain data"""
        try:
            url = f"{self.base_url}/option-chain-indices?symbol={symbol}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch option chain: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return {}
    
    def get_option_historical_data(self, symbol: str, strike: float, 
                                 option_type: str, expiry: str, days: int = 30) -> pd.DataFrame:
        """Get historical option data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = get_history(
                symbol=symbol,
                start=start_date,
                end=end_date,
                option_type=option_type.upper(),
                strike_price=strike,
                expiry_date=datetime.strptime(expiry, "%Y-%m-%d")
            )
            
            return data
        except Exception as e:
            logger.error(f"Error fetching option historical data: {e}")
            return pd.DataFrame()


class OptionChainAnalyzer:
    """Analyzes option chain data for trading signals"""
    
    def __init__(self, data_provider: NSEDataProvider):
        self.data_provider = data_provider
        
    def analyze_option_chain(self, symbol: str = "NIFTY") -> Dict:
        """Comprehensive option chain analysis"""
        chain_data = self.data_provider.get_option_chain(symbol)
        
        if not chain_data:
            return {}
            
        try:
            records = chain_data.get('records', {})
            data = records.get('data', [])
            
            analysis = {
                'timestamp': datetime.now(),
                'underlying_price': records.get('underlyingValue', 0),
                'pcr': self._calculate_pcr(data),
                'max_pain': self._calculate_max_pain(data),
                'support_resistance': self._find_support_resistance(data),
                'volatility_skew': self._calculate_volatility_skew(data),
                'gamma_levels': self._find_gamma_levels(data),
                'directional_bias': self._determine_directional_bias(data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing option chain: {e}")
            return {}
    
    def _calculate_pcr(self, data: List[Dict]) -> float:
        """Calculate Put-Call Ratio"""
        total_put_oi = 0
        total_call_oi = 0
        
        for item in data:
            if 'PE' in item:
                total_put_oi += item['PE'].get('openInterest', 0)
            if 'CE' in item:
                total_call_oi += item['CE'].get('openInterest', 0)
                
        return total_put_oi / total_call_oi if total_call_oi > 0 else 0
    
    def _calculate_max_pain(self, data: List[Dict]) -> float:
        """Calculate Max Pain level"""
        pain_levels = {}
        
        for item in data:
            strike = item.get('strikePrice', 0)
            
            # Calculate pain for this strike
            total_pain = 0
            
            for other_item in data:
                other_strike = other_item.get('strikePrice', 0)
                
                if 'CE' in other_item and other_strike > strike:
                    ce_oi = other_item['CE'].get('openInterest', 0)
                    total_pain += (other_strike - strike) * ce_oi
                    
                if 'PE' in other_item and other_strike < strike:
                    pe_oi = other_item['PE'].get('openInterest', 0)
                    total_pain += (strike - other_strike) * pe_oi
                    
            pain_levels[strike] = total_pain
            
        return min(pain_levels, key=pain_levels.get) if pain_levels else 0
    
    def _find_support_resistance(self, data: List[Dict]) -> Dict:
        """Find key support and resistance levels"""
        levels = []
        
        for item in data:
            strike = item.get('strikePrice', 0)
            total_oi = 0
            
            if 'CE' in item:
                total_oi += item['CE'].get('openInterest', 0)
            if 'PE' in item:
                total_oi += item['PE'].get('openInterest', 0)
                
            levels.append({'strike': strike, 'oi': total_oi})
        
        # Sort by OI and get top levels
        levels.sort(key=lambda x: x['oi'], reverse=True)
        top_levels = levels[:5]
        
        return {
            'key_levels': [level['strike'] for level in top_levels],
            'strongest_level': top_levels[0]['strike'] if top_levels else 0
        }
    
    def _calculate_volatility_skew(self, data: List[Dict]) -> Dict:
        """Calculate volatility skew"""
        ce_ivs = []
        pe_ivs = []
        strikes = []
        
        for item in data:
            strike = item.get('strikePrice', 0)
            strikes.append(strike)
            
            if 'CE' in item:
                ce_iv = item['CE'].get('impliedVolatility', 0)
                ce_ivs.append(ce_iv)
            else:
                ce_ivs.append(0)
                
            if 'PE' in item:
                pe_iv = item['PE'].get('impliedVolatility', 0)
                pe_ivs.append(pe_iv)
            else:
                pe_ivs.append(0)
        
        return {
            'ce_skew': np.std(ce_ivs) if ce_ivs else 0,
            'pe_skew': np.std(pe_ivs) if pe_ivs else 0,
            'skew_direction': 'put' if np.mean(pe_ivs) > np.mean(ce_ivs) else 'call'
        }
    
    def _find_gamma_levels(self, data: List[Dict]) -> List[float]:
        """Find high gamma levels"""
        gamma_levels = []
        
        for item in data:
            strike = item.get('strikePrice', 0)
            total_gamma = 0
            
            if 'CE' in item:
                ce_gamma = item['CE'].get('gamma', 0)
                ce_oi = item['CE'].get('openInterest', 0)
                total_gamma += ce_gamma * ce_oi
                
            if 'PE' in item:
                pe_gamma = item['PE'].get('gamma', 0)
                pe_oi = item['PE'].get('openInterest', 0)
                total_gamma += pe_gamma * pe_oi
                
            gamma_levels.append({'strike': strike, 'gamma': total_gamma})
        
        # Sort by gamma and return top levels
        gamma_levels.sort(key=lambda x: abs(x['gamma']), reverse=True)
        return [level['strike'] for level in gamma_levels[:3]]
    
    def _determine_directional_bias(self, data: List[Dict]) -> str:
        """Determine market directional bias"""
        call_volume = 0
        put_volume = 0
        call_oi_change = 0
        put_oi_change = 0
        
        for item in data:
            if 'CE' in item:
                call_volume += item['CE'].get('totalTradedVolume', 0)
                call_oi_change += item['CE'].get('changeinOpenInterest', 0)
                
            if 'PE' in item:
                put_volume += item['PE'].get('totalTradedVolume', 0)
                put_oi_change += item['PE'].get('changeinOpenInterest', 0)
        
        # Determine bias based on volume and OI changes
        volume_bias = 'bullish' if call_volume > put_volume else 'bearish'
        oi_bias = 'bullish' if call_oi_change > put_oi_change else 'bearish'
        
        if volume_bias == oi_bias:
            return volume_bias
        else:
            return 'neutral'


class MarketDataManager:
    """Main class for managing all market data operations"""
    
    def __init__(self):
        self.nse_provider = NSEDataProvider()
        self.option_analyzer = OptionChainAnalyzer(self.nse_provider)
        self.cache = {}
        self.cache_timeout = 60  # seconds
        
    def get_real_time_data(self, symbol: str = "NIFTY") -> Dict:
        """Get comprehensive real-time market data"""
        cache_key = f"realtime_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return cached_data
        
        # Fetch fresh data
        data = {
            'nifty_data': self.nse_provider.get_nifty_data(days=1),
            'option_analysis': self.option_analyzer.analyze_option_chain(symbol),
            'timestamp': datetime.now()
        }
        
        # Cache the data
        self.cache[cache_key] = (data, time.time())
        
        return data
    
    def get_historical_analysis(self, symbol: str = "NIFTY", days: int = 30) -> Dict:
        """Get historical market analysis"""
        nifty_data = self.nse_provider.get_nifty_data(days)
        
        if nifty_data.empty:
            return {}
            
        analysis = {
            'price_data': nifty_data,
            'volatility': self._calculate_historical_volatility(nifty_data),
            'trend_analysis': self._analyze_trend(nifty_data),
            'support_resistance_historical': self._find_historical_levels(nifty_data)
        }
        
        return analysis
    
    def _calculate_historical_volatility(self, data: pd.DataFrame) -> float:
        """Calculate historical volatility"""
        if len(data) < 2:
            return 0
            
        returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()
        return returns.std() * np.sqrt(252)  # Annualized volatility
    
    def _analyze_trend(self, data: pd.DataFrame) -> Dict:
        """Analyze price trend"""
        if len(data) < 20:
            return {'trend': 'insufficient_data'}
            
        # Simple moving averages
        data['SMA_5'] = data['Close'].rolling(5).mean()
        data['SMA_20'] = data['Close'].rolling(20).mean()
        
        current_price = data['Close'].iloc[-1]
        sma_5 = data['SMA_5'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        
        if current_price > sma_5 > sma_20:
            trend = 'strong_bullish'
        elif current_price > sma_20:
            trend = 'bullish'
        elif current_price < sma_5 < sma_20:
            trend = 'strong_bearish'
        elif current_price < sma_20:
            trend = 'bearish'
        else:
            trend = 'sideways'
            
        return {
            'trend': trend,
            'current_price': current_price,
            'sma_5': sma_5,
            'sma_20': sma_20
        }
    
    def _find_historical_levels(self, data: pd.DataFrame) -> Dict:
        """Find historical support and resistance levels"""
        highs = data['High'].rolling(window=5).max()
        lows = data['Low'].rolling(window=5).min()
        
        resistance_levels = highs[highs == highs.rolling(window=10, center=True).max()].dropna()
        support_levels = lows[lows == lows.rolling(window=10, center=True).min()].dropna()
        
        return {
            'resistance_levels': resistance_levels.tolist()[-5:],  # Last 5 levels
            'support_levels': support_levels.tolist()[-5:]
        }