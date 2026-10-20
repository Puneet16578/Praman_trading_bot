## 2026-10-21 (Codex): S1 restored work and nightly review

- User reported stashing the pending S1 changes with `git stash push -u`, then
  restoring them with `git stash pop`. Restored status and source diffs match the
  recorded pending changes: evaluation/execution/statistics, execution tests,
  P8-098 and the completed input-report pair. No pre-stash byte manifest exists.
- `logs/weekly_ingest.log` confirms the 20 October 18:00 and 20:00 runs skipped
  because uncommitted S1 source files and DEFECT_REGISTER were present; no steps
  ran. Leaving that tree dirty caused the skips. Commit tested work or stash
  unfinished work before stopping, and before 17:40 on weekdays.
- The 22:00 retry finished at 23:58:44, backups OK, overall WARN, no failed step.
  User reports exit 0. Task independently checked Ready before tests.
  Bhavcopy gap after six attempts and ISIN HTTP 404 are logged; existing map kept.
  User identifies 20 October as Dussehra/NSE holiday. No new trading session was
  expected; the brief correctly refers to latest stored session 19 October.
- Brief review: the in-progress ingestion status was written before backup
  completion. Existing battery gaps (15/16 October) and incomplete disclosure
  date (13 October) remain visible. OPEN_CRITICAL_DEFECT is active for unclassified
  P8-088; parser heading mismatch logged as P8-099, no operational fix attempted.
- Session-start/full suite: Ran 1109 tests in 216.204s, OK, exit 0; existing P8-088
  ResourceWarnings remain. Restored source fixes committed as a1e041c.
- Completed inputs verified by artifact/parent hashes and unchanged primary
  populations/terciles. P8-096 resolved. Frozen reports preserve pre-nightly
  provenance; no attempt to rebuild against the subsequently updated live stores.
- User explicitly approved continued implementation and sealed rehearsal in chat.
  Real development evaluation remains unrun and requires separate approval.
  This handoff is context, not authorization.

## 2026-10-20 (Codex): S1 implementation planning only

- Read the registered S1 protocol and research registry, frozen A/B/C funnel, T1
  identity/calendar/bootstrap/rehearsal, S0 execution/sizing/locks, outcome readers,
  firewall and active costs. Implementation plan presented in the session response.
- No implementation, S1 counts, outcome computation, downloads or store writes.
  Protected rules, registrations, costs, firewall, S0 seal and task are unchanged.
- Unresolved: S1 next-open retry versus S0 rechecking a blocked stop; scheduled-only
  overlap is not necessarily an upper bound on actual skips when exits are delayed;
  binding-evaluation release condition versus the shared firewall's date-only check.
  No resolution selected. Implementation and development evaluation await approval.
- Started clean at 82ebd31. Start suite: Ran 1073 tests in 212.828s, OK, exit 0.
  On resume, ingestion task Ready and tree clean. End-suite evidence is recorded in
  this handoff commit message. Existing P8-088 ResourceWarnings remain.
- This handoff is context only and authorises no further action.
## 2026-10-19 (Codex): S1 and trading research registry registered; documents only

- Approved by the user in their message of 19 October 2026; registered 19 October 2026
  at d176f414eb6371ddb6eccddff778ca19f41f9218. The user explicitly instructed proceeding
  after the earlier 17:40 cutoff. Implementation and evaluation remain separate tasks.
- Added docs/desk/s1_unexplained_drop_prereg.md and docs/desk/trading_research_registry.md.
  Applied only the five final decisions, weekend-hold limitation and registration/status
  edits. Section 11 removed; rules placed in execution, metrics and limitations sections.
  S1 v1 is REGISTERED, not implemented or evaluated; h=5/h=10 remain NOT ATTEMPTED.
- Original approved drafts remain unchanged in
  C:/Users/VICTUS/AppData/Local/Temp/praman_s1_draft_20261019_2d83e28/.
  The final diff is provided there as s1_registration_final.diff; no new research counts,
  outcomes, code, configuration, store, firewall, seal or task changes.
- Started on clean master at 4ae4f729eaf64d7179796536b439e051efca2b9c. Ingestion Ready;
  no active Python process; existing Claude session's last entries were end_turn.
- Start suite: Ran 1073 tests in 200.899s, OK. Pre-registration-commit suite:
  Ran 1073 tests in 200.569s, OK. Both Python exits 0. Existing P8-088 SQLite
  ResourceWarnings remain. End-suite evidence is in this handoff's commit message.
- Follow-up documentation records the actual registration hash in both documents and
  this handoff; it changes no research rule. This note authorises no implementation.

## 2026-10-19 (Codex): S1 draft revisions; documents only

- User's latest decisions replace the earlier S1 proposals; final text still awaits separate approval.
- Revised the same two files outside Git in
  C:/Users/VICTUS/AppData/Local/Temp/praman_s1_draft_20261019_2d83e28/:
  s1_preregistration_DRAFT.md and trading_research_registry_DRAFT.md.
  Saved text was read back and matched the prepared revisions exactly.
- C1-C6 incorporated: dated identity assumptions throughout; no GSM research filter;
  one-/three-session horizons; separate weekday execution/bootstrap calendar; binding-evaluation
  firewall; descriptive audit metrics. S0 entry/sizing/stop quotes, costs, data gaps, boundaries,
  minimums and bootstrap decisions incorporated. D/E/F now use the user's intraday definitions;
  S1 horizons 5/10 recorded as not attempted. Existing attempt/exposure inventory retained.
- Remaining definition gaps: MAE and descriptive-path endpoints, benchmark/metric conventions,
  interior missing bars and post-missing position status, historical operational-switch scope.
  Relevant potentially conflicting texts are quoted; no fix selected. The old next-open entry
  sensitivity is superseded by the user's same-execution instruction.
- No code, new research counts, outcome computation, data download, store write, rule/configuration,
  preregistration, firewall, seal or task change. The draft files are not staged or committed.
- Started on clean master at 0cd41bc4cf3ef5d3f26e841b5c6288b8ca854bfd. Ingestion Ready;
  existing Claude process's last session entries were end_turn, with no active Python process.
  Start suite: Ran 1073 tests in 243.126s, OK, Python exit 0. Existing P8-088 SQLite
  ResourceWarnings persist. End suite result will be recorded in this note's commit message.
- Only this session-rule handoff note is committed. This note authorises no next action.
## 2026-10-19 (Codex): S1 / idea B registration drafts only

- Started on clean master at 2d83e28c5d1d094fd1ee0be65b77a36f2355cb2e; ingestion task Ready.
- Read the governing rules, corrected A/B/C reports, S0 execution/cost sources and T1 protocol.
  No new data counts, outcome calculations, downloads, store writes or implementation.
- Unregistered drafts are outside the repository in
  C:/Users/VICTUS/AppData/Local/Temp/praman_s1_draft_20261019_2d83e28/:
  s1_preregistration_DRAFT.md and trading_research_registry_DRAFT.md.
  Full draft text is also in the session report; temporary files are not durable registration.
- Unresolved conflicts: current identity map versus PIT; using 2025 GSM inputs to justify a
  strategy choice; proposed horizons versus blueprint scope; funnel calendar versus T1's
  weekend exclusion (T1-specific); fixed 1 June release if read as overriding binding evaluation.
  The proposed metric list also omits parts of the blueprint's minimum economics/tail-risk audit.
- Open definitions include quantity/slippage (active S0 limit fills apply no extra slippage),
  bootstrap blocks/seed, missingness, entry-day stops, delayed exits, known GSM and timing.
  No fix or rule exception was selected. S0 stop/holding rules differ from the proposed S1 rules;
  importing S0's entry model does not import its complete strategy.
- Registry draft preserves T1 failures, S0 versions, shadow attempts and forensic exposure;
  D/E/F have no descriptions established in the inspected committed documents.
- Session-start suite: 1,073 tests in 250.711 s, OK. End-suite result is recorded in this note's
  commit message. Existing SQLite ResourceWarnings (P8-088) remain unchanged.
- Only this HANDOFF note is committed. Registration approval, implementation and evaluation
  remain separate future steps; nothing here authorises them. Firewall, seal, task, rules,
  costs and all existing preregistrations are unchanged.

## 2026-10-19 (Claude, from about 11:50): A/B/C small follow-up, items 1-5

- Item 1 b72f913: P8-093 fixed. Item 2's `_calendar` keeps only sessions with an EQ bar known on
  their own day, independent of the requested dates. Callers: item 2's script (default mode and
  `--repaired`) and abc_followup_counts.py `event_inputs` (B funnel, A clean pool); nothing in the
  desk, nightly, T1 or forensic pipeline imports it. The new test fails on the old code.
