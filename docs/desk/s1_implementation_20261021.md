# S1 implementation and sealed rehearsal

Completed 21 October 2026 through item 5 only. **No real S1 development or
2025 evaluation has run.** Development evaluation requires separate user approval.
Synthetic rehearsal results are not evidence of an S1 edge.

## Delivered

1. `desk/s1/inputs.py`, `report.py`, `scripts/s1_build.py` freeze a new S1 funnel.
   They reuse the frozen A/B/C filing categories, cutoffs, gates and historical
   context helpers, and T1's dated identity snapshots and weekday calendar.
   Event-stock, market, peer and turnover populations use dated ISIN eligibility.
   S1 adds unstable-ratio, unknown G3/G5, active ASM and weekend exclusions, tests
   G5 at the limit-sized quantity, and freezes the explained comparison group.
   `sensitivities.py` and `scripts/s1_freeze_sensitivities.py` freeze input variants.
   The old A/B/C scripts and their reports remain unchanged.
2. `reader.py`, `execution.py` and `evaluation.py` compose guarded reads, S0 entry,
   sizing, stop and lock primitives with S1's registered execution rules.
   Triggered exits stay pending through locks and execute at the next unlocked
   session open; S0 itself is unchanged. Missing bars, boundary purges/censoring,
   actual chronological position occupancy, costs/slippage, MAE, separate path
   labels and benchmarks are implemented. All real outcome queries pass through
   the S1 guard and shared firewall; S1 has a hard 2025-12-31 ceiling.
3. `statistics.py` reuses T1's block-bootstrap primitives with the fixed S1
   horizons/family, sample and usable-draw requirements, consistency and verdict
   logic. Sensitivities do not choose a verdict.
4. `tests/test_s1_*.py` cover adversarial post-D selection reads, post-exit MAE,
   period boundaries, both-barrier STOP priority, a filing one second late,
   persistent locked exits, actual occupancy, fixed family/horizons and usable
   draws. The real reader SQL path is exercised on synthetic in-memory SQLite.
5. `rehearsal.py` and `scripts/s1_rehearsal.py` run seeded random labels with
   real S1/legacy readers and database opens blocked. Captured S1 method aliases
   also fail through a context-local seal. No real bar-availability probe is used.

## Inputs-only counts

See [complete input report](s1_inputs_complete_20261020.md) and its
[JSON audit](s1_inputs_complete_20261020.json) for all years, group/horizon cells,
distinct dates, turnover bands, exclusion reasons and exact overlaps.
Absent sparse-counter keys mean zero.

| Year | Unexplained h1 | Unexplained h3 | Explained h1 | Explained h3 |
|---|---:|---:|---:|---:|
| 2019 | 0 | 0 | 0 | 0 |
| 2020 | 20 | 20 | 37 | 37 |
| 2021 | 168 | 168 | 331 | 331 |
| 2022 | 82 | 82 | 154 | 154 |
| 2023 | 279 | 279 | 625 | 625 |
| 2024 | 156 | 154 | 490 | 489 |
| Development total | 705 | 703 | 1637 | 1636 |
| 2025 | 239 | 235 | 316 | 314 |

These counts remove scheduled period-boundary events, but precede fills and actual
position exclusions. The **scheduled-overlap count is not a bound**: delayed exits
can add exclusions and early stops can remove them. Actual occupancy is enforced
only inside the evaluation runner.

Development-only pooled absolute-z terciles are
`[2.8669916004097815, 3.5713588405696233]` (type 7, upper ties).
All 1,545 study dates have UNKNOWN by-18:00 bhavcopy availability. Available logs
cover later dates; successful-step timestamps do not prove a matching-D file was
available. The freeze's metadata audit records 12 logged dates, one with a step
completed by 18:00 and 11 with only later completions. These are not publication
availability counts and do not include the subsequent 20 October nightly.

The immutable local artifact is `data/s1/inputs_complete_20261020_v1.json`
(569,704,185 bytes), SHA-256
`c0d88d62719f090d1bde5430e9801ddad57d03715555f37914d2d6c3597bb309`.
It preserves the original freeze and adds the registered sensitivity exclusions
and explicit rulebook provenance. Artifact/parent hashes, primary populations,
dates, bands, overlaps, terciles and active rulebook/cost hashes were verified on
21 October. The live stores were subsequently updated by the nightly; no rebuild
against those updated stores was performed.

## Rehearsal and verification

Command, run once from clean commit `b539e7e328accadd38aff58d472a4807c2b9cb30`:

```text
python -B scripts/s1_rehearsal.py --inputs data/s1/inputs_complete_20261020_v1.json --output docs/desk/s1_rehearsal_20261021.json --report docs/desk/s1_rehearsal_20261021.md
```

Exit 0, 10.14 seconds, seed 20261020. Reader seal verified; real outcome reads 0.
Primary and all eight one-change sensitivities completed, each with 2,000 usable
draws for tests (a) and (b), h1 and h3. All post-entry prices, missingness, circuits,
benchmarks, market states and labels were synthetic. No 2025 rehearsal was run.
See the [rehearsal report](s1_rehearsal_20261021.md) and
[complete synthetic diagnostics](s1_rehearsal_20261021.json).

Full suites on 21 October:

```text
Ran 1109 tests in 216.204s
OK
Ran 1109 tests in 194.509s
OK
```

Both Python exits were 0. Existing P8-088 SQLite ResourceWarnings persist.
The final session suite result is recorded in the final report/handoff commit
message. No production-store writes, downloads or background jobs were performed.

## Commits and remaining limitations

Each implementation step had a passing full suite before its commit:

| Commit | Step | Full-suite tests |
|---|---|---:|
| dc009f1 | Approved blocked-exit addendum and registry mention, before code | 1073 |
| 2e1df08 | Frozen input funnel | 1079 |
| f9bd480 | Guarded execution | 1091 |
| c11f81d | Primary input coverage report | 1102 |
| 1418b60 | Fixed inference and sensitivities | 1106 |
| 59216ad | Sealed rehearsal implementation | 1106 |
| a1e041c | Scheduled purge before occupancy; reader/lock checks | 1109 |
| b539e7e | Verified complete input report and nightly handoff | 1109 |

P8-094 remains open: the shared firewall's fixed-date release is weaker than D7.
It must be fixed before 1 June 2027. Any future forward-book registration must
require evidence that the binding evaluation has run. No firewall code changed.

Dividend diagnostics use parsed record/book-closure dates, not a complete
ex-dividend calendar; absence of evidence remains UNKNOWN and no dividend is
credited. Other registered identity, availability, daily-bar, special-session,
cost and 2025-exposure limitations remain. Shared price inputs mean the group
comparison is not causal.

The 20 October 18:00 and 20:00 runs skipped because the S1 tree was left dirty.
The user stashed it; the 22:00 retry completed at 23:58:44 with backups OK,
overall WARN, a holiday bhavcopy gap and ISIN HTTP 404. The 19 October brief shows
an active operational gate for unclassified P8-088. Read-only review traced the
severity-heading mismatch and logged P8-099; no operational fix was made.

Protected firewall, S0/seal, task, rule documents, cost configuration and other
registrations are unchanged. The only registration edits are the explicitly
approved S1 Addendum 1 and registry mention. Stop here; real evaluation remains a
separately approved step.
