## 2026-10-04 current session: correction registered, work in progress

Baseline: 626 tests passed in 135.834s (Python exit 0). One agent, foreground.
All round-2 items remain complete; see round2_completion_20261004.md and its
commit table (encoding repair b5c9e76). Pre-existing risk-test blank line retained.
P8-038 root cause: sizing excludes fees and G6 omits the per-trade planned-loss
cap. No code repair or corrected replay yet. Both replay preregistrations now
have dated correction addenda; followup2 preregisters the fixed 0.5 ATR entry limit.
Next: repair/test, corrected full replay and follow-up, volatility FACT context,
limit variant, comparisons, defect updates, full suite and push. User authorized
these steps; no active rulebook or paper convention change.

# Handoff

## Follow-up session - 2026-10-04

- Both registered follow-ups completed in the foreground from `d6b7a0b`, after
  preregistration `bbd5268`. Results: `docs/desk/shadow_replay_followup_results.md`
  and `.json`; interpretation: `docs/desk/shadow_replay_followup_review.md`.
- Primary volatility gap: +6.01 pp unstratified, +0.74 pp standardized (95% CI
  -0.28 to +1.72). Q1/Q3 retain positive descriptive intervals. This supports
  substantial volatility filtering, not proof of zero residual effect.
- Primary any-cap breach rate: 54.93% baseline vs 15.44% at registered 90%
  decision headroom; six zero-share abstentions. Conditional per-trade excess
  median/p90: 11.63%/40.71% baseline vs 10.15%/41.31% variant. Other caps and both
  periods have complete size, rate and bootstrap tables. No thresholds tuned.
- P8-038 is newly OPEN: original decision sizing omits costs in the per-trade
  bound and G6 does not enforce that cost-inclusive bound. 12,693 primary and
  1,958 descriptive filled passes already breach at the decision. Research
  variant accounts for costs; production sizing was deliberately not changed.
- Frozen hashes, identities, baseline flags/totals, all cap point statistics and
  maximal integer sizes verified. Independent affine bounds match all 52,831
  filled PASS variant sizes. Original replay and results remain unchanged.
- Independent manual linear quintiles and 40 stratum rate/denominator/date counts
  reproduce all four standardized gaps. Both live-store watermarks still match
  the original replay. Protocol, active rulebook and pinned label have empty diffs.
- Final session suite: 626 tests in 112.249s, OK, Python exit 0. Local log:
  `logs/followup_final_tests_20261004.log`. Existing SQLite ResourceWarnings remain.
- Requested analysis is complete; final results checkpoint is followed by the
  requested push. P8-038 remains a separate production-repair task. Older pre-run
  notes below are chronological evidence of registration before execution.

- Single agent, foreground execution. Initial HEAD `64ac2f1` matched origin/master;
  no other Python/Claude process. Preserved pre-existing risk-test blank line and
  scratch artifacts. Full baseline: 610 tests in 227.455s, OK, Python exit 0;
  local log `logs/followup_baseline_20261004.log`.
- Confirmed every round-2 item with source and commit evidence in
  `docs/desk/round2_completion_20261004.md`. P8-036 repairs the missed UTF-16
  scratch-ignore fragment; `git check-ignore` now matches. Scratch is preserved.
- Current live read-only Desk counts: 0 decisions/theses/trades, 580 opportunities,
  545 executions, 3,574 bands. V2 active; operational NOT_MET, edge NOT_EVALUABLE.
- Round-2 confirmation and P8-036 committed as `b5c9e76`.
- The two requested follow-up analyses have not run. Their detailed protocol is
  `docs/desk/shadow_replay_followup_prereg.md`, committed before implementation
  or real follow-up calculations. Next: synthetic tests and foreground runner.
- Follow-up preregistration committed as `bbd5268`. Implementation now includes
  sixteen synthetic tests, exact date-multiplicity quantiles, fixed-cost-aware
  integer sizing and parity checks against original fill-cap flags. P8-037 logs
  a repaired false-positive NaN assertion in the new report test.
