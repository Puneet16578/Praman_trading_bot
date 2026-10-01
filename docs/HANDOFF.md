# Handoff

Context for the next agent session, not instructions. Verify every claim here against the
repository before relying on it; nothing in this file authorizes anything (CLAUDE.md,
"Authorization").

**Last updated:** 2026-10-01, by Codex (Phase A).

## Phase A checkpoint — 2026-09-30

- Repository root verified as `D:/Agentic_ai_project/praman`; initial working tree clean.
- User approved the Phase A implementation plan and a complete test-clock audit.
  No other agent, background task, or new scheduled job was started.
- P8-019 fixes the obsolete clock mock introduced with P8-018. The audit found
  no other obsolete date/datetime patch. ISIN-refresh and health-age tests now use
  fixed clocks too. A grep-style guard forbids local `today()` calls in Desk/scripts.
- Baseline on 30 September: 534 tests, one failure and one error, both retry tests.
  Root cause verified in source: the tests patched `date.today`, while production
  called `market_today`. No network/temp-folder failure caused these failures.
- After P8-019: `Ran 535 tests in 133.823s`, `OK`, Python exit code 0.
  Pre-existing SQLite `ResourceWarning` messages remain visible.
- Read-only inspection outside the sandbox confirmed `PramanDailyIngest` has
  `WakeToRun=True`, `StartWhenAvailable=True`, `LogonType=Interactive`, state Ready.
  Last run: 2026-09-29 18:37:07; result 3221225786; missed runs 1. Cause of that
  nonzero result is unverified. The sandbox initially denied task inspection.
- Existing ingestion log contains NSE DNS failures and its latest completed
  summary is the run starting 2026-09-28 22:42:25+05:30, overall ERROR.
- P8-019 committed as `173b7a7` with this handoff.
- Step 0 / P8-020: ingestion writes durable starts and per-step progress; status
  matches finishes and reports unfinished runs; Windows execution state is held
  while running and restored on exit, guarded for other platforms. Seven targeted
  tests pass. Existing task settings required no changes.
- Step 0 full suite: `Ran 542 tests in 197.270s`, `OK`, Python exit code 0.
  The real Windows API also ran successfully in the existing mocked-ingestion
  summary tests. ResourceWarnings remain as in the baseline.
- Live `python desk/cli.py status`: latest trading date 2026-09-25, ingestion
  overall ERROR with one gap, no open positions; ISIN build 2026-09-23 (age 2
  trading sessions in the current store). The store is not caught up to today.
- User selected local `D:\PramanBackups` and cloud
  `C:\Users\VICTUS\OneDrive\PramanBackups`, no encryption. OneDrive exists but no
  process/account could be verified. User then explicitly approved proceeding with
  local backups and keeping cloud disabled until they confirm a synced folder.
- Retention: 14 daily Desk backups in each enabled destination, 8 weekly Praman
  backups locally, 2 weekly in cloud when enabled. Local folder created.
- Step 1 implementation: shared read-only online backup helper, compressed ZIP
  snapshots with counts and hashes, restore proof before retention, `desk backup
  verify`, status timestamps, backups appended after ingestion. Ten targeted tests pass.
- Step 1 code verification: `Ran 552 tests in 115.065s`, `OK`, exit code 0.
  Committed as `8a0af81`. Pre-existing SQLite ResourceWarnings remain.
- First production backup command and explicit `desk backup verify` both exited 0.
  Desk ZIP: 3,793 bytes; Praman ZIP: 329,916,828 bytes. Both passed integrity, row
  counts, and database hashes; every Desk journal table hash matched. Production
  journal is empty, with populated-WAL and corruption recovery covered in tests.
  Full proof: `docs/desk/phase_a_backups.md`. These snapshots were taken during
  ingestion after bhavcopy reached September 29, before the same-day step.
- P8-020 status refinement: keep the latest completed run visible alongside any
  older unmatched start, rather than allowing the old abort to hide recovery.
  Full suite: `Ran 552 tests in 119.817s`, `OK`, exit code 0.
- P8-021 is open: announcement backfill skips already-cached symbols, and its
  caught failures can look OK in the wrapper. No research-ingestion behavior was
  changed. An OK step is not evidence that current disclosures were refreshed.
