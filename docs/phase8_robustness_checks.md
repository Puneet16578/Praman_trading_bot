# Phase 8 — Robustness Checks

**Status: pre-registration written and run exactly as specified below; no threshold, classification,
or scoring-rule was tuned in response to any result.** Where a number moved, the before/after is
stated. Logged as `P8-001` in `docs/DEFECT_REGISTER.md`.

## Summary (read this first)

**1(a)/(b) confirmed numerically:** raw `collapsed_90d` shares its `close(t−20)` anchor with
`return_20d_context_only` (0/15 spot-checked events mismatched, exact to 1e-6). **1(c), headline:**
under the pre-registered event-day-anchored, market-relative label, disclosure-tier-alone's
top-tier precision falls 78.7%→51.1% (exactly base rate, zero lift); the classifier's falls
90.6%(n=255)→28.6%(n=7, below base rate). Corrected decomposition, on a comparable footing (LIFT
over each label's own base rate, not raw Brier): drift-correction alone barely moves the
classifier's LIFT (+16.4pp raw → +15.9pp relative_t20); only removing the shared anchor collapses
it (−22.5pp / +6.7pp) — mechanical coupling, not drift, drove the headline. A cap-band-only baseline
goes *Brier-skill-negative* under the new label while the classifier's aggregate skill stays barely
positive despite its top cell failing — tested further in `docs/phase8b_clean_label_features.md`.
All three momentum features' TRAIN-optimal direction reverses; 2 of 3 fall to/below the new base
rate at precision@20. **Check 2:** the classifier and disclosure tier both beat the only *fair*
(non-oracle) constant baseline (0.2024/0.2091 vs. 0.2111) — they just don't beat the impossible
retrospective oracle (0.192). **Check 3:** "early warning" is complicated, not confirmed —
`UNEXPLAINED` is flagged *less* often than `GROUNDED`/`PARTIALLY_GROUNDED` at every horizon (and
`docs/phase8b_clean_label_features.md` traces this to `momentum_high` cutting across disclosure
tiers, not disclosure content itself), and ~7% of hold-out events are excluded from every label for
a reason (possible delisting/suspension) that skews toward undercounted collapses.

---

## Check 1 — The label

### 1(a): which label did Layers 2-3 score against?

**Confirmed: the raw `collapsed_90d` label**, not `collapsed_relative`. `scripts/phase8_layer2_metrics.py`'s
`compute_multi_horizon_collapse` computes it directly from raw adjusted closes (`g(hist, ...)`,
no division by `market_index.csv` anywhere in that function), and `scripts/phase8_layer3_baselines.py`
reads the same `phase8_2026_outcomes.csv` column. The 2026 hold-out's reported base rate — 74.1%
[95% CI, n=6,049] — is the exact top of the range `docs/phase6_signals.md`'s Check 1 table gives for
this same raw label by year (50.6%-74.1%), which that doc's own words say "was tracking market
drift, not move authenticity." Confirmed by code path, not only by the number matching.

### 1(b): does `collapsed_90d` share its anchor with `return_20d`?

**Confirmed, both by code comparison and by direct numeric spot-check.** `compute_multi_horizon_collapse`'s
`PRE_MOVE_LOOKBACK = 20` and `event_catalogue.py`'s `CUMULATIVE_WINDOW = 20` resolve to the
identical index, `days[idx − 20]`, via the identical `_return`-style adjusted-close lookup. A
15-event random spot-check (seed 42) reconstructed the collapse label's own pre-move base directly
and compared the implied 20-day return against the catalogue's own stored `return_20d_context_only`:

```
0 mismatches / 15 (exact match to 1e-6 on every sampled event)
```

A stock with a small `|return_20d|` therefore sits close to the exact point `collapsed_90d` checks
for a crossing back through — it "collapses" on almost any subsequent move, real signal or none.
This directly explains why low `|return_20d|` was Phase 6's single strongest predictor of collapse
(AUC 0.24-0.28, i.e., 0.72-0.76 correctly oriented) and why `UNEXPLAINED` (defined by
`momentum_high = False`, i.e., low `|return_20d|`) carves out the classifier's top precision tier —
before Check 1(c) below tests whether that is a real signal or the coupling itself.

### 1(c): re-scoring under a label that removes the coupling

**Pre-registered before running (unchanged from the top of this document, reproduced here for
context):** anchor `close(event_date)` (not `t−20`), market-relative (divide by
`market_index.csv`), direction-signed the same way `collapsed_90d`/`collapsed_relative` already
are. `R = direction × [(close(t+90)/index(t+90)) / (close(t)/index(t)) − 1]`, an **endpoint**
return (t to t+90), not the path-dependent "crossed at any point" scan the other two labels use —
a real methodological difference, stated here rather than found later. PRIMARY: `R < 0`.
SECONDARY: `R < −0.10`. Both reported regardless of outcome, per instruction.
Script: `scripts/phase8_robustness_relabel_t0.py`.

**Addition 1 applied: TRAIN-only (2019-2025) `(classification, cap_band)` and
`(disclosure_tier, cap_band)` score tables were re-derived from scratch under EACH label** —
never reusing a table built under a different label to score a different label's outcomes.
Classifications and frozen thresholds themselves are untouched throughout.
Script: `scripts/phase8_robustness_check1_rescoring.py`.

**Unconditional rates, TRAIN vs. HOLD-OUT, under all four labels compared (n=63,363 TRAIN /
n=6,049 HOLD-OUT throughout):**

| Label | TRAIN rate | HOLD-OUT rate | gap |
|---|---|---|---|
| raw_t20 (`collapsed_90d`, existing) | 60.2% | 74.1% | +13.9pp |
| relative_t20 (`collapsed_relative`, existing) | 74.9% | 77.8% | +2.9pp |
| relative_t0_primary (NEW, `R<0`) | 59.2% | 51.0% | **−8.2pp** |
| relative_t0_secondary (NEW, `R<−10%`) | 42.3% | 33.3% | −9.0pp |

**Baseline 3 (disclosure tier) vs. Baseline 4 (classifier), re-scored under each label
(2026 hold-out, n=6,049, 90-session horizon):**

| Label | B3 Brier | B3 max-tier precision | B4 Brier | B4 max-tier precision |
|---|---|---|---|---|
| raw_t20 (existing headline) | 0.2091 | 78.7% [74.2,82.6] n=362 (`ROUTINE_ONLY`×Micro) | 0.2024 | 90.6% [86.4,93.6] n=255 (`UNEXPLAINED`×Micro) |
| relative_t20 (drift-corrected only) | 0.1700 | 84.0% [79.8,87.4] n=362 | 0.1674 | 93.7% [90.1,96.1] n=255 |
| relative_t0_primary (NEW, coupling removed) | 0.2521 | 51.1% [43.9,58.3] n=180 (`NONE`×Mid) | 0.2520 | **28.6% [8.2,64.1]** n=7 (`UNEXPLAINED_ISOLATED`×Mega) |
| relative_t0_secondary (NEW, coupling removed) | 0.2260 | 35.0% [28.4,42.2] n=180 | 0.2264 | 40.0% [11.8,76.9] n=5 (`UNEXPLAINED_ISOLATED`×Small) |

**The max-score cell moves.** Under both raw and drift-corrected labels (same t−20 anchor), the
classifier's top tier is `UNEXPLAINED`×Micro, n=255 — a large, stable cell. Under both new,
t0-anchored labels, it jumps to `UNEXPLAINED_ISOLATED`×Mega (n=7) or ×Small (n=5) — tiny,
inconsistent between the primary and secondary threshold, and its own confidence interval spans
well below the population base rate. This is not a smaller version of the same finding; it is a
different, much noisier cell that a 25-value categorical score happens to land on once the
dominant `UNEXPLAINED`/momentum signal stops being informative.

**Correction to how the table above was first read: raw Brier and raw precision are NOT comparable
across rows, because each label has a different hold-out base rate (74.1% / 77.8% / 51.0% / 33.3%),
and both metrics are mechanically sensitive to the base rate a strategy is scored against. An
earlier version of this section read the Brier improvement from raw_t20 to relative_t20 as
"market drift was suppressing the effect" — that comparison is invalid as stated and is withdrawn.**
The corrected, comparable quantities (`scripts/phase8_robustness_check1_skillscore.py`):

- **LIFT** = a baseline's own max-tier precision minus *that label's own* hold-out base rate (0 = no
  information; comparable across labels because each is measured against its own chance level).
- **BSS** (Brier Skill Score) = `1 − Brier(baseline) / Brier(FAIR)`, where FAIR is the constant
  TRAIN-rate baseline scored on *that same label's* hold-out set (0% = no better than a constant
  informed only by the training period; comparable across labels for the same reason).
