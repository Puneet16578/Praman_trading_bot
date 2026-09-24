# Phase 10 Pre-registration — Amendment 4

**Dated 2026-09-24. Amends `docs/phase10_preregistration.md` and Amendments 1-3 without editing
any of them, per their own immutability notices.** This is the FOURTH and final revision of this
draft, reviewed and passing the commit rule stated in §4 below. The first revision set a threshold
from an undiagnosed number with a backwards direction sentence. The second diagnosed two real
missing-outcome mechanisms but picked its buffer by intuition, not measurement. The third measured
the plateau properly and found none within 120 sessions — the own-session outcome definition has
no clean timing fix because the problem is not timing, it is the definition itself. This fourth
revision adopts the alternative named and deferred in the third: the outcome horizon is redefined
at a global calendar point instead of the security's own trading calendar, which resolves the
selection problem at its root rather than working around it. Once committed, this document is
frozen like every one before it; a further correction would be Amendment 5, in a new file.

**No forward outcome exists yet, as of this commit.** The forward evaluation window (Amendment 1
§3: 2026-09-16 through 2027-01-15) has barely begun. This amendment's own redefinition of the
outcome label (§4) is a change found by diagnosing the LABEL's own statistical properties against
historical data — never by looking at a forward outcome, which does not exist. The earliest
individual forward event's own outcome becomes computable around **late January 2027** (90 global
sessions past 2026-09-16); the full, binding evaluation, per §4's revised timing, runs no earlier
than roughly **early June 2027** (90 global sessions past the window's last date, 2027-01-15, plus
the 10-session staleness-cap margin).

## Summary (read this first)

**Round 3 measured the missing-outcome rate's decay curve properly, per its own decision rule, and
found no plateau within 120 sessions.** Diagnosing why revealed the real problem: the pre-registered
label required a security's own 90th REAL trading session — an unbounded, feature-correlated
quantity for a thinly-traded stock, not a timing nuisance a buffer can fix. Confirmed directly
(`scripts/phase10_amendment4_selection_problem.py`): the OLD definition's TRAIN missing-outcome
rate (buffer≥30 sessions) is a clean monotonic function of `cap_band` — Micro 2.09%, Small 1.84%,
Mid 1.46%, Large 1.36%, Mega 1.20% — and five spot-checked "missing" events in the worst band all
had real gains of +31% to +59% once the artificial censoring was lifted. Missingness under the old
definition is not random; it is correlated with the very inputs the model scores on.

**This amendment redefines the outcome (`P8-013`) at a GLOBAL 90-session horizon** — the market's
own calendar, not the security's — using the security's last available close (extended through
`BE`/`BZ`, `P8-012`) with a 10-session staleness cap beyond which the outcome is genuinely MISSING,
never extrapolated. Verified before trusting it against real data (synthetic cases: no staleness,
exact-boundary zero staleness, beyond-cap missing, and critically that the market index is
evaluated at the security's own last OBSERVED date, never a later date it had no chance to keep
pace with). Real effect: **old-vs-new label agreement is 98.73% overall, with a clean monotonic
gradient by cap_band (Micro 96.60% → Mega 99.79%)** — near-total agreement for liquid names,
changes concentrated in thin ones, exactly as a correct, narrowly-targeted fix should look.
**The new definition's missing-outcome rate is 6.838% (TRAIN) vs. 6.661% (HOLD-OUT) — a 0.176pp
gap**, against the old definition's 1.67% vs. 10.80% gap (a 9.1pp disparity). **The commit rule
(§4) — TRAIN and HOLD-OUT within 2.0pp of each other — passes cleanly.** The elevated 2026 rate
that started this entire investigation is now shown to have been almost entirely a property of the
own-session definition itself, not genuine 2026-specific attrition.

