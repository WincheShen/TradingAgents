# TradingAgents Prompt Optimization — Backlog

## Completed

### Sprint 1 — HOLD Bias Prompt Fix (commit 8b071e2)
- [x] **S1-1** Neutral Debator: "balanced mediator" → "evidence-based judge"
- [x] **S1-2** Trader: 3-tier (BUY/HOLD/SELL) → 5-tier (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)
- [x] **S1-3** Portfolio Manager: added explicit HOLD-usage guardrails
- [x] **S1-4** A/B test: ETN HOLD→OVERWEIGHT, BILI HOLD→OVERWEIGHT, 002028 HOLD→UNDERWEIGHT

### Sprint 2 — Debate Depth + Data Confidence (commit ed9bc27)
- [x] **S2-1** default_config: max_debate_rounds 1→2, max_risk_discuss_rounds 1→2
- [x] **S2-2** Fundamentals Analyst: Data Availability block + no-fabrication rule
- [x] **S2-3** Social Media Analyst: Data Availability block + transparent "Proxy (news-based)" label
- [x] **S2-4** A/B test: ETN OVERWEIGHT→UNDERWEIGHT (conservative rebuttal), BILI stable OVERWEIGHT

---

## Sprint 3 (P2) — Engineering & Memory

| ID | Task | Rationale | Effort |
|----|------|-----------|--------|
| S3-1 | Research Manager: add structured confidence output (score 0-100 + evidence strength) | Helps downstream Trader/PM calibrate conviction | Prompt change, low |
| S3-2 | Social Media Analyst: integrate real sentiment data source (Xueqiu/Eastmoney/Reddit) | Current tool is just `get_news()`; sentiment is inferred, not measured | New tool + vendor, medium |
| S3-3 | Memory system: record post-decision returns (1d/5d/max_drawdown) for each run | Prerequisite for any memory improvement; currently no outcome tracking | Schema + hook, medium |
| S3-4 | Memory system: add time-decay weighting to BM25 retrieval | Recent memories should weigh more than stale ones | Algorithm change, low |
| S3-5 | Memory system: evaluate BM25 → embedding upgrade (only if sample >50) | BM25 is lexical; embeddings capture semantic similarity | Evaluation + optional migration, medium |

## Sprint 4 (P3) — Advanced Prompt & Architecture

| ID | Task | Rationale | Effort |
|----|------|-----------|--------|
| S4-1 | Market Analyst: dynamic indicator selection based on market regime (trend/range/extreme) | Current prompt selects up to 8 indicators regardless of context | Prompt + optional classifier, medium |
| S4-2 | Portfolio Manager: structured output (JSON schema) for machine-readable decisions | Currently free-text; hard to parse programmatically | Prompt + parser, medium |
| S4-3 | Add A-share-specific context to prompts (涨跌停/T+1/板块联动) when market=cn | LLM may not account for A-share trading rules | Prompt conditional, low |
| S4-4 | Dynamic prompt adjustment based on VIX / market volatility regime | Increase risk weight in extreme markets, reduce in calm markets | Config + prompt template, medium |
| S4-5 | Backtesting harness: run N stocks × M dates, aggregate signal accuracy vs actual returns | Currently no systematic way to measure prompt change impact | Script, high |

---

## Decision Log

| Date | Change | Result |
|------|--------|--------|
| 2026-05-10 | S1: Prompt fix (Neutral/Trader/PM) | 3/3 stocks broke out of HOLD |
| 2026-05-10 | S2: debate rounds 1→2 + data confidence | ETN flipped to UNDERWEIGHT (valid); BILI held OVERWEIGHT (stable) |

## Notes

- **Do NOT** blindly reduce HOLD rate. HOLD is correct for most stocks most days. The goal is to prevent strong signals from being neutralized.
- **Debate rounds > 2** showed diminishing returns in initial testing — arguments start repeating. Keep at 2 unless evidence suggests otherwise.
- **002028 gave SELL with partial data** (AKShare proxy failure for indicators). Sprint 2's data confidence flags should help downstream agents discount incomplete analyses, but this needs verification once AKShare connectivity is stable.
- **ETN instability across runs** (OVERWEIGHT in S1, UNDERWEIGHT in S2) may indicate the stock is genuinely on the fence. Consider running each test 3× and taking majority vote for more robust evaluation.
