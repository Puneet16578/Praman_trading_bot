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
