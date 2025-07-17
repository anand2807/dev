"""
Real-time Trading Dashboard
Streamlit-based dashboard for monitoring portfolio and trading signals
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json
import logging

from ..portfolio.portfolio_manager import PortfolioManager
from ..strategies.volatility_strategies import DirectionalVolatilityStrategy, RiskManager
from ..data.market_data import MarketDataManager
from ..utils.greeks import GreeksCalculator
from ..backtesting.backtest_engine import BacktestEngine, run_quick_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingDashboard:
    """Main trading dashboard class"""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_components()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'portfolio_manager' not in st.session_state:
            st.session_state.portfolio_manager = None
        if 'strategy' not in st.session_state:
            st.session_state.strategy = None
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'initial_capital' not in st.session_state:
            st.session_state.initial_capital = 100000
    
    def setup_components(self):
        """Setup trading components"""
        try:
            # Initialize components
            market_data_manager = MarketDataManager()
            greeks_calculator = GreeksCalculator()
            risk_manager = RiskManager()
            
            # Initialize strategy
            strategy = DirectionalVolatilityStrategy(
                market_data_manager, 
                greeks_calculator
            )
            
            # Initialize portfolio manager
            portfolio_manager = PortfolioManager(
                st.session_state.initial_capital,
                market_data_manager,
                greeks_calculator,
                risk_manager
            )
            
            st.session_state.portfolio_manager = portfolio_manager
            st.session_state.strategy = strategy
            st.session_state.market_data_manager = market_data_manager
            
        except Exception as e:
            st.error(f"Error setting up components: {e}")
            logger.error(f"Error setting up components: {e}")
    
    def run(self):
        """Main dashboard function"""
        st.set_page_config(
            page_title="Renaissance Options Trading Dashboard",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .profit {
            color: #00ff00;
        }
        .loss {
            color: #ff0000;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.title("🏛️ Renaissance Options Trading System")
        st.markdown("*Sophisticated volatility-based options trading for Indian markets*")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        if st.session_state.portfolio_manager is None:
            st.error("Portfolio manager not initialized. Please check the setup.")
            return
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time.sleep(5)
            st.rerun()
        
        # Main dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Portfolio Overview", 
            "🎯 Trading Signals", 
            "📈 Market Analysis", 
            "🔄 Backtesting", 
            "⚙️ Settings"
        ])
        
        with tab1:
            self.render_portfolio_overview()
        
        with tab2:
            self.render_trading_signals()
        
        with tab3:
            self.render_market_analysis()
        
        with tab4:
            self.render_backtesting()
        
        with tab5:
            self.render_settings()
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        st.sidebar.header("🎛️ Controls")
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.sidebar.checkbox(
            "Auto Refresh (5s)", 
            value=st.session_state.auto_refresh
        )
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now"):
            st.session_state.last_update = datetime.now()
            st.rerun()
        
        # Portfolio actions
        st.sidebar.subheader("📋 Portfolio Actions")
        
        if st.sidebar.button("📊 Update Positions"):
            if st.session_state.portfolio_manager:
                st.session_state.portfolio_manager.update_positions()
                st.sidebar.success("Positions updated!")
        
        if st.sidebar.button("🚨 Close All Positions"):
            if st.session_state.portfolio_manager:
                st.session_state.portfolio_manager.close_all_positions("manual_close")
                st.sidebar.success("All positions closed!")
        
        # Risk controls
        st.sidebar.subheader("⚠️ Risk Controls")
        
        if st.sidebar.button("🔍 Check Risk Limits"):
            if st.session_state.portfolio_manager:
                risk_status = st.session_state.portfolio_manager.check_risk_limits()
                if risk_status['any_limit_exceeded']:
                    st.sidebar.error("⚠️ Risk limits exceeded!")
                else:
                    st.sidebar.success("✅ All risk limits OK")
        
        # Last update time
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    def render_portfolio_overview(self):
        """Render portfolio overview tab"""
        st.header("📊 Portfolio Overview")
        
        if not st.session_state.portfolio_manager:
            st.error("Portfolio manager not available")
            return
        
        # Get portfolio summary
        portfolio_summary = st.session_state.portfolio_manager.get_portfolio_summary()
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            portfolio_value = portfolio_summary['portfolio_value']
            st.metric(
                "Portfolio Value", 
                f"₹{portfolio_value:,.2f}",
                delta=f"₹{portfolio_summary['total_pnl']:,.2f}"
            )
        
        with col2:
            total_return = portfolio_summary['total_return']
            st.metric(
                "Total Return", 
                f"{total_return:.2%}",
                delta=f"{total_return:.2%}"
            )
        
        with col3:
            st.metric(
                "Cash Balance", 
                f"₹{portfolio_summary['cash_balance']:,.2f}"
            )
        
        with col4:
            st.metric(
                "Open Positions", 
                portfolio_summary['num_positions']
            )
        
        # Portfolio Greeks
        st.subheader("🔢 Portfolio Greeks")
        
        portfolio_greeks = portfolio_summary.get('portfolio_greeks', {})
        
        if portfolio_greeks:
            greek_col1, greek_col2, greek_col3, greek_col4 = st.columns(4)
            
            with greek_col1:
                delta = portfolio_greeks.get('total_delta', 0)
                st.metric("Delta", f"{delta:.2f}")
            
            with greek_col2:
                gamma = portfolio_greeks.get('total_gamma', 0)
                st.metric("Gamma", f"{gamma:.2f}")
            
            with greek_col3:
                theta = portfolio_greeks.get('total_theta', 0)
                st.metric("Theta", f"{theta:.2f}")
            
            with greek_col4:
                vega = portfolio_greeks.get('total_vega', 0)
                st.metric("Vega", f"{vega:.2f}")
        
        # Current positions
        st.subheader("📋 Current Positions")
        
        positions = portfolio_summary.get('positions', [])
        
        if positions:
            positions_df = pd.DataFrame(positions)
            
            # Format the dataframe for display
            display_df = positions_df[['option_type', 'strike', 'expiry', 'quantity', 
                                     'entry_price', 'current_price', 'pnl']].copy()
            
            display_df['pnl_color'] = display_df['pnl'].apply(
                lambda x: 'profit' if x > 0 else 'loss'
            )
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # P&L chart
            if len(positions_df) > 0:
                fig = px.bar(
                    positions_df, 
                    x='strike', 
                    y='pnl',
                    color='pnl',
                    color_continuous_scale=['red', 'green'],
                    title="Position P&L by Strike"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No open positions")
        
        # Recent trades
        st.subheader("📈 Recent Trades")
        
        recent_trades = portfolio_summary.get('recent_trades', [])
        
        if recent_trades:
            trades_df = pd.DataFrame(recent_trades)
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("No recent trades")
        
        # Performance report
        st.subheader("📊 Performance Report")
        
        perf_report = st.session_state.portfolio_manager.generate_performance_report()
        
        if 'message' not in perf_report:
            perf_col1, perf_col2, perf_col3 = st.columns(3)
            
            with perf_col1:
                st.metric("Win Rate", f"{perf_report['win_rate']:.2%}")
                st.metric("Total Trades", perf_report['total_trades'])
            
            with perf_col2:
                st.metric("Profit Factor", f"{perf_report['profit_factor']:.2f}")
                st.metric("Sharpe Ratio", f"{perf_report['sharpe_ratio']:.2f}")
            
            with perf_col3:
                st.metric("Max Drawdown", f"{perf_report['max_drawdown']:.2%}")
                st.metric("Avg Win", f"₹{perf_report['avg_win']:,.2f}")
        else:
            st.info(perf_report['message'])
    
    def render_trading_signals(self):
        """Render trading signals tab"""
        st.header("🎯 Trading Signals")
        
        if not st.session_state.strategy:
            st.error("Strategy not available")
            return
        
        # Generate signals button
        if st.button("🔍 Generate New Signals"):
            with st.spinner("Analyzing market and generating signals..."):
                signals = st.session_state.strategy.generate_trading_signals()
                st.session_state.current_signals = signals
        
        # Display current signals
        if hasattr(st.session_state, 'current_signals'):
            signals = st.session_state.current_signals
            
            if signals:
                st.subheader(f"📡 Current Signals ({len(signals)} found)")
                
                for i, signal in enumerate(signals):
                    with st.expander(f"Signal {i+1}: {signal.strategy} - {signal.option_type} {signal.strike}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Strategy:** {signal.strategy}")
                            st.write(f"**Action:** {signal.action}")
                            st.write(f"**Option Type:** {signal.option_type}")
                            st.write(f"**Strike:** {signal.strike}")
                            st.write(f"**Expiry:** {signal.expiry}")
                            st.write(f"**Quantity:** {signal.quantity}")
                        
                        with col2:
                            st.write(f"**Confidence:** {signal.confidence:.1%}")
                            st.write(f"**Expected Profit:** ₹{signal.expected_profit:,.2f}")
                            st.write(f"**Max Loss:** ₹{signal.max_loss:,.2f}")
                            st.write(f"**Risk/Reward:** {signal.expected_profit/signal.max_loss:.2f}")
                        
                        st.write(f"**Reasoning:** {signal.reasoning}")
                        
                        # Execute signal button
                        if st.button(f"Execute Signal {i+1}", key=f"execute_{i}"):
                            order_id = st.session_state.portfolio_manager.process_signal(signal)
                            if order_id:
                                st.success(f"Signal executed! Order ID: {order_id}")
                            else:
                                st.error("Failed to execute signal")
            else:
                st.info("No signals generated. Market conditions may not be favorable.")
        else:
            st.info("Click 'Generate New Signals' to analyze current market conditions")
        
        # Market regime analysis
        st.subheader("🌡️ Market Regime Analysis")
        
        if st.button("📊 Analyze Market Regime"):
            with st.spinner("Analyzing market regime..."):
                market_regime = st.session_state.strategy.analyze_market_regime()
                
                regime_col1, regime_col2 = st.columns(2)
                
                with regime_col1:
                    st.write(f"**Volatility Regime:** {market_regime['volatility_regime'].value}")
                    st.write(f"**Market Direction:** {market_regime['market_direction'].value}")
                    st.write(f"**Current Volatility:** {market_regime['current_volatility']:.2%}")
                    st.write(f"**PCR:** {market_regime['pcr']:.2f}")
                
                with regime_col2:
                    st.write(f"**Underlying Price:** ₹{market_regime['underlying_price']:,.2f}")
                    st.write(f"**Max Pain:** ₹{market_regime['max_pain']:,.2f}")
                    
                    chain_patterns = market_regime['chain_patterns']
                    st.write("**Chain Patterns:**")
                    for pattern, value in chain_patterns.items():
                        st.write(f"  - {pattern}: {value}")
    
    def render_market_analysis(self):
        """Render market analysis tab"""
        st.header("📈 Market Analysis")
        
        if not hasattr(st.session_state, 'market_data_manager'):
            st.error("Market data manager not available")
            return
        
        # Real-time data
        st.subheader("📊 Real-time Market Data")
        
        if st.button("🔄 Refresh Market Data"):
            with st.spinner("Fetching market data..."):
                real_time_data = st.session_state.market_data_manager.get_real_time_data()
                st.session_state.real_time_data = real_time_data
        
        if hasattr(st.session_state, 'real_time_data'):
            data = st.session_state.real_time_data
            option_analysis = data.get('option_analysis', {})
            
            # Key market metrics
            market_col1, market_col2, market_col3 = st.columns(3)
            
            with market_col1:
                underlying_price = option_analysis.get('underlying_price', 0)
                st.metric("NIFTY Price", f"₹{underlying_price:,.2f}")
            
            with market_col2:
                pcr = option_analysis.get('pcr', 0)
                st.metric("Put-Call Ratio", f"{pcr:.2f}")
            
            with market_col3:
                max_pain = option_analysis.get('max_pain', 0)
                st.metric("Max Pain", f"₹{max_pain:,.2f}")
            
            # Support and resistance levels
            sr_levels = option_analysis.get('support_resistance', {})
            key_levels = sr_levels.get('key_levels', [])
            
            if key_levels:
                st.subheader("🎯 Key Levels")
                
                # Create a chart showing key levels
                fig = go.Figure()
                
                # Add current price line
                fig.add_hline(
                    y=underlying_price, 
                    line_dash="dash", 
                    line_color="blue",
                    annotation_text="Current Price"
                )
                
                # Add key levels
                for level in key_levels:
                    fig.add_hline(
                        y=level, 
                        line_dash="dot", 
                        line_color="red" if level > underlying_price else "green",
                        annotation_text=f"₹{level:,.0f}"
                    )
                
                fig.update_layout(
                    title="Key Support and Resistance Levels",
                    yaxis_title="Price (₹)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Historical analysis
        st.subheader("📊 Historical Analysis")
        
        days = st.slider("Analysis Period (days)", 7, 90, 30)
        
        if st.button("📈 Generate Historical Analysis"):
            with st.spinner("Analyzing historical data..."):
                historical_data = st.session_state.market_data_manager.get_historical_analysis(days=days)
                
                if historical_data:
                    price_data = historical_data.get('price_data')
                    
                    if price_data is not None and not price_data.empty:
                        # Price chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=price_data.index,
                            y=price_data['Close'],
                            mode='lines',
                            name='NIFTY Close',
                            line=dict(color='blue')
                        ))
                        
                        fig.update_layout(
                            title=f"NIFTY Price - Last {days} Days",
                            xaxis_title="Date",
                            yaxis_title="Price (₹)",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Volatility and trend info
                        vol_col1, vol_col2 = st.columns(2)
                        
                        with vol_col1:
                            volatility = historical_data.get('volatility', 0)
                            st.metric("Historical Volatility", f"{volatility:.2%}")
                        
                        with vol_col2:
                            trend_analysis = historical_data.get('trend_analysis', {})
                            trend = trend_analysis.get('trend', 'unknown')
                            st.metric("Trend", trend.replace('_', ' ').title())
                else:
                    st.error("Failed to fetch historical data")
    
    def render_backtesting(self):
        """Render backtesting tab"""
        st.header("🔄 Strategy Backtesting")
        
        # Backtest parameters
        st.subheader("⚙️ Backtest Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date", 
                value=datetime.now() - timedelta(days=90)
            )
            initial_capital = st.number_input(
                "Initial Capital (₹)", 
                value=100000, 
                min_value=10000, 
                step=10000
            )
        
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=datetime.now() - timedelta(days=1)
            )
        
        # Run backtest
        if st.button("🚀 Run Backtest"):
            if start_date >= end_date:
                st.error("Start date must be before end date")
                return
            
            with st.spinner("Running backtest... This may take a few minutes."):
                try:
                    result = run_quick_backtest(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        initial_capital
                    )
                    
                    st.session_state.backtest_result = result
                    
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                    return
        
        # Display results
        if hasattr(st.session_state, 'backtest_result'):
            result = st.session_state.backtest_result
            
            st.subheader("📊 Backtest Results")
            
            # Key metrics
            result_col1, result_col2, result_col3, result_col4 = st.columns(4)
            
            with result_col1:
                st.metric("Total Return", f"{result.total_return:.2%}")
                st.metric("Win Rate", f"{result.win_rate:.2%}")
            
            with result_col2:
                st.metric("Annualized Return", f"{result.annualized_return:.2%}")
                st.metric("Profit Factor", f"{result.profit_factor:.2f}")
            
            with result_col3:
                st.metric("Max Drawdown", f"{result.max_drawdown:.2%}")
                st.metric("Total Trades", result.total_trades)
            
            with result_col4:
                st.metric("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
                st.metric("Best Trade", f"₹{result.best_trade:,.2f}")
            
            # Equity curve
            if result.equity_curve:
                dates = pd.date_range(
                    start=result.start_date, 
                    periods=len(result.equity_curve), 
                    freq='D'
                )
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=result.equity_curve,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='green')
                ))
                
                fig.update_layout(
                    title="Equity Curve",
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value (₹)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Trade analysis
            if result.trade_log:
                st.subheader("📋 Trade Log")
                
                # Convert trade log to DataFrame for display
                trade_df = pd.DataFrame(result.trade_log)
                
                if not trade_df.empty:
                    st.dataframe(trade_df, use_container_width=True)
                else:
                    st.info("No trades executed during backtest period")
    
    def render_settings(self):
        """Render settings tab"""
        st.header("⚙️ System Settings")
        
        # Portfolio settings
        st.subheader("💼 Portfolio Settings")
        
        new_capital = st.number_input(
            "Initial Capital (₹)", 
            value=st.session_state.initial_capital,
            min_value=10000,
            step=10000
        )
        
        if st.button("💰 Reset Portfolio"):
            st.session_state.initial_capital = new_capital
            # Reinitialize portfolio manager
            self.setup_components()
            st.success("Portfolio reset successfully!")
        
        # Strategy parameters
        st.subheader("🎯 Strategy Parameters")
        
        if st.session_state.strategy:
            strategy = st.session_state.strategy
            
            # Volatility threshold
            vol_threshold = st.slider(
                "Volatility Threshold", 
                0.05, 0.30, 
                strategy.volatility_threshold,
                step=0.01
            )
            
            # PCR thresholds
            pcr_bullish = st.slider(
                "PCR Bullish Threshold", 
                0.5, 1.0, 
                strategy.pcr_bullish_threshold,
                step=0.05
            )
            
            pcr_bearish = st.slider(
                "PCR Bearish Threshold", 
                1.0, 2.0, 
                strategy.pcr_bearish_threshold,
                step=0.05
            )
            
            # Time to expiry limits
            min_expiry = st.slider(
                "Min Days to Expiry", 
                1, 30, 
                strategy.min_time_to_expiry
            )
            
            max_expiry = st.slider(
                "Max Days to Expiry", 
                30, 90, 
                strategy.max_time_to_expiry
            )
            
            if st.button("💾 Update Strategy Parameters"):
                strategy.volatility_threshold = vol_threshold
                strategy.pcr_bullish_threshold = pcr_bullish
                strategy.pcr_bearish_threshold = pcr_bearish
                strategy.min_time_to_expiry = min_expiry
                strategy.max_time_to_expiry = max_expiry
                
                st.success("Strategy parameters updated!")
        
        # Risk management settings
        st.subheader("⚠️ Risk Management")
        
        if st.session_state.portfolio_manager:
            pm = st.session_state.portfolio_manager
            
            max_positions = st.slider(
                "Max Positions", 
                5, 50, 
                pm.max_positions
            )
            
            max_daily_loss_pct = st.slider(
                "Max Daily Loss (%)", 
                1, 10, 
                int(pm.max_daily_loss / pm.initial_capital * 100)
            )
            
            if st.button("🛡️ Update Risk Settings"):
                pm.max_positions = max_positions
                pm.max_daily_loss = pm.initial_capital * (max_daily_loss_pct / 100)
                
                st.success("Risk settings updated!")
        
        # System information
        st.subheader("ℹ️ System Information")
        
        st.write(f"**Last Update:** {st.session_state.last_update}")
        st.write(f"**Auto Refresh:** {'Enabled' if st.session_state.auto_refresh else 'Disabled'}")
        
        if st.session_state.portfolio_manager:
            pm = st.session_state.portfolio_manager
            st.write(f"**Open Positions:** {len(pm.positions)}")
            st.write(f"**Cash Balance:** ₹{pm.cash_balance:,.2f}")
        
        # Export/Import settings
        st.subheader("📤 Export/Import")
        
        if st.button("📥 Export Portfolio Data"):
            if st.session_state.portfolio_manager:
                portfolio_data = st.session_state.portfolio_manager.get_portfolio_summary()
                
                # Convert to JSON string
                json_data = json.dumps(portfolio_data, default=str, indent=2)
                
                st.download_button(
                    label="💾 Download Portfolio Data",
                    data=json_data,
                    file_name=f"portfolio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )


def main():
    """Main function to run the dashboard"""
    dashboard = TradingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()