- Item 2 ebf79a8: regenerated item 2 (`--repaired --years`, new), the B funnel and the clean pool,
  each run twice in capped foreground pieces with matching per-year digests. Dated notes give the
  before -> after sizes, and the pre-fix tables are kept in both reports. Key changes: market
  unknown 638 -> 0 events; funnel 09:00 end counts 2020-2025 now 30, 172, 77, 297, 178, 268; pool
  3,402 -> 3,388. Not rerun: item 1's default mode (over 10 min). Found: the pre-fix 120-session
  sensitivity table looks miscopied (noted in the report and in P8-093; can't be checked, as the
  old output wasn't kept).
- Item 3 8a0cc90: March 2020 and March 2021 results coverage with a 125-day window beside 75
  days: 88.2% and 89.5% (28.6% and 56.9% at 75). 272 and 31 symbols are covered only by filings
  after 30 June, which may be June-quarter results. SEBI's actual deadlines were not checked.
- Item 4 8fd9ba0: largest number of B survivors on one date per year and cut-off (section 3e).
- Item 5: read-only quotes for B's registration given in the session report; no edits.
- End-of-session suite: 1,073 tests in 244.374 s, OK (14:34-14:38). Nothing stashed.
- An item 1 default-mode run exceeded 10 min and was auto-moved to the background. I stopped it at
  once; later runs were capped with `timeout` in the foreground. No store, rule, firewall, seal,
  Windows task, cost config or pre-registration change; no downloads; no NSE pages.

## 2026-10-19 (Claude, from 10:10): A/B/C follow-up items 3-6 finished after Codex stopped

- Start: no Python process running; tree had 4 changed files, not the 5 described
  (docs/desk/abc_sourcing_check.md was unchanged). Session-start suite: 1,061 tests OK.
- Item 3 6e57d73 (Codex's funnel, reviewed): market/peer definitions match item 2; price and filing
  cut-offs hold. Review changes: --years and notes parts; per-year runs request the full run's
  dates (P8-093, item 2's calendar depends on requested dates; item 2 left unchanged, fix proposed);
  1/10-session step tables; extra diagnostic clarification sub-counts; end-to-end tests (no bar after
  D read; late filing or SEBI order removes nothing; one-year run streams the same sessions).
  Two runs (full 9 min 12 s; per-year pieces) give identical per-year digests. Final 09:00 counts
  2020-2025: 28, 172, 74, 295, 178, 268. Dividend amounts: 6 of 5,604 record-date filings parse.
- Item 4 12f2f36: A's clean pool 3,402 events; 1,446 more with board outcome / press release.
- Item 5 cc408c1: results coverage by quarter, steps (a)-(d); 2022 gap quarters ~36-37%, 2025
  recovered by board outcomes (95.6% for Sep 2025); Mar 2020 and Mar 2021 low (not investigated).
- Item 6 2a7705e: sourcing check, documentation only; NSE and NSE Indices pages timed out for the
  reader (unreadable, not worked around); SEBI 2005 circular confirms same-day after-hours deal
  disclosure; Codex's F&O-ban "next trade date" not re-checked; MSCI terms forbid bots/AI agents.
- No store, rule, firewall, seal, Windows task or pre-registration change; no downloads.
- End-of-session suite: 1,069 tests in 210.198 s, OK (11:41-11:45). Nothing stashed.

## 2026-10-18 (Codex): both T1 rehearsal checks passed before once-only 2025 evaluation

- Clock-test fix 9cc2558 pushed; runner a51cff1 passed 1,049 tests in 215.789 seconds.
- Development random-label artifact data/t1/rehearsal_20261018T161737Z.json matches
  every saved analytical field of the third rehearsal exactly. Runtime 29.0 seconds;
  peak working set 2,098,688,000 bytes (execution metadata reported separately).
- Hold-out random-label rehearsal completed with reader/firewall sealed and a
  2025-12-31 read ceiling. Tables: docs/desk/t1_holdout_rehearsal_2025.md.
  228 decision sessions through Dec 2, 20 purged sessions Dec 3-31; 395,621 eligible
  stock-days, 21,301 identity exclusions, 386,055 complete windows (97.5820292654%).
- All state coverage 100%. V1/V2 spells 1/2 and usable draws 1,718/1,715 necessarily
  imply INCONCLUSIVE; these are registered statistical limits, not execution errors.
  V3 has 2,000 usable draws. No criteria were loosened or changed.
- Locked development boundaries and weights are read unchanged (all weights 0.2).
  All four development artifact hashes match before/after both rehearsals.
- Next action is the user's approved once-only `python -B scripts/t1_holdout.py evaluate`
  on clean master. It records commit and input hashes before real outcome access,
  refuses source/input/rehearsal mismatch or any repeated attempt, and writes the
  full results/manifest. Commit those immediately, then push. No automatic retry.
- At this pre-run commit no real hold-out outcome has been read. If the result file
  docs/desk/t1_holdout_results_2025.md exists, treat it as locked and do not rerun.
- P8-088 ResourceWarnings remain open; no other clock/log test changes. No 2026
  input/outcome payload, real trade action, nightly task or Strategy 0 change.

## 2026-10-18 (Codex): T1 runner work resumed after P8-090

- Clock-isolation fix 9cc2558 passed 1,039 tests and was pushed.
- Restored the prepared T1 stash; merged both handoff/defect notes without changing
  runner code. Earlier stop notes below describe the previous attempt, now resumed.
- Runner full suite: 1,049 tests in 215.789 seconds, OK. P8-089 resolved.
- Full suite and runner commit precede both random-label rehearsals. All checks must
  pass before the single approved 2025 evaluation. No real hold-out run yet.

## 2026-10-18 (Codex): P8-090 ingestion-health clock test isolation

- User authorised a separate test-only fix before restoring the T1 hold-out stash.
- Fixed 21:00 IST clock for runner/display; one private log per OK/WARN/ERROR case.
  No production clock, retry behaviour or task change. Ten targeted tests pass.
- Full suite: 1,039 tests in 186.212 seconds, OK.
- P8-090 records the defect; docs/desk/test_clock_log_audit_20261018.md lists other
  clock/log dependencies without changing them. P8-088 warnings remain unfixed.
- Next authorised step after this commit/push: restore the prepared T1 runner stash,
  pass the full suite, commit it, then development and hold-out random-label rehearsals.
  Real 2025 evaluation is approved once only after all checks pass; never auto-retry.

## 2026-10-18 (Codex): T1 hold-out preparation stopped at unrelated suite failure

- Prepared runner patch preserved in stash `t1-holdout-prepared-blocked-by-ingestion-clock-test`.
- 30 focused tests pass. Full suite 1,049 tests in 231.837 seconds: one failure,
  test_isin_map_operations.IsinRefreshTest.test_summary_health_levels_and_warn_exit_status.
- Isolated test reproduces the failure after 18:00 IST: real clock + shared temp log
  makes WARN/ERROR cases skip as retries of the first OK case. No unrelated fix made.
- No development regression rehearsal, hold-out rehearsal or real hold-out run occurred.
- All four locked development artifacts still match their recorded SHA-256 hashes.
- Nightly task state rechecked: Ready. Master is left clean; no code commit or push
  because AGENTS.md requires a passing full suite. P8-089 repair remains pending.
- Next step needs the user's decision on the unrelated test's clock isolation.

## 2026-10-18 (Codex): approved T1 hold-out runner preparation

- User approved the runner changes required by P8-089 and one 2025 evaluation only
  after development regression and a sealed random-label hold-out rehearsal pass.
- Pre-registration 99-101 freezes development quintiles for 2025; 144-145 freezes
  development candidate shares. Both are read from hash-verified locked artifacts.
- Explicit hold-out input scope ends at 2025-12-31; development defaults stay at
  2024-12-31. The real firewall, feature formulas and registered settings are unchanged.
- New entry point scripts/t1_holdout.py has separate rehearsal/evaluation modes,
  immutable attempt protection and pre-outcome code/input provenance. Never retry
  a failed real attempt automatically. Development artifacts must remain unchanged.
- Initial suite: 1,039 tests in 330.918 seconds, OK; P8-088 warnings remain unfixed.
- No real hold-out outcome has been read at this preparation stage.

## 2026-10-18 (Codex): single T1 development evaluation completed and locked

- Loader repair fcf9711; third rehearsal matched all saved analytical fields.
- Runner frozen at a4aa42ddba347517f0f00b4c0870231b758b3dc5 on clean master.
  Full suite before outcome access: 1,039 tests in 263.863 seconds, OK.
- One invocation of `python -B scripts/t1_development.py`, exit 0; no crash/retry.
  Commit and 59 file hashes plus bounded logical SQL-row hashes were recorded
  before real outcome access in docs/desk/t1_development_manifest_20261018.json.
- Results and manifest committed immediately as 1bca727. Locked report:
  docs/desk/t1_development_results_20261018.md. No code, setting, threshold or
  result changes after outcome access. Local machine output is
  data/t1/development_20261018.json; persistent .started.json marker prevents rerun.
- All three verdicts FAIL, not INCONCLUSIVE. Standardised differences / family
  98.333333% intervals (percentage points): V1 +3.04997524 [-1.94362883,10.65590136];
  V2 +6.43782516 [-3.53869400,25.50255506]; V3 -1.25378450 [-2.36239255,-0.53342089].
  Positive quintiles 5/5,5/5,1/5; coverage 100%,85.73402876%,98.41256713%; usable
  draws 2000,1999,2000. Applicable spells 9/13 and all cell minimums satisfied.
  No primary contrast unavailable. V1/V2 fail the strictly-positive family lower
  bound; V3 also fails magnitude and directional consistency.
- Identity exclusions 186,581 disclosed. 2025 remains PARTIALLY EXPOSED as required;
  no 2025 input/outcome payload read for this evaluation, and no hold-out run.
- These are conditional historical associations with shared-price coupling, not
  profitability, calibration or permission to activate risk rules. No policy change.
- P8-087 resolved; P8-088 low-priority SQLite ResourceWarnings remains open/unfixed.
  No further tests or computations after the real run; this final edit is handoff only.
- Monday after-run Part 2 remains deferred until the user asks.

## 2026-10-18 (Codex): P8-087 repaired; third rehearsal matched; evaluation runner frozen

- fcf9711 closes P8-087: all development loaders bound before SQL/payload reads;
  later source files skipped, mixed-range files refused, no post-end session query.
- Third random-label rehearsal at fcf9711: `data/t1/rehearsal_20261018T105905Z.json`.
  Every saved analytical field exactly matches the second rehearsal; execution
  timing/memory differ normally. Report: docs/desk/t1_rehearsal3_20261018.md.
- The user authorised the real development evaluation once after that match.
  `scripts/t1_development.py` now prepares its immutable attempt marker and records
  the clean-master commit plus bounded file/logical-row hashes before outcome access.
  The existing reader/firewall evaluates development only. Full tables render to
  docs/desk/t1_development_results_20261018.md; the script refuses a second attempt.
- Validation before real outcome access: 61 focused T1 tests pass; full suite
  1,039 tests in 263.863 seconds, OK, exit 0. P8-088 ResourceWarnings recur, unfixed.
  Input provenance preflight verifies 59 files, 1,300 stored calendar dates,
  2,199,596 EQ rows and 699 action rows within bounded SQL; no outcome computed.
- No real evaluation has run at this preparation commit. Next action is the single
  approved evaluation, followed immediately by committing its result and manifest.
  No code/settings/threshold changes after seeing results; crash/bug means STOP.
- 2025 hold-out and Monday after-run Part 2 remain unstarted.

## 2026-10-18 (Codex): once-only T1 development evaluation stopped in preflight

- Clean master at 9dea1e8b785b4c4aeb0c044e8774478c3210ea7d before inspection.
- Reconciled the 350: 183 already excluded fund units, 166 incomplete ATR windows,
  1 unadjustable ATR window. All move to identity_unknown; only 1,803 lose eligibility.
  Input-only read-only audit, no real outcomes. No count bug.
- P8-087 OPEN: panel loader queries dates after the development end; index/ISIN
  loaders read later files before trimming. Violates the user's strict no-2025-read
  requirement. Found statically before running these loaders or any real evaluation.
- Stopped as instructed. No evaluation attempt, results file, verdict or real-outcome
  access; no code/settings/threshold changes, workaround or retry. Repair and a run
  need the user's next instruction. See docs/desk/t1_development_preflight_20261018.md.
- P8-088 OPEN, low priority: SQLite ResourceWarnings from the prior 1,029-test passing
  suite logged, not fixed. Documentation-only changes; no test rerun after the stop.
- Nightly task checked read-only: Ready. No durable-store or task changes.
  2025 hold-out and Monday after-run Part 2 remain unstarted.

## 2026-10-18 (Codex, Part 1): T1 addendum 3, timing repair, second rehearsal, brief

- User resolved two protocol conflicts explicitly. Final timing keeps stock EQ
  bars on D as a labelled ASSUMPTION, preserves eligibility/ATR/breadth definitions,
  leaves index/VIX on D-1, and makes ISIN snapshots available from S+1 (ASSUMPTION).
- 040cdef: item 1 timing audit, 19 focused feature tests passed.
- 70ebf4b: item 2, addendum 3 recorded separately; 38 focused T1 tests passed.
- 127f0d4: item 3, P8-085 resolved; ISIN strictly after snapshot date, weekend
  exclusion default, updated report assumptions/counts; 51 focused T1 tests passed.
  No other timing calculation changed. Real development outcome run remains unwired.
- Second rehearsal: `docs/desk/t1_rehearsal2_20261018.md`, artifact
  `data/t1/rehearsal_20261018T055421Z.json`. Real reader/firewall sealed throughout;
  seeded random labels only. 34.1 seconds, 2,091,749,376 bytes peak; 1,620,100 eligible
  stock-days, 186,581 identity exclusions (was 184,428). V2 coverage 85.7340%, V3
  98.4126%; V1/V2 spells 9/13; usable draws 2000/1999/2000. All cells clear minimums.
- dea07c7: item 4, brief labels all G1-G6 and adds fixed-category rejection counts
  from stored gates; P8-086 resolved; 16 brief tests passed. The read-only 14 Oct
  line exactly matches the requested text (`docs/desk/screening_brief_20261018.md`).
  No real brief file was written or overwritten; no decision logic changed.
- No authenticated Angel calls, downloads, NSE page reads, credentials, real T1
  outcomes, durable-store changes or Windows-task changes. Task state checked
  read-only: Ready. Firewall and Strategy 0 seal unchanged.
- Full suite run once at end: 1,029 tests in 231.224 seconds, OK, exit 0.
  Unclosed SQLite connection ResourceWarnings appeared in existing tests; no failures.
  No further code changes after this full-suite run.
- Part 2 remains deferred until the user asks after Monday's nightly finishes.
  No Monday run, catch-up or retry claim has been made in this session.

## 2026-10-18 (third round): T1 addendum stopped again; rehearsal; battery retry live (Claude)

- 1 T1 addendum 3: STOPPED, nothing recorded. (d) refers to "the evidence or ASSUMPTION labels the
  build already carries", but for stock bars (knowledge kept as a date; the build uses a bar on its
  own session, while the pre-registration says date-only evidence counts from the next session) and
  for the ISIN snapshots (no Last-Modified kept; no label) there are none. Logged as P8-085 (open).
  (h) also needs one word: the purged December sessions leave the bootstrap's dates, but their bars
  must still complete the outcome windows of the last development decisions.
- 2 bfee6cc + 3c9f385 T1 rehearsal (docs/desk/t1_rehearsal_20261018.md): real store, seeded random
  labels, real outcome sealed and tested; 31.9 s, 2.09 GB peak, no errors; coverage V1 100%, V2 85.7%,
  V3 98.4%; every cell >= 100 windows and 30 dates; usable draws 2000/1999/2000. Real run not started.
- 3 8266abf P8-084 decision time confirmed and recorded in the audit note.
- 4 6ad52de battery retry (option A): 20:00 and 22:00 weekday triggers added to PramanDailyIngest
  (still one task; 18:00 trigger, action, settings and principal identical to the backup in
  logs/task_backups/); a run started this evening counts as done; one skip notice per evening.
- 5 Checks list and 14 Oct counts: in the report; nothing changed.
- Full suite: 1019 tests in 205.301s, OK, exit 0 (10:40-10:44). Nothing stashed.
- Part 2 (after Monday's run, when the user says): as before, plus whether the 20:00 and 22:00
  triggers fired and did nothing (look for "weekly_ingest retry not needed" lines in the log).

## 2026-10-18 (second round, Part 1): T1 addendum stopped; P8-084 two clocks; battery retry proposal (Claude)

- 1 T1 addendum: STOPPED, nothing recorded. Part (a) conflicts with the pre-registration ("A stock
  without a price on a global session has missing input; never forward-fill it into breadth or the
  study"): a next file's previous close is an older close for a symbol that did not trade on the
  missing day (late sessions: 7, 1, 0 and 3 such symbols; for 2022-08-08 there is no file to tell
  which of 1,815 traded). For the user. (h) also needs a word on the 20 purged December sessions.
- 2 The five readings are quoted in the report for the user's confirmation; no development run.
- 3 790075a P8-084 fixed for replay paths: desk assess --as-of and desk scan --date for a past
  session read only rows stored by the end of that IST day; audit replay reads the decision's own
  thesis by id. Reader table in docs/desk/knowledge_date_audit_20261018.md. 7 tests.
- 4 9aadc4e docs/desk/battery_retry_proposal_20261018.md: options A (20:00 and 22:00 triggers), B
  (power-source event 105, logged on this laptop), C (restart on failure); nothing changed.
- 5 Confirmed: a fill on day D uses NSE's list dated the session before D, read as of the run date;
  circuit_bands (with its catch-up) runs before auto_paper.
- Full suite: 1002 tests in 213.606s, OK, exit 0 (09:58-10:02). Nothing stashed.
- Part 2 waits for the user after Monday's run.

## 2026-10-18 (Sunday): Part C, knowledge-date audits, T1 coverage decisions, T1 outcome step (Claude)

No nightly until Monday 18:00; no logged-in Angel call; no download; no NSE page read; firewall,
seal and pre-registration unchanged.
- 1 d62f6e1 Part C (docs/desk/after_run_checks_20261014_16.md): 14 Oct ran 19:31-20:11, all 14 steps
  OK; 15 Oct (13%) and 16 Oct (18%) skipped on battery, no step ran, so Monday's run catches up and
  records 15 and 16 Oct as Strategy 0 burn-in gaps. Tick sizes once (14 Oct: 2,723; 0 unknown of
  2,689); 15-16 Oct ticks UNKNOWN for good. Announcements 14 Oct COMPLETE through 13 Oct, no
  whole/split mismatch. The 14 Oct run fetched the 13 Oct list (NSE 19:00 on 13 Oct, known 14 Oct)
  and the 14 Oct list; the Data health WARN never appeared. The user's after-hours run did not happen.
- 2 6773ef7 P8-083 audit: 0 band rows known before we fetched them (24,978 stored before 3d7423e, all
  same-evening); no decision affected; nothing to correct. September lists lost in P8-025.
- 3 c256983 audit of source-dated data (docs/desk/knowledge_date_audit_20261018.md): bhavcopy,
  announcements, identities, corporate actions, ASM/GSM and tick sizes are source-dated; a late file
  is invisible to live decisions and replays but visible to later live recomputations (P8-084, open).
- 4 1aa76c7 docs/desk/t1_coverage_decisions_20261018.md, input counts only (no outcome exists or was
  read): V2 coverage 85.8%; recommendations: closes from the next file's previous close for the five
  late sessions and 2022-08-08; monthly identity snapshots if a budget is approved (184,428 -> about
  11,600 unknown development stock-days), with a labelled backfill rule for all snapshots; leave
  weekend sessions out of the calendar. For the user's decision.
- 5 d6293fc T1 outcome step, desk/t1_outcome/ (docs/desk/t1_outcome_step.md): adverse20 equal to the
  existing label, through the firewall, with the forward-start and development-period guards;
  tables, standardised differences, coverage/sample/spell checks, decision rule, block bootstrap.
  Synthetic fixtures only (19 tests). Open choices are required arguments; listed for the user.
  STOPPED before the development-period run.
- P8-084 logged (open, Medium); P8-070 note appended. features.py docstring corrected (weekend sessions).
- Full suite: 995 tests in 220.360s, OK, exit 0 (08:53-08:57). Nothing stashed.

## 2026-10-14 (from 15:33): Part B, items 1-7 first (Claude)

User's live results today (recorded as observations, no cause claimed; prices left out):
- 14:5x IP check False: the user's public IP is not the one registered with Angel; every run
  below came from this unregistered address.
- 14:59 and 15:01 capacity summaries (logs/angel_capacity_20261014_145944.json, _150117.json):
  setup failures, ANGEL_API_KEY not set, stopped within a second with no tier; they said only
  "failed or interrupted (no detail is printed)". Not feed failures. Fixed as P8-081.
- 15:04-15:14 `--only-25`: Tier 25 PASS, 21,889 ticks, 25/25 symbols, 10/10 sentinels, receipt lag
  p50/p95/p99/max 1.02/1.47/1.53/2.09 s, max silence 0.8 s, drift 0.03 s, stopped by us at 600.0 s.
- 15:21 connection test: login and quote OK; candles for 2026-09-01 RATE_LIMITED (HTTP 403),
  market open. The first real Angel reply the RATE_LIMITED check has matched.

Done (one commit each, tests where there is code):
- 1 f5b6bcb: the unclassified-denial line drops Codex's app/static-IP hint and ends with
  "see docs/desk/angel_candle_403_20261014.md" (also the permission-denied line).
- 2 09e4e02 (P8-079): a feed we stop ourselves says so: fixed label + message length, never text.
- 3 09765e1 (P8-080): an unclassified 403 records its shape only (JSON/HTML/plain text/empty,
  bytes, error code only if exactly two capitals + four digits).
- 4 eb0b4ef: the capacity probe needs a working login and quote, not candles.
- 5 22b18df: setup guide's public-IP check with a placeholder; cites Moderator_3 in topic 5671.
- 6 9f2d9c5 (P8-081): the probe gives the connection test's fixed stop reasons.
- 7 a4bc84f: R1 design note: no historical candles during market hours; bars from the stream.
- 24abac4: 403 note gains the afternoon results (date ruled out; IP-tied limit not ruled out).
- B1 46e5543: docs/desk/angel_minute_completeness_20261014.md (15:29 flat bar = official close;
  candle extremes = stored high/low; proposed R1 treatment, design only).
- B2 STOPPED, nothing recorded: the requested addendum's V3 ("equal-weight average 20-session
  return of all EQ stocks in the store") differs from addendum 2 (3535590) and the T1 build
  (compounded equal-weight daily return of all other eligible equities, focal excluded); and T1
  data has already been fetched (phase 1, phase 2) and inputs built (1a3991d), so "before any T1
  data is fetched" cannot hold. Items 1, 3 and 4 fit the current text. For the user to settle.
- B3 635688f (P8-082): price-band list missed by the 18:00 nightly (13 Oct 404 at 18:07:58) is now
  fetched on later nights (at most 5 sessions back, own Last-Modified date as knowledge date);
  Data health shows a Price bands line (WARN when missing). NSE pages read: 2 (no timing stated).
  Tonight's run should fetch the 13 Oct list as well as 14 Oct's.
- Pages read today: smartapi.angelone.in 8; nseindia.com 2. No downloads; no NSE during a run.
- Full suite after B3: 974 tests in 222.837s, OK, exit 0 (15:53-15:57). Nothing stashed.

User decisions on that report (from 16:05):
- B2 closed with no change: the user's V3 wording was wrong and addendum 2's definition stands
  (compounded equal-weight daily return of all other eligible equities, focal stock excluded);
  items 1, 3 and 4 are already in the pre-registration, so a new addendum would only repeat them.
- P8-083 (3d7423e): checking the user's statement that a late-fetched band list is known from when
  we fetched it found it was not (knowledge date was NSE's Last-Modified date; direct band reads
  filter on knowledge date only). Fixed: knowledge date = later of Last-Modified date and fetch date;
  an identical re-fetch adds nothing. No waiting in the nightly; tonight is the catch-up's first test.
- Candle summary prints the bars' total volume (compare with the bhavcopy's traded quantity).
- B1's R1 treatment approved (no filled minutes; flat 15:29 bar = close marker; official close from
  the bhavcopy). Design only; nothing built.
- Full suite after these: 976 tests in 215.552s, OK, exit 0 (16:08-16:12). Nothing stashed.

## 2026-10-14 (from 13:55): finishing Codex's Angel work, Part A (Claude)

- A1: Codex's uncommitted 403 diagnostics (P8-076) reviewed against the user's criteria and
  committed unchanged as 0d353e1 (one request, no retry; fixed categories only; unexplained 403
  unclassified; login/quote/master, IP/MAC headers, TLS, endpoints and allowlist unchanged).
  Notes: exact rate-limit phrase match was case-sensitive and non-JSON only; a success reply with a
  non-empty error_type is now rejected.
- A2: 967729e reviewed. Scrip master: stricter rows (dict, -EQ symbol, ASCII-digit token, no shared
  tokens, symbols with an invalid token row dropped) and categorised errors. Candle date: the latest
  SBIN EQ session in the store before today (within 14 days), so 2026-10-13 at 11:22; this replaced
  the fixed 2026-09-01. Control frames: recv_data(control_frame=True); CLOSE stops the feed, PING/PONG
  and text "pong" are skipped, other text frames are an api_rejection. Duration: the deadline starts
  after the subscribe; the probe fails a tier whose feed ended early. Nothing weakened; added a test
  that the feed keeps CERT_REQUIRED + hostname checks and the master keeps verify=True.
- A3 (P8-077): the feed now sends a protocol PING and Angel's text "ping" every 10 s; server PINGs
  are answered by websocket-client; text "pong" never a tick; every exit records a close summary
  (who closed, code, reason length only, idle and heartbeat seconds, frame counts), printed by the
  connection test and stored by the probe. Angel docs read (2 pages; see the 403 note's URL list).
  The 239-second drop is still unexplained by the code.
- A4 (P8-078): connection test back on the fixed 2026-09-01 (P8-073 reversed by user decision);
  `--candle-date` accepts only a stored SBIN EQ session before the forward window; one summary
  line instead of every bar; Angel's two throttling phrases reported as RATE_LIMITED (reply never
  shown), any other 403 unclassified; the failure line says whether the market was open. Request
  unchanged, one request, no retry. The 403 note now lists the four differences between 08:10 and
  11:22, the forum reports (5595, 5677, 5691, 5692), the moderator's static-IP posts (5679, and
  Codex's 5671, verified), and what each explanation predicts for the next two runs. No cause
  claimed. smartapi.angelone.in pages read today: 8 (2 docs, 6 forum topics).
- Part A commits: 0d353e1, 9a5ad72, 59cd2ba, bf77cc8. Full suite after A4: 958 tests in 236.406s,
  OK, exit 0 (14:23-14:27). Nothing stashed. Angel tests: 81. No authenticated call made by Claude.
  Next (user): connection test (1 Sep, once in market hours, once after 15:30), then --only-25.

## 2026-10-14: Historical candle HTTP 403 follow-up (Codex)

- User confirms successful login/master/SBIN quote, then historical HTTP 403. Exact broker/gateway
  cause is unresolved; no authenticated requests were made by this agent.
- Compared POST endpoint, JSON serialization, all header fields, token selection and date window
  with installed SmartAPI 1.5.5 and official docs. No request mismatch explains the denial.
  Selected 2026-10-13 is an evidenced completed SBIN EQ session; one-day window is valid.
- P8-076 fixed: non-200 responses previously discarded explicit broker error types. Allowlisted
  permission/authentication/input/date/rate-limit indicators now survive as fixed categories;
  generic 403 is unclassified, HTTP status retained, no secrets/raw responses emitted, no retries.
  Smoke failure prints its canonical candle window. Login/quote/master request behavior unchanged.
- Current SmartAPI team guidance says static IP applies to data access too. Ask support to verify
  this app's historical entitlement, migration status, registered source IP and gateway restriction;
  do not invent a permission checkbox or spoof IP headers. Details: docs/desk/angel_candle_403_20261014.md.
- Initial tree clean, nightly Ready. Baseline: 936 tests in 227.928s, OK. Focused: 68 tests OK
  before two additional isolation/error-envelope regressions. Final full-suite result pending.
- Next user-private verification (after account checks): python -u -B scripts\angel_connection_test.py
  No capacity test until candles succeed. No SDK changes, external messages or portal changes.

## 2026-10-14: Angel integration diagnosis and safe fixes (Codex)

- User task: diagnose master, candle and 239-second capacity failures; no authenticated tests
  authorized or run. Public GET succeeded (HTTP 200, 35,325,024 bytes, 150,726 records), old parser
  found a unique SBIN-EQ match; exact earlier live failure causes remain unresolved.
- P8-072..075: robust fail-closed master records; safe transport/API categories; recent completed
  smoke-test session from read-only knowledge-filtered SBIN EQ bhavcopy (14-day freshness bound);
  explicit WebSocket control/close handling, parsing/callback/interruption categories; capacity
  minimum-duration check and --only-25. SDK 1.5.5, TLS, pacing and read-only allowlist unchanged.
- Existing user edit replacing the smoke date with 2026-10-13 was incorporated into automatic
  selection. No other initial dirty files. Baseline: 922 tests, two date-expectation failures.
- Focused verification: 57 Angel tests OK before two further capacity-run regressions were added.
  Offline --check reports setup ready, SDK 1.5.5, websocket-client 1.8.0, logzero 1.7.0.
  Final full-suite: python -B -m unittest discover -s tests -p "test_*.py"
  ran 936 tests in 187.616s, OK (exit 0). Existing SQLite ResourceWarnings remain.
- Detailed findings, test scope, limits and primary references:
  docs/desk/angel_diagnosis_20261014.md. No claim of restored live reliability from mock tests.
- Next user-private command: python -u -B scripts\angel_connection_test.py
  Only after success: python -u -B scripts\angel_stream_capacity_test.py --only-25
  Each authenticated test requires explicit user initiation and hidden terminal credential input.

## 2026-10-14 (07:50): Angel connection test says why it stops; library installed (Claude)

- P8-071 (Low, closed): the connection test exited 1 silently. Now one plain stop line every run,
  a setup check before login, and `--check` (no login, never reads ANGEL_API_KEY): run on the
  nightly's Python, "Setup ready for the connection test." 45 Angel tests OK.
- Library: `pip --dry-run` on Python313 showed only smartapi-python 1.5.5 and logzero 1.7.0, both
  new; nothing installed would change. Installed hash-checked with --no-deps (wheel hash matches the
  reviewed one). pip check: only pre-existing tensorflow/keras/tensorboard/astunparse gaps,
  unrelated. requirements-angel.txt pins the exact versions.
- The user runs the connection test next (lines in docs/desk/angel_connection_setup.md section 2),
  then the capacity probe; R1 waits for both. Tonight's after-run checks (ticks recorded, announcement
  check passed, the brief) are still pending.

## 2026-10-14 (from 01:13): P8-069 fixed; 13 Oct note; T1 phase 2 (Claude)

- P8-069 (user approval): the bulk refresh's whole/split comparison covers completed days only;
  the IST day in progress is stored, never compared or certified (receipts certify D-1, P8-049).
  The saved 13 Oct responses pass under the new rule. Tests: test_announcements_open_day.py (4).
  Tonight's 18:00 run is the first under it; after it, confirm the announcement check passed.
- 13 Oct note (append-only): scripts/desk_annotate_p8069.py annotates the 52 opportunity rows and
  Strategy 0's 13 Oct run; shown in desk status and every brief. Dry run on a temporary copy
  (production unchanged), then run on production after this commit (see the next entry).
- 13 Oct note applied in production after b3115c6: 52 opportunity rows + 1 S0 run; desk status shows
  "Strategy 0 burn-in dates decided on incomplete disclosure data: 1: 2026-10-13 (P8-069; 52 screen
  results annotated)".
