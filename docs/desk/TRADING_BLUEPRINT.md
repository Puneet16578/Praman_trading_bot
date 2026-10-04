# Praman trading blueprint

Extracted from `docs/desk/blueprint/Praman_High_Selectivity_Trading_System_Blueprint.pdf` (SHA-256 `92e91128277bae0c2112a6916dc6042373a78ebeb2ea0832f55bd0435e675e39`) by `python scripts/extract_trading_blueprint.py` using pdfplumber. The text above the amendments marker is regenerated from the PDF; the user-approved "Praman amendments" below it are maintained by hand and take precedence over the blueprint where they differ. CLAUDE.md and AGENTS.md take precedence over both.

## PRAMAN

## Personal High-Selectivity Trading System

Refined Architecture, Development Roadmap and Agent Instruction Pack Objective: build a selective, auditable system that may take zero to a few trades when evidence, calibrated probability, expected value and risk controls align.

#### Important boundary

The objective is not to guarantee profit or force daily trading. The system must be designed to abstain. Profitability must be demonstrated by point-in-time historical testing, forward paper trading and small-capital live validation before automation is trusted. Prepared as an instruction-ready specification for coding agents

<!-- end of PDF page 1 -->

## How to use this document

- Give the relevant phase section to Codex/Claude/Antigravity. Do not ask an agent to implement the entire document in one session.
- Treat the existing repository, frozen pre-registration, AGENTS.md/CLAUDE.md, HANDOFF.md and tests as the source of truth.
- Implement one bounded feature at a time, add tests, run the full suite at the phase boundary, update HANDOFF.md, commit and push.
- Do not modify protected historical/forward experiments after seeing outcomes. New trading research should be registered separately.

| Section | Purpose |
|---|---|
| 1. Product definition | What Praman should become and what it must not become |
| 2. Target architecture | The full trading pipeline |
| 3. Decision contract | Exact outputs and abstention logic |
| 4. Intelligence modules | Market, sector, event, fundamental, analogue and model layers |
| 5. Alpha and confidence | Labels, models, calibration, uncertainty and meta-selection |
| 6. Risk / portfolio / execution | Deterministic safety layer and realistic fills |
| 7. Evaluation | How to prove value without fooling ourselves |
| 8. Automation levels | Paper -> assisted -> small live -> automated |
| 9. Build roadmap | Fastest sensible implementation order |
| 10. Acceptance criteria | Definition of done for each stage |
| 11. Master agent prompt | Copy-paste instruction for coding agents |

<!-- end of PDF page 2 -->

## 1. Product definition

#### One-line definition

Praman should become an evidence-constrained, high-selectivity personal trading decision system for NSE equities that scans broadly, trades rarely, quantifies uncertainty and expected value, enforces deterministic risk, and defaults to NO TRADE when evidence is insufficient.

### Current Praman vs. trading Praman

| Current forensic layer | New trading layer |
|---|---|
| Explains unusual price moves | Estimates whether a tradable opportunity exists |
| Measures disclosures, delivery, volume, surveillance and subsequent behaviour | Combines market/sector context, alpha models, event/fundamental evidence, analogues and portfolio constraints |
| Avoids manipulation conclusions | Avoids profit guarantees and unsupported confidence claims |
| Deterministic, point-in-time and auditable | Keeps the same audit discipline while adding trading-specific targets and execution |
| Research output | NO TRADE / LONG CANDIDATE / SHORT CANDIDATE, followed by risk and execution checks |

### Core design principles

- Abstention first: zero trades is a valid and often desirable outcome.
- Probability is not enough: require positive expected value after costs and acceptable downside.
- Calibrated confidence: a reported 70% must mean approximately 70% on comparable unseen cases.
- Point-in-time or nothing: no future knowledge in features, labels, analogues, fundamentals or disclosures.
- AI for interpretation; deterministic code for calculations, gates, PnL, risk, sizing and execution constraints.
- Separate long and short research; do not treat low long probability as a short signal.
- Every decision must be reproducible from data snapshot, code commit, rulebook and model version.
- No automatic capital deployment until paper/live readiness gates are satisfied.

