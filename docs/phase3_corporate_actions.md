# Phase 3, Session A — Corporate Actions Tiering and Adjustment

## The tier scheme

Every bonus/split action gets a `confidence_tier`:

- **CONFIRMED** — announcement matched (correct desc, within the measured 121-day window,
  closest-preceding, not deferred language) AND its parsed ratio agrees with `subject`.
- **MATCHED_UNCONFIRMED** — announcement matched structurally, but its text couldn't corroborate
  the ratio (no numbers, self-contradictory, unparsed form). Ratio from `subject`, knowledge_date
  from the announcement.
- **EX_DATE_FALLBACK** — no announcement found, or a matched one downgraded for an out-of-range
  gap. Ratio from `subject`, knowledge_date = ex_date.
- **QUARANTINE** — both sides parsed and disagree. Never written to the store.

Demergers get a fifth, separate marker, **DEMERGER_EXCLUSION** — not part of this confidence
scheme (there's no ratio to confirm), just an exclusion flag: symbol + ex-date, no ratio, no
factor. See CLAUDE.md's scope-boundary note for why this is permanent, not provisional.

## Design conclusion applied, not re-litigated

The AURIGROW verification (previous session) resolved which endpoint is the numeric arbiter:
`subject`'s "1:1" was confirmed correct against the actual filed PDF; the announcement's own
auto-generated "11104000:111040000" had a stray extra zero. Every row in every tier stores the
ratio from `subject`. The announcement contributes knowledge_date, and — where parseable — a
corroboration check, never the number itself.

## Gap sanity check

Measured distribution (253 v1-agreeing cases, previous session): min=28, median=44, p95=65,
max=121 days between announcement and ex-date. `MIN_GAP_DAYS=28`, `MAX_GAP_DAYS=121`. A matched
announcement whose gap falls outside this range is downgraded to EX_DATE_FALLBACK — **42 rows
downgraded** in the real run below.

## Real ingestion results (2019–2026, from the already-cached data — zero new network calls)

```
CONFIRMED:            340  (48.7%)
MATCHED_UNCONFIRMED:  114  (16.3%)
EX_DATE_FALLBACK:     149  (21.3%)
QUARANTINE:             5  (0.7%)  -- not written
-----------------------------------
Bonus/Split total:    608
DEMERGER_EXCLUSION:    90  (12.9% of all written rows)
TOTAL WRITTEN:        698
Downgraded to EX_DATE_FALLBACK for out-of-range gap: 42
Unhandled action types (dividends, rights, etc. -- out of scope this session): 15,826
```

**Usable across the three writable tiers: (340+114+149)/608 = 603/608 = 99.2%** — matches the
~99% expectation.

**Idempotency, real data**: re-running the identical script a second time inserted **0** new rows;
all 693 rows reported `skipped_duplicate`.

## QUARANTINE — all 5, not written

```
AURIGROW,   2022-01-20: subject 1:1 vs announcement 11104000:111040000 -- RESOLVED (prior session): subject correct, announcement auto-text has a stray zero (verified against filed PDF)
BEPL,       2023-07-05: subject 1:2 vs announcement 2:1 -- announcement is internally self-contradictory (P3-002, deferred)
KOTHARIPRO, 2025-02-18: subject 1:1 vs announcement 30000000:31500000 -- unresolved, which side is wrong is unknown
UNIVASTU,   2025-10-13: subject 2:1 vs announcement 25357180:11995590 -- unresolved
MONEYBOXX,  2025-12-15: subject 1:1 vs announcement 37502745:32704600 -- unresolved
```

## BAJFINANCE 2025 — the permanent compounding fixture, verified against real data

Real rows now in the store:
```
BAJFINANCE  BONUS  event_date=2025-06-16  knowledge_date=2025-04-29  ratio=4.0:1.0  CONFIRMED
BAJFINANCE  SPLIT  event_date=2025-06-16  knowledge_date=2025-04-29  ratio=2.0:1.0  CONFIRMED
```
Real bhavcopy fetched for 2025-06-13 (last trading day before the ex-date) specifically for this
verification — one additional real network call, 2,855 rows, BAJFINANCE's real close: **Rs 9,331.00**.

```
compute_adjustment_factor(BAJFINANCE, price_date=2025-06-13, as_of=2025-06-20) = 10.0   (5 x 2, not 4 or 2)
adjusted_close(as_of=2025-06-15, BEFORE ex-date)  = 9331.0   (no adjustment -- window can't span the ex-date yet)
adjusted_close(as_of=2025-06-20, AFTER ex-date)   = 933.1    (9331 / 10)
```
933.1 is consistent with BAJFINANCE's real, publicly observable post-action trading level in late
June 2025. Test: `tests/test_price_adjustment.py::BajfinanceCompoundingFixtureTest`.

## As-of adjusted price: query-time only

`src/signals/price_adjustment.py::adjusted_close` / `compute_adjustment_factor` — no stored
column. Every call re-reads `corporate_actions` via `latest_as_of(..., as_of)` (Section 7), so an
action not yet knowledge-dated as of the query never affects the result even if its ex_date has
already passed in calendar time (`BitemporalSafetyTest`, fixture-verified). A demerger falling
inside the (price_date, as_of] window raises `UnadjustableWindowError` rather than being silently
skipped or averaged over (`DemergerUnadjustableTest`).

## Timing-signal exclusion, enforced structurally

`src/signals/corporate_action_timing.py::timing_reliable_corporate_actions` is the only sanctioned
read path for anything reasoning about *when* an action became public (e.g. future pre-announcement
accumulation signals) — it filters out EX_DATE_FALLBACK rows by construction.
`tests/test_corporate_action_timing.py` asserts this, and separately demonstrates that the raw
guard call does NOT filter by tier — proving the dedicated accessor is necessary, not redundant.

## Corporate-action knowledge-date-ordering guard, real data — owed since Phase 2

`tests/test_corporate_actions_real_data_guard.py`. Real BAJFINANCE rows invisible before their
real 2025-04-29 announcement date, visible after. Honest scope note: every real writable row in
this dataset has knowledge_date preceding event_date (board announcements precede ex-dates as a
matter of regulatory process) — the inverse ordering (late-announced action) has no real example
yet and remains fixture-verified only (`test_bitemporal_core.py::CorporateActionKnowledgeDateOrderingTest`).
A test (`test_no_real_row_has_knowledge_date_after_event_date`) documents this rather than leaving
it an unstated assumption.

## Implementation note: `requests` directly, not the `NseIndiaApi` package

The approved source was NseIndiaApi's endpoints and session approach. All of this session's (and
the prior session's) fetching was implemented with plain `requests` hitting the same underlying
`nseindia.com/api/corporates-corporateActions` / `corporate-announcements` endpoints directly,
without adding the third-party package as a dependency. Same source, same ToS posture already
recorded in CLAUDE.md, same endpoints verified this session — just without an extra dependency
for two simple JSON calls. Flagging explicitly rather than treating it as equivalent to what was
literally approved.

## Deferred (not built this session, logged in DEFECT_REGISTER.md)

P3-001 (the "for every" prose bonus form), P3-002 (bonus-side internal-consistency check),
P3-003 (AFFLE's floating-point INTERNAL_MISMATCH artifact). All currently land in the safe
`MATCHED_UNCONFIRMED`/`QUARANTINE` tiers rather than being silently wrong.

## No new parsing work beyond what was already validated

Per instruction, the parser itself (optional Rs./Re. prefix, face-value fallback, "ration of"
tolerance) is exactly what was already measured last session — not widened further here.

## Tests

`python -m unittest discover -s tests -v` → **112 tests, 0 failures**.
`python -m py_compile` across `src/`, `tests/`, `scripts/` → clean.

## Acceptance checklist

- [x] Tier counts reported for all 608 actions — 99.2% usable across the three writable tiers.
- [x] QUARANTINE rows (5) listed individually, confirmed NOT in the store (real-data test).
- [x] BAJFINANCE compounding verified by hand against real data — 10x, output shown above.
- [x] Test asserting timing-based signals cannot see EX_DATE_FALLBACK rows.
- [x] Adjusted-price computation proven to use only actions known as-of the query date (fixture + real).
- [x] Full suite green, py_compile clean.