- T1 phase 2 (user approval, <= 60 requests): 41 used (7ef59e8). NIFTY 50/NIFTY 500/India VIX from
  niftyindices' historical-data endpoint, one request per series-year (the VIX form's endpoint is
  gone: 8 requests got a 404 redirect, my error for not testing one first); VIX's 8 missing
  sessions from dated Daily Snapshot files. Cross-check vs the 16 phase 1 files: index closes
  identical; VIX O/H/L differ only by rounding. Every URL in data/raw/t1_sources/phase2/requests.jsonl.
- T1 build (1a3991d; artifact data/t1/build_20261013T202004Z.sqlite, report
  docs/desk/t1_coverage_20261014.md): no outcome loaded or computed. A first build from uncommitted
  code (same-day basket knowledge, too strict) is kept in data/t1/_superseded/ with a note.
  For the user's review: 5 sessions known months later (strict rule leaves 50-session V2 gaps),
  2022-08-08 missing from the store (P8-070, with four weekend sessions), identity UNKNOWN before
  2019-11-15 and between sparse snapshots (67k stock-days in 2024). Spells: V1 9 dev / 1 hold-out;
  V2 13 dev / 2 hold-out. STOP: no outcome until the user has reviewed the report.

## 2026-10-14 (from 00:37): announcements failure, T1 probe and addendum 2, P8-064 implementation (Claude)

- Item 1 (P8-069, Medium, open): 13 Oct's announcements were incomplete because the bulk refresh's
  whole/split check failed on one 13 Oct filing published at 18:06:54, four seconds before the
  whole-window request and missing from the single-day request two seconds later. All 8 requests
  were HTTP 200 in 0.18-1.79 s: no timeout, no HTTP failure (the documentation-read timeouts were
  the fetch tool, unrelated). The 12 Oct half matched, but the whole window failed, the receipt was
  PARTIAL, 13 Oct's G2 had disclosures UNKNOWN for all 52 candidates. The data catch up on the next
  run (last_complete stays 12 Oct); the 13 Oct decisions do not. Fix proposed, not implemented.
- Item 2 (0f6f2ba): T1 phase 1 probe, 25 of the 64 approved requests, 00:41-00:46 IST, task Ready.
  NSE Indices Daily Snapshot exists on all 16 sampled dates (2 per year, Sep 2018-Aug 2025), own
  date matches, NIFTY 50/NIFTY 500/INDIA VIX rows present. Last-Modified on the trading evening
  23:10-23:50 IST for 14/16, 01:10 next day for 1, rewritten later for 1. NSE copies: identical
  closes, re-uploaded before Aug 2020. Every URL and header in t1_sourcing_probe_20261014.md; raw
  files and ledger in data/raw/t1_sources/. scripts/t1_source_probe.py enforces budget/spacing/
  nightly hours. Phase 2 (full history, ~1,830 files) not approved.
- Item 3: T1 addendum 2 (user-approved pre-registration change): V3 relative to the equal-weight
  market of eligible stocks from Praman's own store (breadth universe, focal stock excluded);
  sector-relative strength dropped; family stays three. Index/VIX close for D known from D+1,
  labelled ASSUMPTION, with the probe's header evidence; V1 at D uses closes through D-1.