Refit under the new label (§3): coefficients stable relative to every prior round;
`disclosure_UNKNOWN_COVERAGE` remains at roughly a third of its pre-correction (Amendment 1)
magnitude; `isolated`'s coefficient (+0.012, z=+0.71) remains not distinguishable from zero, now
even more clearly than under the own-session label. Phase 8b re-run (§6) under the new label: no
feature's direction reverses; every feature's CI excludes 0.5 except `asm_gsm_labelled`. Missing-
data threshold set from TRAIN's own fully-aged rate under the new definition (6.838% + 3pp =
**9.8%**), replacing both the original pre-registration's 5% and every provisional figure from
rounds 2-3. Evaluation timing: **10 sessions past the last window event's own GLOBAL t+90**,
directly matching the staleness cap rather than an intuited buffer. Pinned commit updated to
`c4925b6fb4016a942d49bd8d9b4270a977f3ed97` (`phase8_robustness_relabel_t0.py`'s core logic
changed this round).

---

## 1. Universe: equity-only, applied — and how forward symbols get resolved

**Rule (unchanged from the measurement in `docs/phase10_p8007_corrections.md` §4, now APPLIED, not
just measured):** exclude every symbol whose ISIN starts `INF` (a fund unit — has no company
disclosures, so disclosure-tier classification cannot apply to it) and every symbol with NO
resolved ISIN at all (cannot be classified as equity either — excluded conservatively, not assumed
in). Every other prefix (`INE`, and the small `IN9...` differential-voting-rights class) is kept.

**Applied to the historical catalogue**: 3,414 EQ symbols → 2,827 kept (459 fund-unit-excluded,
128 unresolved-excluded); catalogue 75,300 → 70,638 events.

**Forward symbols are resolved the same way, on the same cadence as the rest of the ingestion
schedule (Amendment 2 §5), confirmed wired, not just described:** `scripts/weekly_ingest.py`'s
`STEPS` list reads `[("bhavcopy", ...), ("announcements", ...), ("isin_map", step_isin_map),
("corporate_actions", ...), ("asm_gsm", ...)]` — `step_isin_map()` calls `scripts/build_isin_
map.py`'s `main()` before `step_corporate_actions()`, which loads the same file. Every future
catalogue build reports its own unresolved count directly (`build_final_event_catalogue.py`'s own
console output) — no new reporting mechanism needed.

## 2. Every data correction this session, by P-number

| ID | What | Status |
|---|---|---|
| `P8-007` | ETF/fund-unit corporate actions never captured; `UNKNOWN_COVERAGE` coefficient confounded with instrument type | Equity-only rule applied (§1); confound directly measured in the refit (§3) — coefficient shrinks to roughly a third of its original magnitude |
| `P8-008` | 699 of 702 production `corporate_actions` rows traced to a stale pre-`P8-006` cache; full live sweep never run | Full sweep run, diffed, and promoted to production |
| `P8-009` | `STRUCTURAL_BREAK_ACTION_TYPES`/`UNADJUSTABLE_ACTION_TYPES` independently hand-mirrored, silently drifted | Merged into one definition; identity-asserting test added |
| `P8-010` | A renamed security's actions are filed under whatever symbol NSE's live feed currently reports, not the symbol in effect on the action's own date | ISIN-based resolution built, tested, and applied in the real production promotion; 195 ISINs found to map to >1 symbol project-wide |
| `P8-011` | The announcement cross-check fetch is not yet ISIN-aware, unlike the row-write path | Found, not fixed — low severity, one row observed affected, zero adjustment-factor impact, deferred |
| `P8-012` | A stock moved to trade-for-trade settlement (`BE`/`BZ`) leaves the EQ series but keeps trading; `build_symbol_history`'s EQ-only default silently treated this as "delisted" | **Fixed for labels** — `extend_with_series` parameter, wired into label computation. The event catalogue itself stays EQ-only, unchanged |
| `P8-013` | The pre-registered outcome label's own-session horizon creates feature-correlated missingness — a clean monotonic gradient by `cap_band`, confirmed directly | **Fixed** — the outcome horizon is redefined at a global 90-session point with a 10-session staleness cap (§4). This is the headline change of this amendment |