<!-- end of PDF page 3 -->

## 2. Target architecture

```
NSE / filings / market / sector / fundamentals
|
v
Bitemporal point-in-time store
|
v
Opportunity detection layer
|
v
Forensic + event + fundamental evidence
|
v
Market / sector / regime context
|
v
Alpha model ensemble
P(up), P(down), expected return, MFE/MAE
|
v
Calibration + uncertainty layer
|
v
Meta-model / trade selector
|
v
Historical analogues + expected value
|
v
Deterministic risk + portfolio vetoes
|
v
NO TRADE / LONG / SHORT
|
v
Execution constraints + fill validation
|
v
Position monitor + thesis monitor
|
v
Exit -> journal -> evaluator -> drift
```

### Separation of responsibilities

| Layer | Allowed | Not allowed |
|---|---|---|
| LLM / language layer | Read disclosures, extract structured events, summarize evidence, generate bull/bear/skeptic arguments | Calculate PnL, size positions, change risk limits, decide final execution |
| ML / statistical layer | Estimate directional probabilities, expected returns, adverse/favorable excursion, meta-selection | Override hard risk or data-quality vetoes |
| Deterministic engine | Costs, sizing, risk budgets, portfolio caps, data freshness, execution checks, journal, replay | Invent evidence or infer unavailable facts |
| Human / policy | Approve risk policy, decide automation level, review ambiguous cases | Change frozen research after seeing protected outcomes |

<!-- end of PDF page 4 -->

## 3. Decision contract

#### The system should not output a naked BUY/SELL score

Every candidate must expose evidence quality, calibrated probability, uncertainty, expected value, downside, liquidity, portfolio effect and the reason it is accepted or rejected.

### Candidate output schema

```
symbol
direction: LONG | SHORT | NONE
horizon: 1d | 3d | 5d | 10d
state: NO_TRADE | WATCH | ELIGIBLE | VETO
calibrated_probability
probability_interval / uncertainty_score
expected_net_return_after_costs
expected_loss_if_wrong
expected_value
maximum_adverse_excursion_estimate
maximum_favorable_excursion_estimate
historical_analogue_count
market_regime
sector_regime
evidence_completeness
forensic_flags
liquidity_state
portfolio_incremental_risk
invalidations[]
rejection_reasons[]
model_version / rulebook_version / data_as_of / commit_hash
```

### Final state logic

| State | Meaning |
|---|---|
| NO_TRADE | No candidate has enough evidence/edge; normal system output. |
| WATCH | Interesting but one or more required conditions are not yet satisfied. |
| ELIGIBLE | All research and deterministic risk conditions are satisfied; still subject to execution checks. |
| VETO | Hard data, risk, liquidity, surveillance, portfolio, execution or operational rule blocks the trade. |

#### Critical rule

Do not impose a daily trade quota. The scanner may inspect thousands of stock-days and produce zero eligible trades.

<!-- end of PDF page 5 -->

## 4. Intelligence modules to add

| Module | Purpose |
|---|---|
| Market intelligence | Nifty/equal-weight trend, breadth, volatility, dispersion, liquidity and regime. A stock signal is interpreted within market conditions. |
| Sector intelligence | Stock-vs-sector and sector-vs-market relative strength; sector breadth and volatility; prevents treating a broad sector move as stock-specific alpha. |
| Opportunity detector | Scans the whole eligible universe for unusual price/volume/delivery, relative-strength changes, disclosures and other preregistered triggers. |
| Event intelligence | Parses exchange announcements and classifies event type, direction, magnitude, novelty, certainty, effective date and source. |
| Minimal fundamentals | Revenue, profit, margins, cash flow, debt, coverage, ROE/ROCE, promoter holding/pledge and valuation using point-in-time availability. |
| Expectation vs. reality | Normalizes event size by company scale and, where legitimate data exists, compares reported outcomes with prior expectations. |
| Historical analogue engine | Finds genuinely comparable historical setups and reports base rates, return distribution, MFE, MAE and target-before-stop frequencies. |
| Bull/Bear/Skeptic/Pre-mortem | Structured challenge layer that identifies supporting evidence, contradictions, shared assumptions and plausible failure paths. |
| Portfolio intelligence | Correlation, sector concentration, beta/factor concentration, liquidity concentration, stress loss and effective number of independent bets. |
| Drift monitor | Tracks calibration, feature distributions, expectancy, slippage and performance by regime; can automatically downgrade models to paper-only. |

