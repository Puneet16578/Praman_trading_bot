# P8-007 Corrections — Data Corrections, Staged Separately

**No refit, no amendment, and no change to the production `corporate_actions` table or any
derived table, per instruction.** Two code changes were made and committed this session (items
2/3's fix, and one bug found while verifying it) — both are currently inert against production
data: no `RIGHTS`/`RATIO_CONFLICT` row exists there, and the corrected full sweep lives in a
SEPARATE staging database, never merged in. Amendment 4 is decided from these results next
session, not here.

## Summary (read this first)

**Item 1:** the real, live, full `fetch_all(2019, 2026)` sweep — never previously executed
(`P8-008`) — has now actually run: 18,190 raw actions across 8 years, 578 distinct
bonus/split-shaped announcement-window fetches, 951 rows staged. **It crashed once**, on a real
NSE connection reset at 330/578 fetches, and resumed cleanly from cache with zero re-fetching —
confirming the resumable design was not a theoretical precaution. **Diffed against production
(702 rows): 700 match exactly.** Of the 2 differences: **zero are a genuine completeness gap** —
both are one real company (`HEG`/`HEGAM`, same ISIN) whose ticker changed, filed under the
pre-rename symbol in production and the post-rename symbol live (detail in §1). Of 251 rows
present live but absent from production: 249 are this session's own `RIGHTS`/`RATIO_CONFLICT`
code fix becoming visible for the first time (expected), 1 is `AJANTPHARM`'s regex-fixed `BONUS`
row, and 1 is `HEGAM`'s correctly-labeled counterpart of the same ticker-rename case. **`UNIVASTU`
appears exactly where predicted** — present live, absent from production, now correctly written
as a `RATIO_CONFLICT` exclusion marker. One row (`PFC`, `BONUS`, 2023-09-21) upgrades from
`EX_DATE_FALLBACK` to `CONFIRMED` with a real, earlier knowledge_date — a real announcement the
old cache's fetch apparently missed, not a disagreement.

**Item 2:** `UNIVASTU` is confirmed `QUARANTINE`-classified by the current, unmodified matching
logic — a garbled auto-parsed announcement ratio (`25357180:11995590` vs. the correct `2:1`), the
same known failure mode already documented for `AURIGROW`. Phase 3's original in-memory
`quarantined` list was never persisted anywhere, so "was `UNIVASTU` among Phase 3's own quarantined
rows" cannot be answered retroactively — this is the most useful available substitute. `QUARANTINE`
and `RIGHTS` now both write structural-break exclusion markers instead of being dropped/miscounted.

**Item 3:** the `Bonus-` regex is fixed. Run against all 18,190 live subjects: **zero remaining
genuine equity bonus/split gaps.** 8 residual subjects still contain the word "bonus" and still
don't match — all 8 verified correctly excluded: a bonus DEBENTURE issue (`BRITANNIA`, a different
instrument, not equity dilution) and bonus NCRPS/preference-share issues (`RADIOCITY`, `TVSHLTD`
x2, `TVSMOTOR`, `SIYSIL` x2 — already known from a Phase 5 audit, re-confirmed here at full live
scale).

**Item 4:** ISIN resolution improved from a single-snapshot 79.41% to a real, multi-snapshot
**99.12%** (2,932 of 2,958 catalogued symbols), using 8 additional historical bhavcopy fetches
across both NSE schema eras. Equity-only rule (measured, not applied): would remove **6.07% of
TRAIN**, **10.72% of HOLD-OUT**. **61.22% of every `UNKNOWN_COVERAGE` event is a confirmed
fund unit** — up from the 43.90% lower bound the live-ETF-list-only method gave in the prior
scoping pass (superseded, not contradicted: same underlying claim, a more complete method).

**Item 5:** shape scan re-run on the staged corrected actions + equity-only population: **96 → 55
hits.** 41 removed as fund-units (more than the 32 the live ETF list alone caught — the ISIN
method's completeness advantage, confirmed again). Of the 55: 1 explained by a real ratio
(`AJANTPHARM`), 2 explained by an exclusion marker (`M&MFIN` Rights, `UNIVASTU` ratio-conflict —
its mystery is now resolved, not unexplained), **52 unexplained — a clean subset of the original
61, exactly as expected. Zero new hits appeared.**

**Two things found this session that are not part of the 5-item scope, reported per CLAUDE.md's
verification-honesty rule, not folded into the above:**
- **A real bug in this session's own item-2 fix**, caught while verifying it before commit:
  `price_adjustment.py` keeps a second, hand-mirrored copy of the exclusion-type list
  (`UNADJUSTABLE_ACTION_TYPES`) that was not updated alongside `event_catalogue.py`'s. Fixed and
  tested in a separate commit (`P8-009` below).
- **The `HEG`/`HEGAM` ticker rename** (§1): not a defect in the classic sense, but a real,
  newly-exposed structural risk — this project's own corporate-actions/bhavcopy join is symbol-
  string-based throughout, and a naive promotion of the live sweep's current-symbol data into
  production would silently orphan `HEG`'s real split/demerger from 1,726 days of its own,
  correctly-labeled price history. Logged as `P8-010`, decided at Amendment 4.

---

## 1. Full live sweep, diffed against production

`scripts/phase10_p8007_full_sweep_staging.py`: resumable by construction (every year's action
fetch and every announcement-window fetch is cached to disk immediately on success). Step 1 (8
year-fetches, 18,190 raw actions) completed in seconds, no issues. Step 2 (578 distinct
bonus/split-shaped `(symbol, ex_date)` announcement-window fetches) **crashed at fetch #330** with
`requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(10054, 'An
existing connection was forcibly closed by the remote host'...))` — a real NSE-side reset, not a
bug in this code. Re-invoking the identical script skipped all 330 already-cached fetches and
completed the remaining 248 without incident. **This is exactly the failure mode the resumable
design existed for, observed for real on the first genuine overnight-scale run.**

**Staging write result** (`data/processed/praman_staging_p8007_sweep.db`, gitignored, never
merged into production):

| Tier | Count |
|---|---|
| `CONFIRMED` | 342 |
| `MATCHED_UNCONFIRMED` | 115 |
| `EX_DATE_FALLBACK` | 149 |
| `RIGHTS_EXCLUSION` | 244 |
| `DEMERGER_EXCLUSION` | 93 |
| `RATIO_CONFLICT_EXCLUSION` | 5 |
| `CAPITAL_REDUCTION_EXCLUSION` | 3 |
| **Total inserted** | **951** |

Unhandled action types (dividends, AGMs, buybacks, etc. — correctly not written): 15,936 of
18,190 raw rows.

**Diff (`scripts/phase10_p8007_sweep_diff.py`), by comparison key `(symbol, action_type,
event_date)`:**

| Category | n |
|---|---|
| Exact match (both sides agree) | 700 of 702 |
| Present live, absent from ours | 251 |
| Present in ours, absent live | 2 |
| Same key, `knowledge_date`/`confidence_tier` differs | 1 |
| Same key, ratio differs | 0 |

**Present live, absent from ours (251), grouped by cause:**

| Cause | n |
|---|---|
| A. New action type from this session's own code fix (`RIGHTS`/`RATIO_CONFLICT`) | 249 |
| B. `BONUS` the OLD (pre-fix) regex could not parse at all | 1 |
| C. Symbol never in production `corporate_actions` at all | 0 |
| D. Symbol known to production, this action/date is new | 1 |

Bucket A (249) is expected and not a completeness finding — it is this session's own item-2 code
change (write `RIGHTS`/`RATIO_CONFLICT` instead of dropping/miscounting) becoming visible for the
first time against real data. Bucket B is `AJANTPHARM BONUS 2022-06-22, "Bonus- 1:2"` — the exact
case that motivated item 3's fix, now correctly captured (`MATCHED_UNCONFIRMED`, ratio 1:2).
Bucket D, `HEGAM SPLIT 2024-10-18`, is the correctly-labeled counterpart of the ticker-rename case
below — not a new gap.

**`UNIVASTU`, checked directly as instructed:**

```
('UNIVASTU', 'RATIO_CONFLICT', '2025-10-13') -> {
  'ratio_numerator': None, 'ratio_denominator': None, 'confidence_tier': 'RATIO_CONFLICT_EXCLUSION',
  'details': 'subject=2:1 announcement=25357180:11995590', 'knowledge_date': '2025-08-29',
  'source_file': 'p8007_full_sweep_2019_2026_live',
}
```

Present live, absent from production — exactly as predicted going in.

**Present in ours, absent live (2) — traced fully, not left as an unexplained gap:**

```
HEG    DEMERGER  2026-09-07  (production, source=nse_corporate_actions_2019_2026_cached.json)
HEG    SPLIT     2024-10-18  ratio=10.0:2.0  (production, same source)
```

Neither is missing from the live feed. Both are filed live under a **different symbol string for
the exact same security**: `HEGAM`. Confirmed, not assumed:

- Both `HEG` and `HEGAM` resolve to the **identical ISIN**, `INE545A01024`
  (`data/raw/nse_symbol_isin_current.json`).
- `HEG`'s own raw bhavcopy close falls from 2570.40 (2024-10-17) to 496.35 (2024-10-18) — a
  5.18x drop, matching the 10:2 (5x) split ratio **on `HEG`'s own price series**, not a
  coincidence.
- `HEG`'s own raw bhavcopy close falls from 728.25 (2026-09-04) to 272.20 (2026-09-07) — a real
  ~62.6% value drop, consistent with a genuine demerger, again on `HEG`'s own series.
- `HEG` has 1,726 bhavcopy rows, 2019-10-01 through **2026-09-21** (its last trading day under
  that symbol). `HEGAM` has exactly **one** bhavcopy row, dated **2026-09-22** — the very next
  trading day, sourced from that day's real bhavcopy file.

**Conclusion: `HEG` renamed its own ticker to `HEGAM` effective 2026-09-22**, immediately after
the 2026-09-07 demerger — the same real-world event, not two companies. NSE's live
corporate-actions endpoint reports this ISIN's entire disclosure history (back to a 2019 buyback)
under its *current* symbol string, regardless of what ticker was actually in effect on each
historical date. This project's own bhavcopy ingestion, by contrast, correctly preserves the
ticker *as traded on that date* — so `HEG`'s 1,726 rows of real price history remain filed under
`HEG`, not `HEGAM`.

**Why this matters beyond this one symbol:** this project's `corporate_actions`↔`bhavcopy` join
is symbol-string-based throughout (`compute_adjustment_factor`, `build_symbol_history`). If a
future correction naively promoted the live sweep's `HEGAM`-labeled split/demerger rows into
production as a "fix" for these 2 rows, it would **silently orphan both actions from 1,726 days of
`HEG`-labeled price history** — the exclusion/adjustment would stop applying to the price series
it exists to protect. The OLD stale cache happened to get this one case right, by having been
fetched before the rename. Filed as a new, distinct defect (`P8-010`) precisely because "trust the
live feed's symbol field" is not a safe general policy here — any future reconciliation needs to
resolve identity via ISIN, not symbol string.

**The one same-key content difference:**

```
('PFC', 'BONUS', '2023-09-21'): ours=EX_DATE_FALLBACK/knowledge_date=2023-09-21
                                 live=CONFIRMED/knowledge_date=2023-08-11
```

The live sweep's announcement-window fetch found a real, earlier announcement (2023-08-11) that
the old cache's own fetch apparently missed, upgrading the tier from a safe ex-date fallback to a
fully confirmed real announcement date. An improvement, not a disagreement to resolve.

## 2. Quarantine and Rights now fail closed

`build_rows_and_report` (`src/ingestion/nse_market_data/corporate_actions.py`): a `QUARANTINE`-
tier disagreement (subject and announcement ratios don't agree) and a Rights issue (a real,
disclosed ratio this project does not attempt to adjust for — a different mechanism than
bonus/split, depending on subscription premium and theoretical ex-rights price, not the ratio
alone) both used to either vanish entirely or get silently miscounted as generic "unhandled."
Both now write a structural-break exclusion marker — no ratio, no factor — under new action types
`RATIO_CONFLICT`/`RIGHTS`, so the existing 60-session demerger-exclusion machinery applies to them
identically to a demerger or capital reduction.

`UNIVASTU`'s real, unmodified classification, checked directly:

```
classify_bonus_split({'type': 'BONUS', 'numerator': 2.0, 'denominator': 1.0, ...}, ...)
  -> tier=QUARANTINE (subject "2:1" vs. announcement "25357180:11995590" disagree)
```

The same auto-text-quality failure this module's own docstring already documents for `AURIGROW`.
Phase 3's original in-memory `quarantined` list was never written to any file or table, so "was
`UNIVASTU` among Phase 3's own quarantined rows" has no retrievable answer — what the current,
unmodified logic classifies it as today is the most useful substitute, and it is: `QUARANTINE`,
now correctly surfaced as `RATIO_CONFLICT_EXCLUSION` rather than dropped.

Tested: `tests/test_corporate_actions_ingestion.py` (`test_rights_becomes_exclusion_marker_no_ratio`,
`test_quarantine_becomes_ratio_conflict_exclusion_marker_still_logged`,
`test_quarantined_row_written_as_ratio_conflict_exclusion_not_a_trusted_ratio`),
`tests/test_event_catalogue.py` (`test_rights_window_excluded_same_as_demerger`,
`test_ratio_conflict_window_excluded_same_as_demerger`), `tests/test_price_adjustment.py`
(`RightsAndRatioConflictUnadjustableTest`).

## 3. The "Bonus-" regex fix

`parse_subject_ratio`'s pattern widened from `r"\bBonus\s+(\d+)\s*:\s*(\d+)\b"` to
`r"\bBonus[\s\-:.]*(\d+)\s*:\s*(\d+)\b"` — tolerates any mix of whitespace/hyphen/colon/period
between "Bonus" and the ratio, still matching the plain form. Real case:
`AJANTPHARM, 2022-06-22, "Bonus- 1:2"` — confirmed failing before the fix, passing after.

**Ran the fixed parser against every one of the 18,190 live-fetched subjects (not just the known
case): zero remaining genuine equity bonus/split gaps.** 8 subjects still contain "bonus" and
still don't match `parse_subject_ratio` — each verified correctly excluded, not missed:

| Symbol | Date | Subject | Why correctly excluded |
|---|---|---|---|
| `BRITANNIA` | 2019-08-22, 2021-05-25 | "Scheme Of Arangement- Bonus - 1 Debenture For 1 Equity Share Held" | Bonus **debenture** — a different instrument, no equity share-count dilution |
| `RADIOCITY` | 2023-01-13 | "Scheme Of Arrangement - Bonus Ncrps 1:10" | Bonus **NCRPS** (non-convertible redeemable preference shares) — not equity |
| `TVSHLTD` | 2023-03-24, 2026-09-08 | "Bonus Ncrps 1:116" / "...46:1" | Same — preference shares |
| `TVSMOTOR` | 2025-08-25 | "Scheme Of Arrangement - Bonus Ncrps 4:1" | Same |
| `SIYSIL` | 2026-08-21 (x2) | "Scheme Of Arrangement - Bonus Ncrps 4:1" / "3:1" | Same |

The NCRPS cases are already known from a Phase 5 audit (`is_demerger_subject`'s own docstring
explicitly names this exact class as a reason "Scheme Of Arrangement" was rejected as a general
demerger pattern) — re-confirmed here at full live scale, not a new finding. The `BRITANNIA` bonus-
debenture case is newly confirmed at this scale. Neither follows the simple share-count dilution
formula `factor_for_action` implements for `BONUS`; matching them would apply a wrong adjustment
factor, not a missing one. Split-shaped subjects: **zero** unmatched across all 18,190 — the
existing "From Rs X To Rs Y Per Share" pattern already generalizes correctly.

Tests added: `test_hyphen_attached_bonus_real_ajantpharm_subject`,
`test_bonus_hyphen_no_space_variant`, `test_bonus_plain_space_form_still_matches`.

## 4. Equity-only universe rule — measured, not applied

`scripts/phase10_p8007_isin_universe.py`, ISIN prefix method (`INE`=company equity,
`INF`=mutual-fund/ETF unit — confirmed directly: `GROWWGOLD`/`SILVERBEES`/`NIFTYBEES` all `INF`;
`RELIANCE`/`TCS`/`AJANTPHARM` all `INE`), preferred over the live `/api/etf` list per instruction
because it also resolves renamed/delisted ETFs the list misses.

**This project's own bhavcopy ingestion does NOT carry ISIN** (`sec_bhavdata_full` format,
confirmed directly). A DIFFERENT NSE file does — `jugaad_data.nse.bhavcopy_save`
(the CM/UDiFF bhavcopy), under two schemas across its history (legacy `SYMBOL,SERIES,...,ISIN`
pre-mid-2024; UDiFF `TckrSymb,SctySrs,...,ISIN` current). A single current-day snapshot resolves
only 79.41% of catalogued symbols (delisted/renamed ones fail). Fetching 8 additional real
historical snapshots (legacy: 2019-11-15, 2020-06-15, 2021-02-17, 2021-06-15, 2021-07-22,
2022-06-15, 2023-06-15; UDiFF: 2025-02-04, 2025-06-16, 2025-10-13) improved this to:

| Metric | Value |
|---|---|
| Distinct catalogued symbols | 2,958 |
| Resolved to an ISIN | 2,932 (**99.12%**) |
| Unresolved | 26 (0.88%) |
| Of resolved: `INE` (equity) | 2,538 |
| Of resolved: `INF` (fund unit) | 391 |
| Of resolved: other prefix (`IN9...`, DVR shares — genuine equity, correctly retained) | 3 |

The 3 "other prefix" symbols (`JISLDVREQS`, `TATAMTRDVR`, `FELDVR`) are Differential Voting Rights
shares of real operating companies — a distinct ISIN series, still genuine equity, not fund units.
The equity-only rule only removes `INF`-prefixed symbols, so these 3 are correctly retained
either way.

**If applied (not applied this session):**

| Population | n events | Would remove | Share |
|---|---|---|---|
| TRAIN (2019-2025) | 64,450 | 3,915 | **6.07%** |
| HOLD-OUT (2026) | 10,850 | 1,163 | **10.72%** |

**`UNKNOWN_COVERAGE` composition (n=8,294):** 5,078 (**61.22%**) are confirmed fund units — up
from the prior scoping pass's 43.90% (live-ETF-list-only, a known lower bound). Same underlying
claim, a more complete method; **the `UNKNOWN_COVERAGE` coefficient's instrument-type
confounding is confirmed more strongly, not newly discovered.**

