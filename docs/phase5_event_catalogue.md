# Phase 5 — The event catalogue

Status: threshold comparison complete, per explicit instruction to stop here. No signal or
classification logic has been built. Nothing in this phase writes a new fact table — the
catalogue is derived data, recomputed from `bhavcopy` + `corporate_actions` + `surveillance_flags`
every run (`python scripts/build_event_catalogue.py`).

## 1. What "unusual" means here

An "unusual move" is defined relative to each stock's own trailing distribution, not a global
threshold — a 3% move is unusual for a low-volatility utility and unremarkable for a small-cap.
For each `(symbol, trading day)` with at least 60 prior trading days of history:

- 1-session return and 20-session cumulative return, both corporate-action-adjusted
- z-score and percentile rank of the 1-session return against its own trailing 60-session window
- volume ratio: traded quantity vs. trailing 60-session median
- delivery percentage and its own trailing 60-session percentile

A day is a *candidate event* if `(|z| > Z or |20d cumulative| > C) AND volume ratio > V` for a
given threshold bracket. See §4 for the three brackets compared.

## 2. Architecture

`src/signals/event_catalogue.py`:

- `SymbolHistory` — one per symbol, built once by `build_symbol_history()`. Holds the full
  bhavcopy vintage history (keyed by `event_date`, each a list of `(knowledge_date, row)` pairs so
  the correct vintage can be resolved *as of any day*, not just the latest) plus the symbol's
  `corporate_actions` as two precomputed step functions: `cum_factor_up_to(date)` (cumulative
  BONUS/SPLIT adjustment factor) and `demerger_dates` (sorted DEMERGER event dates).
- `compute_daily_stats(hist)` — the main loop, walks trading days from index 60 onward and emits
  one `DailyStat` per day.

### 2.1 Why bhavcopy and corporate_actions are treated differently

This is the one place in the codebase where two tables that are both bitemporal are handled with
genuinely different code paths, and it is deliberate, not an inconsistency:

- **`corporate_actions` is timing-agnostic for this catalogue.** A BONUS or SPLIT ratio, once it
  exists in the store at all, does not change with `as_of` — NSE does not restate a 4:1 bonus into
  a 3:1 bonus later. So `cum_factor_up_to()` is built once per symbol from *all* actions ever
  written, with no `as_of` filter, and is valid for computing a return as of any later date. This
  is what lets the whole per-symbol adjustment collapse into O(1) lookups per day instead of one
  `compute_adjustment_factor()` call per pair.

  **`EX_DATE_FALLBACK` does not apply to this path.** That confidence tier exists on
  `corporate_actions` for a different reason — some ex-dates are themselves uncertain/inferred —
  and it governs whether a *specific announcement's effective date* can be trusted for as-of
  correctness at the time it was newly published. It has nothing to do with this catalogue, which
  only cares whether the ratio value is stable across `as_of`, not whether any single as-of query
  near the announcement date would have seen the right effective date. Do not reapply that
  reminder here — it was misapplied once already during planning, before any code was written.

- **`bhavcopy` is NOT timing-agnostic.** A raw close price, volume, or delivery percentage *can*
  legitimately be restated at a later `knowledge_date` with a different value (NSE republishes
  corrected bhavcopy rows). So every raw price/volume/delivery lookup resolves to the specific
  vintage visible as of the day being evaluated — `SymbolHistory.price_row_as_of(event_date,
  as_of)` — never a single precomputed "final" series.

### 2.2 The vectorized return, and its guarded precondition

For a return between two dates `D1 <= D2 <= as_of`, adjustment normally requires
`compute_adjustment_factor(D1, as_of)` and `compute_adjustment_factor(D2, as_of)` computed
separately per pair. Algebraically, if `g(D) = raw_close_as_of(D) * cum_factor_up_to(D)`, then
`adjusted_close(D2,as_of) / adjusted_close(D1,as_of) == g(D2) / g(D1)` — the `as_of`/`T`
dependence cancels out exactly, **given that every corporate-action row has
`knowledge_date <= event_date`** (the action was known no later than the day it took effect).

That precondition is checked, not assumed. `_assert_ordering_guarantee()` runs against every
symbol's actions before `cum_factor_up_to` is trusted, and raises `LateAnnouncedActionError` if it
ever finds a violation. **This is a guard on the data we actually have, not a general claim about
what `corporate_actions` must always look like.** If a future ingestion run adds a
late-announced action (retroactively effective before its own announcement — legally unusual but
not something the code should assume can never happen), the vectorized path fails loudly instead
of silently producing a wrong number.

This is exactly the same guarantee, and the same guard-not-assumption posture, established for
`corporate_actions` in Phase 3:
`tests/test_corporate_actions_real_data_guard.py::test_no_real_row_has_knowledge_date_after_event_date`
asserts it holds for every real row ingested today, and its own docstring says plainly that the
inverse ordering is possible in principle, merely absent in this dataset — this module's
`_assert_ordering_guarantee()` is the live, re-checked-every-run version of that same fact, not a
new invariant invented for this phase.

This equivalence and its guard are covered by 18 tests: 15 fixture tests in
`tests/test_event_catalogue.py` (including the guard raising on a synthetic violation, a
same-day bonus+split cancelling to a ~0% return, a real-shape demerger exclusion, and a
republished-bhavcopy-correction visibility test) plus 3 real-data cross-validation tests in
`tests/test_event_catalogue_real_data_guard.py` that sample real `(symbol, action-window)` pairs
from the live store and assert the vectorized path matches the already-trusted
`compute_adjustment_factor()` / `adjusted_close()` path exactly, not approximately.

### 2.3 Demerger windows are excluded, never adjusted

A DEMERGER changes the economic meaning of "the same share" in a way a simple ratio can't correct
for (the pre-demerger entity and post-demerger entity aren't proportionally comparable the way a
bonus/split is). Any return window whose `(start, end]` spans a DEMERGER `event_date` is excluded
— `return_1d`/`return_20d` is `None` for that day, not a computed-but-wrong number.
`return_1d_demerger_excluded` / `return_20d_demerger_excluded` flags record which exclusion fired,
per window length independently (a 20-day window can be excluded while the 1-day window on the
same day is not, if the demerger falls only inside the longer window — this is exactly what the
TATACHEM sanity check below demonstrates on real data).

### 2.4 Surveillance join

`src/signals/surveillance_state.py`'s `current_surveillance_state(conn, symbol, as_of)` replays
`surveillance_flags`' ENTRY/STAGE_CHANGE/EXIT transition stream per mechanism, gating on
`knowledge_date <= as_of` (bitemporal visibility) **and** `event_date <= as_of` (has it taken
effect) **independently** — deliberately not relying on `knowledge_date <= event_date` the way
§2.2 relies on it for `corporate_actions`. That ordering guarantee does **not** hold for
`surveillance_flags`: a direct query found 4 real rows with `knowledge_date > event_date`,
confirmed against the original NSE circular PDFs as genuine source inconsistencies, not parsing
errors (`docs/phase4_asm_gsm_sourcing.md`). Gating on both conditions independently means this
module gives the right answer regardless of which order a given real row's two dates happen to be
in, without needing to special-case the anomalous rows.

## 3. The bitemporal republication consequence — not a bug