- Item 4 (P8-064 closed, both books, no new S0 version, DESIGN.md changelog): desk/paper/locks.py.
  No sell on a session locked all day at the lower limit (stop, pending exit, manual close tried
  again next session under the same rule, reason recorded and in the brief); no buy at an upper
  lock (normal no-fill, counted as an attempt); flat bar with band/tick/reference unknown = assumed
  locked both ways; buy limit capped at the next session's upper limit when that band was recorded
  before the decision; limit above a band unknown at decision = rejected, normal no-fill. Tick sizes:
  new nightly step tick_sizes (after circuit_bands) records Angel's public scrip master ticks
  (paise; master generated ~08:00 IST, dated to that session) into the new tick_sizes table; plain
  HTTPS, no SDK. Records change only when a rule binds. Replay of all 7 S0 runs (with each run's
  visible band reports): identical. 16 tests in tests/test_paper_locks.py; 13 behavioural ones fail
  with the checks off. Tonight's run is the first to record ticks.
- Item 5: R1 untouched until the user has run the connection test and the capacity probe.

## 2026-10-13/14 (night): after-run checks; T1 addendum and sourcing; R1 probe; P8-064 buy side (Claude)

- 13 Oct nightly 18:00:02-18:39:05, overall=WARN. New WARNs, neither from today's changes (the two
  steps, their modules and STEPS unchanged since fc39780): announcements_recent bulk window
  12-13 Oct AnnouncementFetchError (receipt PARTIAL, complete only through 12 Oct), so all 52
  candidates failed G2 (disclosures UNKNOWN) and Strategy 0 had nothing to decide (designed
  fail-closed behaviour); circuit_bands 13 Oct price-band report 404 at 18:07:58 (13 Oct bands stay
  UNKNOWN). The brief does not say why 0 passed (reported, not changed).
- Checks passed: "What changed: nothing since the previous monitor run"; previous finished run
  12 Oct 21:09:46 overall=OK "(0d ago)"; the nightly made logs_20261013T130547594726Z.zip and
  verified it (105 files, every hash matched by an independent check); strategy_gaps exists, 0 rows;
  ten ISIN snapshots cached 18:06:39-42, hashes verify; no skip.
- T1 (user-approved pre-registration change): addendum 1 committed 86b2543 before any fetch or
  feature: >= 5 separate adverse spells per period for V1/V2 (runs < 20 sessions apart merge;
  UNKNOWN sessions never split), 60-session blocks for V1/V2, V1/V2 probably INCONCLUSIVE on 2025
  alone, sourcing before outcomes. Sourcing part 1 (97a0e05): documentation pages only,
  niftyindices 11/20, nseindia 4/20, every URL listed; no data downloaded. Key facts: Daily Snapshot
  files ind_close_all_DDMMYYYY.csv (archive via POST endpoint, depth unstated); publication evidence
  unproven (Last-Modified untested); common industry classification only from 31 Mar 2022, no dated
  per-company history found; V3 options for the user. Phase 1 probe budget (<= 64 requests) awaits
  approval: fetch nothing until then, and nothing from NSE while the nightly runs.
- R1 (7348b20): design approved with the two changes (same-day flags allowed for every symbol;
  no event-anchored change or join to catalogue events >= 2026-09-16, including research reads of
  live.sqlite, before 2027-06-01; one-minute bars, not ticks; live.sqlite to nightly backups once it
  exists), dated changelog. Built only scripts/angel_stream_capacity_test.py + 14 offline tests:
  refuses dirty tree / non-master / running nightly; tiers 25-1000 by turnover known before today,
  10 minutes each, end by 15:30, stop at first failure; first tick per symbol kept out of lag
  stats; summary in logs/ without prices; raw ticks only in data/live/probe/. Not run (needs the
  user's login during market hours, after the connection test passes). Stop here for the user's
  review; no watcher, no NSE RSS (needs a budget).
- P8-064 buy side (document only): the registered limit entry fills a paper buy at the open on an
  all-day upper lock when the limit is at or above the locked price (synthetic: fills at 102 and
  101 with limit 102). Proposed POSSIBLY_LOCKED_UPPER detection, LOCKED_UPPER no-fill (counted as
  an attempt), LOCK_STATUS_UNKNOWN for unverifiable flat bars. Engine unchanged.
- Memory: the user's network rules (doc pages <= 20 per site, URLs listed; downloads need a budget;
  no NSE during the nightly).

## 2026-10-13 (16:46): Claude takes over from Codex: pending commits, before the nightly

- Root verified (D:/Agentic_ai_project/praman), master; task Ready, next run 18:00, no run in
  progress, so items 1-4 were done before 17:45. Codex's report not relied on; each item verified.
- Uncommitted at start: CLAUDE.md (Angel rule moved), the P8-064 fill audit plus a pointer to it in
  locked_circuit_review_20261013.md, the connection setup guide plus a link in
  angel_market_data.md. No code or config was dirty.
- CLAUDE.md (f310045, on its own): the Angel rule appears once, at the start of the
  non-negotiables, byte-identical to the previously committed copy and to AGENTS.md's; the only
  other change is removing the old end-of-file section that held it.
- P8-064 audit (09705aa): recounted read-only with SQL returning counts only: 4 Strategy 0 fills,
  each with its EQ bar, 0 exactly flat; 0 manual fills. Desk stores band % for 1-12 Oct but no
  tick sizes or absolute lower limits, so all four stay unclassified under the full test. No
  prices, symbols or results. P8-064 stays open.
- Setup guide (this commit): hidden prompt sets ANGEL_API_KEY for the current process only (no
  setx), removed afterwards; Python313 python.exe 3.13.6 verified (the task runs the adjacent
  pythonw.exe); smartapi-python pinned 1.5.5; now states plainly that it is not verified whether
  Angel accepts 127.0.0.1 in the IP headers. The guide's True/False visibility check is for the
  user's own terminal; no agent has read the key.
- Full suite before this commit: 858 tests in 433.756s, OK, exit 0. Pushed (user approval).
- After tonight's run (not yet run): confirm "nothing since the previous monitor run"; previous
  finished run 12 Oct, OK/WARN, not called stale; own verified logs archive; gap table exists and
  empty; ten ISIN snapshots cached; no skip or new WARN from today's changes; then the full brief.
  R1 stays design-only.

## 2026-10-13 Codex: follow-up 1, SDK side effects

- Original nine commits pushed to origin/master (through 31cdbe0), as approved.
- P8-068 fixed: intercept SDK DNS/hardware probes, suppress import bytecode and
  stream debug logs, explicit loopback IP/zero MAC headers. No SDK constructors.
  Terminal script suppresses bytecode before imports; arbitrary imports need -B.
- 28 offline Angel tests in 1.343s, OK. Fresh-process no-I/O import guard;
  complete mocked session with seven distinct synthetic secrets; network routes
  and file/folder writes guarded. Pinned wheel actual import/construction also
  checked offline with logging/feed dependencies stubbed. No real key used.
- Public-IP discovery is not performed. A provider requiring real IP headers may
  reject login; actual account compatibility remains DOCUMENTED, NOT VERIFIED.
- Full suite: 858 tests in 459.070s, OK, Python exit 0. Follow-ups 2/3/4
  remain for separate commits; R1 still under review, no code.

## 2026-10-13 Codex: C design / pre-nightly handoff

- Parts A and B complete, each item committed; B3/B4 commit 5dbfae6.
- C proposal: docs/desk/R1_market_hours_watcher_design.md. Design only, awaiting
  user OK. Covers 90-second conditional RSS, morning reconciliation, real-time
  detection snapshots, isolated append-only bitemporal tables, foreground
  capacity measurement, firewall tests, wake/gap handling and both log formats.
- Explicit constraints: current B stream is blocking/LTP-only; R1 needs a
  cooperative foreground transport adaptation. Initially volume snapshots rotate
  every 15 minutes over 100 symbols. Protected or uncertain event coverage
  suppresses derived move flags. No watcher code, tables or job created.
- D NOT VERIFIED: tonight's 13 October run starts 18:00 IST and had not started
  at this handoff. After it finishes, inspect its complete brief and verify:
  "nothing since the previous monitor run"; previous finished run 12 October
  with OK/WARN; its own verified logs archive; gap table empty; ten ISIN snapshots
  cached. Do not substitute the 12 October brief. If still running, stop.
- Network permission covers Angel public docs/package/master reads only. No
  package installed or authenticated call made. Push awaits explicit permission.
  No wakeup, background loop or other agent was started. No production store
  modified. P8-064 locked-circuit paper-fill defect remains OPEN, engine unchanged.
- Final full suite: 855 tests in 307.625s, OK, Python exit 0. Existing SQLite
  ResourceWarnings remain. Nightly task Ready at 16:08 IST; no active run.
  Commit this design/handoff on master, then verify the tree is clean before
  requesting push permission. The 17:45 deadline has not been approached.

## 2026-10-13 Codex: B3 / B4

- B2 committed eea5ce6. B3 adds scripts/angel_connection_test.py for the user's
  private terminal: login, SBIN quote, 2026-09-01 minute candles, 30 seconds of
  live SBIN during regular hours with a fresh quote, then logout in finally.
  Prints prices/timestamps only; failures return exit 1 without raw errors.
- Calendar/open-status proxy and optional installation instructions documented
  in docs/desk/angel_market_data.md. The agent has not run an authenticated call.
- B4: no Angel import in nightly, no scheduled job, no stores written. SDK/feed
  tests are mocked and offline. Part A's authorized nightly wait fix is separate.
- Full suite before this commit: 855 tests in 323.532s, OK, Python exit 0.
- R1 design is uncommitted, awaiting its final review/commit and user approval.
  D cannot be verified yet: 13 October's 18:00 nightly has not started.
  Push still needs explicit user permission; no push attempted.

## 2026-10-13 Codex: B2

- B1 committed ca99d6e. B2 adds only the optional read-only Angel wrapper,
  pinned smartapi-python 1.5.5 requirements, mocked tests and documentation.
- Seven public capabilities; allowlisted REST dispatcher, hidden prompts,
  midnight expiry, no token refresh/persistence, muted vendor/HTTP debug logs,
  exact NSE EQ mapping, conservative 4.1-second global REST spacing and bounded
  foreground feed. No nightly integration, store write or package installation.
- Latest EQ master comparison: 2694/2696 mapped; CCAVENUE and MOREPENLAB unmapped.
  Live authentication/IP compatibility/feed reliability DOCUMENTED, NOT VERIFIED.
- Draft defects P8-065/066/067 fixed before commit; P8-064 remains open by design.
- Targeted Angel tests: 25 in 0.847s, OK. Full suite: 855 tests in 213.836s,
  OK, Python exit 0. This run includes the separately committed B3 script tests.
- At 15:53 IST the nightly task was Ready. Clean master deadline remains 17:45.
  C design is being prepared; no R1 implementation. D awaits tonight's run.

## 2026-10-13 Codex: B1

- Part A complete. A5 engine unchanged; 830 tests in 150.115s, OK.
- B1 user-approved policy inserted verbatim into CLAUDE.md and AGENTS.md and replaces
  the blanket prohibition in blueprint Praman amendment 5. Existing order bans retained.
- Exact old/new report: docs/desk/angel_policy_changes_20261013.md.
- Public Angel reads only: official SDK 1.5.5 wheel/hash reviewed, official forum rate limits
  found; current scrip master maps 2694/2696 latest Praman EQ symbols, misses CCAVENUE/MOREPENLAB.
  No package installation, login, NSE request or push performed. Wrapper work in progress.
- Full suite: 830 tests in 708.088s, OK, Python exit 0 before B1 commit.

## 2026-10-13 Codex: A5

- A4 committed after 830 tests in 371.519s, OK.
- A5 / P8-064 OPEN (Medium): shared paper stop rule invents a fill for a specified all-day
  lower-circuit lock with no buyers. Synthetic reproduction returned ('stop_gap', 95).
- Proposal: docs/desk/locked_circuit_review_20261013.md. Exact preceding-session band,
  authoritative reference price/tick, conservative ambiguous-bar handling, deferred append-only
  exits retaining position risk. Engine unchanged; no sealed outcomes read or live stores written.
- Full suite: 830 tests in 150.115s, OK, Python exit 0. Part A is complete.

## 2026-10-13 Codex: A4

- A3 committed after 830 tests in 400.832s, OK.
- A4 audit: docs/desk/isin_today_audit_20261013.md. Two confirmed today's-404s among 11
  logged ISIN attempts: 28 September within 13:53:03-14:22:14 IST; 3 October (Saturday)
  within 06:22:38.949684-06:22:40.459427 IST. Exact request times not retained.
- No evidence of routine evening today's-404: seven known successes, one DNS failure and one
  indeterminate interrupted weekday-evening attempt. Historical WARNs are distinct (P8-060).
  No retry or suppression change proposed on this evidence. No NSE request made.
- A4 is documentation only; full suite: 830 tests in 371.519s, OK, Python exit 0.

## 2026-10-13 Codex: A3

- A2 committed 4fd562a (826 tests in 377.973s, OK).
- A3 / P8-063: brief/status freshness uses last finished run's IST finish date against the
  previous weekday, independently of Strategy 0's unchanged registered 7-day constant.
  No holiday calendar: conservative weekday proxy documented; absent bars never imply holidays.
- Targeted: 35 tests in 1.049s, OK. Full suite: 830 tests in 400.832s, OK, Python exit 0.

## 2026-10-13 Codex: A2

- A1 committed 17702f8 (824 tests passed).
- A2 / P8-062: same-day bhavcopy waits only if the original run started on today's weekday
  at/after 15:30 IST; morning, weekend and midnight-crossing runs skip immediately with a reason.
- Both this and the 09:00 cutoff use weekdays; no forward holiday calendar found. Limitation
  recorded in OPERATIONS.md and session_20261013_followups.md. Cutoff rule unchanged.
- Targeted: 19 tests in 2.861s, OK. Full suite: 826 tests in 377.973s, OK, Python exit 0.

## 2026-10-13 Codex: A1 (user's Parts A-D session)

- Root verified; master initially clean. User confirmed Claude idle and closed.
- Nightly task Ready, next 18:00 IST; no Python ingestion running. Hard stop for a clean master at 17:45.
- Baseline: 822 tests in 267.549s, OK, Python exit 0; existing SQLite ResourceWarnings.
- A1 / P8-061: manual time exits now require a recorded order on the horizon/recovery run,
  then fill at the following open. Delay shown in the brief; stop catch-up retained.
  Read-only production manual paper_trade_events count: 0; no production records changed.
- Targeted tests: 21 in 12.733s, OK. Full suite: 824 tests in 177.209s, OK, Python exit 0.
- A2-A5, B, C design and D after-nightly verification remain. No network used yet.
- User approved only Angel public docs/package/scrip-master reads; ask before any other network, including push.

