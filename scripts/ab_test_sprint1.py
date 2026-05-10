#!/usr/bin/env python3
"""Sprint-1 A/B test: run modified prompts on the same stocks that previously
returned HOLD across all levels, and compare the new decisions.

Baseline (old prompts):
  002028 2026-04-21 → Trader HOLD, Neutral HOLD, Portfolio HOLD
  BILI   2026-04-22 → Trader HOLD, Neutral HOLD, Portfolio HOLD
  ETN    2026-04-23 → Trader HOLD, Neutral HOLD, Portfolio HOLD

Usage:
  python scripts/ab_test_sprint1.py                   # run all 3
  python scripts/ab_test_sprint1.py ETN 2026-04-23    # run one
"""
import sys, os, json, datetime

# ── ensure the package is importable from the repo root ──────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ── test matrix ──────────────────────────────────────────────────────
TEST_CASES = [
    ("ETN",    "2026-04-23"),
    ("BILI",   "2026-04-22"),
    ("002028", "2026-04-21"),
]

BASELINE = {
    "ETN":    {"trader": "HOLD", "neutral": "HOLD", "portfolio": "Hold"},
    "BILI":   {"trader": "HOLD", "neutral": "HOLD", "portfolio": "Hold"},
    "002028": {"trader": "HOLD", "neutral": "HOLD", "portfolio": "Hold"},
}

# ── config ───────────────────────────────────────────────────────────
config = DEFAULT_CONFIG.copy()
config["deep_think_llm"]  = "gpt-5.3-chat"
config["quick_think_llm"] = "gpt-5.3-chat"
config["max_debate_rounds"] = 2
config["max_risk_discuss_rounds"] = 2

# For A-share stock 002028, use akshare
config_cn = config.copy()
config_cn["market"] = "cn"
config_cn["data_vendors"] = {
    "core_stock_apis": "akshare",
    "technical_indicators": "akshare",
    "fundamental_data": "akshare",
    "news_data": "akshare",
}

def extract_decisions(final_state):
    """Pull Trader / Neutral / Portfolio decisions from the graph state."""
    trader_plan = final_state.get("trader_investment_plan", "")
    risk_state  = final_state.get("risk_debate_state", {})
    neutral_resp = risk_state.get("current_neutral_response", "")
    portfolio    = risk_state.get("judge_decision", "")

    def find_proposal(text):
        for line in text.split("\n"):
            if "FINAL TRANSACTION PROPOSAL" in line.upper():
                return line.strip()
        return "(not found)"

    def find_rating(text):
        for line in text.split("\n"):
            low = line.lower().strip()
            if any(k in low for k in ["**rating", "rating:", "1. **rating"]):
                return line.strip()
        # fallback: look for the signal processor keywords anywhere
        for keyword in ["Buy", "Overweight", "Hold", "Underweight", "Sell"]:
            if f"**{keyword}**" in text[:500]:
                return f"Rating: {keyword} (extracted from bold)"
        return "(not found)"

    def find_neutral_stance(text):
        """Neutral no longer uses FINAL TRANSACTION PROPOSAL. Extract its verdict."""
        proposal = find_proposal(text)
        if proposal != "(not found)":
            return proposal
        # Look for stance keywords in the last portion
        tail = text[-800:].lower()
        for stance in ["buy", "overweight", "hold", "underweight", "sell"]:
            if f"lean toward {stance}" in tail or f"side with the {stance}" in tail:
                return f"Leans: {stance.upper()}"
        # Check which side it picks
        if "conservative" in tail and ("better-supported" in tail or "stronger" in tail):
            return "Leans: CONSERVATIVE (Hold/Underweight)"
        if "aggressive" in tail and ("better-supported" in tail or "stronger" in tail):
            return "Leans: AGGRESSIVE (Buy/Overweight)"
        return "(stance unclear)"

    return {
        "trader_proposal": find_proposal(trader_plan),
        "neutral_stance": find_neutral_stance(neutral_resp),
        "portfolio_rating": find_rating(portfolio),
    }

def run_one(ticker, trade_date):
    """Run a single stock through the graph and return extracted decisions."""
    use_cn = not ticker.isalpha()  # simple heuristic: 002028 → CN
    cfg = config_cn if use_cn else config
    ta = TradingAgentsGraph(debug=False, config=cfg)
    final_state, signal = ta.propagate(ticker, trade_date)
    decisions = extract_decisions(final_state)
    decisions["signal"] = signal
    # Also store raw text snippets for debugging
    risk_state = final_state.get("risk_debate_state", {})
    decisions["neutral_raw_tail"] = risk_state.get("current_neutral_response", "")[-500:]
    decisions["portfolio_raw_tail"] = risk_state.get("judge_decision", "")[-500:]
    return decisions

# ── main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        cases = [(sys.argv[1], sys.argv[2])]
    elif len(sys.argv) == 2:
        cases = [(c[0], c[1]) for c in TEST_CASES if c[0] == sys.argv[1]]
    else:
        cases = TEST_CASES

    results = {}
    for ticker, date in cases:
        print(f"\n{'='*60}")
        print(f" Running {ticker} @ {date}")
        print(f"{'='*60}")
        try:
            decisions = run_one(ticker, date)
            results[ticker] = decisions
            print(f"\n  [NEW] Trader   : {decisions['trader_proposal']}")
            print(f"  [NEW] Neutral  : {decisions['neutral_stance']}")
            print(f"  [NEW] Portfolio: {decisions['portfolio_rating']}")
            print(f"  [NEW] Signal   : {decisions['signal']}")
            old = BASELINE.get(ticker, {})
            print(f"  [OLD] Trader   : {old.get('trader', '?')}")
            print(f"  [OLD] Neutral  : {old.get('neutral', '?')}")
            print(f"  [OLD] Portfolio: {old.get('portfolio', '?')}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results[ticker] = {"error": str(e)}

    # Save results
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"ab_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")