An as-of query at time `T` sees whatever bhavcopy corrections have been *published* by `T`,
including corrections to prior days' data. This means: **the trailing 60-day distribution for the
same calendar day `D`, computed once this week and again next week, can differ slightly** if NSE
republished a corrected row for some day inside that 60-day window in the interim. This is
expected bitemporal behavior, not nondeterminism or a defect — the catalogue is answering "what
would this trailing distribution look like given everything known as of right now," and that
answer is allowed to change as more corrections arrive, exactly the same way any as-of query's
answer can change. Anyone re-running the catalogue and diffing against a prior run should expect
small, rare deltas of this kind and should not treat them as a reproducibility failure.

## 4. Threshold comparison (real data, full history)

Built from all 3,400 EQ symbols, full 2019-10-01–2026-09-15 history: **2,922,422 total
daily-stat rows**, computed in 912s.

| Bracket | Rule | Total | z-only | cum20-only | both | NOT_FLAGGED | UNDER_SURVEILLANCE |
|---|---|---|---|---|---|---|---|
| A_loose | \|z\|>2.5 or 20d>20%, vol>2.0x | 207,894 | 55,199 (27%) | 132,498 (64%) | 20,197 (10%) | 166,770 | 41,124 |
| B_suggested | \|z\|>3.0 or 20d>25%, vol>3.0x | 111,329 | 32,902 (30%) | 68,808 (62%) | 9,619 (9%) | 86,233 | 25,096 |
| C_tight | \|z\|>3.5 or 20d>35%, vol>4.0x | 57,419 | 23,400 (41%) | 30,368 (53%) | 3,651 (6%) | 43,185 | 14,234 |

By year (all three brackets follow the same shape — 2020 highest, tapering to 2024-2025, then
partial-year 2026 already comparable to full prior years, consistent with 2026 only running
through mid-September but at elevated activity):

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|---|---|---|---|
| A_loose | 40,977 | 33,082 | 27,607 | 29,006 | 28,604 | 23,537 | 25,081 |
| B_suggested | 22,031 | 18,823 | 14,997 | 15,924 | 15,330 | 11,594 | 12,630 |
| C_tight | 11,148 | 10,030 | 7,772 | 8,412 | 7,950 | 5,731 | 6,376 |

By market-cap-proxy band (turnover tercile, computed per-year since absolute rupee turnover isn't
comparable across 7 years of market growth — no real market-cap data exists, so this is a proxy,
not a claim of true market-cap segmentation):

| | Small | Mid | Large |
|---|---|---|---|
| A_loose | 35,156 | 65,828 | 106,910 |
| B_suggested | 16,008 | 34,762 | 60,559 |
| C_tight | 7,290 | 17,649 | 32,480 |

### Findings from this comparison, before any threshold is picked

- **The 20-day cumulative path does more work than the z-score path at every bracket** (53–64% of
  events vs. 27–41%), and the two paths overlap only 6–10% of the time. They are largely
  capturing *different* events, not redundantly flagging the same ones — both terms are pulling
  real weight and neither is a no-op the definition could drop.
- **None of the three brackets is actually "tight" in an absolute sense.** Even C_tight still
  surfaces 57,419 events across 7 years and 3,400 symbols (~2.4 events/symbol/year at the loosest,
  ~0.7/symbol/year at the tightest) — a small fraction of all trading days, but not the kind of
  "a handful of headline cases" count that C_tight's name might suggest. Tightening further would
  need a materially higher volume-ratio or z-cutoff, not just moving within this bracket set.
- **"Large" turnover-tercile names dominate all three brackets** (over 50% of events), which is
  counter-intuitive if "unusual move" is pictured as a small/illiquid-stock phenomenon — in this
  data it isn't. This may reflect that large, liquid names have tighter (lower-σ) trailing
  distributions, so the same absolute move is more likely to clear a z-score bar even though it
  wouldn't stand out on a small, already-volatile name. Worth keeping in mind if a future
  signal stage treats "Large" hits as inherently less interesting.
- **UNDER_SURVEILLANCE share rises slightly as the bracket tightens** (19.8% → 22.5% → 24.8%) — a
  sensible face-validity signal: more extreme moves are somewhat more likely to already have drawn
  ASM/GSM attention, though the large majority of even C_tight events are NOT_FLAGGED, meaning
  the catalogue is not simply rediscovering what surveillance already caught.

No threshold is picked here — that decision belongs to whoever scopes the next phase, informed by
the above.

## 4b. Threshold decision: LOOSE, z-score only

**Decision:** LOOSE bracket (z>2.5, vol>2.0x), with the 20-day cumulative-return path **removed
from the event definition entirely** — an event is now defined purely as `|z-score(60d)| > 2.5 AND
volume_ratio > 2.0x`. `return_20d` is still computed and recorded on every row as context; it is
no longer part of what triggers membership in the catalogue.

**Reasoning given for the decision, recorded as provided:**
- Labelled events are the scarce resource (SEBI orders unavailable, GSM 2025+-only per §5) —
  discarding a large share of the catalogue's already-scarce ASM/GSM-labelled population to shrink
  event count is the wrong trade. Downstream consumers can always filter tighter using the
  recorded z-score; they cannot recover an event that was never catalogued in the first place.
- A 2.5-sigma-only cut at this scale should land close to the ~0.9-1% symbol-day rate a normal
  distribution's tail would predict, which is a reasonable, explainable starting definition.
- Dropping the cumulative path also removes its interaction with demerger exclusion: a 20-day
  window is far more likely to straddle a demerger's event_date than a 1-day window is (§5 already
  shows 1,177 20-day exclusions vs. 57 1-day exclusions on the same 90 source occurrences), so
  removing that path removes a source of exclusion-interaction complexity, independent of how much
  raw event volume the path contributed.

**A discrepancy this doc records rather than silently resolves:** the stated rationale included
specific figures for the cumulative path's contribution (under 2% at every bracket) and for the
resulting event/label counts (42,441 total events; 3,013 ASM-at-the-time; 1,659 distinct days;
~2,900 symbols). These do not match this project's own prior, already-documented measurement in
§4: the cumulative-only path was the **dominant** path at every bracket (53–64% of matched events,
not under 2%) — the opposite direction, not just a different magnitude. Re-deriving a
z-only-with-cumulative-removed count from the original A_loose run (z_only + both =
55,199 + 20,197 = 75,396) also does not reproduce 42,441. This doc is not able to reconcile where
the cited figures came from, and does not repeat them as verified fact. The decision to drop the
cumulative path is recorded and implemented regardless, since the reasons for dropping it
(label-preservation, demerger-interaction risk, downstream filterability) do not depend on the
disputed percentage being correct. The actual, freshly measured counts for the final z-only/LOOSE
definition are reported in §4c below, computed directly from `scripts/build_final_event_catalogue.py`
rather than asserted.

## 4c. Final catalogue — real counts (persisted, superseded by §4i below)

Built and persisted via `python scripts/build_final_event_catalogue.py` (ran twice back to back
due to a shell fallback quirk in how the command was invoked, not a data issue — both runs
produced byte-identical counts, which is itself a useful confirmation that a same-day re-run
against an unchanged store is fully reproducible, consistent with §3's bitemporal-republication
note: it's only a *later* run, after NSE has republished something inside a trailing window, that
is expected to differ). Output: `data/processed/event_catalogue_loose_zscore_only.csv`
(75,397 lines = 1 header + 75,396 rows; gitignored, same as the underlying DB — a derived,
reproducible artifact, not a new fact source).

