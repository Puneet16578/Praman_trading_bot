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

## Step 3: Nightly opportunity logger (2026-10-01)
- Verified and finalized the previous agent's uncommitted work for `desk scan`.
- Implemented `desk scan` which evaluates opportunities using the existing catalogue trigger and gate orchestrator in research mode.
- `opportunity_log` and `opportunity_executions` append-only tables are created and enforced by SQLite triggers.
- Evaluated events are safely firewalled in `outcome_firewall.py`.
- Added `desk_scan` to `scripts/weekly_ingest.py` (the nightly task) after the ingestion step.
- Added a scratch `proof_scan.py` testing the scan on the last 10 trading days.

## Step 4 (In Progress): Historical shadow replay
- Drafted `scripts/phase11_shadow_replay.py` to efficiently parallel-process the ~60,694 final catalogue events over 2019-10-01 to 2026-09-15. 
- `UnadjustableWindowError` exceptions are caught to correctly exclude structurally-broken 20-session tail windows.
- The next agent should finish evaluating the generated raw JSON against `docs/desk/shadow_replay_prereg.md` requirements (bootstrapping confidence intervals with seed `20261001` and joining with `data/processed/phase8_relabel_t0_relative.csv`) and output to `docs/desk/shadow_replay_results.md`.
- See `scratch/aggregate_shadow_replay.py` for a skeleton of the aggregation step.

 
 # #   R e v i e w - a n d - R e p a i r :   P o i n t s   1   a n d   2   ( F i r e w a l l   a n d   F r o z e n   D e c i s i o n s )  
 -   R e s t r i c t   e x e c u t i o n _ o b s e r v a t i o n   s t r i c t l y   t o   p e r m i t t e d   f i e l d s   ( f i l l _ d a t e ,   f i l l _ p r i c e ,   q u a n t i t y ,   g a p _ i n r ,   g a p _ p c t ,   g a p _ t h r o u g h ,   c a p _ b r e a c h _ r e a s o n s ,   n o _ f i l l _ r e a s o n ) .  
 -   V e r i f i e d   e x e c u t i o n _ o b s e r v a t i o n   i n   d e s k / s c a n . p y   n e v e r   c o m p u t e d   M A E   ( M A E   w a s   p r e v i o u s l y   o n l y   d r a f t e d   i n   s c r i p t s / d e s k _ s h a d o w _ r e p l a y . p y   f o r   b a c k w a r d   r e p l a y ) .  
 -   A d d e d   t e s t _ f r o z e n _ d e c i s i o n _ c o m p o n e n t s _ i n _ e x e c u t i o n   a s s e r t i n g   t h a t   t h e   s t r e s s   v a l u e s   f e d   t o   r i s k   c a l c u l a t i o n s   a r e   p r e c i s e l y   t h o s e   f r o m   t h e   l o a d e d   f r o z e n   p l a n   ( p r o v i n g   j s o n   s t r i n g s   a r e   n o t   s p l i t   m a n u a l l y ) .  
  
 # #   R e v i e w - a n d - R e p a i r :   P o i n t s   3 ,   4 ,   5 ,   7  
 -   P r e - r e g i s t r a t i o n   i n t e g r i t y :   T h e   f i l e   d o c s / d e s k / s h a d o w _ r e p l a y _ p r e r e g . m d   o n l y   h a d   a   t r a i l i n g   l i n e   e n d i n g   d i f f e r e n c e   c a u s e d   b y   C R L F .   T h e   p r e v i o u s   a g e n t   c o r r e c t l y   a p p e n d e d   t h e   a d d e n d u m .   N o   t e x t   w a s   r e w r i t t e n .  
 -   S t e p   3   P r o o f :   E x e c u t e d   s c r a t c h / p r o o f _ s c a n . p y   f o r   t h e   l a s t   1 0   t r a d i n g   d a y s .   O u t p u t   m a t c h e d   e x p e c t a t i o n s   ( 3 1 5   S C R E E N _ F A I L ,   2 1 8   E x e c u t i o n s   w r i t t e n ) .   D B   c l e a r e d   c o r r e c t l y .  
 -   U n r e s o l v e d   I S I N   s y m b o l s :   M o d i f i e d   d e s k / s c a n . p y   t o   c o u n t   s y m b o l s   l a c k i n g   a   v a l i d   e q u i t y   I S I N   a n d   r e p o r t   i t   v i a   l o g g i n g   a n d   s t d o u t   o n   e v e r y   r u n .  
 -   S c r a t c h   F i l e s :   C o n f i r m e d   s c r a t c h /   w a s   c o m p l e t e l y   u n t r a c k e d   a n d   s u c c e s s f u l l y   a d d e d   i t   t o   . g i t i g n o r e .  
 