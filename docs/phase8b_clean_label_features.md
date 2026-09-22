# Phase 8b — Feature Re-analysis Under the Clean Label

**Measurement only, per instruction — the classifier is not redesigned here.** Everything below
uses `relative_t0_primary` (`docs/phase8_robustness_checks.md`'s pre-registered, event-day-anchored,
market-relative label), the frozen thresholds, and the existing classification — unchanged.

## Summary (read this first)

Re-ran Phase 6's feature-vs-outcome analysis under the decoupled label, TRAIN and HOLD-OUT, pooled
and by cap_band. **The classifier's current core axis does not survive:** `return_20d_context_only`
(TRAIN AUC 0.533) flips sign on the 2026 hold-out (0.475, CI [0.461,0.490], entirely below 0.5);
`close_to_close_60d` shows the same pattern (0.520→0.484). Both were Phase 6's strongest features
under the coupled label. **`volume_ratio` confirms the ORIGINAL design hypothesis** (high →
underperformance, TRAIN 0.577, hold-out 0.530) but only in Small/Large/Mega — Micro/Mid are chance
on hold-out. **A real signal Phase 6 never found emerges: `delivery_pct_percentile_60d`** — a
consistent, correctly-signed effect in every band, both splits (0.40-0.47) — not used anywhere in
`classify_event()` today. `same_date_event_count`/ASM status are unaffected (already near-null).
Cap-band-only (item 5) goes Brier-skill-negative under the clean label. `PARTIALLY_GROUNDED`'s
flag-rate finding (item 6) is overwhelmingly a `momentum_high` effect — `GROUNDED`, which doesn't
depend on momentum_high, shows the *same* ~20pp gap — with a smaller, real disclosure-tier gradient
underneath, more visible at 120 sessions than at 20.

---

## Item 3 — Phase 6's feature analysis, re-run under `relative_t0_primary`

Script: `scripts/phase8b_feature_reauc.py`. TRAIN n=63,363 (2019-2025), HOLD-OUT n=6,049 (2026) —
the walk-forward split Phase 6 itself never had (Phase 6 measured TRAIN-period AUCs only). AUC
confidence intervals use the Hanley-McNeil (1982) normal approximation, named explicitly since this
project always names its statistical methods. Direction tested throughout: does a HIGH value of the
feature (absolute value, for the signed ones) predict collapse under the clean label — matching
Phase 6's own convention — except `delivery_pct_percentile_60d`, tested non-negated (Phase 6's own
convention there too, since the original design hypothesis was "low delivery predicts collapse").

| Feature | TRAIN pooled | HOLD-OUT pooled |
|---|---|---|
| zscore_60d | 0.5270 [0.5224,0.5315] | 0.5374 [0.5229,0.5519] |
| volume_ratio | 0.5769 [0.5724,0.5814] | 0.5299 [0.5154,0.5445] |
| delivery_pct_percentile_60d | 0.4166 [0.4120,0.4211] | 0.4347 [0.4203,0.4491] |
| return_20d_context_only | 0.5328 [0.5282,0.5373] | **0.4753 [0.4608,0.4898]** |
| close_to_close_60d | 0.5197 [0.5152,0.5243] | 0.4836 [0.4691,0.4982] |
| same_date_event_count | 0.4675 [0.4629,0.4721] | 0.4639 [0.4494,0.4784] |
| asm_gsm_labelled | 0.5012 [0.4967,0.5058] | 0.5025 [0.4879,0.5170] |

**Stratified by cap_band (5-way Micro/Small/Mid/Large/Mega — sourced from
`event_classifications.csv`/`phase8_2026_classifications.csv`'s own per-year quintile bands, not
the catalogue's older 3-way `cap_band` column, which does not carry Micro/Mega at all — a real
mismatch caught and fixed while writing this script, not a finding):**

| Feature | Micro TRAIN / HOLD-OUT | Small | Mid | Large | Mega |
|---|---|---|---|---|---|
| zscore_60d | 0.529 / **0.577** | 0.547 / **0.605** | 0.522 / 0.505 | 0.515 / 0.493 | 0.518 / 0.506 |
| volume_ratio | 0.561 / 0.505 | 0.603 / 0.539 | 0.587 / 0.500 | 0.570 / 0.537 | 0.556 / **0.593** |
| delivery_pct_percentile_60d | 0.448 / 0.422 | 0.395 / 0.380 | 0.411 / 0.470 | 0.410 / 0.444 | 0.426 / 0.423 |
| return_20d_context_only | 0.529 / **0.404** | 0.540 / 0.482 | 0.533 / 0.497 | 0.522 / 0.480 | 0.534 / 0.521 |
| close_to_close_60d | 0.508 / 0.440 | 0.523 / 0.516 | 0.522 / 0.492 | 0.517 / 0.488 | 0.524 / 0.485 |
| same_date_event_count | 0.455 / 0.462 | 0.455 / 0.470 | 0.467 / 0.465 | 0.486 / 0.471 | 0.479 / 0.451 |
| asm_gsm_labelled | 0.508 / 0.507 | 0.502 / 0.503 | 0.499 / 0.502 | 0.498 / 0.500 | 0.500 / 0.499 |

