import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from bot.orders import execute_trade
from bot.huggingface_client import MarketSentimentAnalyzer, HFAnalyzerError
from bot.client import BinanceClientError
from bot.logging_config import logger

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Binance AI Trading Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #f0b90b;
        color: black;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #d4a008;
        color: black;
    }
    .sentiment-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #1e2130;
        border-left: 5px solid #f0b90b;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e8/Binance_Logo.png", width=200)
    st.title("Settings")
    
    api_status = "✅ Connected" if os.getenv("BINANCE_API_KEY") else "❌ Missing Keys"
    hf_status = "✅ Connected" if os.getenv("HUGGINGFACE_API_KEY") else "⚠️ AI Disabled"
    
    st.info(f"Binance API: {api_status}")
    st.info(f"HF Inference: {hf_status}")
    
    st.divider()
    st.markdown("### Bot Status")
    st.success("System: Online")

# Main Dashboard
st.title("🤖 Agentic Trading Dashboard")
st.markdown("---")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📊 Place Order")
    with st.container(border=True):
        symbol = st.text_input("Trading Symbol", value="BTCUSDT").upper()
        side = st.selectbox("Order Side", ["BUY", "SELL"])
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
        
        q_col, p_col = st.columns(2)
        with q_col:
            quantity = st.number_input("Quantity", min_value=0.0001, format="%.4f", step=0.001)
        with p_col:
            price = st.number_input("Price", min_value=0.0, format="%.2f", disabled=(order_type == "MARKET"))

        if st.button("🚀 Execute Trade"):
            try:
                # Basic validation for price
                exec_price = price if order_type == "LIMIT" else None
                
                with st.spinner("Executing trade on Binance Testnet..."):
                    response = execute_trade(symbol, side, order_type, quantity, exec_price)
                
                st.success(f"Order Successful! ID: {response.get('orderId')}")
                st.json(response)
            except Exception as e:
                st.error(f"Execution Failed: {e}")

with col2:
    st.subheader("🧠 AI Agent Sentiment")
    with st.container(border=True):
        news_input = st.text_area("Paste News Headline or Market Context", 
                                 placeholder="e.g., Bitcoin breaks $90k resistance as ETF inflows accelerate...")
        
        if st.button("🔍 Analyze Sentiment"):
            if not news_input:
                st.warning("Please enter some text to analyze.")
            else:
                analyzer = MarketSentimentAnalyzer()
                try:
                    with st.spinner("Agent thinking..."):
                        result = analyzer.analyze_sentiment(news_input)
                    
                    sentiment = result['sentiment'].upper()
                    signal = result['signal']
                    conf = result['confidence']
                    
                    # Layout for results
                    s_col1, s_col2 = st.columns(2)
                    
                    color = "#2ecc71" if signal == "BUY" else "#e74c3c" if signal == "SELL" else "#f1c40f"
                    
                    with s_col1:
                        st.metric("Sentiment", sentiment)
                    with s_col2:
                        st.metric("Confidence", f"{conf:.1%}")
                    
                    st.markdown(f"""
                        <div class='sentiment-box'>
                            <h3 style='color:{color}; margin:0;'>Signal: {signal}</h3>
                            <p style='margin-top:10px;'><b>Consensus Reasoning:</b> {result['reasoning']}</p>
                            <hr style='margin:10px 0; border:0.5px solid #444;'>
                            <p style='font-size:0.8em; color:#bbb;'><b>Multi-Agent Breakdown:</b><br>{result['agent_details']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if signal != "HOLD":
                        if st.button(f"⚡ Follow AI Signal: {signal} {symbol}"):
                            try:
                                with st.spinner(f"Agent executing {signal}..."):
                                    res = execute_trade(symbol, signal, "MARKET", quantity, None)
                                st.success("Agent Trade Executed!")
                                st.json(res)
                            except Exception as e:
                                st.error(f"Trade failed: {e}")
                                
                except HFAnalyzerError as e:
                    st.error(f"AI Error: {e}")

st.markdown("---")
st.subheader("📜 System Logs (Recent)")
try:
    if os.path.exists("logs/trading_bot.log"):
        with open("logs/trading_bot.log", "r") as f:
            lines = f.readlines()
            st.code("".join(lines[-20:]), language="text")
    else:
        st.info("No logs found yet.")
except Exception:
    st.error("Could not read log file.")
