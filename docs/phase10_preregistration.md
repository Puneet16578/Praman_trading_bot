# Phase 10 — Redesign Pre-registration

**This document is a specification, not an implementation. Nothing described here has been built
or evaluated. The classifier is not touched by this document.**

**Immutability notice: this document is not edited after the commit that introduces it.** Its
value as pre-registration depends on that. Any correction, refinement, or change of mind after
this commit belongs in a NEW document (e.g. `docs/phase10_preregistration_amendments.md`) that
references this one and states a reason and a date — never as an edit to the text below. The
git commit timestamp of this file is the proof that every choice below was made before any forward
evaluation data existed.

**Why now, not later:** `docs/phase8b_clean_label_features.md` used 2026 hold-out AUCs to decide
which features generalize under the decoupled label. That is model selection informed by test-set
performance — 2026 is no longer a clean hold-out for a model whose feature set was chosen using it
(`praman/CLAUDE.md`, Evaluation integrity). Every choice below is therefore frozen BEFORE any
forward data exists, so a future evaluation on genuinely new data is not contaminated the same way.

---

## Features and directions

| Feature | Direction | Status |
|---|---|---|
| `delivery_pct_percentile_60d` | LOW → underperform | IN — weak but consistent, every band, both TRAIN and 2026 hold-out (`docs/phase8b_clean_label_features.md` item 3) |
| `volume_ratio` | HIGH → underperform, **with a band interaction** | IN, conditionally — weak but consistent in Small/Large/Mega only; treated as uninformative in Micro/Mid (item 3/4) |
| `same_date_event_count` | LOW → underperform (isolated moves underperform) | IN — weak but consistent, at least as stable TRAIN→HOLD-OUT as `volume_ratio` (item 3, corrected reading) |
| `disclosure_tier` | SUBSTANTIVE lowest risk, NONE highest, ROUTINE_ONLY between | IN — retained as-is; item 6 found it carries a smaller, real, independent gradient once `momentum_high` is held fixed, on the flag-rate outcome (a different outcome variable from collapse — not double-counted as evidence for both) |
| `momentum_high` / `return_20d_context_only` | — | **DROPPED.** The classifier's current core axis. Reverses sign on real, out-of-sample 2026 hold-out data once scored against a label that does not share its own anchor (`docs/phase8_robustness_checks.md` Check 1(c); `docs/phase8b_clean_label_features.md` item 3, pooled hold-out AUC 0.475, CI entirely below 0.5). `close_to_close_60d`, its close correlate (0.74 correlation, Phase 6), is not substituted in as a replacement without its own independent re-validation. |
| `zscore_60d` | — | **NOT INCLUDED.** Band-conditional (real Micro/Small, chance Mid/Large/Mega) AND non-monotonic at the extreme tail (P@20 15%, far below base rate, despite a positive pooled AUC) — too unstable a shape to spec a single rule around here. |
| ASM/GSM-labelled status | — | **NOT INCLUDED.** The one feature that adds nothing under any label version tested, coupled or clean. |

## Label

`relative_t0_primary` (`docs/phase8_robustness_checks.md`): market-relative, event-day-anchored,
signed by initial direction, endpoint return at **90 sessions**. `R = direction × [(close(t+90)/
index(t+90)) / (close(t)/index(t)) − 1]`. Collapse := `R < 0`. Not the secondary (`R < −0.10`)
threshold — the primary only, to match what item 3's feature validation was actually measured
against.

## Thresholds — fit on 2019-2025 ONLY, computed now, frozen

Script: `scripts/phase10_compute_thresholds.py`. TRAIN population: 64,450 events (`event_date <
2026-01-01`), the same TRAIN population every other Phase 8/8b TRAIN-only measurement in this
project uses. Median chosen as the split point for `delivery_pct_percentile_60d` and
`same_date_event_count` (simplest symmetric boundary, and both showed a fairly uniform effect
across bands in item 3 — no reason to prefer a different percentile over median for either);
`volume_ratio` computed per band because item 3 found it real only in three of five bands.

