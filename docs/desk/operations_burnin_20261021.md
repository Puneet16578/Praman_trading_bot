# Strategy 0 operational record since 14 October

Read-only as of 21 October 2026 before market open. Sources: normal daily briefs,
`logs/weekly_ingest.log`, operational `strategy_runs`, `strategy_gaps`, unsealed
defect-switch metadata, monitoring event dates and circuit-band metadata. Both
SQLite connections used `open_readonly`; no strategy outcome detail, prices,
returns, P&L or sealed switch payload was selected. No nightly/replay was run.

| Session | Classification | Evidence |
|---|---|---|
| 14 October | Decided | Run 8; 46 candidates, 0 accepted, 46 rejected for open-risk budget; no entry blocker; 2 positions monitored. |
| 15 October | Skipped | No strategy run; BATTERY_SKIP gap; ingestion skipped at 18:00 with battery 13%. |
| 16 October | Skipped | No strategy run; BATTERY_SKIP gap; ingestion skipped at 20:35 with battery 18%. |
| 19 October | Decided | Run 9; 37 candidates, 2 accepted, 35 rejected for open-risk budget; `entry_blocked_by=[]`; defect-readiness switch active. |

No session in this interval was blocked from Strategy 0 decisions by the defect
gate. `OPERATIONAL_GATE_FAIL` is not an entry-blocking effect in the current code.
See [gate audit](operations_gate_20261021.md). The gate first appears active in
the 19 October brief and its stored unsealed trigger agrees. The earlier brief
on 14 October says it had never triggered.

17/18 October are weekend dates. The user identified 20 October as the NSE
Dussehra holiday; no 20 October session exists in the store. The 22:00 run reused
the latest session (19 October) without adding a duplicate strategy decision.
21 October is not yet due at this audit's pre-market time.

## Price-band catch-up

The 19 October run recorded all three dated reports, as confirmed by aggregated
rows in `circuit_bands`. Times below are IST; original stored timestamps are UTC.

| Report date | Rows | First recorded | Knowledge date | Published timestamp |
|---|---:|---|---|---|
| 15 October | 3,572 | 19 October 18:09:05.495659 | 19 October | 15 October 18:10:39 |
| 16 October | 3,587 | 19 October 18:09:06.558107 | 19 October | 16 October 19:22:09 |
| 19 October | 3,575 | 19 October 18:09:08.117747 | 19 October | 19 October 18:01:08 |

These are report dates, not the session dates when their bands apply: the report
from the preceding trading session supplies a session's limits. Late reports
retain 19 October knowledge dates; they were not backdated into missed decisions.
No download or ingestion was performed for this audit.

## Stop-monitoring catch-up and gaps

On 19 October, stored `MONITORED` event dates show two checks for 15 October,
two for 16 October and one for 19 October, all recorded at approximately
18:41:25 IST. Source `strategy0.py` iterates every unchecked session in time order
using the existing stop rule. This verifies the monitoring catch-up, not its
sealed financial outcomes; no stop/exit price or result was inspected.
The run-level monitored count is 2 positions, not the number of session checks.

Exactly two gaps in this interval were recorded by run 9 at 18:41:25 on
19 October: **15 October BATTERY_SKIP** and **16 October BATTERY_SKIP**.
The strategy did not create retroactive candidate decisions for those dates.
No new gap was recorded for the 20 October non-session.

## Exact skip/retry lines

From `logs/weekly_ingest.log`:

```text
=== 2026-10-15T18:00:01.944768+05:30 weekly_ingest skipped: WARN on battery at 13% (below 30%); no step ran; the next run catches up ===
=== 2026-10-16T20:35:44.548530+05:30 weekly_ingest skipped: WARN on battery at 18% (below 30%); no step ran; the next run catches up ===
=== 2026-10-19T20:00:01.067052+05:30 weekly_ingest retry not needed: this evening's run started at 2026-10-19T18:00:02.769699+05:30 ===
=== 2026-10-19T22:00:00.996386+05:30 weekly_ingest retry not needed: this evening's run started at 2026-10-19T18:00:02.769699+05:30 ===
=== 2026-10-20T18:00:02.975002+05:30 weekly_ingest skipped: WARN uncommitted changes in files the nightly runs or reads: desk/s1/evaluation.py, desk/s1/execution.py, desk/s1/statistics.py, docs/DEFECT_REGISTER.md; no step ran; the next run catches up ===
=== 2026-10-20T20:00:00.229418+05:30 weekly_ingest skipped: WARN uncommitted changes in files the nightly runs or reads: desk/s1/evaluation.py, desk/s1/execution.py, desk/s1/statistics.py, docs/DEFECT_REGISTER.md; no step ran; the next run catches up ===
=== 2026-10-20T22:00:00.380025+05:30 weekly_ingest started ===
=== 2026-10-20T22:00:00.380025+05:30 weekly_ingest step=backups status=OK completed=2026-10-20T23:58:44.672585+05:30 ===
```

The completed 20 October run is overall WARN (holiday bhavcopy gap, ISIN HTTP
404); every other step is OK. Task history independently reports last result 0.
No additional 20:00/22:00 retry lines for 15/16 October appear in this log;
their execution cannot be inferred from absence. No task-history reconstruction,
new retry, data repair or missed-decision replay was performed.
