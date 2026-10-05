# Pinned forward pipeline vs the restructured announcement store

Dated 2026-10-06; requested by the user as a P8-046 follow-up. Question: can the pinned forward
pipeline (`afe3e2b`, Amendment 5) still read the announcement store now that it holds bulk,
ISIN-dated rows (switch `904c53f`, backfill 2026-10-05)? Inputs only: disclosure tiers are a model
input; no outcome label is read or computed, so the forward-window firewall is not touched. No
frozen artifact, pre-registration or store was changed.

**Verdict: PASS. No evaluation-blocking defect found.** The pinned code reads the restructured
store without error and, for recent events, sees the same rows as before the restructure. Its
existing rename blind spot (P8-046) continues in the forward window and is recorded as a known
limitation in `docs/OPERATIONS.md`.

Machine-readable results: `pinned_reader_verification.json`. Reproduce with
`git worktree add --detach <dir> afe3e2b`, then
`python scripts/verify_pinned_announcement_reader.py --worktree <dir>` (about 35 s), then
`git worktree remove <dir>`.

## Method

- **Store:** a temporary copy of `data/processed/praman.db` made by SQLite online backup (the
  source opened read-only), read through a read-only connection: 1,032,635 announcement rows,
  latest session 2026-10-05.
- **Events:** 1,156 (symbol, date) pairs, event-list sha256 `b9318ad4...`, seed 20261006:
  - the 625 the Desk scan logged from 2026-09-16;
  - a seeded random sample of 500 EQ sessions from 2026-09-24 to 2026-10-05, whose windows lie
    wholly after the bulk coverage start of 2026-09-10;
  - the 46 sessions since 2026-09-16 of the recently renamed securities.
- **Pinned tiers:** `scripts/pinned_disclosure_tiers.py`, run with the afe3e2b worktree first on
  `sys.path`. Every `src` module it imports was checked to load from the worktree. It repeats
  `build_event_classifications.py`'s tier code verbatim:
  - coverage is "any row under the symbol";
  - rows come from `SELECT event_date, category ... WHERE symbol=?`;
  - the window is 10 sessions on the ISIN-stitched trading history;
  - the tier comes from `classify_disclosure_window`.

  `phase8_classify_holdout.py`'s tier code is identical, except that it uses the unstitched
  history.
- **HEAD tiers:** `src.mcp.tools.get_disclosure_window`, which follows ISIN aliases, applies
  `knowledge_date <= event date` and keeps one row per announcement. It is paired with the same
  any-row coverage rule.
- **Comparison:** tiers and window rows are compared for every event, and every difference is
  explained from the copy itself. The pass criteria were written into the script before the first
  run.
- **`init_db`:** the pinned `init_db` was run on the temporary copy, because the pinned evaluation
  calls it before reading.

## Results

| | Events |
|---|---:|
| Identical tier and identical window rows | **1,143** |
| Tier differs: window boundary, renamed securities (CRESTO 4, HEGAM 9) | 13 |
| Any other difference (unexplained, misfiled, duplicate, read-after-event) | **0** |

- **Criterion A, the pinned code runs:** it does, including `init_db`, which added and removed
  nothing on the restructured schema.
- **Criterion B, every tier difference explained:** all 13 are window-boundary cases.
  - The pinned reader stitches the renamed security's history, so it has a full 10-session window
    and gives SUBSTANTIVE.
  - HEAD's reader uses the new symbol's own history, which is shorter than 10 sessions, so it
    returns "insufficient history". The Desk then reads the dimension as UNKNOWN.
  - Here HEAD is the more conservative reader, not the pinned one.
- **Criterion C, no misfiled rows:** no row HEAD attributes to an event is filed under a symbol that
  was not trading when the row was published.

**What the pinned reader cannot see.** Within its own stitched window, it never reads rows filed
under the security's other symbol:
- In the sample this happened in 9 HEGAM events: 118 HEG-filed rows.
- All 118 were filed by the old per-symbol path; the bulk path filed none of them.
- Seeing them would change no tier, because HEGAM's own rows already made every window
  SUBSTANTIVE.

**Tier mix.** Pinned tiers across the sample were 453 SUBSTANTIVE, 478 ROUTINE_ONLY, 112 NONE and
113 UNKNOWN_COVERAGE.
- **Fund units:** 55 of the UNKNOWN_COVERAGE events are INF fund units from the random sample.
  They are outside the equity-only catalogue.
- **Equities:** the remaining 58 are 5.3% of the 1,101 equity events, close to the 5.1% share in
  the frozen 2019-2025 training classifications. Their symbols have no NSE announcement under
  either the symbol or the ISIN, in either the old per-symbol data or the bulk data.
- **Example:** ABBOTINDIA's absence was confirmed in the raw bulk capture for 2026-09-28 to
  2026-10-05, which includes the quarter-end trading-window notices nearly every company files.
  Many of these symbols first appear in this project's bhavcopy in April or August 2026.
- **Conclusion:** forward UNKNOWN_COVERAGE keeps its training meaning for equities: the source has
  no announcements for the symbol.

## Limits

- **The sample:** 1,156 events over three weeks, not the whole forward window. The random part is
  500 of the roughly 22,000 EQ sessions it was drawn from.
- **The reference reader:** HEAD's reader stands in for "correct". The two readers share a blind
  spot for any row filed under a symbol neither queries. Checked separately on the whole store: the
  152 equity bulk rows filed under a symbol not trading near publication all belong to symbols
  with no session since publication (for example GAMMONIND, ERAINFRA, LEEL), so no forward event
  can reach them so far.
- **Future renames:** since 2026-10-05 the bulk path files each announcement under the symbol
  trading on its publication date. For an event in a security's first 10 sessions after a future
  rename, the pinned reader will therefore see only the post-rename announcements.
  - Under the old per-symbol refresh, a newly renamed symbol had no stored rows, was never fetched,
    and its events were UNKNOWN_COVERAGE. So this is not worse.
  - The sample contains no such case. The expected number of forward events affected is small: a
    handful of renames over the window, each with up to 10 sessions.