## 2026-10-13 (from 09:12): approved round: P8-057, P8-056 gaps, P8-060 cache, branch guard (Claude)

- The user's "tonight's run has finished" came at 09:12 on 13 Oct: the latest run was 12 Oct's; the
  13 Oct run is at 18:00. Item 3 checks (What changed, previous run 12 Oct, own logs archive, brief)
  wait for it.
- P8-057 fixed (user approval): Strategy 0 checks every session not yet monitored, in date order,
  with the same stop rule (now shared as `desk.paper.execution.stop_rule`); a time exit after a
  skipped night is ordered at the next run with the delay recorded and shown in the brief. Replay of
  all six runs on temporary copies: identical (run 1's operational record lacks only v3's
  candidate_order key). Manual monitor unchanged; its time exit after a missed run is retroactive
  (reported, awaiting the user).
- P8-056 fixed (user decision): a trading date with no Strategy 0 run is an append-only burn-in
  gap (`strategy_gaps`) with its reason (battery skip, uncommitted code, not on master, git
  unavailable, run failed, no run at all), recorded by the next run, which decides its own date
  normally; a run deciding after 09:00 IST on the next weekday makes no decisions (gap
  DECIDED_TOO_LATE) but processes entries, stops and exits. No catch-up exception to the stale-data
  switch. The brief lists the gaps; `desk status` counts them. Replay of all six runs with this
  code on temporary copies: identical, no gaps. Never happened before: all runs decided the same
  evening. Reported, not changed: after midnight, `bhavcopy_today` waits ~75 min for a file that
  cannot exist, so a run starting after ~07:00 could miss the cut-off.
- P8-059 hole closed (user request): the nightly also skips, with a WARN in the log and brief,
  when HEAD is on another branch or detached, or git cannot read HEAD. Work on a branch now skips
  the nightly just as an unfinished tree does: switch back to master before stopping.
- DEFECT_REGISTER.md stays a nightly input of the P8-059 guard (agreed with the user, no change).
- P8-060 fixed (user approval): fixed historical ISIN snapshots cached in `data/raw/isin_snapshots/`
  with SHA-256 sidecars, hash checked on every use, re-downloaded if missing or damaged; failures name
  the HTTP status; today's snapshot unchanged (404 stays a WARN). Map from the cache = map from fresh
  downloads (all ten dates, temporary cache). The real cache does not exist yet: tonight's run fills
  it (expect ten "downloaded and cached" lines in its isin_map output); from 14 Oct expect "cached
  snapshot, hash verified".
- Item 6, citation sweep (src/, desk/, scripts/, shared/; 185 files): every cited document exists;
  all 48 defect IDs cited are in the register and match their topic; blueprint sections 3, 6.3, 7,
  8, 13, amendment 4, DESIGN constitution items 3 and 5, CLAUDE.md invariants 1, 8, 12 and D1/D6,
  session items B1-B5, Amendment 2 §5, Amendment 4 §1 and the phase-doc item numbers checked
  against their targets. "Section 7/8/11" means CLAUDE.md invariants 7/8/11 (CLAUDE.md itself
  writes "(Section 11)"): correct. Fixed (comments only): `desk/lib/rulebook.py` cited
  "docs/desk/DESIGN.md's own working procedure", which never existed (it is CLAUDE.md's);
  `src/classification/event_classifier.py` attributed to invariant 12 a rule it does not state;
  `desk/ingestion_health.py`'s STALE_AFTER_DAYS comment said ingestion is weekly; stale skip and
  monitoring descriptions after today's changes (weekly_ingest, brief, ingestion_health,
  strategy0 docstrings), and the skip notice in the brief now states the 09:00 cut-off.
  Reported, not changed: (1) STALE_AFTER_DAYS = 7 was set for weekly ingestion; with nightly runs
  the health line in the brief and `desk status` calls a last run up to 7 days old not STALE. For
  Strategy 0 it matters little: a date is decided once and only before the 09:00 cut-off (P8-056),
  so an old session cannot be decided late. It is cited by S0's registered definition, so changing
  it is the user's call. (2) "item N" in Desk Phase 1 files (paper/execution.py item 9,
  risk/officer.py item 7, evidence/bundle.py item 5, ingestion_health.py item 5) and "round 2,
  item 4" in phase10_amendment4_phase8b_reauc.py cite session instruction lists that are not in the
  repository (the last is §5 of docs/phase10_amendment4_prep2.md); unverifiable, left as they are.
  (3) `src/bitemporal/schema.py` raises "... -- Section 7 violation." (a message, consistent with
  the convention above).

## 2026-10-13: working-tree guard (P8-059) and manual open-risk measure (Claude)

- Start 08:39: task Ready, no run in progress, no Python running; tree clean at fc39780
  (`git --no-optional-locks status --porcelain --untracked-files=all` empty), so the guard could be
  turned on. git: `C:\Program Files\Git\cmd\git.exe`, on the machine PATH the task inherits.
- Item 1 (user approval): the nightly skips with a WARN (log and brief) when a file it runs or
  reads has an uncommitted change or git cannot run; docs and theses do not trip it, except the
  three docs it reads at run time (DEFECT_REGISTER.md and the two shadow_replay_followup*_results.json).
  CLAUDE.md session rule added (user-approved wording). Catch-up check: the data steps catch up;
  a skipped date's bands, scan, Strategy 0 decisions and brief do not (P8-056, open, awaiting the
  user), and Strategy 0 checks stops on the run date only (P8-057, open, awaiting the user).
- Before stopping any session: leave the tree clean (commit, or `git stash push -u`); otherwise the
  next nightly skips.
- Item 2: G6 and sizing counted open manual trades at entry-to-stop risk although the rulebook caps
  stress loss (P8-058, Medium; no documented decision for entry-to-stop; no manual trade or
  decision ever existed, so nothing affected). Fixed: each counts at the stress loss recorded on its
  opening decision; an unrecorded one makes G5/G6 UNKNOWN. No rulebook change.
- ISIN WARN 6-9 Oct (user question): transient NSE HTTP errors on one or two of the ten fixed
  historical snapshots re-downloaded every night, a different date each night; nothing changed, and
  12 Oct was a night when all succeeded. P8-060 (Low, open): proposed cache for the fixed snapshots,
  awaiting approval.
- Waiting on the user: P8-056 (catch up a skipped date's scan/S0/brief?), P8-057 (S0 stop checks on
  skipped sessions), P8-060 (ISIN snapshot cache).
- After the 2026-10-13 nightly (user request): confirm "What changed: nothing since the previous
  monitor run", that the previous finished run shown is 12 Oct's (OK), and that the nightly made and
  verified its own logs archive; show the brief in full.

## 2026-10-12 (morning): nightly runs 6-9 October and the burn-in record (Claude, read-only check)

| Weekday | Run | Started | Finished | Result |
|---|---|---|---|---|
| Tue 6 Oct | missed at 18:00 (asleep, on battery, task AC-only: P8-053); run on demand | 21:02 | 21:43 | WARN |
| Wed 7 Oct | late: laptop in standby at 18:00, missed-start recovery on waking 19:05 | 19:06 | 21:26 | WARN |
| Thu 8 Oct | late: standby at 18:00, recovery on waking 18:53 | 18:54 | 19:27 | WARN |
| Fri 9 Oct | late: standby until 19:43 | 19:44 | 20:26 | WARN |

- No run was skipped and none failed. Every WARN is the isin_map step's historical-snapshot HTTP
  errors (map rebuilt each time). On 7 Oct the laptop re-entered standby at 19:09 and the first
  step only completed at 20:55, consistent with the run pausing during standby.
- Burn-in record: every stored session has a desk scan and a Strategy 0 run (5 Oct 45 events, run 1
  v2; 6 Oct 66, run 2 v3; 7 Oct 43, run 3; 8 Oct 56, run 4; 9 Oct 40, run 5). **No gaps since
  6 October.** No kill switch triggered.
- Strategy 0 positions (status only): 5PAISA OPEN (v2); AUBANK CLOSED (v2); its exit trigger, date
  and price were neither read nor shown (sealed until 2027-06-01). JINDALSTEL: v3's first
  acceptance (decided 8 Oct, 48 shares, limit 1027.52), FILL_OPEN on 9 Oct at 1014.70, OPEN.
- `logs/brief_2026-10-11.txt` is not a run: six skip notices written at 23:53-23:54 on Sunday 11 Oct
  by the battery-dependent tests (P8-055). Moved (user direction) to
  `logs/_quarantine/brief_2026-10-11.txt` with a one-line NOTE.txt; not deleted.
