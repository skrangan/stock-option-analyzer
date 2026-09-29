"""
charts.py - Interactive Plotly charts with a modern, crisp LIGHT THEME
for stock performance, percentage growth, 2-week forward forecast cone, and quarterly earnings reactions.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_growth_chart(df: pd.DataFrame, ticker_symbol: str, period_label: str) -> go.Figure:
    """
    Create a percentage growth chart showing cumulative return (%) from the start of the period.
    Rendered with a clean, light color scheme.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for this period", showarrow=False, font=dict(color="#475569"))
        return fig

    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    total_return_pct = df["Growth_Pct"].iloc[-1]
    
    line_color = "#059669" if total_return_pct >= 0 else "#DC2626"
    fill_color = "rgba(5, 150, 105, 0.08)" if total_return_pct >= 0 else "rgba(220, 38, 38, 0.08)"

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.75, 0.25],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # Growth % Line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Growth_Pct"],
            mode="lines",
            name=f"{ticker_symbol} Growth %",
            line=dict(color=line_color, width=2.5),
            fill="tozeroy",
            fillcolor=fill_color,
            customdata=df["Close"],
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Growth: <b>%{y:+.2f}%</b><br>Price: $%{customdata:.2f}<extra></extra>"
        ),
        row=1, col=1
    )

    # Zero baseline
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#94A3B8",
        line_width=1.2,
        row=1, col=1
    )

    # Volume subplot
    vol_colors = [
        "#059669" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#DC2626"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.65),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: %{y:,.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    if "Vol_SMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Vol_SMA_20"],
                mode="lines",
                name="20D Avg Vol",
                line=dict(color="#D97706", width=1.5, dash="dot"),
                hoverinfo="skip"
            ),
            row=2, col=1
        )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=55, r=20, t=50, b=30),
        height=520,
        title=dict(
            text=f"<b>{ticker_symbol} Cumulative Growth ({period_label})</b> &nbsp;&nbsp; "
                 f"<span style='color:{line_color}; font-size:16px;'>{total_return_pct:+.2f}% (${start_price:.2f} ➔ ${end_price:.2f})</span>",
            font=dict(size=17, color="#0F172A")
        ),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            tickfont=dict(color="#475569")
        ),
        xaxis2=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            tickfont=dict(color="#475569")
        ),
        yaxis=dict(
            title="Return (%)",
            ticksuffix="%",
            showgrid=True,
            gridcolor="#E2E8F0",
            titlefont=dict(color="#334155"),
            tickfont=dict(color="#475569")
        ),
        yaxis2=dict(
            title="Volume",
            showgrid=True,
            gridcolor="#E2E8F0",
            titlefont=dict(color="#334155"),
            tickfont=dict(color="#475569")
        )
    )

    return fig

