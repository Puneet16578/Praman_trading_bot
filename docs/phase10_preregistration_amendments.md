# Phase 10 Pre-registration — Amendment 1

**Dated 2026-09-22. This document amends `docs/phase10_preregistration.md` without editing it,
per that document's own immutability notice.** Both documents are frozen once committed — this
amendment itself is not edited after its own commit either. A future correction, if one is ever
needed, is Amendment 2, in a new file, never an edit to this one or to the original.

**Committed before any forward outcome exists**, same discipline as the original: the evaluation
window fixed in §3 below has not started accumulating 90-session outcomes as of this commit's
timestamp.

## Summary (read this first)

Three gaps in the original pre-registration, closed: (1) **the scoring function itself was never
specified** — features, directions, and thresholds existed but nothing said how they combine into
a probability. Fixed: an unregularized logistic regression, fit once on 2019-2025 TRAIN data under
`relative_t0_primary`, coefficients frozen below, never refit. (2) **max-tier LIFT breaks when a
model's top tier is tiny** (the current classifier's was n=7 under the clean label) — replaced with
**top-decile LIFT**, a fixed 10% of the evaluation set for every model including the current
classifier, with a seeded tie-break procedure (validated on already-spent 2026 data as a mechanism
check, not a result — it correctly handled a 1,155-way tie in a real run). Success criterion 2 is
now top-decile vs. top-decile. (3) **the evaluation window was unfixed** — now
2026-09-16 through 2027-01-15 (4 months, within the original 3-6 month range), expected to contain
~5,100 events at the historical rate, evaluated once, no interim looks.

---

## 1. The scoring function

**Fit on 2019-2025 TRAIN data only (`event_date < 2026-01-01`), target `relative_t0_primary`
(PRIMARY threshold, `R < 0`) — the identical TRAIN population and label every other Phase 8/8b/10
TRAIN-only measurement in this project uses.** Unregularized logistic regression
(`sklearn.linear_model.LogisticRegression(penalty=None)`, equivalent to classical MLE — no
hyperparameter to silently tune). Script: `scripts/phase10_fit_scoring_function.py`.

**Inputs, exactly as pre-registered, no features added:**

| Input | Definition |
|---|---|
| `delivery_low` | `delivery_pct_percentile_60d < 15.0` (pooled TRAIN median, `docs/phase10_preregistration.md`) |
| `isolated` | `same_date_event_count < 47` (pooled TRAIN median) |
| `volume_ratio_high_band_eligible` | `volume_ratio ≥` that event's own band's TRAIN median, **AND** `cap_band ∈ {Small, Large, Mega}` — a single interaction term (not per-band dummies): the simplest reading of "interacted with a Small/Large/Mega indicator so it carries no weight in Micro/Mid," and stated here explicitly since the original spec did not fix which of several possible interaction forms was meant |
| `disclosure_tier` | one-hot, **`NONE` as the reference level** (the "no disclosure" baseline — a choice, not fixed by the original spec, stated here so it isn't ambiguous later); `SUBSTANTIVE`, `ROUTINE_ONLY`, `UNKNOWN_COVERAGE` each get their own coefficient |

**TRAIN population:** 63,360 of 64,450 TRAIN events had every input and the label
(1,090 excluded for a missing `delivery_pct_percentile_60d`, `volume_ratio`, `same_date_event_count`,
or a computable `relative_t0_primary` outcome — the same kind of exclusion, for the same reasons,
every other TRAIN-only measurement in this project already reports).

**Feature prevalence in that population**, for context on what the fit saw: `delivery_low` 49.5%,
`isolated` 47.7%, `volume_ratio_high_band_eligible` 30.1% (lower than 50% by construction — it can
only be 1 in 3 of 5 bands), `disclosure_tier` SUBSTANTIVE 43.5% / ROUTINE_ONLY 31.2% /
UNKNOWN_COVERAGE 10.2% / NONE (reference) 15.1% (residual). Label (`collapsed_t0_primary`) base
rate: 59.2% (matches `docs/phase8_robustness_checks.md`'s already-reported TRAIN rate for this
label exactly — a direct consistency check, not a new number).

**The frozen coefficients — computed once, written here, never refit:**

```
intercept:                            +0.242510
delivery_low:                         +0.440636
isolated:                             +0.035727
volume_ratio_high_band_eligible:      +0.210644
disclosure_SUBSTANTIVE:               -0.233919
disclosure_ROUTINE_ONLY:              -0.061484
disclosure_UNKNOWN_COVERAGE:          -0.396295
```

Score for a new event: `p = sigmoid(intercept + Σ coefficient × input)`, inputs as defined above,
`NONE` disclosure contributing 0 (the reference level). **In-sample (TRAIN) AUC 0.5870, Brier
0.2362** — reported for the record, not as a forward-generalization claim; TRAIN performance is not
what the pre-registered success criterion is judged against.

**Reading the coefficients, briefly, without treating this as a new finding session:**
`delivery_low`'s coefficient (+0.441) is the largest in magnitude, consistent with
`docs/phase8b_clean_label_features.md` item 3 calling it the most uniform feature measured.
`isolated`'s own coefficient (+0.036) is much smaller than its univariate AUC (~0.53, item 3) would
suggest alone — expected in a multivariate fit when inputs are correlated with each other, not a
contradiction of the univariate result. `SUBSTANTIVE` and `UNKNOWN_COVERAGE` both carry a NEGATIVE
coefficient relative to `NONE` (lower predicted collapse probability than no-disclosure), consistent
with disclosure tier's own real, if modest, contribution found in `docs/phase8b_clean_label_features.md`
item 6 on a different outcome (flag rate, not collapse) — reported as directionally consistent, not
claimed as the same finding restated.

## 2. Top-decile LIFT, replacing max-tier LIFT

**Problem this replaces:** `docs/phase8_robustness_checks.md` Check 1(c) found the current
classifier's own max-scored tier under `relative_t0_primary` was n=7 — too small and too unstable
(its identity even moved between the primary and secondary thresholds) to be the metric a success
criterion hinges on. Max-tier LIFT rewards or punishes models based on how a 25-value categorical
score happens to break, not on genuine ranking quality.

**Procedure, fixed now for every model that will be scored, including the CURRENT classifier:**

1. Score every event in the evaluation set.
2. `k = round(n_total × 0.10)` — the top decile, by count, not by score threshold.
3. Sort descending by score. Every event with a score strictly greater than the score at rank `k`
   is "clearly in" the top decile.
4. If ties span the rank-`k` boundary (expected for the current classifier's coarse categorical
   score, and possible for the new logistic score if many probabilities round together), fill the
   remaining slots needed to reach exactly `k` by sampling from the tied-at-boundary group with
   `random.Random(42).sample(...)` — **seed 42, this project's own established default** (Layer 1's
   2,000-event sample used the same seed, `docs/phase8_evaluation_results.md`).