- **CAPBAND\_ONLY** (item 5, addition to the original ask): score = TRAIN rate for the event's
  `cap_band` alone — no `disclosure_tier`, no `classification` — added because both B3 and B4's
  score tables already condition on `cap_band`, so whatever skill they show could be coming
  entirely from band composition rather than from disclosure content or the classifier's own logic.

| Label | HOLD-OUT base rate | Baseline | Brier | BSS | Max-tier precision | LIFT |
|---|---|---|---|---|---|---|
| raw_t20 | 74.1% | B3 disclosure_tier | 0.2091 | 1.0% | 78.7% [74.2,82.6] n=362 | +4.6pp |
| raw_t20 | 74.1% | B4 classification | 0.2024 | 4.1% | 90.6% [86.4,93.6] n=255 | **+16.4pp** |
| raw_t20 | 74.1% | CAPBAND_ONLY | 0.2088 | 1.1% | 78.0% [75.7,80.2] n=1,252 | +3.9pp |
| relative_t20 | 77.8% | B3 disclosure_tier | 0.1700 | 2.0% | 84.0% [79.8,87.4] n=362 | +6.1pp |
| relative_t20 | 77.8% | B4 classification | 0.1674 | 3.5% | 93.7% [90.1,96.1] n=255 | **+15.9pp** |
| relative_t20 | 77.8% | CAPBAND_ONLY | 0.1696 | 2.2% | 85.5% [83.4,87.3] n=1,252 | +7.6pp |
| relative_t0_primary (NEW) | 51.0% | B3 disclosure_tier | 0.2521 | 1.7% | 51.1% [43.9,58.3] n=180 | +0.1pp |
| relative_t0_primary (NEW) | 51.0% | B4 classification | 0.2520 | 1.8% | 28.6% [8.2,64.1] n=7 | **−22.5pp** |
| relative_t0_primary (NEW) | 51.0% | CAPBAND_ONLY | 0.2572 | −0.3% | 49.7% [46.9,52.5] n=1,245 | −1.3pp |
| relative_t0_secondary (NEW) | 33.3% | B3 disclosure_tier | 0.2260 | 1.8% | 35.0% [28.4,42.2] n=180 | +1.7pp |
| relative_t0_secondary (NEW) | 33.3% | B4 classification | 0.2264 | 1.7% | 40.0% [11.8,76.9] n=5 | +6.7pp |
| relative_t0_secondary (NEW) | 33.3% | CAPBAND_ONLY | 0.2306 | −0.2% | 34.1% [31.5,36.7] n=1,245 | +0.8pp |

