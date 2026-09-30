"""
stock_core.py - Core data extraction, analytics, technical calculations,
earnings reaction analysis, and 2-week outlook forecasting for stock analysis.
Designed to be 100% pickle-serializable for caching with Streamlit.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

def get_stock_data(symbol: str) -> dict:
    """
    Fetch comprehensive stock information, historical prices, and raw data.
    Does NOT return any unpicklable session/thread objects.
    """
    symbol = symbol.strip().upper()
    ticker = yf.Ticker(symbol)
    
    # Fetch 5 years of daily history for deep analysis and period charts
    hist = ticker.history(period="5y")
    
    if hist.empty:
        # Fallback test with 1mo
        hist_check = ticker.history(period="1mo")
        if hist_check.empty:
            raise ValueError(f"No trading data found for ticker '{symbol}'. Please check the symbol or exchange.")
        hist = hist_check
        
    # Drop rows where Close is NaN (e.g. today's unclosed trading row or holidays)
    hist = hist[pd.notna(hist["Close"]) & pd.notna(hist["Open"])]
    if hist.empty:
        raise ValueError(f"No valid historical price bars found for ticker '{symbol}'.")
        
    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        info = {}
        
    # Safely query fast_info (resilient to cloud IP rate limiting)
    fast_info = {}
    try:
        fi = ticker.fast_info
        for k in ("lastPrice", "previousClose", "marketCap", "yearHigh", "yearLow", "currency", "exchange"):
            try:
                val = fi[k]
                if val is not None and not pd.isna(val):
                    fast_info[k] = val
            except Exception:
                pass
    except Exception:
        pass
        
    # Extract earnings and recommendations safely
    earnings_dates = None
    try:
        earnings_dates = ticker.earnings_dates
    except Exception:
        earnings_dates = None
        
    recs_summary = None
    try:
        recs_summary = ticker.recommendations_summary
    except Exception:
        recs_summary = None
        
    calendar = None
    try:
        calendar = ticker.calendar
    except Exception:
        calendar = None

    # Latest trading row from validated history
    latest_row = hist.iloc[-1]
    prev_row = hist.iloc[-2] if len(hist) > 1 else latest_row
    
    # Priority cascade: fast_info -> info -> latest history bar
    raw_curr = (
        fast_info.get("lastPrice")
        or info.get("currentPrice")
        or info.get("regularMarketPrice")
        or latest_row["Close"]
    )
    curr_price = float(raw_curr)
    
    raw_prev = (
        fast_info.get("previousClose")
        or info.get("previousClose")
        or info.get("regularMarketPreviousClose")
        or prev_row["Close"]
    )
    prev_close = float(raw_prev)
    
    change_abs = curr_price - prev_close
    change_pct = (change_abs / prev_close * 100) if prev_close else 0.0
    
    # 52-week High/Low
    hist_1y = hist.tail(252)
    calc_52_high = float(hist_1y["High"].max()) if not hist_1y.empty else curr_price
    calc_52_low = float(hist_1y["Low"].min()) if not hist_1y.empty else curr_price
    
    high_52 = float(fast_info.get("yearHigh") or info.get("fiftyTwoWeekHigh") or calc_52_high)
    low_52 = float(fast_info.get("yearLow") or info.get("fiftyTwoWeekLow") or calc_52_low)
    
    # Position within 52w range (0% to 100%)
    if high_52 > low_52:
        pos_52 = max(0.0, min(100.0, ((curr_price - low_52) / (high_52 - low_52)) * 100.0))
    else:
        pos_52 = 50.0

    market_cap = fast_info.get("marketCap") or info.get("marketCap")
    currency = fast_info.get("currency") or info.get("currency", "USD")
    exchange = fast_info.get("exchange") or info.get("exchange", "Exchange")

    return {
        "symbol": symbol,
        "short_name": info.get("shortName") or info.get("longName") or symbol,
        "currency": currency,
        "exchange": exchange,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "current_price": curr_price,
        "previous_close": prev_close,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "open": float(latest_row["Open"]),
        "day_high": float(latest_row["High"]),
        "day_low": float(latest_row["Low"]),
        "fifty_two_week_high": high_52,
        "fifty_two_week_low": low_52,
        "fifty_two_week_position": pos_52,
        "market_cap": market_cap,
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "beta": info.get("beta"),
        "dividend_yield": (info.get("dividendYield") * 100) if info.get("dividendYield") else None,
        "eps_trailing": info.get("trailingEps"),
        "info": info,
        "fast_info": fast_info,
        "history": hist,
        "earnings_dates": earnings_dates,
        "recommendations_summary": recs_summary,
        "calendar": calendar
    }

def calculate_growth_metrics(hist: pd.DataFrame, curr_price: float) -> dict:
    """
    Calculate growth percentage for:
    - 1 Week (7 calendar days)
    - 1 Month (30 calendar days)
    - 3 Months (90 calendar days)
    - 6 Months (180 calendar days)
    - 1 Year (365 calendar days)
    - Year to Date (YTD)
    """
    if hist.empty or len(hist) < 2:
        return {}
        
    latest_dt = hist.index[-1]
    results = {}
    
    periods = [
        ("1_week", "1 Week", pd.Timedelta(days=7)),
        ("1_month", "1 Month", pd.DateOffset(months=1)),
        ("3_month", "3 Months", pd.DateOffset(months=3)),
        ("6_month", "6 Months", pd.DateOffset(months=6)),
        ("1_year", "1 Year", pd.DateOffset(years=1)),
    ]
    
    for key, label, delta in periods:
        target_dt = latest_dt - delta
        sub = hist[hist.index <= target_dt]
        if not sub.empty:
            start_row = sub.iloc[-1]
            start_price = float(start_row["Close"])
            growth_pct = ((curr_price - start_price) / start_price) * 100.0
            change_dollar = curr_price - start_price
            results[key] = {
                "label": label,
                "start_date": sub.index[-1].strftime("%Y-%m-%d"),
                "start_price": start_price,
                "current_price": curr_price,
                "growth_pct": growth_pct,
                "change_dollar": change_dollar,
                "available": True
            }
        else:
            results[key] = {
                "label": label,
                "start_date": None,
                "start_price": None,
                "current_price": curr_price,
                "growth_pct": None,
                "change_dollar": None,
                "available": False
            }
            
    # YTD Growth
    year_start_dt = pd.Timestamp(year=latest_dt.year, month=1, day=1, tz=latest_dt.tz)
    sub_ytd = hist[hist.index < year_start_dt]
    if not sub_ytd.empty:
        start_row = sub_ytd.iloc[-1]
        start_price = float(start_row["Close"])
        growth_pct = ((curr_price - start_price) / start_price) * 100.0
        change_dollar = curr_price - start_price
        results["ytd"] = {
            "label": "YTD",
            "start_date": sub_ytd.index[-1].strftime("%Y-%m-%d"),
            "start_price": start_price,
            "current_price": curr_price,
            "growth_pct": growth_pct,
            "change_dollar": change_dollar,
            "available": True
        }
    else:
        results["ytd"] = {
            "label": "YTD",
            "start_date": None,
            "start_price": None,
            "current_price": curr_price,
            "growth_pct": None,
            "change_dollar": None,
            "available": False
        }
        
    return results

def calculate_volume_metrics(hist: pd.DataFrame, curr_price: float, info: dict) -> dict:
    """
    Extract and compute detailed volume metrics.
    """
    latest_volume = int(info.get("regularMarketVolume") or hist["Volume"].iloc[-1])
    
    vol_10d = int(hist["Volume"].tail(10).mean()) if len(hist) >= 10 else latest_volume
    vol_30d = int(hist["Volume"].tail(30).mean()) if len(hist) >= 30 else vol_10d
    vol_3m = int(hist["Volume"].tail(63).mean()) if len(hist) >= 63 else vol_30d
    avg_vol_info = int(info.get("averageVolume") or vol_3m)
    
    rvol_10d = (latest_volume / vol_10d) if vol_10d > 0 else 1.0
    rvol_3m = (latest_volume / vol_3m) if vol_3m > 0 else 1.0
    dollar_volume = latest_volume * curr_price
    
    if rvol_10d >= 1.5:
        volume_status = f"Very High Activity ({rvol_10d:.1f}x 10-day avg)"
        volume_sentiment = "Bullish/Active"
    elif rvol_10d >= 1.1:
        volume_status = f"Above Average (+{((rvol_10d - 1)*100):.0f}%)"
        volume_sentiment = "Moderate"
    elif rvol_10d <= 0.7:
        volume_status = f"Light / Below Average ({rvol_10d:.2f}x 10-day avg)"
        volume_sentiment = "Quiet"
    else:
        volume_status = f"Normal Volume ({rvol_10d:.2f}x 10-day avg)"
        volume_sentiment = "Normal"
        
    return {
        "current_volume": latest_volume,
        "avg_volume_10d": vol_10d,
        "avg_volume_30d": vol_30d,
        "avg_volume_3m": vol_3m,
        "avg_volume_info": avg_vol_info,
        "rvol_10d": rvol_10d,
        "rvol_3m": rvol_3m,
        "dollar_volume": dollar_volume,
        "volume_status": volume_status,
        "volume_sentiment": volume_sentiment
    }

def calculate_two_week_outlook(hist: pd.DataFrame, curr_price: float, info: dict, recs_summary: pd.DataFrame = None) -> dict:
    """
    Synthesize a rigorous 2-week outlook without requiring unpicklable Ticker instances.
    """
    closes = hist["Close"]
    
    # 1. RSI (14-day)
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi_series = 100 - (100 / (1 + rs))
    rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
    
    # 2. Moving Averages
    sma20 = float(closes.rolling(20).mean().iloc[-1]) if len(closes) >= 20 else curr_price
    sma50 = float(closes.rolling(50).mean().iloc[-1]) if len(closes) >= 50 else curr_price
    sma200 = float(closes.rolling(200).mean().iloc[-1]) if len(closes) >= 200 else curr_price
    
    pct_from_sma20 = ((curr_price - sma20) / sma20) * 100
    pct_from_sma50 = ((curr_price - sma50) / sma50) * 100
    
    # 3. MACD (12, 26, 9)
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    latest_macd = float(macd_line.iloc[-1])
    latest_signal = float(signal_line.iloc[-1])
    latest_hist = float(macd_hist.iloc[-1])
    macd_bullish = latest_macd > latest_signal
    
    # 4. Volatility & 2-Week Statistical Range
    returns = closes.pct_change(fill_method=None).dropna()
    daily_vol = float(returns.tail(20).std()) if len(returns) >= 20 else 0.015
    vol_10d = daily_vol * np.sqrt(10)
    
    # 14-day linear trend velocity
    lookback = min(14, len(closes))
    y_vals = closes.tail(lookback).values
    x_vals = np.arange(lookback)
    poly = np.polyfit(x_vals, y_vals, 1)
    slope = float(poly[0])
    
    # Trend projected change over 10 trading days (damped by 0.7)
    trend_proj_change = slope * 10 * 0.7
    proj_center = curr_price + trend_proj_change
    
    proj_upper = max(proj_center * (1 + vol_10d * 1.28), curr_price * (1 + vol_10d * 0.8))
    proj_lower = min(proj_center * (1 - vol_10d * 1.28), curr_price * (1 - vol_10d * 0.8))
    
    # 5. Wall Street Analyst Consensus
    target_mean = info.get("targetMeanPrice")
    target_median = info.get("targetMedianPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    rec_key = info.get("recommendationKey", "").replace("_", " ").title()
    num_analysts = info.get("numberOfAnalystOpinions", 0)
    
    analyst_upside_pct = None
    if target_mean and target_mean > 0:
        analyst_upside_pct = ((target_mean - curr_price) / curr_price) * 100
        
    rec_breakdown = {}
    if recs_summary is not None and not recs_summary.empty:
        try:
            rec_breakdown = recs_summary.iloc[0].to_dict()
        except Exception:
            rec_breakdown = {}

    # 6. Composite Score (-100 to +100)
    score = 0
    rationales = []
    
    if rsi >= 75:
        score -= 15
        rationales.append(f"RSI is {rsi:.1f} (Overbought territory - risk of short-term pullback or consolidation).")
    elif rsi > 55:
        score += 20
        rationales.append(f"RSI is {rsi:.1f} (Healthy upward momentum above the 50 neutral line).")
    elif rsi < 30:
        score += 15
        rationales.append(f"RSI is {rsi:.1f} (Oversold condition - potential technical bounce candidate).")
    elif rsi < 45:
        score -= 15
        rationales.append(f"RSI is {rsi:.1f} (Weak momentum below neutral 50 line).")
    else:
        rationales.append(f"RSI is {rsi:.1f} (Neutral momentum within the 45-55 corridor).")
        
    if curr_price > sma20:
        score += 20
        rationales.append(f"Price is trading +{pct_from_sma20:.1f}% above its 20-Day moving average (${sma20:.2f}), confirming short-term uptrend.")
    else:
        score -= 20
        rationales.append(f"Price is trading {pct_from_sma20:.1f}% below its 20-Day moving average (${sma20:.2f}), signaling short-term pressure.")
        
    if sma20 > sma50:
        score += 15
        rationales.append(f"20-Day MA (${sma20:.2f}) is above 50-Day MA (${sma50:.2f}), indicating positive intermediate alignment.")
    else:
        score -= 15
        rationales.append(f"20-Day MA (${sma20:.2f}) is below 50-Day MA (${sma50:.2f}), showing bearish intermediate trend alignment.")
        
    if macd_bullish:
        score += 15
        hist_trend = "widening" if latest_hist > 0 else "converging"
        rationales.append(f"MACD line ({latest_macd:.2f}) is above Signal line ({latest_signal:.2f}) with a {hist_trend} positive histogram.")
    else:
        score -= 15
        rationales.append(f"MACD line ({latest_macd:.2f}) is below Signal line ({latest_signal:.2f}), showing negative momentum pressure.")
        
    slope_pct_day = (slope / curr_price) * 100
    if slope_pct_day > 0.15:
        score += 15
        rationales.append(f"14-day price trajectory shows strong upward velocity of {slope_pct_day:+.2f}%/day.")
    elif slope_pct_day < -0.15:
        score -= 15
        rationales.append(f"14-day price trajectory shows downward drag of {slope_pct_day:+.2f}%/day.")
    else:
        rationales.append(f"14-day price trajectory has been relatively flat ({slope_pct_day:+.2f}%/day).")
        
    if analyst_upside_pct is not None:
        if analyst_upside_pct > 10:
            score += 15
            rationales.append(f"Wall Street consensus 12M target (${target_mean:.2f}) implies +{analyst_upside_pct:.1f}% upside with {num_analysts} analyst ratings.")
        elif analyst_upside_pct < -5:
            score -= 10
            rationales.append(f"Wall Street target (${target_mean:.2f}) implies {analyst_upside_pct:.1f}% downside from current level.")
        else:
            rationales.append(f"Wall Street target (${target_mean:.2f}) is near parity ({analyst_upside_pct:+.1f}%).")
            
    score = max(-100, min(100, score))
    
    if score >= 50:
        verdict = "Bullish"
        verdict_icon = "🟢"
        color = "#10B981"
        outlook_desc = "Strong technical tailwinds and momentum suggest upward price action over the next 2 weeks."
    elif score >= 20:
        verdict = "Moderately Bullish"
        verdict_icon = "🌱"
        color = "#34D399"
        outlook_desc = "Favorable technical setup with mild upside bias over the next 2 weeks."
    elif score > -20:
        verdict = "Neutral / Rangebound"
        verdict_icon = "⚪"
        color = "#F59E0B"
        outlook_desc = "Mixed signals suggest consolidation or range-bound trading over the next 2 weeks."
    elif score > -50:
        verdict = "Moderately Bearish"
        verdict_icon = "🍂"
        color = "#F87171"
        outlook_desc = "Softening momentum and technical resistance indicate downside pressure over the next 2 weeks."
    else:
        verdict = "Bearish"
        verdict_icon = "🔴"
        color = "#EF4444"
        outlook_desc = "Significant technical headwind and negative momentum suggest caution over the next 2 weeks."

    forward_dates = []
    curr_dt = hist.index[-1].date()
    step_dt = curr_dt
    days_added = 0
    while days_added < 10:
        step_dt += timedelta(days=1)
        if step_dt.weekday() < 5:
            days_added += 1
            frac = days_added / 10.0
            p_val = curr_price + (proj_center - curr_price) * frac
            band_up = curr_price + (proj_upper - curr_price) * np.sqrt(frac)
            band_dn = curr_price + (proj_lower - curr_price) * np.sqrt(frac)
            forward_dates.append({
                "date": step_dt.strftime("%Y-%m-%d"),
                "expected": round(p_val, 2),
                "upper": round(band_up, 2),
                "lower": round(band_dn, 2)
            })

    return {
        "verdict": verdict,
        "verdict_icon": verdict_icon,
        "verdict_color": color,
        "outlook_desc": outlook_desc,
        "composite_score": score,
        "rationales": rationales,
        "current_price": curr_price,
        "projected_target_2w": round(proj_center, 2),
        "expected_range_lower": round(proj_lower, 2),
        "expected_range_upper": round(proj_upper, 2),
        "expected_change_pct": round(((proj_center - curr_price) / curr_price) * 100, 2),
        "expected_volatility_2w_pct": round(vol_10d * 100, 2),
        "rsi_14": round(rsi, 1),
        "sma_20": round(sma20, 2),
        "sma_50": round(sma50, 2),
        "sma_200": round(sma200, 2),
        "macd": round(latest_macd, 2),
        "macd_signal": round(latest_signal, 2),
        "macd_bullish": macd_bullish,
        "target_mean": target_mean,
        "target_median": target_median,
        "target_high": target_high,
        "target_low": target_low,
        "analyst_upside_pct": round(analyst_upside_pct, 1) if analyst_upside_pct is not None else None,
        "recommendation_key": rec_key,
        "num_analysts": num_analysts,
        "recommendations_breakdown": rec_breakdown,
        "forward_projection": forward_dates
    }

def calculate_quarterly_results(earnings_dates: pd.DataFrame, calendar: dict, hist: pd.DataFrame) -> dict:
    """
    Determine:
    1. Next quarterly results announcement date & countdown
    2. Last quarterly results announcement date & EPS beat/miss
    3. Stock performance after announcing the last quarterly results (1-day, 3-day, 1-week)
    4. Historical quarters performance table
    Does NOT require a Ticker object.
    """
    ed = earnings_dates
    if ed is None or ed.empty:
        if calendar and isinstance(calendar, dict):
            next_dates = calendar.get("Earnings Date", [])
            if next_dates:
                next_d = next_dates[0]
                return {
                    "has_earnings_data": True,
                    "is_etf_or_fund": False,
                    "next_earnings": {
                        "date": pd.Timestamp(next_d).strftime("%b %d, %Y"),
                        "datetime_full": str(next_d),
                        "days_until": (pd.Timestamp(next_d).date() - datetime.now().date()).days,
                        "eps_estimate": None
                    },
                    "last_earnings": None,
                    "historical_earnings": []
                }
        return {
            "has_earnings_data": False,
            "is_etf_or_fund": True,
            "message": "Quarterly earnings reports are not available for this ticker (e.g., Index ETF, Mutual Fund, or delisted company)."
        }

    ed_copy = ed.copy()
    tz = ed_copy.index.tz
    if tz is None:
        tz = pytz.timezone("America/New_York")
        ed_copy.index = ed_copy.index.tz_localize(tz)
    now_ts = pd.Timestamp.now(tz=tz)
    
    # 1. Next Earnings
    future_ed = ed_copy[ed_copy.index > now_ts]
    next_earnings = None
    if not future_ed.empty:
        next_row = future_ed.sort_index().iloc[0]
        days_until = (next_row.name - now_ts).days
        is_exact_time = next_row.name.hour > 0 or next_row.name.minute > 0
        if next_row.name.hour >= 16 or (next_row.name.hour >= 15 and next_row.name.minute >= 30):
            timing_status = "Confirmed by IR (After Market Close)"
        elif 0 < next_row.name.hour <= 10:
            timing_status = "Confirmed by IR (Before Market Open)"
        elif is_exact_time:
            timing_status = "Scheduled by IR"
        else:
            timing_status = "Estimated Calendar Window"

        next_earnings = {
            "date": next_row.name.strftime("%b %d, %Y"),
            "datetime_full": next_row.name.strftime("%Y-%m-%d %H:%M %Z"),
            "days_until": days_until,
            "eps_estimate": next_row.get("EPS Estimate") if pd.notna(next_row.get("EPS Estimate")) else None,
            "timing_status": timing_status,
            "primary_source": "Yahoo Finance / LSEG Institutional Corporate Events",
            "official_origin": "Company Investor Relations (IR) Press Releases & SEC Form 8-K Filings"
        }

        
    hist_aligned = hist.copy()
    if hist_aligned.index.tz is None:
        hist_aligned.index = hist_aligned.index.tz_localize(tz)
    else:
        hist_aligned.index = hist_aligned.index.tz_convert(tz)
        
    hist_dates = [d.date() for d in hist_aligned.index]
    
    def evaluate_earnings_reaction(ed_dt, row):
        ed_date = ed_dt.date()
        is_after_market = ed_dt.hour >= 16 or (ed_dt.hour >= 15 and ed_dt.minute >= 30)
        
        if ed_date in hist_dates:
            pos = hist_dates.index(ed_date)
        else:
            prev_dates = [i for i, d in enumerate(hist_dates) if d <= ed_date]
            pos = prev_dates[-1] if prev_dates else 0
            
        if is_after_market:
            base_pos = pos
            reaction_pos = pos + 1
        else:
            base_pos = max(0, pos - 1)
            reaction_pos = pos
            
        eps_est = row.get("EPS Estimate")
        eps_rep = row.get("Reported EPS")
        surprise = row.get("Surprise(%)")
        
        eps_est_val = float(eps_est) if pd.notna(eps_est) else None
        eps_rep_val = float(eps_rep) if pd.notna(eps_rep) else None
        surprise_val = float(surprise) if pd.notna(surprise) else None
        
        beat_status = "N/A"
        if eps_rep_val is not None and eps_est_val is not None:
            if eps_rep_val > eps_est_val:
                beat_status = "Beat"
            elif eps_rep_val < eps_est_val:
                beat_status = "Miss"
            else:
                beat_status = "Met"
                
        rx_data = {
            "date": ed_dt.strftime("%b %d, %Y"),
            "datetime_full": ed_dt.strftime("%Y-%m-%d %H:%M %Z"),
            "timing": "After Market Close" if is_after_market else "Before Market Open",
            "eps_estimate": eps_est_val,
            "eps_reported": eps_rep_val,
            "surprise_pct": surprise_val,
            "beat_status": beat_status,
            "reaction_date": None,
            "prior_close": None,
            "reaction_close": None,
            "perf_1d_pct": None,
            "perf_3d_pct": None,
            "perf_1w_pct": None,
            "has_reaction": False
        }
        
        if reaction_pos < len(hist_aligned):
            base_p = float(hist_aligned["Close"].iloc[base_pos])
            rx_p = float(hist_aligned["Close"].iloc[reaction_pos])
            rx_d = hist_aligned.index[reaction_pos].strftime("%b %d, %Y")
            
            p1 = ((rx_p - base_p) / base_p) * 100.0
            
            p3 = None
            if reaction_pos + 2 < len(hist_aligned):
                p3_close = float(hist_aligned["Close"].iloc[reaction_pos + 2])
                p3 = ((p3_close - base_p) / base_p) * 100.0
                
            p5 = None
            if reaction_pos + 4 < len(hist_aligned):
                p5_close = float(hist_aligned["Close"].iloc[reaction_pos + 4])
                p5 = ((p5_close - base_p) / base_p) * 100.0
                
            rx_data.update({
                "reaction_date": rx_d,
                "prior_close": round(base_p, 2),
                "reaction_close": round(rx_p, 2),
                "perf_1d_pct": round(p1, 2),
                "perf_3d_pct": round(p3, 2) if p3 is not None else None,
                "perf_1w_pct": round(p5, 2) if p5 is not None else None,
                "has_reaction": True
            })
            
        return rx_data

    # Past earnings
    past_ed = ed_copy[(ed_copy.index <= now_ts) & ed_copy["Reported EPS"].notna()]
    if past_ed.empty:
        past_ed = ed_copy[ed_copy.index <= now_ts]
        
    last_earnings = None
    historical_list = []
    
    if not past_ed.empty:
        sorted_past = past_ed.sort_index(ascending=False)
        last_dt = sorted_past.index[0]
        last_earnings = evaluate_earnings_reaction(last_dt, sorted_past.iloc[0])
        
        for dt_idx, row_data in sorted_past.head(6).iterrows():
            historical_list.append(evaluate_earnings_reaction(dt_idx, row_data))
            
    return {
        "has_earnings_data": True,
        "is_etf_or_fund": False,
        "next_earnings": next_earnings,
        "last_earnings": last_earnings,
        "historical_earnings": historical_list
    }

def get_full_stock_analysis(symbol: str) -> dict:
    """
    Convenience method that computes all data, metrics, volume, outlook, and earnings
    at once into a 100% pickle-serializable dictionary.
    """
    raw = get_stock_data(symbol)
    hist = raw["history"]
    curr_price = raw["current_price"]
    info = raw["info"]
    
    growth = calculate_growth_metrics(hist, curr_price)
    volume = calculate_volume_metrics(hist, curr_price, info)
    outlook = calculate_two_week_outlook(hist, curr_price, info, raw.get("recommendations_summary"))
    quarterly = calculate_quarterly_results(raw.get("earnings_dates"), raw.get("calendar"), hist)
    
    return {
        "raw": raw,
        "growth": growth,
        "volume": volume,
        "outlook": outlook,
        "quarterly": quarterly
    }

def get_growth_chart_data(hist: pd.DataFrame, period: str) -> pd.DataFrame:
    """
    Slice history according to requested period:
    1W, 1M, 3M, 6M, 1Y, 2Y, 5Y, YTD
    And compute cumulative % growth from start of that period.
    """
    if hist.empty:
        return hist
        
    latest_dt = hist.index[-1]
    
    period_map = {
        "1W": pd.Timedelta(days=7),
        "1M": pd.DateOffset(months=1),
        "3M": pd.DateOffset(months=3),
        "6M": pd.DateOffset(months=6),
        "1Y": pd.DateOffset(years=1),
        "2Y": pd.DateOffset(years=2),
        "5Y": pd.DateOffset(years=5),
    }
    
    if period == "YTD":
        year_start = pd.Timestamp(year=latest_dt.year, month=1, day=1, tz=latest_dt.tz)
        df_period = hist[hist.index >= year_start].copy()
        if df_period.empty:
            df_period = hist.tail(10).copy()
    elif period in period_map:
        start_target = latest_dt - period_map[period]
        df_period = hist[hist.index >= start_target].copy()
    else:
        df_period = hist.copy()
        
    if df_period.empty:
        df_period = hist.tail(30).copy()
        
    base_price = float(df_period["Close"].iloc[0])
    df_period["Growth_Pct"] = ((df_period["Close"] - base_price) / base_price) * 100.0
    
    df_period["SMA_20"] = hist["Close"].rolling(20).mean().loc[df_period.index]
    df_period["SMA_50"] = hist["Close"].rolling(50).mean().loc[df_period.index]
    df_period["SMA_200"] = hist["Close"].rolling(200).mean().loc[df_period.index]
    df_period["Vol_SMA_20"] = hist["Volume"].rolling(20).mean().loc[df_period.index]
    
    return df_period