<!-- end of PDF page 6 -->

## 5. Alpha, confidence and trade selection

### 5.1 Trading-specific labels

- Preserve the frozen forensic/forward experiment. Create a separate trading research registry and separate labels.
- Evaluate multiple horizons: 1, 3, 5 and 10 sessions. Do not assume one horizon works for every signal family.
- Prefer path-aware labels (target-before-stop / stop-before-target / timeout) over only terminal return.
- Use volatility-adjusted barriers and account for executable next-session prices and costs.
- Generate LONG and SHORT labels separately and respect real-world execution constraints.

### 5.2 Model stack

| Component | Recommended starting point | Reason |
|---|---|---|
| Baseline | Logistic regression | Interpretable benchmark; exposes whether complexity is actually needed. |
| Tree model | LightGBM or XGBoost | Strong for nonlinear tabular interactions and missingness. |
| Alternative | Random Forest / ExtraTrees | Diversity for ensemble disagreement. |
| Sequence model | Only after tabular baselines | Use only if walk-forward evidence shows incremental value. |
| LLM | Not an alpha calculator | Use for structured reading/extraction, not return prediction. |

### 5.3 Calibration and uncertainty

- Calibrate probabilities out-of-sample using Platt/logistic scaling or isotonic regression as appropriate.
- Report reliability diagrams and Brier score; do not call raw model scores probabilities unless calibrated.
- Quantify uncertainty with bootstrap/model dispersion/conformal or other preregistered methods appropriate to the model.
- Require both sufficiently high calibrated probability and sufficiently low uncertainty.

### 5.4 Meta-selection

#### Recommended structure

Stage A predicts direction/return characteristics. Stage B predicts whether Stage A should be trusted enough to trade. This allows the system to reject most model predictions.

```
Broad universe
-> trigger / opportunity
-> directional models
-> calibration
-> meta-selector
-> evidence / analogue checks
-> risk + portfolio
-> 0 to few eligible trades
```

### 5.5 Expected value, not win rate

Core decision quantity: EV = P(win) x average win - P(loss) x average loss - costs.

- A high win rate can still lose money if losses are much larger than wins.
- Require positive expected value after brokerage, taxes/fees, slippage assumptions and realistic fill logic.

<!-- end of PDF page 7 -->

## 6. Risk, portfolio and execution

### 6.1 Deterministic risk stack

| Gate | Examples |
|---|---|
| Data validity | Freshness, as-of correctness, corporate actions, identity mapping, missing-data thresholds |
| Security risk | Liquidity, price bands/dynamic ranges, surveillance categories, gap risk |
| Trade risk | Planned stop, stress loss, quantity, maximum position size, risk/reward |
| Portfolio risk | Open-risk budget, sector concentration, correlation clusters, beta/factor concentration |
| Behavior/operations | Drawdown brake, losing-streak brake, open high-severity defects, stale ingestion, backup/restore health |
| Execution | Maximum acceptable gap/slippage, actual fill risk recheck, no-fill/suspension handling |

### 6.2 Execution policy

- Decision price and research evidence are frozen at decision time.
- Execution is a separate append-only event using an actually available future price.
- Before any live order, apply a maximum acceptable entry/slippage policy. If the opportunity deteriorates before fill, cancel rather than chase.
- After fill, recompute actual risk and portfolio impact. Never silently resize or change a frozen historical experiment.
- Short execution must have its own adapter for actual instrument availability and applicable exchange/broker rules.

### 6.3 Kill switches