(format: TRAIN AUC / HOLD-OUT AUC, both pooled-direction; full CIs in the script's own output)

**Reading this plainly, stratified before believed, per instruction:**

- **`return_20d_context_only` and `close_to_close_60d` — the two features the ENTIRE momentum axis
  and Phase 6's "0.70 ensemble ceiling" were built on — fail to generalize.** TRAIN says weak-but-
  real (0.52-0.53, both features, every band); HOLD-OUT is at or below 0.50 in 4 of 5 bands for
  both, and the pooled hold-out AUC for `return_20d_context_only` (0.475, CI entirely below 0.5) is
  the single strongest reversal in this table — worst in Micro specifically (0.404), the exact band
  the original classifier's top precision tier (`UNEXPLAINED`×Micro) was built on. This is not a
  small effect: a feature TRAIN said was weakly informative in the collapse-predicting direction
  is, on real 2026 data, mildly informative in the OPPOSITE direction.
- **`volume_ratio` partially confirms the original design hypothesis, but is band-conditional, not
  uniform** — see item 4 below.
- **`delivery_pct_percentile_60d` is a genuinely new finding: consistent, correctly-signed,
  non-trivial signal in every band, on both TRAIN and HOLD-OUT** (0.40-0.47 throughout — recall
  AUC is symmetric around 0.5, so this is exactly as strong as 0.53-0.60 oriented the other way).
  Phase 6 measured this same feature against the *coupled* labels and found it essentially null
  (pooled AUC 0.4793 raw / 0.5062 relative, "indistinguishable from chance," `docs/phase6_signals.md`)
  — the clean label recovers a real effect Phase 6's own coupled measurement could not see.
  **`delivery_pct_percentile_60d` is not used anywhere in `classify_event()`'s decision logic** —
  it is reported as a signal field on every event but plays no role in `disclosure_tier`,
  `momentum_high`, or `is_isolated`. This is the clearest concrete redesign target this document
  produces.
- **`same_date_event_count` and `asm_gsm_labelled` are unaffected by the label swap** — both were
  already near-null under the coupled labels (Phase 6) and remain near-null here. Consistent, not
  surprising, recorded for completeness.

## Item 4 — volume_ratio, confirmed but not uniformly

**Claim to confirm: high volume_ratio predicts underperformance (TRAIN AUC 0.577), the ORIGINAL
design hypothesis the coupled label had inverted (Phase 6 found volume_ratio *below* 0.50 in every
cut it measured).** The pooled hold-out precision@20 result from `docs/phase8_robustness_checks.md`
(16/20 = 80.0%, well above the new label's 51.0% base rate) and this item's own pooled hold-out AUC
(0.5299, CI [0.5154,0.5445], excludes 0.50) both point the same way — **the reversal is real, not a
20-event fluke.**

**Confirmed only partially once stratified, per instruction to stratify before believing anything.**
Hold-out AUC by band: Micro 0.505 (chance), Small 0.539, Mid 0.500 (chance), Large 0.537,
**Mega 0.593 (strongest band)**. The pooled effect is real, but it is carried by Small/Large/Mega —
Micro and Mid show no distinguishable effect on 2026 data at all, even though TRAIN suggested a
real effect in every band (0.561-0.603). **Do not state "volume_ratio predicts underperformance"
as a uniform, band-independent finding — state it as real in aggregate and in three of five bands,
absent in Micro and Mid on this hold-out.** The precision@20 result (n=20) is a small sample from a
population where this band-unevenness could matter — most of the 20 top-ranked events are very
likely concentrated in bands where the effect is real, which is consistent with, not contradictory
to, the banded picture here.

## Item 5 — cap-band-only baseline

Reported in full in `docs/phase8_robustness_checks.md` Check 1(c) (script:
`scripts/phase8_robustness_check1_skillscore.py`); summarized here because it bears directly on
what a redesign should target. Under `relative_t0_primary`: CAPBAND_ONLY's Brier Skill Score is
**−0.3%** (worse than a flat constant) and its LIFT is −1.3pp — cap_band alone carries no
information under the clean label. B4 (the full classifier) still shows a small positive BSS
(1.8%) in aggregate despite its top tier failing — **the aggregate skill the classifier retains is
not coming from cap_band**, which strengthens (not weakens) the case that whatever residual signal
survives in the 25-cell table is coming from `disclosure_tier` — tested directly next.

## Item 6 — is PARTIALLY_GROUNDED's flag rate about disclosure, or about momentum?

`PARTIALLY_GROUNDED` and `UNEXPLAINED` are, by construction (`classify_event()`), **the identical
disclosure-tier population** (`ROUTINE_ONLY`, or `NONE`-and-not-isolated) **split purely by
`momentum_high`** — nothing else distinguishes them. So Check 3's finding that `PARTIALLY_GROUNDED`
is flagged 2-3x more often than `UNEXPLAINED` is, structurally, already a `momentum_high`
comparison, not a disclosure-tier one — stated here explicitly rather than left implicit.

**Decisive test: does `GROUNDED` (`disclosure_tier=SUBSTANTIVE`, which does NOT depend on
momentum_high in the classification rule at all) show the same gap by momentum_high?**
Script: `scripts/phase8b_momentum_flagrate_check.py`. Same population/right-censoring as Check 3.

| Horizon | SUBSTANTIVE (GROUNDED), momentum_high=True | momentum_high=False | gap |
|---|---|---|---|
| 20d | 27.8% [25.9,29.9] n=1,924 | 8.0% [7.0,9.1] n=2,490 | +19.8pp |
| 60d | 36.2% [33.8,38.7] n=1,495 | 15.1% [13.6,16.8] n=1,943 | +21.1pp |
| 120d | 42.7% [38.8,46.7] n=602 | 21.1% [18.9,23.5] n=1,209 | +21.6pp |

Compare directly to the `PARTIALLY_GROUNDED` vs. `UNEXPLAINED` gap Check 3 reported: +16.4pp (20d,
27.6% vs. 11.2%), +17.3pp (60d), +22.9pp (120d) — **essentially the same gap, in an event population
(`GROUNDED`) that cannot possibly owe it to the `PARTIALLY_GROUNDED`/`UNEXPLAINED` disclosure split,
because `GROUNDED` doesn't have one.** `momentum_high` alone, pooled across every disclosure tier,
shows the same ~18-21pp gap at every horizon (25.7% vs. 8.0% at 20d; 33.8% vs. 14.5% at 60d; 40.5%
vs. 19.4% at 120d).

**Does disclosure_tier still matter once momentum_high is held fixed? A little, and more so at
120 sessions than at 20.** Within `momentum_high=True`, the three disclosure tiers are nearly
indistinguishable at 20d (SUBSTANTIVE 27.8%, ROUTINE_ONLY 27.6%, NONE 27.7%) and only start to
separate at 120d (SUBSTANTIVE 42.7%, ROUTINE_ONLY 46.4%, NONE 57.0%). Within `momentum_high=False`,
a small, consistent, monotonic gradient is visible at every horizon (SUBSTANTIVE 8.0%/15.1%/21.1%
< ROUTINE_ONLY 11.6%/19.9%/26.0% < NONE 10.1%/22.2%/30.7%, roughly) — smaller than the momentum
effect but real and directionally sensible (less disclosure, more likely to eventually get flagged).

**Recorded plainly, per instruction, either way: the class was substantially re-deriving the
exchange's own trigger, not primarily adding information from disclosure content — at least at the
20/60-session horizons, where disclosure_tier's own contribution is close to zero once momentum is
held fixed. It is not PURELY re-derivation** — a smaller, real, disclosure-tier-driven gradient
survives, particularly by 120 sessions and particularly among low-momentum events. NSE's own
published ASM criteria (`docs/phase6_signals.md` Part B) include close-to-close price variation
thresholds directly, so a `momentum_high`-driven flag-rate effect is exactly the mechanism this
document's own sourcing work already predicted, not a new coincidence.

---

## What a redesign would target (reported, not built, per scope)

Based on item 3 specifically, not on any other section of this evaluation:

1. **`momentum_high` (built on `return_20d_context_only`) is the single highest-priority item to
   re-validate or drop.** It is the classifier's current core discriminating axis (it alone
   separates `PARTIALLY_GROUNDED` from `UNEXPLAINED`, and gates `UNEXPLAINED_ISOLATED`), and it is
   the one shown here to reverse sign on real, out-of-sample 2026 data once measured against a
   label that does not share its own anchor.
2. **`delivery_pct_percentile_60d` is a real, currently-unused signal** (consistent, correctly
   signed, every band, both TRAIN and HOLD-OUT) that plays no role in `classify_event()` today —
   the clearest concrete addition this analysis identifies.
3. **`volume_ratio` is worth keeping, but only with a band interaction** (real in Small/Large/Mega,
   absent in Micro/Mid on hold-out) — a uniform, pooled use of it would misrepresent Micro/Mid
   events specifically, the two bands where this project's catalogue is most concentrated.
4. **`same_date_event_count` (isolation) and ASM/GSM status add nothing under either label version**
   — dropping or deprioritizing them is not a loss of signal Phase 6 hadn't already found.

None of this has been implemented. This is a measurement of where a future redesign's evidence
points, not a recommendation acted on here.

---

## Standing check (item 7)

Recorded in `praman/CLAUDE.md`'s "Recurring failure modes" section: **before any feature is
evaluated against an outcome label, state explicitly whether they share an input.** This has now
happened twice in this project — `collapsed_90d` shared its anchor with `return_20d_context_only`
(`P8-001`), and `momentum_high`'s flag-rate association was substantially the same quantity NSE's
own ASM criteria use directly (item 6, above). Two independent instances of the same failure shape
is exactly the threshold this project's own defect register (P4-012/P4-013) has previously treated
as "stop patching individually, add a standing check" — applied here to evaluation methodology
rather than to a parser.
