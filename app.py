"""
app.py - Stock Analysis Web Application
Built with Streamlit, Plotly, and yfinance.
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

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 4px;
    }
    .metric-value-lg {
        font-size: 26px;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 12px;
        color: #64748B;
        margin-top: 4px;
    }
    .badge-green {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }
    .badge-red {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }
    .badge-neutral {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }
    .outlook-box {
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
        border-left: 6px solid;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.title("📈 Stock Analyzer")
    st.caption("Comprehensive growth, volume, 2-week outlook & earnings analysis")
    
    st.markdown("### 🔍 Enter Ticker Symbol")
    
    # Session state for ticker input
    if "ticker_input" not in st.session_state:
        st.session_state.ticker_input = "AAPL"
        
    def set_ticker(sym):
        st.session_state.ticker_input = sym

    # Popular Tickers Quick Selector
    st.write("Popular Tickers:")
    cols_chips = st.columns(4)
    chips = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "SPY"]
    for idx, c in enumerate(chips):
        col_idx = idx % 4
        with cols_chips[col_idx]:
            if st.button(c, key=f"btn_{c}", use_container_width=True):
                set_ticker(c)
                
    ticker_sym = st.text_input(
        "Ticker Symbol",
        value=st.session_state.ticker_input,
        key="main_ticker_text",
        placeholder="e.g. AAPL, NVDA, TSLA..."
    ).strip().upper()

    st.markdown("---")
    st.markdown("### ⚙️ Chart Settings")
    selected_period = st.select_slider(
        "Time Range for Growth Chart",
        options=["1W", "1M", "3M", "6M", "1Y", "2Y", "5Y", "YTD"],
        value="6M"
    )
    chart_view = st.radio(
        "Chart View Mode",
        options=["📈 Cumulative Growth (%)", "🕯️ Candlesticks & Moving Averages ($)"],
        index=0
    )
    show_mas = st.checkbox("Show 20/50/200 Day Moving Averages", value=True)
    
    st.markdown("---")
    st.caption("Data source: Real-time & daily market data via Yahoo Finance API.")
    st.caption("Predictions are quantitative models and not financial advice.")

# ----------------- MAIN APP EXECUTION -----------------
if not ticker_sym:
    st.info("👈 Please enter or select a ticker symbol in the sidebar.")
    st.stop()

# Fetch data with cache
@st.cache_data(ttl=120)
def load_data(symbol: str):
    return sc.get_stock_data(symbol)

try:
    with st.spinner(f"Fetching real-time data and stats for {ticker_sym}..."):
        stock_data = load_data(ticker_sym)
except Exception as e:
    st.error(f"❌ Could not load data for ticker **'{ticker_sym}'**: {e}")
    st.info("Please verify the ticker symbol (e.g. AAPL, MSFT, NVDA, SPY).")
    st.stop()

# Unpack core data
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

# Calculate core metrics
growth_metrics = sc.calculate_growth_metrics(hist, curr_price)
volume_metrics = sc.calculate_volume_metrics(hist, curr_price, stock_data["info"])
outlook = sc.calculate_two_week_outlook(hist, stock_data["ticker_obj"], curr_price, stock_data["info"])
quarterly = sc.calculate_quarterly_results(stock_data["ticker_obj"], hist)

# ----------------- HEADER SECTION -----------------
head_col1, head_col2 = st.columns([3, 2])
with head_col1:
    st.title(f"{short_name} ({ticker_sym})")
    st.markdown(f"**Exchange:** `{exchange}` &nbsp;|&nbsp; **Sector:** `{sector}` &nbsp;|&nbsp; **Industry:** `{industry}`")

with head_col2:
    delta_color = "normal" if change_abs >= 0 else "inverse"
    price_sign = "+" if change_abs >= 0 else ""
    st.metric(
        label=f"Current Price ({currency})",
        value=f"${curr_price:.2f}",
        delta=f"{price_sign}${change_abs:.2f} ({price_sign}{change_pct:.2f}%)"
    )

st.markdown("---")

# ----------------- GROWTH METRICS CARDS -----------------
st.subheader("📊 Stock Growth Summary")
st.caption("Percentage return from the start of each period to the current price:")

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
    else:
        st.info("1-Week: Not enough history")

# ----------------- TRADE VOLUME & CURRENT STATS -----------------
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

# ----------------- INTERACTIVE CHART SECTION -----------------
st.subheader(f"📈 Stock Growth & Price Action ({selected_period})")

df_slice = sc.get_growth_chart_data(hist, selected_period)

if not df_slice.empty:
    # Summary banner for selected period
    p_start = df_slice["Close"].iloc[0]
    p_end = df_slice["Close"].iloc[-1]
    p_high = df_slice["High"].max()
    p_low = df_slice["Low"].min()
    p_ret = df_slice["Growth_Pct"].iloc[-1]
    p_ret_sign = "+" if p_ret >= 0 else ""
    p_color = "#10B981" if p_ret >= 0 else "#EF4444"

    st.markdown(
        f"**Selected Period Performance:** Start: **${p_start:.2f}** ➔ Current: **${p_end:.2f}** | "
        f"Return: <span style='color:{p_color}; font-weight:700;'>{p_ret_sign}{p_ret:.2f}% (${p_ret_sign}{p_end - p_start:.2f})</span> | "
        f"Period High: **${p_high:.2f}** | Period Low: **${p_low:.2f}**",
        unsafe_allow_html=True
    )

    if "Cumulative Growth" in chart_view:
        fig_main = charts.create_growth_chart(df_slice, ticker_sym, selected_period)
    else:
        fig_main = charts.create_candlestick_chart(df_slice, ticker_sym, show_ma=show_mas)

    st.plotly_chart(fig_main, use_container_width=True)
else:
    st.warning("No price history available for the selected period.")

st.markdown("---")

# ----------------- 2-WEEK OUTLOOK SECTION -----------------
st.subheader("🔮 2-Week Stock Outlook (Next 10 Trading Days)")
st.caption("Multi-source intelligence synthesizing Wall Street consensus, short-term momentum, moving averages, and statistical volatility bounds.")

# Verdict Box
box_bg = "rgba(16, 185, 129, 0.08)" if outlook["composite_score"] >= 20 else ("rgba(239, 68, 68, 0.08)" if outlook["composite_score"] <= -20 else "rgba(245, 158, 11, 0.08)")
st.markdown(f"""
<div class="outlook-box" style="background: {box_bg}; border-color: {outlook['verdict_color']};">
    <div style="font-size: 20px; font-weight: 700; color: {outlook['verdict_color']};">
        {outlook['verdict_icon']} 2-Week Outlook Verdict: {outlook['verdict']} (Score: {outlook['composite_score']:+d}/100)
    </div>
    <div style="font-size: 15px; color: #E2E8F0; margin-top: 6px;">
        {outlook['outlook_desc']}
    </div>