| Condition | Required action |
|---|---|
| Stale or inconsistent market data | NO NEW TRADES |
| Risk state unavailable | NO NEW TRADES |
| Daily/weekly drawdown limit breached | Freeze new entries; manage exits only |
| Repeated order/execution failures | Disable automated execution |
| Model calibration/edge degradation | Reduce size or revert model to PAPER ONLY |
| Critical unresolved defect | Operational gate fails |

<!-- end of PDF page 8 -->

## 7. How to prove the system adds value

#### Primary research objective

Do not optimize for the best-looking backtest. Optimize for evidence that survives unseen time periods, realistic costs, parameter perturbations and regime changes.

### Evaluation ladder

```
Development period
-> walk-forward / purged validation
-> untouched holdout
-> forward shadow opportunities
-> paper trading
-> small live capital
-> scale only after edge-confidence gate
```

| Audit dimension | Minimum evidence |
|---|---|
| Discrimination | AUC/PR metrics where appropriate, but never as the only trading metric |
| Calibration | Reliability curve, Brier score, observed win rate by probability bucket |
| Economics | Net expectancy after costs, profit factor, payoff ratio, benchmark-relative return |
| Tail risk | MAE, severe-loss frequency, gap-through-stop, circuit/illiquidity stress where data permits |
| Stability | Performance by year/regime/sector/cap bucket; parameter-neighbour stability |
| Uncertainty | Bootstrap confidence intervals and explicit sample counts |
| Multiple testing | Record every attempted strategy/parameter family; apply appropriate correction/deflated metrics |
| Process quality | Good-loss/bad-win matrix, rule adherence, overrides, missing exit provenance |
| Execution realism | Actual next-available prices, slippage/cost assumptions, no-fill cases |

### No-retrospective-tuning rule

- Once a registered experiment has been evaluated, do not alter that experiment and call the altered version the same test.
- New hypotheses are allowed, but they must become a new strategy/version with their own untouched evaluation window.
- Keep failed strategies visible in the strategy registry.

<!-- end of PDF page 9 -->

## 8. Automation levels

| Level | Mode | Requirements |
|---|---|---|
| A0 | Research only | Historical scanner/evaluator; no order creation. |
| A1 | Paper trading | Automated candidate generation and paper fills; human reviews all decisions. |
| A2 | Assisted live | System proposes trades and exact risk; human explicitly confirms each order. |
| A3 | Small-capital constrained auto | Only preapproved strategies, small size, deterministic hard gates and kill switches; human monitors. |
| A4 | Broader automation | Only after substantial live evidence, stable calibration/expectancy and operational reliability. |

#### Recommended current destination

Build toward A1 first, then A2. Do not jump directly from historical research to A3/A4.

<!-- end of PDF page 10 -->

## 9. Fastest sensible build roadmap

| Phase | Scope | Exit condition |
|---|---|---|
| T0 - Freeze & baseline | Close existing replay/evaluator defects, verified backups, clean handoff | Full suite green; current experiment frozen and reproducible |
| T1 - Market context | Market/sector regime, breadth, volatility, dispersion, relative strength | Point-in-time features + tests + historical coverage report |
| T2 - Trading dataset | 1/3/5/10-day long/short path-aware labels and opportunity dataset | No leakage; registered label definitions; reproducible dataset |
| T3 - Baseline alpha | Logistic + tree models, walk-forward evaluation | Baselines documented, costs included, no tuning on final holdout |
| T4 - Calibration/meta | Calibrated probabilities, uncertainty, meta-selector, abstention | Calibration report and selectivity/coverage curves |
| T5 - Analogues/events | Historical analogue engine + structured disclosure/event extraction | Evidence provenance and validation benchmark |
| T6 - Fundamentals | Minimal PIT fundamentals + event materiality by company scale | Coverage/freshness thresholds documented |
| T7 - Portfolio/execution | Correlation/risk clusters, fill policy, slippage, short constraints | Paper engine rejects invalid fills and portfolio breaches |
| T8 - Paper forward | Automated daily scan + paper trading + evaluator + drift | Sufficient duration/trades/opportunities; no serious rule violations |
| T9 - Assisted live | Human-confirmed small-capital execution | Operational gate passed; live monitoring/kill switches verified |
| T10 - Limited automation | Only proven strategies and predefined risk envelope | Edge-confidence gate passed with live/forward evidence |

