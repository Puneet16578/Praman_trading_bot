# Amendment 4 Prep, Round 2 — Diagnose Before Setting a Threshold

Round 1 (`docs/phase10_amendment4_prep.md`) measured HOLD-OUT's fully-elapsed missing-outcome rate
at 10.80% and set a threshold from it without asking why it was 6.5x TRAIN's 1.67% — the resulting
draft amendment also stated the threshold's own directional consequence backwards. Both caught in
review before either was committed. This document is the diagnosis, the fix, and the corrected
numbers; `docs/phase10_preregistration_amendment4.md` (still uncommitted, still pending review) is
updated to match.

## Summary (read this first)

**Diagnosed, not guessed.** Two real, distinct, independently-confirmed mechanisms explain most of
HOLD-OUT's elevated rate:

- **(a) Boundary artifact.** The outcome computation needs the symbol's OWN 90th real EQ session,
  not a global 90-session window — a symbol trading slightly less densely than the index needs
  extra calendar time to catch up, and events near the data's true end don't have that time yet.
  Requiring 30 sessions of buffer drops HOLD-OUT's rate 10.80%→8.32%. Replicated on TRAIN at an
  artificial 2024-06-30 truncation: TRAIN events near THAT boundary hit 13.0% missing — HIGHER
  than HOLD-OUT's raw rate — confirming this is generic to data-boundary proximity, not a
  2026-specific effect.
- **(b) Series move.** `build_symbol_history`'s EQ-only default treats a stock moved to
  trade-for-trade settlement (`BE`/`BZ`) as if it vanished, when it's still trading. 31.93% of
  HOLD-OUT's lacking events have `BE`/`BZ` rows after their last EQ date; TRAIN's own historical
  share (28.64%) is nearly identical — a constant background gap this project's ingestion has
  silently had since Phase 2, only surfaced by this diagnosis. **Fixed for real** (not just
  measured): `build_symbol_history` gained `extend_with_series`, wired into both label-computation
  scripts. Real, verified effect: HOLD-OUT's delisting/suspension count drops 709→495.

**Residual after both fixes: HOLD-OUT 8.447% vs. TRAIN 1.588%** (buffer≥20 sessions, matching the
evaluation-timing fix below). New threshold: **11.4%** (8.447% + 3pp) — LOWER than the flawed first
draft's 13.8%, because part of the gap was actually fixed, not just tolerated. The evaluation
timing itself also moves: binding evaluation now waits 20 extra sessions past the last window
event's own t+90 (~late June 2027, not ~late May 2027).

**Direction corrected:** a higher missing-data threshold is a LAXER standard (tolerates more
missing data before COMPROMISED triggers), not a stricter one — the first draft had this backwards.

**Specification completed:** the secondary comparison model is now Amendment 1's COMPLETE scoring
function (old coefficients AND old thresholds together, not coefficients alone); standard errors
are reported for the new fit (`isolated`'s coefficient, z=+1.12, is NOT distinguishable from zero
— a direct, checkable answer); a derived-artifacts rebuild policy is pre-specified, motivated by
two real staleness bugs found this session (one in `market_index.csv`/`outcome_labels.csv`, a
second, independent one caught while re-running Phase 8b: `phase8b_feature_reauc.py`'s own stale
`HOLDOUT_CLASS_PATH` would have silently overwritten fresh cap_band values); the weekly ISIN
refresh, claimed but never actually wired in the first draft, is now really wired into
`weekly_ingest.py` (confirmed by the line, not just the docstring).