</div>
""", unsafe_allow_html=True)

out_col1, out_col2, out_col3 = st.columns(3)
with out_col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Projected 2-Week Target</div>
        <div class="metric-value-lg" style="color: {outlook['verdict_color']};">
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

# 2-Week Forecast Cone Chart & Rationale Side-by-Side
cone_col, rat_col = st.columns([3, 2])

with cone_col:
    fig_cone = charts.create_forecast_cone_chart(hist, outlook, ticker_sym)
    st.plotly_chart(fig_cone, use_container_width=True)

with rat_col:
    st.markdown("#### 🧠 Quantitative & Fundamental Rationale")
    for r in outlook["rationales"]:
        st.markdown(f"- {r}")

    # Wall Street Analyst breakdown
    st.markdown("#### 🏛️ Wall Street Consensus")
    if outlook.get("target_mean"):
        up_pct = outlook["analyst_upside_pct"]
        up_sign = "+" if up_pct and up_pct >= 0 else ""
        up_color = "#10B981" if up_pct and up_pct >= 0 else "#EF4444"
        st.markdown(f"""
        - **Consensus Rating:** `{outlook['recommendation_key']}` ({outlook['num_analysts']} analyst opinions)
        - **Mean Target:** **${outlook['target_mean']:.2f}** (<span style='color:{up_color}; font-weight:600;'>{up_sign}{up_pct:.1f}% implied move</span>)
        - **Median Target:** ${outlook.get('target_median', 0):.2f}
        - **Range:** ${outlook.get('target_low', 0):.2f} (Low) ➔ ${outlook.get('target_high', 0):.2f} (High)
        """, unsafe_allow_html=True)
    else:
        st.write("No analyst targets available for this ticker.")

st.markdown("---")

# ----------------- QUARTERLY RESULTS & PERFORMANCE SECTION -----------------
st.subheader("📅 Quarterly Results Announcement & Stock Performance")
st.caption("Earnings announcement dates, EPS consensus vs reported, and immediate post-announcement market reactions.")

if quarterly.get("is_etf_or_fund"):
    st.info(f"ℹ️ {quarterly['message']}")
else:
    q_col1, q_col2 = st.columns(2)

    # Next Quarterly Announcement
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

    # Last Quarterly Announcement & Post-Announcement Reaction
    with q_col2:
        st.markdown("### 📢 Last Quarterly Results & Performance")
        last_q = quarterly.get("last_earnings")
        if last_q:
            beat_cls = "badge-green" if last_q["beat_status"] == "Beat" else ("badge-red" if last_q["beat_status"] == "Miss" else "badge-neutral")
            surp_sign = "+" if last_q["surprise_pct"] and last_q["surprise_pct"] >= 0 else ""
            surp_str = f"({surp_sign}{last_q['surprise_pct']:.2f}% surprise)" if last_q.get("surprise_pct") is not None else ""
            
            p1 = last_q.get("perf_1d_pct")
            p1_sign = "+" if p1 and p1 >= 0 else ""
            p1_color = "#10B981" if p1 and p1 >= 0 else "#EF4444"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Announcement Date & Timing</div>
                <div class="metric-value-lg">{last_q['date']}</div>
                <div style="margin-top: 6px;">
                    <span class="{beat_cls}">{last_q['beat_status']} {surp_str}</span>
                    &nbsp;&nbsp;<span style="font-size: 13px; color: #94A3B8;">({last_q['timing']})</span>
                </div>
                <div class="metric-sub" style="margin-top: 10px;">
                    • <b>Reported EPS:</b> ${last_q.get('eps_reported', 0):.2f} vs Estimate: ${last_q.get('eps_estimate', 0):.2f}<br>
                    • <b>Prior Close:</b> ${last_q.get('prior_close', 0):.2f} ➔ <b>Reaction Close:</b> ${last_q.get('reaction_close', 0):.2f}
                </div>
                <hr style="border-color: rgba(148, 163, 184, 0.2); margin: 10px 0;">
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

    # Historical Earnings Reaction Chart & Table
    hist_earnings = quarterly.get("historical_earnings", [])
    if hist_earnings:
        st.markdown("#### 📜 Historical Earnings Reactions (Past Quarters)")
        fig_earnings = charts.create_earnings_reaction_bar_chart(hist_earnings, ticker_sym)
        st.plotly_chart(fig_earnings, use_container_width=True)

        # Tabular breakdown
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
st.caption(f"Stock Analysis Application • Real-time intelligence for {ticker_sym} • Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