#### Parallel work allowed

A read-only web cockpit may be built alongside T1-T7, but it must consume backend outputs and must not reimplement calculations in JavaScript.

<!-- end of PDF page 11 -->

## 10. Definition of done / acceptance criteria

| Area | Acceptance condition |
|---|---|
| Data | Every trading feature has event date + knowledge date; PIT query tests include adversarial future-data cases. |
| Labels | Trading labels are preregistered before evaluation; path ordering and global-session handling are tested. |
| Models | Every complex model beats a transparent baseline on untouched data or is rejected. |
| Calibration | Probability buckets match observed frequencies within documented uncertainty; sample counts shown. |
| Selectivity | Performance is reported as a function of coverage (e.g., top 1%, 5%, 10% candidates), not only a single threshold. |
| Costs | All headline trading metrics are after realistic fees/costs and a documented slippage model. |
| Risk | A candidate cannot bypass deterministic security/trade/portfolio/operational gates. |
| Execution | Decision, order request, fill and post-fill risk are separate append-only events. |
| Reproducibility | Decision can be replayed using commit, data snapshot/hash, rulebook, model and prompt versions. |
| Paper/live | Automation level cannot increase until the relevant readiness gate passes. |
| Monitoring | Drift/calibration/expectancy degradation can automatically downgrade a strategy to paper-only. |
| UI | Dashboard is a view/controller over backend truth; no duplicate risk/PnL logic in frontend. |

<!-- end of PDF page 12 -->

## 11. Copy-paste master instruction for coding agents

#### How to use

Do not give this whole project to one agent in one run. Paste this master instruction, then append exactly one phase/task from Section 9.

```
You are working on PRAMAN, an existing NSE forensic/research repository that is being extended into a
high-selectivity personal trading decision system.
SOURCE OF TRUTH
1. Verify the repository root and git status.
2. Read AGENTS.md / CLAUDE.md, docs/HANDOFF.md, relevant DESIGN/rulebook docs, and only the files
needed for the assigned task.
3. Existing frozen pre-registrations and protected forward windows MUST NOT be altered or evaluated
early.
4. Preserve unrelated uncommitted work.
PRODUCT OBJECTIVE
Build an auditable system that scans broadly but may take zero to a few trades. A trade is eligible
only when point-in-time evidence, calibrated probability, expected value after costs, uncertainty,
deterministic risk, liquidity and portfolio constraints align. NO TRADE is a first-class successful
output.
NON-NEGOTIABLE ARCHITECTURE
- Keep the existing forensic classifier and frozen research separate from new trading research.
- Every feature/fact must be point-in-time: event date + knowledge date + as-of reads.
- LLMs may read/extract/summarize evidence; they may not calculate PnL, position size, risk limits,
portfolio mutation or execution decisions.
- LONG and SHORT research are separate.
- Raw model scores are not probabilities until calibrated.
- Optimize expected value after costs and downside, not win rate alone.
- Deterministic risk/portfolio/operational vetoes override ML/LLM output.
- Decision, execution/fill, monitoring and exit are separate append-only events.
- Never force a daily trade quota.
- Do not add broker automation in the current task unless explicitly authorized.
ENGINEERING PROCESS
- Before edits: report baseline git status and targeted/full test state as appropriate.
- Write a short implementation plan and identify invariants affected.
- Implement only the assigned phase/task.
- Add adversarial tests, especially for PIT leakage, corporate actions, identity mapping, costs,
execution ordering and risk boundaries.
- Use temporary/read-only copies for proofs and experiments; never clear/recreate durable stores.
- Run targeted tests during development and the full suite once at the task/phase boundary.
- Update docs/HANDOFF.md with exact completed work, limitations, unresolved defects and next step.
- Commit coherent tested changes. Push when requested/available.
RESEARCH PROCESS
- Register label/metric/threshold definitions before observing evaluation results.
- Preserve all failed strategies and parameter attempts in the strategy registry.
- Report sample counts, missingness, confidence intervals and regime/year breakdowns.
- Never tune a frozen experiment after seeing its outcome. New ideas require a new version and new
evaluation.
FINAL REPORT
Return: changed files, tests, commit(s), data/research artifacts created, PASS/PARTIAL/MISSING against
the assigned acceptance criteria, unresolved defects/limitations, and the safest next task.
```