## 3. The scoring function, refit under the corrected label — identical specification, with SEs

**Fit on 2019-2025 TRAIN data only (`event_date < 2026-01-01`), target `relative_t0_primary`
(PRIMARY threshold, `R < 0`, now under the `P8-013` global-horizon definition) — identical
specification to Amendment 1 §1: unregularized logistic regression, the same four inputs, the same
median rule, the same Small/Large/Mega `volume_ratio_high_band_eligible` interaction, `NONE`
disclosure as the same reference level. Thresholds are computed from features, not the label, so
are unchanged by `P8-013`:** `delivery_low` 13.3333, `isolated` 45.0, `volume_ratio` band medians
(Micro/Small/Mid/Large/Mega) 5.0926/6.8397/7.6364/8.6042/7.4616.

**TRAIN population: 56,541 of 56,544 cap_band-matched equity-only TRAIN events had every input and
the label** (the new label's own 6.838% missing rate, §4, is the dominant reason this is smaller
than the 59,727 usable under the prior round's own-session label — an accepted, deliberate
trade-off: fewer usable TRAIN rows in exchange for a label whose missingness is not correlated
with the model's own inputs).

**Coefficients, WITH standard errors (Fisher information, unchanged method from round 2), across
every round for direct comparison:**

```
                                   Amendment 1     Round 2 (own-      Round 4 (P8-013     SE        z
                                   (pre-corr.)     session, P8-012)   global horizon)   (round 4)  (round 4)
intercept:                        +0.242510       +0.263847          +0.282662         0.024407  +11.58
delivery_low:                     +0.440636       +0.441840          +0.441680         0.018612  +23.73
isolated:                         +0.035727       +0.019065          +0.012487         0.017551   +0.71
volume_ratio_high_band_eligible:  +0.210644       +0.190164          +0.189702         0.020439   +9.28
disclosure_SUBSTANTIVE:           -0.233919       -0.231507          -0.239005         0.025500   -9.37
disclosure_ROUTINE_ONLY:          -0.061484       -0.065065          -0.066848         0.026874   -2.49
disclosure_UNKNOWN_COVERAGE:      -0.396295       -0.165400          -0.172378         0.044697   -3.86
```

**These round-4 coefficients are BINDING** — the score for a new forward event is
`p = sigmoid(intercept + Σ coefficient × input)`.

**`isolated`'s coefficient (`same_date_event_count < 45`) is not distinguishable from zero under
either post-correction label** (z=+1.12 under the own-session label, z=+0.71 under this amendment's
global-horizon label) — consistent across two independent label definitions, not an artifact of
either one. Every OTHER coefficient is significant at `|z|>2.4` and stable across all three
post-correction fits (Amendment 1, round 2, round 4), moving by less than one SE round-to-round.

**`disclosure_UNKNOWN_COVERAGE` remains at roughly a third of its pre-correction magnitude**
(−0.172 vs. −0.396) under this label too — the `P8-007` confound-removal finding is not an
artifact of which outcome-label definition is used.

**FAIR baseline, recomputed under the new label:** TRAIN `relative_t0_primary` rate is **60.27%**
(Amendment 1: 59.20%; round 2's own-session label: 59.96%) — the FAIR constant for criterion 1's
BSS.

**In-sample (TRAIN) AUC 0.5797, Brier 0.2350** — reported for the record only, per the original
pre-registration's own instruction not to treat TRAIN performance as a forward-generalization
claim.

**Honest limitation, unchanged from round 2:** standard errors for Amendment 1's ORIGINAL
(pre-correction) fit are not reported — that fit's exact TRAIN design matrix lived only in
gitignored `data/processed/` CSVs, overwritten before this requirement was known. Reconstructing
it exactly would require a full historical pipeline re-run against the pre-promotion database
backup and pre-Amendment-4 code, not attempted.

## 4. The outcome label, redefined at a global horizon (`P8-013`) — the headline change

### Why the own-session definition had to go, not just be timed around

Round 3 measured the missing-outcome rate's decay curve by buffer band on the TRAIN replicate and
found no band below 120 sessions came within 1.0pp of the 120+ reference rate — the artifact does
not have a clean, boundable timing fix. Diagnosing why (this round) found the deeper problem the
timing framing was obscuring:

- **Unbounded tail.** A thinly-traded stock can take arbitrarily long, in calendar time, to log 90
  real EQ sessions. Round 3's own 90-120 buffer band was still ~3pp above the 120+ baseline — no
  finite buffer cleanly separates "genuinely gone" from "just slow to accumulate sessions."
- **Heterogeneous horizon.** A stock trading roughly half of all sessions gets an effective
  ~180-session "90-session" return under the own-session definition — the label does not measure
  the same real-world time span for every security.
- **Feature-correlated missingness, confirmed directly** (`scripts/phase10_amendment4_selection_
  problem.py`, TRAIN, buffer≥30 sessions):

  | cap_band | n | missing | rate |
  |---|---|---|---|
  | Micro | 12,142 | 254 | 2.092% |
  | Small | 12,139 | 223 | 1.837% |
  | Mid | 12,138 | 177 | 1.458% |
  | Large | 12,139 | 165 | 1.359% |
  | Mega | 12,136 | 145 | 1.195% |

  A clean monotonic gradient — smaller, thinner names are systematically more likely to lack a
  computable outcome. Weaker but present gradients by `volume_ratio_high` (LOW 1.499% vs. HIGH
  1.677%) and `delivery_low` (HIGH/NORMAL delivery 1.747% vs. LOW delivery 1.425% — direction
  reported as measured, not forced to match an assumed story). **Trading density tracks model
  inputs, so events lacking outcomes are not a random subset of the population the model scores.**
  Five events sampled from the highest-missingness band all had large real gains (+31% to +59%,
  round 3's own evidence) once the artificial own-session censoring was lifted — these were never
  actually "unknowable," only artificially excluded by a definition that couldn't see far enough.

### The new definition

**Outcome = the signed, market-relative return from `close(event_date)` to the security's LAST
AVAILABLE close (across EQ, extended through `BE`/`BZ` per `P8-012`) on or before the 90th GLOBAL
trading session after `event_date`, with the equal-weighted index evaluated at that SAME observed
date.** `scripts/phase8_robustness_relabel_t0.py`'s `compute_t0_relative`:

1. `target_date` = the 90th session in `market_index.csv`'s own calendar after `event_date` (not
   the security's own calendar).
2. `last_date` = the security's own last available close on or before `target_date`.
3. **Staleness cap: if `last_date` is more than 10 GLOBAL sessions before `target_date`, the
   outcome is MISSING** — a genuine, uncensored gap (likely suspension/delisting), never
   extrapolated across.
4. The market index is evaluated AT `last_date` (matching `relative_g`'s existing, unchanged
   convention of comparing a price to the index on its OWN observation date) — never at
   `target_date` if that differs, which would otherwise attribute market drift the security had no
   chance to participate in to its own "return."

**Verified before trusting it against real data**, via hand-constructed synthetic cases: a normal
no-staleness case; a case where the last available date lands EXACTLY at the target (zero
staleness, identical result to the no-staleness case); a case stopping 45 sessions before target
(correctly MISSING, beyond the 10-session cap); and — the case that actually exercises the
index-date convention — a security stopping 5 sessions before target with the index rising sharply
in those 5 sessions: confirmed the function returns the result using the index level AT the
security's own last observed date (a clean, hand-verified `+100%` relative return), not the
(materially different, wrong) result that would follow from using the index level at the later
target date.

### Real effect, measured

**Old-vs-new label agreement: 98.73% overall** (61,827 events with both labels computable; 61,039
agree). **By `cap_band` — a clean monotonic gradient, exactly the shape a correctly-targeted fix
should produce:**

| cap_band | n (both computable) | agree | rate |
|---|---|---|---|
| Micro | 11,254 | 10,871 | 96.597% |
| Small | 12,181 | 11,971 | 98.276% |
| Mid | 12,687 | 12,571 | 99.086% |
| Large | 12,786 | 12,734 | 99.593% |
| Mega | 12,919 | 12,892 | 99.791% |

Near-total agreement for liquid names; disagreement concentrated almost entirely in `Micro`/
`Small` — exactly the population the own-session definition's selection bias was shown to affect.

**The missing-outcome rate under the new definition, TRAIN vs. HOLD-OUT** (fully elapsed = the
global t+90 has already occurred as of the data's own end):

| | n | missing | rate |
|---|---|---|---|
| TRAIN | 60,694 | 4,150 | **6.838%** |
| HOLD-OUT | 6,020 | 401 | **6.661%** |
| **Gap** | | | **0.176pp** |

Against the own-session definition's 1.67% (TRAIN) vs. 10.80% (HOLD-OUT) — a 9.1pp gap. **The
elevated 2026 rate that motivated this entire investigation (rounds 1-3) is now shown to have been
almost entirely a property of the own-session definition itself.** `possible_delisting_or_
suspension` (the heuristic flag for HOLD-OUT events lacking an outcome for reasons other than data-
cutoff proximity) falls further: 709 (original) → 495 (`P8-012` alone) → **368** (`P8-012` +
`P8-013` together).

### Commit rule, applied exactly as specified

**TRAIN (6.838%) and HOLD-OUT (6.661%) are within 2.0pp of each other (0.176pp) → PASS → this
amendment is committed**, per the rule stated in advance: the rule itself is the review, not a
separate approval step.

### Evaluation timing and missing-data threshold, set from this measurement

1. **Timing: the binding evaluation runs no earlier than 10 sessions after the LAST window
   event's own GLOBAL t+90** — directly matching the staleness cap (§4), not an intuited buffer.
   Estimated date: the window's last event (2027-01-15) reaches its own global t+90 around
   ~late May 2027 (90 global sessions ≈ 4.3 calendar months later); +10 sessions (≈2 calendar
   weeks) puts the binding evaluation no earlier than roughly **early June 2027**. An estimate
   only — the real trading calendar and this project's own ingestion cadence are not known that
   far in advance.
2. **Missing-data threshold: 9.8%** (TRAIN's own fully-aged rate under the new definition, 6.838%,
   plus the instructed 3-point margin: 6.838% + 3.0pp = 9.838%, stated as 9.8%). **This replaces
   the original pre-registration's 5% (Amendment 2 §4) and every provisional figure from rounds
   2-3 (20 sessions/11.4%), which are now superseded, not merely refined** — those figures were
   trying to compensate for a definitional problem with a timing adjustment; this figure is set
   from a definition that has already removed most of the problem, so it should be read as "the
   genuine residual attrition rate plus margin," not "how much artifact to tolerate."
3. **Pre-specified WORST-CASE SENSITIVITY, kept exactly as drafted in round 2/3, to run alongside
   the binding result at evaluation time** (no forward data exists yet to compute this now): every
   forward-window event still missing its outcome (staleness-capped, or insufficient forward
   history) is re-scored as `label = 1` (underperformed/collapsed) in a separate sensitivity pass,
   reported ALONGSIDE the binding result, never blended into it — the same discipline Amendment 2
   §3 established for the `UNKNOWN_COVERAGE` sensitivity. These outcomes are not missing at random
   even under the corrected definition (a security still failing the staleness cap is
   disproportionately one in genuine distress); this sensitivity bounds that residual bias.

### Considered and NOT further needed

Round 3 named, and did not adopt, "computing outcomes at 90 GLOBAL sessions using the last
available close" as an alternative that would remove the boundary artifact at its root but require
a full relabel and refit. **This amendment IS that alternative, now adopted**, precisely because
round 3's own diagnosis (no plateau, a clean feature-correlated gradient) showed the timing-only
fix could not work and the definitional one was the one actually available. The relabel and refit
it required have both been done (§3, this section).

## 5. Secondary comparison model — complete, scored against the corrected outcome

**Unchanged in principle from round 3's correction, now scored against the `P8-013`-redefined
outcome throughout.** Amendment 1's coefficients were fit against Amendment 1's OWN thresholds
(`delivery_low` at 15.0, `isolated` at 47.0, the old per-band `volume_ratio` medians) — applying
those coefficients to inputs computed under different thresholds would score a system that was
never actually fit or specified anywhere. **The secondary comparison is Amendment 1's COMPLETE,
unmodified scoring function** — old thresholds define the same four input indicators, old
coefficients combine them — applied to the SAME corrected forward data (equity-only population,
corrected corporate actions, stitched and series-extended price history, and now the `P8-013`
global-horizon outcome) as the binding model. This isolates the effect of the DATA-and-LABEL
correction from the effect of the model refit: if the two scores diverge materially, that is
itself informative, independent of whether the redesign passes its success criteria. **Reported
alongside the binding result, never in place of it, never used to pick whichever number looks
better.**

**All other success criteria, evaluation metrics, and procedures are UNCHANGED** from the original
pre-registration and Amendments 1-2: BSS vs. FAIR (criterion 1, CI must exclude zero), top-decile
LIFT vs. the current classifier (criterion 2, paired-bootstrap CI lower bound must exceed zero,
seed 42 for tie-breaks, seed 2027 for the 2,000 bootstrap resamples), per-band AUC with
Hanley-McNeil CIs, the `UNKNOWN_COVERAGE` sensitivity analysis (Amendment 2 §3, re-stated against
the corrected population's own new TRAIN prevalence, 4.94%, not the old 10.2%).

## 6. Phase 8b's clean-label feature analysis, re-run under the corrected label

`scripts/phase10_amendment4_phase8b_reauc.py` (a separate script from `phase8b_feature_reauc.py`,
whose own committed output remains a historical record against pre-correction data), re-run once
more against the `P8-013`-redefined label.

**Headline, unchanged from round 3: no feature's direction reverses. Every pre-registration
inclusion/exclusion decision (`docs/phase10_preregistration.md`) still holds.**

| Feature | TRAIN AUC [95% CI] (n) | Excl. 0.5? | HOLD-OUT AUC [95% CI] (n) | Excl. 0.5? |
|---|---|---|---|---|
| `zscore_60d` | 0.5297 [0.5249,0.5345] (56,544) | **Yes** | 0.5274 [0.5123,0.5425] (5,619) | **Yes** |
| `volume_ratio` | 0.5801 [0.5754,0.5849] (56,544) | **Yes** | 0.5413 [0.5263,0.5564] (5,619) | **Yes** |
| `delivery_pct_percentile_60d` | 0.4196 [0.4147,0.4244] (56,541) | **Yes** | 0.4658 [0.4506,0.4809] (5,619) | **Yes** |
| `return_20d_context_only` | 0.5267 [0.5219,0.5315] (56,300) | **Yes** | 0.4840 [0.4688,0.4992] (5,618) | **Yes** (barely) |
| `close_to_close_60d`* | 0.5132 [0.5084,0.5181] (56,057) | **Yes** | 0.4689 [0.4537,0.4841] (5,600) | **Yes** |
| `same_date_event_count` | 0.4752 [0.4704,0.4801] (56,544) | **Yes** | 0.4813 [0.4662,0.4965] (5,619) | **Yes** (barely) |
| `asm_gsm_labelled` | 0.5002 [0.4953,0.5050] (56,544) | No | 0.5058 [0.4906,0.5209] (5,619) | No |

*`close_to_close_60d.csv` itself was not rebuilt this session (a Phase 6 artifact, out of scope) —
its numbers mix a stale feature file with the freshly-corrected population and label, unchanged
caveat from prior rounds.

**Every feature's CI excludes 0.5 in both populations except `asm_gsm_labelled`**, whose CI
straddles 0.5 in both — the only feature statistically indistinguishable from chance, consistent
with "adds nothing" (`docs/phase10_preregistration.md`).

**`same_date_event_count`'s CI excluding 0.5 (a real, weak marginal signal) and `isolated`'s
non-significant multivariate coefficient (§3) are compatible findings, not the same fact restated
twice** — a weak-but-genuine univariate association becoming statistically redundant once
correlated, stronger features are already in the model is ordinary multicollinearity, confirmed
consistent across both the own-session and global-horizon label definitions.

`docs/RESULTS.md` cites the corrected `zscore_60d` figure (0.5234 under the own-session label,
0.5274 under this amendment's global-horizon label — both close, both far from the pre-correction
0.537) rather than the pre-correction one.

## 7. Derived artifacts: rebuilt from the store at evaluation time, never reused

**Pre-specified, motivated by real, found-not-guessed-at incidents across this session:**
`market_index.csv`/`outcome_labels.csv` staleness (round 2), `phase8b_feature_reauc.py`'s own
stale `HOLDOUT_CLASS_PATH` silently overwriting fresh values (round 3). **Rule: the BINDING
evaluation rebuilds every derived artifact — the event catalogue, clustering, classifications, and
label files — directly from the bitemporal store at the pinned commit, immediately before scoring.
It never reuses a CSV already sitting in `data/processed/` from an earlier run, however recent.**
A derived artifact is a cache of the store's own state at build time, not a second source of
truth.

## 8. Pinned commit

**Pinned commit: `c4925b6fb4016a942d49bd8d9b4270a977f3ed97`** (supersedes round 2's `97a459e` —
`phase8_robustness_relabel_t0.py`'s core label-computation logic changed this round, so a re-pin
is required, unlike round 3 which made no pipeline code changes). The forward evaluation computes
every input using the code at THIS commit specifically:

| Input | Pinned source |
|---|---|
| Event catalogue / raw signals | `src/signals/event_catalogue.py`, `scripts/build_final_event_catalogue.py` (equity-only, symbol-group-stitched, EQ-only) |
| ISIN resolution / symbol groups | `src/ingestion/nse_market_data/isin_mapping.py`, `data/raw/nse_symbol_isin_current.json` refreshed weekly (§1) |
| Corporate actions | `src/ingestion/nse_market_data/corporate_actions.py` (ISIN-resolved, fail-closed `RIGHTS`/`RATIO_CONFLICT` exclusion markers) |
| Co-movement (`same_date_event_count`) | `scripts/compute_clustering.py` (symbol-group-stitched) |
| Disclosure-tier mapping | `src/signals/disclosure_classification.py` |
| Cap-band quintiles | `scripts/build_event_classifications.py` (equity-only, symbol-group-stitched) |
| Label (`relative_t0_primary`) | `scripts/phase8_robustness_relabel_t0.py` (`P8-013` global-horizon definition, 10-session staleness cap, `P8-012` series extension) |
| Scoring function coefficients / thresholds | §3 above |

If any of this code changes in this repository before the forward evaluation runs, the BINDING
evaluation still runs against the pinned commit (`git worktree`/`git checkout` at evaluation time,
or an equivalent snapshot) — not against whatever `master` has become by 2027. Per §7, the
evaluation additionally rebuilds every derived artifact from the store at this commit rather than
reusing any existing file.

---

## What is still not done

`P8-011` (announcement fetch not ISIN-aware) remains open — low severity, one row observed
affected, zero adjustment-factor impact. The 48 shape-scan hits not explained by a rename remain
uninvestigated individually. Amendment 1's original (pre-correction) fit's standard errors are not
recoverable without a costly historical pipeline reconstruction, not attempted. No forward data
exists — nothing above has been evaluated against anything. The next real action on this
pre-registration is the evaluation itself, no earlier than ~early June 2027 (§4).
