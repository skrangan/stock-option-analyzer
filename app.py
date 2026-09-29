"""
app.py - Stock Analysis & Option Purchase Decision Application
Light-themed, modern, responsive financial dashboard with prominent timeframe controls
and an interactive Option Buy Decision & P&L Simulator.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import stock_core as sc
import options_core as oc
import charts

# Configure page settings
st.set_page_config(
    page_title="Stock & Option Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Light Theme CSS
st.markdown("""
<style>
    /* Main Background & Clean Light Typography */
    .stApp {
        background-color: #FFFFFF;
        color: #0F172A;
    }
    
    /* Clean Light Metric Card Styling */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }
    .metric-value-lg {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 12px;
        color: #64748B;
        margin-top: 6px;
        line-height: 1.4;
    }
    
    /* Light Badges */
    .badge-green {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
    }
    .badge-red {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
    }
    .badge-neutral {
        background-color: #FFFBEB;
        color: #D97706;
        border: 1px solid #FDE68A;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
    }
    
    /* Decision & Outlook Boxes */
    .decision-box-light {
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 22px;
        border: 1px solid #E2E8F0;
        border-left: 6px solid;
        background-color: #F8FAFC;
    }
    
    /* Config Panel */
    .config-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    
    /* Prominent Top-Level Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #F1F5F9;
        padding: 6px 8px;
        border-radius: 10px;
        margin-bottom: 22px;
        border: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        padding: 0 24px;
        color: #475569;
        background-color: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F172A;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
    }

</style>
""", unsafe_allow_html=True)

# Session State for Timeframe, Ticker, and Option settings
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "AAPL"
if "selected_timeframe" not in st.session_state:
    st.session_state.selected_timeframe = "6M"

def set_timeframe(tf):
    st.session_state.selected_timeframe = tf

def set_ticker(sym):
    st.session_state.current_ticker = sym

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.title("📈 Stock & Option Hub")
    st.caption("Real-time stats, growth, 2-week outlook, earnings & option decisions")
    
    st.markdown("### 🔍 Enter Ticker Symbol")
    
    # Quick Pick Chips
    st.write("Popular Tickers:")
    chips = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "SPY"]
    cols_chips = st.columns(4)
    for idx, c in enumerate(chips):
        col_idx = idx % 4
        with cols_chips[col_idx]:
            if st.button(c, key=f"btn_chip_{c}", use_container_width=True):
                set_ticker(c)
                st.rerun()

    ticker_sym = st.text_input(
        "Search Symbol",
        value=st.session_state.current_ticker,
        key="main_ticker_input",
        placeholder="e.g. AAPL, NVDA, TSLA..."
    ).strip().upper()
    
    if ticker_sym != st.session_state.current_ticker:
        set_ticker(ticker_sym)

    st.markdown("---")
    st.markdown("### 💡 Key Capabilities")
    st.markdown("""
    - **Stock Analytics**: Real-time stats, volume, 1W/3M/6M/1Y growth, and quarterly earnings performance.
    - **2-Week Outlook**: Multi-source statistical projection & technical momentum.
    - **Option Buy/Pass Analyzer**: Evaluates whether to buy an option based on strike, bid amount, expiration date, theta decay, and probability of profit.
    """)

# ----------------- MAIN APP EXECUTION -----------------
active_ticker = st.session_state.current_ticker

if not active_ticker:
    st.info("👈 Please enter or select a ticker symbol in the sidebar.")
    st.stop()

# Fetch data with cache (100% pickle-serializable)
@st.cache_data(ttl=120)
def load_data(symbol: str):
    return sc.get_full_stock_analysis(symbol)

@st.cache_data(ttl=120)
def load_options_expirations(symbol: str):
    return oc.get_available_expirations(symbol)

@st.cache_data(ttl=120)
def load_option_chain(symbol: str, expiration_date: str):
    return oc.get_option_chain_data(symbol, expiration_date)

try:
    with st.spinner(f"Fetching data for {active_ticker}..."):
        analysis = load_data(active_ticker)
except Exception as e:
    st.error(f"❌ Could not load data for ticker **'{active_ticker}'**: {e}")
    st.info("Please verify the ticker symbol (e.g. AAPL, MSFT, NVDA, SPY).")
    st.stop()

# Unpack analysis data
stock_data = analysis["raw"]
growth_metrics = analysis["growth"]
volume_metrics = analysis["volume"]
outlook = analysis["outlook"]
quarterly = analysis["quarterly"]

hist = stock_data["history"]
curr_price = stock_data["current_price"]
prev_close = stock_data["previous_close"]
change_abs = stock_data["change_abs"]
change_pct = stock_data["change_pct"]
short_name = stock_data["short_name"]
currency = stock_data["currency"]
sector = stock_data["sector"]
industry = stock_data["industry"]
exchange = stock_data["exchange"]

# ----------------- HEADER SECTION -----------------
head_col1, head_col2 = st.columns([3, 2])
with head_col1:
    st.title(f"{short_name} ({active_ticker})")
    st.markdown(f"**Exchange:** `{exchange}` &nbsp;|&nbsp; **Sector:** `{sector}` &nbsp;|&nbsp; **Industry:** `{industry}`")

with head_col2:
    price_sign = "+" if change_abs >= 0 else ""
    st.metric(
        label=f"Current Price ({currency})",
        value=f"${curr_price:.2f}",
        delta=f"{price_sign}${change_abs:.2f} ({price_sign}{change_pct:.2f}%)"
    )

st.markdown("---")

# ----------------- PRIMARY NAVIGATION (SESSION-STATE PRESERVED) -----------------
if "active_nav_tab" not in st.session_state:
    st.session_state.active_nav_tab = "📊 Stock Analytics & Growth"

chosen_nav = st.segmented_control(
    "Navigation View:",
    options=["📊 Stock Analytics & Growth", "🎯 Option Buy Decision & P&L Simulator"],
    default=st.session_state.active_nav_tab,
    key="segmented_main_nav"
)
if chosen_nav and chosen_nav != st.session_state.active_nav_tab:
    st.session_state.active_nav_tab = chosen_nav
    st.rerun()

# ==============================================================================
# VIEW 1: STOCK ANALYTICS & GROWTH
# ==============================================================================
if st.session_state.active_nav_tab == "📊 Stock Analytics & Growth":
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        st.info(f"💡 Looking to evaluate options on **{active_ticker}**? Switch views above or click:")
    with col_nav2:
        if st.button("🎯 Open Option Simulator", key="btn_jump_to_opts", use_container_width=True, type="primary"):
            st.session_state.active_nav_tab = "🎯 Option Buy Decision & P&L Simulator"
            st.rerun()

    
    # Growth Metrics Cards
    st.subheader("📊 Stock Growth Summary")
    st.caption("Percentage return from the start of each period to current price:")

    g_col1, g_col2, g_col3, g_col4 = st.columns(4)

    # 1-Year Growth
    with g_col1:
        g1y = growth_metrics.get("1_year", {})
        if g1y.get("available"):
            pct = g1y["growth_pct"]
            badge_cls = "badge-green" if pct >= 0 else "badge-red"
            sign = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">1-Year Growth</div>
                <div class="metric-value-lg"><span class="{badge_cls}">{sign}{pct:.2f}%</span></div>
                <div class="metric-sub">Start: ${g1y['start_price']:.2f} ({g1y['start_date']})<br>Change: {sign}${g1y['change_dollar']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View 1Y Chart", key="btn_view_1y", use_container_width=True):
                set_timeframe("1Y")
                st.rerun()
        else:
            st.info("1-Year: Not enough history")

    # 6-Month Growth
    with g_col2:
        g6m = growth_metrics.get("6_month", {})
        if g6m.get("available"):
            pct = g6m["growth_pct"]
            badge_cls = "badge-green" if pct >= 0 else "badge-red"
            sign = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">6-Month Growth</div>
                <div class="metric-value-lg"><span class="{badge_cls}">{sign}{pct:.2f}%</span></div>
                <div class="metric-sub">Start: ${g6m['start_price']:.2f} ({g6m['start_date']})<br>Change: {sign}${g6m['change_dollar']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View 6M Chart", key="btn_view_6m", use_container_width=True):
                set_timeframe("6M")
                st.rerun()
        else:
            st.info("6-Month: Not enough history")

    # 3-Month Growth
    with g_col3:
        g3m = growth_metrics.get("3_month", {})
        if g3m.get("available"):
            pct = g3m["growth_pct"]
            badge_cls = "badge-green" if pct >= 0 else "badge-red"
            sign = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">3-Month Growth</div>
                <div class="metric-value-lg"><span class="{badge_cls}">{sign}{pct:.2f}%</span></div>
                <div class="metric-sub">Start: ${g3m['start_price']:.2f} ({g3m['start_date']})<br>Change: {sign}${g3m['change_dollar']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View 3M Chart", key="btn_view_3m", use_container_width=True):
                set_timeframe("3M")
                st.rerun()
        else:
            st.info("3-Month: Not enough history")

    # 1-Week Growth
    with g_col4:
        g1w = growth_metrics.get("1_week", {})
        if g1w.get("available"):
            pct = g1w["growth_pct"]
            badge_cls = "badge-green" if pct >= 0 else "badge-red"
            sign = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">1-Week Growth</div>
                <div class="metric-value-lg"><span class="{badge_cls}">{sign}{pct:.2f}%</span></div>
                <div class="metric-sub">Start: ${g1w['start_price']:.2f} ({g1w['start_date']})<br>Change: {sign}${g1w['change_dollar']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View 1W Chart", key="btn_view_1w", use_container_width=True):
                set_timeframe("1W")
                st.rerun()
        else:
            st.info("1-Week: Not enough history")

    # Trade Volume & Market Stats
    st.subheader("📦 Volume of Trade & Market Statistics")
    v_col1, v_col2, v_col3, v_col4 = st.columns(4)

    with v_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Today's Trade Volume</div>
            <div class="metric-value-lg">{volume_metrics['current_volume']:,}</div>
            <div class="metric-sub">Shares exchanged today</div>
        </div>
        """, unsafe_allow_html=True)

    with v_col2:
        rvol = volume_metrics["rvol_10d"]
        rvol_badge = "badge-green" if rvol >= 1.2 else ("badge-red" if rvol <= 0.8 else "badge-neutral")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Relative Volume (RVOL)</div>
            <div class="metric-value-lg"><span class="{rvol_badge}">{rvol:.2f}x</span></div>
            <div class="metric-sub">{volume_metrics['volume_status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with v_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">10-Day Avg Volume</div>
            <div class="metric-value-lg">{volume_metrics['avg_volume_10d']:,}</div>
            <div class="metric-sub">3-Month Avg: {volume_metrics['avg_volume_3m']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with v_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Dollar Volume Traded</div>
            <div class="metric-value-lg">${volume_metrics['dollar_volume']:,.0f}</div>
            <div class="metric-sub">Total capital traded today</div>
        </div>
        """, unsafe_allow_html=True)

    # Key valuation metrics row
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        mcap = stock_data["market_cap"]
        mcap_str = f"${mcap:,.0f}" if mcap else "N/A"
        if mcap and mcap >= 1e12:
            mcap_str = f"${mcap / 1e12:.2f} Trillion"
        elif mcap and mcap >= 1e9:
            mcap_str = f"${mcap / 1e9:.2f} Billion"
        st.metric("Market Cap", mcap_str)
    with m_col2:
        pe = stock_data["trailing_pe"]
        st.metric("P/E Ratio (TTM)", f"{pe:.2f}" if pe else "N/A")
    with m_col3:
        fpe = stock_data["forward_pe"]
        st.metric("Forward P/E", f"{fpe:.2f}" if fpe else "N/A")
    with m_col4:
        beta = stock_data["beta"]
        st.metric("Beta", f"{beta:.2f}" if beta else "N/A")
    with m_col5:
        st.metric(
            "52-Week Range",
            f"${stock_data['fifty_two_week_low']:.2f} - ${stock_data['fifty_two_week_high']:.2f}"
        )

    st.markdown("---")

    # Interactive Chart Section with Prominent Timeframe Selector
    st.subheader("📈 Stock Growth & Price Action")

    timeframes_list = ["1W", "1M", "3M", "6M", "1Y", "2Y", "5Y", "YTD"]
    current_tf = st.session_state.selected_timeframe
    if current_tf not in timeframes_list:
        current_tf = "6M"

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 1])

    with ctrl_col1:
        chosen_tf = st.segmented_control(
            "⏱️ Choose Timeframe:",
            options=timeframes_list,
            default=current_tf,
            key="segmented_tf_selector"
        )
        if chosen_tf and chosen_tf != st.session_state.selected_timeframe:
            set_timeframe(chosen_tf)
            st.rerun()

    with ctrl_col2:
        chart_view_mode = st.segmented_control(
            "📊 Chart Mode:",
            options=["📈 Growth Return (%)", "🕯️ Candlesticks ($)"],
            default="📈 Growth Return (%)",
            key="segmented_chart_mode"
        )

    with ctrl_col3:
        st.write("")
        st.write("")
        show_mas = st.checkbox("Show SMAs", value=True)

    active_tf = st.session_state.selected_timeframe
    df_slice = sc.get_growth_chart_data(hist, active_tf)

    if not df_slice.empty:
        p_start = df_slice["Close"].iloc[0]
        p_end = df_slice["Close"].iloc[-1]
        p_high = df_slice["High"].max()
        p_low = df_slice["Low"].min()
        p_ret = df_slice["Growth_Pct"].iloc[-1]
        p_ret_sign = "+" if p_ret >= 0 else ""
        p_color = "#059669" if p_ret >= 0 else "#DC2626"

        st.markdown(
            f"**Selected Timeframe ({active_tf}):** Start: **${p_start:.2f}** ➔ Current: **${p_end:.2f}** | "
            f"Return: <span style='color:{p_color}; font-weight:700; font-size:15px;'>{p_ret_sign}{p_ret:.2f}% (${p_ret_sign}{p_end - p_start:.2f})</span> | "
            f"Period High: **${p_high:.2f}** | Period Low: **${p_low:.2f}**",
            unsafe_allow_html=True
        )

        if chart_view_mode == "📈 Growth Return (%)":
            fig_main = charts.create_growth_chart(df_slice, active_ticker, active_tf)
        else:
            fig_main = charts.create_candlestick_chart(df_slice, active_ticker, show_ma=show_mas)

        st.plotly_chart(fig_main, use_container_width=True)
    else:
        st.warning(f"No price history available for timeframe '{active_tf}'.")

    st.markdown("---")

    # 2-Week Outlook Section
    st.subheader("🔮 2-Week Stock Outlook (Next 10 Trading Days)")
    st.caption("Multi-source intelligence synthesizing Wall Street consensus, short-term momentum, moving averages, and statistical volatility bounds.")

    verdict_border = outlook["verdict_color"]
    st.markdown(f"""
    <div class="decision-box-light" style="border-left-color: {verdict_border};">
        <div style="font-size: 20px; font-weight: 700; color: {verdict_border};">
            {outlook['verdict_icon']} 2-Week Outlook Verdict: {outlook['verdict']} (Score: {outlook['composite_score']:+d}/100)
        </div>
        <div style="font-size: 15px; color: #334155; margin-top: 6px;">
            {outlook['outlook_desc']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    out_col1, out_col2, out_col3 = st.columns(3)
    with out_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Projected 2-Week Target</div>
            <div class="metric-value-lg" style="color: {verdict_border};">
                ${outlook['projected_target_2w']:.2f} ({outlook['expected_change_pct']:+.2f}%)
            </div>
            <div class="metric-sub">Base-case trajectory over 10 trading days</div>
        </div>
        """, unsafe_allow_html=True)

    with out_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Expected 2-Week Trading Corridor</div>
            <div class="metric-value-lg">${outlook['expected_range_lower']:.2f} - ${outlook['expected_range_upper']:.2f}</div>
            <div class="metric-sub">Statistical 80% confidence channel (±1.5σ)</div>
        </div>
        """, unsafe_allow_html=True)

    with out_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">2-Week Expected Volatility</div>
            <div class="metric-value-lg">±{outlook['expected_volatility_2w_pct']:.2f}%</div>
            <div class="metric-sub">Derived from 20-day historical ATR & standard deviation</div>
        </div>
        """, unsafe_allow_html=True)

    cone_col, rat_col = st.columns([3, 2])

    with cone_col:
        fig_cone = charts.create_forecast_cone_chart(hist, outlook, active_ticker)
        st.plotly_chart(fig_cone, use_container_width=True)

    with rat_col:
        st.markdown("#### 🧠 Quantitative & Fundamental Rationale")
        for r in outlook["rationales"]:
            st.markdown(f"- {r}")

        st.markdown("#### 🏛️ Wall Street Consensus")
        if outlook.get("target_mean"):
            up_pct = outlook["analyst_upside_pct"]
            up_sign = "+" if up_pct and up_pct >= 0 else ""
            up_color = "#059669" if up_pct and up_pct >= 0 else "#DC2626"
            st.markdown(f"""
            - **Consensus Rating:** `{outlook['recommendation_key']}` ({outlook['num_analysts']} analyst opinions)
            - **Mean Target:** **${outlook['target_mean']:.2f}** (<span style='color:{up_color}; font-weight:600;'>{up_sign}{up_pct:.1f}% implied move</span>)
            - **Median Target:** ${outlook.get('target_median', 0):.2f}
            - **Range:** ${outlook.get('target_low', 0):.2f} (Low) ➔ ${outlook.get('target_high', 0):.2f} (High)
            """, unsafe_allow_html=True)
        else:
            st.write("No analyst targets available for this ticker.")

    st.markdown("---")

    # Quarterly Results Section
    st.subheader("📅 Quarterly Results Announcement & Stock Performance")
    st.caption("Earnings announcement dates, EPS consensus vs reported, and immediate post-announcement market reactions.")

    if quarterly.get("is_etf_or_fund"):
        st.info(f"ℹ️ {quarterly['message']}")
    else:
        q_col1, q_col2 = st.columns(2)

        with q_col1:
            st.markdown("### 🔔 Next Quarterly Results")
            next_q = quarterly.get("next_earnings")
            if next_q:
                countdown = next_q["days_until"]
                cd_badge = "badge-neutral" if countdown > 14 else "badge-green"
                eps_est_str = f"${next_q['eps_estimate']:.2f}" if next_q.get("eps_estimate") is not None else "Pending"
                timing_st = next_q.get("timing_status", "Scheduled by IR")
                prim_src = next_q.get("primary_source", "Yahoo Finance / LSEG Corporate Events")
                off_src = next_q.get("official_origin", "Company Investor Relations & SEC Filings")
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Expected Announcement Date</div>
                    <div class="metric-value-lg">{next_q['date']}</div>
                    <div style="margin-top: 8px;">
                        <span class="{cd_badge}">⏳ In ~{countdown} days</span>
                        &nbsp;&nbsp;<span style="font-size: 13px; font-weight: 600; color: #0284C7;">({timing_st})</span>
                    </div>
                    <div class="metric-sub" style="margin-top: 10px;">
                        • <b>Exact Datetime:</b> {next_q['datetime_full']}<br>
                        • <b>Consensus EPS Estimate:</b> {eps_est_str}<br>
                        • <b>Data Source:</b> {prim_src}<br>
                        • <b>Official Origin:</b> {off_src}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Next earnings date is not yet confirmed by the company.")

        with q_col2:
            st.markdown("### 📢 Last Quarterly Results & Performance")
            last_q = quarterly.get("last_earnings")
            if last_q:
                beat_cls = "badge-green" if last_q["beat_status"] == "Beat" else ("badge-red" if last_q["beat_status"] == "Miss" else "badge-neutral")
                surp_sign = "+" if last_q["surprise_pct"] and last_q["surprise_pct"] >= 0 else ""
                surp_str = f"({surp_sign}{last_q['surprise_pct']:.2f}% surprise)" if last_q.get("surprise_pct") is not None else ""
                
                p1 = last_q.get("perf_1d_pct")
                p1_sign = "+" if p1 and p1 >= 0 else ""
                p1_color = "#059669" if p1 and p1 >= 0 else "#DC2626"

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Announcement Date & Timing</div>
                    <div class="metric-value-lg">{last_q['date']}</div>
                    <div style="margin-top: 6px;">
                        <span class="{beat_cls}">{last_q['beat_status']} {surp_str}</span>
                        &nbsp;&nbsp;<span style="font-size: 13px; color: #64748B;">({last_q['timing']})</span>
                    </div>
                    <div class="metric-sub" style="margin-top: 10px;">
                        • <b>Reported EPS:</b> ${last_q.get('eps_reported', 0):.2f} vs Estimate: ${last_q.get('eps_estimate', 0):.2f}<br>
                        • <b>Prior Close:</b> ${last_q.get('prior_close', 0):.2f} ➔ <b>Reaction Close:</b> ${last_q.get('reaction_close', 0):.2f}
                    </div>
                    <hr style="border-color: #E2E8F0; margin: 10px 0;">
                    <div style="font-size: 16px; font-weight: 700; color: {p1_color};">
                        Immediate 1-Day Stock Performance: {p1_sign}{p1:.2f}%
                    </div>
                    <div class="metric-sub">
                        • <b>3-Day Reaction:</b> {('+' if last_q.get('perf_3d_pct', 0) >= 0 else '')}{last_q.get('perf_3d_pct', 0):.2f}%<br>
                        • <b>1-Week Reaction:</b> {('+' if last_q.get('perf_1w_pct', 0) >= 0 else '')}{last_q.get('perf_1w_pct', 0):.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Last quarterly results details not available.")

        hist_earnings = quarterly.get("historical_earnings", [])
        if hist_earnings:
            st.markdown("#### 📜 Historical Earnings Reactions (Past Quarters)")
            fig_earnings = charts.create_earnings_reaction_bar_chart(hist_earnings, active_ticker)
            st.plotly_chart(fig_earnings, use_container_width=True)

            table_rows = []
            for r in hist_earnings:
                p1_val = f"{r['perf_1d_pct']:+.2f}%" if r.get("perf_1d_pct") is not None else "N/A"
                p1w_val = f"{r['perf_1w_pct']:+.2f}%" if r.get("perf_1w_pct") is not None else "N/A"
                surp_val = f"{r['surprise_pct']:+.2f}%" if r.get("surprise_pct") is not None else "N/A"
                rep_val = f"${r['eps_reported']:.2f}" if r.get("eps_reported") is not None else "N/A"
                est_val = f"${r['eps_estimate']:.2f}" if r.get("eps_estimate") is not None else "N/A"
                
                table_rows.append({
                    "Earnings Date": r["date"],
                    "Timing": r["timing"],
                    "EPS Est": est_val,
                    "Reported EPS": rep_val,
                    "Surprise": surp_val,
                    "Result": r["beat_status"],
                    "1-Day Reaction": p1_val,
                    "1-Week Reaction": p1w_val
                })
                
            df_hist_q = pd.DataFrame(table_rows)
            st.dataframe(df_hist_q, use_container_width=True, hide_index=True)


# ==============================================================================
# VIEW 2: OPTION BUY DECISION & P&L SIMULATOR
# ==============================================================================
else:
    st.subheader(f"🎯 Option Purchase Decision & P&L Simulator for {active_ticker}")
    st.caption(
        f"Enter your strike price, bid/premium amount, and expiration date. "
        f"The engine calculates exact breakeven, P&L curves over time, probability of profit, and tells you whether to buy or avoid."
    )

    # Fetch available real-market expirations
    expirations_list = load_options_expirations(active_ticker)
    
    # Context Banner with 2-week outlook
    st.markdown(f"""
    <div style="background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 10px; padding: 12px 18px; margin-bottom: 20px;">
        <b>Current Stock Context:</b> Price = <b>${curr_price:.2f}</b> &nbsp;|&nbsp; 
        2-Week Outlook = <b style="color: {outlook['verdict_color']};">{outlook['verdict_icon']} {outlook['verdict']}</b> 
        (Score: {outlook['composite_score']:+d}/100) &nbsp;|&nbsp; 
        Expected 2-Week Volatility = <b>±{outlook['expected_volatility_2w_pct']:.2f}%</b>
    </div>
    """, unsafe_allow_html=True)

    # Option Inputs Card
    st.markdown("#### ⚙️ Option Contract Parameters")
    opt_in1, opt_in2, opt_in3 = st.columns(3)

    with opt_in1:
        opt_type_choice = st.segmented_control(
            "Option Type:",
            options=["CALL (Bullish)", "PUT (Bearish)"],
            default="CALL (Bullish)",
            key="opt_type_selector"
        )
        opt_type_clean = "call" if "CALL" in opt_type_choice else "put"

    with opt_in2:
        if expirations_list:
            # Format expirations with DTE
            today_d = date.today()
            exp_options = []
            exp_map = {}
            for e in expirations_list:
                try:
                    d_obj = datetime.strptime(e, "%Y-%m-%d").date()
                    dte_days = (d_obj - today_d).days
                    lbl = f"{e} ({dte_days} days to exp)"
                    exp_options.append(lbl)
                    exp_map[lbl] = e
                except Exception:
                    exp_options.append(e)
                    exp_map[e] = e
                    
            # Pick a default around 2 to 4 weeks
            def_idx = min(2, len(exp_options) - 1)
            selected_exp_lbl = st.selectbox(
                "Expiration Date:",
                options=exp_options,
                index=def_idx,
                key="opt_exp_selector"
            )
            chosen_expiration_str = exp_map[selected_exp_lbl]
        else:
            # Fallback date picker if no live options chain
            default_exp = (date.today() + timedelta(days=21))
            chosen_exp_date = st.date_input(
                "Expiration Date:",
                value=default_exp,
                min_value=date.today() + timedelta(days=1),
                key="opt_custom_date"
            )
            chosen_expiration_str = chosen_exp_date.strftime("%Y-%m-%d")

    with opt_in3:
        num_contracts = st.number_input(
            "Number of Contracts:",
            min_value=1,
            max_value=1000,
            value=1,
            step=1,
            help="1 standard option contract = 100 shares"
        )

    # Second row of inputs: Strike Price & Bid Amount
    opt_in4, opt_in5 = st.columns(2)

    with opt_in4:
        # Suggest default ATM strike
        suggested_strike = round(curr_price / 5.0) * 5.0
        strike_input = st.number_input(
            "Strike Price ($):",
            min_value=0.5,
            value=float(suggested_strike),
            step=2.5,
            format="%.2f",
            help="The price at which you can buy (Call) or sell (Put) the stock."
        )

    # Check live market quote if available
    live_chain = None
    market_bid = 0.0
    market_ask = 0.0
    market_iv = 0.28
    if expirations_list and chosen_expiration_str:
        try:
            live_chain = load_option_chain(active_ticker, chosen_expiration_str)
            target_list = live_chain["calls"] if opt_type_clean == "call" else live_chain["puts"]
            # Find matching strike
            matching_rows = [r for r in target_list if abs(r["strike"] - strike_input) < 0.25]
            if matching_rows:
                matched = matching_rows[0]
                market_bid = matched.get("bid", 0.0)
                market_ask = matched.get("ask", 0.0)
                if matched.get("iv", 0) > 0.02:
                    market_iv = matched["iv"]
        except Exception:
            pass

    with opt_in5:
        # Default bid suggestion
        suggested_bid = market_bid if market_bid > 0 else max(1.0, round(curr_price * 0.02, 2))
        bid_input = st.number_input(
            "Bid Amount / Premium Paid ($/share):",
            min_value=0.01,
            value=float(suggested_bid),
            step=0.25,
            format="%.2f",
            help="The price per share you pay for the option. Total contract cost = Bid × 100."
        )

    if market_bid > 0 or market_ask > 0:
        st.info(f"💡 **Live Market Reference for ${strike_input:.2f} {opt_type_clean.upper()} ({chosen_expiration_str}):** Bid: **${market_bid:.2f}** | Ask: **${market_ask:.2f}** | Implied Volatility (IV): **{market_iv*100:.1f}%**")

    st.markdown("---")

    # Run Option Evaluation Engine
    trade_eval = oc.analyze_option_trade(
        symbol=active_ticker,
        current_price=curr_price,
        option_type=opt_type_clean,
        strike=strike_input,
        bid_amount=bid_input,
        expiration_date_str=chosen_expiration_str,
        num_contracts=num_contracts,
        custom_iv=market_iv,
        outlook=outlook
    )

    # 1. "SHOULD I BUY THIS OPTION?" VERDICT BANNER
    st.subheader("🤖 Should You Buy This Option?")
    v_color = trade_eval["verdict_color"]
    st.markdown(f"""
    <div class="decision-box-light" style="border-left-color: {v_color};">
        <div style="font-size: 22px; font-weight: 800; color: {v_color};">
            {trade_eval['verdict_icon']} Recommendation: {trade_eval['verdict']} (Score: {trade_eval['verdict_score']:+d}/100)
        </div>
        <div style="font-size: 16px; color: #1E293B; margin-top: 8px; font-weight: 500;">
            {trade_eval['summary_text']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Rationale & Warning Columns
    chk_col1, chk_col2 = st.columns(2)
    with chk_col1:
        st.markdown("##### 📋 Decision Rationale Checklist")
        for r in trade_eval["rationales"]:
            st.markdown(f"- {r}")

    with chk_col2:
        st.markdown("##### ⚠️ Risk Warnings & Friction Points")
        if trade_eval["warnings"]:
            for w in trade_eval["warnings"]:
                st.markdown(f"- {w}")
        else:
            st.markdown("- ✅ No severe friction points detected. Hurdle and time decay are within reasonable bounds.")

    st.markdown("---")

    # 2. KEY METRICS SCORECARDS
    st.subheader("💵 Profit & Loss Summary Metrics")
    pnl_c1, pnl_c2, pnl_c3, pnl_c4, pnl_c5 = st.columns(5)

    with pnl_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Cost (Max Risk)</div>
            <div class="metric-value-lg" style="color: #DC2626;">${trade_eval['total_investment']:,.2f}</div>
            <div class="metric-sub">${trade_eval['bid_amount']:.2f}/share × {trade_eval['shares_controlled']} shares</div>
        </div>
        """, unsafe_allow_html=True)

    with pnl_c2:
        be_p = trade_eval['breakeven_price']
        req_p = trade_eval['move_to_breakeven_pct']
        be_badge = "badge-green" if req_p <= 3.0 else ("badge-neutral" if req_p <= 7.0 else "badge-red")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Breakeven Price</div>
            <div class="metric-value-lg">${be_p:.2f}</div>
            <div class="metric-sub">Required Move: <span class="{be_badge}">{('+' if req_p>=0 else '')}{req_p:.1f}%</span></div>
        </div>
        """, unsafe_allow_html=True)

    with pnl_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Max Profit Potential</div>
            <div class="metric-value-lg" style="color: #059669;">{trade_eval['max_profit_str']}</div>
            <div class="metric-sub">Upside: {trade_eval['max_profit_pct_str']}</div>
        </div>
        """, unsafe_allow_html=True)

    with pnl_c4:
        pop_badge = "badge-green" if trade_eval['pop'] >= 45 else ("badge-neutral" if trade_eval['pop'] >= 30 else "badge-red")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Probability of Profit</div>
            <div class="metric-value-lg"><span class="{pop_badge}">{trade_eval['pop']:.1f}%</span></div>
            <div class="metric-sub">Odds of stock beating breakeven</div>
        </div>
        """, unsafe_allow_html=True)

    with pnl_c5:
        th = trade_eval['greeks']['theta_daily_total']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Daily Theta Decay</div>
            <div class="metric-value-lg" style="color: #DC2626;">-${abs(th):.2f} / day</div>
            <div class="metric-sub">Time decay loss per day ({trade_eval['dte']} DTE)</div>
        </div>
        """, unsafe_allow_html=True)

    # Greeks Sub-Row
    gr_c1, gr_c2, gr_c3, gr_c4 = st.columns(4)
    with gr_c1:
        st.metric("Delta (Δ)", f"{trade_eval['greeks']['delta']:.3f}", help="Price move of option per $1 move in stock.")
    with gr_c2:
        st.metric("Gamma (Γ)", f"{trade_eval['greeks']['gamma']:.4f}", help="Rate of change in Delta per $1 move in stock.")
    with gr_c3:
        st.metric("Vega (ν)", f"${trade_eval['greeks']['vega']:.2f}", help="$ change per 1% change in Implied Volatility.")
    with gr_c4:
        st.metric("Implied Volatility (IV)", f"{trade_eval['iv']:.1f}%", help="Annualized expected volatility priced into this option.")

    st.markdown("---")

    # 3. INTERACTIVE P&L SIMULATION CHART
    st.subheader(f"📉 Profit & Loss Chart Across Stock Prices ({trade_eval['expiration_date']})")
    st.caption("Visualizes total dollar gain or loss at Expiration (0 DTE), Halfway to Expiration (50% DTE), and Today (T+0).")

    fig_pnl = charts.create_options_pnl_chart(trade_eval)
    st.plotly_chart(fig_pnl, use_container_width=True)

    st.markdown("---")

    # 4. SCENARIO MATRIX TABLE
    st.subheader("📑 Expiration P&L Scenario Matrix")
    st.caption("How your investment performs across various stock prices on the expiration date:")

    matrix_rows = []
    for sc_row in trade_eval["scenarios"]:
        p_val = sc_row["stock_price"]
        chg_val = f"{sc_row['stock_change_pct']:+.1f}%"
        opt_v = f"${sc_row['option_val_exp']:.2f}"
        pnl_v = f"{('+' if sc_row['pnl_exp_dollar']>=0 else '')}${sc_row['pnl_exp_dollar']:,.2f}"
        roi_v = f"{('+' if sc_row['roi_exp_pct']>=0 else '')}{sc_row['roi_exp_pct']:.1f}%"
        status_lbl = sc_row["label"]

        matrix_rows.append({
            "Stock Price ($)": f"${p_val:.2f}",
            "Stock Move (%)": chg_val,
            "Option Value ($)": opt_v,
            "Net Profit/Loss ($)": pnl_v,
            "Return on Investment (ROI)": roi_v,
            "Key Benchmark": status_lbl
        })

    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"Stock & Option Analysis System • Real-time intelligence for {active_ticker} • Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