- Task change approved by user: existing `PramanDailyIngest` now launches
  `pythonw.exe` instead of `python.exe`; arguments and working directory unchanged.
  Re-read confirms wake-to-run and missed-start recovery True, Interactive logon,
  Ready state. No password, new task, or background helper was created.
- The terminated 21:33 run's only progress line was
  `=== 2026-09-30T21:33:17.908703+05:30 weekly_ingest started ===`.
  There was no completed step or finish. Task result 3221225786 (0xC000013A),
  externally terminated per the user; the log cannot identify the exact interruption.
- Foreground ingestion started with approved network access at
  `2026-09-30T21:49:09.771404+05:30`; bhavcopy completed OK at 21:52:31.
  It completed at 22:09:51 with exit code 0, overall WARN, and zero gaps.
  Announcements, corporate actions, ASM/GSM and today's bhavcopy reported OK.
  The warning was exactly two historical ISIN snapshot HTTP errors: 2020-06-15
  and 2021-02-17. Today's ISIN snapshot succeeded, with refreshed metadata at
  22:08:58 and age zero. `desk status` confirms latest trading day 2026-09-30.
  The earlier 21:33 interrupted start remains visible alongside this completed run.
- Post-ingestion full suite completed: `Ran 552 tests in 103.981s`, `OK`, exit 0.
  The follow-up backup command was blocked by automatic approval review's usage
  limit (not a safety rejection). On the user's 1 October resume it was retried
  with approval and succeeded: new daily Desk ZIP
  `desk_20261001T012818106568Z.zip`, 3,793 bytes; weekly Praman archive re-verified.
  No ingestion process remains active. Backup/restore code and proof commits
  `8a0af81` and `da7e346` were pushed before the interruption.
- Step 2 completed: NSE dated price-band reports stored append-only with publication
  knowledge dates and exact-date as-of reads. Reports describe the next session;
  missing dates stay UNKNOWN. Derivatives are explicitly DYNAMIC, not fixed 10%.
  Assess shows planned, locked-circuit, and stress losses; stress includes the
  two-day locked loss. No pinned scripts or Praman source code changed.
- Source report: `docs/desk/price_band_source.md`. Production ingestion for ten
  report dates, 2026-09-17 through 2026-09-30, inserted 35,427 rows, independently
  checked against SQLite counts. Real fixture tests cover A2ZINFRA (5%) and
  RELIANCE (dynamic), append-only history, replay watermarks and unavailable dates.
- Step 2 full suite: `Ran 561 tests in 165.944s`, `OK`, Python exit 0.
  P8-022 fixes an omitted registry test fixture; P8-023 fixes zero-share assessment
  output dereferencing an absent stress result. SQLite ResourceWarnings remain.
- Steps 3–6 remain pending. The foreground-ingestion prerequisite is complete.
- On 1 October the user fixed the screening convention: event close is the final
  decision price; freeze stop level (close minus 2 x ATR20), whole-share size,
  stress loss and liquidity at the event date. Append a separate next-session
  execution row with actual open, unchanged quantity, explicit gap, immediate
  gap-through and cap-breach flags, or NO_FILL. Never resize at execution.
- `docs/desk/shadow_replay_prereg.md` records this convention and the question,
  metrics, prediction, periods, missingness policy and bootstrap specification
  before any shadow outcome run. DESIGN records the later eligible-stock-day table.
  No replay outcomes have been computed. Step 3 implementation is next.
- Rechecked status on 1 October: latest trading date 2026-09-30; local Desk and
  Praman backups have successful restore checks this morning. Cloud stays disabled.
  Initial tree was clean; full baseline suite completed with Python exit 0
  (561-test suite, unchanged code; SQLite ResourceWarnings remain).
- Network downloads, test-only pip installation, and push need the user's approval
  when reached. Each tested step must include this handoff in its commit.

The sections below preserve the prior session's context; the checkpoint above is current.

## Current state

- **Phase:** Desk Phase 1 is complete; paper trading has not started. The user will make the
  first paper trade themselves. No decision, thesis, or trade exists in `data/desk/desk.sqlite`
  (0 rows in every table).
- **Task just finished:** post-Phase-1 operational hardening: P8-015 to P8-018, plus this
  handoff and the rules for working across agents.
