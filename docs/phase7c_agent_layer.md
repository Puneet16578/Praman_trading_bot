# Phase 7c — the multi-agent evidence layer

Status: implemented and tested (fixture + real-data). This layer does not improve on Phase 6's
measured 0.611-0.70 AUC ceiling and is not meant to -- it exists to make a classification
independently checkable: what was measured, what disclosures existed, what the exchange did and
when, where these disagree, and what could not be determined.

## Architecture, and what was ported vs. built fresh

Ported (adapted, not imported -- CLAUDE.md "extend, never fork" governs reuse WITHIN a project,
not copying a foundation into a new one; the InsightForge modules were read in full and their
patterns re-implemented in Praman's own tree) from InsightForge's multi-agent orchestrator
(`src/agent/multi_agent/` in the InsightForge tree):

- **Supervisor.plan()** (`src/agent/supervisor.py`) -- deterministic routing. InsightForge's
  version is a dict keyed by question_type; Praman has exactly one question type ("classify and
  evidence this event"), so the plan collapses to one fixed dispatch order.
- **Authorization gate** (`src/mcp/tools.py:authorize_tool_call`/`call_tool`) -- role x tool x
  task-allowlist x budget, fail-closed. Every specialist agent's every tool call passes through
  this; there is no other path to the store.
- **BudgetTracker** (`src/agent/budgets.py`) -- per-agent and total tool-call bounds.
- **EvidenceClaim / AgentTaskResult / EventReport** (`src/agent/models.py`) -- typed, bounded
  contracts; no agent communicates through free-form text.
- **Deterministic Synthesis** (`src/agent/synthesis.py`) -- every structural section is built
  directly from data; no narrative-text hook a provider could use to suppress or override
  anything, because no provider is called anywhere in this path at all.
- **MultiAgentOrchestrator** (`src/agent/orchestrator.py`) -- plan -> dispatch -> verify ->
  synthesize, a single deterministic pass (not InsightForge's round-based incremental-follow-up
  loop -- there is no open-ended question here for a round to discover more about).

Built fresh, with no InsightForge equivalent: **the roster itself** (Market Microstructure,
Disclosure, Surveillance, Adversary are Praman-specific; the tools they call recompute Phase 5/6
signals, disclosure windows, and surveillance state fresh from THIS project's own bitemporal
store), and **the Adversary's verification mechanism** (`verify` closures on each claim, compared
against independent recomputation -- InsightForge's own `EvidenceValidator.validate_claim()` only
checks that evidence of the right TYPE exists, never that a cited NUMBER matches its source; this
was confirmed by direct reading before Phase 7 began, and is exactly the gap this Adversary fills).

## The five agents

1. **Market Microstructure** (`src/agent/specialists.py:MarketMicrostructureAgent`) --
   recomputes volume_ratio, delivery_pct(+percentile), zscore_60d, return_20d fresh from bhavcopy
   via `build_symbol_history`/`compute_daily_stats` (never from a cached catalogue CSV), plus the
   raw OHLC/quantity inputs those signals were built from.
2. **Disclosure** (`DisclosureAgent`) -- checks announcement coverage, then every
   `corporate_announcements` row in the canonical 10-session pre-event window, then the
   SUBSTANTIVE/ROUTINE_ONLY/NONE tier. A symbol with no cached announcement data gets an explicit
   `UNKNOWN_COVERAGE`-shaped claim, never conflated with "checked, found nothing."
3. **Surveillance** (`SurveillanceAgent`) -- ASM/GSM stage as-of the event date
   (`current_surveillance_state`, bitemporally correct) plus lead time to any subsequent flag
   (`SurveillanceTimeline.first_entry_after`, retrospective by design -- see
   `src/signals/surveillance_state.py`'s docstring for why full knowledge is correct there and
   would not be for a live signal).
4. **Adversary** (`src/agent/adversary.py`) -- four checks on every claim before it can reach
   Synthesis: banned-term lint (invariant 12, no exceptions for hedging), window/cherry-pick
   consistency (a claim's declared window must match the canonical constant), and TWO independent
   numeric-verification tiers (see "Transcription vs. derivation" below), the second added after a
   review noted the first alone only proves a claim was copied faithfully, not computed correctly.
   A failed claim at ANY tier never reaches output; every check's outcome is recorded in
   `EventReport.adversary_findings` AND on the surviving claim's own `verification` field, not
   silently dropped or implied to be uniform coverage.
5. **Synthesis** (`src/agent/synthesis.py`) -- deterministic renderer. Computes the final
   classification via `classify_event()` using ONLY accepted (post-Adversary) claims plus two
   catalogue-relative reference values (cap_band, same_date_event_count -- see below), assembles
   the report, and attaches two fixed notes to every report: `PROVENANCE_NOTE` (Phase 7b's
   approved disclaimer, rewritten during this phase to avoid the word "manipulated" even in
   negated form -- see "a lint false positive that wasn't" below) and `DISCRIMINATIVE_POWER_NOTE`
   (the Phase 6 0.611-0.70 held-out AUC ceiling, attached unconditionally next to every
   classification -- not only inside the longer provenance paragraph -- so a reader looking at one
   event doesn't have to go find the general disclaimer to see the system's actual measured
   discriminative power).

## Transcription vs. derivation -- two independent numeric-verification tiers

A review of the original single-tier design pointed out a real gap: checking a claim's
`volume_ratio` against the same tool call it came from proves the number was **transcribed**
correctly, not that it was **derived** correctly -- a bug inside the shared derivation function
(`src/mcp/tools.py:get_market_microstructure`) would return the identical wrong number on both the
original call and the re-check, and pass every time. This is exactly the gap InsightForge's own
`EvidenceValidator.validate_claim()` left open (confirmed by direct reading during Phase 7
planning): it checks that evidence of the right TYPE exists, never that a cited number is
arithmetically correct.

**TRANSCRIPTION** (`EvidenceClaim.verify`, unchanged from the original design) -- re-runs the SAME
function the claim's value came from, cheap, runs on every claim that has one.

**DERIVATION** (`EvidenceClaim.derivation_verify`, `src/agent/derivation_check.py`, new) -- for a
random, seeded, reproducible ~20% sample of DERIVATION-eligible claims, recomputes the value via a
SEPARATE, independently-written code path: plain SQL directly against `bhavcopy`, never
`build_symbol_history`/`compute_daily_stats`. Sampling is a pure function of the claim's own
`claim_id` (SHA-256, fixed salt) -- deterministic and reproducible, so the byte-identical-twice-run
determinism guarantee still holds; it is not wall-clock random.

**Scope, stated honestly rather than silently narrowed:** DERIVATION is implemented for
`volume_ratio` and `delivery_pct_percentile_60d` -- both computable from raw bhavcopy quantities
alone, no corporate-action price adjustment needed. `return_20d` and `zscore_60d` need an ADJUSTED
return series; an independent second implementation of that adjustment machinery is materially
larger and is **not attempted here** -- those claim types report `derivation: NOT_APPLICABLE` and
remain transcription-only. Every accepted claim in the report states both tiers' outcome
explicitly (`PASS` / `FAIL` / `NOT_APPLICABLE` / `NOT_SAMPLED`), so the report never implies
uniform coverage it doesn't have.

Verified against a hand-built fixture with values chosen so the expected result is computable by
hand (`tests/test_derivation_check.py`), against real production data (`tests/
test_orchestrator_real_data_guard.py` -- confirmed at least one real claim per run is actually
sampled and independently re-derived, not trivially skipped), and against a deliberately
constructed systematic bug: `tests/test_adversary.py::AdversaryDerivationTierTest::
test_derivation_catches_a_systematic_bug_transcription_alone_would_miss` builds a claim whose
`verify` (the same buggy shared function, called twice) agrees with its own wrong cited value --
transcription PASSES -- while `derivation_verify` (the independent implementation) computes the
correct value and disagrees, and the claim is rejected. That is the exact scenario this tier
exists to catch.

## Live vs. reference data -- a deliberate split, stated explicitly

Every Market Microstructure, Disclosure, and Surveillance fact is recomputed **live**, per report,
directly from the bitemporal store -- never from a cached artifact, so the Adversary's
recomputation check is a genuine independent re-derivation.

Two fields are the deliberate exception: **cap_band** and **same_date_event_count** are inherently
catalogue-wide statistics (a turnover quintile cut for a whole year; a same-day event count across
every symbol) that cannot be cheaply recomputed for one event in isolation without reloading and
re-deriving the entire catalogue -- exactly the batch work `scripts/build_event_classifications.py`
already does correctly. These two are read from that script's own persisted output
(`data/processed/event_classifications.csv`, `data/processed/classification_thresholds.json`) via
`src/agent/reference_data.py`, with the provenance stated in the field itself (`"source":
"data/processed/event_classifications.csv ... catalogue-relative, not live-recomputed per
report"`), never disguised as a live computation.

## Two real bugs found and fixed during testing

**Real-data cross-check, not a synthetic test, is what caught both** -- `tests/
test_orchestrator_real_data_guard.py` runs the live pipeline against five real catalogued events
(one per class) and asserts the live classification matches what the batch classifier already
computed for the same event. First run: 2 of 5 failed.

1. **Shared budget across reports (the real bug).** `MultiAgentOrchestrator` originally held one
   `BudgetTracker` for the instance's whole lifetime. Generating report 3 and 4 on the same
   instance silently exhausted the shared tool-call budget, causing the Disclosure agent to be
   denied and error out -- which the Synthesis logic at the time defaulted (wrongly) to
   `has_coverage=True, disclosure_tier="NONE"` rather than surfacing the failure. Fixed two ways:
   (a) `run_for_event` now allocates a fresh `BudgetTracker` per call, never shared across reports
   on the same orchestrator instance; (b) independently of the budget fix, an agent error is now
   an explicit, conservative `UNKNOWN_COVERAGE` outcome with a named gap
   (`"DISCLOSURE agent could not complete: ..."`), never a silent default toward "no disclosure
   found." Regression-tested directly (`tests/test_orchestrator.py::OrchestratorBudgetIsolationTest`),
   including a deliberately tiny budget that forces the failure path and checks it degrades safely.
2. **A banned-term lint false positive that wasn't quite a false positive.** The approved
   Phase 7b provenance note said `... not "likely manipulated."` -- a negated, disclaiming use of
   the word, and the lint (correctly, by design) has no negation exception, so it flagged its own
   disclaimer. Rather than add negation detection (fragile, and itself a plausible bypass vector
   for genuine verdict language wrapped in a superficial negation), the note was rewritten to
   convey the same disclaimer without ever using the trigger word: *"...describe an absence of a
   substantive disclosure and where the measured signals fall -- they are not a finding about why
   the price moved, and carry no conclusion about the cause of the move."* Stricter lint, safer
   report text, no exception logic to get wrong later.

## Three fixes from reading an actual generated report

Generating and reading one complete real report (3IINFOTECH, 2020-04-17) surfaced three real gaps
no amount of unit testing had caught, because they were about what the report DIDN'T say rather
than what it said incorrectly:

1. **The disclosures themselves were invisible.** The Disclosure agent computed a tier
   (SUBSTANTIVE/ROUTINE_ONLY/NONE) but never showed which announcements produced it -- a reader
   could see "GROUNDED" and never see the actual disclosure the classification rests on. Fixed:
   every row in the disclosure window now renders as its own claim with the category, the
   per-row SUBSTANTIVE/ROUTINE/AMBIGUOUS tier (`classify_category_safe`), and any description text
   NSE provided. A real attachment URL was requested too; checked directly, this project's schema
   has no such column (`corporate_announcements` stores `attchmntText`, never `attchmntFile`) --
   rather than fabricate one, the report now says so explicitly as its own claim ("Attachment URLs
   are not captured by this project's announcement ingestion").
2. **Catalogue membership was asserted, not shown.** A report could state "volume ratio 5.65x"
   without saying whether that, or the z-score, was what actually qualified this event for the
   catalogue in the first place. Checked directly against `scripts/build_final_event_catalogue.py:
   is_event()` (the real, single source of truth): it is a strict AND, not an OR -- every
   catalogued event satisfies BOTH `|z-score| > 2.5` AND `volume_ratio > 2.0x` by construction,
   so "qualified on one criterion alone" is not a real state this catalogue can produce. The
   Market Microstructure agent now states both thresholds and confirms the event's own live values
   against both, so a reader can verify catalogue membership themselves instead of assuming an OR.
3. **The proportionality limitation lived only in the design doc.** `GROUNDED_LIMITATION_NOTE`
   (a "Board Meeting Intimation" and a major order win are both SUBSTANTIVE; this design does not
   distinguish a disclosure that plausibly justifies a move's magnitude from one that doesn't) is
   now attached to `EventReport.classification_notes` whenever `classification == GROUNDED`,
   alongside `INDISTINGUISHABLE_PAIR_NOTE` when both apply (`classification_notes` is a list, not
   a single optional string, for exactly this reason -- more than one note can apply to the same
   class). Also added: `BASELINE_COMPARISON_NOTE`, attached unconditionally, stating plainly that
   no random/naive-threshold/disclosure-tier-only/deterministic-classifier baseline exists yet --
   Phase 8's job, named here so its absence isn't mistaken for a favorable comparison.

## Testing summary

| Suite | What it covers |
|---|---|
| `tests/test_banned_terms.py` | 5 violation shapes (blatant/hedged/split-across-sentences/implied-by-ranking/rhetorical-question), 5/5 on SELF-AUTHORED controls -- reported as such, not as "100%" (InsightForge's comparable heuristics scored 1/3 and 2/3 on their own; a perfect score by the detector's own author is weak evidence, not strong). False-positive check against CLAUDE.md's own "acceptable fact" example and this project's real claim templates. |
| `tests/test_banned_terms_adversarial_evasion.py` | The honest follow-up: 5 sentences written specifically to state a verdict while evading every regex in banned_terms.py. Measured result: **0/5 caught.** Reported separately, not blended into the self-authored 5/5, and not gated (a low score here is the finding, not a bug to fix by loosening the test). Strengthening the lint against these specific evasions is future work, tracked here rather than papered over. |
| `tests/test_mcp_authorization.py` | Role/tool/task-allowlist/budget fail-closed gate. |
| `tests/test_adversary.py` | Transcription tier: 6 deliberately fabricated claims (wrong number, fake record, correct-number-but-verdict-language, cherry-picked window, a raising verify(), a mixed good+bad batch), every one rejected, one genuine claim kept as a negative control. Derivation tier (`AdversaryDerivationTierTest`): a claim whose transcription PASSES (same buggy shared function called twice) but whose independent derivation disagrees and is rejected; NOT_APPLICABLE/NOT_SAMPLED recorded, never silently PASS; a raising derivation fails closed. |
| `tests/test_derivation_check.py` | The independent recomputation functions themselves, against a hand-built fixture with values chosen so the expected result is computable by hand (not by re-running this project's own code); insufficient-history and unknown-symbol return None, never a wrong number; empirical sample-rate and determinism checks. |
| `tests/test_synthesis.py` | `classification_note` appears only for GROUNDED/UNEXPLAINED_ISOLATED (the measured indistinguishable pair) and nowhere else; `discriminative_power_note` (0.611-0.70) is attached unconditionally to every report regardless of class; both are banned-term-lint clean. |
| `tests/test_orchestrator.py` | Full pipeline structure, banned-term-clean output, UNKNOWN_COVERAGE/GROUNDED paths, determinism (two runs byte-identical `to_dict()`), the budget-isolation regression, every accepted claim states which verification tier it received. |
| `tests/test_orchestrator_real_data_guard.py` | Live pipeline vs. batch classifier agreement on 5 real catalogued events (one per class); real evidence never trips the Adversary (transcription OR derivation); at least one real claim per run is confirmed actually sampled and independently re-derived, not trivially skipped; real reports are banned-term-clean. |

Acceptance criteria from the Phase 7 framing, checked directly: full report generation with no LLM
provider configured anywhere in the path (there is none to configure); the Adversary catches
fabricated claims at both the transcription tier (6/6 constructed shapes) and the derivation tier
(a systematic-bug scenario transcription alone cannot see), plus a negative control at each tier
that isn't wrongly rejected; banned-term lint negative-controlled with a recorded catch rate
(5/5); deterministic structure (two runs of the identical event produce byte-identical `to_dict()`
output, including the deterministic derivation sample); full suite green (326 tests).
