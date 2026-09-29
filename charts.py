"""
charts.py - Interactive Plotly charts for stock performance, percentage growth,
2-week forward forecast cone, and quarterly earnings reactions.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_growth_chart(df: pd.DataFrame, ticker_symbol: str, period_label: str) -> go.Figure:
    """
    Create a percentage growth chart showing cumulative return (%) from the start of the period.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for this period", showarrow=False)
        return fig

    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    total_return_pct = df["Growth_Pct"].iloc[-1]
    
    line_color = "#10B981" if total_return_pct >= 0 else "#EF4444"
    fill_color = "rgba(16, 185, 129, 0.12)" if total_return_pct >= 0 else "rgba(239, 68, 68, 0.12)"

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
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
        line_color="#64748B",
        line_width=1.2,
        row=1, col=1
    )

    # Volume subplot
    vol_colors = [
        "#10B981" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#EF4444"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.7),
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
                line=dict(color="#F59E0B", width=1.5, dash="dot"),
                hoverinfo="skip"
            ),
            row=2, col=1
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0)",
        plot_bgcolor="rgba(30, 41, 59, 0.4)",
        margin=dict(l=50, r=20, t=40, b=30),
        height=520,
        title=dict(
            text=f"<b>{ticker_symbol} Cumulative Growth ({period_label})</b> &nbsp;&nbsp; "
                 f"<span style='color:{line_color}; font-size:16px;'>{total_return_pct:+.2f}% (${start_price:.2f} ➔ ${end_price:.2f})</span>",
            font=dict(size=18, color="#F8FAFC")
        ),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        xaxis2=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        yaxis=dict(
            title="Return (%)",
            ticksuffix="%",
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)"
        ),
        yaxis2=dict(
            title="Volume",
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.1)"
        )
    )

    return fig

def create_candlestick_chart(df: pd.DataFrame, ticker_symbol: str, show_ma: bool = True) -> go.Figure:
    """
    Create a professional Candlestick chart with Moving Averages and Volume bars.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
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
            increasing_line_color="#10B981",
            decreasing_line_color="#EF4444"
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
                    line=dict(color="#38BDF8", width=1.5)
                ),
                row=1, col=1
            )
        if "SMA_50" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["SMA_50"],
                    mode="lines", name="50 SMA",
                    line=dict(color="#FBBF24", width=1.5)
                ),
                row=1, col=1
            )
        if "SMA_200" in df.columns and df["SMA_200"].dropna().shape[0] > 0:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["SMA_200"],
                    mode="lines", name="200 SMA",
                    line=dict(color="#C084FC", width=1.5)
                ),
                row=1, col=1
            )

    # Volume Subplot
    vol_colors = [
        "#10B981" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#EF4444"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.7),
            hovertemplate="Volume: %{y:,.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0)",
        plot_bgcolor="rgba(30, 41, 59, 0.4)",
        margin=dict(l=50, r=20, t=40, b=30),
        height=540,
        title=dict(
            text=f"<b>{ticker_symbol} Candlestick & Volume Chart</b>",
            font=dict(size=18, color="#F8FAFC")
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        xaxis2=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        yaxis=dict(title="Price ($)", showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        yaxis2=dict(title="Volume", showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

def create_forecast_cone_chart(hist: pd.DataFrame, outlook_data: dict, ticker_symbol: str) -> go.Figure:
    """
    Create a 2-Week forward forecast projection cone chart.
    Displays recent historical price action seamlessly connecting to the 10 trading day forward forecast.
    """
    recent_hist = hist.tail(30).copy()
    forward_pts = outlook_data.get("forward_projection", [])
    
    if not forward_pts or recent_hist.empty:
        fig = go.Figure()
        fig.add_annotation(text="Forecast cone data unavailable", showarrow=False)
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
            line=dict(color="#38BDF8", width=2.5),
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
            line=dict(color="rgba(16, 185, 129, 0.6)", width=1.5, dash="dash"),
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
            line=dict(color="rgba(239, 68, 68, 0.6)", width=1.5, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(56, 189, 248, 0.12)",
            hovertemplate="<b>%{x}</b><br>Lower Bound: $%{y:.2f}<extra></extra>"
        )
    )

    # 4. Projected Center Target
    verdict_color = outlook_data.get("verdict_color", "#F59E0B")
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

    # Add vertical line dividing history and forecast
    fig.add_vline(
        x=last_dt,
        line_width=1.5,
        line_dash="solid",
        line_color="#94A3B8"
    )

    fig.add_annotation(
        x=last_dt,
        y=curr_price,
        text=" Today",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#94A3B8",
        font=dict(color="#F8FAFC", size=12)
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0)",
        plot_bgcolor="rgba(30, 41, 59, 0.4)",
        margin=dict(l=50, r=20, t=40, b=30),
        height=450,
        title=dict(
            text=f"<b>{ticker_symbol} 2-Week Forward Forecast Cone (10 Trading Days)</b>",
            font=dict(size=17, color="#F8FAFC")
        ),
        xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        yaxis=dict(title="Price ($)", showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )

    return fig

def create_earnings_reaction_bar_chart(historical_earnings: list, ticker_symbol: str) -> go.Figure:
    """
    Create a bar chart comparing past quarterly earnings announcement reactions (1-Day and 1-Week price % changes).
    """
    valid_records = [
        r for r in historical_earnings 
        if r.get("has_reaction") and r.get("perf_1d_pct") is not None
    ]
    
    if not valid_records:
        fig = go.Figure()
        fig.add_annotation(text="No post-earnings price reaction data available", showarrow=False)
        return fig
        
    valid_records = list(reversed(valid_records)) # Chronological order
    dates = [r["date"] for r in valid_records]
    p1_vals = [r["perf_1d_pct"] for r in valid_records]
    p1w_vals = [r.get("perf_1w_pct", 0) or 0 for r in valid_records]
    surprises = [r.get("surprise_pct") for r in valid_records]

    fig = go.Figure()

    # 1-Day Reaction
    bar_colors_1d = ["#10B981" if v >= 0 else "#EF4444" for v in p1_vals]
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
            line=dict(color="#FBBF24", width=2.5),
            marker=dict(size=8, color="#FBBF24"),
            hovertemplate="<b>%{x}</b><br>1-Week Reaction: <b>%{y:+.2f}%</b><extra></extra>"
        )
    )

    fig.add_hline(y=0, line_dash="solid", line_color="#64748B", line_width=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0)",
        plot_bgcolor="rgba(30, 41, 59, 0.4)",
        margin=dict(l=50, r=20, t=40, b=30),
        height=380,
        title=dict(
            text=f"<b>{ticker_symbol} Historical Earnings Announcement Price Reactions</b>",
            font=dict(size=17, color="#F8FAFC")
        ),
        xaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)"),
        yaxis=dict(
            title="Stock Performance (%)",
            ticksuffix="%",
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig
