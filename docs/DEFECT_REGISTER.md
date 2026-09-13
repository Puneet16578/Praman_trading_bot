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