**The corrected decomposition, stated on comparable terms this time: B4's LIFT is essentially
unchanged by drift-correction alone (+16.4pp raw_t20 → +15.9pp relative_t20, both hold the same
t−20 anchor) and collapses only once the anchor itself moves (−22.5pp / +6.7pp under the two
t0-anchored labels). The decomposition's conclusion stands: mechanical coupling, not market drift,
is what was driving the original headline** — it now stands on a comparison that is actually valid,
not the earlier Brier-improvement framing.

**Item 5's cap-band-only baseline adds a second, independent line of evidence.** Under raw_t20 and
relative_t20, B4 (LIFT +16.4pp / +15.9pp) clearly exceeds CAPBAND_ONLY (LIFT +3.9pp / +7.6pp) — the
classifier is doing more than re-deriving cap_band under the coupled labels. Under
relative_t0_primary, CAPBAND_ONLY's BSS goes *negative* (−0.3%) — cap_band alone is worse than a
flat constant once the anchor coupling is removed — while B4 still shows a small positive BSS
(1.8%) despite its top tier's LIFT being sharply negative. These two numbers are not
contradictory: BSS is a whole-population average over all 25 cells, LIFT is specific to the single
arg-max cell. The honest reading is that B4's 25-cell table still captures a little coarse
variation in aggregate (mostly likely still disclosure_tier's own residual signal, tested directly
in `docs/phase8b_clean_label_features.md` item 6) even though its specific top cell is a tiny,
unreliable artifact (n=7) — not evidence that the top-tier finding was wrong.