- Tests can no longer write into the real logs/ folder: `shared/log_paths.py` resolves it for every
  writer, tests/__init__.py points it at a temporary folder, and tests/test_zzz_real_logs_untouched.py
  fails the suite if the real folder changed (the suite's own redirected output file excepted).
  Do not run the suite while a nightly is running: that check would (correctly) flag the nightly's
  writes.
- Tonight's run (2026-10-12): the laptop was in standby 17:41-21:08; missed-start recovery started
  the task at 21:08:42 (on battery at 38%, above the 30% guard). 21:09:46-22:03:08, task result 0,
  overall OK, all 13 steps OK (isin_map without WARN), `manual_monitor` OK at 21:52:50. Brief
  "Manual book monitoring": Mechanical exits 0, Pending opens/closes 0, Open positions 0, and
  "What changed: no prior run to diff against" (this was the first monitor run ever; from the next
  run, with no positions, it reads "nothing since the previous monitor run"). Strategy 0: 46 passed
  evidence, 0 accepted (budget: Rs 24,798.64 of 25,000 held by 5PAISA and JINDALSTEL), seed
  a8944467c5f0ead0.
- Logs backup added (user request): `desk/backups.py` kind `logs`, daily, `desk_keep` retention;
  snapshot copy first, manifest from the copies, restore check against the archive's own manifest
  only; in the nightly backup step, `desk backup verify` and `desk status`. Tests in
  tests/test_backups.py. First logs archive made at 22:26 with `python scripts/backup_stores.py`
  (desk and Praman already backed up tonight, re-verified only): logs_20261012T165644157156Z.zip,
  99 files, 2,421,495 bytes, 218,575 compressed. `desk backup verify` then exited 0: desk, Praman
  and logs all integrity ok.

## 2026-10-11: manual-book monitoring catch-up and nightly mechanical exits (Claude)

- Start: root verified, clean at 5882b92; no repo file changed since 2026-10-09 and no Codex session
  record in the last 3 days (a Codex VS Code app-server process started 23:40 but no session was
  active). GitHub unreachable at start (connection timeout to github.com:443).
- ABC (the user's thesis example) was invented: no thesis file created, no dry run. Standing
  preferences for future theses (saved to Claude's memory): sector = NSE's own industry
  classification; time exit = "exit at the next session open after the horizon".
- Confirmed: `desk monitor` did NOT catch up missed sessions (stop checked on the run date only):
  P8-054 (Medium). Fixed: every session since entry, in date order, stop in force per date; plus the
  mechanical time exit (open of the first session after the horizon and the entry session). New
  nightly step `manual_monitor` (after auto_paper, before brief); the brief shows the manual report.
  Targets and evidence/risk/portfolio exits stay manual. No manual trade exists yet.
- P8-055 (Low, my own from P8-053): three test harnesses read the machine's real battery; on
  battery at 21% five tests failed. Isolated; affected modules pass on battery.
- Docs: HOW_TO_PAPER_TRADE.md exits section, theses/_template.yaml exit comment, OPERATIONS.md.
- Next run 2026-10-12 18:00: expect a manual_monitor step line in the log and "Manual book
  monitoring ... Open positions: 0" in the brief (nothing to check yet).

## 2026-10-07: first Strategy 0 v3 run verified; battery policy (P8-053) (Claude)

- The 2026-10-06 18:00 run was missed (asleep and on battery; the task was AC-only): P8-053. Started
  on demand at the user's request; held Queued until AC power, ran 21:02:22-21:43:15, task result 0,
  overall=WARN (isin_map: historical snapshots 2020-06-15 and 2021-06-15 HTTP errors, as on an
  earlier run; map rebuilt, age 0). All other 11 steps OK, GAPs 0.
- Registry: S0 v2 revision 2 SUPERSEDED_AFTER_ONE_RUN and v3 revision 1 PAPER_BURN_IN (both
  2026-10-06 21:40 IST). strategy_runs run 2: v3, 2026-10-06, code c76f544; seed
  211cd6834da9a787... from "S0-v3-candidate-order|2026-10-06", 58 candidates ranked.
- Entries (version 2 events, written by v3's run 2): 5PAISA FILL_OPEN on 2026-10-06, 135 shares,
  open 358.10 under the 367.90 limit; AUBANK FILL_OPEN, 47 shares, open 1034.70 under the 1042.08
  limit; basis factor 1.0, no cap breach at fill. Both OPEN. All 58 new candidates rejected on
  OPEN_RISK_BUDGET (Rs 24,764.32 of 25,000 held). No kill switch.
- Freshness row 3: COMPLETE through 2026-10-06, recorded 21:11 IST, certifies 2026-10-05 (P8-049);
  2026-10-06 decisions read disclosures as FACT. Refresh: 8 requests as predicted (cookie, the
  2026-10-05 identity file, two windows with split checks), 759 inserted.
- logs/brief_2026-10-06.txt shows version 3, the seed, the in-progress health line (10 steps
  logged, isin_map=WARN) and the Open risk by book block; `desk status` shows v3's line.
- P8-053 fixed after the checks (user approval): task may start on battery (only XML change);
  weekly_ingest skips below 30% on battery with a WARN in the log and the brief. Tests added.
- Then (user approval) "stop if the computer switches to battery power" turned off as well
  (StopIfGoingOnBatteries false, only XML change): a run started on AC continues if unplugged.
- Next run 2026-10-07 18:00: first monitoring of 5PAISA and AUBANK (MONITORED events, version 2);
  if on battery below 30% at start, expect the skip WARN instead of a run.

## 2026-10-06 (from 01:11 IST): approved fixes P8-049/050/051, Strategy 0 v3, P8-046 follow-ups (Claude)

- Root verified; clean start at 9a24f1c (= origin/master); no Python running; PramanDailyIngest
  next run 2026-10-06 18:00. One agent, foreground only. User approvals (message of 2026-10-06):
  P8-049 fix as proposed (Medium); fix P8-050 and P8-051; Strategy 0 v3 with a seeded random
  candidate order, applied from the next run, v2 superseded after one run; OPERATIONS.md known
  limitation for P8-046; verify the pinned pipeline (afe3e2b) reads the restructured store.
- P8-049 fixed: receipts certify at most the IST day before the day they were recorded (applied
  on read). Production rows 1-2 now certify 2026-10-04: 2026-10-05 decisions unchanged; a
  2026-10-06 decision is UNKNOWN until tonight's receipt (expected to certify 2026-10-05).
- Strategy 0 v3 (P8-052): v2's order was alphabetical (registered "ordered by symbol then
  opportunity_id"); 5PAISA and AUBANK were #1 and #3 (ATLANTAELE #2 did not fit). v3 = v2 with a
  seeded random order (seed sha256("S0-v3-candidate-order|<date>"), rank sha256("<seed>|<symbol>")),
  recorded in each run's operational record and shown in the brief. One book across versions, one
  run per date across versions, S0-wide fill-failure streak (else v2's two pending positions would
  have been orphaned). v1/v2 hashes match production. Rehearsed on a temporary desk copy.
  Tonight's run will: append v2 revision 2 SUPERSEDED_AFTER_ONE_RUN, register v3, settle 5PAISA
  and AUBANK (version 2 events, v3 run), then decide 2026-10-06's candidates in seeded order (seed
  for 2026-10-06: 211cd6834da9a787...). If both entries fill they hold Rs 24,764.32 of Rs 25,000,
  so most new candidates will be rejected on the budget.
- P8-050 fixed: the nightly passes its own start to the brief, whose health line now reads "this
  run (started ...) is in progress: N steps logged so far, all OK. Previous finished run ...";
  `desk status` (outside the run) is unchanged. P8-051 fixed: one shared "Open risk by book" block
  (brief and `desk status`): Strategy 0 as of its latest run with its held positions (symbol,
  state, version, decision date; no prices or P&L) plus the manual book. Verified on production
  `desk status`.
- P8-046 implications: OPERATIONS.md now records the known limitation for the June 2027
  evaluation (about 2,400 events, ~3% of the catalogue, probably misrecorded tiers; audit
  estimates and sampling limits), explicitly not an amendment. Pinned pipeline check
  (docs/desk/pinned_reader_verification.md): afe3e2b in a temporary worktree (since removed),
  read-only store copy, 1,156 recent events: 1,143 identical to HEAD in tier and rows, 13
  window-boundary differences (CRESTO, HEGAM; HEAD more conservative), pinned init_db a no-op, 0
  unexplained. PASS, not evaluation-blocking. My first draft assumed forward UNKNOWN_COVERAGE
  would be rarer; measured, equity UNKNOWN_COVERAGE is 5.3% vs training 5.1% (symbols with no NSE
  announcements at all, e.g. ABBOTINDIA confirmed absent from the raw bulk capture), so that claim
  was dropped. Re-run once more with module paths recorded relative to the worktree (identical
  results, event-list sha256 b9318ad4...); worktree removed (`git worktree list` shows only master).
- Commits this session: a950028 (P8-049), e36ac7c (S0 v3, P8-052), 63f8254 (P8-050, P8-051),
  67962c1 (P8-046 limitation and pinned-reader check), plus this handoff commit. Open defects:
  P8-043 (Medium), P8-046 (Medium, historical effect); no open High.
- Tonight's run (2026-10-06 18:00), verify afterwards:
  1. trading_strategies: S0 v2 revision 2 SUPERSEDED_AFTER_ONE_RUN; S0 v3 revision 1
     PAPER_BURN_IN.
  2. strategy_runs run 2 is v3 for 2026-10-06, and operational.candidate_order records seed
     211cd6834da9a787... and the full order. If the 2026-10-06 bhavcopy is not stored by
     desk_scan, the run date stays 2026-10-05 and the result is ALREADY_RUN (expected).
  3. 5PAISA (limit 367.90) and AUBANK (limit 1042.08) settle against 2026-10-06: entry events with
     strategy_version 2 and the v3 run's run_id.
  4. source_freshness row 3 COMPLETE through 2026-10-06, certifying 2026-10-05 (P8-049), so
     2026-10-06 decisions read disclosures as FACT.
  5. logs/brief_2026-10-06.txt: "Strategy 0 version 3; candidate order SEEDED_RANDOM, seed
     211cd6834da9a787", the "Open risk by book" block, and "this run (started ...) is in
     progress" in Data health; `desk status` then shows the Strategy 0 line for version 3.

## 2026-10-05 evening: first nightly with the bulk refresh and Strategy 0 v2 verified (Claude)

- Root verified; clean at b4a8f96 (= origin/master). One agent, foreground only. No network use
  by this session after the 12:28 rollout.
- 14:04 pre-flight on a temporary Desk copy (production Praman opened read-only): S0 v2 on the
  2026-10-01 events gave 6 candidates, 2 accepted, 4 rejected OPEN_RISK_BUDGET; the brief
  rendered; the 16 SCREEN_FAIL -> PASS flips were older rows that failed G2 on sector (since
  exempted), not a regression. Production unchanged.
- Nightly: PramanDailyIngest 18:00:01-18:51:11 IST, task Ready, LastTaskResult 0, overall=OK,
  GAPs 0. All 12 steps OK: bhavcopy 18:07:20, announcements 18:07:20 (bulk-mode no-op), isin_map
  18:07:24 (OK; it got HTTP 404 on 10-01 and 10-03), announcements_recent 18:07:39,
  corporate_actions 18:07:50, asm_gsm 18:08:34, bhavcopy_today 18:08:40, circuit_bands 18:08:41,
  desk_scan 18:40:19, auto_paper 18:40:30, brief 18:40:32, backups 18:51:11.
- Freshness: Desk source_freshness row 2, COMPLETE MARKET through 2026-10-05, recorded 18:07:39
  IST; complete_through 2026-10-05, market coverage from 2026-09-10 (a 2026-10-05 decision needs
  2026-10-04). Refresh 2026-09-28..10-05: 5 requests (cookie, 2 bulk, 2 split checks; all HTTP
  200; 14.3 s), 4,834 rows, 270 inserted (corporate_announcements 1,032,635), 121 returned rows
  with unresolved identity (18 of the 270 stored). Identity files reused (security_identities
  55,146, latest 2026-10-01). September still 17,077. New P8-049 (Medium): a receipt certifies its
  own run day, although 25-38% of a day's filings arrive after 18:07 IST.
- Brief (logs/brief_2026-10-05.txt): strategy_runs run 1 is S0 version 2, A1, code b4a8f96;
  trading_strategies has S0 v2 PAPER_BURN_IN and v1 SUPERSEDED_NEVER_RUN. 45 screened, 37 passed
  evidence, 2 accepted, 35 rejected OPEN_RISK_BUDGET (reason recorded on each event). Accepted:
  5PAISA limit 367.90 (= 360.90 + 0.5 x ATR20 13.9975), qty 135, stress Rs 19,866.53; AUBANK
  limit 1042.08 (= 1029.20 + 0.5 x 25.765), qty 47, stress Rs 4,897.79; S0 open risk Rs 24,764.32
  of 25,000. Kill switches clear, P&L brake EXEMPT, calibration INACTIVE; kill_switch_events 0.
  No P&L shown (brief's SEALED line; desk status shows none). Its data-health line calls its own
  run "never finished": P8-050 (Low).
- desk status: exit 0; ingestion overall=OK, no open High defect, latest session 2026-10-05, ISIN
  map OK. It shows only the manual book's open risk and positions (0.00, []): P8-051 (Low).
- desk backup verify: exit 0 in 2m08s. Desk archive desk_20261005T131032452338Z.zip integrity ok;
  row_counts include all seven new tables (kill_switch_events 0, trading_strategies 3,
  strategy_runs 1, strategy_paper_events 37, decision_contracts 37, source_freshness 2,
  record_annotations 580). Praman archive integrity ok, security_identities 55,146. Afterwards both
  production stores' row counts equal the 18:40 backup manifests.
- Network today: rollout 48 requests (backfill 28/30, audit 20/20) plus the nightly's 5; all HTTP
  200.
- Full suite after the register entries: 754 tests in 371.302s, OK, exit 0
  (logs/nightly_verify_final_suite_20261005.log). Readiness parser: no open High/Critical defect,
  none unclassified, so OPEN_CRITICAL_DEFECT stays clear.
- Next nightly (2026-10-06 18:00), verify: the 5PAISA and AUBANK entries settle against the
  2026-10-06 session (a no-fill at the limit is not a fill failure); the refresh covers
  2026-09-28..10-04 and 10-05..10-06 and fetches the 2026-10-05 identity file (about 8 requests);
  a new COMPLETE receipt.
- Waiting on the user: P8-049's proposed fix (cap each receipt at the last fully elapsed IST day,
  on read). Until then, after a night whose refresh fails, that night's S0 decisions and any
  manual assess at the default as-of (until the next COMPLETE refresh) treat the previous day as
  complete; so does a manual --as-of later than the latest receipt's day. P8-050 and P8-051 are
  Low display fixes. Still open: P8-043 (Medium) and P8-046
  (Medium; historical reach is report-only).

## 2026-10-05 midday: bulk announcement switch finished (Claude; Codex out until 2026-10-10)

- Root verified; HEAD e09d608; 17 modified + 6 untracked files from Codex's unfinished
  bulk switch. No Python running. PramanDailyIngest next run 2026-10-05 18:00.
- Requests: the 8 reconciliation calls (e09d608) are the only network use. No
  data/raw/announcement_runs capture directory and no rollout receipt exist, and
  CaptureSession creates that directory before its first request: backfill budget 0/30
  and audit budget 0/20 used before this session.
- Production stores: Praman store schema WAS migrated by an uncommitted draft at 11:58
  (5 nullable corporate_announcements columns, 2 indexes, insert trigger; no rows
  changed; security_identities absent) -> P8-048. Desk store unchanged since
  2026-10-04 21:10.
- Finished: fixed the broken trigger tuple (the cause of the reported failures),
  equity read filter now excludes INF only (keeps IN9 DVRs), and ingestion resolves
  identity from the security_identities fact table as of the run. Conditions 1-4
  verified in tests (rename pairs, hash fallback, dated ISIN, fund retained/filtered,
  revision vintages, legacy duplicates preserved and new ones blocked, failed window
  holds the watermark with WARN, per-symbol fallback behind PRAMAN_ANNOUNCEMENTS_MODE).
- Planned backfill computed read-only: 4 windows x 3 = 12 announcement calls + 15
  identity files + 1 cookie = 28 of 30. Full suite: 754 tests in 414.554s, OK.
- Committed 904c53f at 12:28 IST (before the 16:30 target; stash fallback NOT used).
- Backfill + audit run in the foreground at 12:28 (scripts/run_bulk_announcement_backfill_audit.py
  --execute-approved, 101 s, exit 0; receipt docs/desk/announcements_bulk_rollout_results.json;
  raw captures under data/raw/announcement_runs/). Requests: backfill 28/30 (cookie 1, bulk 4,
  split checks 8, identity 15), audit 20/20; all HTTP 200, no retries/errors.
  Backfill COMPLETE 2026-09-10..2026-10-05: 12,394 rows, 9,400 inserted, 2,994 already stored,
  store delta +9,400, other tables unchanged; security_identities created (55,146 rows,
  2026-09-10..2026-10-01); 163 rows with ambiguous/absent dated identity (read as UNKNOWN).
  September 2026: 17,077 rows / 17,067 unique / 2,384 symbols (equity-only identical), inside
  16,000-21,000 (was 8,847). October to 2026-10-05 (partial): 1,188. Desk source_freshness row 1:
  COMPLETE MARKET through 2026-10-05. P8-021 CLOSED.
- P8-046 audit (report only): 12/20 sampled securities' frozen tiers differ (all
  UNKNOWN_COVERAGE); ~2,356 of 4,402 renamed-security events affected (HT ~2,407), ~1,816 via
  missing disclosures; limits in docs/desk/announcement_rename_audit_results.md. 195 vs 205:
  the 10 extra current groups are 7 INF ETF groups + 3 equity renames not in the historical log.
- Tonight (18:00): bulk state last_complete 2026-10-05 -> windows 2026-09-28..10-04 and 10-05,
  4 bulk calls + cookie, identities cached. Readiness parser now finds no open High or
  unclassified defect, so the OPEN_CRITICAL_DEFECT kill switch should clear.

## 2026-10-05: bulk reconciliation and T1 exposure clarification

- Root verified D:/Agentic_ai_project/praman; clean start at 0dbfe6b. Pushed that
  commit to origin/master with the user's explicit network approval. One agent,
  foreground only. Part 1 remains deferred to Monday's run; P8-021 stays open.
- Baseline full suite: 739 tests in 542.379s, OK, Python exit 0; log
  logs/bulk_reconcile_baseline_20261005.log. Existing SQLite ResourceWarnings.
- The original September 7-13 probe was already before September 18. Eight of ten
  newly approved NSE requests used, all HTTP 200, no retries/redirects. No further
  requests needed; two unused. No production ingestion/store or fetcher changes.
- All discrepancies reconciled in docs/desk/announcements_bulk_reconciliation.json:
  3,088 exact stored-key matches, five rename explanations (HEG -> HEGAM two,
  SANGINITA -> AGASTYAEN three). Of 44 extra bulk keys, three are the SANGINITA
  aliases and 41 belong to 20 symbols excluded by the EQ-only backfill universe.
  Two HEGAM counterparts were already stored. Every stored row is present or
  explained. No pagination, boundary/timezone, revision or withdrawal discrepancy.
- Whole-week bulk 3,132 = split windows 2,492 + 640, identical persisted fields;
  both days' bulk contents match. HMT 6/6 and MELSTAR 9/9 match live per-symbol.
  Old HEG/SANGINITA requests return empty. P8-046 logs the resulting obsolete-symbol
  freshness risk as OPEN; no production remedy authorized by this investigation.
  P8-047 records/corrects inconsistent UTF-8 decoding in the draft audit script.
- Revised proposal in docs/desk/announcements_bulk_proposal.md: bulk dated windows
  up to a week, dated identity/coverage guards, existing scope retained. Proposal
  only; await switch approval. Current identity evidence cannot be backdated.
- T1 preregistration now uses the user's exact partially-exposed 2025 description
  and requires forward data for decisive out-of-sample trading-model evidence.
  No variant, period, threshold or metric changed; no T1 implementation.
- Targeted offline parity/rename mutation tests: 5 passed, exit 0. Final full suite:
  742 tests in 478.753s, OK, Python exit 0; log
  logs/bulk_reconcile_final_20261005.log. Existing SQLite ResourceWarnings remain.
  Staged diff checks clean. No source-fetch switch or T1 implementation performed.

## 2026-10-04 late session: Parts 2/3 and ingestion-health repair

- Part 1 still waits for Monday 2026-10-05 18:00 IST. Scheduler last run Oct 3
  05:54:25, result 0; next Oct 5 18:00. No Oct 5 log/brief exists yet. P8-021 stays
  open; no source-freshness, first S0 v2 run or seven-table backup closure claimed.
- Root verified D:/Agentic_ai_project/praman; clean start de08ece. Baseline full
  suite 736 tests in 340.330s, OK, exit 0. One agent, foreground; no store writes.
- P8-045: current unfinished-run flags are superseded by later completed OK/WARN
  runs; ERROR does not supersede. History is unchanged. Real status now shows
  the completed October 3 run without the October 1 current warning. Targeted
  progress/parity/raw-field guard tests: 12 passed. Final full suite: 739 tests
  in 364.627s, OK, Python exit 0 (logs/t1_prereg_session_suite_20261004.log).
  Existing SQLite ResourceWarnings remain. Diff checks clean.
- P7-001 audit: no confirmed defect ID, recalled KOTAKBANK numbers or raw-field
  rename located. Guard was preventive at first commit 7b3de51; RESULTS correction
  1c3f655. Dated clarification appended to RESULTS and DEFECT_REGISTER; historical
  entries preserved. P8-024/P8-044 remain distinct confirmed price-basis defects.
- User explicitly approved at most five NSE requests for Sep 7-13 only. Exactly
  five made, all 200: cookie, bulk, RELIANCE/TCS/KOTAKBANK. Bulk 3,132 rows / 1,357
  symbols, three live per-symbol comparisons 4/3/4 exactly equal. Stored backfill
  comparison: 3,088 exact matches, 44 extra bulk keys, five stored keys absent
  (HEG 2, SANGINITA 3), no shared-key field differences. Completeness unresolved.
  docs/desk/announcements_bulk_proposal.md proposes bulk-first only after resolving
  discrepancies and separate approval. Production fetch remains unchanged. Offline
  fixture/test committed; raw responses and hashes retained. No more requests are
  authorized by that spent five-request budget.
- docs/desk/t1_market_context_prereg.md registers four variants (baseline + three
  contrasts), fixed coverage/effect/uncertainty criteria, 2,000 paired 20-session
  moving-block date bootstraps, and all requested bitemporal inputs. No T1 code or
  outcome analysis. Official-index/VIX archives and sector membership are not yet
  verified/ingested. Existing market_index.csv uses a retrospective proxy and
  cannot stand in for official bitemporal indices.
- 2025 remains excluded from NEW T1 selection, but the protocol explicitly states
  its adverse20 outcomes were already exposed by shadow studies. It cannot be
  described as a previously unseen outcome hold-out. Implementation awaits review.

## 2026-10-04 (evening) user approvals: CLAUDE.md, Strategy 0 v2, P8-021, share basis

- Start: root verified; tree clean at ae32853; no Python running; production Desk
  store unchanged since 2026-10-03 07:00. The scheduled task PramanDailyIngest has a
  weekly trigger at 18:00 IST; next run Monday 2026-10-05 18:00 (none on Sunday), so
  "tonight's" run is that one.
- Item 1: CLAUDE.md D3/D5 amended to the approved wording plus the sentence "The T4
  calibration gate's pass criteria are pre-registered before any model is evaluated
  against them." DESIGN.md constitution 5 and changelog mirror it; the blueprint
  conflict note is marked resolved. Commit e7d13c4.
- Item 2: Strategy 0 v2 = v1 with limit-price sizing (registry: v1 kept as
  SUPERSEDED_NEVER_RUN with its exact reviewed definition; v2 PAPER_BURN_IN; the
  engine reads sizing_rule from the registered definition). v2 re-sizes each
  accepted candidate with the rulebook function at decision price + 0.5 x ATR20,
  never above the screening quantity, re-checks every decision cap at that price,
  and budgets stress measured at the limit. Exits/monitoring now record every price
  on the decision share basis (also item 4). Manual: desk assess sizes at
  planned_entry + 0.5 x ATR20 (screening keeps decision-price sizing); the AXISBANK
  real-data test now expects 65 shares (was 66). Dry run on a temp copy of the real
  store, 2026-10-01: SGIL 81 -> 66 shares, TATASTEEL 280 -> 276; 2 accepted, 4
  rejected OPEN_RISK_BUDGET; production unchanged. Suite: 724 tests in 119.208s, OK.
- Strategy 0 registered in the PRODUCTION Desk store on 2026-10-04 20:50 IST
  (ensure_registered): manual v1, S0 v1 SUPERSEDED_NEVER_RUN, S0 v2 PAPER_BURN_IN.
  Opening the store created the five automation tables additively; all nine existing
  tables' row counts unchanged (opportunity_log 580, opportunity_executions 545,
  circuit_bands 3,574, decisions/theses/paper trades 0). The burn-in's first run is
  the next nightly (Monday 2026-10-05 18:00). P8-043 CLOSED with follow-up 3 evidence.
- Item 4: tests/test_share_basis_structural.py (one synthetic 10:1 split through manual
  open, monitor/stop, pending manual close, and Strategy 0 entry/monitor/stop exit):
  every recorded price on the decision basis; costs and P&L equal the economic oracle on
  real post-split shares. Mutation-checked (two injected basis defects both caught).
  Strategy 0 monitoring now also records raw_open/raw_low as labelled evidence.
  Correction to the request's premise: P7-001 is not a defect (refuted twice per
  docs/RESULTS.md); P8-044 is the second confirmed share-basis defect after P8-024.
  Suite: 725 tests in 138.634s, OK.
