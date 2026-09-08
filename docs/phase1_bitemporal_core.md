# Phase 0 + Phase 1 — Scaffold and Bitemporal Core

## What was built

- Repo scaffold: `src/{config,bitemporal,ingestion,signals,mcp,agent}`, `evaluation/`, `tests/`,
  `docs/`, `data/{fixtures,raw}`. `CLAUDE.md` carries the Praman instructions plus the data-sourcing
  decisions made 2026-09-08 (NSE via `jugaad-data` directly against nseindia.com despite its ToS
  prohibiting automated collection — a knowing choice, not a silent one; SEBI orders scraped from
  `sebi.gov.in/enforcement/orders.html`).
- `src/bitemporal/schema.py` — the fact-table registry. `FactTable` is a frozen dataclass whose
  `__post_init__` refuses to construct if `event_date`/`knowledge_date` are missing from its
  columns, if its business key references an undeclared column, or if the business key includes
  `knowledge_date` (which distinguishes vintages of a fact, not the fact's identity). Four tables
  registered: `bhavcopy`, `corporate_actions`, `surveillance_flags`, `sebi_orders`.
- `src/bitemporal/dates.py` — one date-string validator (`YYYY-MM-DD` or `datetime.date`), shared
  by both the guard and the store so "valid date" can't drift between the read and write paths.
- `src/bitemporal/guard.py` — the as-of enforcement point (Section 7). `read_as_of()` returns every
  vintage of a fact visible as of a given date; `latest_as_of()` dedupes to one row per business key
  (max `knowledge_date`, tie-broken by `row_id`). `as_of` is a required positional argument (missing
  it is a `TypeError` at the call site, not a silent default); a malformed value, an unknown table,
  or an unknown filter column all raise `TemporalGuardError` rather than returning a partial result.
- `src/bitemporal/store.py` — the append-only writer (Section 8). Every column except `row_id`/
  `recorded_at` must be supplied explicitly, including nullable ones as `None` — no silent
  "missing means null." A re-insert of the same (business key, knowledge_date) is rejected
  (`StoreValidationError`), not silently ignored; a genuine restatement needs a new `knowledge_date`.
  No `UPDATE` statement exists anywhere in this module or anywhere in `src/` against a registered
  fact table — enforced by `tests/test_no_update_on_fact_tables.py`, a grep-based structural test,
  not a review checklist.
- `src/bitemporal/connection.py` — SQLite bootstrap (local-first, matching InsightForge's default
  mode). Idempotent `init_db()`.

## What was deliberately deferred

- Real ingestion. Every test in this phase runs against a tiny, explicitly-fake fixture row
  (`FIXTURECO`, `DELISTEDCO`) — this proves the plumbing, not the guard against real-world
  messiness. Per your instruction, the guard must be re-tested against real bhavcopy data as soon
  as NSE ingestion lands, with the three specific cases you named (delisted mid-series, a
  corporate action announced after its own ex-date, a republished/corrected bhavcopy) run again
  against actual ingested rows — this phase's fixture versions of those three cases are a first
  pass, not a substitute.
- `sebi_orders`' schema is registered now (so `bhavcopy`/`corporate_actions`/`surveillance_flags`
  aren't designed around eventually needing a fourth table bolted on) but nothing populates it yet
  — that's the SEBI ingestion phase, after NSE ingestion per your reordering.

## Tests

`python -m unittest discover -s tests -v`

```
Ran 28 tests in 0.012s

OK
```

Covers: schema self-validation (4 tests), date validator (4), guard fail-closed behavior (7),
restatement-never-overwrites (4), store validation (5), delisted-symbol-stays-queryable (1),
corporate-action knowledge-date-ordering (2), no-UPDATE structural grep (1).

## Open item carried forward

Real-data guard re-test (your instruction #3) — owed once NSE ingestion (next phase) produces
actual bhavcopy rows to run these same edge cases against.
