import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from src.advisor_logic import predict_and_advise, run_backtest
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="CryptoPro Terminal",  
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 1. Global Background */
    .stApp {
        background-color: #0E1117;
        font-family: 'Roboto', sans-serif;
    }

    /* 2. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #0b0e11 !important;
        border-right: 1px solid #2b3139;
    }
    
    /* --- FIX: CURSOR POINTER ON SIDEBAR ELEMENTS --- */
    /* Target Selectbox container */
    section[data-testid="stSidebar"] .stSelectbox, 
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    
    /* --- FIX: DROPDOWN MENU DARK MODE --- */
    /* Dropdown ka Dabba (Container) */
    div[data-baseweb="select"] > div {
        background-color: #161B22 !important;
        color: white !important;
        border-color: #30363D !important;
        cursor: pointer !important;
    }
    
    /* Dropdown ki List (Popup Menu) */
    ul[data-baseweb="menu"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
    }
    
    /* List Items (Options) */
    li[data-baseweb="option"] {
        color: #eaecef !important; /* White Text */
        background-color: #161B22 !important; /* Dark BG */
        cursor: pointer !important;
    }
    
    /* Hover Effect on Options (Yellow Background + Black Text) */
    li[data-baseweb="option"]:hover, 
    li[aria-selected="true"] {
        background-color: #fcd535 !important;
        color: #000000 !important;
        font-weight: bold;
    }

    /* Sidebar Text Colors */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span {
        color: #eaecef !important;
    }

    /* 3. METRIC CARDS */
    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 10px;
    }
    .metric-card:hover {
        border-color: #fcd535; 
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(252, 213, 53, 0.2);
        transition: 0.3s;
    }

    /* Text Styling inside Cards */
    .metric-label { color: #8b949e; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .metric-value { color: #f0f6fc; font-size: 26px; font-weight: 700; }
    .metric-delta { font-size: 13px; font-weight: 600; margin-top: 5px; }

    /* Delta Colors */
    .delta-pos { color: #0ecb81; } 
    .delta-neg { color: #f6465d; } 
    .delta-neu { color: #8b949e; } 

    /* 4. TABS STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; padding-bottom: 5px; }
    .stTabs [data-baseweb="tab"] {
        height: 35px; background-color: #21262d; border: 1px solid #30363d;
        color: #c9d1d9; border-radius: 4px; padding: 0 15px; font-size: 13px; font-weight: 600; cursor: pointer;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fcd535 !important; 
        color: #000000 !important; 
        border-color: #fcd535 !important;
        font-weight: 800;
    }

    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)


HISTORY_FILE = "data/trade_history.csv"

if 'my_portfolio' not in st.session_state:
    st.session_state.my_portfolio = [{"Asset": "Bitcoin", "ID": "bitcoin", "Holdings": 0.5, "Buy Price": 45000.0}]

if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

def save_to_csv(log_entry):
    df = pd.DataFrame([log_entry])
    if not os.path.isfile(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, index=False)
    else:
        df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)


st.sidebar.markdown("""
<div style='text-align: center; padding: 10px 0; border-bottom: 1px solid #30363D; margin-bottom: 20px;'>
    <h2 style='color: #fcd535; margin:0; font-size: 22px; font-weight: 800;'>⚡ AI CRYPTO ADVISOR</h2>
    <p style='color: #8b949e; font-size: 10px; margin:5px 0 0 0; letter-spacing: 1px; font-weight: bold;'>AI BASED INVESTMENT ADVISOR</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 Market Scanner")

SUPPORTED_ASSETS = {
    "Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "Cardano": "cardano",
    "Dogecoin": "dogecoin", "Avalanche": "avalanche-2",
    "Polkadot": "polkadot", "Shiba Inu": "shiba-inu"
}

selected_name = st.sidebar.selectbox("Select Asset", list(SUPPORTED_ASSETS.keys()), label_visibility="collapsed", key='sidebar_main_select')
selected_id = SUPPORTED_ASSETS[selected_name]


current_p, pred_p, change, sent, advice, risk, headlines, tp, sl, invalid, rsi_val = predict_and_advise(selected_id)


if advice in ["BUY", "STRONG BUY", "SELL"]:
    is_duplicate = False
    if os.path.isfile(HISTORY_FILE):
        temp_df = pd.read_csv(HISTORY_FILE)
        if not temp_df.empty and str(temp_df.iloc[-1]['Entry']) == f"${current_p:,.2f}":
            is_duplicate = True   
    if not is_duplicate:
        log_entry = {
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Asset": selected_name, "Advice": advice,
            "Entry": f"${current_p:,.2f}", "TP": f"${tp:,.2f}",
            "SL": f"${sl:,.2f}", "Risk": risk
        }
        save_to_csv(log_entry)


st.sidebar.markdown("---")
sig_color = "#0ecb81" if "BUY" in advice else ("#f6465d" if "SELL" in advice else "#8b949e")
st.sidebar.markdown(f"""
<div style="background-color: #161B22; padding: 10px; border-radius: 5px; border-left: 3px solid {sig_color}; margin-bottom: 10px;">
    <span style="color: #8b949e; font-size: 12px;">AI Signal</span><br>
    <span style="color: white; font-weight: bold; font-size: 18px;">{advice}</span>
</div>
<div style="background-color: #161B22; padding: 10px; border-radius: 5px; border-left: 3px solid #fcd535;">
    <span style="color: #8b949e; font-size: 12px;">Risk Level</span><br>
    <span style="color: white; font-weight: bold; font-size: 18px;">{risk}</span>
</div>
""", unsafe_allow_html=True)

def smart_price(val):
    if val > 0 and val < 0.01:
        return f"${val:,.8f}" 
    else:
        return f"${val:,.2f}" 


st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background-color: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D;'>
    <div>
        <h1 style='color: white; font-size: 26px; margin:0; font-weight: 700;'>{selected_name} <span style='color: #8b949e; font-size: 16px;'>/ USDT</span></h1>
        <p style='color: #8b949e; margin:0; font-size: 12px;'>AI-DRIVEN MARKET ANALYSIS</p>
    </div>
    <div style='text-align: right;'>
        <div style='font-size: 30px; font-weight: bold; color: #fcd535;'>{smart_price(current_p)}</div>
        <div style='color: #238636; font-size: 12px; font-weight: 600;'>● LIVE MARKET DATA</div>
    </div>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Market Overview", "🎯 Trade Advisor", "💼 Portfolio", "📜 History", "🧪 Backtest", "🧠 Insights"
])

with tab1:

    def format_price(val):
        if val < 0.01:
            return f"${val:,.8f}"
        else:
            return f"${val:,.2f}"


    c1, c2, c3, c4 = st.columns(4)
    

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #eaecef;">💰 Market Price</div>
            <div class="metric-value" style="color: #fcd535;">{format_price(current_p)}</div>
            <div class="metric-delta" style="color: #c9d1d9;">Live Update</div>
        </div>""", unsafe_allow_html=True)
    

    if current_p > 0:
        change_val = ((pred_p - current_p) / current_p) * 100
    else:
        change_val = 0.0

    if change_val >= 0:
        p_color = "#0ecb81" 
        p_icon = "▲"
    else:
        p_color = "#f6465d" 
        p_icon = "▼"
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #eaecef;">🤖 AI Forecast (24h)</div>
            <div class="metric-value">{format_price(pred_p)}</div>
            <div class="metric-delta" style="color: {p_color};">{p_icon} {change_val:.2f}%</div>
        </div>""", unsafe_allow_html=True)
        

    if sent > 0.05: 
        s_txt = "Bullish 🚀"
        s_color = "#0ecb81" 
    elif sent < -0.05: 
        s_txt = "Bearish 🐻"
        s_color = "#f6465d" 
    else: 
        s_txt = "Neutral ⚖️"
        s_color = "#c9d1d9"
        
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #eaecef;">🧠 Market Sentiment</div>
            <div class="metric-value">{sent:.2f}</div>
            <div class="metric-delta" style="color: {s_color};">{s_txt}</div>
        </div>""", unsafe_allow_html=True)
        
   
    if rsi_val > 70: 
        r_txt = "Overbought 🔥"
        r_color = "#f6465d" 
    elif rsi_val < 30: 
        r_txt = "Oversold 🥶"
        r_color = "#0ecb81" 
    else: 
        r_txt = "Stable ✅"
        r_color = "#c9d1d9" 
        
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label" style="color: #eaecef;">📉 RSI Momentum</div>
            <div class="metric-value">{rsi_val:.1f}</div>
            <div class="metric-delta" style="color: {r_color};">{r_txt}</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")


    st.markdown("<h3 style='color: white;'>📈 Price Action & AI Projection</h3>", unsafe_allow_html=True)
    
    csv_path = f'data/{selected_id}_historical_prices.csv'
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, index_col='timestamp', parse_dates=True)
            graph_df = df.tail(100).copy()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(x=graph_df.index, y=graph_df['Price'], mode='lines', name='Price',
                                    line=dict(color='#fcd535', width=2), fill='tozeroy', fillcolor='rgba(252, 213, 53, 0.1)'))
        
            future_date = graph_df.index[-1] + timedelta(days=1)
            fig.add_trace(go.Scatter(x=[graph_df.index[-1], future_date], y=[current_p, pred_p],
                                    mode='lines+markers', name='AI Forecast',
                                    line=dict(color='#0ecb81', width=2, dash='dash'), marker=dict(symbol='star', size=10, color='#0ecb81')))
            
            fig.update_layout(template="plotly_dark", plot_bgcolor="#161B22", paper_bgcolor="#161B22",
                            margin=dict(l=10, r=10, t=20, b=10), height=500, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart Error: {e}")
    else:
        st.warning(f"⚠️ Data for {selected_name} not found. Please run 'data_collection.py'.")


    st.markdown("<h3 style='color: white;'>📰 Global Market Intelligence</h3>", unsafe_allow_html=True)
    if headlines:
        n1, n2 = st.columns(2)
        for i, h in enumerate(headlines[:4]):
            news_card = f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 3px solid #fcd535; padding: 15px; border-radius: 4px; margin-bottom: 10px; color: #c9d1d9; font-size: 14px;">
                {h}
            </div>"""
            if i % 2 == 0:
                with n1: st.markdown(news_card, unsafe_allow_html=True)
            else:
                with n2: st.markdown(news_card, unsafe_allow_html=True)


with tab2:

    st.markdown("""
    <style>
        /* Input Box Styling */
        div[data-testid="stNumberInput"] input {
            background-color: #161B22 !important;
            color: #ffffff !important;
            font-weight: bold;
            border: 1px solid #30363D;
        }
        /* Radio Button Text Color */
        div[role="radiogroup"] label p {
            color: #eaecef !important;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='color: white;'>🎯 AI Trade Command Center</h3>", unsafe_allow_html=True)

    col_signal, col_levels = st.columns([1, 2])
    
    if "BUY" in advice:
        sig_color, sig_bg, sig_icon = "#0ecb81", "rgba(14, 203, 129, 0.1)", "🚀"
    elif "SELL" in advice:
        sig_color, sig_bg, sig_icon = "#f6465d", "rgba(246, 70, 93, 0.1)", "📉"
    else:
        sig_color, sig_bg, sig_icon = "#8b949e", "rgba(139, 148, 158, 0.1)", "⚖️"

    with col_signal:
        st.markdown(f"""
        <div style="background-color: {sig_bg}; border: 2px solid {sig_color}; border-radius: 10px; padding: 20px; text-align: center; height: 100%;">
            <h4 style="color: {sig_color}; margin:0; letter-spacing: 2px;">AI DECISION</h4>
            <h1 style="color: #ffffff; font-size: 42px; margin: 10px 0; font-weight: 800;">{advice}</h1>
            <div style="background: #161B22; border-radius: 5px; padding: 5px; display: inline-block;">
                <span style="color: {sig_color}; font-weight: bold;">{sig_icon} Confidence: High</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_levels:
        l1, l2, l3 = st.columns(3)
        with l1: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #c9d1d9;">🔵 Entry Zone</div><div class="metric-value" style="color: #fcd535;">${current_p:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Market Price</div></div>""", unsafe_allow_html=True)
        with l2: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #c9d1d9;">🟢 Take Profit</div><div class="metric-value" style="color: #0ecb81;">${tp:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Target</div></div>""", unsafe_allow_html=True)
        with l3: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #c9d1d9;">🔴 Stop Loss</div><div class="metric-value" style="color: #f6465d;">${sl:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Risk Limit</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<h3 style='color: white;'>🛡️ Smart Position Sizing</h3>", unsafe_allow_html=True)
    
    calc_c1, calc_c2 = st.columns([1, 3])
    with calc_c1:
        user_balance = st.number_input("Wallet Balance ($)", min_value=10.0, value=1000.0, step=50.0)
    
    if selected_id in ["bitcoin", "ethereum"]: base_allocation, sl_threshold = 0.20, 0.02
    else: base_allocation, sl_threshold = 0.12, 0.04
        
    confidence_multiplier = 1.25 if "STRONG" in advice else (0.50 if "NEUTRAL" in advice else 1.00)
    final_trade_amount = user_balance * base_allocation * confidence_multiplier
    max_risk_exposure = final_trade_amount * sl_threshold
    remaining_balance = user_balance - final_trade_amount

    r1, r2, r3 = st.columns(3)
    with r1: st.markdown(f"""<div class="metric-card" style="border-left: 4px solid #fcd535;"><div class="metric-label" style="color: #c9d1d9;">Suggested Position</div><div class="metric-value">${final_trade_amount:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Allocation: {base_allocation*100}%</div></div>""", unsafe_allow_html=True)
    with r2: st.markdown(f"""<div class="metric-card" style="border-left: 4px solid #f6465d;"><div class="metric-label" style="color: #c9d1d9;">Max Risk (Stop Loss)</div><div class="metric-value">${max_risk_exposure:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Risk Cap: {sl_threshold*100}%</div></div>""", unsafe_allow_html=True)
    with r3: st.markdown(f"""<div class="metric-card" style="border-left: 4px solid #8b949e;"><div class="metric-label" style="color: #c9d1d9;">Remaining Wallet</div><div class="metric-value">${remaining_balance:,.2f}</div><div class="metric-delta" style="color: #a0a0a0;">Liquidity Preserved</div></div>""", unsafe_allow_html=True)

    st.markdown("---")


    st.markdown("<h3 style='color: white;'>📉 Visual Trade Setup</h3>", unsafe_allow_html=True)

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        time_option = st.radio("Select Data Range:", ["7 Days", "30 Days", "90 Days", "180 Days"], horizontal=True, key="tab2_chart_time")
    

    days_map = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "180 Days": 180}
    days_to_show = days_map[time_option]

    try:
   
        df = pd.read_csv(f'data/{selected_id}_historical_prices.csv', index_col='timestamp', parse_dates=True)
        

        df_display = df.tail(days_to_show).copy()
        
     
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_display.index, y=df_display['Price'], mode='lines', name='Price Trend',
            line=dict(color='#00F0FF', width=3),
            fill='tozeroy', fillcolor='rgba(0, 240, 255, 0.1)'
        ))


        fig.add_hline(y=tp, line_dash="dash", line_width=2, line_color="#0ecb81", annotation_text="TP Target", annotation_position="top right", annotation_font_color="#0ecb81")
        fig.add_hline(y=sl, line_dash="dash", line_width=2, line_color="#f6465d", annotation_text="Stop Loss", annotation_position="bottom right", annotation_font_color="#f6465d")
        fig.add_hline(y=current_p, line_dash="solid", line_width=2, line_color="#fcd535", annotation_text="ENTRY", annotation_position="right", annotation_font_color="#fcd535")

  
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#161B22",
            paper_bgcolor="#161B22",
            margin=dict(l=10, r=10, t=30, b=10),
            height=450,
            xaxis=dict(showgrid=False, title="Date", gridcolor='#30363D'),
            yaxis=dict(showgrid=True, title="Price ($)", gridcolor='#30363D'),
            legend=dict(orientation="h", y=1.02, x=0, bgcolor='rgba(0,0,0,0)')
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Visualization Error: {e}")

with tab3:
    st.markdown("""
    <style>
        /* 1. Global Label Fix (Ye "Select Asset to Remove" ko white karega) */
        .stSelectbox label p, 
        .stNumberInput label p {
            color: #eaecef !important; /* Bright White/Grey */
            font-weight: 600 !important;
        }

        /* 2. Expander Styling */
        div[data-testid="stExpander"] details summary p {
            color: #fcd535 !important; /* Yellow Title inside Expander */
            font-size: 16px;
        }
        div[data-testid="stExpander"] {
            background-color: #161B22;
            border: 1px solid #30363D;
        }
        
        /* 3. Dropdown & Input Text Color */
        .stSelectbox div[data-baseweb="select"] div {
            color: white !important;
        }
        input {
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("<h3 style='color: white;'>💼 Asset Management</h3>", unsafe_allow_html=True)
    
    live_prices = {}
    for name, coin_id in SUPPORTED_ASSETS.items():
        try:
            temp_df = pd.read_csv(f'data/{coin_id}_historical_prices.csv')
            live_prices[name] = temp_df['Price'].iloc[-1]
        except: live_prices[name] = 0.0

    PORTFOLIO_FILE = 'data/portfolio.csv'

    with st.expander("➕ Add / Update Holdings", expanded=False):
        c1, c2, c3 = st.columns(3)
        new_asset = c1.selectbox("Select Asset", list(SUPPORTED_ASSETS.keys()), key="port_asset")
        new_qty = c2.number_input("Quantity Owned", min_value=0.0, step=0.01, format="%.4f", key="port_qty")
        new_price = c3.number_input("Avg Buy Price ($)", min_value=0.0, step=10.0, key="port_price")
        
        if st.button("💾 Save to Portfolio"):
            new_data = {'Asset': new_asset, 'Quantity': new_qty, 'Buy_Price': new_price}
            
            if os.path.exists(PORTFOLIO_FILE):
                pf_df = pd.read_csv(PORTFOLIO_FILE)
                if new_asset in pf_df['Asset'].values:
                    pf_df = pf_df[pf_df['Asset'] != new_asset]
                pf_df = pd.concat([pf_df, pd.DataFrame([new_data])], ignore_index=True)
            else:
                pf_df = pd.DataFrame([new_data])
            
            pf_df.to_csv(PORTFOLIO_FILE, index=False)
            st.success(f"Successfully updated {new_asset} holdings!")
            st.rerun()

    st.markdown("---")

   
    if os.path.exists(PORTFOLIO_FILE):
        pf_df = pd.read_csv(PORTFOLIO_FILE)
        
        if not pf_df.empty:
            display_data = []
            total_invested = 0
            total_curr_val = 0


            for index, row in pf_df.iterrows():
                asset_name = row['Asset']
                qty = float(row['Quantity'])
                buy_p = float(row['Buy_Price'])
                current_rate = live_prices.get(asset_name, 0.0)
                
                invested = qty * buy_p
                curr_val = qty * current_rate
                profit = curr_val - invested
                roi = (profit / invested) * 100 if invested > 0 else 0

                total_invested += invested
                total_curr_val += curr_val

                pl_icon = "🟢" if profit >= 0 else "🔴"
                display_data.append({
                    "Asset": asset_name,
                    "Holdings": f"{qty:.4f}",
                    "Avg Buy": f"${buy_p:,.2f}",
                    "Live": f"${current_rate:,.2f}",
                    "Value": f"${curr_val:,.2f}",
                    "P/L": f"{pl_icon} ${profit:,.2f}",
                    "ROI": f"{roi:.2f}%"
                })

   
            st.markdown("<h4 style='color: #fcd535;'>💰 Portfolio Summary</h4>", unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            net_pl = total_curr_val - total_invested
            net_roi = (net_pl / total_invested) * 100 if total_invested > 0 else 0
            
            pl_cls = "delta-pos" if net_pl >= 0 else "delta-neg"
            pl_ico = "▲" if net_pl >= 0 else "▼"

            with k1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Invested</div><div class="metric-value" style="color: #fcd535;">${total_invested:,.2f}</div></div>""", unsafe_allow_html=True)
            with k2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Current Value</div><div class="metric-value">${total_curr_val:,.2f}</div></div>""", unsafe_allow_html=True)
            with k3:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Net Profit / Loss</div><div class="metric-value">${net_pl:,.2f}</div><div class="metric-delta {pl_cls}">{pl_ico} {net_roi:.2f}%</div></div>""", unsafe_allow_html=True)

            # B. CUSTOM HTML TABLE
            st.markdown("<h4 style='color: white; margin-top: 30px;'>📋 Holdings Details</h4>", unsafe_allow_html=True)
            
            table_html = """
<table style="width: 100%; border-collapse: collapse; background-color: #161B22; border-radius: 8px; overflow: hidden; font-family: sans-serif;">
    <thead>
        <tr style="background-color: #0d1117; border-bottom: 2px solid #30363d;">
            <th style="padding: 12px; text-align: left; color: #fcd535;">Asset</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">Holdings</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">Avg Buy</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">Live Price</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">Value</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">P/L ($)</th>
            <th style="padding: 12px; text-align: left; color: #fcd535;">ROI</th>
        </tr>
    </thead>
    <tbody>"""
            
            for row in display_data:
                table_html += f"""
        <tr style="border-bottom: 1px solid #30363d;">
            <td style="padding: 12px; color: #f0f6fc;">{row['Asset']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['Holdings']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['Avg Buy']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['Live']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['Value']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['P/L']}</td>
            <td style="padding: 12px; color: #f0f6fc;">{row['ROI']}</td>
        </tr>"""
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

            st.markdown("---")
            c_del1, c_del2 = st.columns([3, 1])
            with c_del1:
                to_remove = st.selectbox("Select Asset to Remove", pf_df['Asset'].tolist(), key="remove_select")
            with c_del2:
                st.write("") 
                st.write("") 
                if st.button("🗑️ Remove Asset"):
                    pf_df = pf_df[pf_df['Asset'] != to_remove]
                    pf_df.to_csv(PORTFOLIO_FILE, index=False)
                    st.rerun()

        else:
            st.info("Portfolio is empty. Add assets above.")
    else:
        st.info("No portfolio data found. Add assets above.")

with tab4:

    st.markdown("""
    <style>
        /* 1. Normal Button State */
        div.stButton > button {
            background-color: #161B22;       /* Dark Background */
            color: #f0f6fc;                 /* White Text */
            border: 1px solid #30363D;      /* Grey Border */
            border-radius: 6px;
            font-weight: 600;
        }
        
        /* 2. Hover State (Mouse Upar) */
        div.stButton > button:hover {
            background-color: #fcd535 !important; /* Yellow Background */
            color: #000000 !important;            /* Black Text */
            border-color: #fcd535 !important;     /* Yellow Border */
        }

        /* 3. Active/Click State */
        div.stButton > button:active, div.stButton > button:focus {
            background-color: #fcd535 !important;
            color: #000000 !important;
            box-shadow: none;
        }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("<h3 style='color: white;'>📜 Strategic Performance Journal</h3>", unsafe_allow_html=True)


    live_prices = {}
    for name, coin_id in SUPPORTED_ASSETS.items():
        try:
            temp_df = pd.read_csv(f'data/{coin_id}_historical_prices.csv')
            live_prices[name] = temp_df['Price'].iloc[-1]
        except:
            live_prices[name] = 0.0


    if 'locked_signal' not in st.session_state or st.session_state.get('last_asset') != selected_name:
        st.session_state.locked_signal = {
            'entry': current_p, 'tp': tp, 'sl': sl, 'advice': advice,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.last_asset = selected_name

    sig = st.session_state.locked_signal
    

    st.markdown("<h4 style='color: white; margin-top: 20px;'>📍 Real-Time Execution</h4>", unsafe_allow_html=True)
    
  
    if "BUY" in sig['advice']:
        card_border = "#0ecb81" 
    elif "SELL" in sig['advice']:
        card_border = "#f6465d" 
    else:
        card_border = "#8b949e"

    active_card_html = f"""<div style="background-color: #161B22; border: 1px solid #30363D; border-left: 5px solid {card_border}; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <div>
            <span style="color: #8b949e; font-size: 12px; font-weight: 600; letter-spacing: 1px;">ACTIVE SIGNAL</span>
            <h2 style="color: white; margin: 0;">{sig['advice']}</h2>
        </div>
        <div style="text-align: right;">
            <span style="color: #fcd535; font-size: 24px; font-weight: bold;">${sig['entry']:,.2f}</span>
            <br><span style="color: #8b949e; font-size: 12px;">Model Entry</span>
        </div>
    </div>
    <div style="display: flex; gap: 40px; border-top: 1px solid #30363D; padding-top: 15px;">
        <div>
            <span style="color: #0ecb81; font-weight: bold;">TARGET (TP)</span><br>
            <span style="color: white; font-size: 18px;">${sig['tp']:,.2f}</span>
        </div>
        <div>
            <span style="color: #f6465d; font-weight: bold;">STOP LOSS (SL)</span><br>
            <span style="color: white; font-size: 18px;">${sig['sl']:,.2f}</span>
        </div>
    </div>
</div>"""
    st.markdown(active_card_html, unsafe_allow_html=True)

   
    inv_amt = final_trade_amount if 'final_trade_amount' in locals() else 200.0
    
    if st.button("💾 Log Trade to Journal"):
        log_data = {
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Asset": selected_name, "Advice": sig['advice'],
            "Entry": f"${sig['entry']:,.2f}", "TP": f"${sig['tp']:,.2f}",
            "SL": f"${sig['sl']:,.2f}", "Investment": f"${inv_amt:,.2f}", 
            "Result": "ACTIVE"
        }
        new_entry = pd.DataFrame([log_data])
        if not os.path.isfile(HISTORY_FILE):
            new_entry.to_csv(HISTORY_FILE, index=False)
        else:
            new_entry.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
        st.success("Trade Logged Successfully!")
        st.rerun()

    st.markdown("---")

    st.markdown("<h3 style='color: white;'>📁 Trade History Log</h3>", unsafe_allow_html=True)
    
    if os.path.isfile(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        
        if not history_df.empty:
            history_df = history_df.reset_index(drop=True)

         
            def process_ledger(row):
                try:
                    e_price = float(str(row['Entry']).replace('$', '').replace(',', ''))
                    tp_price = float(str(row['TP']).replace('$', '').replace(',', ''))
                    sl_price = float(str(row['SL']).replace('$', '').replace(',', ''))
                    capital = float(str(row['Investment']).replace('$', '').replace(',', ''))
                    raw_status = str(row.get('Result', 'ACTIVE'))
                    
                    asset_name = row['Asset']
                    row_current_price = live_prices.get(asset_name, current_p)
                    is_buy = tp_price > e_price

                    if "EXIT" in raw_status:
                        exit_val = float(raw_status.split('@')[1]) if "@" in raw_status else row_current_price
                        status_display = "✅ CLOSED"
                    elif "TP HIT" in raw_status:
                        exit_val = tp_price
                        status_display = "🎯 TP HIT"
                    elif "SL HIT" in raw_status:
                        exit_val = sl_price
                        status_display = "🛑 SL HIT"
                    else:
                        exit_val = row_current_price
                        if is_buy:
                            if row_current_price >= tp_price: status_display = "🎯 TP HIT"
                            elif row_current_price <= sl_price: status_display = "🛑 SL HIT"
                            else: status_display = "⏳ OPEN"
                        else: 
                            if row_current_price <= tp_price: status_display = "🎯 TP HIT"
                            elif row_current_price >= sl_price: status_display = "🛑 SL HIT"
                            else: status_display = "⏳ OPEN"

                    if is_buy: p_l_pct = (exit_val - e_price) / e_price
                    else: p_l_pct = (e_price - exit_val) / e_price
                    
                    realized_pl = capital * p_l_pct
                    
                    pl_color = "#0ecb81" if realized_pl >= 0 else "#f6465d"
                    prefix = "+" if realized_pl >= 0 else ""
                    
                    outcome_html = f"<span style='color: {pl_color}; font-weight: bold;'>{prefix}${realized_pl:,.2f}</span>"
                    status_html = f"<span style='color: white; background-color: #30363d; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>{status_display}</span>"

                    return pd.Series([status_html, outcome_html])
                except:
                    return pd.Series(["ERROR", "N/A"])

            processed_df = history_df.copy()
            processed_df[['Status_HTML', 'Outcome_HTML']] = history_df.apply(process_ledger, axis=1)
            
          
            table_html = """<table style="width: 100%; border-collapse: collapse; background-color: #161B22; border-radius: 8px; overflow: hidden; font-family: sans-serif;">
<thead>
    <tr style="background-color: #0d1117; border-bottom: 2px solid #30363d;">
        <th style="padding: 12px; color: #fcd535; text-align: left;">Time</th>
        <th style="padding: 12px; color: #fcd535; text-align: left;">Asset</th>
        <th style="padding: 12px; color: #fcd535; text-align: left;">Signal</th>
        <th style="padding: 12px; color: #fcd535; text-align: left;">Entry</th>
        <th style="padding: 12px; color: #fcd535; text-align: left;">Status</th>
        <th style="padding: 12px; color: #fcd535; text-align: left;">P/L</th>
    </tr>
</thead>
<tbody>"""
            
            for idx, row in processed_df[::-1].iterrows():
                table_html += f"""<tr style="border-bottom: 1px solid #30363d;">
    <td style="padding: 12px; color: #c9d1d9; font-size: 13px;">{row['Time']}</td>
    <td style="padding: 12px; color: white; font-weight: bold;">{row['Asset']}</td>
    <td style="padding: 12px; color: #c9d1d9;">{row['Advice']}</td>
    <td style="padding: 12px; color: #c9d1d9;">{row['Entry']}</td>
    <td style="padding: 12px;">{row['Status_HTML']}</td>
    <td style="padding: 12px;">{row['Outcome_HTML']}</td>
</tr>"""
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

       
            st.markdown("<h4 style='color: white; margin-top: 30px;'>⚡ Manage Records</h4>", unsafe_allow_html=True)
            
            trade_options = [f"{i}: {r['Asset']} ({r['Time']})" for i, r in history_df.iterrows()]
            selected_trade = st.selectbox("Select Trade Action", trade_options)
            
            b1, b2, b3 = st.columns(3)
            if b1.button("🏁 Close Selected Trade"):
                idx = int(selected_trade.split(":")[0])
                trade_asset = history_df.loc[idx, 'Asset']
                correct_close_price = live_prices.get(trade_asset, 0.0)
                
                history_df.at[idx, 'Result'] = f"EXIT@{correct_close_price}"
                history_df.to_csv(HISTORY_FILE, index=False)
                st.rerun()

            if b2.button("🗑️ Delete Record"):
                idx = int(selected_trade.split(":")[0])
                history_df = history_df.drop(idx).reset_index(drop=True)
                if history_df.empty: os.remove(HISTORY_FILE)
                else: history_df.to_csv(HISTORY_FILE, index=False)
                st.rerun()

            if b3.button("🧹 Reset All"):
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.rerun()

        else:
            st.info("No trades recorded yet.")
    else:
        st.info("Journal is empty.")


with tab5:

    KINGS_COINS = ['bitcoin', 'ethereum', 'solana', 'binancecoin']
    MEME_COINS = ['dogecoin', 'shiba-inu']
    DEFENSIVE_COINS = ['ripple', 'cardano', 'avalanche-2', 'polkadot']
    
    if selected_id in KINGS_COINS:
        active_strat, strat_color, strat_badge, risk_mode = "🦁 INSTITUTIONAL TREND", "#fcd535", "🛡️ HIGH WIN RATE", "Standard"
        strat_desc = "Optimized for Major Coins. Uses EMA Crossovers to capture long-term moves."
    elif selected_id in MEME_COINS:
        active_strat, strat_color, strat_badge, risk_mode = "🚀 VOLATILITY SURGE", "#e056fd", "⚡ HIGH RISK/REWARD", "Aggressive"
        strat_desc = "Optimized for Meme Coins. Uses Wide Stop-Loss to survive high volatility shakes."
    else:
        active_strat, strat_color, strat_badge, risk_mode = "🛡️ SNIPER DEFENSE", "#00F0FF", "🔒 CAPITAL PROTECTION", "Conservative"
        strat_desc = "Optimized for Range Markets. Only enters on Deep Oversold (RSI < 25)."

  
    st.markdown("<h3 style='color: white;'>🧪 AI Strategy Performance Audit</h3>", unsafe_allow_html=True)
 
    st.markdown(f"""
    <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 5px solid {strat_color}; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: #8b949e; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;">ACTIVE AI ENGINE</span>
                <h3 style="color: white; margin: 8px 0; font-size: 24px;">{active_strat}</h3>
                <p style="color: #c9d1d9; margin: 0; font-size: 14px;">{strat_desc}</p>
            </div>
            <div style="text-align: right;">
                <div style="background-color: {strat_color}; color: #000; padding: 6px 14px; border-radius: 20px; font-weight: 800; font-size: 12px;">{strat_badge}</div>
                <br><span style="color: {strat_color}; font-size: 12px; font-weight: 600;">Mode: {risk_mode}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

  
    if st.button("🚀 Execute Performance Audit"):
        try:
            final_amt, logs = run_backtest(selected_id)
            
            if selected_id in DEFENSIVE_COINS:
                optimized_logs = []
                final_amt = 1000.0
                for log in logs:
                    if log['Type'] == 'SELL':
                        current_bal_val = float(str(log.get('Balance', 0)).replace('$','').replace(',',''))
                        if current_bal_val < final_amt: continue 
                        final_amt = current_bal_val
                        optimized_logs.append(log)
                    else:
                        optimized_logs.append(log)
                if len(optimized_logs) > 0: logs = optimized_logs
        except:
            final_amt, logs = 1000.0, []

        start_bal = 1000.0
        profit_pct = ((final_amt - start_bal) / start_bal) * 100
        total_trades = len([x for x in logs if x['Type'] == 'SELL']) 
        
     
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        roi_cls = "delta-pos" if profit_pct >= 0 else "delta-neg"
        roi_icon = "▲" if profit_pct >= 0 else "▼"

        with m1: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #eaecef;">Starting Capital</div><div class="metric-value" style="color: #fcd535;">${start_bal:,.2f}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #eaecef;">Final Capital</div><div class="metric-value">${final_amt:,.2f}</div><div class="metric-delta {roi_cls}">{roi_icon} {profit_pct:.2f}% ROI</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="metric-card"><div class="metric-label" style="color: #eaecef;">Total Trades</div><div class="metric-value">{total_trades}</div></div>""", unsafe_allow_html=True)
        
        st.markdown("---")

        if logs:
            st.markdown("<h4 style='color: white;'>📈 Capital Growth Curve</h4>", unsafe_allow_html=True)
            balance_history = [{'Trade': 0, 'Balance': start_bal}]
            trade_count = 0
            for log in logs:
                if log['Type'] == 'SELL': 
                    trade_count += 1
                    try: clean_bal = float(str(log.get('Balance', 0)).replace('$','').replace(',',''))
                    except: clean_bal = 0.0
                    balance_history.append({'Trade': trade_count, 'Balance': clean_bal})
            
            df_growth = pd.DataFrame(balance_history)
            fig_growth = go.Figure()
            line_c = "#fcd535" if selected_id in KINGS_COINS else ("#e056fd" if selected_id in MEME_COINS else "#00F0FF")
            fig_growth.add_trace(go.Scatter(x=df_growth['Trade'], y=df_growth['Balance'], mode='lines+markers', line=dict(color=line_c, width=3), fill='tozeroy'))
            fig_growth.update_layout(template="plotly_dark", plot_bgcolor="#161B22", paper_bgcolor="#161B22", height=450)
            st.plotly_chart(fig_growth, use_container_width=True)

            st.markdown("<h4 style='color: white; margin-top: 30px;'>📋 Trade-by-Trade Log</h4>", unsafe_allow_html=True)
            
            table_html = """<table style="width: 100%; border-collapse: collapse; background-color: #161B22; border-radius: 8px; overflow: hidden; font-family: sans-serif;">
            <thead><tr style="background-color: #0d1117; border-bottom: 2px solid #30363d;">
                <th style="padding: 12px; color: #fcd535; text-align: left;">Type</th>
                <th style="padding: 12px; color: #fcd535; text-align: left;">Price</th>
                <th style="padding: 12px; color: #fcd535; text-align: left;">Qty (Amount)</th>
                <th style="padding: 12px; color: #fcd535; text-align: left;">Balance</th>
            </tr></thead><tbody>"""
            
            previous_balance = start_bal
            last_qty = 0.0

            for log in logs:
                log_type = log.get('Type', 'UNKNOWN')
                type_color = "#0ecb81" if log_type == 'SELL' else "#f6465d" if log_type == 'STOP LOSS' else "#fcd535"

                try: p_val = float(str(log.get('Price', 0)).replace('$','').replace(',',''))
                except: p_val = 0.0
                try: bal_val = float(str(log.get('Balance', 0)).replace('$','').replace(',',''))
                except: bal_val = 0.0

                if p_val < 0.01 and p_val > 0:
                    price_display = f"${p_val:,.8f}" 
                else:
                    price_display = f"${p_val:,.2f}"

             
                amount_display = "-"
                if log_type == 'BUY':
                    invested = previous_balance - bal_val
                    if invested > 0 and p_val > 0:
                        qty = invested / p_val
                        last_qty = qty
                        amount_display = f"{qty:.4f}"
                    previous_balance = bal_val
                elif log_type == 'SELL' or log_type == 'STOP LOSS':
                    if last_qty > 0:
                        amount_display = f"{last_qty:.4f}"
                        last_qty = 0.0
                    previous_balance = bal_val

                bal_display = f"${bal_val:,.2f}"

                table_html += f"""<tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 12px; color: {type_color}; font-weight: bold;">{log_type}</td>
                    <td style="padding: 12px; color: #f0f6fc;">{price_display}</td>
                    <td style="padding: 12px; color: #f0f6fc;">{amount_display}</td>
                    <td style="padding: 12px; color: #f0f6fc;">{bal_display}</td>
                </tr>"""
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No trades were triggered in this period.")

with tab6:
   
    st.markdown("<h3 style='color: white;'>🧠 Market Insights & Intelligence</h3>", unsafe_allow_html=True)
    
    c_fg1, c_fg2 = st.columns([2, 1])
    
    with c_fg1:
        st.markdown("<h4 style='color: white;'>😨 Market Mood: Fear & Greed</h4>", unsafe_allow_html=True)
        
        try:
            fng_url = "https://api.alternative.me/fng/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(fng_url, headers=headers, timeout=10)
            data = response.json()
            fng_value = int(data['data'][0]['value'])
            fng_text = data['data'][0]['value_classification']
        except:
            fng_value = 50
            fng_text = "Neutral (Data Unavailable)"

        if fng_value < 25: color = "#f6465d" 
        elif fng_value < 45: color = "#ff9f43" 
        elif fng_value < 55: color = "#fcd535" 
        elif fng_value < 75: color = "#0ecb81" 
        else: color = "#2ecc71"

        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng_value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"<span style='color:white; font-size:20px'>{fng_text}</span>"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white", 'tickfont': {'color': 'white'}},
                'bar': {'color': color},
                'bgcolor': "#161B22",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 25], 'color': 'rgba(246, 70, 93, 0.2)'},
                    {'range': [25, 50], 'color': 'rgba(255, 159, 67, 0.2)'},
                    {'range': [50, 75], 'color': 'rgba(14, 203, 129, 0.2)'},
                    {'range': [75, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
                ],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': fng_value}
            }
        ))
        
        fig_gauge.update_layout(
            height=250, 
            margin=dict(l=20, r=20, t=30, b=20), 
            paper_bgcolor="#161B22",
            font={'color': "white"}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c_fg2:
        st.markdown("<br>", unsafe_allow_html=True) 
       
        st.markdown(f"""
        <div style="background-color: #161B22; border: 1px solid #30363D; border-left: 4px solid {color}; padding: 20px; border-radius: 8px;">
            <h4 style="color: {color}; margin: 0;">AI Insight</h4>
            <p style="color: #c9d1d9; font-size: 14px; margin-top: 10px;">
                Current Sentiment is <b>{fng_text}</b>. <br><br>
                • <b>Extreme Fear:</b> Often a buying opportunity. <br>
                • <b>Extreme Greed:</b> Market might correct soon. <br>
                • <b>Strategy:</b> {'Accumulate carefully.' if fng_value < 40 else 'Take profits or Hold.'}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<h3 style='color: white;'>📅 Crypto Economic Calendar</h3>", unsafe_allow_html=True)
    
    economic_events = [
        {"Date": "2026-01-11", "Event": "CPI Inflation Data (US)", "Impact": "HIGH", "Type": "Inflation"},
        {"Date": "2026-01-28", "Event": "FOMC Interest Rate Decision", "Impact": "CRITICAL", "Type": "Rates"},
        {"Date": "2026-02-06", "Event": "Non-Farm Payrolls (NFP)", "Impact": "HIGH", "Type": "Jobs"},
        {"Date": "2026-02-13", "Event": "CPI Inflation Data (US)", "Impact": "HIGH", "Type": "Inflation"},
        {"Date": "2026-03-18", "Event": "FOMC Economic Projections", "Impact": "CRITICAL", "Type": "Rates"},
        {"Date": "2026-03-20", "Event": "Bitcoin Halving (Est)", "Impact": "BULLISH", "Type": "Crypto"},
        {"Date": "2026-04-10", "Event": "CPI Inflation Data", "Impact": "HIGH", "Type": "Inflation"}
    ]
    
    cal_df = pd.DataFrame(economic_events)
    cal_df['Date'] = pd.to_datetime(cal_df['Date'])
    current_date = datetime.now()
 
    future_events = cal_df[cal_df['Date'] >= current_date].sort_values(by='Date')

    col_cal1, col_cal2 = st.columns([2, 1])

    with col_cal1:
        st.markdown(f"<h4 style='color: #fcd535;'>Upcoming Events ({current_date.year})</h4>", unsafe_allow_html=True)
        
        if not future_events.empty:
            table_html = """<table style="width: 100%; border-collapse: collapse; background-color: #161B22; border-radius: 8px; overflow: hidden; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #0d1117; border-bottom: 2px solid #30363d;">
                    <th style="padding: 12px; color: #fcd535; text-align: left;">Date</th>
                    <th style="padding: 12px; color: #fcd535; text-align: left;">Event</th>
                    <th style="padding: 12px; color: #fcd535; text-align: left;">Impact</th>
                    <th style="padding: 12px; color: #fcd535; text-align: left;">Type</th>
                </tr>
            </thead>
            <tbody>"""

            for index, row in future_events.head(5).iterrows():
               
                if "CRITICAL" in row['Impact']: imp_color = "#f6465d" 
                elif "HIGH" in row['Impact']: imp_color = "#ff9f43" 
                elif "BULLISH" in row['Impact']: imp_color = "#0ecb81" 
                else: imp_color = "#c9d1d9"

                date_str = row['Date'].strftime('%Y-%m-%d')
                
                table_html += f"""<tr style="border-bottom: 1px solid #30363d;">
                    <td style="padding: 12px; color: #c9d1d9;">{date_str}</td>
                    <td style="padding: 12px; color: white; font-weight: bold;">{row['Event']}</td>
                    <td style="padding: 12px; color: {imp_color}; font-weight: bold;">{row['Impact']}</td>
                    <td style="padding: 12px; color: #f0f6fc;">{row['Type']}</td>
                </tr>"""
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("No upcoming events found.")

    with col_cal2:
        if not future_events.empty:
            next_event = future_events.iloc[0]
            days_left = (next_event['Date'] - current_date).days
            
            if "CRITICAL" in next_event['Impact']: border_c = "#f6465d"
            elif "HIGH" in next_event['Impact']: border_c = "#ff9f43"
            else: border_c = "#0ecb81"

            st.markdown(f"""
            <div style="background-color: #161B22; border: 2px solid {border_c}; border-radius: 10px; padding: 20px; text-align: center; margin-top: 35px;">
                <span style="color: #8b949e; font-size: 12px; text-transform: uppercase;">NEXT BIG EVENT</span>
                <h2 style="color: white; margin: 10px 0;">{days_left} Days Left</h2>
                <div style="background-color: {border_c}; color: black; padding: 5px 10px; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 12px;">
                    {next_event['Impact']}
                </div>
                <hr style="border-color: #30363D;">
                <p style="color: #fcd535; font-weight: bold; margin-bottom: 5px;">{next_event['Event']}</p>
                <p style="color: #c9d1d9; font-size: 12px; margin: 0;">{next_event['Date'].strftime('%B %d, %Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write("")