# Praman — Interview Brief (30 minutes)

Every number below is cited to the committed document or script that produced it. Where a figure
was superseded during the project's own history, both the old and new values are given, with the
correction's source.

## 1. Sixty-second pitch

Praman is a forensic classifier for unusual price moves on the NSE (India's National Stock
Exchange): given a stock that moved sharply, it measures whether the move has an informational
basis (a disclosure that plausibly explains it) or carries manipulation-*consistent* signatures,
and tries to prove that classification against SEBI enforcement history, exchange surveillance
flags, and subsequent price behavior. **It never states a conclusion about manipulation** —
invariant 12, `CLAUDE.md` — only measured signals and their values.

**What it found:** the original headline result — the full system's top-tier precision clearing
disclosure-tier-alone's — was retracted by its own pre-registered robustness review
(`P8-001`, `docs/DEFECT_REGISTER.md`). It was a label artifact (the outcome label and the
classifier's core input shared an anchor point), not real signal: under a corrected label, neither
the classifier nor disclosure tier alone shows lift over its own base rate.

**What's pending:** a redesigned, four-input scoring function is pre-registered and now FROZEN
(`docs/phase10_preregistration_amendment5.md`) after five rounds of amendment — mostly spent fixing
the outcome label itself, not the model. It evaluates **forward-only**, on data that does not exist
yet; the earliest possible run is **~early June 2027**.

## 2. Architecture, in five sentences

1. Every fact carries an `event_date` and a `knowledge_date`, and every query is as-of a specific
   date — corporate-action adjustment, event cataloguing, and outcome labelling all respect this,
   and a function that reads data with no as-of parameter is treated as a bug, not a convenience
   (`CLAUDE.md` invariant 7, "bitemporal or nothing").
2. A deterministic Supervisor dispatches three specialist agents (Market Microstructure,
   Disclosure, Surveillance), each of which recomputes its own signals **live** from the bitemporal
   store, never from a cached artifact (`docs/phase7c_agent_layer.md`).
3. Every specialist tool call passes through one authorization gate (`src/mcp/tools.py`) checking
   role × tool × task-allowlist × budget, fail-closed — a role-mismatched or budget-exhausted call
   is refused outright, never logged-and-allowed anyway.
4. Before any claim reaches output, a deterministic Adversary independently re-derives it — for two
   claim types, via a second, separately-implemented recomputation path that never calls the shared
   derivation function — and runs a banned-term lint; a claim that doesn't reproduce, or that uses
   prohibited language, is dropped, not softened.
5. **No language model is called anywhere in this codebase** — confirmed by grep across all of
   `src/` and pinned by test (`OrchestratorDeterminismTest`) — because invariant 12 (never state a
   manipulation conclusion) is easier to guarantee architecturally, with no narrative-generation
   surface in the shareable path at all, than lexically, with a word list a paraphrase evades
   (measured directly: 0/11 adversarial phrasings caught, `P8-003`).

## 3. Findings, in order

1. **The headline, and its retraction (`P8-001`).** Phase 8 originally reported the full system's
   top-tier precision (90.6%, n=255) clearing disclosure-tier-alone's (78.7%, n=362) with
   non-overlapping CIs. A pre-registered robustness check found both were scored against a label
   sharing its anchor (`close(event_date−20)`) with the classifier's own core momentum input.
   Re-scored under a decoupled label: disclosure-tier-alone falls to 51.1% — exactly its own base
   rate, zero lift — and the classifier falls to 28.6% on a tiny, noisy cell (n=7, *below* base
   rate). (`docs/RESULTS.md` §1)
2. **Drift vs. coupling, decomposed.** Correcting market drift alone barely moves the classifier's
   lift (+16.4pp → +15.9pp, same anchor); only removing the *shared anchor* collapses it (to
   −22.5pp / +6.7pp). Mechanical coupling, not market drift, drove the original headline.
   (`docs/RESULTS.md` §1, `docs/phase8_robustness_checks.md`)
3. **Clean-label features, with confidence intervals.** Re-measured under the decoupled label
   (`docs/phase10_preregistration_amendment5.md` §6): `delivery_pct_percentile_60d` and
   `same_date_event_count` are weak but stable TRAIN→HOLD-OUT; the classifier's own core axis
   (`return_20d_context_only`) **reverses sign** on real 2026 hold-out data (HOLD-OUT AUC 0.4853,
   upper CI bound exactly 0.5000 — reported as borderline, not confidently "excludes 0.5"). No
   feature reverses direction across any correction round.
4. **The pre-registration, frozen.** A new four-input logistic scoring function
   (`delivery_low`, `isolated`, `volume_ratio_high_band_eligible`, disclosure tier), fit once on
   2019-2025 TRAIN data, missing-data threshold 4.3%, evaluated forward-only from 2026-09-16
   through 2027-01-15, pinned to commit `afe3e2bd07abe8b602c4119b916f7696a3c12131`. Not yet
   evaluated — no forward outcome exists. (`docs/phase10_preregistration_amendment5.md`)

## 4. The defect story — six that show the method

1. **`P8-001` — the headline retraction.** See §3.1. The single best example of this project's
   entire discipline: a strong, statistically clean-looking result, caught before shipping, by a
   pre-registered check built specifically to look for shared-anchor coupling.
2. **`P8-013` → `P8-014` — a fix for one selection bias silently created a second, worse one.**
   The original outcome label required a stock's own 90th *real* trading session — thinly-traded
   stocks take disproportionately longer in calendar time to reach that, so missingness correlated
   with `cap_band` (Micro 2.09% vs. Mega 1.20%, `P8-013`). Fixed by redefining the horizon on the
   *global* calendar instead — but the very first check of the new label's *own* missingness
   (rather than assuming the fix had worked) found it had gotten *worse*: TRAIN missing rate 6.838%,
   a 14.1pp Micro-vs-Mega gap. Root cause: the series-bridging fix from an earlier round
   (`P8-012`) only patched a *permanent* EQ→BE/BZ migration, not a *temporary* surveillance-driven
   stint — exactly the stocks this project most needs to keep. Fixed at the root (a full per-date
   bridge); final TRAIN missing rate 1.310%. (`docs/DEFECT_REGISTER.md` `P8-013`/`P8-014`)
3. **No `P7-001` exists.** A suspected `prev_close`-unadjusted bug in `close_to_close_60d` was
   proposed twice and investigated both times: the function uses the same corporate-action-adjusted
   `_return()` every other return feature uses, and `prev_close` is referenced nowhere outside its
   own declaration (confirmed by grep, now permanently guarded by a test). It is not a defect — one
   of the strongest single raw features this project found, in fact. **The closest real analogue —
   a genuine price-adjustment bug, caught before it touched any real data — is `P8-009`**:
   `price_adjustment.py`'s `UNADJUSTABLE_ACTION_TYPES` (a hand-mirrored copy of a list in a
   different module) missed two action types a companion fix had just added elsewhere, found only
   by re-reading every consumer of the old pairing before trusting the fix was complete, not by
   assuming one correct edit implied the other.