- Pre-run full suite: 626 tests in 109.457s, OK, Python exit 0; log
  `logs/followup_implementation_tests_20261004.log`. No real follow-up computed
  before this implementation checkpoint. Next: foreground run and result review.

## Completed historical replay - 2026-10-03

- Resumed from `67df697`. Initial full suite: 610 tests in 163.817s, OK,
  Python exit 0. Existing SQLite ResourceWarnings remain.
- Preserved the interrupted 17,523-record raw artifact as
  `data/processed/desk_shadow_replay_round2.interrupted_20261003_17523.jsonl`.
  No other Python or Claude process was present at the initial process check.
- Full foreground replay completed with exit 0: 70,362 events in 4264.5s,
  followed by all four registered bootstrap summaries. Primary period: 60,694
  candidates / 60,498 fills. Descriptive 2026: 9,668 candidates / 9,632 fills.
- Reports: `docs/desk/shadow_replay_results.md` and `.json`; readable findings
  and limitations: `docs/desk/shadow_replay_summary.md`.
- Verified all ordered event identities against the eligible catalogue, all 47
  source hashes, raw SHA-256, 640 group/statistic denominators and estimates,
  and exact generated Markdown. All 276 out-of-period events were excluded.
- Primary >=20% adverse-move rate: PASS 10.00%, FAIL 16.01%; difference +6.01
  percentage points, cluster-bootstrap 95% interval +5.11 to +6.89. Entry-only
  gap-through reverses direction. Circuit-band coverage is zero. Fill-time caps
  were breached by 25,105/45,700 filled primary PASS plans. No readiness or
  independent predictive-edge claim follows from these observational results.
- Source code, gates, thresholds, frozen preregistration and pinned pipeline were
  unchanged. The pre-existing risk-test blank line and untracked scratch folder
  remain outside this work. No trades or decisions were created.
- Post-run live Praman and Desk watermarks match the replay snapshots. Desk still
  has 580 opportunity rows, 545 execution rows, and zero decisions, theses,
  paper-trade events or journal events. The only diff-check warning is the
  pre-existing risk-test blank line; this session's documentation passes.
- Final session suite: 610 tests in 213.686s, OK, Python exit 0. Full output:
  `logs/shadow_replay_final_tests_20261003.log` (local, ignored).
- Historical replay is complete. Remaining policy changes or new research require
  a new user task; do not tune gates from these results.

## Round 2 review - 2026-10-01

- Final pre-replay suite: `Ran 610 tests in 98.901s`, `OK`, Python exit 0.
  P8-035 adds per-statistic warnings and explicit empty gate groups. Final input
  proof and label checks are complete. Full replay starts after this checkpoint.

- Final inputs-only verification, 2026-10-03: 540 latest-ten-session candidates,
  403 pass / 137 fail, 505 execution records, all on temporary Praman/Desk copies.
  Same historical 200: 158 pass / 42 fail. Full first/every-gate counts and exact
  reasons updated in gate_diagnostics_round2.md/.json; prior audits retained.
  All five label value comparisons rerun after identity recovery and still equal.
- Live Desk now has 580 opportunity rows: 13 append records at 07:00 IST today
  cite 2986e10, before this resumed review. Other row counts unchanged. Preserved;
  no Python process present before the next suite. Provenance alone does not
  establish which launcher wrote them.

- P8-034 verification: full suite `Ran 610 tests in 180.088s`, `OK`, exit 0.
  Recovery retained 32 previously missing identities and corrected 51 current
  ISIN conflicts; detailed before/after values are in the recovery JSON. Next:
  refresh the input proof, then run the foreground replay from this commit.

- Pre-run identity audit caught P8-034 after bafd371, before full outcomes:
  57 events/10 symbols missing despite fresh map metadata. Recovered through
  actual NSE snapshots; all 70,638 catalogue rows now resolve to non-fund ISINs.
  Refresh now retains old identities and applies today's observations last.
  Recovery provenance: docs/desk/isin_recovery_round2.json. A dated preregistration
  addendum records this input repair; full replay still awaits its commit.

