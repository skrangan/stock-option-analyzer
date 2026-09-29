# 📈 Stock Analysis & Option Decision Platform

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/skrangan/stock-option-analyzer)

A modern, high-performance, mobile-responsive stock analysis and option decision application. It features both a lightweight mobile SPA (`FastAPI` + `Tailwind` + `Chart.js`) and a rich desktop dashboard (`Streamlit` + `Plotly`), providing real-time equity statistics, multi-period growth tracking, volume analytics, a multi-source 2-week quantitative outlook forecast, quarterly earnings performance reactions, and a Black-Scholes option purchase simulator.

---

## 🌟 Key Features

1. **Current Stats & Fundamentals**:
   - Live / latest price, day change ($ and %), day high/low, and 52-week range.
   - Market capitalization, Trailing & Forward P/E, Beta, Dividend Yield, and Sector/Industry metadata.

2. **Growth Metrics**:
   - Exact percentage return and dollar gain/loss for:
     - **1 Year Growth**
     - **6 Month Growth**
     - **3 Month Growth**
     - **1 Week Growth**
     - *(Plus 1 Month & YTD growth for full context)*.
   - High-contrast, color-coded metric cards with starting dates and benchmark prices.

3. **Trade Volume Analytics**:
   - Today's trade volume (shares traded).
   - 10-day and 3-month volume averages.
   - **Relative Volume (RVOL)** multiplier indicating unusual market or institutional activity.
   - Total dollar volume traded today.

4. **Interactive Growth & Candlestick Charts**:
   - Time range selection: **1W, 1M, 3M, 6M, 1Y, 2Y, 5Y, YTD**.
   - **Cumulative Growth View (%)**: Visualizes exact percentage return from the start of the selected period, with a zero-baseline reference.
   - **Candlestick & Moving Averages View ($)**: Professional price chart with 20-day, 50-day, and 200-day SMAs.
   - Volume subplot with color-coded bars and 20-day moving average volume overlay.

5. **Multi-Source 2-Week Stock Outlook (Next 10 Trading Days)**:
   - **Synthesized Outlook Verdict**: `🟢 Bullish`, `⚪ Neutral`, or `🔴 Bearish` with a composite momentum score (-100 to +100).
   - **2-Week Price Forecast Cone**: 10-day forward projection chart displaying expected trajectory alongside upper resistance (+1.5σ) and lower support (-1.5σ) confidence boundaries.
   - **Short-Term Technical Momentum**: 14-day RSI, MACD signal crossover, 20/50-day moving average alignment, and 14-day linear trend velocity.
   - **Wall Street Analyst Consensus**: Mean/Median target prices, implied upside/downside %, consensus rating, and analyst distribution.
   - **Clear Rationale**: Bulleted takeaways explaining the technical and fundamental forces driving the outlook.

6. **Quarterly Results & Earnings Reaction Hub**:
   - **Next Quarterly Results**: Expected announcement date, days countdown, and consensus EPS estimate.
   - **Last Quarterly Results**: Announcement date, session timing (After Market Close vs Before Market Open), reported EPS vs consensus estimate (Beat/Miss and surprise %).
   - **Post-Announcement Stock Performance**:
     - Immediate 1-day stock reaction (% and $).
     - 3-day cumulative reaction (%).
     - 1-week (5 trading days) cumulative reaction (%).
     - Prior close vs reaction close.
   - **Historical Earnings Reaction Chart & Table**: Track record of the past 4-6 quarters comparing EPS surprises with immediate market reactions.

7. **🎯 Option Purchase Decision & P&L Simulator**:
   - **"Should I Buy This Option?" Verdict Engine**: Recommends `🟢 FAVORABLE`, `🟡 SPECULATIVE`, or `🔴 UNFAVORABLE` based on:
     - Directional alignment with the 2-week technical outlook.
     - Probability of Profit (PoP).
     - Required move to breakeven vs expected market volatility.
     - Time decay (Theta) burn severity over the Days to Expiration (DTE).
   - **Interactive Inputs**:
     - Option Type (Call / Put).
     - Expiration Date (populated from real live options chain or custom date).
     - Strike Price ($) and Bid Amount / Premium Paid ($/share).
     - Number of contracts.
   - **P&L Metrics**:
     - Total investment (max loss), Breakeven Price & % move needed, Max Profit potential.
     - Probability of Profit (PoP %).
     - Daily Theta time decay ($/day) and Black-Scholes Greeks (Delta, Gamma, Vega, IV).
   - **Multi-Date P&L Curve Chart**: Visualizes profit/loss across stock prices at Expiration (0 DTE), Halfway to Expiration (50% DTE), and Today (T+0).
   - **Scenario Matrix Table**: Detailed breakdown of stock prices from -20% to +20%, net dollar P&L, and ROI (%).


---

## 🚀 How to Run

### Option 1: Mobile-Friendly Fast Web App (Recommended for Phone & Desktop)
Runs the lightweight FastAPI backend with instant 15ms calculation and full mobile responsiveness:
```bash
./run_web.sh
```
Or:
```bash
/opt/anaconda3/bin/uvicorn server:app --host 0.0.0.0 --port 8000
```
- Open `http://localhost:8000` on your computer.
- Access it on your mobile phone on the same Wi-Fi using your local IP (e.g., `http://10.0.0.185:8000`).

---

### Option 2: Free 1-Click Cloud Deployment to Render
To access your app from anywhere in the world on your phone without leaving your Mac running:
1. Click the **[Deploy to Render](https://render.com/deploy?repo=https://github.com/skrangan/stock-option-analyzer)** button or log in to [dashboard.render.com](https://dashboard.render.com) with GitHub.
2. Select **New +** > **Blueprint** (or **Web Service**), and pick `skrangan/stock-option-analyzer`.
3. Render automatically reads [`render.yaml`](file:///Users/skrangan/Documents/Stock%20analysis/render.yaml) and deploys the app on the Free tier.
4. You will get a permanent public HTTPS URL (e.g. `https://stock-option-analyzer.onrender.com`).

---

### Option 3: Streamlit Interactive Dashboard
Full desktop analytical dashboard with Plotly charts:
```bash
./run.sh
```
Opens in your browser at `http://localhost:8501`.

---

### Option 4: Terminal Command-Line Interface (CLI)
For rapid terminal lookup of any stock ticker or option:
```bash
/opt/anaconda3/bin/python cli.py AAPL
/opt/anaconda3/bin/python cli.py NVDA --option call --strike 130 --bid 5.50 --dte 30
```

---

## 📁 Project Structure

- [`app.py`](file:///Users/skrangan/Documents/Stock%20analysis/app.py): The main Streamlit interactive web dashboard.
- [`stock_core.py`](file:///Users/skrangan/Documents/Stock%20analysis/stock_core.py): Core data engine containing all calculations for growth, volume, 2-week outlook, and earnings reactions.
- [`charts.py`](file:///Users/skrangan/Documents/Stock%20analysis/charts.py): Plotly charting module (Growth %, Candlesticks, 2-Week Forecast Cone, Earnings Reaction Bars).
- [`cli.py`](file:///Users/skrangan/Documents/Stock%20analysis/cli.py): Fast terminal-based stock analysis tool.
- [`run.sh`](file:///Users/skrangan/Documents/Stock%20analysis/run.sh): One-click launch script.
- [`requirements.txt`](file:///Users/skrangan/Documents/Stock%20analysis/requirements.txt): Python dependency specification.
