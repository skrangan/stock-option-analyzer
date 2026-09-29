"""
cli.py - Terminal Command-Line Interface for Stock Analysis
Usage:
    python cli.py <TICKER>
Example:
    python cli.py AAPL
    python cli.py NVDA
"""

import sys
import stock_core as sc

def format_delta(pct, dollar=None):
    if pct is None:
        return "N/A"
    sign = "+" if pct >= 0 else ""
    if dollar is not None:
        return f"{sign}{pct:.2f}% ({sign}${dollar:.2f})"
    return f"{sign}{pct:.2f}%"

def run_cli(symbol: str):
    print("\n" + "=" * 65)
    print(f"  FETCHING STOCK ANALYSIS FOR: {symbol.upper()}")
    print("=" * 65)

    try:
        data = sc.get_stock_data(symbol)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

    hist = data["history"]
    curr_price = data["current_price"]
    info = data["info"]

    growth = sc.calculate_growth_metrics(hist, curr_price)
    volume = sc.calculate_volume_metrics(hist, curr_price, info)
    outlook = sc.calculate_two_week_outlook(hist, data["ticker_obj"], curr_price, info)
    quarterly = sc.calculate_quarterly_results(data["ticker_obj"], hist)

    # 1. Company Header
    print(f"\n🏢 {data['short_name']} ({data['symbol']}) | Exchange: {data['exchange']}")
    print(f"   Sector: {data['sector']} | Industry: {data['industry']}")
    print(f"   Current Price: ${curr_price:.2f} | Day Change: {format_delta(data['change_pct'], data['change_abs'])}")
    print(f"   Day Range: ${data['day_low']:.2f} - ${data['day_high']:.2f} | 52W Range: ${data['fifty_two_week_low']:.2f} - ${data['fifty_two_week_high']:.2f}")

    # 2. Growth Summary
    print("\n" + "-" * 65)
    print("📊 STOCK GROWTH SUMMARY")
    print("-" * 65)
    for k in ["1_week", "3_month", "6_month", "1_year", "ytd"]:
        g = growth.get(k, {})
        if g.get("available"):
            print(f"  • {g['label']:<10}: {format_delta(g['growth_pct'], g['change_dollar']):<20} (Start: ${g['start_price']:.2f} on {g['start_date']})")
        else:
            lbl = g.get('label', k)
            print(f"  • {lbl:<10}: Not available")

    # 3. Volume of Trade
    print("\n" + "-" * 65)
    print("📦 VOLUME OF TRADE")
    print("-" * 65)
    print(f"  • Today's Volume    : {volume['current_volume']:,} shares")
    print(f"  • 10-Day Avg Volume : {volume['avg_volume_10d']:,} shares")
    print(f"  • 3-Month Avg Volume: {volume['avg_volume_3m']:,} shares")
    print(f"  • Relative Volume   : {volume['rvol_10d']:.2f}x ({volume['volume_status']})")
    print(f"  • Dollar Volume     : ${volume['dollar_volume']:,.0f}")

    # 4. 2-Week Outlook
    print("\n" + "-" * 65)
    print(f"🔮 2-WEEK STOCK OUTLOOK: {outlook['verdict_icon']} {outlook['verdict'].upper()} (Score: {outlook['composite_score']:+d}/100)")
    print("-" * 65)
    print(f"  • Projected Target  : ${outlook['projected_target_2w']:.2f} ({outlook['expected_change_pct']:+.2f}%)")
    print(f"  • Expected Range    : [${outlook['expected_range_lower']:.2f} - ${outlook['expected_range_upper']:.2f}] (80% Confidence)")
    print(f"  • Expected Volatility: ±{outlook['expected_volatility_2w_pct']:.2f}%")
    print(f"  • Summary           : {outlook['outlook_desc']}")
    print("  • Key Drivers:")
    for r in outlook["rationales"]:
        print(f"     - {r}")
    if outlook.get("target_mean"):
        print(f"  • Wall Street Consensus: Mean Target ${outlook['target_mean']:.2f} ({format_delta(outlook.get('analyst_upside_pct'))} move) across {outlook['num_analysts']} analysts")

    # 5. Quarterly Results
    print("\n" + "-" * 65)
    print("📅 QUARTERLY RESULTS & PERFORMANCE")
    print("-" * 65)
    if quarterly.get("is_etf_or_fund"):
        print(f"  ℹ️ {quarterly['message']}")
    else:
        # Next
        nq = quarterly.get("next_earnings")
        if nq:
            eps_str = f"${nq['eps_estimate']:.2f}" if nq.get("eps_estimate") is not None else "Pending"
            print(f"  🔔 Next Quarterly Results: {nq['date']} (in ~{nq['days_until']} days) | Est EPS: {eps_str}")
        else:
            print("  🔔 Next Quarterly Results: Not yet announced")

        # Last
        lq = quarterly.get("last_earnings")
        if lq:
            print(f"\n  📢 Last Quarterly Results: {lq['date']} ({lq['timing']})")
            surp_str = f"({lq['surprise_pct']:+.2f}% surprise)" if lq.get("surprise_pct") is not None else ""
            print(f"     • Result: {lq['beat_status']} {surp_str} (Reported: ${lq.get('eps_reported', 0):.2f} vs Est: ${lq.get('eps_estimate', 0):.2f})")
            if lq.get("has_reaction"):
                print(f"     • Reaction Date       : {lq['reaction_date']}")
                print(f"     • Prior -> Post Close : ${lq['prior_close']:.2f} -> ${lq['reaction_close']:.2f}")
                print(f"     • 1-Day Stock Reaction: {format_delta(lq['perf_1d_pct'])}")
                if lq.get("perf_3d_pct") is not None:
                    print(f"     • 3-Day Reaction      : {format_delta(lq['perf_3d_pct'])}")
                if lq.get("perf_1w_pct") is not None:
                    print(f"     • 1-Week Reaction     : {format_delta(lq['perf_1w_pct'])}")
        else:
            print("  📢 Last Quarterly Results: Details not found")

    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run_cli(ticker)
