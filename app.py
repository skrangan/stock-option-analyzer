"""
app.py - Stock Analysis Web Application
Light-themed, modern, responsive financial dashboard with prominent timeframe controls.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import stock_core as sc
import charts

# Configure page settings
st.set_page_config(
    page_title="Stock Analyzer & Forecast",
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
    
    /* Outlook Box */
    .outlook-box-light {
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 22px;
        border: 1px solid #E2E8F0;
        border-left: 6px solid;
        background-color: #F8FAFC;
    }
    
    /* Timeframe Toolbar Container */
    .timeframe-toolbar {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Session State for Timeframe & Ticker
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
    st.title("📈 Stock Analyzer")
    st.caption("Real-time stats, growth, volume, 2-week outlook & quarterly results")
    
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
    st.markdown("### ℹ️ About Application")
    st.markdown("""
    - **Light Theme Active**: Designed for high contrast and readability.
    - **Timeframe Selector**: Positioned right above the chart on the main screen for one-click switching.
    - **Outlook Engine**: Synthesizes Wall Street analyst targets, RSI, MACD, and statistical volatility.
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

# ----------------- GROWTH METRICS CARDS (LIGHT THEME) -----------------
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

# ----------------- TRADE VOLUME & MARKET STATS (LIGHT THEME) -----------------
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

# ----------------- PROMINENT TIMEFRAME & INTERACTIVE CHART SECTION -----------------
st.subheader("📈 Stock Growth & Price Action")

# PROMINENT MAIN-PAGE TIMEFRAME SELECTION BAR
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
    st.write("") # Spacer
    st.write("") # Spacer
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

# ----------------- 2-WEEK OUTLOOK SECTION (LIGHT THEME) -----------------
st.subheader("🔮 2-Week Stock Outlook (Next 10 Trading Days)")
st.caption("Multi-source intelligence synthesizing Wall Street consensus, short-term momentum, moving averages, and statistical volatility bounds.")

# Light Verdict Box
verdict_border = outlook["verdict_color"]
st.markdown(f"""
<div class="outlook-box-light" style="border-left-color: {verdict_border};">
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

# ----------------- QUARTERLY RESULTS & PERFORMANCE SECTION (LIGHT THEME) -----------------
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
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Expected Announcement Date</div>
                <div class="metric-value-lg">{next_q['date']}</div>
                <div style="margin-top: 8px;">
                    <span class="{cd_badge}">⏳ In ~{countdown} days</span>
                </div>
                <div class="metric-sub" style="margin-top: 10px;">
                    • <b>Exact Datetime:</b> {next_q['datetime_full']}<br>
                    • <b>Consensus EPS Estimate:</b> {eps_est_str}
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

st.markdown("---")
st.caption(f"Stock Analysis Application • Real-time intelligence for {active_ticker} • Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
