import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Stock Copilot AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #464b5d;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Constants ---
POPULAR_STOCKS = {
    "Apple": "AAPL",
    "Google": "GOOGL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Meta": "META",
    "NVIDIA": "NVDA",
    "Netflix": "NFLX",
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Zomato": "ZOMATO.NS",
    "Paytm": "PAYTM.NS"
}

# --- Sidebar ---
with st.sidebar:
    st.title("🤖 Stock Copilot")
    
    # Load API Key from Environment
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Google API Key not found. Please set it in the .env file.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    st.markdown("---")
    st.subheader("Select Stock")
    
    search_mode = st.radio("Search Mode", ["Popular Stocks", "Custom Search"])
    
    if search_mode == "Popular Stocks":
        selected_company = st.selectbox("Choose a Company", list(POPULAR_STOCKS.keys()))
        ticker = POPULAR_STOCKS[selected_company]
    else:
        user_input = st.text_input("Enter Symbol or Name", value="AAPL").strip()
        # Simple name resolution
        ticker = POPULAR_STOCKS.get(user_input, user_input.upper())
    
    period = st.selectbox(
        "Time Period",
        options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'],
        index=2
    )
    
    # Chat Reset Logic
    if "last_ticker" not in st.session_state:
        st.session_state.last_ticker = None
        
    if ticker != st.session_state.last_ticker:
        st.session_state.messages = []
        st.session_state.last_ticker = ticker
    
    st.markdown("---")
    st.info("💡 **Tip:** Ask the Copilot about trends, comparisons, or financial health!")

# --- Helper Functions ---
def get_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return stock, hist
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None

def get_ai_insight(prompt, context_data):
    try:
        # Use gemini-1.5-flash for speed, fallback to pro if needed
        model = genai.GenerativeModel('gemini-2.5-flash')
        full_prompt = f"""
        You are an expert financial analyst and stock market copilot.
        
        Context Data:
        {context_data}
        
        User Question:
        {prompt}
        
        Provide a concise, professional, and data-driven answer. Use bullet points where appropriate.
        """
        response = model.generate_content(full_prompt)
        if response.parts:
            return response.text
        else:
            return "⚠️ The AI could not generate a response. This might be due to safety filters or an API issue."
    except Exception as e:
        return f"Error generating insight: {e}"

# --- Main Content ---
if ticker:
    stock, hist = get_stock_data(ticker, period)
    
    if stock and not hist.empty:
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"{stock.info.get('longName', ticker)} ({ticker})")
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            delta = current_price - previous_close
            delta_percent = (delta / previous_close) * 100
            
            st.metric(
                label="Current Price",
                value=f"${current_price:.2f}",
                delta=f"{delta:.2f} ({delta_percent:.2f}%)"
            )
        
        with col2:
            logo_url = stock.info.get('logo_url')
            if logo_url:
                st.image(logo_url, width=100)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Chart", "📊 Financials", "ℹ️ Overview", "💬 AI Copilot"])

        with tab1:
            # Interactive Plotly Chart
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'])])
            fig.update_layout(
                title=f'{ticker} Stock Price ({period})',
                yaxis_title='Price',
                xaxis_title='Date',
                template='plotly_dark',
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume Chart
            st.subheader("Trading Volume")
            st.bar_chart(hist['Volume'])

        with tab2:
            st.subheader("Key Financial Metrics")
            info = stock.info
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
                st.markdown(f"**PE Ratio:** {info.get('trailingPE', 'N/A')}")
                st.markdown(f"**EPS:** {info.get('trailingEps', 'N/A')}")
            with m_col2:
                st.markdown(f"**52 Week High:** {info.get('fiftyTwoWeekHigh', 'N/A')}")
                st.markdown(f"**52 Week Low:** {info.get('fiftyTwoWeekLow', 'N/A')}")
                st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")
            with m_col3:
                st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
                st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
                st.markdown(f"**Beta:** {info.get('beta', 'N/A')}")

            st.subheader("Income Statement (Annual)")
            st.dataframe(stock.income_stmt)

        with tab3:
            st.subheader("Company Summary")
            st.write(stock.info.get('longBusinessSummary', 'No summary available.'))

        with tab4:
            st.header("💬 Chat with Stock Copilot")
            
            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # React to user input
            if prompt := st.chat_input(f"Ask about {ticker}..."):
                # Display user message in chat message container
                st.chat_message("user").markdown(prompt)
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Prepare context for AI
                context = f"""
                Stock: {ticker}
                Current Price: {current_price}
                PE Ratio: {stock.info.get('trailingPE', 'N/A')}
                Market Cap: {stock.info.get('marketCap', 'N/A')}
                Business Summary: {stock.info.get('longBusinessSummary', '')[:500]}...
                Recent History (Last 5 points): {hist.tail().to_string()}
                """
                
                with st.spinner("Thinking..."):
                    response = get_ai_insight(prompt, context)
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error("Could not load stock data. Please check the ticker symbol.")
else:
    st.info("Please enter a stock ticker in the sidebar to get started.")