**Phase 8b re-run** against the fully corrected data: no feature's direction reverses; several
magnitudes moved more than the earlier, narrower contamination-only sensitivity check did (up to
0.027 vs. that check's <0.003), appropriately, since this correction touches far more of the
population.

---

## 1. Diagnosis

### (a) Boundary artifact

`scripts/phase10_amendment4_boundary_diagnosis.py`. Outcome mechanism restated precisely:
`compute_outcome_labels.py`'s `compute_outcome` needs `idx + 90` to exist in the SYMBOL'S OWN
`trading_days` list (EQ series only) — not a global-calendar 90-session window. "Fully elapsed"
(this project's prior measurement) only checks the GLOBAL calendar.

```
HOLD-OUT, raw fully-elapsed (buffer>=0):                n=7045  lacking=761  rate=10.802%
HOLD-OUT, buffered (buffer>=30 sessions beyond t+90):   n=5048  lacking=420  rate=8.320%

TRAIN replicate, artificial truncation at 2024-06-30:
  Near-boundary (buffer 0-30 before truncation):  n=2023  lacking=263  rate=13.000%
  Safely earlier (buffer 90+ before truncation):  n=39131 lacking=933  rate=2.384%
```

The near-boundary TRAIN rate (13.0%) exceeding HOLD-OUT's own raw rate (10.8%) is the key result:
boundary proximity alone can produce an elevation at least this large, with nothing else going on.

### (b) Series move

Same script. For HOLD-OUT's 761 fully-elapsed-lacking events, checked whether the symbol has `BE`/
`BZ` bhavcopy rows dated after its own last EQ row:

```
HOLD-OUT fully-elapsed, lacking-outcome events: 761
  -> symbol has BE/BZ rows after its own last EQ date: 243 (31.93%)
```

Repeated for the buffer≥30 subset (removing most of (a)'s effect first) and for TRAIN as a
baseline comparison:

```
HOLD-OUT buffer>=30 lacking: n=420  series-moved-after-EQ=126 (30.00%)  residual=294 (70.00%)
TRAIN   buffer>=30 lacking: n=1079 series-moved-after-EQ=309 (28.64%)  residual=770 (71.36%)
```

Nearly identical series-move shares (30.00% vs. 28.64%) between HOLD-OUT and TRAIN's own historical
population confirm this is a constant, previously-unnoticed background rate, not a 2026 anomaly.

### Fix: `extend_with_series` (`P8-012`)

`src/signals/event_catalogue.py`'s `build_symbol_history` gains an optional `extend_with_series`
parameter (default `()`, identical to before): rows from additional series, STRICTLY AFTER the
primary series' own last date, are appended for LABEL/OUTCOME continuity. Deliberately narrow —
rows inside any overlap period between EQ and the extension series (observed in real data: a
BE-designated lot can trade concurrently with EQ for the same company) are never merged, avoiding
an ambiguous, potentially-wrong price splice. Wired into `compute_outcome_labels.py` and
`phase8_robustness_relabel_t0.py` with `extend_with_series=("BE", "BZ")` — labels only; `build_
final_event_catalogue.py` (the event catalogue itself) is untouched, staying EQ-only per
instruction. Tests: `ExtendWithSeriesTest` (4 cases, including the overlap-period exclusion).

**Real, measured effect after rebuilding both label files:**

```
Before P8-012: HOLD-OUT possible_delisting_or_suspension = 709
After  P8-012: HOLD-OUT possible_delisting_or_suspension = 495   (214 fewer, matches ~30% almost exactly)
```

### (c) Residual, with both fixes applied

Re-measured against the rebuilt `outcome_labels.csv` (series-extended) with a 20-session buffer
(matching the evaluation-timing fix below, for a consistent basis):

| Buffer | HOLD-OUT n | HOLD-OUT lacking | HOLD-OUT rate | TRAIN n | TRAIN lacking | TRAIN rate |
|---|---|---|---|---|---|---|
| 0 | 6,020 | 534 | 8.870% | 60,694 | 964 | 1.588% |
| 20 | 5,209 | 440 | **8.447%** | 60,694 | 964 | 1.588% |
| 30 | 4,185 | 299 | 7.145% | 60,694 | 964 | 1.588% |

(TRAIN's rate is buffer-invariant because almost all TRAIN events sit far from the data's true
end — only a thin slice near the TRAIN/HOLD-OUT boundary could be affected at all.)

**Basis for the threshold: 8.447% (buffer≥20, matching the timing fix) + 3.0pp = 11.447%, stated
as 11.4%.**

## 2. Fixes applied to the evaluation design (see the draft amendment §4 for the full text)

1. Binding evaluation delayed 20 sessions past the last window event's own t+90 (addresses (a)
   directly, not just via a padded threshold).
2. Missing-data threshold reset 5% → 11.4% (not the flawed first draft's 13.8%), with the
   direction of the change stated correctly: LAXER, because it tolerates more missing data before
   COMPROMISED triggers, justified specifically because normal historical attrition (even after
   fixing (b)) exceeds the original 5% bar.
3. Worst-case sensitivity pre-specified: every forward-window event missing its outcome due to
   delisting/suspension/an unrecovered series move is re-scored `label=1` in a sensitivity pass
   reported alongside (never blended into) the binding result, since these outcomes are not
   missing at random.

## 3. Specification completeness

- **Secondary model, corrected**: Amendment 1's coefficients AND thresholds together (the complete,
  unmodified original scoring function), not coefficients alone applied to new thresholds — the
  earlier phrasing specified something that was never actually fit anywhere.
- **Standard errors**: computed directly from the observed Fisher information (`I=XᵀWX` at the
  fitted probabilities, `SE=sqrt(diag(I⁻¹))`) — no `statsmodels` dependency (not installed; this is
  the identical classical-MLE quantity it would report). `isolated`'s coefficient: z=+1.12, p≈0.26
  — not distinguishable from zero. Every other coefficient significant at `|z|>2.5`. Old (Amendment
  1) fit's SEs are NOT recoverable without reconstructing the pre-correction pipeline from the
  database backup and old code (~30 minutes) — not attempted this round, stated as an open gap.
- **Derived artifacts**: pre-specified that the binding evaluation rebuilds every derived artifact
  from the store at the pinned commit, never reusing an existing CSV — motivated by two real,
  found staleness bugs this session (market_index.csv/outcome_labels.csv in round 1;
  phase8_2026_classifications.csv silently overwriting fresh cap_band values, caught while
  building this round's Phase 8b re-run, below).
- **Weekly ISIN refresh**: confirmed actually wired. `scripts/weekly_ingest.py`'s `STEPS` now
  includes `("isin_map", step_isin_map)`, before `corporate_actions`. Verified directly:
  `[s[0] for s in STEPS] == ['bhavcopy', 'announcements', 'isin_map', 'corporate_actions', 'asm_gsm']`.

## 4. Refit, re-run after `P8-012`'s label fix

TRAIN n: 59,540 (round 1, pre-`P8-012`) → **59,727** (this round, post-`P8-012` — 187 more usable
rows recovered). Coefficients moved only slightly (all within their own standard errors of the
round-1 refit):

```
                                   Round 1 (pre-P8-012)   This round (post-P8-012)   SE        z
intercept:                        +0.262537               +0.263847              0.023542  +11.21
delivery_low:                     +0.442955               +0.441840              0.018075  +24.44
isolated:                         +0.019262                +0.019065              0.017047   +1.12
volume_ratio_high_band_eligible:  +0.191298                +0.190164              0.019894   +9.56
disclosure_SUBSTANTIVE:           -0.231665                -0.231507              0.024641   -9.40
disclosure_ROUTINE_ONLY:          -0.064696                -0.065065              0.025986   -2.50
disclosure_UNKNOWN_COVERAGE:      -0.159399                -0.165400              0.043277   -3.82
```

## 5. Phase 8b re-run

`scripts/phase10_amendment4_phase8b_reauc.py` (a separate script from `phase8b_feature_reauc.py`,
whose own committed output remains a historical record against pre-correction data). Real bug
found and fixed while building this: the original script's `HOLDOUT_CLASS_PATH` (`phase8_2026_
classifications.csv`, never rebuilt) would have silently overwritten the freshly-rebuilt HOLD-OUT
`cap_band` values, since `event_classifications.csv` now already covers the full range. Fixed by
reading only `event_classifications.csv` in the new script.

| Feature | TRAIN AUC (old → new) | HOLD-OUT AUC (old → new) |
|---|---|---|
| `zscore_60d` | 0.5270 → 0.5293 | 0.5374 → 0.5234 |
| `volume_ratio` | 0.5769 → 0.5787 | 0.5299 → 0.5390 |
| `delivery_pct_percentile_60d` | 0.4166 → 0.4202 | 0.4347 → 0.4618 |
| `return_20d_context_only` | 0.5328 → 0.5241 | 0.4753 → 0.4760 |
| `close_to_close_60d`* | 0.5197 → 0.5127 | 0.4836 → 0.4665 |
| `same_date_event_count` | 0.4675 → 0.4755 | 0.4639 → 0.4814 |
| `asm_gsm_labelled` | 0.5012 → 0.5002 | 0.5025 → 0.5028 |

*not rebuilt this session, stale feature file mixed with fresh population/label — caveat stated in
the re-run script's own docstring.

**No feature's direction reverses.** Every pre-registration inclusion/exclusion decision holds.
Magnitude shifts are larger than the earlier, narrower 342-event contamination-only sensitivity
check (<0.003 there; up to 0.027 here) — expected, since this correction touches far more of the
population (equity-only filtering alone removes ~10% of HOLD-OUT).

---

## What changed in the draft amendment (`docs/phase10_preregistration_amendment4.md`)

Rewritten §4 (missing-data) from scratch with the real diagnosis; corrected the threshold-direction
sentence; corrected §5 (secondary model) to specify old coefficients+thresholds together; added
standard errors to §3's coefficient table; added §6 (Phase 8b re-run); added §7 (derived-artifacts
rebuild policy); updated §1 to cite the actual wired `weekly_ingest.py` line; re-pinned to
`97a459e429f0dde5ae18a10e3cf1ce375df8259d`. **Still not committed — pending review, per
instruction.**