5. `precision = hits / k` on the resulting top-`k` set. `LIFT = 100 × precision − 100 ×` the
   evaluation set's own base rate.

**Mechanism validated, not a result** (`scripts/phase10_topdecile_lift_mechanism_check.py`, run
against the already-spent 2026 hold-out purely to confirm the procedure executes correctly on a
real, heavily-tied score before committing to it for data that doesn't exist yet): the current
classifier's `classification`-only score on 2026 produced `k=605`, a 1,155-way tie at the boundary
score (0.6275) with only 27 events clearly above it and 578 needed from the tie — exactly the kind
of boundary case this procedure exists to handle, resolved deterministically and reproducibly given
the fixed seed. **This number (LIFT ≈ +2.0pp) is a mechanism check on spent data, is NOT a forward
result, and must not be cited as evidence about the redesign's performance.**

**Success criterion 2, restated from `docs/phase10_preregistration.md` (§ Success criterion), now
in terms of this metric:** the new design's top-decile LIFT must exceed the current classifier's
own top-decile LIFT, both computed on the identical forward evaluation set from §3, same procedure,
same seed.

## 3. The evaluation window, fixed now

**Window: catalogued events with `event_date` from 2026-09-16 through 2027-01-15 inclusive** (4
calendar months — within the original pre-registration's stated 3-6 month range). Chosen for size:
at the historical rate this project's own 2026 hold-out established — 10,850 events over
2026-01-01 through 2026-09-15 (258 days, 8.5 months) is **1,276 events/month, computed directly,
not assumed** (matches the "~1,275/month" figure this amendment was asked to state) — 4 months is
expected to contain **~5,100 events**, comparable in size to the 6,049-event 2026 hold-out this
project's other metrics are reported against.

**Evaluated exactly once**, after the LAST event in the window (2027-01-15) has 90 real trading
sessions of forward history, so its `relative_t0_primary` outcome is computable for every event in
the window. At roughly 21 trading sessions per calendar month, 90 sessions is approximately 4.3
calendar months — the earliest this evaluation can run is therefore approximately **late May
2027**, an estimate only (the real trading calendar, holidays, and this project's own data
ingestion cadence are not known that far in advance, and this document does not pretend otherwise).

**No interim looks at outcomes before that date.** Checking the window's events' outcomes before
the last one has reached 90 sessions — even "just to see" — would be exactly the kind of look this
pre-registration exists to prevent, and would need its own dated amendment stating that it happened
before any such look, not after.

---

## What is still not done

Per the original pre-registration and this amendment alike: **nothing is built, nothing is
evaluated.** The scoring function's coefficients are frozen numbers in this document, not code in
`src/`. No forward data exists yet. The next real action on this pre-registration is the evaluation
itself, not before 2027-01-15 has 90 sessions of forward history behind it.