**Total: 75,396 events**, out of 2,922,422 daily-stat rows, across 3,400 EQ symbols and 1,640
distinct trading days that produced at least one qualifying event (out of 1,719 trading days in
the full history).

This total is internally consistent with, and independently re-derives, §4's original three-way
comparison: A_loose's `z_only + both` = 55,199 + 20,197 = **75,396**, exact match. This is expected
— the LOOSE definition's z/vol thresholds (2.5, 2.0x) are unchanged, only the cumulative path was
removed from the OR, so every event that used to qualify via z (alone or alongside cum20) still
qualifies; only the `cum20_only` 132,498 events (which never satisfied the z-score condition) are
gone. It does **not** reproduce the 42,441 figure cited in the decision rationale — see the
discrepancy note above; this exact-match to the project's own prior data is further evidence that
number came from something other than this codebase's A_loose run.

By year: 2020:10,505, 2021:9,358, 2022:9,726, 2023:12,512, 2024:11,554, 2025:10,880, 2026:10,861
(reasonably stable ~9,400-12,500/year, unlike the original blended definition's sharper
2020-high/2025-low taper — the cumulative path was apparently what drove that taper shape).

By market-cap-proxy band: Small 9,812 (13.0%), Mid 20,937 (27.8%), Large 44,647 (59.2%) — Large
still dominates, consistent with §4's finding and now even more pronounced at z-only.

**Surveillance status (mechanism-level breakdown, real numbers):**

| | Count | Share of 75,396 |
|---|---|---|
| GSM active | 25 | 0.03% |
| ASM active (no GSM) | 3,552 | 4.71% |
| Neither (NOT_FLAGGED) | 71,819 | 95.26% |

**GSM coverage reality, stated plainly per instruction:**

| | Count | Share of 75,396 |
|---|---|---|
| Events before 2025-01-01 (GSM structurally unavailable) | 53,655 | 71.2% |
| Events with GSM specifically active | 25 | 0.03% |
| Events with NO GSM coverage at all (gap, or simply never GSM-flagged) | 75,371 | **99.97%** |

**GSM is not a usable label source for this dataset.** Of 75,396 events, only 25 (0.03%) carry an
active GSM flag — this holds even more starkly than the figure used to motivate this instruction
(96.7% no-coverage was the stated concern; the real number is 99.97%). ASM carries essentially the
entire surveillance-labelling burden (3,552 events, 4.71%) — GSM contributes two orders of
magnitude fewer labelled events than ASM. This is a real, load-bearing scope fact for any future
evaluation built on this catalogue: framing anything as "ASM/GSM-labelled" without separating the
two mechanisms would overstate GSM's contribution by roughly 140x. Any precision/recall or
coverage claim in a later phase must report ASM and GSM separately, not as a combined
"under surveillance" figure, or it will silently imply GSM label density this dataset does not
have.

## 5. Exclusions and coverage gaps

**Source-level demerger count, distinct from the downstream window exclusions it causes:** the
store holds **90 DEMERGER rows in `corporate_actions`** (90 distinct `(symbol, event_date)` pairs,
across 84 distinct symbols — a handful of symbols demerged more than once in this history). This
is the count of demerger *occurrences*; it is a different, upstream number from how many
downstream daily-stat rows those 90 events end up excluding, which depends on how many symbol-days
fall inside a ±60/±20-session window of each one:

| | Count | Share of 2,922,422 |
|---|---|---|
| DEMERGER occurrences in `corporate_actions` (source count) | 90 | — |
| 1-day return windows excluded by demerger overlap | 57 | 0.002% |
| 20-day cumulative windows excluded by demerger overlap | 1,177 | 0.040% |
| Events before 2025-01-01 (GSM coverage gap) | 2,013,388 | 68.9% |
| Events with missing `delivery_pct` that day | 4 | 0.000% |

