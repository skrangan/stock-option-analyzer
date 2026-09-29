"""
cli.py - Terminal Command-Line Interface for Stock & Option Analysis
Usage:
    python cli.py AAPL
    python cli.py AAPL --option call --strike 335 --bid 4.50 --exp 2026-10-16
"""

import sys
import argparse
import stock_core as sc
import options_core as oc

def format_delta(pct, dollar=None):
    if pct is None:
        return "N/A"
    sign = "+" if pct >= 0 else ""
    if dollar is not None:
        return f"{sign}{pct:.2f}% ({sign}${dollar:.2f})"
    return f"{sign}{pct:.2f}%"

def run_cli():
    parser = argparse.ArgumentParser(description="Stock & Option Analyzer CLI")
    parser.add_argument("ticker", nargs="?", default="AAPL", help="Stock ticker symbol (e.g. AAPL, NVDA, TSLA)")
    parser.add_argument("--option", choices=["call", "put"], default=None, help="Analyze an option purchase ('call' or 'put')")
    parser.add_argument("--strike", type=float, default=None, help="Option strike price ($)")
    parser.add_argument("--bid", type=float, default=None, help="Option bid amount / premium paid per share ($)")
    parser.add_argument("--exp", type=str, default=None, help="Option expiration date (YYYY-MM-DD)")
    parser.add_argument("--contracts", type=int, default=1, help="Number of option contracts (default: 1)")

    args = parser.parse_args()
    symbol = args.ticker.strip().upper()

    print("\n" + "=" * 70)
    print(f"  FETCHING ANALYSIS FOR: {symbol}")
    print("=" * 70)

    try:
        analysis = sc.get_full_stock_analysis(symbol)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

    data = analysis["raw"]
    curr_price = data["current_price"]
    growth = analysis["growth"]
    volume = analysis["volume"]
    outlook = analysis["outlook"]
    quarterly = analysis["quarterly"]

    # 1. Company Header
    print(f"\n🏢 {data['short_name']} ({data['symbol']}) | Exchange: {data['exchange']}")
    print(f"   Sector: {data['sector']} | Industry: {data['industry']}")
    print(f"   Current Price: ${curr_price:.2f} | Day Change: {format_delta(data['change_pct'], data['change_abs'])}")
    print(f"   Day Range: ${data['day_low']:.2f} - ${data['day_high']:.2f} | 52W Range: ${data['fifty_two_week_low']:.2f} - ${data['fifty_two_week_high']:.2f}")

    # 2. Growth Summary
    print("\n" + "-" * 70)
    print("📊 STOCK GROWTH SUMMARY")
    print("-" * 70)
    for k in ["1_week", "3_month", "6_month", "1_year", "ytd"]:
        g = growth.get(k, {})
        if g.get("available"):
            print(f"  • {g['label']:<10}: {format_delta(g['growth_pct'], g['change_dollar']):<20} (Start: ${g['start_price']:.2f} on {g['start_date']})")
        else:
            lbl = g.get('label', k)
            print(f"  • {lbl:<10}: Not available")

    # 3. Volume of Trade
    print("\n" + "-" * 70)
    print("📦 VOLUME OF TRADE")
    print("-" * 70)
    print(f"  • Today's Volume    : {volume['current_volume']:,} shares")
    print(f"  • 10-Day Avg Volume : {volume['avg_volume_10d']:,} shares")
    print(f"  • Relative Volume   : {volume['rvol_10d']:.2f}x ({volume['volume_status']})")
    print(f"  • Dollar Volume     : ${volume['dollar_volume']:,.0f}")

    # 4. 2-Week Outlook
    print("\n" + "-" * 70)
    print(f"🔮 2-WEEK STOCK OUTLOOK: {outlook['verdict_icon']} {outlook['verdict'].upper()} (Score: {outlook['composite_score']:+d}/100)")
    print("-" * 70)
    print(f"  • Projected Target  : ${outlook['projected_target_2w']:.2f} ({outlook['expected_change_pct']:+.2f}%)")
    print(f"  • Expected Range    : [${outlook['expected_range_lower']:.2f} - ${outlook['expected_range_upper']:.2f}] (80% Confidence)")
    print(f"  • Expected Volatility: ±{outlook['expected_volatility_2w_pct']:.2f}%")
    print(f"  • Summary           : {outlook['outlook_desc']}")

    # 5. Quarterly Results
    print("\n" + "-" * 70)
    print("📅 QUARTERLY RESULTS & PERFORMANCE")
    print("-" * 70)
    if quarterly.get("is_etf_or_fund"):
        print(f"  ℹ️ {quarterly['message']}")
    else:
        nq = quarterly.get("next_earnings")
        if nq:
            eps_str = f"${nq['eps_estimate']:.2f}" if nq.get("eps_estimate") is not None else "Pending"
            print(f"  🔔 Next Quarterly Results: {nq['date']} (in ~{nq['days_until']} days) | Est EPS: {eps_str}")
        
        lq = quarterly.get("last_earnings")
        if lq:
            print(f"  📢 Last Quarterly Results: {lq['date']} ({lq['timing']}) | Result: {lq['beat_status']} (Reported: ${lq.get('eps_reported', 0):.2f} vs Est: ${lq.get('eps_estimate', 0):.2f})")
            if lq.get("has_reaction"):
                print(f"     • 1-Day Stock Reaction: {format_delta(lq['perf_1d_pct'])} (Prior: ${lq['prior_close']:.2f} -> Post: ${lq['reaction_close']:.2f})")
                if lq.get("perf_1w_pct") is not None:
                    print(f"     • 1-Week Reaction     : {format_delta(lq['perf_1w_pct'])}")

    # 6. Option Evaluation (if option parameters supplied or default ATM)
    if args.option or args.strike or args.bid:
        opt_type = args.option or "call"
        strike = args.strike or (round(curr_price / 5.0) * 5.0)
        bid = args.bid or max(1.0, round(curr_price * 0.02, 2))
        
        exp_date = args.exp
        if not exp_date:
            exps = oc.get_available_expirations(symbol)
            exp_date = exps[min(2, len(exps)-1)] if exps else "2026-10-16"

        print("\n" + "=" * 70)
        print(f"🎯 OPTION BUY DECISION & P&L EVALUATION: {opt_type.upper()} ${strike:.2f}")
        print("=" * 70)

        trade = oc.analyze_option_trade(
            symbol=symbol,
            current_price=curr_price,
            option_type=opt_type,
            strike=strike,
            bid_amount=bid,
            expiration_date_str=exp_date,
            num_contracts=args.contracts,
            outlook=outlook
        )

        print(f"  🤖 VERDICT: {trade['verdict_icon']} {trade['verdict']} (Score: {trade['verdict_score']:+d}/100)")
        print(f"  Summary: {trade['summary_text']}\n")
        print(f"  • Expiration Date   : {trade['expiration_date']} ({trade['dte']} days to expiration)")
        print(f"  • Total Cost        : ${trade['total_investment']:,.2f} (${trade['bid_amount']:.2f}/sh × {trade['shares_controlled']} shares)")
        print(f"  • Breakeven Price   : ${trade['breakeven_price']:.2f} (Required Move: {trade['move_to_breakeven_pct']:+.2f}%)")
        print(f"  • Max Profit        : {trade['max_profit_str']}")
        print(f"  • Max Loss          : -${trade['max_loss']:,.2f} (-100%)")
        print(f"  • Probability Profit: {trade['pop']:.1f}%")
        print(f"  • Daily Theta Decay : -${abs(trade['greeks']['theta_daily_total']):.2f} / day")
        print(f"  • Delta (Δ)         : {trade['greeks']['delta']:.3f} | Gamma (Γ): {trade['greeks']['gamma']:.4f}")
        
        print("\n  📋 Checklist Rationale:")
        for r in trade["rationales"]:
            print(f"    - {r}")
        if trade["warnings"]:
            print("  ⚠️ Risk Warnings:")
            for w in trade["warnings"]:
                print(f"    - {w}")

        print("\n  📑 P&L at Expiration Matrix:")
        print(f"    {'Stock Price':<14} {'Move (%)':<10} {'Net P&L ($)':<16} {'ROI (%)':<10} {'Benchmark'}")
        print("    " + "-" * 60)
        for row in trade["scenarios"]:
            p_str = f"${row['stock_price']:.2f}"
            m_str = f"{row['stock_change_pct']:+.1f}%"
            pnl_str = f"{('+' if row['pnl_exp_dollar']>=0 else '')}${row['pnl_exp_dollar']:,.2f}"
            roi_str = f"{('+' if row['roi_exp_pct']>=0 else '')}{row['roi_exp_pct']:.1f}%"
            bench = row['label']
            print(f"    {p_str:<14} {m_str:<10} {pnl_str:<16} {roi_str:<10} {bench}")

    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    run_cli()