### Re-running the naive-vs-correct direction comparison under the new label

Script: `scripts/phase8_robustness_check1_direction.py` (same method as
`scripts/phase8_precision_at_k_alternative_orderings.py`, outcome source swapped to
`collapsed_t0_primary`).

**Step 1 — TRAIN direction, old label vs. new label:**

| Feature | Old label (raw `collapsed_90d`) | New label (`collapsed_t0_primary`) |
|---|---|---|
| zscore_60d | AUC 0.4420 → rank LOW as collapse-prone | AUC 0.5270 → rank **HIGH** as collapse-prone |
| volume_ratio | AUC 0.4005 → rank LOW | AUC 0.5769 → rank **HIGH** |
| return_20d_context_only | AUC 0.2446 → rank LOW | AUC 0.5328 → rank **HIGH** |

**Every feature's empirically-correct direction flips**, and every AUC moves much closer to 0.50
(0.53-0.58 vs. 0.24-0.44 under the old label, i.e., far weaker once oriented). This is the direct,
predicted consequence of 1(b): `return_20d_context_only`'s apparent 0.24 AUC (0.76 oriented) was
overwhelmingly the anchor-sharing artifact, not a real momentum-persistence effect — under a label
that doesn't share its anchor, `|return_20d|` is only weakly informative (0.533), not the strongest
signal in the whole project as Phase 6 reported.

**Step 2 — precision@20 on the 2026 hold-out, each feature's own new-label-correct direction**
(n=6,049, new-label base rate 51.0%):

| Feature | Hits/20 | Precision | 95% CI |
|---|---|---|---|
| zscore_60d (high) | 3/20 | **15.0%** | [5.2%, 36.0%] |
| volume_ratio (high) | 16/20 | 80.0% | [58.4%, 91.9%] |
| return_20d_context_only (high) | 8/20 | **40.0%** | [21.9%, 61.3%] |

**Before/after:** under the old label, all three features scored 85-95% correctly directed, all
comfortably above that label's 74.1% base rate. Under the new label, only `volume_ratio` clears its
own 51.0% base rate; `return_20d_context_only` — the feature Phase 6 called "the strongest predictor
found in this entire investigation" — falls to 40.0%, *below* base rate; `zscore_60d` falls to
15.0%, far below. The single feature that holds up best under the decoupled label is the one Phase
6's own stratification work had called the *weaker* of the two momentum-shaped features
(`volume_ratio`, not `return_20d`) — a genuine reversal, not a rounding difference.

### Addition 4 — survivorship inside the forward window

Of the 4,795 2026 hold-out events with no computable 90-session outcome under any label (all three
labels share the identical `idx+90` existence gate, so this affects all of them identically):

