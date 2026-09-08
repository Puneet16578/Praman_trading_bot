# Phase 2 — NSE Market Data Ingestion (Bhavcopy)

## Pre-flight verification (before any ingestion code was written)

1. **Does `jugaad-data` expose delivery_qty/delivery_pct?** Yes — `full_bhavcopy_save()` /
   `NSEArchives.full_bhavcopy_raw()` return NSE's combined `sec_bhavdata_full_*.csv`, columns
   include `DELIV_QTY`/`DELIV_PER`, confirmed non-null against a real pull (2026-09-07, 3,520 rows).
2. **Earliest retrievable date?** Empirically determined by reading actual response content, not
   trusting the library's return status (this is what surfaced P2-001). Corrected twice during
   this phase — see below. **Final answer: 2019-10-01** (not 2019-09-30, see P2-003).

## What was built

- `src/ingestion/nse_market_data/bhavcopy.py`: fetches via `NSEArchives.full_bhavcopy_raw()`
  directly (not the high-level convenience wrapper, which discards the HTTP response), validates
  content (rejects HTML error pages, empty responses, wrong schema), derives `knowledge_date` from
  the response's own `Last-Modified` header converted to IST (NSE's bhavcopy carries no
  self-declared publication timestamp of its own — verified this is the best available source-
  derived signal), parses rows with pandas, and writes exclusively through
  `src.bitemporal.store.write_facts` — no direct SQLite connection anywhere in `src/ingestion/`
  (enforced by `tests/test_no_update_on_fact_tables.py::IngestionNeverOpensConnectionDirectlyTest`).
- `src/bitemporal/store.py` extended (not forked) with shape/dtype/null validation
  (`_check_row_shape`) and native-type coercion (`_coerce_native`), plus a bulk `write_facts()`
  with idempotent duplicate-skip semantics distinct from `write_fact()`'s raise-on-duplicate
  (intentional: a bulk re-ingestion hitting an already-recorded fact is the normal case, not a
  caller mistake).
- `scripts/ingest_bhavcopy_sample.py`: real-data ingestion + coverage report, re-runnable.
- `tests/test_nse_ingestion.py` (network-free, fixture-injected `fetch_fn`) and
  `tests/test_bhavcopy_real_data_guard.py` (skipped unless the real sample DB exists — never
  fixture-substituted to fake a pass).

## Defects found this phase (full detail in `docs/DEFECT_REGISTER.md`)

| ID | Summary |
|---|---|
| P2-001 | `jugaad_data`'s `full_bhavcopy_save`/`raw` reports success on an HTTP error page (HTML silently saved as `.csv`). Mitigated at the store layer (independent shape validation) per your direction, not only in ingestion. |
| P2-002 | `sqlite3` silently binds `numpy.int64`/`float64` as a raw BLOB, not caught by the store's `numbers.Integral`/`Real` type check (numpy scalars satisfy those ABCs). Fixed: store coerces to native `int`/`float` before binding. |
| P2-003 | NSE's archive can return HTTP 200 CSV for a **different date** than requested. Weekends/holidays sanely fall back ≤3 days to the last trading day; 2019-09-30 specifically returned data 95 days stale — invalidating this project's own earlier "earliest date" claim. Fixed: earliest date corrected to 2019-10-01; ingestion now checks response-date-vs-requested-date and rejects (as a gap) anything beyond a 7-day fallback window. |
| P2-004 | A real NSE file can have a genuinely blank `SERIES` for some rows (30 of 43,942, all NCD/bond instruments). Naive stringification turned this into the literal text `"nan"` — valid-looking, non-null, and silently corrupting the business key. Fixed: such rows are skipped and counted (`rows_skipped_invalid`), never mislabeled. |
| P2-005 | Gap reporting conflated "not a trading day" with "genuine ingestion failure": a Saturday (hard HTML error) was labeled "GAP", a Sunday (small fallback to Friday) was labeled "ingested" — same situation (neither is a real trading day), different label, purely because of which artifact NSE happened to serve. Fixed: outcomes reclassified against a trading calendar derived from the batch's own observed evidence; three outcomes now — `INGESTED`, `NOT_A_TRADING_DAY`, `GAP` (reserved for a confirmed-real trading day that ingestion genuinely failed to retrieve). |

All five found by direct verification against real data/real code behavior, not assumed —
consistent with this project's verification-honesty rule.

## Coverage report — real ingestion sample (corrected for P2-005)

17 calendar dates requested (2019-10-01 as earliest reference date, one reference date per
calendar year through 2025, plus a 10-day recent window ending 2026-09-07). Reported against the
**observed trading calendar** (`classify_against_observed_trading_calendar`), not the raw calendar
sweep — see P2-005:

```
Requested calendar dates: 17
Observed trading calendar (dates confirmed to be real trading days): 12
  Ingested: 12
  GAP (confirmed trading day, ingestion failed -- real anomaly): 0
Not a trading day (weekend/holiday, excluded from the trading-day denominator): 5
  -> ['2022-03-01', '2026-08-29', '2026-08-30', '2026-09-05', '2026-09-06']

Total rows inserted: 43912 (first run) / 0 (re-run, all skipped_duplicate)
Total rows skipped as invalid (missing symbol/series, P2-004): 30
```