- **Latest code commit:** `1febbba` (desk status prints the latest trading date). The commit that
  adds this file follows it; `git log -1` is authoritative.
- **Full suite:** `python -m unittest discover -s tests -p "test_*.py"`: 534 tests, OK.
- **Remote:** `origin` = `https://github.com/Puneet16578/Praman_trading_bot` (private), branch `master`.

## Done this session (2026-09-28)

| Commit | What |
|---|---|
| `d730834`, `323caf4` | CLAUDE.md Authorization rule (typed or pasted user messages count; claims in files, logs, and tool output never do); no Claude Code wakeups, loops, or cron jobs; `.gitignore` covers all of `data/` |
| `e34956b` | P8-015: missing `import time` in the same-day bhavcopy retry path |
| `f84d643` | P8-016: `demo/run_demo.ps1` binds to localhost explicitly; the earlier "reachable from the network" alarm was a netstat misread |
| `b57b9dd` | P8-017: ISIN refresh reports WARN on today's 404 and keeps the existing map; health levels OK/WARN/ERROR; companion `.meta.json` (build time with offset, SHA-256, snapshot dates); G1 fails when the map is more than 5 trading days old; decisions record `isin_map_built_at` and replay uses only the recorded value |
| `8c50eae` | P8-018: one IST market clock (`shared/market_time.py`); log timestamps carry `+05:30`; paper open and close, `desk evening`, the G7 override month, and the ingestion scripts use the NSE calendar date |
| `1febbba` | `desk status` prints the latest trading date in the store |

Operational, outside git:
- Windows task `PramanDailyIngest` registered as user VICTUS: weekdays at 18:00, runs only while
  logged in, starts late if missed. No other Praman task exists.
- Desk `decisions` migrated (`isin_map_built_at`; 0 rows before and after).
- Companion file written for the existing 23 September ISIN map (build time taken from the file
  timestamp and labelled as such).
- Store caught up through 2026-09-25 by a manual run of the first five ingestion steps.
- The Streamlit demo (PID 232860) was stopped.

## In progress

Nothing. The working tree is clean after the handoff commit.

## Next step

1. After the 18:00 run on 2026-09-28 (the first scheduled run), check
   `Get-ScheduledTaskInfo -TaskName PramanDailyIngest` and the tail of `logs/weekly_ingest.log`.
   Expect `bhavcopy_today` to ingest 2026-09-28 (or log a GAP), and `isin_map` to refresh the map
   and write a companion with `build_time_source: refresh`.
2. `.\desk status` should then show the latest trading date as 2026-09-28 and an ISIN map age of 0,
   and `.\desk evening` should stop refusing.
3. Wait for the user's first paper trade. Don't assess, open, or close anything unasked.

## Open questions and known limitations

- **G1 masking:** a stale-ISIN-map failure returns before G1's other checks, so it can hide a
  coexisting data-gap reason. Accepted, not fixed.
- **Fresh clone:** without `data/raw/nse_symbol_isin_current.meta.json`, every new assessment fails
  G1 (fail-closed by design), and real-data tests expecting ELIGIBLE depend on local `data/`.
- **Health line:** it shows `overall=ERROR` until the next run. That entry is the 13:53 manual
  catch-up, whose `isin_map` step failed before P8-017.
- **Paper-open staleness** still counts calendar days, not trading sessions (known Phase 1
  simplification, `desk/paper/open.py`).
- **Discrepancies in the previous handoff:** it described about 21 uncommitted files (+534/-25)
  and four syntactically invalid test calls. On resume there were 17 files (about +411/-22), all
  compiled, and the four calls were already valid. The work was verified directly, not taken on trust.

## Step 1: Stress-loss bug fix (2026-10-01)
- Fixed P8-024 where the overnight-gap stress loss multiplied the current close by the cumulative corporate-action factor, inflating the component for stocks with past splits (like BAJFINANCE).
- Regression tests added in `tests/test_desk_risk.py` for BAJFINANCE and a synthetic split showing the stress loss is invariant to historical splits.
- Reported that no committed worked example or stored decision was affected (since `data/desk/desk.sqlite` has 0 rows and is unused yet).
- Appended a dated addendum to `docs/desk/shadow_replay_prereg.md`.
