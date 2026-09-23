# Amendment 4 Prep — Measure, Fix, Rebuild, Refit, Draft

Covers all three parts of the instruction in order. Part 1 is read-only measurement against the
PRE-correction data (deliberately — it is what justified the Part 2/3 decisions, not something to
re-run circularly against data those decisions already changed). Part 2 is code, tests first,
committed separately from Part 1's measurement scripts. Part 3 promotes corrected data into
production for the first time this corrections-session family of work, applies the equity-only
rule for real, rebuilds the full pipeline, and refits. **The actual pre-registration amendment
(`docs/phase10_preregistration_amendment4.md`) is drafted but NOT committed — reviewed first, per
instruction.**

## Summary (read this first)

**Part 1, item 1:** inverting the ISIN map found **195 ISINs mapping to more than one symbol**
(398 symbols, all with real trading history) — not just the one `HEG`/`HEGAM` case `P8-010`
already knew about. 19 of those renames have at least one corporate action "orphaned" (ex-date
inside one member's own trading window, filed under a sibling symbol) — 26 orphaned actions total.

**Item 2:** checking the P8-007 corrections' 52 persisting "unexplained" shape-scan hits against
each event's ISIN siblings' own action history explains **4 more**: `COSMOFILMS`/`COSMOFIRST`,
`INFIBEAM`/`CCAVENUE`, `MINDAIND`/`UNOMINDA`, `NXTDIGITAL`/`NDLVENTURE` — each a real `BONUS` or
`DEMERGER` filed under the post-rename symbol, exactly explaining the pre-rename symbol's
apparently-unexplained shape. 48 remain genuinely unexplained.

**Item 3, the load-bearing finding:** among catalogued events whose 90-session window has fully
elapsed, **TRAIN's missing-outcome rate is 1.67%** — comfortably under Amendment 2's 5%
"compromised" threshold. **HOLD-OUT's is 10.80% — more than double that threshold**, and almost
none of it is rename (0.52-0.54% in both populations): it is overwhelmingly suspension (6.8pp) and
delisting (3.48pp). **The forward evaluation window is at real, concrete risk of being reported
COMPROMISED for reasons that have nothing to do with the redesign's hypothesis.** A real staleness
bug was found and fixed while building this measurement (`market_index.csv`/`outcome_labels.csv`
were several trading days behind the live `bhavcopy` table, misclassifying several still-active
symbols as delisted) — both rebuilt fresh before trusting the numbers above.

**Part 2:** three code items, tests first, full suite green after each. Item 6 merges the two
independently-hand-mirrored `STRUCTURAL_BREAK_ACTION_TYPES`/`UNADJUSTABLE_ACTION_TYPES` tuples
(`P8-009`'s own root cause) into a single definition. Item 4 (`P8-010`'s fix) adds ISIN-based
symbol resolution to corporate-actions ingestion. Item 5 adds optional history-stitching across a
rename to `build_symbol_history`, since renames were measured to cause ~0.52-0.54% of
fully-elapsed events to miss their outcome — just over the 0.5% bar set for doing this. Found and
fixed a real bug while wiring item 5 in: `compute_daily_stats` labeled every output row with a
single fixed `hist.symbol` rather than each row's own actual traded symbol — harmless before
stitching existed, would have mislabeled every post-rename day under the pre-rename symbol once it
did.

**Part 3:** production `corporate_actions` promoted for the first time this session (backed up
first): **702 → 974 rows**, ISIN-resolved. `UNIVASTU`/`AJANTPHARM`/`HEG`'s split all confirmed
correctly present. Two rows (`PFC` `BONUS`, `HEG` `SPLIT`) now hold two coexisting append-only
vintages each — handled deliberately, not by accident, both directions of `latest_as_of`'s
max-knowledge_date tie-break verified and reported (§Part 3.1). A related, smaller gap found while
spot-checking (`P8-011`: the announcement cross-check fetch isn't ISIN-aware, unlike the row-write
path — zero ratio impact, deferred). **Equity-only rule now APPLIED, not just measured**: 3,414 EQ
symbols → 2,827 kept (459 fund-unit-excluded, 128 unresolved-excluded). Full pipeline rebuilt:
catalogue 75,300 → 70,638 events. Thresholds recomputed against the corrected TRAIN population and
refit: **`disclosure_UNKNOWN_COVERAGE`'s coefficient shrinks from −0.396295 to −0.159399 — less
than half — the direct, measured confirmation that this coefficient substantially encoded
instrument type**, exactly as `P8-007` hypothesized. Every other coefficient is stable. New pinned
commit: `f4909fd362ed4113ca592e4df8f1164fa7e9f77b`.

---

## Part 1 — Measurement (read-only, against the pre-correction data)

### Item 1: every ISIN mapping to more than one symbol

`scripts/phase10_amendment4_isin_renames.py`. **195 ISINs** resolve to more than one symbol in the
current map, all 398 distinct symbols involved carrying real EQ bhavcopy history (every group is a
genuine, chronologically-clean rename — no group has overlapping date ranges). A sample (full list
in the script's own log output):

| ISIN | Symbols (chronological) |
|---|---|
| `INE931S01010` | `ADANITRANS` (2019-10-01..2023-08-23) → `ADANIENSOL` (2023-08-24..) |
| `INE191H01014` | `PVR` (..2023-05-11) → `PVRINOX` (2023-05-12..) |
| `INE775A01035` | `MOTHERSUMI` (..2022-06-08) → `MOTHERSON` (2022-06-09..) |
| `INE155A01022` | `TATAMOTORS` (..2025-10-23) → `TMPV` (2025-10-24..) |
| `INE545A01024` | `HEG` (..2026-09-21) → `HEGAM` (2026-09-22..) |
| ... | 190 more, many ETF symbol-convention changes, many real company renames |

**Orphaned actions** (ex-date inside one member's window, filed under a sibling): 19 renames
affected, 26 actions total, including two real `BONUS 1:1` actions
(`INFIBEAM`/`CCAVENUE` ×2, `MINDAIND`/`UNOMINDA`) directly relevant to item 2 below, several
`DEMERGER`/`RIGHTS` exclusion markers, and `HEG`'s own `SPLIT` (the case that started this whole
line of investigation).

### Item 2: checking the 52 unexplained shape hits against ISIN siblings

Of the P8-007 corrections' 52 persisting "unexplained" hits, checking each against its ISIN
siblings' own action history (±45 days) explains **4 more**:

| Symbol | Date | Sibling's action |
|---|---|---|
| `COSMOFILMS` | 2022-06-16 | `COSMOFIRST` `BONUS` 2022-06-16, `Bonus 1:2` |
| `INFIBEAM` | 2022-03-14 | `CCAVENUE` `BONUS` 2022-03-14, `Bonus 1:1` |
| `MINDAIND` | 2022-07-07 | `UNOMINDA` `BONUS` 2022-07-07, `Bonus 1:1` |
| `NXTDIGITAL` | 2022-12-06 | `NDLVENTURE` `DEMERGER` 2022-11-22 |

48 remain genuinely unexplained — the large majority resolve to no known multi-symbol ISIN at all
(not a rename case), and the few that do (`ATLANTAA`/`ATLANTA`, `IBULHSGFIN`/`SAMMAANCAP`,
`INCREDIBLE`/`ADHUNIKIND`, `TICL`/`TCLCONS`) were checked and found no matching action even under
the sibling. Not individually re-investigated further (out of this pass's scope).

### Item 3: missing outcomes by cause, TRAIN vs. HOLD-OUT

`scripts/phase10_amendment4_missing_outcomes.py`. **A real staleness bug was found and fixed
first**: `market_index.csv` (last date 2026-09-15) and `outcome_labels.csv` were both built against
a `bhavcopy` snapshot several real trading days behind the live table (ongoing weekly ingestion had
since extended it through 2026-09-22) — this misclassified several still-actively-trading symbols
(e.g. `A2ZINFRA`, still trading through 2026-09-22) as "delisted." Both artifacts rebuilt fresh
(`scripts/build_market_index.py`, `scripts/compute_outcome_labels.py`) before trusting anything
below.

Classification waterfall (RENAME via ISIN-sibling continuity; SUSPENSION if the symbol's own last
bhavcopy date is within 10 sessions of the global end; DATA_GAP if the stop date coincides with a
whole-market low-coverage day — none found; DELISTING as the residual, explicitly a heuristic, not
an independently confirmed fact — this project has no delisting-notice feed):

| | TRAIN | HOLD-OUT |
|---|---|---|
| Fully elapsed | 64,450 | 7,045 |
| **Lacking a 90-session outcome** | **1,079 (1.674%)** | **761 (10.802%)** |
| — DELISTING | 582 (0.903%) | 245 (3.478%) |
| — RENAME | 334 (0.518%) | 37 (0.525%) |
| — SUSPENSION | 163 (0.253%) | 479 (6.799%) |

**TRAIN is well under the 5% compromised threshold. HOLD-OUT is more than double it — driven by
suspension and delisting, not rename.** Since the forward evaluation window (2026-09-16 through
2027-01-15) is temporally and compositionally closest to this same 2026 population, this is a real
signal that Amendment 2's missing-data rule could report the forward evaluation COMPROMISED for
reasons unrelated to the redesign's hypothesis — addressed in the draft amendment (§4 there).

---

## Part 2 — Code (tests first, committed separately: `d4861fc`→measurement, `eaadffe`→this part)

### Item 6 — merge the two mirrored constants (`P8-009`'s root cause)

`STRUCTURAL_BREAK_ACTION_TYPES` (`event_catalogue.py`) and `UNADJUSTABLE_ACTION_TYPES`
(`price_adjustment.py`) are now both defined once, in `corporate_actions.py`, and imported by both
modules — the exact duplication that let `P8-009` happen (`RIGHTS`/`RATIO_CONFLICT` added to one
copy, missed in the other) is now structurally impossible, not just disciplined against. A new
test (`SharedStructuralBreakDefinitionTest`) asserts object identity (`assertIs`), not just value
equality, so a future addition to one without the other fails loudly.

### Item 4 — ISIN-based action identity (`P8-010`'s fix)

New `src/ingestion/nse_market_data/isin_mapping.py`: `fetch_isin_snapshot` (real CM/UDiFF bhavcopy
fetch, both historical schemas), `merge_isin_snapshots`, `build_symbol_groups`, `load_isin_map` —
formalizes the ad hoc multi-snapshot fetch the P8-007 corrections session used into a reproducible,
tested module. `scripts/build_isin_map.py` replaces the untracked one-off process that originally
built `data/raw/nse_symbol_isin_current.json` (re-run this session: 3,289 symbols, one date failed
with a real transient 404, handled gracefully).

`corporate_actions.py` gains `resolve_isin_symbol` (pure: given a raw symbol, an ex_date, and a
dict of candidate symbols → their own bhavcopy date ranges, returns whichever candidate's window
covers `ex_date`) and `build_isin_candidates_for_actions` (the DB-touching wrapper that builds that
dict, only for ISINs actually present in the batch being ingested). `build_rows_and_report`/
`ingest_corporate_actions` gain an optional `isin_candidates`/`isin_map` parameter, default `None`
— fully backward compatible, every existing fixture unaffected. `weekly_ingest.py`'s
corporate-actions step now loads the map when present, falling back to no resolution otherwise
(P8-006's lesson: a real pipeline step must not hard-depend on a file nothing in the repo can
reproduce).

### Item 5 — stitch price/label history across a rename

`build_symbol_history` gains an optional `symbol_group` parameter (default `None` = `[symbol]`,
identical to before). Given a group, it merges every member's bhavcopy rows and corporate actions
into one continuous chronological history — safe because a real rename's members never overlap in
date (confirmed: all 195 detected renames are strictly contiguous). Wired into every script that
needs it: `build_final_event_catalogue.py`, `compute_clustering.py`, `build_event_classifications.py`,
`compute_outcome_labels.py`, `phase8_robustness_relabel_t0.py`.

**Found and fixed a real bug while wiring this in**: `compute_daily_stats` labeled every output
`DailyStat` row with a single fixed `hist.symbol`, not each row's own actual traded symbol
(`today_row["symbol"]`). Harmless before stitching existed (the two were always identical for a
single, unstitched symbol) — but would have mislabeled every post-rename day under the pre-rename
symbol once stitching was used, corrupting the catalogue with duplicated/mislabeled rows across a
rename boundary. Fixed (`symbol=today_row["symbol"]`); `build_final_event_catalogue.py`'s driving
loop also changed to process each rename GROUP once (not once per member symbol, which would have
double-built the stitched history), and its demerger-window lookup now uses each row's own real
symbol, not the group's representative.

---

## Part 3 — Rebuild, refit

### 3.1 Promotion, with append-only handled deliberately

`scripts/phase10_amendment4_promote_corporate_actions.py`. Production DB backed up first
(`data/processed/praman_pre_p8007_promotion_backup_20260923T174335.db`, 1.4GB, untouched copy).
Re-derives every row from the cached full sweep using the current, fixed code (ISIN resolution
included) and lets `write_facts`'s own UNIQUE-constraint duplicate handling decide what's new:

```
Production corporate_actions: 702 -> 974 rows
Inserted: 272   Skipped duplicate (identical 4-tuple): 679
```

Spot-checked directly: `UNIVASTU` (1 row, `RATIO_CONFLICT`), `AJANTPHARM` (1 row, `BONUS` 1:2),
`HEG` (3 rows — the pre-existing `DEMERGER` and `SPLIT`, plus a NEW correctly-ISIN-resolved `SPLIT`
vintage), `HEGAM` (unchanged, 1 row from `weekly_ingest`), `M&MFIN` (2 `RIGHTS` rows — the known
2020-07-22 case **plus a newly-discovered second Rights issue, 2025-05-14**, not previously known
to this project).

**Two business keys now hold two coexisting vintages, exactly the append-only shape the PFC case
was flagged for in advance — both checked, neither silently left to accident:**

| Business key | Old vintage | New vintage | `latest_as_of` winner (late `as_of`) |
|---|---|---|---|
| `PFC` `BONUS` 2023-09-21 | `knowledge_date=2023-09-21`, `EX_DATE_FALLBACK` | `knowledge_date=2023-08-11`, `CONFIRMED` | **OLD** (later knowledge_date) |
| `HEG` `SPLIT` 2024-10-18 | `knowledge_date=2024-08-13`, `MATCHED_UNCONFIRMED` | `knowledge_date=2024-10-18`, `EX_DATE_FALLBACK` | **NEW** (later knowledge_date) |

Both ratios are IDENTICAL between old and new vintage in both cases (`PFC`: 1.0:4.0 both;
`HEG`: 10.0:2.0 both) — **`compute_adjustment_factor`'s output is unaffected by either resolution,
confirmed directly.** The only consequence is which `confidence_tier` metadata `latest_as_of`
surfaces for a late `as_of` query: `PFC`'s real, more-precise announcement date (2023-08-11) IS now
correctly visible via `read_as_of` for any `as_of` in [2023-08-11, 2023-09-21) — fixing the
bitemporal-visibility gap that mattered — even though `latest_as_of` itself still prefers the
older-filed fallback row afterward. `HEG`'s case is the mirror image (the new, less-precise
`EX_DATE_FALLBACK` vintage wins) — traced to a real, related gap: the announcement cross-check
fetch itself isn't ISIN-aware yet, only the final row write is (logged as `P8-011`, deferred, zero
ratio impact). **Decision made explicitly: accept both as a known, narrow, disclosed limitation of
append-only + max-knowledge_date tie-break semantics — not worth a special-case for 2 rows out of
974, and zero effect on any adjustment factor this project computes.**

### 3.2 Equity-only rule, applied

```
Equity-only universe rule applied: 3414 EQ symbols -> 2827 kept,
  459 excluded as fund-unit (INF ISIN), 128 excluded as unresolved (no ISIN found)
```

Rule: exclude `INF`-prefix ISINs (fund units) AND unresolved symbols (no ISIN in any snapshot) —
per instruction, both excluded and counted. Every other prefix (`INE`, and the small `IN9...` DVR
class) is kept.

### 3.3 Full pipeline rebuild

| Artifact | Before | After |
|---|---|---|
| `event_catalogue_loose_zscore_only.csv` | 75,300 events | **70,638 events** |
| `clustering.csv` | 75,300 rows | 70,638 rows |
| `event_classifications.csv` (+ `classification_thresholds.json`, the live agent layer's own input) | 75,300 rows | 70,638 rows |
| `phase8_relabel_t0_relative.csv` | 75,300 rows | 70,638 rows |

Rebuild order: catalogue → clustering → classifications → relabel (each depends on the catalogue;
classifications and relabel are independent of each other). Runtimes: catalogue 1,064s, clustering
665s, classifications 72s, relabel 78s.

### 3.4 Thresholds recomputed, refit

**"Same median rule" means recomputing the median of the CORRECTED TRAIN population, not reusing
the pre-correction values** — the thresholds themselves are a function of TRAIN, and TRAIN's
composition changed (equity-only filter, corrected corporate actions).

| Threshold | Old (pre-correction, n=64,450) | New (corrected, n=60,694 cap_band-matched) |
|---|---|---|
| `delivery_pct_percentile_60d` pooled median | 15.0000 | **13.3333** |
| `same_date_event_count` pooled median | 47.0000 | **45.0000** |
| `volume_ratio` Micro | 4.7182 | **5.0926** |
| `volume_ratio` Small | 6.6737 | **6.8397** |
| `volume_ratio` Mid | 7.2739 | **7.6364** |
| `volume_ratio` Large | 8.4210 | **8.6042** |
| `volume_ratio` Mega | 7.5811 | **7.4616** |

Refit (`scripts/phase10_fit_scoring_function.py`, identical specification: same four inputs,
median rule, `volume_ratio_high_band_eligible` interaction restricted to Small/Large/Mega, `NONE`
disclosure as reference level, unregularized logistic regression, `relative_t0_primary` PRIMARY
threshold label):

| Coefficient | Old (TRAIN n=63,360) | New (TRAIN n=59,540) |
|---|---|---|
| intercept | +0.242510 | +0.262537 |
| `delivery_low` | +0.440636 | +0.442955 |
| `isolated` | +0.035727 | +0.019262 |
| `volume_ratio_high_band_eligible` | +0.210644 | +0.191298 |
| `disclosure_SUBSTANTIVE` | −0.233919 | −0.231665 |
| `disclosure_ROUTINE_ONLY` | −0.061484 | −0.064696 |
| **`disclosure_UNKNOWN_COVERAGE`** | **−0.396295** | **−0.159399** |

In-sample AUC 0.5870 → 0.5797, Brier 0.2362 → 0.2356. Label base rate 59.2% → 59.96% (the new FAIR
baseline). `disclosure_UNKNOWN_COVERAGE` prevalence in TRAIN: 10.2% → 4.95% (roughly halved,
consistent with removing fund units, which mechanically never have announcement coverage).

**Reading this directly: `UNKNOWN_COVERAGE`'s coefficient shrinks by more than half once the
fund-unit confound is removed from the population it's fit on.** This is the measured confirmation
of what `P8-007` could only hypothesize from correlation (61.22% of `UNKNOWN_COVERAGE` events were
confirmed fund units) — the model's largest-magnitude coefficient substantially WAS instrument
type, not disclosure behavior, and now that instrument type is excluded rather than left to
confound the fit, the coefficient shrinks accordingly. Every other coefficient is stable within
noise, indicating those findings were not similarly confounded.

**New pinned commit for the feature pipeline (supersedes Amendment 2 §2's `a01eda4`):
`f4909fd362ed4113ca592e4df8f1164fa7e9f77b`.**

---

## What Amendment 4 decides (drafted, not committed — see `docs/phase10_preregistration_amendment4.md`)

- Whether/how the missing-data threshold should account for the measured HOLD-OUT suspension/
  delisting rate (item 3) so the forward evaluation isn't compromised for unrelated reasons.
- The refit coefficients above become the new binding scoring function.
- The equity-only rule and the new pinned commit become the forward evaluation's actual pipeline.
- `P8-011` (announcement fetch not ISIN-aware) and the 48 remaining unexplained shape hits are
  left open, explicitly, for a future session.