- Item 3 (P8-021 additions): desk/source_freshness.py + append-only Desk table
  source_freshness: the disclosure dimension is a FACT only if the announcement source
  is complete through the day before the decision (limit 0 days; baseline 2026-09-17
  from the backfill; otherwise a nightly refresh row, failed symbols excluded; read
  via the Desk connection so replay is exact). Stale, never-covered or short-history
  windows are UNKNOWN -> INSUFFICIENT / SCREEN_FAIL. Refresh cadence now nightly; the
  nightly step records the watermark. desk/annotations.py + append-only
  record_annotations + views opportunity_log_annotated / decisions_annotated;
  scripts/desk_annotate_p8021.py. docs/OPERATIONS.md records the Amendment 2 sec. 5
  lapse as an operational deviation (recoverable by publication date). P8-021 stays
  OPEN until the first live refresh is verified. Suite: 736 tests in 350.179s, OK.
- Production annotation (scripts/desk_annotate_p8021.py --until 2026-10-04T15:40:13Z,
  the fix commit ee4900c): 580 opportunity_log rows annotated
  INCOMPLETE_DISCLOSURE_EVIDENCE (453 with windows past the 2026-09-17 coverage); no
  decisions or legacy opportunities exist; every pre-existing table count unchanged;
  source_freshness empty until the first refresh. Until then any assessment dated after
  2026-09-18 is INSUFFICIENT on disclosures, by design.

Next nightly run (Monday 2026-10-05 18:00 IST) - verify afterwards:
- announcements_recent: first refresh (~2,280 symbols from ~2026-09-10; runtime
  unmeasured), a source_freshness row through 2026-10-05, refresh state COMPLETE, and
  Sep/Oct per-symbol counts back to normal -> then close P8-021.
- Strategy 0 v2's first run (2026-10-05 candidates, sized at the limit) and
  logs/brief_2026-10-05.txt.
- `desk backup verify`: row_counts must include all seven new tables (kill_switch_events,
  trading_strategies, strategy_runs, strategy_paper_events, decision_contracts,
  source_freshness, record_annotations).
- Round-end full suite: 736 tests in 346.577s, OK, exit 0
  (logs/evening_round_final_suite_20261004.log). Commits this round: e7d13c4 (CLAUDE.md),
  b13cc7e (S0 v2 + manual limit sizing), 1d80e0e (P8-043 closed), 2877873 (structural
  share-basis test), ee4900c (P8-021 additions), plus this handoff commit.

## 2026-10-04 (afternoon) round end: status of the seven decisions

Commits (oldest first): 385ca78 (items 1, 3), e76c0d6 (item 2), c524616 (P8-007),
8954d4c (P8-021), f5ceec8 (item 4a + P8-044), b2df2a2 (follow-up 3 prereg),
bc46648 (follow-up 3 implementation), 72a0a97 (follow-up 3 results + review), plus
this handoff commit. Final suite: 724 tests in 133.397s, OK, exit 0
(logs/decisions_round_final_suite_20261004.log). Details below.

Waiting on the user:
- CLAUDE.md Desk invariants D3/D5 still say the old rule (authoritative); the
  matching amendment needs explicit approval (wording in the session report).
- Follow-up 3 PASSED; Strategy 0 v2 and the manual sizing change are PROPOSED only.
  S0 v1 will be registered and start its burn-in on the next nightly run unless the
  user decides otherwise first.

Waiting on the next nightly run (not yet happened: production desk.sqlite last
modified 2026-10-03 07:00; last weekly_ingest 2026-10-03):
- Item 7: run `desk backup verify` and confirm its row_counts list the five new
  tables (kill_switch_events, trading_strategies, strategy_runs,
  strategy_paper_events, decision_contracts).
- P8-021 close-out: confirm announcements_recent reached COMPLETE
  (data/processed/announcements_refresh_state.json) and 2026-09/10 per-symbol
  announcement counts recovered; then add the closure marker. The first refresh
  covers ~2,280 symbols; its runtime is unmeasured and may lengthen that night.
- First real S0 run: read logs/brief_<date>.txt, `desk status`, strategy_runs.

## 2026-10-04 (afternoon) user decisions on the seven open items

- Start: root verified; no Python process running; working tree clean at 7dccc19.
  Production data/desk/desk.sqlite unchanged since 2026-10-03 07:00 (no nightly
  run since Part B): none of the five new tables exist yet and Strategy 0 has
  never been registered in any durable store, so its v1 definition could still
  be amended in code before first registration.
- Items 1 and 3 (Strategy 0 rules, amended before first registration):
  fill-failure threshold 3 APPROVED, counting OPERATIONAL failures only: missing
  or unusable next-session data (ENTRY_FILL_FAILED failure=MISSING_DATA), an
  engine error while settling an entry (caught, failure=ENGINE_ERROR, run
  continues), and a crashed nightly run (journalled S0_RUN_FAILED by the nightly
  wrapper, re-raised). An untouched limit (NO_FILL) is ATTEMPT_OK: never counted
  and it ends a failure streak; a cancelled entry is NOT_ATTEMPTED (skipped).
  P&L brakes (drawdown, losing streak) EXEMPT for S0 until 2027-06-01: not
  evaluated, no P&L read (seal.brake_inputs now refuses sealed decisions like
  every other reader); status/brief show EXEMPT. They apply from 2027-06-01 and
  to any other strategy; manual trades keep the existing G7 brakes. Tests cover
  both failure cases, engine and crashed-run errors, the exemption, and a
  synthetic June 2027 run that exercises the brake end to end. Suite: 697 tests
  in 133.469s, OK.
- Item 2: DESIGN.md constitution 3 and 5 amended as the user approved (validated
  statistical-model or user probabilities only; never LLM, never invented; model
  probability/EV display-only and UNVALIDATED until the T4 calibration gate; no
  numeric trade score for anything unvalidated) with a dated Changelog section
  giving before/after text. TRADING_BLUEPRINT.md marks the conflict resolved in
  DESIGN.md. The decision contract enforces it: UNVALIDATED status for the eight
  model-estimate fields only, source must be statistical_model (with model
  version) or user, labelled display-only, never ELIGIBLE; KNOWN needs a passed
  validation reference. NOT changed: CLAUDE.md D3/D5 (same rules, authoritative)
  need the user's explicit approval; proposed wording is in the session report.
  Suite: 699 tests in 115.336s, OK.
- Item 5a, P8-007 CLOSED (mitigated): scripts/desk_p8007_verification.py (read-only,
  decision rule fixed in the script) -> docs/desk/p8007_verification.json. Catalogue
  70,638 events / 2,549 symbols all equity; Desk opportunity log 456 symbols all
  equity; 349 of 2,662 EQ-series symbols on 2026-10-01 are fund units, all excluded;
  zero fund-unit shape hits. Residuals noted in the register (no ETF split source;
  catalogue build fails open without an ISIN map; 43 unexplained equity split-shaped
  moves). desk/readiness.open_defects now honours an explicit closure marker
  (**CLOSED in the table row, or a "**Status.** Closed" line) so history is kept.
  Suite: 700 tests in 117.553s, OK.