<!-- end of PDF page 13 -->

## 12. Per-phase prompt template

```
Continue PRAMAN from the current committed HANDOFF.
ASSIGNED PHASE: [insert exactly one phase/task]
Goal:
[one clear outcome]
Required deliverables:
- [module / schema / command / report]
- tests for [critical invariants]
- documentation / HANDOFF update
Acceptance criteria:
- [copy only the relevant criteria from this blueprint]
Do not:
- modify frozen preregistration or protected outcomes
- add unrelated features
- change risk limits just to improve historical performance
- rewrite deterministic calculations in the UI/LLM
- start broker automation
Work in small checkpoints. Run targeted tests during implementation and the complete suite once before
the final commit. Report PASS/PARTIAL/MISSING against every acceptance criterion.
```

### Recommended next instruction

#### Next phase after current closeout

T1 - Market and sector context: build point-in-time market/sector regime, breadth, volatility, dispersion and stock-vs-sector/market relative-strength features. Do not yet train the final trading model.

<!-- end of PDF page 14 -->

## 13. What the final user should see

```
PRAMAN - DAILY DECISION DESK
Universe scanned: 2,695
Candidates: 34
Passed evidence/data checks: 11
High-confidence model candidates: 4
Passed risk/portfolio/execution checks: 2
Candidate ABC
Direction: LONG
Calibrated P(profitable): 0.xx
Uncertainty: LOW / MEDIUM / HIGH
Expected net return: x.x%
Expected loss if wrong: x.x%
Expected value: +x.xxR
Historical analogues: N = xxx
Market: supportive / neutral / hostile
Sector: supportive / neutral / hostile
Evidence completeness: xx%
Risk: PASS
Portfolio: PASS
Execution: WAIT / ELIGIBLE / CANCEL
Final state: WATCH / ELIGIBLE / VETO
Most important output on many days:
NO TRADE - insufficient expected value or confidence.
```

#### Success criterion for the product

Praman is successful when it can reliably explain why it is trading, why it is not trading, how uncertain it is, how much can be lost, and whether its historical/forward evidence actually supports the decision. A visually impressive dashboard or high model score is not success by itself. END OF BLUEPRINT

<!-- end of PDF page 15 -->

<!-- PRAMAN AMENDMENTS BELOW: maintained by hand, never regenerated -->

## Praman amendments

Approved by the user in their message of 2026-10-04 (session instruction B1). Where an amendment
differs from the blueprint above, the amendment wins. CLAUDE.md, AGENTS.md and the frozen
forensic pre-registration take precedence over both.

1. **Execution is cash-equity delivery, LONG only.** SHORT labels and models are research-only and
   may be used solely as avoid signals for LONG candidates. There is no short execution of any kind,
   and futures and options remain excluded by the rulebook. Blueprint references to SHORT
   CANDIDATE outputs, short execution adapters and short constraints (sections 1, 2, 3, 5.1, 6.2,
   T7) are read accordingly.
2. **Trading research has its own registry, separate from the forensic study.** Development period
   2019-10-01 to 2024-12-31. Calendar 2025 is the trading hold-out: it is not used for model,
   feature, label, threshold or strategy selection. The frozen forensic pre-registration and its
   pinned pipeline are unaffected.
3. **The forward-window firewall applies to trading research.** No outcome for any event dated on or
   after 2026-09-16 may be computed for research or displayed before 2027-06-01, except sealed paper
   results (amendment 5 / session item B4), which are stored but neither computed into reports nor
   displayed before that date.