def create_candlestick_chart(df: pd.DataFrame, ticker_symbol: str, show_ma: bool = True) -> go.Figure:
    """
    Create a professional Candlestick chart in Light Mode with Moving Averages and Volume bars.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False, font=dict(color="#475569"))
        return fig

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.75, 0.25]
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#059669",
            increasing_fillcolor="#059669",
            decreasing_line_color="#DC2626",
            decreasing_fillcolor="#DC2626"
        ),
        row=1, col=1
    )

    # Moving averages
    if show_ma:
        if "SMA_20" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["SMA_20"],
                    mode="lines", name="20 SMA",
                    line=dict(color="#0284C7", width=1.6)
                ),
                row=1, col=1
            )
        if "SMA_50" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["SMA_50"],
                    mode="lines", name="50 SMA",
                    line=dict(color="#D97706", width=1.6)
                ),
                row=1, col=1
            )
        if "SMA_200" in df.columns and df["SMA_200"].dropna().shape[0] > 0:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["SMA_200"],
                    mode="lines", name="200 SMA",
                    line=dict(color="#7C3AED", width=1.6)
                ),
                row=1, col=1
            )

    # Volume Subplot
    vol_colors = [
        "#059669" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#DC2626"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.65),
            hovertemplate="Volume: %{y:,.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=55, r=20, t=50, b=30),
        height=540,
        title=dict(
            text=f"<b>{ticker_symbol} Candlestick & Volume Chart</b>",
            font=dict(size=17, color="#0F172A")
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickfont=dict(color="#475569")),
        xaxis2=dict(showgrid=True, gridcolor="#E2E8F0", tickfont=dict(color="#475569")),
        yaxis=dict(title="Price ($)", showgrid=True, gridcolor="#E2E8F0", titlefont=dict(color="#334155"), tickfont=dict(color="#475569")),
        yaxis2=dict(title="Volume", showgrid=True, gridcolor="#E2E8F0", titlefont=dict(color="#334155"), tickfont=dict(color="#475569")),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#334155")
        )
    )

    return fig

def create_forecast_cone_chart(hist: pd.DataFrame, outlook_data: dict, ticker_symbol: str) -> go.Figure:
    """
    Create a 2-Week forward forecast projection cone chart in Light Mode.
    """
    recent_hist = hist.tail(30).copy()
    forward_pts = outlook_data.get("forward_projection", [])
    
    if not forward_pts or recent_hist.empty:
        fig = go.Figure()
        fig.add_annotation(text="Forecast cone data unavailable", showarrow=False, font=dict(color="#475569"))
        return fig
        
    last_dt = recent_hist.index[-1].strftime("%Y-%m-%d")
    curr_price = outlook_data["current_price"]
    
    forecast_dates = [last_dt] + [pt["date"] for pt in forward_pts]
    forecast_expected = [curr_price] + [pt["expected"] for pt in forward_pts]
    forecast_upper = [curr_price] + [pt["upper"] for pt in forward_pts]
    forecast_lower = [curr_price] + [pt["lower"] for pt in forward_pts]

    fig = go.Figure()

    # 1. Recent Historical Close Line
    fig.add_trace(
        go.Scatter(
            x=[d.strftime("%Y-%m-%d") for d in recent_hist.index],
            y=recent_hist["Close"],
            mode="lines",
            name="Actual Close",
            line=dict(color="#0284C7", width=2.5),
            hovertemplate="<b>%{x}</b><br>Actual Price: $%{y:.2f}<extra></extra>"
        )
    )

    # 2. Upper Bound Line
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_upper,
            mode="lines",
            name="Upper Range (+1.5σ)",
            line=dict(color="#059669", width=1.5, dash="dash"),
            hovertemplate="<b>%{x}</b><br>Upper Bound: $%{y:.2f}<extra></extra>"
        )
    )

    # 3. Lower Bound Line with Fill
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_lower,
            mode="lines",
            name="Lower Range (-1.5σ)",
            line=dict(color="#DC2626", width=1.5, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(37, 99, 235, 0.08)",
            hovertemplate="<b>%{x}</b><br>Lower Bound: $%{y:.2f}<extra></extra>"
        )
    )

    # 4. Projected Center Target
    verdict_color = outlook_data.get("verdict_color", "#2563EB")
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_expected,
            mode="lines+markers",
            name="2-Week Target Trajectory",
            line=dict(color=verdict_color, width=3, dash="dot"),
            marker=dict(size=5, color=verdict_color),
            hovertemplate="<b>%{x}</b><br>Expected Path: $%{y:.2f}<extra></extra>"
        )
    )

    # Vertical line dividing history and forecast
    fig.add_vline(
        x=last_dt,
        line_width=1.5,
        line_dash="solid",
        line_color="#64748B"
    )

    fig.add_annotation(
        x=last_dt,
        y=curr_price,
        text=" Today",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#64748B",
        font=dict(color="#0F172A", size=12)
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=55, r=20, t=50, b=30),
        height=450,
        title=dict(
            text=f"<b>{ticker_symbol} 2-Week Forward Forecast Cone (10 Trading Days)</b>",
            font=dict(size=17, color="#0F172A")
        ),
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickfont=dict(color="#475569")),
        yaxis=dict(title="Price ($)", showgrid=True, gridcolor="#E2E8F0", titlefont=dict(color="#334155"), tickfont=dict(color="#475569")),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#334155")
        ),
        hovermode="x unified"
    )

    return fig

def create_earnings_reaction_bar_chart(historical_earnings: list, ticker_symbol: str) -> go.Figure:
    """
    Create a bar chart comparing past quarterly earnings announcement reactions in Light Mode.
    """
    valid_records = [
        r for r in historical_earnings 
        if r.get("has_reaction") and r.get("perf_1d_pct") is not None
    ]
    
    if not valid_records:
        fig = go.Figure()
        fig.add_annotation(text="No post-earnings price reaction data available", showarrow=False, font=dict(color="#475569"))
        return fig
        
    valid_records = list(reversed(valid_records))
    dates = [r["date"] for r in valid_records]
    p1_vals = [r["perf_1d_pct"] for r in valid_records]
    p1w_vals = [r.get("perf_1w_pct", 0) or 0 for r in valid_records]

    fig = go.Figure()

    # 1-Day Reaction
    bar_colors_1d = ["#059669" if v >= 0 else "#DC2626" for v in p1_vals]
    fig.add_trace(
        go.Bar(
            x=dates,
            y=p1_vals,
            name="1-Day Stock Reaction (%)",
            marker=dict(color=bar_colors_1d),
            text=[f"{v:+.1f}%" for v in p1_vals],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>1-Day Reaction: <b>%{y:+.2f}%</b><extra></extra>"
        )
    )

    # 1-Week Reaction
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=p1w_vals,
            name="1-Week Cumulative (%)",
            mode="lines+markers",
            line=dict(color="#D97706", width=2.5),
            marker=dict(size=8, color="#D97706"),
            hovertemplate="<b>%{x}</b><br>1-Week Reaction: <b>%{y:+.2f}%</b><extra></extra>"
        )
    )

    fig.add_hline(y=0, line_dash="solid", line_color="#94A3B8", line_width=1)

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=55, r=20, t=50, b=30),
        height=380,
        title=dict(
            text=f"<b>{ticker_symbol} Historical Earnings Announcement Price Reactions</b>",
            font=dict(size=17, color="#0F172A")
        ),
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickfont=dict(color="#475569")),
        yaxis=dict(
            title="Stock Performance (%)",
            ticksuffix="%",
            showgrid=True,
            gridcolor="#E2E8F0",
            titlefont=dict(color="#334155"),
            tickfont=dict(color="#475569")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#334155")
        )
    )

    return fig

def create_options_pnl_chart(trade_data: dict) -> go.Figure:
    """
    Create an interactive Profit & Loss (P&L) curve chart across underlying stock prices
    for an option purchase (Call or Put) in Light Mode.
    Shows At Expiration (0 DTE), Halfway to Expiration (50% DTE), and Today (T+0).
    """
    curve = trade_data["curve_data"]
    prices = curve["prices"]
    pnl_exp = curve["pnl_exp"]
    pnl_half = curve["pnl_halfway"]
    pnl_today = curve["pnl_today"]

    curr_p = trade_data["current_price"]
    strike_p = trade_data["strike"]
    be_p = trade_data["breakeven_price"]
    opt_type = trade_data["option_type"]
    symbol = trade_data["symbol"]
    tot_inv = trade_data["total_investment"]

    fig = go.Figure()

    # Zero P&L horizontal reference
    fig.add_hline(
        y=0,
        line_width=1.5,
        line_color="#475569",
        line_dash="solid"
    )

    # 1. P&L at Expiration (Solid line)
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl_exp,
            mode="lines",
            name="At Expiration (0 DTE)",
            line=dict(color="#0F172A", width=3),
            hovertemplate="<b>Stock: $%{x:.2f}</b><br>P&L at Expiration: <b>$%{y:,.2f}</b><extra></extra>"
        )
    )

    # 2. P&L Halfway to Expiration (Dashed line)
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl_half,
            mode="lines",
            name=f"Halfway to Exp ({trade_data['dte'] // 2} DTE)",
            line=dict(color="#2563EB", width=2, dash="dash"),
            hovertemplate="<b>Stock: $%{x:.2f}</b><br>P&L Halfway: <b>$%{y:,.2f}</b><extra></extra>"
        )
    )

    # 3. P&L Today (T+0) (Dotted line)
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl_today,
            mode="lines",
            name="Today (T+0)",
            line=dict(color="#8B5CF6", width=2, dash="dot"),
            hovertemplate="<b>Stock: $%{x:.2f}</b><br>P&L Today: <b>$%{y:,.2f}</b><extra></extra>"
        )
    )

    # Vertical line: Current Stock Price
    fig.add_vline(
        x=curr_p,
        line_width=1.5,
        line_dash="dash",
        line_color="#64748B",
        annotation_text=f"Current: ${curr_p:.2f}",
        annotation_position="top left",
        annotation_font=dict(color="#334155", size=11)
    )

    # Vertical line: Strike Price
    fig.add_vline(
        x=strike_p,
        line_width=1.5,
        line_dash="dot",
        line_color="#D97706",
        annotation_text=f"Strike: ${strike_p:.2f}",
        annotation_position="bottom left",
        annotation_font=dict(color="#D97706", size=11)
    )

    # Vertical line: Breakeven Price
    be_color = "#059669" if opt_type == "CALL" else "#DC2626"
    fig.add_vline(
        x=be_p,
        line_width=2,
        line_dash="dash",
        line_color=be_color,
        annotation_text=f"Breakeven: ${be_p:.2f}",
        annotation_position="top right",
        annotation_font=dict(color=be_color, size=12, family="sans-serif")
    )

    # Shade Profit / Loss zones
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        margin=dict(l=55, r=20, t=55, b=35),
        height=480,
        title=dict(
            text=f"<b>{symbol} ${strike_p:.2f} {opt_type} P&L Simulation ({trade_data['expiration_date']})</b> &nbsp;&nbsp; "
                 f"<span style='font-size:14px; color:#64748B;'>Investment: ${tot_inv:,.2f} | Breakeven: ${be_p:.2f}</span>",
            font=dict(size=17, color="#0F172A")
        ),
        xaxis=dict(
            title="Underlying Stock Price ($)",
            showgrid=True,
            gridcolor="#E2E8F0",
            titlefont=dict(color="#334155"),
            tickfont=dict(color="#475569")
        ),
        yaxis=dict(
            title="Total Profit / Loss ($)",
            showgrid=True,
            gridcolor="#E2E8F0",
            titlefont=dict(color="#334155"),
            tickfont=dict(color="#475569"),
            zeroline=True,
            zerolinecolor="#475569",
            zerolinewidth=1.5
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#334155")
        ),
        hovermode="x unified"
    )

    return fig

