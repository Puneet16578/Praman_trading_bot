# Praman Expert Desk — Design

**This is the reference document for every phase of the Desk.** The Desk is a new, separate layer
built on top of Praman (the research system in the rest of this repository). Praman is complete and
its pre-registration is frozen. **The Desk reads Praman; it never modifies it.** Phase 1 contains no
LLM and makes no network calls in its assessment path.

Dated 2026-09-27, at the start of Phase 1 (the deterministic core).

---

## Purpose

A personal decision platform acting as research analyst, quant researcher, risk manager, portfolio
manager, trading journal, and red team. For any stock under consideration it answers: (1) what is
actually happening, (2) why it might be happening, (3) what evidence contradicts that, (4) whether
the opportunity is worth the risk given the whole portfolio, (5) what would prove the thesis wrong.

**It never outputs BUY.** Its outputs are decision states: `INSUFFICIENT`, `RESEARCH_REQUIRED`,
`WATCH`, `ELIGIBLE`, `VETO`, `EXPIRED`. The human makes every decision and places every order
manually.

## Constitution

1. **Point-in-time everything**: every record carries event date, knowledge date, and `recorded_at`.
2. **The LLM (later phases) reads, challenges, and explains. It never forecasts, calculates, or
   decides.** Enforced in software, not by prompt.
3. **Gates, not scores.** Abstention is a first-class outcome. No numeric trade score for anything
   unvalidated: an UNVALIDATED probability or expected value is displayed with that label and never
   ranks, gates, sizes or changes the state of a trade. (Amended 2026-10-04; see Changelog.)
4. **Market and sector context change risk limits, never trade direction.**
5. **Probabilities come from statistical models or from the user — never from an LLM, and never
   invented.** A model probability must come from a statistical model fitted and calibrated on
   point-in-time data and validated out-of-sample. A model probability or expected value is
   display-only and labelled UNVALIDATED until it passes the T4 calibration gate. The T4 calibration
   gate's pass criteria are pre-registered before any model is evaluated against them. User
   probabilities do not influence position sizing until the evaluator shows they are calibrated.
   (Amended 2026-10-04; see Changelog.)
6. **Every decision is reproducible**: store watermark, rulebook hash, code commit, model and prompt
   versions.
7. **Forward-window firewall**: no outcome computation for catalogue events dated 2026-09-16 onward
   before the binding evaluation (no earlier than early June 2027). The frozen pre-registration and
   pinned pipeline are never modified.
8. **Personal use only.** No shared or public output.
9. **Paper before live.** Live use only after the rulebook's pre-committed criteria are met. Order
   placement is always manual.

## Architecture

- **L0 Data & store** (Praman, read-only)
- **L1 Evidence** (quality gate, epistemic types, provenance, firewall, coverage)
- **L2 Context engines** (market state, sector, events/catalysts, fundamentals, analogues/base
  rates, drift)
- **L3 Thesis & challenge** (thesis graph, analyst roles, red team, pre-mortem, scenarios, evidence
  updater)
- **L4 Risk & portfolio** (six-layer risk officer, costs, correlation, risk-based portfolio manager)
- **L5 Decision** (states, human decision, append-only journal)
- **L6 Monitoring** (what-changed, five exit triggers, edge/drift)
- **L7 Learning** (post-trade scientist, "what did I miss?", calibration, research memory, strategy
  lab, model lab)

## Workflow

**Nightly:** ingest → quality gate → read new disclosures → refresh context → log opportunities
(inputs and states only) → monitor positions and watchlist → morning brief.

**Per idea:** intake (user thesis as hypotheses) → evidence assembly → sufficiency gate → context →
thesis graph → challenge → verification → evidence update → risk officer → portfolio manager →
decision state → human decision → journal.

**After a trade:** nightly monitoring → exit on a trigger → post-trade scientist → "what did I
miss?" (public before the decision? recorded in the store? → process failure / ingestion failure /
unknowable) → research memory.

**Periodic:** weekly behavioural review; monthly evaluator; quarterly strategy and model labs; June
2027 binding evaluation.

## Build order

Phase A adds an inputs-only opportunity log for the existing unusual-move
catalogue. A later phase will add a daily table of every eligible stock-day with
anomaly flags, so research is not limited to events the catalogue already notices.
That daily universe table is not part of Phase A.

