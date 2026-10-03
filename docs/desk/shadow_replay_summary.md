# Historical shadow replay: findings

Completed 2026-10-03 using committed runner `67df697`. Full results:
[tables and provenance](shadow_replay_results.md),
[machine-readable results](shadow_replay_results.json).

## Limits that matter

- No historical circuit-band sessions were covered in either period. Locked-circuit
  comparisons are unavailable; this does not mean there were no locked sessions.
- Of 45,700 filled primary-period SCREEN_PASS candidates, 25,105 (54.93%)
  breached at least one cap at the next-session opening price. The fixed research
  convention preserves quantity and stop, records the breach, and does not resize
  or change the earlier screening state. Passing at the close therefore does not
  establish that the frozen plan meets caps at the fill.
- Screening and outcomes share price inputs; ATR stops mechanically affect stop
  measures. These are observational associations with an empty hypothetical
  portfolio, current identity mappings, and unavailable historical map freshness.
  They do not establish a causal benefit, profitability, or live-trading readiness.
- The 2026 period is descriptive only. No event from 2026-09-16 onward was included.

## Primary period: 2019-2025

The runner processed 60,694 candidates: 45,707 SCREEN_PASS and 14,987 SCREEN_FAIL.
There were 60,498 fills and 196 NO_FILL records. Complete 20-session paths were
available for 45,501 passed and 14,688 rejected candidates; 505 paths were missing.
The signed 90-session label was missing for 796 candidates.

| Measure | SCREEN_PASS | SCREEN_FAIL | FAIL minus PASS, percentage points (95% interval) |
|---|---:|---:|---:|
| Low at least 20% below decision price within 20 sessions | 10.00% | 16.01% | +6.01 (+5.11, +6.89) |
| Stop gap-through before an earlier stop exit | 3.91% | 5.69% | +1.78 (+1.32, +2.25) |
| Mean maximum adverse excursion from decision price | 9.70% | 11.81% | +2.11 (+1.84, +2.40) |
| Entry-only stop gap-through | 0.270% | 0.128% | -0.142 (-0.301, -0.022) |
| Mean signed 90-session market-relative return | -2.14% | -3.18% | -1.04 (-1.73, -0.36) |

Rejected candidates had worse observed 20-session downside tails on the first
three measures. Entry-only gap-through went in the opposite direction; the
finding is not uniform across metrics. The signed return is direction-aware and
must not be read as long-position profit. Entry-gap denominators are 45,578 and
14,821; signed-return denominators are 45,110 and 14,788.

Intervals use the registered 2,000 event-date cluster bootstrap replicates and
seed 20261001. All five differences above had 2,000 usable replicates. Intervals
are descriptive and not adjusted for multiple comparisons. Individual gate and
reason groups overlap; their complete results, including empty groups, are in
the full report.

Among primary SCREEN_PASS candidates, fill breaches included the planned-risk
cap (15,080), per-stock capital cap (16,097), turnover cap (128), and open-risk
budget (3). These counts overlap and must not be added together.

## Descriptive 2026 period

There were 9,668 candidates: 7,133 passed, 2,535 rejected; 9,632 had fills.
The >=20% adverse-move rate was 7.74% versus 12.88%, a difference of +5.15
percentage points (95% interval +3.13 to +7.45). The stop-gap difference was
inconclusive: +0.63 points, interval -0.64 to +2.01. There were 529 incomplete
20-session paths and 3,702 missing 90-session labels. These results do not
provide an independent hold-out evaluation.

## Completion and verification

- 70,362 ordered event records match the eligible catalogue exactly; 276 of the
  original 70,638 catalogue events fall outside the registered period.
- Verified the raw artifact SHA-256, all 47 recorded source hashes, 640
  group/statistic denominators and estimates, and exact generated Markdown.
- Source databases were opened read-only and copied with SQLite's backup API.
  Analysis used disposable read-only copies; no decisions or paper trades were made.
- The interrupted 17,523-record artifact was preserved separately under
  `data/processed/desk_shadow_replay_round2.interrupted_20261003_17523.jsonl`.
- Reproduce with `python -u scripts/desk_shadow_replay.py`. Source watermarks,
  cutoffs, hashes, rulebook and cost versions are recorded in the full report.