4. **`P2-001` — a silent HTML-as-CSV download.** `jugaad_data.nse.full_bhavcopy_save()` reports
   success (no exception) even when NSE serves an HTML error page instead of real bhavcopy data.
   Found by noticing nine years of "successfully fetched" pre-2019 files were all exactly 3,651
   bytes — reading one showed `<!DOCTYPE html>`. Fixed at the store layer (independent shape/type
   validation on every write), not just the ingestion module, so no future data source can smuggle
   a malformed row past validation the same way.
5. **`P8-003` — the banned-term lint misses 11 of 11 hand-written adversarial phrasings.** ("strong
   buy," "insider trading," bare "highly suspicious," etc.) Resolved *architecturally*, not by
   expanding the word list: confirmed zero LLM-provider-calling code exists anywhere in `src/`, so
   there is no free-text generation surface for a paraphrase to evade in the first place. The lint
   stays as a backstop, with its 0/11 catch rate recorded plainly, not hidden.
6. **`P8-007` — ETF unit splits, found and reported not fixed.** A pre-specified scan for
   unadjusted-split price shapes found 96 hits with zero matching `corporate_actions` rows — this
   project has never captured ETF unit splits, confirmed directly (`HDFCNIFETF`, a real 10:1 split,
   close 1628.18→162.44 overnight, absent from the actions table entirely). Contamination was
   quantified (≈0.4% of events, immaterial to conclusions) and the gap was **left open and reported
   as such**, rather than silently patched around, because building real ETF ingestion was out of
   scope for that pass.

## 5. Likely questions, answered honestly

**Does it work?** Not demonstrated. The one clean-looking result was retracted once checked
properly (`P8-001`); nothing has beaten a naive baseline with a CI excluding zero on genuinely
out-of-sample data. What does work: the verification machinery (100% of 29,764 claims checked, two
claim types independently re-derived from raw data) and an architecture that cannot narrate a
conclusion even if asked to.

**Which LLM?** None. Zero LLM-provider-calling code exists anywhere in this codebase (§2.5). Any
future narrative capability is restricted by standing policy to local/dev-only, never shareable
output (`CLAUDE.md` invariant 2).

**Why not deep learning?** The label is a noisy proxy (`collapsed_Nd`, a price-reversion heuristic,
not a regulatory determination), confirmed-positive examples are scarce (SEBI history usable only
from 2019-10-01 onward, the real data floor), and every real bug found so far (`P8-001`, `P8-013`,
`P8-014`) was in the *label*, not model capacity. An interpretable logistic fit with 4-6 inputs
matches both the data constraints and invariant 12's explainability requirement.

**How do you know there's no look-ahead bias?** Structurally, not by convention: every table row
carries `knowledge_date`, every query filters `knowledge_date <= as_of`, and a query without an
as-of parameter is treated as a bug (`CLAUDE.md` invariants 7-11). Concretely: thresholds are frozen
on TRAIN before hold-out is touched (`scripts/phase8_freeze_thresholds.py`), and the current
pre-registration's coefficients were committed to git before any forward outcome could possibly
exist — the commit timestamp is the proof.

**Why five amendments?** Because the outcome *label* turned out to be most of the real work, and
each amendment is a dated, git-committed record of a specific defect found and fixed, never a
silent edit (inherited evaluation-integrity rule: report a defect's before/after impact explicitly).
Two of the five (4 and 5) exist because the label had a structural selection bias that took two
separate rounds to fully close (§4.2).

**Is this investment advice?** No — architecturally not. No buy/sell/hold, no targets, no ratings
(invariant 12), enforced primarily by having no code path that renders free-text narrative into
shareable output at all, not by the banned-term lint alone (`P8-003`).

**What would you do differently?** Measure a new outcome label's *own* missingness against the
model's inputs *before* pre-registering on it, not after four rounds of amendment. `P8-013`/`P8-014`
show that "the label looks like a reasonable fix" and "the label's missingness is uncorrelated with
what you're trying to measure" are different claims, and the second one is the one that actually
matters — it should have been the first check, not the fifth.

**How does this relate to InsightForge?** Praman is seeded from InsightForge — same author, same
non-negotiable architectural invariants carried over unchanged (deterministic-by-default, one
authorization gate, evaluation integrity: expected values computed not authored, adversarial
benchmarking, never tune a score up, report failures first). Different domain entirely (NSE market
surveillance vs. BI/analytics benchmarking), same discipline: measure before asserting, and a defect
found in your own evaluation gets a dated correction, never a quiet edit.

## 6. Numbers to know cold

| Number | Source |
|---|---|
| 100% of 29,764 claims verified; 1 correctly withheld | `docs/RESULTS.md` §3 |
| 786/4,000 (19.65%) claims independently re-derived from raw data | `docs/RESULTS.md` §3 |
| Retraction: classifier top-tier precision 90.6%→28.6% (n=7); disclosure-alone 78.7%→51.1% | `docs/RESULTS.md` §1 |
| Precision@k gap +30/+20/+16/+15pp (k=10/20/50/100); CI-confirmed only at k=100 | `docs/RESULTS.md` §2 |
| Lead time: p10=2, p25=3, p50=14, p75=52, p90=95 sessions | `docs/RESULTS.md` §5 |
| 35 defects logged (5 Ph.2, 3 Ph.3, 13 Ph.4, 14 Ph.8-10) | `docs/DEFECT_REGISTER.md` |
| Real usable data floor: 2019-10-01 | `CLAUDE.md` "Data sourcing"; `P2-003` |
| 2026 hold-out: 10,850 events, spent for model selection as of 2026-09-22 | `CLAUDE.md` "Evaluation integrity"; `P8-001` |
| Frozen pre-reg: TRAIN missing 1.310%, HOLD-OUT 0.897% (gap 0.413pp), threshold 4.3% | `docs/phase10_preregistration_amendment5.md` |
| Pinned forward-pipeline commit | `afe3e2bd07abe8b602c4119b916f7696a3c12131` |
| Forward window 2026-09-16→2027-01-15 (~5,100 events); earliest run ~early June 2027 | Amendments 1, 4, 5 |
| Test suite: 367/367 passing, 26 test files | this session's verified run; `README.md` |

## 7. What NOT to claim

- **No deployment or live trading.** Nothing in this project is wired to a broker, an order system,
  or any live decision path. It is an offline forensic/research classifier.
- **No manipulation detection.** Praman reports measured signals and their values; it is
  architecturally incapable of stating "this is manipulation" (invariant 12), and no evaluation run
  has ever validated it as a detector of anything.
- **No LLM agents.** Zero language-model calls exist in this codebase today, and any future
  narrative capability is local/dev-only by standing policy — never describe this as an "AI agent"
  system in the LLM-agentic sense.
- **No performance figure without its caveat.** Every AUC, precision, or lift number in this project
  has a specific population, label version, and correction history attached (§6) — never state one
  bare, and never cite a number from `docs/phase6_signals.md`'s original (pre-`P8-001`) tables as
  current without also citing the retraction.