## 5. Shape scan re-run

`scripts/phase10_p8007_shape_scan_rerun.py`: same shapes/tolerance as the original
pre-registered scan, run against (a) the staged, corrected actions from §§1-3 instead of
production, and (b) the equity-only population from §4 (5,078 fund-unit rows excluded from the
catalogue before scanning).

| | Original (production actions, live-ETF-list-only) | Re-run (staged corrected actions, ISIN equity-only) |
|---|---|---|
| Total hits | 96 | **55** |
| ETF/fund-unit excluded | 32 | 41 |
| Explained by a real ratio | 0 | 1 (`AJANTPHARM`) |
| Explained by an exclusion marker | 0 (bucket didn't exist) | 2 (`M&MFIN` Rights, `UNIVASTU` ratio-conflict) |
| Confirmed missed action (old bucket) | 3 | — (now folded into the two explained buckets above) |
| Unexplained | 61 | **52** |

**Reconciliation, exact:** of the original 96, 3 (`AJANTPHARM`, `M&MFIN`, `UNIVASTU`) move into
the explained buckets under the corrected actions. Of the remaining 93 (32 ETF + 61 no-action), 41
are now excluded as fund-units under the more complete ISIN method (9 more than the 32 the live
ETF list alone caught), leaving 52 unexplained — **a clean subset of the original 61, exactly the
persistence the instruction anticipated. No new hit appeared anywhere in this re-run** (the shape
logic and target list are byte-identical to the original scan; the population filter can only
remove rows, never add one, so a new hit is structurally impossible here — confirmed by
construction, not merely by inspection).

`UNIVASTU`'s long-standing "unresolved downstream drop" (`P8-007`/`P8-008`) is now **fully
resolved**: correctly explained by its own `RATIO_CONFLICT` exclusion marker, not unexplained.

The 52 persisting unexplained hits were not individually re-investigated this session (out of the
5-item scope) — reported as a list in the script's own output for whoever picks up that
investigation next.

---

## New defects found this session (not part of the 5-item scope)

### P8-009 — `price_adjustment.py`'s `UNADJUSTABLE_ACTION_TYPES` missed `RIGHTS`/`RATIO_CONFLICT`

Found while verifying item 2's own fix before committing it, not by the user or by a later audit.
`event_catalogue.py` documents its `STRUCTURAL_BREAK_ACTION_TYPES` as a deliberate, hand-mirrored
copy of `price_adjustment.py`'s exclusion-type list (for a fast vectorized catalogue-build path vs.
a slower, per-pair-verified path) — updating one without the other leaves the slow path silently
treating a `RIGHTS`/`RATIO_CONFLICT` window as adjustment-neutral (factor unchanged, no exception)
instead of raising `UnadjustableWindowError`. Not a wrong multiplicative factor, but a silent skip
of the exact fail-closed behavior item 2 exists to guarantee. Fixed same session, before affecting
any real computation (no row of either type exists in production, and nothing calls
`compute_adjustment_factor` against the new staging data). Tests added
(`RightsAndRatioConflictUnadjustableTest`, `test_event_catalogue.py`'s two new exclusion tests).
Full suite: 338/338 pass. Committed separately (`59d1dbf`).

### P8-010 — a live-feed "current symbol" is not always this project's own symbol for a given date

Found tracing the 2 "present in ours, absent live" diff rows (§1). `HEG` renamed its own ticker to
`HEGAM` around the 2026-09-07 demerger (confirmed: identical ISIN `INE545A01024`; `HEG`'s own raw
price shows the exact split/demerger signatures on both dates; `HEGAM` first appears in this
project's own bhavcopy the very next trading day after `HEG`'s last one). NSE's live
corporate-actions endpoint reports this security's entire history under its *current* symbol,
retroactively — not the symbol actually in effect on each historical date. This project's
`corporate_actions`↔`bhavcopy` join (`compute_adjustment_factor`, `build_symbol_history`) is
symbol-string-based throughout. **Not fixed this session** (would require touching production,
explicitly out of scope) — flagged because a future correction that naively trusts the live feed's
symbol field would silently orphan `HEG`'s real split/demerger from 1,726 days of correctly-`HEG`-
labeled price history. Any future reconciliation of the staged sweep into production must resolve
identity via ISIN for cases like this, not symbol string alone. Decided at Amendment 4, not here.

---

## What is still open, stated plainly

Not decided in this pass, per instruction: whether/how to promote the staged sweep
(`data/processed/praman_staging_p8007_sweep.db`) into production; whether the equity-only rule
(§4) should actually be applied, and if so how it interacts with `P8-010`'s ISIN-vs-symbol
reconciliation need; whether the 52 persisting unexplained shape hits warrant individual
investigation; whether `HEG`'s specific ticker-rename case needs a manual, symbol-aware
correction distinct from a blanket live-sweep merge. All are measured and reported here; none are
applied. **Amendment 4 is decided from these results next session, not before it.**
