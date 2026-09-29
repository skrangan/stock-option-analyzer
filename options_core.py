"""
options_core.py - Options analytics, Black-Scholes Greeks, Probability of Profit (PoP),
and "Should I Buy This Option?" decision modeling.
Designed to be 100% pickle-serializable for caching with Streamlit.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, date

def get_available_expirations(symbol: str) -> list:
    """
    Fetch list of available option expiration date strings (YYYY-MM-DD) for a ticker.
    """
    try:
        ticker = yf.Ticker(symbol.strip().upper())
        opts = ticker.options
        return list(opts) if opts else []
    except Exception:
        return []

def get_option_chain_data(symbol: str, expiration_date: str) -> dict:
    """
    Fetch calls and puts option chain for a given expiration date.
    Returns clean dictionaries and lists without any unpicklable objects.
    """
    try:
        ticker = yf.Ticker(symbol.strip().upper())
        chain = ticker.option_chain(expiration_date)
        
        calls_df = chain.calls.copy() if chain.calls is not None else pd.DataFrame()
        puts_df = chain.puts.copy() if chain.puts is not None else pd.DataFrame()
        
        # Standardize columns
        cols = ['strike', 'bid', 'ask', 'lastPrice', 'impliedVolatility', 'volume', 'openInterest', 'inTheMoney']
        
        calls_clean = []
        if not calls_df.empty:
            for _, row in calls_df.iterrows():
                calls_clean.append({
                    "strike": float(row.get("strike", 0)),
                    "bid": float(row.get("bid", 0) or 0),
                    "ask": float(row.get("ask", 0) or 0),
                    "lastPrice": float(row.get("lastPrice", 0) or 0),
                    "iv": float(row.get("impliedVolatility", 0) or 0),
                    "volume": int(row.get("volume", 0) or 0) if pd.notna(row.get("volume")) else 0,
                    "oi": int(row.get("openInterest", 0) or 0) if pd.notna(row.get("openInterest")) else 0,
                    "itm": bool(row.get("inTheMoney", False))
                })
                
        puts_clean = []
        if not puts_df.empty:
            for _, row in puts_df.iterrows():
                puts_clean.append({
                    "strike": float(row.get("strike", 0)),
                    "bid": float(row.get("bid", 0) or 0),
                    "ask": float(row.get("ask", 0) or 0),
                    "lastPrice": float(row.get("lastPrice", 0) or 0),
                    "iv": float(row.get("impliedVolatility", 0) or 0),
                    "volume": int(row.get("volume", 0) or 0) if pd.notna(row.get("volume")) else 0,
                    "oi": int(row.get("openInterest", 0) or 0) if pd.notna(row.get("openInterest")) else 0,
                    "itm": bool(row.get("inTheMoney", False))
                })
                
        all_strikes = sorted(list(set([c["strike"] for c in calls_clean] + [p["strike"] for p in puts_clean])))
        
        return {
            "symbol": symbol.upper(),
            "expiration": expiration_date,
            "calls": calls_clean,
            "puts": puts_clean,
            "strikes": all_strikes,
            "has_data": len(all_strikes) > 0
        }
    except Exception as e:
        return {
            "symbol": symbol.upper(),
            "expiration": expiration_date,
            "calls": [],
            "puts": [],
            "strikes": [],
            "has_data": False,
            "error": str(e)
        }

def black_scholes_pricing(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> dict:
    """
    Calculate theoretical option price and Greeks using the Black-Scholes-Merton model.
    """
    option_type = option_type.lower()
    if T <= 0.0001:
        # At expiration
        if option_type == 'call':
            val = max(0.0, S - K)
            delta = 1.0 if S > K else 0.0
        else:
            val = max(0.0, K - S)
            delta = -1.0 if S < K else 0.0
        return {
            "price": val,
            "delta": delta,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0
        }

    sigma = max(0.05, min(3.0, sigma)) # Clamp reasonable IV
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = float(norm.cdf(d1))
        # Daily theta ($ / calendar day)
        theta = float((- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365.0)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = float(norm.cdf(d1) - 1.0)
        theta = float((- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365.0)

    gamma = float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))
    vega = float((S * norm.pdf(d1) * np.sqrt(T)) / 100.0) # $ change per 1% change in IV

    return {
        "price": max(0.0, float(price)),
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega
    }

def analyze_option_trade(
    symbol: str,
    current_price: float,
    option_type: str,
    strike: float,
    bid_amount: float,
    expiration_date_str: str,
    num_contracts: int = 1,
    custom_iv: float = None,
    outlook: dict = None
) -> dict:
    """
    Comprehensive evaluation of an option purchase:
    - Breakeven price and % move required
    - Total cost and max profit / max loss
    - Greeks and daily theta burn
    - Probability of Profit (PoP)
    - "Should I Buy This Option?" Verdict (Favorable / Speculative / Unfavorable) with rationale
    - Full P&L matrix and curve across stock prices at expiration, today, and halfway
    """
    option_type = option_type.lower()
    contracts = max(1, int(num_contracts))
    shares_controlled = contracts * 100
    
    # Cost and Risk
    cost_per_share = float(bid_amount)
    total_investment = cost_per_share * shares_controlled
    max_loss = total_investment
    max_loss_pct = -100.0

    # Expiration date & DTE
    try:
        exp_dt = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
    except Exception:
        exp_dt = date.today()
        
    today = date.today()
    dte = max(0, (exp_dt - today).days)
    T = max(dte, 0.25) / 365.0
    r = 0.045 # Current risk-free treasury rate ~4.5%

    # Default IV if none passed
    sigma = custom_iv if (custom_iv and custom_iv > 0.01) else 0.28

    # Breakeven & Directional Move
    if option_type == 'call':
        breakeven_price = strike + cost_per_share
        move_req_dollar = breakeven_price - current_price
        move_req_pct = ((breakeven_price - current_price) / current_price) * 100.0
        max_profit = float('inf')
        max_profit_str = "Unlimited"
        max_profit_pct_str = "Unlimited"
        
        # Probability of Profit: P(S_T > Breakeven)
        d2_be = (np.log(current_price / breakeven_price) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        pop = float(norm.cdf(d2_be) * 100.0)
    else:
        breakeven_price = max(0.0, strike - cost_per_share)
        move_req_dollar = current_price - breakeven_price
        move_req_pct = ((current_price - breakeven_price) / current_price) * 100.0
        max_profit = (strike - cost_per_share) * shares_controlled
        max_profit_str = f"${max_profit:,.2f}"
        max_profit_pct = ((strike - cost_per_share) / cost_per_share) * 100.0 if cost_per_share > 0 else 0
        max_profit_pct_str = f"{max_profit_pct:+.1f}%"
        
        # Probability of Profit: P(S_T < Breakeven)
        d2_be = (np.log(current_price / breakeven_price) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        pop = float((1.0 - norm.cdf(d2_be)) * 100.0)

    # Black-Scholes Greeks
    bs_now = black_scholes_pricing(current_price, strike, T, r, sigma, option_type)
    daily_theta_per_share = bs_now["theta"]
    daily_theta_total = daily_theta_per_share * shares_controlled

    # Expected Move over DTE: sigma * sqrt(T)
    expected_move_pct = sigma * np.sqrt(T) * 100.0
    expected_move_dollar = current_price * (expected_move_pct / 100.0)

    # ------------------ "SHOULD I BUY THIS OPTION?" DECISION ENGINE ------------------
    score = 0
    rationales = []
    warnings = []

    # 1. Alignment with 2-week outlook
    stock_verdict = outlook.get("verdict", "Neutral") if outlook else "Neutral"
    if option_type == 'call':
        if "Bullish" in stock_verdict:
            score += 35
            rationales.append(f"✅ Directional alignment: Call option aligns with the stock's {stock_verdict} outlook.")
        elif "Bearish" in stock_verdict:
            score -= 40
            warnings.append(f"⚠️ Trend Conflict: You are buying a Call, but the stock's 2-week outlook is {stock_verdict}.")
        else:
            score += 5
            rationales.append(f"ℹ️ Stock outlook is Neutral ({stock_verdict}), requiring strong catalyst for Call upside.")
    else: # put
        if "Bearish" in stock_verdict:
            score += 35
            rationales.append(f"✅ Directional alignment: Put option aligns with the stock's {stock_verdict} outlook.")
        elif "Bullish" in stock_verdict:
            score -= 40
            warnings.append(f"⚠️ Trend Conflict: You are buying a Put, but the stock's 2-week outlook is {stock_verdict}.")
        else:
            score += 5
            rationales.append(f"ℹ️ Stock outlook is Neutral ({stock_verdict}), requiring significant downside catalyst for Put.")

    # 2. Probability of Profit (PoP)
    if pop >= 48:
        score += 30
        rationales.append(f"✅ High statistical probability of profit ({pop:.1f}% chance of exceeding breakeven).")
    elif pop >= 35:
        score += 15
        rationales.append(f"⚖️ Moderate probability of profit ({pop:.1f}%). Requires reasonable follow-through.")
    elif pop >= 20:
        score -= 10
        warnings.append(f"⚠️ Low probability of profit ({pop:.1f}%). Low odds of reaching breakeven (${breakeven_price:.2f}).")
    else:
        score -= 30
        warnings.append(f"🚨 Very low probability of profit ({pop:.1f}%). Functioning like an out-of-the-money lottery ticket.")

    # 3. Required Move vs Expected Market Move
    if move_req_pct <= expected_move_pct * 0.75:
        score += 20
        rationales.append(f"✅ Realistic breakeven hurdle: Needs a {move_req_pct:+.1f}% move, well within the expected {expected_move_pct:.1f}% market swing.")
    elif move_req_pct <= expected_move_pct * 1.3:
        score += 5
        rationales.append(f"⚖️ Achievable breakeven hurdle: Needs a {move_req_pct:+.1f}% move vs expected {expected_move_pct:.1f}% swing.")
    else:
        score -= 25
        warnings.append(f"⚠️ High hurdle: Requires {move_req_pct:+.1f}% move to break even, exceeding the expected {expected_move_pct:.1f}% market move.")

    # 4. Theta Decay & Days to Expiration
    if dte <= 2:
        score -= 30
        warnings.append(f"🚨 Extreme Theta risk: Only {dte} days to expiration. Daily time decay will aggressively destroy option value.")
    elif dte <= 7:
        score -= 15
        warnings.append(f"⚠️ High Theta decay: {dte} DTE. Position loses approximately ${abs(daily_theta_total):.2f}/day in time decay.")
    elif dte >= 21:
        score += 15
        rationales.append(f"✅ Ample runway: {dte} DTE gives the underlying stock sufficient time to move without rapid theta burn.")
    else:
        rationales.append(f"ℹ️ Manageable DTE ({dte} days), with daily theta erosion of approximately ${abs(daily_theta_total):.2f}/day.")

    # Score Verdict
    score = max(-100, min(100, score))
    if score >= 40:
        verdict = "FAVORABLE (Consider Buying)"
        verdict_icon = "🟢"
        verdict_color = "#059669"
        summary_text = "Favorable technical and statistical setup. The option aligns with current market momentum with reasonable odds of reaching breakeven."
    elif score >= 0:
        verdict = "SPECULATIVE (Proceed with Caution)"
        verdict_icon = "🟡"
        verdict_color = "#D97706"
        summary_text = "Mixed setup. Potential reward exists, but hurdle to profitability or theta decay presents elevated risk. Keep position size small."
    else:
        verdict = "UNFAVORABLE (High Risk / Avoid)"
        verdict_icon = "🔴"
        verdict_color = "#DC2626"
        summary_text = "Unfavorable risk/reward profile. Trend contradiction, low probability of profit, or extreme time decay make buying this option high-risk."

    # ------------------ P&L SCENARIOS TABLE ------------------
    pct_steps = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
    # Add breakeven step if not already close
    scenarios = []
    prices_to_test = [current_price * (1 + p / 100.0) for p in pct_steps]
    prices_to_test.append(breakeven_price)
    prices_to_test.append(strike)
    prices_to_test = sorted(list(set([round(p, 2) for p in prices_to_test])))

    for p in prices_to_test:
        stock_chg_pct = ((p - current_price) / current_price) * 100.0
        
        # Value at expiration
        if option_type == 'call':
            val_at_exp = max(0.0, p - strike)
        else:
            val_at_exp = max(0.0, strike - p)
            
        pnl_exp_dollar = (val_at_exp - cost_per_share) * shares_controlled
        roi_exp_pct = (pnl_exp_dollar / total_investment) * 100.0 if total_investment > 0 else 0
        
        # Value today (T)
        bs_today = black_scholes_pricing(p, strike, T, r, sigma, option_type)
        pnl_today_dollar = (bs_today["price"] - cost_per_share) * shares_controlled
        roi_today_pct = (pnl_today_dollar / total_investment) * 100.0 if total_investment > 0 else 0
        
        is_be = abs(p - breakeven_price) < 0.05
        is_curr = abs(p - current_price) < 0.05
        
        label = ""
        if is_be:
            label = "Breakeven"
        elif is_curr:
            label = "Current Price"
        elif p == strike:
            label = "Strike Price"

        scenarios.append({
            "stock_price": p,
            "stock_change_pct": stock_chg_pct,
            "option_val_exp": val_at_exp,
            "pnl_exp_dollar": pnl_exp_dollar,
            "roi_exp_pct": roi_exp_pct,
            "pnl_today_dollar": pnl_today_dollar,
            "roi_today_pct": roi_today_pct,
            "label": label
        })

    # ------------------ P&L CURVE DATA (PLOTLY) ------------------
    p_min = max(1.0, current_price * 0.70)
    p_max = current_price * 1.30
    curve_prices = np.linspace(p_min, p_max, 100)
    
    curve_pnl_exp = []
    curve_pnl_halfway = []
    curve_pnl_today = []
    
    half_T = T * 0.5
    for p in curve_prices:
        # At expiration
        if option_type == 'call':
            v_exp = max(0.0, p - strike)
        else:
            v_exp = max(0.0, strike - p)
        curve_pnl_exp.append((v_exp - cost_per_share) * shares_controlled)
        
        # Halfway
        bs_half = black_scholes_pricing(p, strike, half_T, r, sigma, option_type)
        curve_pnl_halfway.append((bs_half["price"] - cost_per_share) * shares_controlled)
        
        # Today
        bs_tod = black_scholes_pricing(p, strike, T, r, sigma, option_type)
        curve_pnl_today.append((bs_tod["price"] - cost_per_share) * shares_controlled)

    return {
        "symbol": symbol.upper(),
        "option_type": option_type.upper(),
        "strike": strike,
        "bid_amount": cost_per_share,
        "num_contracts": contracts,
        "shares_controlled": shares_controlled,
        "current_price": current_price,
        "expiration_date": expiration_date_str,
        "dte": dte,
        "total_investment": total_investment,
        "breakeven_price": round(breakeven_price, 2),
        "move_to_breakeven_pct": round(move_req_pct, 2),
        "move_to_breakeven_dollar": round(move_req_dollar, 2),
        "max_loss": total_investment,
        "max_loss_pct": max_loss_pct,
        "max_profit_str": max_profit_str,
        "max_profit_pct_str": max_profit_pct_str,
        "pop": round(pop, 1),
        "iv": round(sigma * 100, 1),
        "greeks": {
            "delta": round(bs_now["delta"], 3),
            "gamma": round(bs_now["gamma"], 4),
            "theta_per_share": round(daily_theta_per_share, 3),
            "theta_daily_total": round(daily_theta_total, 2),
            "vega": round(bs_now["vega"], 3)
        },
        "expected_move_pct": round(expected_move_pct, 1),
        "verdict": verdict,
        "verdict_icon": verdict_icon,
        "verdict_color": verdict_color,
        "verdict_score": score,
        "summary_text": summary_text,
        "rationales": rationales,
        "warnings": warnings,
        "scenarios": scenarios,
        "curve_data": {
            "prices": [round(p, 2) for p in curve_prices],
            "pnl_exp": [round(val, 2) for val in curve_pnl_exp],
            "pnl_halfway": [round(val, 2) for val in curve_pnl_halfway],
            "pnl_today": [round(val, 2) for val in curve_pnl_today]
        }
    }