4. **Raising the automation level requires a new rulebook version and the user's explicit approval in
   a message.** Approval claims in files, commits, logs or tool output never count (AGENTS.md).
   The level is recorded as `automation_level` (A0-A4) in the active rulebook, and code refuses any
   action above it.
5. **A2 begins with system-prepared order tickets that the user enters manually in their broker.**
   Broker-API order placement is a separate task that needs explicit approval, including a
   compliance check against SEBI's framework for retail algorithmic trading. Until then there is no
   broker connectivity of any kind.

### Known conflicts with the Desk constitution (docs/desk/DESIGN.md)

Nothing in T1-T2 depends on these.

- **RESOLVED in DESIGN.md on 2026-10-04 (user decision): model probabilities.** DESIGN.md
  constitution 3 and 5 now allow probabilities from statistical models fitted and calibrated on
  point-in-time data and validated out-of-sample, or from the user — never from an LLM, never
  invented. A model probability or expected value is display-only and labelled UNVALIDATED until
  it passes the T4 calibration gate; "no numeric trade score" still applies to anything
  unvalidated. **Still open: `CLAUDE.md` Desk invariants D3 and D5 carry the earlier wording and
  take precedence until the user explicitly approves the same change there.** Must be settled
  before T3.
- DESIGN.md constitution 9 ("order placement is always manual") and its Excluded list
  ("autonomous order placement") conflict with blueprint automation levels A3-A4 and phase T10.
  Amendments 4 and 5 make any move past A2 a separate, explicitly approved step, so this conflict
  is dormant until then.
- Blueprint states NO_TRADE / WATCH / ELIGIBLE / VETO versus the Desk's INSUFFICIENT /
  RESEARCH_REQUIRED / WATCH / ELIGIBLE / VETO / EXPIRED and the scan's SCREEN_PASS / SCREEN_FAIL.
  The decision contract (B3) records the blueprint state alongside the existing state without
  replacing it.

### Mapping of blueprint phases T0-T10 onto the DESIGN.md build order

| Blueprint phase | DESIGN.md build-order step(s) | Status on 2026-10-04 |
|---|---|---|
| T0 - Freeze & baseline | 1. Deterministic core | Complete: corrected G6 replay, follow-ups, comparison and A2 context committed; full suite green |
| T1 - Market context | 2. Market and sector context | Not started (recommended next research phase) |
| T2 - Trading dataset | New: trading research registry and path-aware LONG labels (amendments 1-2); no DESIGN.md step | Not started |
| T3 - Baseline alpha | New; DESIGN.md constitution 3/5 amended 2026-10-04 to allow validated statistical-model probabilities. DESIGN.md 10 (Strategy lab) is the nearest step | Not started; CLAUDE.md D3/D5 still need the same approval |
| T4 - Calibration/meta | 9. Evaluator (calibration); 13. Drift and edge monitoring | Not started; calibration kill switch defined but inactive (B2) |
| T5 - Analogues/events | 4. LLM foundation and disclosure reader; 5. Event and catalyst intelligence; 6. Analogues and evidence updater; 7. Challenge | Not started |
| T6 - Fundamentals | 3. Minimal fundamentals slice; 12. Full fundamentals and accounting forensics | Not started |
| T7 - Portfolio/execution | 8. Portfolio intelligence; execution realism from follow-up 2 (P8-043) | Partial: fill observer, cap checks, limit-entry evidence |
| T8 - Paper forward | 14. Paper cockpit (first half); automation level A1 | Foundation in this session: Strategy 0 sealed paper burn-in, kill switches, daily brief |
| T9 - Assisted live | 14. Constrained live use; automation level A2 via manual order tickets (amendment 5) | Not started; needs a new rulebook version and approval |
| T10 - Limited automation | 14. "Execution integration last, if ever"; A3-A4 | Not started; needs the constitution 9 decision, SEBI compliance check and approval |

DESIGN.md step 11 (Fine-tuning) has no blueprint counterpart; the blueprint restricts LLMs to
reading and extraction, which is consistent with DESIGN.md's Excluded list.