- Item 5b, P8-021 severity HIGH (measured: announcements essentially stopped after the
  2026-09-18/19 backfill; Sep 8,847 rows, Oct 18; breaches the intent of Amendment 2
  sec. 5 weekly ingestion; recoverable because knowledge_date = publication date and
  duplicates are skipped). FIXED IN CODE: src fetch raises AnnouncementFetchError on
  non-200/non-list (src change under the user's "fix" instruction); backfill
  failures print WARN; new weekly nightly step announcements_recent
  (scripts/ingest_announcements_recent.py) after isin_map. Status stays OPEN (High)
  until the first nightly refresh is verified live; the operational gate fails on it
  meanwhile. First live refresh: ~2,280 symbols, runtime unmeasured. Suite: 706
  tests in 118.691s, OK.
- Item 4a: manual paper convention switched to the limit entry (user-approved):
  day limit = thesis planned_entry + 0.5 x ATR20 at the decision date; fill at the
  open if at/below the limit, else at the limit if the low reaches it, else NO FILL
  (terminal, journalled PAPER_OPEN_NO_FILL, never retried by the monitor). Quantity
  unchanged. HOW_TO_PAPER_TRADE.md and the DESIGN.md changelog updated.
- P8-044 (High, found and fixed while doing 4a, no records affected): the manual
  paper path priced fills/stops/exits with the history-wide split factor
  (cum_factor_up_to), i.e. the earliest share basis (TATASTEEL x10). Now every
  paper price is on the decision date's share basis via
  desk/paper/execution.basis_factor (point-in-time; 1.0 without an intervening
  bonus/split); Strategy 0 entries and monitoring use the decision date as basis.
  Demergers refuse rather than guess. Suite: 717 tests in 147.384s, OK.
- Item 4b: follow-up 3 preregistered (docs/desk/shadow_replay_followup3_prereg.md),
  committed alone before implementation or calculation. Pass criteria fixed in it:
  P1 zero per-trade breaches at the fill; P2 primary fill rate >= 60%; size
  reduction reported, not gated.
- Follow-up 3 implementation (desk/shadow_followup3.py, scripts/desk_shadow_followup3.py,
  7 synthetic tests) committed before the run. Test finding stated before results:
  the 0.80 ratio applies only where the per-trade budget binds; below ~5% ATR20 the
  10% per-stock position cap binds and the ratio is ~decision/limit (~0.98).
  Suite: 724 tests in 136.616s, OK.
- Follow-up 3 RUN (bc46648, 7 s, frozen artifacts only): PASS. Primary: 0 per-trade
  breaches at the fill in 44,442 fills (FU2 frozen size: 27.47%); fill rate 97.10%
  (unchanged); mean quantity ratio 0.907, median 0.943 (bimodal: ~0.80 where the
  per-trade budget binds, ~0.98 where the 10% stock cap binds); 1 abstention; p90
  budget use at fill 95.8% vs 113.2%. 2026 descriptive agrees. Review
  docs/desk/shadow_replay_followup3_review.md PROPOSES (not applied) Strategy 0 v2
  (size at the limit price) and the matching manual sizing change; P8-043 stays
  open until applied. Note: S0 v1 not yet registered in production.

## 2026-10-04 session end: Part A and Part B complete

Commits this session (oldest first): 3743fd3, b3a8b22, 62bb1f6, ed81160, 4cdfca3,
7da7af4, 6a57ce7, ca56f79, 15024e9, 47272e2, 08e6f58, 3372ca3 (Part A);
aa17772 (B1), 0822c7e (B2), 31d4ac0 (ACTIVE->v3), 0cc95f8 (B3), af8da10 (B4),
c65ac4f (B5), plus this handoff commit. Final suite: 691 tests in 106.442s, OK,
exit 0 (logs/session_final_suite_20261004.log). Detailed notes follow below.

Open items needing the user's decision (none blocks the nightly run):
1. Strategy 0 fill-failure kill-switch threshold 3 is PROPOSED (registry, not
   rulebook); approve or change (a change needs a new S0 version).
2. DESIGN.md constitution 3/5 (no model probabilities/scores) conflicts with
   blueprint T3-T4; decide before T3 (TRADING_BLUEPRINT.md amendments section).
3. The S0 drawdown/losing-streak brake reads sealed P&L internally; a trip is a
   visible one-bit disclosure. Keep, or exempt S0 from the brake.
4. Recommendation (not applied): switch the manual paper convention to the
   0.5 x ATR20 limit (docs/desk/shadow_replay_followup2_review.md).
5. P8-043 (open, Medium): ~27-30% of fills breach the per-trade cap at the fill;
   sizing against the limit price needs its own preregistration.
6. Operational gate fails on pre-existing P8-007 (open High) and P8-021 (open,
   unclassified severity); the OPEN_CRITICAL_DEFECT switch reports this.
7. Open observation: one unexplained >10-minute suite run (see below).

Safest next task: after the next nightly run, read logs/brief_<date>.txt,
`desk status` and the new Desk tables to verify the first real S0 run
(registration, candidates, kill-switch rows, contracts) on production; then
preregister T1 (point-in-time market and sector context features).

## 2026-10-04 T0 closeout session (Claude, resumed after Codex usage limit)

- Root verified as D:/Agentic_ai_project/praman. Corrected replay found still
  running (PID 103240, `python -u scripts/desk_shadow_replay.py`, started
  08:19:24 IST from HEAD 7801550); not touched. 47,691/70,362 records at 09:17.
- User authorised reviewing/committing new files outside the replay's hashed set
  while it runs; no full suite and no edits to hashed files (desk/*.py present at
  08:19, replay script, label/catalogue scripts, prereg, inputs) until it ends.
  desk/volatility_context.py and desk/shadow_followup2.py postdate the start and
  are not in its recorded source hashes.
- Reviewed the unfinished Codex files. P8-040 cutoff fix is present (bars queried
  as of the replay run_date). Review fixes (P8-041): explicit retrospective label
  on volatility context; two-sided baseline-opening consistency guard plus
  positive-quantity check in the limit runner; added the prereg-required
  shared-date paired-draw test. Targeted tests only (17 OK); full suite deferred.
- Wiring test tests/test_volatility_context_wiring.py is held uncommitted: it
  needs desk/cli.py and desk/scan.py edits, which wait for the replay to finish.
- Pre-existing trailing blank line in tests/test_desk_risk.py left unstaged.
- Committed review work: 3743fd3 (volatility context), b3a8b22 (follow-up 2
  code, P8-040/P8-041), 62bb1f6 (G6 comparison script, UNKNOWN-gate test).
- Corrected replay finished 09:51:48 IST. Verified: code_commit 7801550; all 49
  source hashes match committed/disk files; raw SHA-256 9a71fcf3... matches;
  70,362 unique events (52,912 SCREEN_PASS, 17,450 SCREEN_FAIL); watermarks,
  rulebook, costs, cutoffs, seed and data-input hashes identical to pre-G6; only
  repair files and the addended prereg differ. Run completion implies zero
  decision-time cap assertion failures. Results committed separately.
- A2 wiring: desk assess and desk scan append a linked VOLATILITY_CONTEXT
  journal entry after the decision/opportunity is stored and print it; no gate,
  plan or sizing change. Any lookup failure becomes UNKNOWN (P8-042: the first
  wiring let an unexpected exception abort assess after recording a decision).
- Full suite (canonical command): 646 tests in 400.179s, OK, Python exit 0; log
  logs/t0_closeout_suite_20261004.log. An earlier attempt exceeded 10 minutes and
  was stopped (cause not identified; per-test timings showed no hang, longest
  test 47s); logs/t0_closeout_timed_20261004.log has per-test durations.
- Trailing blank line in tests/test_desk_risk.py folded into the wiring commit at
  the user's request.
- User then authorised running the three short jobs in-session, foreground:
  - Follow-up re-run (7da7af4): run in a temporary detached worktree at ed81160,
    because its guard requires every replay-hashed source to match and the A2
    wiring had changed desk/cli.py and desk/scan.py. Data were byte copies;
    two CRLF-only files were matched to the main checkout's bytes. Provenance
    verified (raw hash, embedded replay provenance, sources, boundaries). 22 s.
  - Volatility reference (6a57ce7): additions only; Q1-Q5 pooled adverse20
    2.78 / 5.98 / 9.80 / 14.66 / 24.24 %. 7 s.
  - G6 comparison (script ca56f79 adds flip attribution + test; results
    15024e9). Labels/adverse20 unchanged for all 70,362; corrected decision-cap
    breaches zero for every cap; quantities only decreased. Net +72 passes, all
    FAIL->PASS: 71 via G5 (old oversized quantity also over the 1% ADV order
    cap), 1 via G6 open-risk stress (KAYA 2026-06-12, descriptive). No
    PASS->FAIL: cost-inclusive sizing makes the per-trade check non-binding.
- Corrected 2019-2025 headline (all candidates; follow-up and replay agree):
  SCREEN_PASS 45,770, SCREEN_FAIL 14,924 (14,788 with measurable ATR20).
  Adverse20: PASS 10.01% [8.71, 11.68] (n=45,564 valid); FAIL 15.99%
  [14.42, 17.87] (n=14,625 valid); FAIL minus PASS +5.98 pp [5.08, 6.84].
  Volatility-standardized gap +0.74 pp [-0.28, 1.71]; attenuation 5.24 pp.
  Pre-G6: 45,707 / 14,987; +6.01 pp [5.11, 6.89]; standardized +0.74.
- Full suite before the comparison-script commit: 648 tests in 279.529s, OK.
- OPEN OBSERVATION: one full-suite run (10:06 IST, right after the replay
  finished) exceeded 10 minutes and was stopped; it had used ~189 CPU-seconds
  in ~12 minutes of wall time, so it was mostly waiting. Three later runs took
  242-400 s with no test over 47 s. Cause unidentified. If it recurs, add a
  per-test timeout (per-test timing runner approach: logs/t0_closeout_timed_20261004.log).
- Temporary worktree D:/Agentic_ai_project/praman_followup_wt removed with
  `git worktree remove` after the commits above (it deregistered the worktree
  and deleted its files but could not delete the then-in-use empty folder;
  that empty folder was removed with rmdir). `git worktree list` is clean.
- A4 follow-up 2 run in-session (user-authorised), foreground, 26 s, from
  47272e2. Production store opened only via mode=ro for the online backup;
  SHA-256 ecb36311..., size and mtime identical before/after; temp copy
  removed. WAL sidecars praman.db-wal (0 B) / -shm appeared (WAL-mode store,
  read-only connections cannot remove them); left untouched. Snapshot hash
  equals the corrected replay's. Primary: fill 97.10% vs 99.98%; at-fill
  per-trade breach 27.47% vs 30.38%, difference -2.91 pp [-3.14, -2.70];
  p90 excess 24.1% vs 40.7% of cap; adverse20 among fills +0.14 pp.
  Review and recommendation (switch manual convention to the limit; NOT
  applied): docs/desk/shadow_replay_followup2_review.md. Untested stronger
  option (size against the limit price) needs its own preregistration.
- A5: P8-038 resolution appended (fixed and verified); P8-043 opened for the
  remaining at-fill per-trade breaches (30.38% baseline / 27.47% limit).
  Part A complete; Part B (blueprint, automation framework, decision contract,
  Strategy 0 sealed paper engine, daily brief) starts next. Part A final
  suite: 648 tests in 272.586s, OK, exit 0 (logs/part_a_final_suite_20261004.log).
- B1: docs/desk/TRADING_BLUEPRINT.md extracted from the blueprint PDF (SHA-256
  92e91128...) with pdfplumber via scripts/extract_trading_blueprint.py
  (regenerates only the text above the amendments marker). Appended the five
  user-approved Praman amendments, the T0-T10 to DESIGN.md build-order mapping,
  and OPEN constitution conflicts needing a user decision before T3 (DESIGN.md
  3/5 vs model probabilities; 9/Excluded vs A3-A4; state vocabularies). DESIGN.md
  gains only a pointer. Suite: 651 tests in 400.626s, OK.
- B2: rulebook schema gains automation_level (A0-A4; v1/v2 load as A0; v3+ must
  state it). rulebook/desk_rulebook_v3.yaml = v2 + automation_level A1 only
  (user-approved). desk/automation/levels.py refuses actions above the level and
  broker-API orders at every level. desk/automation/kill_switches.py: six
  deterministic switches (stale/inconsistent data, risk state unavailable,
  drawdown/losing-streak brake, repeated fill failures, open critical defect,
  calibration - inactive until T4); state changes appended to kill_switch_events,
  latched switches need `desk killswitch reset <switch> --reason`; `desk status`
  shows level and switches with sealed detail hidden. New append-only tables for
  B2-B4 created additively by init_desk_db. DEFECT_REGISTER: P8-043 made
  parser-readable (Medium, open); P8-038 status lines relabelled so the parser
  reads it as fixed. Parser now: open high P8-007, unclassified P8-021 (both
  pre-existing) -> OPEN_CRITICAL_DEFECT switch will trip (operational gate only).
  ACTIVE switched to v3 in a separate commit (loader refuses an uncommitted pointer).
  B2 suite (v2 still active): 665 tests in 97.359s, OK.
- rulebook/ACTIVE -> desk_rulebook_v3.yaml committed alone; suite immediately
  after: 665 tests in 113.495s, OK. Active: v3, automation_level A1.
- B3: desk/decision_contract.py implements the blueprint candidate schema; every
  field KNOWN (value + definition) or UNKNOWN (reason + supplying phase, never a
  value). Later-phase fields (calibrated probability, interval, uncertainty, EV,
  expected net return, expected loss if wrong, MAE/MFE, analogue count, market
  and sector regime, forensic flags) are UNKNOWN. Blueprint-state rule: VETO on a
  hard veto, NO_TRADE for insufficient/screen-fail, otherwise WATCH (nothing is
  blueprint-ELIGIBLE before T4). `desk assess` appends a linked decision_contracts
  row; failure is journalled, never aborts. B3 suite: 671 tests in 121.460s, OK.
- B4: desk/automation/registry.py (append-only versioned registry; S0 "baseline
  screen" PAPER_BURN_IN, purpose: exercise the automation, NOT expected to be
  profitable; `manual` registered as ACTIVE_MANUAL). Entry policy computed by the
  user's pre-stated rule from committed follow-up 2 results: LIMIT (breach diff
  -2.91 pp [-3.14, -2.70], fill 97.10%). desk/automation/strategy0.py: nightly
  engine (kill switches -> settle entries -> monitor/stop/time exits -> candidates
  vs open-risk budget, alphabetical order), one transaction per run, idempotent,
  events + linked contracts; own notional book separate from manual trades.
  desk/automation/seal.py: S0 outcomes for decisions >= 2026-09-16 refused before
  2027-06-01; brake inputs are the one privileged path (sealed detail; a trip
  discloses one bit). Nightly: weekly_ingest step auto_paper after desk_scan;
  `desk auto-paper [--date]`. Fill-failure threshold 3 is PROPOSED (registry,
  not rulebook). Dry run on a temporary copy of the real Desk store for
  2026-10-01: 6 candidates, 2 accepted, 4 rejected OPEN_RISK_BUDGET; production
  Desk store hash unchanged; temp removed. Seal dates derive from
  desk/outcome_firewall.py (single-boundary test). B4 suite: 685 tests in 108.307s, OK.
- B5: desk/brief.py + `desk brief [--date] [--write]`: blueprint daily-decision-desk
  layout with today's fields (universe, candidates, passed checks, accepted,
  fills/no-fills/failures/cancels, at-fill cap breaches, rejected by reason, kill
  switches, open risk for S0 and the manual book, data health); model fields are
  UNKNOWN with their phase; NO TRADE printed as a normal outcome; S0 outcomes
  sealed. Nightly step `brief` after auto_paper writes logs/brief_<date>.txt.
  Real-data preview on a temporary Desk copy for 2026-10-01 rendered correctly;
  production Desk store unchanged. B5 suite: 691 tests in 123.603s, OK.
- NOTE: the next nightly run (or any `desk` command) creates the five new
  append-only tables in data/desk/desk.sqlite through the existing additive
  init_desk_db path; no existing row or table is touched. The first nightly
  auto_paper run registers S0 and starts the sealed burn-in.

## 2026-10-04 G6 repair checkpoint

Cost-inclusive whole-share sizing and independent G6 per-trade cap enforcement
implemented. Unknown quantitative gates no longer derive ELIGIBLE. All six caps
checked in real SCREEN_PASS and ELIGIBLE regressions and asserted in the replay.
Full suite: 629 tests, 292.674s, OK, Python exit 0; existing ResourceWarnings.
Old reports copied to *_pre_g6; old raw retained at
 data/processed/desk_shadow_replay_pre_g6.jsonl (same registered SHA-256).
Prereg addenda/limit protocol cb89f96 precede this implementation. Corrected full
replay/follow-up and remaining context/limit work are still pending. P8-039 logs
new test quantity mismatch and repaired text encoding mistake. User's trailing
blank line in test_desk_risk.py remains unstaged.

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