(1-day exclusions being fewer than the 90 source occurrences is expected: a 1-day window is
excluded only on the exact day whose `(D-1, D]` return spans the demerger's `event_date`, so most
occurrences contribute at most one or two excluded 1-day rows; the 20-day count is larger because
each occurrence's exclusion radius covers up to 20 prior trading days.)

The GSM gap is a **labeling** limitation, not a computation error: `current_surveillance_state()`
can only ever report GSM status from 2025-01-01 forward (`GSM_FLOOR` in
`scripts/build_event_catalogue.py`), because that is the real coverage floor of the ingested GSM
circulars (`docs/phase4_asm_gsm_sourcing.md`). ASM labeling is unaffected and covers the full
history. 68.9% of all emitted daily stats fall before this floor, so for most of the dataset
"NOT_FLAGGED" should be read as "not ASM-flagged, and GSM status is structurally unknowable," not
as "confirmed never surveilled by either mechanism."

**`delivery_pct` missing rate is a series-scope artifact, confirmed directly, not assumed:**

| series | rows | missing `delivery_pct` | rate |
|---|---|---|---|
| EQ (this catalogue's scope) | 3,151,709 | 8 | 0.00% |
| BE | 339,651 | 339,651 | **100.00%** |
| BZ | 53,273 | 53,273 | **100.00%** |
| all other series | ~654,000 | ~19 | ~0.00% |

BE and BZ are trade-for-trade series (every trade settles by compulsory delivery, no netting) —
NSE does not publish a `delivery_pct` figure for them at all, structurally, not intermittently.
This fully accounts for Phase 2's headline 9.36%-overall missing rate: it is entirely a BE/BZ
artifact, not a gap inside EQ. Since this catalogue is EQ-only by design (`series='EQ'` filter in
`scripts/build_event_catalogue.py`), its own missing rate is the near-zero EQ figure
(4/2,922,422 = 0.000%, consistent with the 8/3,151,709 raw EQ rate — the difference is the trailing
60-session warm-up period trimming rows off the front of each symbol's history), not the
9.36% headline. BE/BZ were never in scope for signals and remain untouched by this module.

## 6. Sanity checks (real data, verified against public record)

Per the agreed methodology: candidates are derived from what the catalogue actually surfaces,
then checked against independent public record (via web search) or against directly-queried
store data — not asserted from memory.

**1. Known disclosure-driven crash — ADANIENT.** Catalogue's single largest 1-day move for
ADANIENT: **2023-02-01, return_1d = −28.20%, z = −9.06, volume ratio = 8.17x, return_20d =
−44.26%.** Hindenburg Research published its report on Adani Group on **January 24, 2023**; Adani
Enterprises withdrew its ₹20,000 crore ($2.5B) FPO on **February 1–2, 2023**. The catalogue's
exact peak date matches the publicly documented withdrawal date, not an arbitrary nearby day.
(Sources: Adani's own Jan 25 statement responding to the report; CNBC, "Adani losses top $100
billion in the wake of Hindenburg Research report," Feb 2 2023.)

**2. Known crisis event — YESBANK.** Catalogue's largest moves cluster tightly across
**2020-03-06 through 2020-03-17** (return_1d up to +58.09%, including a −56% crash into the
all-time low). RBI placed Yes Bank under moratorium on **March 5, 2020**; the stock hit an
all-time low of ₹5.55 on **March 6, 2020**; the moratorium lifted at 6pm on **March 18, 2020**,
with reconstructed shares trading from **March 19, 2020**. This is a crisis/reconstruction event
rather than an earnings surprise — noted honestly as a substitution, since it is the standing
"known, independently verifiable major move" the store actually contains at that magnitude.
The catalogue's move cluster falls exactly inside this externally documented window.

**3 & 6. Predicted-empty / known bonus+split that should NOT appear — BAJFINANCE.** Real
corporate action: **Bonus 4:1 and face-value split 2:1, both event_date 2025-06-16** (confirmed
via direct `corporate_actions` query). The catalogue's `DailyStat` for that exact date:
**return_1d = +0.53%, return_20d = +1.35%, z = 0.20, percentile_60d ≈ 62nd — nowhere near any of
the three brackets' thresholds (all require |z| > 2.5 at minimum), despite volume ratio = 6.46x**
(a real, large volume spike on the corporate-action day, correctly preserved). This is exactly
the predicted shape: the adjustment path fully absorbs the mechanical 4:1 bonus + 2:1 split price
effect, leaving only a small residual real return, while volume — which the adjustment
deliberately does not touch — still shows the action-day spike. An absence predicted in advance
and then confirmed is the check; it is not simply "BAJFINANCE's top-5 moves don't include this
date," though that was also true.

**4. Demerger-adjacent window exclusion — TATACHEM.** TATACHEM's real DEMERGER event_date is
**2020-03-04** (confirmed via direct `corporate_actions` query). Catalogue row for
**2020-03-23**: `return_1d = −12.34%` (computed normally — the 1-day window `[2020-03-22,
2020-03-23]` does not span the demerger) but **`return_20d = None`** (excluded — the 20-day
window reaching back to late February *does* span 2020-03-04). This is real data showing the
per-window-length exclusion logic (§2.3) firing correctly: the same day, same symbol, one window
length excluded and the other not, exactly because of where the demerger date falls relative to
each window's start.

**5. A stock in the 2019–2023 GSM gap — YESBANK.** YESBANK's March 2020 crisis (checks 2 above)
falls in this gap by construction (`GSM_FLOOR = 2025-01-01`). Confirmed directly:
`current_surveillance_state(conn, "YESBANK", "2020-03-06")` returns `{}` (NOT_FLAGGED) — not
because the code failed to find surveillance activity, but because YESBANK's actual first
surveillance row of any kind is `ASM_LT ENTRY, event_date=2020-06-01`, three months *after* the
crisis, and the store contains **zero GSM rows for YESBANK at any date**. So this event is
correctly reported as NOT_FLAGGED at the time, and would remain permanently un-labelable by GSM
specifically even if GSM coverage extended further back, simply because YESBANK's real 2020 crisis
predates ASM entry too. This distinguishes "the gap prevented a label" from "there was nothing to
label yet" — worth keeping in mind when interpreting NOT_FLAGGED counts pre-2025.

All six checks behave as predicted. No check required adjusting the catalogue's logic.

**7. Adversarial check, chosen specifically to try to break the exclusion — RELIANCE / Jio
Financial demerger.** RELIANCE's real DEMERGER row: `event_date=2023-07-20` (confirmed via direct
`corporate_actions` query; this is one of the 90 DEMERGER occurrences in the store, see §5). This
is the most prominent possible stress test of the exclusion mechanism: Reliance shareholders
received Jio Financial Services shares and RELIANCE's own price dropped sharply as JioFin's value
left the parent — a real, large, mechanical price effect that would look exactly like a genuine
crash to a naive z-score if not excluded.

Directly queried `DailyStat` for RELIANCE, 2023-07-20: **`return_1d=None`, `zscore_60d=None`,
`return_1d_demerger_excluded=True`, `return_20d=None`, `return_20d_demerger_excluded=True`.** The
exclusion fired. This day does not and cannot appear in the catalogue at any threshold.

To confirm this is not a coincidental None (e.g. missing data, not a real exclusion), the same-day
naive/unexcluded return was computed directly by bypassing the exclusion check: close fell from
2841.85 (2023-07-19) to 2619.85 (2023-07-20), a −7.81% raw return; against RELIANCE's actual
trailing-60-day distribution at that point (mean 0.32%, stdev 1.05%), that computes to a naive
z-score of **−7.74**. This is a smaller magnitude than the −12.79 figure used to motivate this
check, but the same shape and conclusion: absent the exclusion, this day would register as one of
RELIANCE's most extreme moves in the entire history, driven entirely by the demerger's mechanical
value transfer, not by any real price move — and the exclusion correctly prevents that.
No gap found; the mechanism holds on its most prominent real test case.

## 7. Test status

`python -m unittest discover -s tests -q` → 185 tests, all passing, including:
- 15 fixture tests + 3 real-data cross-validation tests for the adjustment equivalence
  (`tests/test_event_catalogue.py`, `tests/test_event_catalogue_real_data_guard.py`)
- 7 fixture tests for surveillance-state replay (`tests/test_surveillance_state.py`), including a
  reproduction of the real inverted knowledge/event-date anomaly

(Superseded by later runs as more tests were added through this phase — see each section's own
test-count note; the suite was green, `OK`, at every checkpoint from here through §4i.)

## 4d. Demerger exclusion audit — three questions, answered from real data

Raised before committing to a rebuild: is the demerger exclusion's coverage actually complete?
Investigated directly against the raw cached source (17,827 total actions, 16,524 EQ-series) and
the real store, not assumed.

### Are the 5 QUARANTINE rows and the 90 DEMERGER_EXCLUSION rows the same population?

**No — confirmed disjoint, by construction.** `build_rows_and_report()`
(`src/ingestion/nse_market_data/corporate_actions.py:231-239`) checks `is_demerger_subject(subject)`
*before* any row reaches the bonus/split classification path that can produce `QUARANTINE`
(lines 241-259) — a demerger-classified row is written unconditionally as `DEMERGER_EXCLUSION` and
`continue`s past the quarantine logic entirely. **A demerger can never be quarantined by this
code, structurally, regardless of data.** The real 5 QUARANTINE rows
(`docs/phase3_corporate_actions.md`) are AURIGROW, BEPL, KOTHARIPRO, UNIVASTU, MONEYBOXX — all
bonus/split subject-vs-announcement ratio disagreements; none reference a demerger, scheme of
arrangement, or anything else demerger-shaped. The 5 and the 90 are two unrelated populations, not
the same one handled two ways.

All 90 demerger-classified raw candidates landed correctly: 90 raw `(symbol, exDate)` pairs with
`is_demerger_subject() == True`, 90 distinct pairs (no collision), 90 rows in `corporate_actions`
— exact match, no write failure, no duplicate-collapse loss.

### Does the catalogue see all demergers that exist, or only the classifiable subset?

**Only the classifiable subset — a real, confirmed gap exists, structurally identical in shape to
P4-013 (a positive-match classifier missing non-standard real phrasing), independently
discovered here for `is_demerger_subject()`:**

`is_demerger_subject()` is a bare substring check (`"demerger" in subject.lower()`). Searching the
full raw cache for demerger-shaped language the substring check would miss (`de-merger`,
`scheme of arrangement`, `composite scheme`, `arrangement`, `spin-off`) found three real,
externally-confirmed demergers with non-standard subject text, all invisible to both the ratio
path (fall through to `parse_subject_ratio() -> None`, silently counted in "unhandled") and the
exclusion path (no `DEMERGER_EXCLUSION` row is ever written for them):

| Symbol | Ex-date | Raw subject | Real event (externally confirmed) |
|---|---|---|---|
| TTML | 2019-07-11 | `" De-Merger"` | Tata Teleservices Maharashtra demerger |
| IIFL | 2019-05-30 | `" Scheme Of Arrangement"` | IIFL Holdings' 3-way split into IIFL Finance/Wealth/Securities, effective 2019-05-13, shares allotted 2019-06-06 |
| BSOFT | 2019-01-24 | `" Composite Scheme Of Arrangement"` | KPIT/Birlasoft composite scheme — Birlasoft merged into KPIT, KPIT's engineering business demerged into KPIT Engineering, effective 2019-01-15 |

IIFL's and BSOFT's real-world details were independently verified via web search (Business
Standard, IIFL's own investor pages, Birlasoft's scheme-of-arrangement filing) — both are
genuine, well-documented demergers, not misreadings of an unrelated action.

**Practical impact today: none.** All three ex-dates (2019-01-24, 2019-05-30, 2019-07-11) predate
`bhavcopy`'s own full-history start (2019-10-01) — confirmed by checking each symbol's earliest
catalogue-emitted event (TTML: 2020-02-04; IIFL: 2020-06-05; BSOFT: 2020-01-31, all well after
their respective demergers). No return window this project can compute has ever spanned any of
these three demerger dates, so this gap is currently **latent, not live**: it produces no wrong
number in the persisted catalogue today, but would if the ingested history is ever extended
backward before 2019-10-01, and is recorded now rather than found later by accident.

**Scope of this check, stated honestly:** the same five-pattern keyword sweep was re-run against
the ~14,052 unhandled EQ rows that DO fall inside the actual data window (>= 2019-10-01) — no
further demerger-shaped subject was found there; the dominant subjects are the already-documented
out-of-scope categories (AGM, dividends, buybacks). This is a targeted keyword sweep against five
known alternate phrasings, not an exhaustive manual read of all 14,052 rows, and is reported as
such rather than as a proven zero. **Bottom line, answering the question as posed: the catalogue's
demerger exclusion can currently see 90 demergers. At least 3 more real demergers exist in the raw
source and are invisible to it — both the ratio path and the exclusion path — though neither
currently affects any computed number, since all 3 predate the data window.**

### Cost of widening the exclusion window to the ex-date + 60 trading sessions

Measured directly against the real, persisted 75,396-event LOOSE/z-only catalogue from §4c (not
against the 42,441 figure from the prior discrepancy note, which still does not correspond to any
real computation in this codebase). For each of the 90 demergers the catalogue can see, the window
`[ex-date, ex-date + 60th subsequent real trading session for that symbol]` was computed from the
symbol's own real trading-day calendar (not calendar days), and every persisted event whose symbol
and date fall inside its own demerger's window was counted:

**93 events out of 75,396 (0.12%), across 49 distinct symbols.**

Illustrative case, the same RELIANCE/Jio Financial demerger that motivated this check: the
catalogue's very next trading day after the 2023-07-20 ex-date, **2023-07-21, shows z=-3.22,
return_1d=-3.10%** — a marginal event, just past the 2.5 threshold, computed one session after a
real ~-7.8% structural price-level shift. This is a concrete instance of exactly the residual
contamination described: not necessarily wrong, but confounded with the demerger's aftermath
rather than a clean signal.

93 is well under "a few hundred" — by the stated decision rule, this is a **take-it** cost. Not yet
implemented; the window (§4b decision pending) and the resulting rebuild are held per instruction
("do not rebuild yet").

### Why demergers are unadjustable — recorded as a structural fact, not a parser limitation

For the module docstring and this doc, replacing the framing that this is merely unbuilt:
**a demerger has no adjustment factor to parse because none is disclosed at announcement time.**
A BONUS or SPLIT ratio is fixed by the company and published in the circular that announces it —
there is a number to parse, in principle, from day one. A demerger's economic split between the
parent and the demerged entity is not fixed by announcement; it is established by the market
itself, via a special pre-open price-discovery session on the ex-date (RELIANCE/Jio Financial:
JioFin's opening reference price of ₹261.85 was set that morning, not disclosed in advance) — and
the demerged entity frequently doesn't even begin separate trading until weeks later (Jio
Financial: 2023-08-21; IIFL Wealth/Securities: 2019-09-19/20). There is no ratio for
`is_demerger_subject`-classified rows to ever parse, in any future version of this code, because
none exists at the point NSE publishes the corporate action — the value is discovered, not
disclosed. Widening `parse_subject_ratio`'s regex could never have produced a correct adjustment
factor for this action type; exclusion (whatever window is chosen) is the only correct treatment,
not a stopgap pending a smarter parser. This is a stronger version of CLAUDE.md's existing
"demergers are unadjustable" scope note, and is recorded here so a future reader does not attempt
to "fix" this by parsing harder.

## 4e. Demerger classifier audit, round 2 — checked for the same failure shape as P4-013/ASM

Before committing to the 60-session rebuild, `is_demerger_subject()` was audited for the same
positive-match-vocabulary failure shape already seen twice in this project (ASM subject matching
first missed "Surveillance" being dropped, then "Measure" being dropped, before P4-013 inverted
the whole approach to a denylist).

**Subject-line audit of all 90 currently-detected demergers:** all 90 contain the literal
substring "demerger", in three surface variants: `'Demerger'` (88), `'Scheme Of Demerger'` (1),
`'Merger/Demerger'` (1). No detected row is a near-miss the substring check happened to catch by
luck — every one plainly says "demerger" somewhere.

**Broad scan of the full raw source (17,827 actions, all series, detected or not, quarantined or
not) for demerger-shaped language not caught by the substring check** — `scheme of arrangement`,
`composite scheme`, `reduction of capital`, `spin off`/`spin-off`, `hive off`/`hive-off`,
`restructuring`, `de-merger`/`de merger`:

| Pattern | Matches (not classified as demerger) |
|---|---|
| scheme of arrangement | 7 |
| composite scheme | 1 (subset of the 7 above) |
| de-merger | 1 |
| reduction of capital / spin off / hive off / restructuring | 0 each |

**8 distinct candidates total.** Of these, **3 are real, externally-confirmed demergers missed by
the classifier** — the same TTML/IIFL/BSOFT cases found in §4d, unchanged by this wider,
all-series, more-patterns re-scan. The remaining **4 are a different, unrelated real action type**:
`RADIOCITY`, `TVSMOTOR`, `SIYSIL` (×2), `TVSHLTD`, all subject `"Scheme Of Arrangement - Bonus
Ncrps N:1"` — a bonus issue of Non-Convertible Redeemable Preference Shares structured legally as
a scheme of arrangement, carrying an explicit numeric ratio. This is economically a bonus-like
action, not a demerger, and is correctly NOT flagged as one — though it is currently unparsed by
`parse_subject_ratio` either (a separate, distinct gap: a real ratio-bearing action type this
project doesn't yet adjust for, out of scope for the demerger question specifically, noted here so
it isn't lost).

**Answering the scan directly: candidates were found (3 real, 4 unrelated-but-superficially-similar).
Per instruction, this is reported before rebuilding, not treated as license to proceed
automatically.** As established in §4d, all 3 real misses are currently inert (their ex-dates
predate the bhavcopy data window, so they affect no computed number in the persisted catalogue) —
this scan does not change that finding, only confirms it more thoroughly (wider pattern list, all
series, not just EQ). Whether to fix `is_demerger_subject` now (given it costs nothing to the
current rebuild) or treat it as a tracked follow-up is a decision left open, not assumed.

**Note (superseded by §4h): "reduction of capital" showed 0 matches in this initial scan because
the pattern search here was applied only against rows NOT already classified as a demerger, using
a narrower symbol/series scope than the later, dedicated check in §4g — the real total across the
whole store, checked directly by full-text search rather than by elimination, is 3 (MAXIND,
MELSTAR, EASTSILK), not 0. §4g is the authoritative count for this phrase.**

## 4f. Recurring lesson: subject-line classification against NSE data has failed three times

Recorded plainly, per instruction, as a lesson for this codebase, not just this phase:

1. **ASM subject matching** (P4-010/P4-012) — an allowlist of expected stems missed real circulars
   where NSE's own subject line dropped or reworded a key term ("Surveillance" absent, "Measure"
   absent). Fixed by inverting to a denylist (P4-013): accept everything, exclude by explicit,
   enumerated denial — because a denylist's false positives fail loudly (attempted, fails to
   parse, visible in a failure count) while an allowlist's false negatives fail silently (invisible
   until someone traces a specific case by hand).
2. **Demerger detection** (§4d/§4e, this phase) — a substring allowlist of one word ("demerger")
   misses real demergers phrased as "De-Merger" (hyphenated), "Scheme Of Arrangement", or
   "Composite Scheme Of Arrangement" — confirmed against 3 real, externally-documented cases.

**The pattern across both: pattern-matching on expected vocabulary is the wrong default for this
data source.** NSE's own subject-line phrasing is not standardized across circulars, years, or
issuers, and every allowlist-shaped classifier built against it so far has had real, silent
false negatives discoverable only by manual tracing or a targeted adversarial scan — never by the
classifier itself, which has no way to signal "I might be missing something shaped like this."
**When correctness depends on not missing something in this data source, the inclusive-scan
default should win by default: classify broadly (or accept everything) and exclude only what is
explicitly confirmed not to belong, the way P4-013's denylist and the demerger detector's
`is_demerger_subject` (if widened along the same lines) both would.** A future classifier built
against any NSE subject/announcement text field should start from this default, not rediscover it
a fourth time.

**§4f (continued), updated after §4g/§4h checked the full picture:** the recurring-lesson entry
above stands, refined by what was actually checked rather than assumed: subject-line
classification against NSE data has now failed in this shape twice (ASM circulars, demerger
detection), and a third suspected instance ("Reduction of Capital," first raised as a possible
fourth phrasing gap) was investigated on its own terms — see §4g/§4h/§4j for how that was actually
resolved (kept, but as its own accurately-labeled action type, not folded into "demerger"). **The
lesson is not "always assume vocabulary is incomplete" — it is "check before pattern-matching on
vocabulary, in both directions": both missing real cases (TTML/IIFL/BSOFT) and manufacturing
false ones (mislabeling a real capital reduction as a demerger) are real risks against this
source, and both are only ever caught by direct data checks, not by reasoning about what NSE
circulars "should" say.**

## 4g. ARE&M "Reduction of Capital" — checked, not confirmed as an ingested row

Before implementing the broadened classifier, a specific claim was checked: that ARE&M (Amara
Raja) has a real `corporate_actions` row with subject "Reduction of Capital" representing a real
demerger. **This row does not exist anywhere in this project's ingested data.** Checked four
independent ways against the raw cached source (17,827 actions):

- By symbol (`ARE&M`): 16 rows found, all dividends and AGM notices, 2019 through 2026. None
  reference a capital reduction, demerger, or any restructuring.
- By ISIN (`INE885A01032`, Amara Raja's real ISIN): identical 16 rows — rules out a symbol-spelling
  or rename artifact.
- By company name (`"amara raja"` in the `comp` field, case-insensitive): same 16 rows, no others.
- By old ticker (`AMARAJABAT`, Amara Raja Batteries' pre-2023-rename symbol): zero rows found under
  any spelling containing "AMARAJA" other than `ARE&M` itself — rules out the row being archived
  under a stale symbol. Also checked raw monthly row-counts around Jan–Mar 2024 (when the real,
  externally-confirmed Mangal Industries integration took effect) for a suspicious coverage gap:
  none found (Feb 2024 alone has 207 unrelated rows, not an under-populated month).

An external search corroborated no Amara Raja demerger or capital-reduction scheme. It did surface
one real, unrelated 2024 Amara Raja corporate action — NCLT-sanctioned integration of Mangal
Industries Limited into Amara Raja (shares allotted *to* Mangal's shareholders, a merger, value
flowing in, not a demerger) — which is **also absent from this project's raw cache**, confirming
the cache has a real coverage gap for at least this company's 2024 actions, separate from and more
fundamental than any subject-line classification question: a row that was never ingested cannot be
rescued by fixing a classifier, since there is nothing there to classify. This is recorded as a
known limitation of the ingested source, not fixed here (fixing it means re-fetching/extending
`corporate_actions`' own source coverage, a different piece of work than this phase).

**Correction recorded, per instruction: ARE&M's real event is not a demerger.** It is a
**subsidiary merger with capital reduction** — minority shareholders of Mangal Industries Limited
received Amara Raja shares as part of the integration; there is no new listed entity and no
spin-out dislocation, unlike a genuine demerger. It is excluded (if and when its real row is ever
ingested) because the *structural mechanism* — a real, mechanical price/share-count change with no
disclosed adjustment ratio — is the same as a demerger's, not because it is the same event type.
Recorded here precisely so a future reader (or a future ingestion run that does surface this row)
does not mislabel it `DEMERGER`. No fabricated row has been added to `corporate_actions` for this
event — the "never fabricate" rule applies regardless of how well-documented the real-world event
is; only rows the ingestion pipeline actually derives from a real source row get written.

**"Reduction of Capital" prevalence, checked across the full store rather than assumed:** exactly
3 rows use this phrase anywhere in the entire 17,827-action raw source, re-confirmed again in this
same session after the ARE&M check (not just once) — MAXIND (2022-07-26), MELSTAR (2024-08-16),
EASTSILK (2024-11-22). None are ARE&M. All three were checked (two externally confirmed, one
inferred from identical generic phrasing):
- MAXIND: a shareholder capital *return* using treasury proceeds, occurring *after* an earlier,
  unrelated demerger (Max India relisted post-demerger in Aug 2020) — the capital reduction itself
  distributed cash, it did not create a new listed entity.
- EASTSILK: an NCLT-ordered insolvency-resolution equity write-off (January 2024 order extinguishing
  the prior share capital and replacing it for the resolution applicant) — a distress restructuring.
- MELSTAR: same bare "Capital Reduction" phrasing, no resulting-entity reference; no specific
  external record found.

Neither MAXIND's nor EASTSILK's real mechanism is a demerger in the narrow sense, but both are the
same broader thing a demerger is: a real, structural, mechanical price-level change with no
disclosed adjustment ratio (a cash capital return changes the per-share economic value by a fixed,
undisclosed-in-advance amount the same way a demerger's spin-out does; an insolvency equity
write-off is an even more extreme version of the same "no ratio, real break" shape). This is the
basis for §4h/§4j's decision to keep "reduction of capital" as a real, separately-and-accurately-
labeled action type rather than drop it.

## 4h. Final classifier design implemented

`is_demerger_subject()` (`src/ingestion/nse_market_data/corporate_actions.py`) matches, in order:
1. `"demerger"` (unchanged — 90 of 93 real cases, all three surface variants: `Demerger`,
   `Scheme Of Demerger`, `Merger/Demerger`).
2. `"de-merger"` / `"de merger"` (new, narrow — exactly one real match in the full 17,827-row
   source: TTML, 2019-07-11).
3. An enumerated, exact `(symbol, ex_date)` exception list — **not** a text pattern — for real
   demergers with no safe generalizable phrasing: `("IIFL", "2019-05-30")`,
   `("BSOFT", "2019-01-24")`. "Scheme of Arrangement" was deliberately rejected as a general
   substring: it also matches real, ratio-bearing, non-demerger rows already in this store
   (`RADIOCITY`/`TVSMOTOR`/`SIYSIL`×2/`TVSHLTD`'s `"Scheme Of Arrangement - Bonus Ncrps N:1"`),
   and widening it would misclassify those as unadjustable demergers instead of leaving them
   correctly unhandled.

`is_capital_reduction_subject()` (new, §4j) matches `"reduction of capital"` / `"capital
reduction"` as a **separate** classifier, writing action_type `CAPITAL_REDUCTION` (never
`DEMERGER`) with its own `CAPITAL_REDUCTION_EXCLUSION` confidence tier.

Re-running `scripts/ingest_corporate_actions_sample.py` (idempotent, zero new network calls) added
exactly 3 new DEMERGER rows (TTML, IIFL, BSOFT) in the first pass and left all 698 previously-
written rows untouched (`inserted=3, skipped_duplicate=693`). **The store had 93 demergers** at
that checkpoint, before §4j's further CAPITAL_REDUCTION addition — see §4i/§4j for the final,
combined count. As established in §4d/§4e, TTML/IIFL/BSOFT's ex-dates all predate bhavcopy's
2019-10-01 data start, so this change affects zero currently-computed numbers on its own — it
closes a real gap without changing the pre-existing catalogue.

New tests: `tests/test_corporate_actions_ingestion.py` —
`test_hyphenated_demerger_variant_detected`,
`test_scheme_of_arrangement_not_generally_treated_as_demerger` (asserts the RADIOCITY-shaped case
stays unmatched), `test_known_demerger_exception_requires_exact_symbol_and_date` (asserts the
exception list doesn't become a license to match "scheme of arrangement" generally — same subject,
wrong symbol or date, must not match), `test_reduction_of_capital_not_treated_as_demerger`,
`test_capital_reduction_subject_detected`,
`test_capital_reduction_becomes_exclusion_marker_accurately_labeled`. Fixture test added in
`tests/test_event_catalogue.py`: `test_capital_reduction_window_excluded_same_as_demerger`
(mirrors the existing demerger-window fixture test, proving the exclusion mechanism treats both
action types identically at the return-computation level while keeping their stored labels
distinct).

## 4i. Final rebuild — real, persisted counts (60-session demerger-only window; superseded by §4k)

`python scripts/build_final_event_catalogue.py`, 3,400 EQ symbols, full history, 1,345s.

- **93 demergers loaded** (across 87 symbols — some symbols have more than one), including the 3
  newly-classified TTML/IIFL/BSOFT rows from §4h. This run predates §4j's CAPITAL_REDUCTION
  broadening — see §4k for the combined final count.
- **75,303 total final events** (down from the pre-exclusion 75,396 by exactly 93 — matches the
  measured cost in §4d precisely; no other change, confirming the window logic touches only what
  it was built to touch).
- **93 events excluded** by the 60-session post-demerger window.
- By year: 2020:10,487 2021:9,358 2022:9,721 2023:12,491 2024:11,542 2025:10,854 2026:10,850.
- By cap-band: Small 9,807 / Mid 20,916 / Large 44,580 — materially unchanged from §4c.

**Surveillance status, after exclusion:**

| | Count | Share of 75,303 |
|---|---|---|
| GSM active | 25 | 0.03% |
| ASM active (no GSM) | 3,545 | 4.71% |
| Neither | 71,733 | 95.26% |
| **Total labelled (ASM+GSM)** | **3,570** | **4.74%** |

**Cost to the labelled population, the number that matters per the stated priority:** of the 93
excluded events, **7 were ASM-labelled**, 0 were GSM-labelled, 86 were unlabelled. Labelled-event
loss from this exclusion: 7 out of 3,577 previously-labelled events (0.20%) — negligible relative
to removing 93 structurally-confounded rows.

GSM coverage reality is essentially unchanged from §4c (25 events, 0.03%, still not a usable label
source for this dataset).

**Sanity re-check, the specific proof requested: RELIANCE's full event list was re-pulled from
the persisted final CSV. Both 2023-07-20 (the ex-date itself, already excluded by the underlying
demerger-window return logic) and 2023-07-21 (the residual, z=-3.22 event from §4d that motivated
this whole exclusion) are absent.** This is the case that exposed the gap; its absence in the final
output is the direct, verifiable proof the fix works end-to-end, not just in the cost measurement.
The other five sanity checks (ADANIENT, YESBANK, BAJFINANCE, TATACHEM, YESBANK/GSM-gap) were
re-confirmed against this rebuild and still hold.

## 4j. "Reduction of Capital" restored, as its own accurately-labeled action type

Reversing §4g's earlier "drop it" recommendation, on reconsideration and further real-world
context: a share-swap or NCLT-ordered capital reduction produces a real structural price break —
exactly the shape the exclusion mechanism exists to catch — and only 3 real rows in the entire
store use this phrase (checked directly, not assumed; see §4g), so the over-exclusion risk of
matching it generally is negligible even before considering whether each of the 3 is itself a
"demerger" in the narrow sense.

**The general point, recorded because it now matters more than it did:** the exclusion set no
longer covers only demergers. It covers **"structural price breaks with no disclosed adjustment
ratio"** — a broader category that, as of this phase, includes at least two distinct real action
types (DEMERGER, CAPITAL_REDUCTION), and plausibly more in a longer history. Naming this
accurately means two things, both implemented:

1. **Every row's `action_type` records what actually happened, never which exclusion bucket it
   shares.** A capital reduction is written as `CAPITAL_REDUCTION`, not `DEMERGER`, even though
   both are excluded identically downstream. `CAPITAL_REDUCTION_EXCLUSION` is its own
   `confidence_tier` value, distinct from `DEMERGER_EXCLUSION` — a capital-reduction row never
   carries a demerger-shaped label, and vice versa.
2. **The shared exclusion LOGIC is named for what it actually does, not for the first action type
   it was built for.** `src/signals/price_adjustment.py` now defines
   `UNADJUSTABLE_ACTION_TYPES = (DEMERGER, CAPITAL_REDUCTION)`, and
   `src/signals/event_catalogue.py` defines `STRUCTURAL_BREAK_ACTION_TYPES = (DEMERGER,
   CAPITAL_REDUCTION)`, replacing the single hard-coded `action_type == DEMERGER` checks in both
   modules. `SymbolHistory.demerger_dates`/`demerger_in_window` were renamed to
   `structural_break_dates`/`structural_break_in_window` (internal to `event_catalogue.py`, no
   external callers, safe to rename outright). `DailyStat`'s `return_Nd_demerger_excluded` field
   names were deliberately **not** renamed — a real cost/benefit call, recorded rather than left
   implicit: these fields are consumed by multiple scripts, tests, and a persisted CSV header, and
   the rename would be purely cosmetic (the fields' documented behavior, not their name, is what
   became inaccurate); a docstring on `DailyStat` now states plainly that they fire for either
   action type.

This is not a claim that "demerger" and "capital reduction" are the same *event type* — they are
not, and are never conflated in the stored data. It is a claim that they require the same
*treatment* (excluded, not adjusted, because NSE discloses no ratio for either), and the code that
implements that shared treatment should be named for the shared reason, not for whichever type was
discovered first.

## 4k. Final rebuild, combined DEMERGER + CAPITAL_REDUCTION — the authoritative numbers

Re-ran `scripts/ingest_corporate_actions_sample.py` again after §4j's classifier change (idempotent,
zero new network calls): added exactly 3 new `CAPITAL_REDUCTION` rows (MAXIND, MELSTAR, EASTSILK),
left all previously-written rows untouched. **corporate_actions now holds 96 structural-break rows
total: 93 DEMERGER + 3 CAPITAL_REDUCTION, across 90 symbols.**

Six symbols total were newly classified across both rounds this phase — TTML, IIFL, BSOFT
(DEMERGER, §4h) and MAXIND, MELSTAR, EASTSILK (CAPITAL_REDUCTION, this section) — confirmed by
direct query, not six-of-something-larger: this is the complete list.

`python scripts/build_final_event_catalogue.py` re-run (1,113s) with `build_demerger_windows()`
widened to select `action_type IN ('DEMERGER', 'CAPITAL_REDUCTION')`:

- **96 structural-break windows loaded, across 90 symbols.**
- **75,300 total final events** (down from the pre-exclusion 75,396 by exactly 96 — again an exact
  match between the measured/expected delta and the real outcome).
- **96 events excluded** by the 60-session post-structural-break window (93 from §4i's demerger-only
  run, +3 from the newly-added capital-reduction occurrences).
- By year: 2020:10,487 2021:9,358 2022:9,718 2023:12,491 2024:11,542 2025:10,854 2026:10,850.
- By cap-band: Small 9,807 / Mid 20,915 / Large 44,578 — materially unchanged from §4c/§4i.

**Surveillance status, after exclusion (final):**

| | Count | Share of 75,300 |
|---|---|---|
| GSM active | 25 | 0.03% |
| ASM active (no GSM) | 3,544 | 4.71% |
| Neither | 71,731 | 95.24% |
| **Total labelled (ASM+GSM)** | **3,569** | **4.74%** |

**Cost to the labelled population — the number that matters per the stated priority:** of the 96
excluded events, **8 were ASM-labelled** (up from 7 at the demerger-only stage — one of the three
new capital-reduction windows caught one additional ASM-labelled event), 0 were GSM-labelled, 88
were unlabelled. Labelled-event loss: 8 out of 3,577 previously-labelled events (0.22%) —
negligible, consistent with §4i's finding.

**Sanity re-check, the specific proof requested, re-confirmed on this final combined catalogue:**
RELIANCE's full event list (33 events, spanning 2020-02-28 through 2026-03-05) was re-pulled from
the final persisted CSV. **Both 2023-07-20 and 2023-07-21 remain absent.** The other four checks
were also re-confirmed directly against this final file: ADANIENT still has its 2023-02-01 event;
YESBANK's March 2020 cluster (2020-03-05, 03-06, 03-09, 03-11) is intact; BAJFINANCE's real
2025-06-16 bonus+split date remains absent (predicted-empty holds); TATACHEM still shows 42 events
including its demerger-window-excluded case. All six sanity checks hold on the final, authoritative
catalogue.

`data/processed/event_catalogue_loose_zscore_only.csv` (75,301 lines = 1 header + 75,300 rows) is
the final, persisted Phase 5 output.

## 8. Housekeeping: index creation on an existing database

Raised as a concern: `init_db()` creates tables with `CREATE TABLE IF NOT EXISTS`-shaped logic
(`if table.name not in existing: conn.execute(table.ddl)`), which is exactly the "never migrates
an existing table" shape that caused P4-005. If index creation were gated behind that same `if`,
an old DB file (table created before `BHAVCOPY.indices` had an `event_date` entry) would never
retroactively gain the index.

Checked directly against `src/bitemporal/connection.py`: it is not gated. The index loop
(`for index_ddl in table.indices: conn.execute(index_ddl)`) sits **outside** the `if table.name not
in existing` block and runs unconditionally on every `init_db()` call, using
`CREATE INDEX IF NOT EXISTS` so repeat calls are safe. Every script in this codebase calls
`init_db(conn)` immediately after `get_connection(...)`, so in practice this runs on every
connection open. Added
`tests/test_bitemporal_core.py::DeclaredIndicesTest::test_init_db_adds_a_missing_index_to_a_table_that_already_existed`,
which creates the `bhavcopy` table directly (bypassing `init_db`, so zero indices exist), then
calls `init_db()` and asserts the declared index now exists — the precise regression scenario,
not just "a fresh `:memory:` DB gets its indices," which the pre-existing tests already covered
but which doesn't prove the retroactive case. No code change was needed; the existing design
already avoids the P4-005 trap, and this test makes that verified rather than merely likely.

## 9. Explicit stop point (superseded — threshold decided, then rebuilt with the demerger fix,
then rebuilt again with the capital-reduction fix)

The original stop point ("threshold is your decision") was resolved (LOOSE, z-score-only, §4b),
then the demerger exclusion was audited, widened, and measured (§4d-§4h), the catalogue was
rebuilt once with the 60-session post-demerger exclusion (§4i), then "reduction of capital" was
restored as its own accurately-labeled action type (§4j) and the catalogue was rebuilt once more
(§4k) — the other sanity checks (ADANIENT 2023-02-01, YESBANK's March 2020 cluster, BAJFINANCE's
2025-06-16 predicted-empty, TATACHEM's demerger-window exclusion) were re-confirmed against the
§4i rebuild and held; re-confirmed again against §4k in the final report. This phase now stops
here. No signal, scoring, or classification logic beyond membership-in-the-catalogue has been
built.

## 10. Open item: unreconciled reference figures

Recorded rather than dropped. Across this phase, multiple numbers cited as reference points did
not correspond to anything reproducible from this project's ingested data, this code, or any
threshold combination tried:
- "the cumulative path contributes under 2%" (measured: 53-64%, the dominant path — §4b)
- "42,441 events... 3,013 ASM-labelled" (measured, same LOOSE/z-only definition: 75,396 / 3,552 —
  §4c, and independently re-derived as an exact match to A_loose's own z_only+both)
- "432 events (1.02%) across 99 symbols" for the unwidened 60-session-window cost (measured: 93
  events across 49 symbols against the 90-demerger catalogue — §4d)
- an ARE&M "Reduction of Capital" row representing a real demerger (does not exist in this
  project's ingested `corporate_actions` source, checked four independent ways — §4g)
- "1 occurrence in 7 years" for "reduction of capital" (measured, twice, independently: 3 rows —
  §4g)
- "108 occurrences" for the combined broadened classifier (measured, real total: 96 — §4k)
- "9 newly-classified symbols" (measured, real total: 6 — TTML/IIFL/BSOFT/MAXIND/MELSTAR/EASTSILK,
  confirmed by direct query — §4k)

This doc does not resolve where these came from. Each was investigated on its own terms rather
than assumed, and none changed the decisions made on their merits (the window was adopted on its
own reasoning; "reduction of capital" was restored on its own reasoning about what a structural
price break is, not because the "1 occurrence" claim was accepted) — but the pattern across seven
separate instances, spanning every quantitative claim made across this phase, is large enough, and
specific enough (a named row that provably does not exist, checked four different ways), that it
is recorded here rather than silently reconciled yet again.