| | n | % of the 4,795 |
|---|---|---|
| Data-cutoff proximity (global calendar also lacks 90 sessions after event_date — genuine) | 4,025 | 83.9% |
| **Possible delisting/suspension** (global calendar has 90+ sessions after event_date, but this symbol's own trading history ends first) | **770** | **16.1%** |

Heuristic, stated as such — this project has no direct delisting-event feed, only the comparison
between a symbol's own last trading day and the global EQ calendar (`market_index.csv`). 770 events
is 7.1% of the full 10,850-event hold-out, silently absent from every collapse-rate number in this
document and in `docs/phase8_evaluation_results.md` alike. A symbol that stops trading inside the
window is, if anything, the most severe form of "the move did not hold" — every label here treats
that as a missing observation, not a positive. All three labels are equally exposed (same gate), so
this does not change which label looks relatively better, but it means every absolute collapse rate
in this whole evaluation is a lower bound in expectation, not a neutral estimate.

---

## Check 2 — The 0.192 constant baseline is an oracle

Script: `scripts/phase8_robustness_check2_baselines.py`. Same label (raw `collapsed_90d`), same
6,049-event hold-out as the original Layer 3 table — this check is about the baseline table's own
framing, not the label question above.

| Baseline | Constant | Brier (2026 hold-out) | Precision at "top tier" |
|---|---|---|---|
| 1. Random | n/a (per-event uniform score) | 0.3328 (unchanged) | **74.1% [73.0,75.2]** — the theoretical expectation of a random arg-max pick, not a measured n=1 statistic |
| **FAIR** (constant = real 2019-2025 TRAIN rate) | 60.21% (n=63,363) | **0.2111** | n/a — a constant score ties the whole population, precision = base rate trivially |
| **ORACLE** (constant = the 2026 hold-out's own true rate — relabelled, not renamed away) | 74.14% (n=6,049) | **0.1917** | n/a, same reason |
| 3. Disclosure tier alone | — | 0.2091 | 78.7% [74.2,82.6] n=362 |
| 4. Deterministic classifier | — | 0.2024 | 90.6% [86.4,93.6] n=255 |

**Before/after:** the original document's framing ("the classifier does not beat a strategy that
uses no information at all") is corrected, not overturned. The 0.192 figure only beats the
classifier because it is computed from the answer key (2026's own realized mean) — a number that
does not exist as of 2025-12-31. **The only constant baseline actually computable in advance, FAIR
(0.2111), is worse than BOTH the classifier (0.2024) and disclosure-tier-alone (0.2091).** Under
this (raw-label) comparison, the classifier and disclosure tier both add real information relative
to anything an evaluator could have used without looking at 2026 at all; they simply cannot beat an
oracle that already knows 2026's answer. The random baseline's n=1 "precision" row is replaced with
its correct theoretical value (the base rate, 74.1%) rather than an arbitrary single draw.

---

## Check 3 — Lead time is conditional on being flagged

Script: `scripts/phase8_robustness_check3_leadtime.py`. Population: the 10,850-event 2026 hold-out,
minus 385 already-under-surveillance-at-event_date (no lead time to measure) and 8
flag-found-but-gap-not-computable (small trading-calendar gap) = **10,457 events**, before
right-censoring.

**Addition 5 — right-censoring applied per horizon**, using the global EQ trading calendar
(`market_index.csv`, 1,718 sessions, through 2026-09-15): only events with at least N sessions of
follow-up *before the data's own end* are included at horizon N, so late-2026 events are not
counted as "not flagged" purely because there hasn't been time to flag them yet.

| Horizon | Dropped (insufficient follow-up) | Eligible n | Pooled rate |
|---|---|---|---|
| 20 sessions | 984 / 10,457 | 9,473 | 15.6% [14.9,16.3] |
| 60 sessions | 2,728 / 10,457 | 7,729 | 22.9% [22.0,23.8] |
| 120 sessions | 6,212 / 10,457 | 4,245 | 26.4% [25.1,27.8] |

**By classification (fraction flagged WITHIN the horizon, out of ALL eligible events in that class —
not just the ones that got a lead time):**

| Classification | 20d | 60d | 120d |
|---|---|---|---|
| GROUNDED | 16.6% [15.5,17.7] n=4,414 | 24.3% [22.9,25.7] n=3,438 | 28.3% [26.2,30.4] n=1,811 |
| PARTIALLY_GROUNDED | **27.6% [25.6,29.8]** n=1,748 | **38.1% [35.7,40.6]** n=1,505 | **50.7% [46.7,54.6]** n=608 |
| UNEXPLAINED | **11.2% [9.9,12.6]** n=2,016 | **20.8% [18.9,22.9]** n=1,613 | 27.8% [25.2,30.6] n=1,063 |
| UNEXPLAINED_ISOLATED | 19.6% [13.1,28.4] n=102 | 27.8% [19.2,38.6] n=79 | 33.3% [13.8,60.9] n=12 |
| UNEXPLAINED_UNKNOWN_COVERAGE | 1.4% [0.9,2.3] n=1,193 | 0.2% [0.1,0.7] n=1,094 | 0.1% [0.0,0.8] n=751 |

**This complicates the "early warning" framing rather than confirming it.** `UNEXPLAINED` — the
class the original lead-time section highlighted as evidence of early detection — is flagged by the
exchange *less* often than `GROUNDED` at every single horizon (11.2% vs. 16.6% at 20d; 20.8% vs.
24.3% at 60d), and far less often than `PARTIALLY_GROUNDED` (which is flagged 2-3x more than either
other substantive class at every horizon — a genuinely new, unexplained pattern this check surfaced,
not one it went looking for). The original lead-time section's real finding — that `UNEXPLAINED`
events which *do* eventually get flagged take longer to get there (median 33 sessions vs. 12/9) — is
unaffected by this check and remains true; what this check adds is that most `UNEXPLAINED` events
are never corroborated by an exchange flag at all within the observable window (72.2% still
unflagged even at 120 sessions, eligible n=1,063). **State plainly, per instruction: ASM criteria
are themselves price/volume-variation rules (`docs/phase6_signals.md` Part B) — a flag 2-3 sessions
after a catalogued move is the same rule firing on the same move after a publication lag, detection
of the same event rather than early warning. The early-warning claim only stands where flag rates
differ meaningfully by class, and here they do differ — but not in the direction, or with the
interpretation, the original framing assumed.**

**By cap_band**, included for completeness (same population/right-censoring):

| cap_band | 20d | 60d | 120d |
|---|---|---|---|
| Micro | **20.3% [18.5,22.1]** n=1,876 | **33.5% [31.2,35.8]** n=1,659 | **38.9% [35.8,42.1]** n=930 |
| Small | 16.9% [15.3,18.7] n=1,902 | 24.6% [22.5,26.7] n=1,604 | 29.1% [26.2,32.2] n=863 |
| Mid | 12.7% [11.2,14.2] n=1,904 | 18.5% [16.6,20.5] n=1,555 | 26.5% [23.7,29.5] n=887 |
| Large | 13.8% [12.3,15.4] n=1,904 | 19.6% [17.7,21.7] n=1,489 | 21.8% [19.1,24.8] n=820 |
| Mega | 14.5% [13.0,16.1] n=1,887 | 16.9% [15.1,19.0] n=1,422 | 12.6% [10.4,15.2] n=745 |

Smaller cap bands are flagged more often at every horizon — consistent with ASM's own eligibility
criteria concentrating in smaller, thinner-float names (`docs/phase6_signals.md`'s ASM-reframe
section), not a claim about this project's own classification adding information beyond cap_band.

---

## What changes in RESULTS.md

1. The headline ("full system's top-tier precision clears disclosure-tier-alone's") is no longer
   stated as a bare finding — it is reported alongside the fact that it does not survive Check 1(c)'s
   label correction, with `P8-001` cited.
2. The 0.192 "beats the classifier" framing is corrected to name it ORACLE and add the FAIR
   baseline (0.2111), which the classifier and disclosure tier both beat.
3. The lead-time "early warning" claim is qualified with Check 3's flag-rate-by-class table.
4. `abs(return_20d_context_only)` is no longer cited as this project's strongest, best-supported
   feature without the caveat that its apparent strength was measured under a label check 1(b)/(c)
   show shares its own anchor.