1. Deterministic core.
2. Market and sector context.
3. Minimal fundamentals slice.
4. LLM foundation and disclosure reader.
5. Event and catalyst intelligence.
6. Analogues and evidence updater.
7. Challenge (roles, red team, pre-mortem, scenarios).
8. Portfolio intelligence.
9. Evaluator.
10. Strategy lab.
11. Fine-tuning.
12. Full fundamentals and accounting forensics.
13. Drift and edge monitoring.
14. Paper cockpit, then constrained live use; execution integration last, if ever.

The trading blueprint's phases T0-T10 are mapped onto these steps, with the user-approved
amendments and the open constitution conflicts, in `docs/desk/TRADING_BLUEPRINT.md`.

## Excluded

Return-prediction fine-tuning, reinforcement learning for trading, autonomous order placement,
intraday high-frequency trading, technical-indicator collections, self-modifying agents,
model-invented probabilities, any public output.

## Success

Honest calibration; vetoed opportunities measurably underperform passed ones; falling rule
violations; no loss ever exceeds budget; (later) disclosure extraction above a pre-registered
accuracy bar and zero unverified numbers in any output. A persistent edge is a bonus, not the goal.

## Changelog

**2026-10-06 — Strategy 0 v3: seeded random candidate order; v2 superseded after one run
(approved by the user in their message of 2026-10-06).** Before (v2): the day's SCREEN_PASS
candidates were taken in symbol order and accepted greedily against the open-risk budget, so the
spelling of a symbol decided which candidates were traded when not all fit (2026-10-05: 37 passed,
2 accepted, 35 rejected on the budget). After (v3): the same greedy budget rule over a seeded random
order: seed = sha256("S0-v3-candidate-order|<decision date>"), each candidate ranked by
sha256("<seed>|<symbol>"), ties by opportunity_id; the seed and the order are recorded with each
run. Nothing else changes. v2 ran once (2026-10-05) and is marked SUPERSEDED_AFTER_ONE_RUN; its two
pending positions stay in the one Strategy 0 book, keep version 2 on every event and count against
the same budget. A run date is processed once across versions, and the fill-failure streak counts
every version's entries.

**2026-10-04 — manual decisions are sized at the entry limit price; Strategy 0 v2 likewise
(approved by the user in their message of 2026-10-04, after follow-up 3 passed).** Before: `desk
assess` sized at the thesis `planned_entry`; Strategy 0 used the screening quantity sized at the
decision price. After: both size with the same rulebook function at the day limit order's price
(manual: `planned_entry` + 0.5 × ATR20; Strategy 0: decision price + 0.5 × ATR20), so a limit
fill can never exceed the per-trade cap. Research screening keeps decision-price sizing. Strategy 0
v1 stays in the registry as superseded before it ever ran.

**2026-10-04 — manual paper entry convention switched to the limit entry (approved by the user in
their message of 2026-10-04, following `docs/desk/shadow_replay_followup2_review.md`).** Before: fill
at the next eligible session's open. After: a day limit order at the decision's sizing price
(thesis `planned_entry`) + 0.5 × ATR20 at the decision date; fill at the open if at or below the
limit, else at the limit if the session low reaches it, else NO FILL (cancelled, not carried).
Quantity unchanged. Implemented in `desk/paper/open.py`; user guide `docs/desk/HOW_TO_PAPER_TRADE.md`.

**2026-10-04 — constitution items 3 and 5 amended (approved by the user in their message of
2026-10-04, resolving the conflict recorded in `docs/desk/TRADING_BLUEPRINT.md`).**

- Item 3, before: "**Gates, not scores.** Abstention is a first-class outcome. No numeric trade
  score anywhere." After: the "no numeric trade score" rule still applies to anything unvalidated;
  an UNVALIDATED probability or expected value is displayed with that label and never ranks, gates,
  sizes or changes the state of a trade.
- Item 5, before: "**Probabilities come from data or from the user, never from a model.** User
  probabilities do not influence position sizing until the evaluator shows they are calibrated."
  After: probabilities may come from statistical models fitted and calibrated on point-in-time data
  and validated out-of-sample, or from the user — never from an LLM, and never invented. A model
  probability or expected value is display-only and labelled UNVALIDATED until it passes the T4
  calibration gate. The user-probability sizing rule is unchanged.
- `CLAUDE.md` Desk invariants D3 and D5 were amended to the same wording later on 2026-10-04,
  with the user's explicit approval, adding to D5 (and here to item 5): "The T4 calibration gate's
  pass criteria are pre-registered before any model is evaluated against them."

**2026-10-04 — Build order gains a pointer** to the blueprint phase mapping in
`docs/desk/TRADING_BLUEPRINT.md` (session item B1). No rule changed.