| Feature | Threshold | n |
|---|---|---|
| `delivery_pct_percentile_60d` (pooled) | **15.0000** — `delivery_low` := value < 15.0 | 64,447 |
| `same_date_event_count` (pooled) | **47.0000** — `isolated` := value < 47 | 64,450 |
| `volume_ratio`, Micro | 4.7182 | 12,893 |
| `volume_ratio`, Small | 6.6737 | 12,890 |
| `volume_ratio`, Mid | 7.2739 | 12,890 |
| `volume_ratio`, Large | 8.4210 | 12,890 |
| `volume_ratio`, Mega | 7.5811 | 12,887 |

`volume_ratio_high` := value ≥ that event's own band median. **Per the band-interaction finding:
the `volume_ratio_high` flag is only to be treated as informative in Small/Large/Mega. In
Micro/Mid it is computed (for completeness and future re-testing) but not weighted as evidence** —
item 3's hold-out AUC in those two bands was indistinguishable from chance (0.505, 0.500).

**Note on `same_date_event_count`'s threshold, distinct from the isolated_comovement_threshold
already in the live classifier:** the current classifier's `is_isolated` flag uses a TRAIN-only
p25 cutoff for a different purpose (carving out `UNEXPLAINED_ISOLATED`, `scripts/
phase8_freeze_thresholds.py`). This pre-registration's `isolated` threshold (median, 47) is a
SEPARATE quantity for a general-purpose feature role, not a replacement for that existing p25
cutoff — the two are not required to match, and this document does not touch the existing
classifier's own threshold.

## Evaluation protocol

**FORWARD only.** No evaluation happens until events with `event_date > 2026-09-15` (this
project's own most recent bhavcopy as of this pre-registration) have accumulated at least 90
trading sessions of forward history, so their `relative_t0_primary` outcome is computable. This
is not the existing 2026 hold-out re-used — that hold-out is spent (see the Evaluation Integrity
note in `praman/CLAUDE.md` and `docs/RESULTS.md`). The first eligible forward-evaluation date is
therefore whatever future date is 90 trading sessions past this document's own commit date plus
however long it takes new events to accumulate — not computed here, because computing it requires
data that does not exist yet.

**Metrics, fixed now, before any forward data exists:**
- **BSS** (Brier Skill Score) vs. a FAIR constant baseline (the TRAIN 2019-2025
  `relative_t0_primary` rate, computed once now: see `docs/phase8_robustness_checks.md`'s
  `relative_t0_primary` TRAIN rate, 59.2%, — re-confirm at evaluation time against whatever the
  final pre-2026-01-01 TRAIN population is, but do not refit it on anything after 2026-01-01).
- **LIFT** at the max-scored tier (max-tier precision minus the forward evaluation set's own base
  rate) — the same quantity `docs/phase8_robustness_checks.md`/`phase8b` used throughout.
- **Per-band AUC with 95% CIs** (Hanley-McNeil, as in `scripts/phase8b_feature_reauc.py`) for the
  new design's own combined score, pooled and by cap_band.
- **BSS confidence interval**: paired bootstrap, 2,000 resamples of the forward evaluation set,
  recomputing BSS each resample, 2.5/97.5 percentiles — specified now, before the forward data
  exists, so the CI method itself is not chosen post-hoc to flatter a result.

**Baselines, evaluated on the identical forward set:**
1. Random
2. Naive threshold (`|return_1d| > 10%`)
3. Disclosure tier alone
4. Cap-band alone
5. **The CURRENT (existing, `momentum_high`-based) classifier** — run unchanged, as a live
   comparison point for whether the redesign is actually better, not merely different
6. The new design (this pre-registration)

(Baselines 1-3 mirror the five originally used in Phase 8 Layer 3; cap-band-alone is added per
`docs/phase8b_clean_label_features.md` item 5's finding that it is not redundant information to
skip; the current classifier is added because "beats the thing it replaces" is the only comparison
that actually justifies a redesign.)

## Success criterion — written now, binding

**The new design succeeds if, and only if, BOTH hold on the first forward evaluation set:**
1. Its BSS vs. FAIR has a 95% (bootstrap) confidence interval that excludes zero, AND
2. Its LIFT at the max-scored tier exceeds baseline 5's (the current classifier's) LIFT at ITS OWN
   max-scored tier on the same forward set.

Falling short of either condition is not a reason to lower the bar after seeing the result — per
`praman/CLAUDE.md`'s inherited evaluation-integrity rule, if the criterion is later judged to have
been genuinely malformed, that requires a dated correction stating the before/after impact, in a
new document, never a silent edit to this one.
