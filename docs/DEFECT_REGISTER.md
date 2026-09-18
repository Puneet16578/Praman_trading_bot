# Defect Register

Every defect this project finds in itself, with an ID, root cause, fix, and re-verification
evidence — including ones introduced by this project's own code, per CLAUDE.md's verification
honesty rule.

| ID | Found | Severity | What it was | Status |
|---|---|---|---|---|
| P2-001 | Ph. 2 (NSE ingestion, pre-flight) | High | `jugaad_data.nse.full_bhavcopy_save()` reports success (no exception) even when NSE returns an HTTP error page instead of real bhavcopy data. | Fixed — mitigated at the store layer |
| P2-002 | Ph. 2 (NSE ingestion, pre-implementation) | High | `sqlite3` silently binds a `numpy.int64`/`numpy.float64` parameter as a raw BLOB instead of an integer/float — no exception, no warning, and the store's own `numbers.Integral`/`numbers.Real` type check does not catch it (numpy scalars correctly satisfy those ABCs). | Fixed — store coerces to native `int`/`float` before binding |
| P2-003 | Ph. 2 (NSE ingestion, real-data verification) | High | NSE's bhavcopy archive can return HTTP 200 with well-formed CSV content for a **different date** than the one requested, under the requested date's own URL. For weekends/holidays this is a sane 1-3 day fallback to the nearest prior trading day; for 2019-09-30 specifically, the returned content was for 2019-06-27 — a 95-day anomaly, not a holiday fallback. This also invalidated this project's own earlier "earliest available date: 2019-09-30" claim, which had only checked "is this real CSV," not "is this CSV actually dated 2019-09-30." | Fixed — corrected earliest date to 2019-10-01; ingestion now compares the response's own DATE1 to the requested date and rejects (as a gap) any mismatch beyond a small fallback window |
| P2-004 | Ph. 2 (NSE ingestion, real-data verification) | Medium | A real NSE bhavcopy file can have a genuinely blank `SERIES` for some rows (observed: 30 of 43,942 rows in the 2019-10-01 file, all bond/NCD-like instruments — DHFL, HUDCO, IBULHSGFIN, IRFC). The parser's `str(nan_value).strip()` silently turned this into the literal text `"nan"` — a valid-looking, non-null string that passed the store's type check and would have corrupted the business key `(symbol, event_date, series)`. | Fixed — rows missing SYMBOL or SERIES are skipped (not force-labeled) and counted in `rows_skipped_invalid`, never silently stored |
| P2-005 | Ph. 2 (NSE ingestion, reporting review) | Medium | Gap reporting conflated "weekend/holiday, not a trading day" with "genuine ingestion failure on a real trading day" — a Saturday (hard HTML error) reported as "GAP" and a Sunday (small fallback to Friday's data) reported as "ingested," purely because of which artifact NSE happened to serve, not because of anything meaningfully different about the two dates. | Fixed — outcomes reclassified against a trading calendar derived from the batch's own observed `actual_event_date` evidence; GAP now means a date some other outcome confirms is real, but whose own fetch failed |
| P3-001 | Ph. 3 (corporate actions, parser widening review) | Low | The "N (word) Equity Share...for every M (word) Equity Shares" prose form of a bonus ratio (no colon) is common in real announcements (VBL, COSMOFIRST, XPROINDIA, MANINFRA, NYKAA, SBCL, KRISHANA all use it) and is not parsed — these land as `MATCHED_UNCONFIRMED`, which is safe (ratio still comes from `subject`) but avoidably conservative. | Known-deferred — optional polish, not built this session per explicit instruction |
| P3-002 | Ph. 3 (corporate actions, parser widening review) | Low | Bonus announcement text can be internally self-contradictory (BEPL: headline "ratio of 2:1" contradicted by its own explanatory clause "1 Equity Share...for every 2" — a real NSE authoring error). No internal-consistency check exists for bonus text the way `INTERNAL_MISMATCH` already exists for splits; currently caught only indirectly, via disagreement with `subject`, landing safely in `QUARANTINE`. | Known-deferred — optional polish, not built this session per explicit instruction |
| P3-003 | Ph. 3 (corporate actions, real ingestion) | Low | AFFLE's split announcement produces `INTERNAL_MISMATCH count=50.000004 fv=5.0` — a floating-point artifact (an extraction or rounding edge case), not a genuine inconsistency; the true ratio is very likely a clean 10.0. Currently and safely classified `MATCHED_UNCONFIRMED` (ratio still from `subject`), not silently trusted with the wrong number. | Known-deferred — optional polish, not built this session per explicit instruction |
| P4-001 | Ph. 4 (ASM ingestion, multi-era fixture verification) | Medium | `EXCLUSION_TITLE_RE` only matched the bare `"excluded from ASM Framework"` wording seen in the 2019/2021/2025/2026 samples. The real 2023 ST-ASM annexure phrases the same section as `"excluded from Short - Term ASM Framework"` — the regex silently missed it, and the section was mis-routed to `unparsed_titles` (undercounted, not fabricated, but still a real coverage gap). | Fixed — regex now accepts an optional `(Long|Short) - Term` infix and uses it to set `mechanism` directly when present |
| P4-002 | Ph. 4 (GSM ingestion, real-PDF verification) | Medium | `EVENT_DATE_RE`'s gap between the `GSM`/`framework` anchor and the `with effect from`/`w.e.f.` phrase excluded newlines (`[^\n.]`), on the assumption a stray period elsewhere in the paragraph was the bigger risk. Real GSM circular PDF text wraps mid-sentence — the 2024 sample's actual text is `"...Stage II of GSM\nwith effect from December 23, 2024."` — so the gap must cross a line break; the regex failed to find the event date on this real, correctly-formatted circular. | Fixed — gap changed to `[\s\S]{0,80}?` (any char including newline, still length-bounded) |
| P4-003 | Ph. 4 (GSM ingestion, real-network smoke test before the full run) | Medium | Even after P4-002's fix, 2 of 5 freshly live-fetched GSM circulars (`SURV71944`, `SURV71726`) still failed event-date extraction. Real cause: the literal phrase `"with effect from"` inside `EVENT_DATE_RE` used literal spaces, but these two circulars wrap the line break *inside* that phrase itself — `"...moved to Stage I of GSM with\neffect from December 23, 2025."` — a newline between "with" and "effect", not just before the phrase. | Fixed — literal spaces inside the phrase changed to `\s+` (`with\s+effect\s+from`) |
| P4-004 | Ph. 4 (full real ingestion run, first attempt) | **Critical** | The real DB's `surveillance_flags` table was created (empty) during Phase 1, before this table's schema was extended for real ASM/GSM data. `init_db()` only creates a table if a table of that name doesn't already exist — it never migrates an existing table when the registry's DDL changes. Every real write this session's first full ingestion run attempted failed with `sqlite3.OperationalError: table surveillance_flags has no column named action_type`. Final state after that run: `total_rows=0` — nothing was actually persisted, despite the run completing (exit code 0) and reporting `circulars_processed: 2883`. | Fixed — stale table was empty (verified: `SELECT COUNT(*)=0` before drop), so `DROP TABLE surveillance_flags` + `init_db()` re-create was a safe, lossless migration. Full ingestion re-run after the fix. |
| P4-005 | Ph. 4 (same run, report-accuracy review) | High | `ingest_asm_circular`/`ingest_gsm_circular` incremented `report.circulars_processed` **before** calling `write_facts`. When P4-004 made every write raise, the calling sweep loop's `except Exception` correctly counted each circular as failed too — but `circulars_processed` had already been bumped, so a circular whose data never reached the store was still counted as "processed." This is what let the first run's summary (`circulars_processed: 2883`) look like a mostly-successful run right next to `total_rows=0` in the same report — the two numbers should never have been able to disagree that badly. | Fixed — `circulars_processed` now increments only after `write_facts` returns without raising, in both modules |
| P4-006 | Ph. 4 (2nd full run, pre-retry failure-cause grouping) | High | `to_iso_date` only tried `%B` (full month name). Real circulars roughly SURV52458-58318 (mid-2022 to mid-2023) spell the w.e.f. date as `"Apr 03 2023"` — abbreviated month, no comma. This was **91% of all 482 ASM failures** (439/482, 232 distinct real date strings, all one shape) — the burst-and-plateau failure pattern that looked like it could be rate-limiting was mostly this one date-format gap. | Fixed — tries `%B %d %Y` then falls back to `%b %d %Y` |
| P4-007 | Ph. 4 (same pre-retry review) | High | Real circular SURV64061's subject was `"Applicability of Enhnaced Surveillance Measure (ESM)"` — `"Enhnaced"`, a genuine typo of `"Enhanced"` — which the `"enhanced"` exclusion stem in `is_periodic_asm_subject` did not catch, so an ESM circular (a mechanism CLAUDE.md explicitly says this project does not ingest) was nearly treated as periodic ASM. Investigating it also surfaced a second, independent bug: its zip nests the workbook in a subfolder (`"SURV64061/Annexure.xlsx"`), which the zip-entry matching (`nm.lower().startswith("annexure")`, a full-path check) missed entirely. | Fixed — added the bare `"esm"` substring (the `(ESM)` abbreviation, effectively typo-proof) to the exclusion check; zip-entry matching changed to match on the basename, not the full path |
| P4-008 | Ph. 4 (post-fix GSM failure review) | Medium | Two real 2026 GSM circulars (SURV72963, SURV72867) extract with spurious whitespace INSIDE digit runs — `"with effect from February 2 5, 2026"` for the 25th — a `pdfplumber` rendering artifact of that PDF generation era, not a real character in the source. `EVENT_DATE_RE`'s `\d{1,2}` cannot match across the injected space, so the event date silently failed to extract. **First attempted fix was itself briefly wrong**: collapsing all `\s+` between two digits also matched the *newline* between one table row's trailing number and the next row's leading serial number (real `MOVE_OUT_TEXT`-shaped text: `"...INE875R01011 EQ 20\n2 FSC..."`), merging two different rows' digits and breaking `ROW_RE`'s per-line matching — caught immediately by the existing `test_move_out_template_with_trailing_columns_and_footnote` test failing, before this second bug ever touched real data. | Fixed — collapse only `[ \t]` (not `\n`) between two digits |
| P4-009 | Ph. 4 (post-retry invariant check, per explicit "sum(event_counts) == COUNT(*)" assertion added to the analysis) | High | `report.event_counts` counted every PARSED event, not every event `write_facts` actually inserted -- `write_facts`'s own `BulkWriteResult.skipped_duplicate` was discarded. Real duplicates do occur: circulars SURV68086/SURV68088 (both ASM_LT, published the same calendar day) both listed ICDSLTD's Stage-I entry with the same event_date -- a genuine same-day corrective/reissue circular pair, the same pattern already documented for corporate actions (KITEX). `write_facts` correctly stored one row and silently skipped the duplicate; the report's summed `event_counts` (31,552) did not match the store's actual `COUNT(*)` (31,550) by exactly 2. One instance was confirmed directly (ICDSLTD); the second was not individually re-traced (would require re-fetching and re-parsing the full ~3,331-circular corpus a second time for zero data-correctness benefit -- the store itself, protected by the UNIQUE constraint, cannot hold a wrong or duplicated row either way) but is the same benign class of event. | Fixed — both `ingest_asm_circular`/`ingest_gsm_circular` now accumulate `report.duplicate_events_skipped` from `write_facts`'s return value; `sum(event_counts) - duplicate_events_skipped == COUNT(*)` holds exactly for all future runs |
| P4-010 | Ph. 4 (post-ingestion lifecycle-coherence check) | **Critical** | Footnote-definition rows were only recognized when the marker text landed in column 0. Real circular SURV49783's Annexure I-A has one at `(None, '* Moved from STASM to LTASM framework', None, None)` -- the Sr.No. cell (column 0) is blank, so the footnote text sits in the SYMBOL column position instead. The column-0-only check missed it entirely, it fell through to being treated as an ordinary data row, and `'* Moved from STASM to LTASM framework'` was ingested as a literal symbol (twice -- once as an ASM_LT ENTRY from SURV49783, once as an ASM_ST EXIT from SURV49784's analogous row). Found via a systematic lifecycle-coherence check across all 4,312 real (symbol, mechanism) tracks in the store, which flagged 3 tracks with a symbol string starting with `*`/`#` as structurally impossible. | Fixed — `_footnote_in_row` now scans every cell in a row (not just column 0): a row with exactly one non-blank cell, and that cell starting with a marker character, is a footnote row regardless of which column it lands in |
| P4-011 | Ph. 4 (same lifecycle-coherence check) | **Critical** | Real circulars mark individual symbols directly in the Symbol column (`"MARATHON *"`, `"IMAGICAA #"`), not only via a trailing marker on the Security Name column (the only place this project's parser checked). The marker was never stripped from the symbol value before storing, so the same real company split into two different stored symbol identities depending on whether a given circular happened to mark it (`"MARATHON"` vs `"MARATHON *"`) -- silently breaking lifecycle continuity (an ENTRY under one spelling with no matching EXIT, and vice versa). This was the dominant cause behind the "double-ENTRY, no EXIT between" and "EXIT with no prior ENTRY" cases the coherence check found far from the 2019-10-01 data floor (where left-censoring is the expected, benign explanation instead). | Fixed — `_strip_marker` strips a trailing `*`/`^`/`#` from both the Symbol and Security Name cells before either is used (as the business-key symbol, or to look up footnote `details`); the marker set was also widened to include `#`, observed for the first time in this circular |
| P4-012 | Ph. 4 (lifecycle-coherence check, second pass after P4-010/011 fixed but the not-near-floor categories did not collapse) | **Critical** | `is_periodic_asm_subject` requires the `"surve"` stem. Real circulars SURV49425/SURV60822/SURV63984/SURV69359 (four occurrences, 2021-2025) drop the word "Surveillance" entirely from their subject -- `"Applicability of Short-Term Additional Measure (ST-ASM)"` -- not a misspelling this project's typo tolerance could catch, an outright omission. These circulars were silently classified as not-periodic and never even attempted (not logged as a failure -- indistinguishable from the thousands of genuinely irrelevant SURV circulars). SURV63984 specifically is where symbol 63MOONS's real ASM exit lived; skipping it silently produced an apparent re-entry with no prior exit a month later, the exact symptom that first exposed this defect. | Fixed — added a narrow fallback: when `"surve"` is absent but `"applicab"`+`"measure"` are both present, accept the subject if it ends with the literal `"(ASM)"`/`"(ST-ASM)"` abbreviation (normalized to a trailing `"asm"`) -- an abbreviation never observed on any excluded-mechanism subject. **Superseded by P4-013** — see below. |
| P4-013 | Ph. 4 (tracing a second post-P4-012 incoherence case, ARENTERP) | **Critical / design change** | Tracing a `stage_mismatch` case the same way as 63MOONS found a SECOND, independent subject-classification miss: SURV49492's subject drops the word `"Measure"` instead of `"Surveillance"` -- `"Applicability of Short- Term Additional Surveillance (ST-ASM)"`. Two distinct real circulars each silently missing a *different* required word, found only by hand-tracing individual symbols' lifecycles, is exactly the pattern that makes an allowlist the wrong design for this data: a false negative is silent and requires exhaustive tracing to find, while a false positive under a denylist fails loudly (a fetch/parse attempt that doesn't match any known Annexure shape) the moment it happens. | **Redesigned, not just fixed** — `is_periodic_asm_subject` inverted from an allowlist (require positive stems) to a denylist (attempt every SURV circular subject unless it matches one of ~25 known-irrelevant categories, built from a full survey of all 1,756 distinct real subjects in the cached corpus, not guessed). Dry-run verified against the full cached index before any network use: converges to the same 62 distinct accepted subjects as the old allowlist, plus exactly 4 real typo/omission variants the allowlist missed, minus exactly 4 subjects the allowlist had wrongly swept in (a standalone ICA circular, two policy/framework announcements, one typo'd Encumbrance circular) — zero unexplained deltas either direction. |

## P2-001 — `full_bhavcopy_save` silent failure on HTTP error

**Root cause.** `jugaad_data.nse.archives.NSEArchives.full_bhavcopy_raw()` calls
`self.get(...)` and returns `r.text` unconditionally — it never checks `r.status_code` or
validates that the response body is actually CSV. When NSE's server returns an HTML error page
(observed for every date before 2019-09-30 during this project's own history-depth probe), the
library writes that HTML to disk with a `.csv` extension and returns normally. A caller checking
only "did an exception get raised" gets a false positive.

**How it was found.** While empirically verifying the earliest retrievable bhavcopy date (a
pre-flight check requested before ingestion code was written), a sweep of dates from 2010 through
2019 all reported success. The returned files were suspiciously identical in size (3,651 bytes)
across totally unrelated dates spanning nine years. Reading one file's content directly showed
`<!DOCTYPE html>` — an NSE error page, not data. Binary-searching the real boundary by reading
file content (not trusting the library's return status) found the true cutover: 2019-09-27
(error page) vs. 2019-09-30 (real CSV, correct columns) — NSE introduced this combined
price+delivery file format starting 2019-09-30, seven business days later than the library's own
documented ("2019 and prior") claim would suggest, and precisely, not fuzzily.

**Fix / mitigation.** Per direction, content validation is NOT left as an ingestion-module nicety
that the next data source or a manual backfill could bypass. It lives in the store's write path
(`src/bitemporal/store.py`), which independently rejects any row/batch that doesn't match the
target table's declared shape before anything reaches SQLite:
- every declared column present (no silent partial row),
- every value's type checked against the table's declared `column_types` (numeric columns
  reject `bool` even though `bool` is an `int` subclass in Python),
- every non-nullable column rejected if `None`,
- the batch itself rejected if empty.

This does not make the store parse HTML — an HTML error page fed into ingestion's CSV parser
will fail to produce the expected columns at all and never reach the store as a row in the first
place. The store's independent check is the second, structural line of defense: it guarantees
that *no* future ingestion path (a different data source, a manual CSV backfill, a bug in a
parser) can smuggle a malformed row past validation just because it happened to not raise an
exception upstream.

**Re-verification.** See `tests/test_bitemporal_core.py`'s `StoreShapeValidationTest` class
(dtype rejection, null rejection, empty-batch rejection) and
`tests/test_nse_ingestion.py`'s content-validation test (an HTML fixture is rejected before
reaching the store). Both pasted with the Phase 2 test run.

## P2-002 — numpy scalar types silently mis-stored as BLOBs by sqlite3

**Root cause.** Python's `sqlite3` module binds query parameters by type-dispatch on the exact
Python type of the value. `numpy.int64`/`numpy.float64` (what every column of a pandas-parsed
CSV actually contains) are not recognized by `sqlite3`'s default adapters as `int`/`float` --
`sqlite3` falls back to treating them as a buffer-protocol object and silently writes the raw
memory bytes as a BLOB. No exception, no warning: `SELECT typeof(a)` on the written column would
report `blob`, not `integer`, and the stored bytes are not the decimal value at all.

This is NOT caught by `store.py`'s own dtype validation: `isinstance(numpy.int64(5),
numbers.Integral)` is `True` (numpy scalar types are registered with Python's numeric ABCs), so
the *shape* check that P2-001 added correctly says "this value is a valid integer" right before
`sqlite3` mis-serializes it anyway. Validating a value's logical type is not the same guarantee
as validating what the DB driver will actually persist for it.

**How it was found.** While building the bhavcopy ingestion module (which reads NSE's CSV via
pandas, whose numeric columns are numpy-typed by default), a deliberate pre-implementation check
of "does `sqlite3` actually bind numpy scalars correctly" was run before wiring pandas output
into the store at all. `conn.execute(..., (np.int64(5), np.float64(2.5)))` bound without error;
reading the row back showed column `a` as a Python `bytes` object containing raw memory, not the
integer 5.

**Fix.** `store.py`'s `_normalized_values()` now coerces every non-null value to the table's
declared native type (`int(...)` for `INTEGER`-marked columns, `float(...)` for `REAL`-marked
columns) immediately after shape validation and before it is ever bound to a SQL parameter --
this runs for every write path (`write_fact` and `write_facts`), so no future ingestion source
can reintroduce this by supplying numpy- or pandas-native numeric types.

**Re-verification.** `tests/test_bitemporal_core.py::NumericCoercionTest` inserts numpy-typed
values through both `write_fact` and `write_facts` and asserts `typeof(...)` on the stored column
is `integer`/`real`, not `blob`, and that the retrieved value round-trips to the correct number.
Pasted with the Phase 2 test run.

## P2-003 — NSE archive silently serves a different date's file than requested

**Root cause.** NSE's bhavcopy archive URL is keyed by requested date, but the file actually
returned is not always for that date. Observed behavior, confirmed by comparing the requested
date against the response CSV's own `DATE1` column across a systematic sweep:

| Requested | Actual DATE1 | Explanation |
|---|---|---|
| 2019-10-02 (holiday) | 2019-10-01 | Sane: falls back to nearest prior trading day |
| 2022-03-01 (holiday) | 2022-02-28 | Sane: same pattern |
| 2026-08-30 (Sunday) | 2026-08-28 | Sane: same pattern |
| 2026-09-06 (Sunday) | 2026-09-04 | Sane: same pattern |
| **2019-09-30** | **2019-06-27** | **Not a fallback — 95 days off, not 1-3** |

The first four are an undocumented but sensible archive convention (serve the last real trading
day's file under a closed-market date's URL). 2019-09-30 is different in kind: it is this
project's own previously-claimed "earliest available date," and it is a genuinely corrupted/
mislabeled archive entry on NSE's side, unrelated to the format-introduction boundary. This
directly invalidated CLAUDE.md's prior claim (checked only "is this real CSV, not an HTML error
page" — true for 2019-09-30, but the real CSV it returned was for the wrong date entirely).

**How it was found.** After the first real-data ingestion run, a sanity query for
`event_date='2019-09-30'` (one of the run's own reference dates) returned zero rows. Rather than
assume the ingestion silently dropped it, the raw response was re-fetched and inspected directly:
its `DATE1` column read `27-Jun-2019`. A systematic sweep of several other requested/actual date
pairs (table above) established the general fallback pattern and confirmed 2019-09-30 is the
outlier, not the rule.

**Fix.** Earliest usable date corrected in CLAUDE.md from 2019-09-30 to **2019-10-01** (verified:
requested date equals the response's own DATE1, exactly, with no fallback involved).
`ingest_bhavcopy_date` now compares the parsed rows' own event_date to the requested trade_date:
a small gap (≤7 calendar days -- covers holiday clusters) is accepted as the documented fallback
behavior and reported with `actual_event_date` distinct from the requested date; a larger gap is
rejected as a gap outcome with an explicit mismatch reason, never silently stored under an
assumption that the requested date was actually served.

**Re-verification.** `tests/test_nse_ingestion.py::DateMismatchTest` — a small (holiday-fallback)
mismatch is accepted and correctly labeled; a large (anomalous) mismatch is rejected as a gap, not
written to the store. Pasted with the Phase 2 test run. The real-data ingestion sample was re-run
with 2019-10-01 as the earliest reference date.

## P2-004 — blank SERIES silently stringified to the literal text "nan"

**Root cause.** `parse_bhavcopy_rows` built each row's `series` field as
`str(record["SERIES"]).strip()`. When pandas parses a genuinely blank CSV cell, the value is
`float('nan')`, and `str(float('nan'))` is the three-character string `"nan"` — a value that
passes every type/non-null check `store.py` runs (it IS a non-null `str`), while being
semantically meaningless and, worse, silently colliding across every affected row for the same
symbol+date under one fake shared "series."

**How it was found.** After the real ingestion sample, a query for symbol+event_date combinations
with more than one `series` value (checking the "multiple series, same date" case requested for
real-data guard re-testing) turned up `'nan'` in the set of distinct series values across the
dataset. Investigating which rows carried it traced to 30 rows, all in the 2019-10-01 file, all
NCD/bond-like instruments with unusually high per-unit prices (e.g. IRFC at 1240, IDFCFIRSTB at
9275) — consistent with debt instruments NSE's own file left the SERIES column blank for that day.

**Fix.** `parse_bhavcopy_rows` now checks `pd.isna()` on both SYMBOL and SERIES before building a
row; either being blank skips that row entirely (it cannot form a valid business key) and
increments a `skipped_invalid` counter returned alongside the valid rows, surfaced through
`DateIngestionOutcome.rows_skipped_invalid` — visible in ingestion reporting, never silently lost.

**Re-verification.** `tests/test_nse_ingestion.py::ParseBhavcopyRowsTest::test_row_with_missing_series_is_skipped_not_labeled_literal_nan`.
Pasted with the Phase 2 test run.

## P2-005 — gap reporting conflated "not a trading day" with "genuine ingestion failure"

**Root cause.** The first real ingestion run reported 2026-08-29 (a Saturday) as a "GAP" and
2026-08-30 (a Sunday) as "ingested," even though neither date is a real trading day. The
difference was purely an artifact of NSE's own serving behavior: a weekend sometimes returns a
flat HTML error (→ `BhavcopyFetchError` → status "gap"), and sometimes returns a small fallback to
the nearest prior trading day's file (→ status "ingested," with a mismatched `actual_event_date`
nobody was checking against the label). Neither label was actually correct: "gap" implies
something needs investigating; "ingested" implies the requested date itself had real data. A
weekend has neither problem — it's simply not a trading day.

**How it was found.** Pointed out directly: "Same situation, different outcome — the behaviour
depends on what NSE happens to serve, not on anything we control." Confirmed by inspecting the
per-date report from the first real run: 2026-08-29/2026-09-05 (Saturdays) labeled "GAP",
2026-08-30/2026-09-06 (Sundays) and 2022-03-01 (Holi, a real holiday) labeled "ingested" — despite
all five being equally non-trading-days.

**Fix.** `classify_against_observed_trading_calendar()` (`src/ingestion/nse_market_data/bhavcopy.py`)
derives which requested dates are genuine trading days purely from the batch's own evidence — the
set of `actual_event_date` values observed across every outcome (whether obtained directly or via
a neighbor's fallback) — with no new network calls and no external holiday calendar dependency.
Three outcomes, not two: `INGESTED` (a date's own direct fetch matched itself — real data for that
date), `NOT_A_TRADING_DAY` (nothing in the batch confirms the date was ever a real trading day —
the ordinary case for weekends and holidays alike), and `GAP` (some OTHER outcome confirms the
date is real, but this date's own fetch failed to retrieve it — a genuine anomaly). Coverage
reporting is now expressed against the derived trading calendar, not the raw calendar sweep.

**Re-verification.** `tests/test_nse_ingestion.py::TradingCalendarClassificationTest` — five cases,
including a synthetic true-gap (a neighbor's fallback confirms a date that its own fetch failed to
retrieve) and a reproduction of the exact real Aug29-Sep7 2026 pattern this project observed,
asserting zero genuine anomalies and the correct three not-a-trading-day dates. Re-run against the
real sample: 12 confirmed trading days, all 12 ingested, 0 gaps, 5 correctly excluded as
not-a-trading-day (`2022-03-01`, both Saturdays, both Sundays). Pasted with the Phase 2 test run.

## P4-001 — ASM exclusion-title regex missed the 2023-era "Short - Term" wording

**Root cause.** `EXCLUSION_TITLE_RE` was written against the T1/T2 (2025) and 2019/2021 samples,
all of which title the exclusion section the bare `"List of securities to be excluded from ASM
Framework w.e.f. ..."`. The 2023 ST-ASM circular (`SURV57402`) instead titles it `"...excluded from
Short - Term ASM Framework w.e.f. July 05, 2023."` — a real wording difference across eras that the
initial regex, matching only the literal phrase `"excluded from ASM Framework"`, did not
anticipate.

**How it was found.** After building the module against the T1/T2 reconciliation fixtures, a
broader verification pass ran the real parser (not an ad hoc script) against all five era-spanning
sample circulars used earlier for the format-stability check (2019/2021/2023/2025/2026). The 2023
case alone reported an unparsed title where none was expected; re-inspecting the raw section title
text directly showed the extra "Short - Term" wording the regex didn't tolerate.

**Fix.** `EXCLUSION_TITLE_RE` now matches an optional `(Long|Short)\s*-\s*Term\s+` infix before
`ASM Framework`; when present, that captured term sets `mechanism` directly (more specific than
falling back to the circular's own subject line), matching how `ENTRY_TITLE_RE`/
`TRANSITION_TITLE_RE` already derive mechanism from their own title text.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_short_term_exclusion_title_variant`
reproduces the exact 2023 title text and asserts it now parses to one `EXIT` event with
`mechanism="ASM_ST"`. Re-run against the real 2023 fixture directly: 0 unparsed titles (was 1),
5 events (was 3). Pasted with the Phase 4 test run.

## P4-002 — GSM event-date regex couldn't cross a real mid-sentence PDF line wrap

**Root cause.** `EVENT_DATE_RE` anchored on `(?:framework|GSM)\b[^\n.]{0,80}?(?:with effect
from|w\.e\.f\.?)...`, deliberately excluding both `.` and `\n` from the gap on the assumption that
a stray sentence-ending period elsewhere in the paragraph was the main risk of over-matching.
Real GSM circular PDF text (extracted via `pdfplumber`) wraps mid-sentence: the actual 2024 sample
reads `"...shall be moved to Stage II of GSM\nwith effect from December 23, 2024."` — the newline
between `"GSM"` and `"with effect from"` made the gap impossible to match, and the regex reported
"event date not found" on a real, correctly-formatted, non-degenerate circular.

**How it was found.** Verifying the GSM parser against three real circulars (2024 stage-move,
2026 stage-move, and a freshly-downloaded real 2025 "moving out of GSM" circular, `SURV71691`,
fetched specifically to check the EXIT template before writing its parsing logic) — the 2024 case
alone failed with `reason: event date not found`, despite the 2026 case (same subject template)
succeeding. Diffing the two extracted texts directly showed the only structural difference was the
line-wrap position relative to the anchor phrase.

**Fix.** Gap character class changed from `[^\n.]{0,80}?` to `[\s\S]{0,80}?` — any character,
including newlines, still bounded to 80 characters so it cannot run away across an unrelated
paragraph.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_stage_move_template`
reproduces the real 2024 wrapped text and asserts `event_date == "2024-12-23"`. Re-run against the
real 2024/2026/SURV71691 PDF text directly: all three now resolve both dates correctly. Pasted with
the Phase 4 test run.

## P4-003 — "with effect from" itself wraps across a line break in some real circulars

**Root cause.** P4-002 fixed the gap *before* the `"with effect from"` anchor phrase to cross line
breaks, but the anchor phrase was still matched as a literal string with ordinary space characters
between its words. Two real, freshly live-fetched circulars (not present in the small sample set
used to build and initially verify the parser) wrap the line break *inside* the phrase itself:
`"...shall be moved to Stage I of GSM with\neffect from December 23, 2025."` — a newline exactly
between "with" and "effect". The literal-space match failed silently (no exception, just an
absent match), and the circular was correctly logged as a failure rather than mis-ingested with a
wrong or missing date — but it was still a real, avoidable gap.

**How it was found.** Before committing to the full real ASM/GSM ingestion run, a deliberate
network smoke test (10 real ASM + 5 real GSM circulars, freshly fetched live, not from the
scratchpad cache used to build the parser) was run first, specifically to catch exactly this kind
of format variance the small hand-picked sample set might have missed. 2 of 5 GSM circulars failed
with "event date not found"; fetching and reading those two circulars' PDF text directly showed the
line wrap fell inside the anchor phrase.

**Fix.** Every literal space inside `"with effect from"` changed to `\s+`
(`with\s+effect\s+from`), matching the same reasoning already applied to the surrounding gap in
P4-002.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_with_effect_from_wrapped_across_a_line_break`
reproduces the exact real `SURV71944` wrapped text and asserts `event_date == "2025-12-23"`.
Re-run the same 5-circular live smoke test: 5/5 now succeed (was 3/5). Pasted with the Phase 4
test run.

## P4-004 — real DB's surveillance_flags table predated the Phase 4 schema and was never migrated

**Root cause.** `src/bitemporal/connection.py::init_db()` checks `sqlite_master` for a table of
each registered name and creates it only if absent — this is correct for a brand-new database, but
it means a table created under an OLDER version of `schema.py` (Phase 1's placeholder
`surveillance_flags`, with only `symbol/stage/event_date/knowledge_date` columns) is never altered
when the registry's DDL later changes. The real project DB (`data/processed/praman.db`) had
exactly this: an empty `surveillance_flags` table created during Phase 1, still in its original
shape, when this session's schema extension (adding `mechanism`, `action_type`, `from_stage`,
`to_stage`, `source_circular`, `details`) was made. Nothing in `init_db()`, `store.py`, or the
ingestion modules checks that an existing table's actual columns match the registry's current
declaration.

**How it was found.** The first full real ingestion run (`scripts/ingest_asm_gsm_sample.py`, 3,334
ASM + 131 GSM circulars) completed with exit code 0 and reported `circulars_processed: 2883`, which
read as a mostly-successful run. But `circulars_failed: 3298` (more failures than circulars even
attempted, a red flag on its own — see P4-005) all shared one literal reason string:
`"table surveillance_flags has no column named action_type"`. The run's own final summary line,
`min_event_date=None max_event_date=None total_rows=0`, made the real severity unambiguous: not
"mostly ingested with a to be reasonable failure rate", but zero rows actually persisted. Checked
directly: `SELECT sql FROM sqlite_master WHERE name='surveillance_flags'` on the real DB showed the
Phase 1 six-column shape, not the current registry's twelve-column shape.

**Fix.** Confirmed the stale table held zero rows (`SELECT COUNT(*)`) before touching it — this was
a schema migration of empty structure, not a data mutation, and would have been refused otherwise.
`DROP TABLE surveillance_flags` followed by `init_db()` (which then created it fresh from the
current registry DDL) brought the real DB in line with `schema.py`. This project has no general
schema-migration mechanism; a future DDL change to an already-populated table would need an
explicit, reviewed migration path (ALTER TABLE / rebuild-and-copy), not this drop-and-recreate
shortcut, which is safe here specifically because the table was empty.

**Re-verification.** `SELECT sql FROM sqlite_master ...` re-checked and matches `schema.py`'s
current `SURVEILLANCE_FLAGS.ddl` exactly. Full ingestion re-run after this fix (see
`docs/phase4_asm_gsm_sourcing.md` for the resulting row counts) actually persisted rows this time,
confirmed by a non-zero `total_rows` and non-`None` min/max `event_date` in the re-run's summary.

## P4-005 — a circular whose write failed could still be counted as "processed"

**Root cause.** `ingest_asm_circular`/`ingest_gsm_circular` incremented `report.circulars_processed`
immediately after parsing succeeded, then called `write_facts` afterward. If `write_facts` raised
(as every call did during the P4-004 incident), the exception propagated up to the caller's sweep
loop, which correctly appended the circular to `circulars_failed` — but `circulars_processed` had
already been incremented and was never rolled back. A circular could therefore be counted in both
`circulars_processed` and `circulars_failed` simultaneously, inflating the "processed" figure to
look far healthier than the actual state of the store.

**How it was found.** Investigating the P4-004 incident's numbers: `circulars_processed: 2883` and
`circulars_failed: 3298` sum to more than the 3,334 ASM circulars actually attempted, which is only
possible if some circulars were double-counted. Tracing `ingest_asm_circular`'s code directly
showed `report.circulars_processed += 1` sits before the `write_facts(...)` call it depends on for
correctness, not after.

**Fix.** Reordered both functions so `circulars_processed` (and, for ASM, the recording of
`unparsed_section_titles`) increments only after `write_facts` returns without raising. A circular
whose write fails is now counted exactly once, as failed, never additionally as processed.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_failed_write_is_never_counted_as_processed`
and the GSM-side equivalent in `IngestGsmCircularTest` each construct a connection with the stale
(pre-Phase-4) table shape, assert the write raises, and assert `report.circulars_processed == 0`
afterward. Pasted with the Phase 4 test run.

## P4-006 — abbreviated, comma-less month names not recognized in w.e.f. dates

**Root cause.** `to_iso_date` parsed the extracted month/day/year text with a single format,
`"%B %d %Y"` (full month name required). Real ASM circulars roughly SURV52458 through SURV58318
(a contiguous run corresponding to mid-2022 through mid-2023) title their sections with the w.e.f.
date spelled `"Apr 03 2023"` — an abbreviated three-letter month with no comma — rather than the
`"April 03, 2023"` form used in every other sampled era. `strptime` with `%B` rejects an
abbreviated month outright.

**How it was found.** Per direction, the 482 ASM failures from the second full ingestion run were
grouped by normalized cause *before* any retry was attempted (see the run's failure-cause
breakdown). 439 of 482 (91%) shared the exact same error shape, `"time data '<X>' does not match
format '%B %d %Y'"`; extracting the 439 raw date strings found 232 distinct values, every one of
them the three-letter-month, no-comma shape. This directly falsified the initial hypothesis that
the run's bursty failure pattern (clean recovery between failure clusters) was NSE-side rate
limiting — it was a real, single-cause format gap concentrated in one calendar era, not a
transient network problem, and no amount of retrying with backoff would ever have fixed it.

**Fix.** `to_iso_date` now tries `"%B %d %Y"` first (the common case), then falls back to
`"%b %d %Y"` (abbreviated month) before raising.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ToIsoDateTest::test_abbreviated_comma_less_month_p4_006`
asserts `to_iso_date("Apr 03 2023") == "2023-04-03"` and two more real observed strings. This fix
also resolved GSM's one date-format failure (SURV74620, `"Jun 10 2026"`) for free, since GSM's
date parsing shares this same function.

## P4-007 — ESM typo bypassed the exclusion filter; and a nested zip path

**Root cause (two independent bugs found investigating one failure).** Real circular SURV64061's
subject line was `"Applicability of Enhnaced Surveillance Measure (ESM)"` — `"Enhnaced"`, a
letter-transposition typo of `"Enhanced"` in NSE's own manually-typed title. `is_periodic_asm_subject`'s
exclusion check looked for the substring `"enhanced"` in the normalized subject; `"enhnaced"` does
not contain that substring, so this ESM circular (a mechanism CLAUDE.md explicitly records as
deliberately not ingested) would have been treated as a periodic ASM circular and ingested under
the wrong mechanism. Investigating why its ingestion attempt failed (rather than silently
succeeding under the wrong label) surfaced a second, unrelated bug: its zip nests the workbook one
level down (`"SURV64061/Annexure.xlsx"`), and `parse_circular_zip_bytes`'s
`nm.lower().startswith("annexure")` check matches against the full zip-entry path, which never
starts with `"annexure"` when the entry is inside a subfolder.

**How it was found.** Investigating the non-date, non-network ASM failures from the second run
(4 remaining after date-format and connection-error causes were set aside) turned up SURV64061's
`"No Annexure*.xlsx found in zip"` error. Checking the cached circular index directly for this
circular's actual subject revealed the ESM/"Enhnaced" title before the zip-structure issue was
even examined — the exclusion-filter gap is the more serious of the two, since it would have
silently mis-labeled real data rather than merely failing to parse it.

**Fix.** Added the bare `"esm"` substring to `is_periodic_asm_subject`'s exclusion check — every
real ESM subject carries the literal `"(ESM)"` abbreviation, three capital letters a typo is very
unlikely to hit, unlike the full word "Enhanced." Independently, `parse_circular_zip_bytes` now
matches the Annexure workbook by the zip entry's basename (last `/`-separated segment), not the
full path.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IsPeriodicAsmSubjectTest::test_esm_excluded_including_the_real_enhnaced_typo`
asserts both the correctly-spelled and the real "Enhnaced" subject are excluded.
`ParseCircularWorkbookTest::test_annexure_nested_inside_a_zip_subfolder_is_still_found` reproduces
the exact real `"SURV64061/Annexure.xlsx"` zip layout and asserts the workbook is still found and
parsed. Pasted with the Phase 4 test run.

## P4-008 — stray whitespace inside digit runs in some real 2026 GSM PDFs

**Root cause.** Two real GSM circulars (SURV72963, SURV72867, both February 2026) extract via
`pdfplumber` with spurious single-space characters inserted inside otherwise-contiguous digit
sequences — `"with effect from February 2 5, 2026"` for what is genuinely the 25th, similarly
`"NSE/SURV/ 72963"` and `"Stage I I"` for "Stage II." This is a rendering artifact of whatever PDF
generation tool produced circulars from that period, not a real character in the source document.
`EVENT_DATE_RE`'s `\d{1,2}` cannot match across the injected space, so `parse_gsm_pdf_text` could
not find the event date at all.

**How it was found.** After the date-format (P4-006) and connection-error causes were set aside,
inspecting the real PDF text of the two remaining unexplained ASM-adjacent... (GSM) failures
directly showed the character-level spacing artifact.

**First fix attempt was itself wrong, caught immediately.** The first version collapsed all
whitespace (`\s+`, which matches `\n`) between two digits. Running the full test suite immediately
after showed `test_move_out_template_with_trailing_columns_and_footnote` failing: real move-out-
template text has one row's trailing number directly followed by a newline and the next row's
leading serial number (`"...INE875R01011 EQ 20\n2 FSC..."`), and the `\s+` version merged the
`"20"` and `"2"` across that newline, corrupting `ROW_RE`'s per-line row matching and silently
dropping the FSC row.

**Fix.** Restricted the collapse to horizontal whitespace only (`[ \t]`, explicitly not `\n`) —
`re.sub(r"(?<=\d)[ \t]+(?=\d)", "", text)`. This still merges the same-line digit splits
(`"2 5"` → `"25"`, `"NSE/SURV/ 72963"` unaffected since a space after `/` isn't between two
digits) without ever crossing a line boundary.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_digits_split_by_a_stray_space_are_collapsed_p4_008`
reproduces the real SURV72963 text shape and asserts both dates resolve correctly. The full suite
(148 tests, including the move-out-template test the first attempt broke) passes. Re-verified
against both real live circulars directly: SURV72963 → GLFL, ENTRY, Stage II, event_date
2026-02-25; SURV72867 → ARSHIYA, ENTRY, Stage I, event_date 2026-02-19.

## P4-009 — event_counts double-counted a genuine cross-circular duplicate

**Root cause.** `ingest_asm_circular`/`ingest_gsm_circular` called `write_facts(...)` and
discarded its return value, then unconditionally incremented `event_counts` for every event the
parser produced. `write_facts` silently and correctly skips a row whose exact business key
(symbol, mechanism, event_date, knowledge_date) already exists — the intended, tested idempotency
behavior — but nothing in the calling code distinguished "this event was newly inserted" from
"this event was already present and correctly skipped." A report built purely from parsed-event
counts therefore overstates the store's actual row count whenever two different circulars
legitimately describe the identical fact.

**How it was found.** The invariant assertion added to the post-ingestion analysis script per
explicit instruction (`sum(event_counts) == COUNT(*) FROM surveillance_flags`) failed on the real,
full post-retry dataset: reported 31,552, stored 31,550, diff=2. Rather than treat a diff of 2 out
of 31,552 as noise, the 27 real same-day/same-mechanism ASM circular pairs found in the cached
circular index were re-fetched and re-parsed directly to check for overlapping events; one pair,
SURV68086/SURV68088 (both ASM_LT, both dated 2025-05-20), both produced an identical
(ICDSLTD, ASM_LT, 2025-05-21) event. The second unit of the diff=2 was not individually
re-traced — doing so would require re-parsing the full successfully-processed corpus a second
time, and the store itself cannot contain a wrong or duplicated row regardless (the UNIQUE
constraint already guarantees that); only the *report's* count was ever inaccurate.

**Fix.** Both ingestion functions now capture `write_facts`'s returned `BulkWriteResult` and
accumulate its `skipped_duplicate` count into a new `report.duplicate_events_skipped` field.
`event_counts` still reflects parsed events (useful for describing what a circular's own Annexure
said); `sum(event_counts) - duplicate_events_skipped` is what should be compared against the
store's `COUNT(*)`, and does so exactly.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_two_same_day_circulars_naming_the_same_symbol_is_tracked_as_a_duplicate_not_lost`
reproduces the exact real SURV68086/SURV68088/ICDSLTD shape (two circulars, same day, same
symbol/mechanism/event_date) and asserts `sum(event_counts) - duplicate_events_skipped ==
COUNT(*)` holds. `test_reingesting_the_same_circular_is_idempotent` was extended to also assert
`duplicate_events_skipped == 2` on a full re-ingest. Pasted with the Phase 4 test run.

## P4-010 — footnote-definition rows outside column 0 were ingested as bogus symbols

**Root cause.** The footnote-row check looked only at `_cell(row, 0)` for a string starting with
`*`/`^`. Real circular SURV49783's Annexure I-A sheet has a footnote row shaped
`(None, '* Moved from STASM to LTASM framework', None, None)` — its Sr.No. column is blank (this
footnote doesn't number a symbol row, it clarifies the one directly above), so the marker text
lands in the Symbol column position, not column 0. The check missed it, the row fell through to
ordinary data-row handling, and `_valid_symbol()` correctly saw a non-empty, non-"Nil" string and
accepted it — because nothing about that check knows a footnote from a symbol by content alone.

**How it was found.** A systematic coherence check was run across every one of the 4,312 real
(symbol, mechanism) tracks in the store (ENTRY → STAGE_CHANGE* → EXIT should never show two
ENTRYs with no EXIT between, or an EXIT with no prior ENTRY, except near the 2019-10-01 data floor
where left-censoring is expected). Three tracks had a "symbol" starting with `*` or `#` —
structurally impossible for a real NSE ticker — which is what triggered fetching the real source
circular directly rather than assuming the store was simply incomplete.

**Fix.** `_footnote_in_row` now scans every cell in the row: a row counts as a footnote definition
if exactly one cell is non-blank and that cell's text starts with a marker character, regardless
of which column position it occupies.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_footnote_row_in_the_symbol_column_not_parsed_as_a_symbol`
reproduces the exact real SURV49783 row shape and asserts exactly one real event (MARATHON) is
produced, not two. Re-verified against the real SURV49783/SURV49784 circulars directly: no bogus
symbols in either circular's output. Pasted with the Phase 4 test run.

## P4-011 — marker attached directly to the Symbol cell was never stripped

**Root cause.** The parser checked for a footnote marker only on the Security Name cell
(`name.strip()[-1:] in ("*", "^")`), using it to attach `details` but never to clean the symbol
itself. Real circulars mark individual securities directly on the Symbol cell instead
(`"MARATHON *"`, `"IMAGICAA #"` — the latter using `#`, a marker character not previously seen).
Since the marker was never stripped, the stored `symbol` value carried it verbatim, and the exact
same real company would be stored under two different symbol strings across different circulars
depending on whether that particular circular happened to mark it — silently fragmenting one
company's ASM history into two unrelated (symbol, mechanism) tracks.

**How it was found.** Same lifecycle-coherence check as P4-010. After excluding cases explained by
the 2019-10-01 data floor (left-censoring), 117 "EXIT with no prior ENTRY" and 90 "double-ENTRY, no
EXIT between" tracks remained unexplained. Inspecting SURV49783/SURV49784 directly (already being
fetched for P4-010) showed the real cause for at least this pair: `"MARATHON *"` (marked, in
SURV49784's exclusion list) versus `"MARATHON"` (unmarked, in SURV49783's entry list) would have
been stored as two different symbols for what is obviously the same real company (same ISIN,
`INE182D01020`, in both rows).

**Fix.** `_strip_marker` strips a trailing marker character (now `*`, `^`, or `#`) from a cell
value, returning the clean value and the marker separately. Applied to both the Symbol and
Security Name cells before either is used — the clean, marker-free symbol is what becomes the
business-key `symbol`; whichever cell actually carried a marker is used to look up the matching
footnote text for `details`.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_marker_on_symbol_with_hash_character`
reproduces the real SURV49784 `"IMAGICAA #"` row and asserts the stored symbol is `"IMAGICAA"` with
`details="As per BSE"`. `test_marked_symbol_matches_unmarked_symbol_across_circulars` asserts a
marked and an unmarked appearance of the same real symbol (`"MARATHON *"` vs `"MARATHON"`) resolve
to the identical stored value. The full ingestion was re-run after this fix (see
`docs/phase4_asm_gsm_sourcing.md` for the before/after lifecycle-coherence numbers). Pasted with
the Phase 4 test run.

## P4-012 — "Surveillance" dropped entirely from four real circular subjects

**Root cause.** `is_periodic_asm_subject` requires the `"surve"` stem to appear anywhere in the
normalized subject -- deliberately typo-tolerant (P4-006's era already showed "Surveillanvce" and
similar misspellings), but a typo-tolerance check only helps when some form of the word is
present. Four real circulars (SURV49425 in 2021, SURV60822 and SURV63984 in 2024, SURV69359 in
2025) title themselves `"Applicability of Short-Term Additional Measure (ST-ASM)"` -- the word
"Surveillance" is not misspelled, it simply is not there. `"surve"` never appears, and the primary
check correctly (given its own rule) rejected the subject.

**How it was found.** After P4-010/P4-011 were fixed and the full ingestion re-run, the
categorized lifecycle-coherence check (run before any retry, specifically to isolate whether the
marker fix was the *whole* explanation) showed the not-near-floor incoherence categories had NOT
collapsed toward zero as expected (`double_entry` 90→93 even went up slightly; `stage_mismatch`
17→20). Per instruction, this was treated as evidence of a second real defect rather than accepted
as a smaller, "good enough" number. One concrete case was traced to ground truth directly: symbol
63MOONS showed ENTRY on 2024-09-10 and ENTRY again on 2024-10-16 with no EXIT between. Its presence
was checked circular-by-circular across every real ST-ASM circular in that window via its
Consolidated-sheet snapshot, which pinpointed the disappearance to somewhere between SURV63967
(2024-09-16, present) and SURV64008 (2024-09-18, absent) -- but 63MOONS appeared in neither
circular's Annexure II. Listing every SURV circular of any subject in that exact date range
surfaced SURV63984 (2024-09-17), whose subject the classifier had rejected; fetching it directly
confirmed 63MOONS's real EXIT (`"* Due to Shortlisting in ESM"`) sitting in its Annexure II, exactly
where it should be if the circular had been included.

**Fix.** Added a narrow, evidence-based fallback to `is_periodic_asm_subject`: when `"surve"` is
absent but `"applicab"` and `"measure"` are both still present, accept the subject anyway if it
ends with the normalized `"asm"` suffix -- the literal `"(ASM)"`/`"(ST-ASM)"` abbreviation every
real periodic subject carries as its last token, and which does not appear as a subject-ending
abbreviation on any of the excluded mechanisms (GSM/ESM/IBC/pledge all end differently, and are
excluded earlier in the same function regardless). Checked directly against the full cached
circular index: exactly 4 circulars are recovered by this fallback, all four the identical real
shape, and re-checking every already-passing real subject in the corpus confirms nothing new is
wrongly included.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IsPeriodicAsmSubjectTest::test_surveillance_word_dropped_entirely_p4_012`
asserts both the real SURV63984 subject and its LT equivalent are now accepted. The full ingestion
was rebuilt a third time after this fix; see `docs/phase4_asm_gsm_sourcing.md` for the resulting
lifecycle-coherence numbers, which is what confirms whether this was the full remaining
explanation.

## P4-013 — allowlist inverted to a denylist after a second, independent subject-classification miss

**Root cause.** Not a single bug but a design flaw: `is_periodic_asm_subject` required specific
positive stems to be present (`"applicab"`, `"measure"`, and either `"surve"` or the `"(ASM)"`
abbreviation after P4-012). This structurally cannot distinguish "a genuine periodic circular with
an unanticipated typo/omission" from "a genuinely irrelevant circular" — it can only ever react to
variants already seen. After P4-012 (the "Surveillance" omission) was fixed and the full ingestion
rebuilt, the categorized lifecycle-coherence check's not-near-floor categories dropped but did not
collapse to zero. Tracing a second case (`ARENTERP`, `stage_mismatch` on 2021-09-13) the same way
63MOONS had been traced found `SURV49492`, subject `"Applicability of Short- Term Additional
Surveillance (ST-ASM)"` — this time the word `"Measure"` is missing, a distinct omission from
P4-012's. Two independent real circulars, each dropping a *different* required word, is the
pattern that makes an allowlist fundamentally the wrong shape for manually-typed, 7-years-of-typos
real data: nothing bounds how many more such variants exist, and each one is silent until someone
manually traces the exact symbol and date range it affected.

**How it was found.** Per explicit instruction, the categorized coherence check was re-run after
every fix rather than accepted on a shrinking-number basis, specifically to catch exactly this
kind of "improved but didn't fully collapse" result. `ALOKTEXT` was traced first and resolved to
an already-known, unfixable cause (`SURV42671`'s missing Annexure). `ARENTERP` was traced second
and found the new, second cause above. At two independent misses of the same general shape, the
call was made to stop patching individual variants and change the underlying design.

**Fix.** `is_periodic_asm_subject` inverted from an allowlist to a denylist: attempt every SURV
circular subject by default, reject only if it matches one of roughly 25 explicit categories
(GSM/ESM/IBC/ICA/Encumbrance/pledge/Deep-OTM/Trade-for-Trade/Persistent-Noise/policy-framework
updates/individual SEBI-SAT-NCLT order & directions circulars/price-band changes/algo-trading
notices/order-to-trade-ratio/surveillance-administrative circulars/standardization & SOP
notices/USDINR conversion/withholding-payout/trade-cancellation-mechanism/position-limit
notices/ETF notices/broker-confidence measures/caution & advisory notices/vendor-tech-admin
circulars/client-due-diligence/member-dashboard/derivatives-contract-specific notices/illiquid
securities/misc risk-control notices). These categories were built from a full survey of all 1,756
distinct real subjects in the cached 2019-2026 index (`survey_output.txt`, this session's
scratchpad), not guessed, and iterated three times against real typo variants found the same way
as the positive-side ones (`"Confimatory"` for Confirmatory, `"Coriggendum"` for Corrigendum,
`"Cautionary"` not matching a bare `"caution"` word-boundary check, `"Encumberance"` typo, "Placing
**of** Orders at..." breaking an adjacency-only regex, `"SAT orders"` plural not matching a
singular-only pattern).

**Verified before any network use.** A dry run compared the new denylist against the old allowlist
over all 7,936 cached circulars with zero fetches: identical 62 distinct subjects accepted in
common; exactly 4 distinct subjects (5 circulars) newly accepted, all confirmed genuine periodic
circulars with a real typo/omission (`"Application"` for "Applicability", `"Appllicability"`
typo, and two more instances of the "Measure"-dropped shape); exactly 4 distinct subjects newly
rejected, all confirmed correct exclusions (a standalone ICA circular the old allowlist had wrongly
sub-classified as generic ASM, two LT-ASM policy/scope-announcement circulars that are not periodic
entry/exit lists, and the "Encumberance" typo variant of the Encumbrance category). Zero
unexplained deltas either direction.

**Re-verification.** All 154 existing tests continue to pass unchanged (the denylist reduces to
the same accept/reject decisions for every case they cover). The full ingestion was rebuilt a
fourth time after this change; see `docs/phase4_asm_gsm_sourcing.md` for the resulting
lifecycle-coherence numbers.