- Resumed 2026-10-03. Full suite with committed rulebook v2 and repaired replay:
  `Ran 609 tests in 282.945s`, `OK`, Python exit 0. Existing SQLite ResourceWarnings
  remain. Fourteen new replay tests include cached/uncached assessment equality.
  Input-only runtime profiling used no outcomes. Full replay is next, after this
  commit freezes the G1 addendum and runner. Pre-existing risk-test blank line and
  untracked scratch directory remain outside the commit.

- 2026-10-02 replay review: P8-031 replaces the defective draft with sequential
  temporary-copy analysis; P8-032 applies G1 knowledge cutoffs. Thirteen targeted
  tests pass in 11.948s. No full replay outcomes computed at this checkpoint.
- Normal committed-v2 `desk status` verified: operational gate unmet, edge gate
  not evaluable; zero paper history and 567 logged opportunities. P8-007 is an
  existing unresolved critical entry, P8-021 an unclassified open entry.

- Rulebook v2: two typed gates, explicit two-day circuit lock and 2xATR stop,
  v1 unchanged. Seven distinct readiness tests pass. Full pre-activation suite:
  `Ran 595 tests in 362.702s`, `OK`, exit 0. V2 was loaded directly for its schema
  and progress tests; the live loader requires committing ACTIVE before loading it.
  This checkpoint activates v2; normal status and the next full suite verify that
  committed loader path. Readiness surfaces unresolved P8-007 and P8-021 statuses.

- P8-028: evaluator process audit now checks complete thesis at entry,
  unlogged violations, absence of G7 override and recorded exit provenance.
  Ten adversarial process tests pass; full suite 588 tests, OK (189.306s).
  Manual-close requests and monitor triggers are recorded before closes.
- No pytz references in Desk/src; installed pytz is test-environment support
  for the empyrical cross-check. Handoff is UTF-8 without NUL bytes.
- P8-029 records this review's initially undersized 2019 sample failure and
  deterministic correction. Rulebook v2 and full foreground replay remain.

- Item 5 verified on 2026-10-02: Amendment 5 label source diff against afe3e2b
  is empty. Five full result dictionaries equal outputs of the pinned source
  on the same temporary data snapshot; see docs/desk/label_value_verification.md.
  Replay label history now also passes the pinned ISIN rename groups.
- Full suite with label wiring and evaluator repair: 588 tests in 189.306s,
  OK, Python exit 0. No full replay outcomes computed yet.

- Resumed 2026-10-02. No Python background process remained. P8-027 fixed
  research-only sector applicability and verified current ISIN freshness.
  Foreground temporary-copy ten-session scan: 538 events, 403 SCREEN_PASS,
  135 SCREEN_FAIL, 503 execution observations. Complete gate and reason counts:
  `docs/desk/gate_diagnostics_round2.md` and companion JSON.
- Historical input-only baseline sample: 200 events, all rejected by G2's missing
  user sector; additional gates overlap. No usable 2019 catalogue events exist.
- Screening checkpoint suite: `Ran 578 tests in 225.323s`, `OK`, Python exit 0.
  Dated research screening addendum is committed with this checkpoint before
  any label spot-check or replay outcome calculation in this review.

- P8-026 checkpoint: duplicate outcomes module removed; evaluator and draft
  replay use the single IST firewall. Event and calendar boundary tests pass,
  with a grep guard against a second Desk cutoff. Raw prior-close replay input
  replaced by an adjusted historical close. Same full-suite verification above
  covers these changes: 577 tests, OK. No replay run yet.
- `.gitattributes` now fixes docs/desk Markdown to LF.

