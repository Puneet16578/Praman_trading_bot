# Phase 7a — Disclosure data sourcing: corporate announcements + SEBI enforcement orders

Status: corporate-announcements cache built and backfilled in full. SEBI orders reconnaissance
complete and ingestion module built and tested against real data (January 2020 sample); the full
7-year SEBI backfill has not been run yet — a separate, explicitly gated step, held per the same
discipline as bhavcopy's full-history run.

## Corporate announcements — design

New bitemporal table `corporate_announcements` (`src/bitemporal/schema.py`), populated by
`src/ingestion/nse_market_data/announcements.py`. Reuses the real `corporate-announcements` NSE
endpoint corporate_actions.py already calls (Phase 3) to cross-check bonus/split ratios — that
usage filters to `desc in {"bonus","stock split"}` and never persists a row; this table stores
**every** announcement, any category, because the Disclosure agent needs "no disclosure found" to
be a real, checkable absence, not an artifact of a narrower filter built for a different purpose.

Confirmed empirically before writing anything: **one request per symbol, spanning 2019-10-01 to
today, returns the symbol's entire announcement history in a single response** — no pagination
(RELIANCE: 2,129 rows in one call). `event_date == knowledge_date ==` the announcement's own real
disclosure timestamp (`sort_date`'s date part) — an announcement has no separate "happened earlier,
announced later" structure the way a bonus ex-date does; the disclosure IS the event, the same
reasoning `DEMERGER_EXCLUSION` rows already use.

## Disclosure count: rows vs. events

**Storage and counting are deliberately different operations.** Every real announcement row is
stored individually and permanently — the bitemporal record, queryable exactly as filed, which is
what the Adversary needs to verify a cited announcement exists. `disclosure_count` for any agent
or report must never be `len(rows)` directly; it must go through
`cluster_announcements_into_events()`, which decides how many distinct real disclosures a set of
rows represents.

**Two real duplication risks were checked, not assumed, on a growing real sample (12 symbols →
the full backfill), and they pointed in different directions:**

1. **Same disclosure, corrected/re-filed** (the Phase 3 KITEX precedent: a bonus ratio typo "2:2"
   fixed to "2:1" 38 seconds later) — real, confirmed: one ADANIENT regulatory disclosure was
   re-filed **9 times within 11 minutes** (2022-06-18). A naive per-row count sees 9 disclosures
   for 1 real event.
2. **Same category, genuinely different disclosures** — checked on 28,617 real same-category,
   near-time pairs across the full backfill: **69.1% have genuinely different `attchmntText`**.
   Real example: two RELIANCE notices under "Analysts/Institutional Investor Meet/Con. Call
   Updates," 4 minutes apart — one for a Morgan Stanley conference, one a non-deal roadshow. This
   is the majority case for broad categories ("Updates," "Analysts/Institutional Investor
   Meet/Con. Call Updates"), not a rare edge case.

**The clustering rule has two required gates, not one:** same `(symbol, category)`, within 1 hour
(`NEAR_DUPLICATE_GAP`, matching `collapse_clusters`' existing precedent) **and** `attchmntText`
similarity (difflib `SequenceMatcher` ratio) **>= 0.95**. The threshold was calibrated against real
data, not chosen as a round number: NSE's own announcement text is heavily templated
("[Company] has informed the Exchange regarding...", "Please note that the Company executives
will be participating in..."), so even genuinely different announcements can score deceptively
high on whole-text similarity from shared boilerplate alone — the real RELIANCE "different"
example above scores **0.883**, meaning even an 0.85 threshold would still wrongly collapse it.
0.95 was chosen specifically because both known-real "different" examples (0.782, 0.883) fall
clearly below it while the real "near-identical/exact re-transmission" population (38.9% of all
pairs, score >=0.95) sits clearly above it. The failure mode this favors is deliberate:
undercounting two rows into one hidden event is worse for a Disclosure agent than overcounting two
genuinely-identical rows as two, because a hidden real disclosure is a worse error than an
unambiguous one counted twice.

Net effect on the full real dataset: naive category+time clustering alone would have reported a
4.55% row-to-event reduction; with the content-similarity gate added, the honest reduction is
**2.44%** — most of what the naive rule collapsed was not actually the same event.

10 tests cover this directly, including the exact real ADANIENT 9-row burst, a synthetic
KITEX-shaped correction (must still collapse), and the real RELIANCE non-collapsing pair (must
not collapse despite matching category+time).

## Full backfill — real results, including a real interruption

`scripts/ingest_announcements_full_history.py`, resumable by design (checks which symbols already
have cached rows at startup, fetches only the rest) — built as resumable *before* running, because
a real 10-symbol timed sample (1.76s/symbol) projected ~87 minutes for the full 3,400-symbol EQ
universe, over the one-hour bar that triggers this pattern (same as bhavcopy's full-history run).

**The run validated its own resumability requirement in practice, not just in theory:** partway
through, the machine lost network connectivity for approximately 15 hours (visible directly in the
run's own log: symbol 2300 to 2400 shows a ~54,600-second gap, versus ~150s for every other
100-symbol block) — real evidence the design decision was warranted, not precautionary padding.
The run resumed automatically once connectivity returned and completed normally. 16 symbols failed
on transient connection errors during the outage itself; a second run (1,063s) picked up exactly
those plus every previously-zero-row symbol (a real limitation of "has cached rows" as the
resume marker — a symbol with a genuine zero-row history can never be marked "confirmed done" and
gets re-attempted on every re-run; harmless for a one-time backfill, since re-fetching a
confirmed-empty symbol is idempotent and cheap, but worth naming for a future recurring job).

**Final real numbers:** 1,021,591 announcement rows across 2,500 of 3,400 EQ symbols (900 symbols
never returned any real row from the live endpoint across the full run).

**603 of the 2,958 catalogue symbols have zero cached announcements.** Investigated directly, not
left as an unexplained number: 263 are delisted or renamed symbols (last traded before Aug 2026 in
this project's own bhavcopy data) — confirmed structurally, not guessed, for at least one case:
`ADANITRANS` traded 2019-10-01 through 2023-08-23, then the company continues today as
`ADANIENSOL` (a distinct symbol in this project's own bhavcopy table); NSE's live announcements
endpoint returns zero for the old, delisted symbol string directly (tested live, confirmed), a
real, structural gap for any pre-rename historical symbol, not a bug in this ingestion code. The
remaining **340 zero-row symbols appear currently active** and are not explained by a rename —
one spot-checked directly (`ABBOTINDIA`, a real, actively-traded, major pharmaceutical company,
confirmed trading through 2026-09-15) returns zero from the live endpoint with no available
explanation. Recorded as a genuine, unresolved anomaly rather than assumed away.

## Coverage — the actual deliverable

For every one of 75,300 catalogued events: is there at least one real announcement (any category)
in the 10 real trading sessions strictly before `event_date`?

| | Count | Share |
|---|---|---|
| >=1 announcement in the 10-session window | 55,928 | 74.3% |
| 0 announcements in the window (confirmed real absence) | 11,078 | 14.7% |
| Fetch gap — symbol has no announcement data cached at all | 8,294 | 11.0% |
| Insufficient trading history for a full 10-session window | 0 | 0.0% |

**The fetch-gap share (11.0%) is reported as a distinct category, never folded into "no
disclosure."** For these 8,294 events, the honest answer is "cannot be determined from this
project's ingested data" — not "no disclosure was found." This is the same distinction CLAUDE.md
already requires for signals: a missing input reports as missing, never as a neutral-looking zero.
Any future Disclosure agent output for an event in this bucket must say so explicitly.

## Substantive vs. routine — a boolean disclosure_present would overstate GROUNDED

Raised correctly: `Analysts/Institutional Investor Meet/Con. Call Updates` is the single largest
category in the entire store (114,140 of 1,021,591 rows, 11.2%) — an investor-meet notice
announces that a meeting *will occur*, not substantive business content. A plain boolean
`disclosure_present` would treat it identically to an earnings release or an order win.

**Category mapping built from the real, complete 280-category distribution (full backfill), not
from intuition** — `src/signals/disclosure_classification.py`. Three tiers:
- **SUBSTANTIVE** (results, orders/contracts, board-meeting outcomes, M&A/restructuring, credit
  rating actions, personnel changes, regulatory actions/approvals, litigation/default,
  capital-structure changes, price/volume queries from the exchange itself) — 322,347 rows (31.6%).
- **ROUTINE** (meeting/call *scheduling*, trading-window notices, compliance certificates,
  newspaper republication, share-certificate administrivia, record-date mechanics, corrections) —
  468,064 rows (45.8%).
- **AMBIGUOUS** (generic catch-alls — `Updates`, `General Updates`, `Press Release`, `Investor
  Presentation`, `Others`) — 231,180 rows (22.6%). Not force-fit into either side: `Updates` and
  `General Updates` were directly confirmed, by reading real row pairs earlier in this phase, to
  bundle both substantive content (CRISIL/CARE rating letters, Regulation 30 disclosures) and
  routine content under one label — a category name alone cannot resolve which. Treated
  conservatively as NOT substantive for the event-level classification (CLAUDE.md invariant 12:
  the safer failure mode for a system that must never overclaim), with the impact of that specific
  choice reported explicitly rather than folded silently into either count.

Coverage against the real store is asserted, not assumed: all 280 real categories are classified
explicitly; a category outside the mapping raises rather than silently defaulting (both directions
tested — every real category covered, and no stale/typo'd mapped category that doesn't actually
exist in the store).

**Real three-way split, all 75,300 catalogued events, 10-session window, `event_date`/knowledge_
date-correct:**

| | Count | Share of known (67,006) |
|---|---|---|
| SUBSTANTIVE disclosure present | 33,005 | 49.3% |
| ROUTINE (or ambiguous-only) disclosure | 22,923 | 34.2% |
| No disclosure at all | 11,078 | 16.5% |
(8,294 fetch-gap events excluded from this denominator — reported separately, per the existing
"missing is not a neutral zero" rule.)

**Reading this plainly: presence alone (74.3% of all events, from the row-level coverage report)
overstates how often a real, substantive explanation exists.** Of the events with *any*
announcement in the window, only about half (49.3%) had one carrying real business content — the
other half had only routine filings that happen to exist in the window without actually
explaining the price move. A future Disclosure agent must report the three-way tier explicitly
("substantive disclosure present" / "routine disclosure only" / "no disclosure"), never collapse
it to a boolean, and GROUNDED-shaped classification thresholds should be set against the
SUBSTANTIVE share, not the presence share.

## Still open

- The full SEBI orders backfill (7 years, ~52 weeks/year, recursive-bisection-on-overflow already
  built and tested) has not been run — a separate, explicit go-ahead needed, same as this backfill
  got.
- PDF text extraction for a confirmed SEBI order `event_date`/period and entity/symbol match
  remains a named follow-on, not done.
- The 340 unexplained zero-announcement active symbols are a real, open question — not resolved
  in this pass.
