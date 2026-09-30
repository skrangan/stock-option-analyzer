"""
server.py - High-Performance FastAPI Backend for Stock & Option Analysis
Provides fast, asynchronous REST APIs for stock data, historical charts,
and real-time option purchase evaluation.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import math
import numpy as np
import stock_core as sc
import options_core as oc
import pandas as pd
from datetime import datetime, date

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(x) for x in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    return obj

app = FastAPI(
    title="Kasthuri Rangan's Stock Analysis for Option Trading",
    description="Real-time stock analytics, 2-week outlook, quarterly results, and option P&L simulator.",
    version="2.0.0"
)

# Enable CORS for cross-origin or local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory LRU cache to prevent rate-limiting (90-second TTL)
cache = {}

def get_cached_analysis(symbol: str, force_refresh: bool = False):
    symbol = symbol.strip().upper()
    now = datetime.now()
    if not force_refresh and symbol in cache:
        entry = cache[symbol]
        if (now - entry["time"]).total_seconds() < 90:
            return entry["data"], entry["time"]
            
    analysis = sc.get_full_stock_analysis(symbol)
    cache[symbol] = {
        "time": now,
        "data": analysis
    }
    return analysis, now

@app.get("/api/stock/{symbol}")
def get_stock(symbol: str, refresh: bool = Query(False)):
    """
    Get full stock statistics, growth rates, volume, 2-week outlook, and quarterly results.
    Pass ?refresh=true to bust the cache and force an immediate live market fetch.
    """
    try:
        analysis, fetched_at = get_cached_analysis(symbol, force_refresh=refresh)
        raw = analysis["raw"]
        
        # Serialize history-free summary with live timestamp
        res = {
            "symbol": raw["symbol"],
            "short_name": raw["short_name"],
            "currency": raw["currency"],
            "exchange": raw["exchange"],
            "sector": raw["sector"],
            "industry": raw["industry"],
            "current_price": raw["current_price"],
            "previous_close": raw["previous_close"],
            "change_abs": round(raw["change_abs"], 2),
            "change_pct": round(raw["change_pct"], 2),
            "open": raw["open"],
            "day_high": raw["day_high"],
            "day_low": raw["day_low"],
            "fifty_two_week_high": raw["fifty_two_week_high"],
            "fifty_two_week_low": raw["fifty_two_week_low"],
            "market_cap": raw["market_cap"],
            "trailing_pe": raw["trailing_pe"],
            "forward_pe": raw["forward_pe"],
            "beta": raw["beta"],
            "dividend_yield": raw["dividend_yield"],
            "last_updated": fetched_at.strftime("%I:%M:%S %p"),
            "growth": analysis["growth"],
            "volume": analysis["volume"],
            "outlook": analysis["outlook"],
            "quarterly": analysis["quarterly"]
        }
        return JSONResponse(content=sanitize_for_json(res))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch stock data for '{symbol}': {str(e)}")

@app.get("/api/chart/{symbol}")
def get_chart_data(symbol: str, period: str = Query("6M", pattern="^(1W|1M|3M|6M|1Y|2Y|5Y|YTD)$")):
    """
    Get sliced historical chart data with cumulative % growth, volume, and moving averages.
    """
    try:
        analysis, _ = get_cached_analysis(symbol)
        hist = analysis["raw"]["history"]
        df_slice = sc.get_growth_chart_data(hist, period)
        
        records = []
        for dt_idx, row in df_slice.iterrows():
            records.append({
                "date": dt_idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
                "growth_pct": round(float(row.get("Growth_Pct", 0)), 2),
                "sma_20": round(float(row["SMA_20"]), 2) if pd.notna(row.get("SMA_20")) else None,
                "sma_50": round(float(row["SMA_50"]), 2) if pd.notna(row.get("SMA_50")) else None,
            })
            
        res = {
            "symbol": symbol.upper(),
            "period": period,
            "count": len(records),
            "data": records
        }
        return JSONResponse(content=sanitize_for_json(res))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/options/expirations/{symbol}")
def get_expirations(symbol: str):
    """
    Get list of available real-market expiration dates.
    """
    try:
        exps = oc.get_available_expirations(symbol)
        today_d = date.today()
        items = []
        for e in exps:
            try:
                dte = (datetime.strptime(e, "%Y-%m-%d").date() - today_d).days
                items.append({"date": e, "dte": dte, "label": f"{e} ({dte}d)"})
            except Exception:
                items.append({"date": e, "dte": 0, "label": e})
        return JSONResponse(content=sanitize_for_json({"symbol": symbol.upper(), "expirations": items}))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/options/chain/{symbol}")
def get_chain(symbol: str, expiration: str):
    """
    Get calls and puts strike quotes for a specific expiration date.
    """
    try:
        chain = oc.get_option_chain_data(symbol, expiration)
        return JSONResponse(content=sanitize_for_json(chain))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/options/analyze")
def analyze_option(
    symbol: str,
    option_type: str = Query("call", pattern="^(call|put)$"),
    strike: float = Query(...),
    bid: float = Query(...),
    expiration: str = Query(...),
    contracts: int = Query(1, ge=1, le=1000)
):
    """
    Evaluate an option purchase: Breakeven, Greeks, PoP, P&L curve, and Buy/Avoid recommendation.
    """
    try:
        analysis, _ = get_cached_analysis(symbol)
        curr_price = analysis["raw"]["current_price"]
        outlook = analysis["outlook"]
        
        result = oc.analyze_option_trade(
            symbol=symbol,
            current_price=curr_price,
            option_type=option_type,
            strike=strike,
            bid_amount=bid,
            expiration_date_str=expiration,
            num_contracts=contracts,
            outlook=outlook
        )
        return JSONResponse(content=sanitize_for_json(result))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ensure static folder exists and serve frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join("static", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            return f.read()
    return "<h1>Stock & Option Analyzer API is running. Place index.html into static/</h1>"