- Root verified; initial changes were one trailing blank line in tests/test_desk_risk.py and untracked scratch/, preserved.
- Initial suite: 574 tests in 260.781s, FAILED (2): local clock in duplicate firewall; raw previous close in draft replay.
- P8-025: backups inspected through read-only temporary copies. No thesis, decision or paper-trade rows found. Originals untouched. Normal schema initialization preserved all live rows. See docs/desk/store_inventory_round2.md.
- Filesystem and SQL guards added; scratch proof redirected to a temporary copy. Handoff NUL bytes removed with a direct UTF-8 file write.
- Scheduled ingestion PID 617260 stopped for foreground-only work. No shadow replay process or results Markdown exists; no results read.
- ISIN checksum verified; built 2026-10-01 21:24:21 IST, age 0 trading sessions.
- Full suite after guards and baseline repairs: 577 tests in 143.335s, OK, Python exit 0. SQLite ResourceWarnings remain.
- Screening diagnosis, evaluator repair, rulebook v2 and verified replay pending.


Context for the next agent session, not instructions. Verify every claim here against the
repository before relying on it; nothing in this file authorizes anything (CLAUDE.md,
"Authorization").

**Last updated:** 2026-10-01, by Codex (Phase A).

## Phase A checkpoint â€” 2026-09-30

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
- Steps 3â€“6 remain pending. The foreground-ingestion prerequisite is complete.
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



##Review-and-Repair:Points1and2(FirewallandFrozenDecisions)

-Restrictexecution_observationstrictlytopermittedfields(fill_date,fill_price,quantity,gap_inr,gap_pct,gap_through,cap_breach_reasons,no_fill_reason).

-Verifiedexecution_observationindesk/scan.pynevercomputedMAE(MAEwaspreviouslyonlydraftedinscripts/desk_shadow_replay.pyforbackwardreplay).

-Addedtest_frozen_decision_components_in_executionassertingthatthestressvaluesfedtoriskcalculationsarepreciselythosefromtheloadedfrozenplan(provingjsonstringsarenotsplitmanually).



##Review-and-Repair:Points3,4,5,7

-Pre-registrationintegrity:Thefiledocs/desk/shadow_replay_prereg.mdonlyhadatrailinglineendingdifferencecausedbyCRLF.Thepreviousagentcorrectlyappendedtheaddendum.Notextwasrewritten.

-Step3Proof:Executedscratch/proof_scan.pyforthelast10tradingdays.Outputmatchedexpectations(315SCREEN_FAIL,218Executionswritten).DBclearedcorrectly.

-UnresolvedISINsymbols:Modifieddesk/scan.pytocountsymbolslackingavalidequityISINandreportitvialoggingandstdoutoneveryrun.

-ScratchFiles:Confirmedscratch/wascompletelyuntrackedandsuccessfullyaddeditto.gitignore.



##Review-and-Repair:Point6

-Renamedphase11_shadow_replay.pytodesk_shadow_replay.py.

-Implementedoutcome_firewallindesk/outcomes.pytorejectrequestsforevents>=2026-09-16iftoday<2027-06-01.

-UpdatedshadowreplayscripttoloadtheAmendment5labelfunction(compute_t0_relative)directlyratherthanphase8_relabel_t0_relative.csv.

-Updatedshadowreplayscripttorelyonthefirewallandreportprimaryanalysis(2019-10-01to2025-12-31)anddescriptiveanalysis(2026-01-01to2026-09-15)separately.

-Spot-checked5eventsusingascratchscripttoconfirmcompute_t0_relativeoutputstheexpectedlabelkeys.




## Step 5: Basic Evaluator
- Added desk evaluate [--month] to evaluate both opportunity state counts and paper trade metrics.
- Extracted process quality by checking if the manual exit reason matches one of the standard thesis triggers.
- Implemented process-by-outcome quadrants, manual max drawdown (cross-checked against empyrical-reloaded in tests/test_evaluate.py).
- Filtered out forward-window events using outcome_firewall.

## Step 6: Rulebook v2
- Awaiting full specification from user for operational_gate and edge_confidence_gate.