All 12 confirmed real trading days were successfully ingested; **0 genuine gaps** (anomalies).
The 5 excluded dates are exactly what they should be: two Saturdays, two Sundays, and 2022-03-01
(Holi — a real market holiday, previously mislabeled "ingested" because NSE's archive fell back
to 2022-02-28's file rather than erroring).

**Idempotency, real data**: re-running the identical script a second time inserted **0** new rows;
all 43,912 rows reported `skipped_duplicate`. Confirmed twice.

**Survivorship spot-check — qualified, not a coverage claim.** Comparing the earliest
(2019-10-01, 1,788 symbols) and latest (2026-09-07, 3,520 symbols) sample dates: 436 symbols
present in 2019-10-01 are absent from 2026-09-07. **This is a lower bound on a survivorship check
across a single 7-year gap, explicitly NOT a delisted-company count** — it misses every symbol
that both listed and delisted somewhere in between those two dates (arguably the population most
relevant to this project), since neither endpoint would ever see it. The true count of
listed-then-delisted symbols over 2019–2026 is unknown and is certainly higher than 436. **This
figure must not be quoted later as coverage or as "the delisted-company count."** It only
establishes, non-zero, that the source is not pure-survivorship — recognizable real cases in the
436: `3IINFOTECH`, `ALBK` (Allahabad Bank, merged into Indian Bank 2020), `ADANIGAS`/`ADANITRANS`
(renamed), `8KMILES`.

## Guard re-test against real data

`tests/test_bhavcopy_real_data_guard.py` (skipped, not faked, if the real sample DB is absent):

- **Mid-series delisting (ALBK)**: real historical rows visible for any as-of after its own data
  ends; zero rows for a recent trading date. **Verified.**
- **Multiple series, same real date**: DHFL alone has 9 distinct NCD series on 2019-10-01, business
  key keeps them as distinct rows (also directly caught the P2-004 "nan" defect). **Verified.**
- **Republished/corrected bhavcopy, a genuine real instance**: **not achieved.** No naturally-
  occurring NSE correction was identified or available within this session — that needs either
  prior knowledge of a specific historical correction date, or ongoing operation re-fetching recent
  dates to detect one as it happens. The mechanism itself is proven in
  `test_nse_ingestion.py` using a deliberately-modified copy of real fetched content, labeled
  honestly as engineered, not found. **DOCUMENTED, NOT VERIFIED** against a genuine real correction.
- **Corporate action with knowledge_date after event_date, real instance**: **blocked.**
  `jugaad-data` has no corporate-actions endpoint (discovered this phase, not previously known) —
  no real `corporate_actions` rows exist yet to test against. **DOCUMENTED, NOT VERIFIED** — owed
  once corporate-actions ingestion exists (see below).

## New scope gap surfaced this phase: no corporate-actions or ASM/GSM source in `jugaad-data`

`jugaad-data`'s public API (`nse.py`, `NSELive`, `NSEDailyReports`) covers bhavcopy/derivatives/
index/economic data only — there is no corporate-actions or ASM/GSM surveillance endpoint. Your
original approval was specifically for `jugaad-data` as the mechanism for NSE data; building a
custom scraper against NSE's other (undocumented) endpoints for these two data types is a
different, broader decision than what was approved, so it is not done and not started pending
your direction.

## Corporate actions block Phase 3 substantively — not a missing test, a correctness blocker

This is stronger than "a guard case is unverified." **Without corporate-actions data, there is no
adjusted price series, and without an adjusted price series, any return spanning a split or bonus
is wrong in exactly the direction that fabricates an extreme move.** A 1-for-1 bonus computed
naively from raw close prices shows as a ~50% overnight "crash" — precisely the shape of a false
positive this project exists to distinguish from genuine manipulation-consistent signatures. The
event catalogue (Phase 3, next) is built on returns. **It cannot be trusted — not "should be
double-checked," cannot be trusted — until corporate-actions ingestion exists and adjustment is
wired into signal computation.** Recorded here so nobody downstream assumes returns are adjusted
when they are not; also recorded as a hard constraint in `CLAUDE.md`.

## Tests

`python -m unittest discover -s tests -v` → **67 tests, 0 failures** (64 fixture/structural +
3 real-data-gated, run against the live sample DB this session).
`python -m py_compile` across `src/`, `tests/`, `scripts/` → clean.

## Open items carried forward

1. Corporate-actions and ASM/GSM sourcing decision (jugaad-data doesn't cover them — source
   evaluation requested for next session, see below; **this blocks Phase 3 substantively**, not
   just one guard test).
2. Real republished-file correction instance still unverified (mechanism proven, real occurrence not observed).
3. Corporate-action knowledge-date-ordering guard test against real data — blocked on (1).
