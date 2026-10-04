# Shadow replay follow-up 3 preregistration: size against the limit price

Dated 2026-10-04. Requested by the user in their message of 2026-10-04 ("pre-register follow-up 3
before running it"). Committed before any implementation or calculation of this experiment. No
follow-up 3 result has been computed. Parameters will not be tuned after results are seen.

## Known before registration (not findings)

Follow-up 2 (`shadow_replay_followup2_results.md`) is known: the 0.5 x ATR20 limit fills 97.10% of
primary passes and leaves 27.47% of its fills over the per-trade cap at the fill, because the
quantity was sized at the decision price. By arithmetic alone, with the registered 2 x ATR20 stop
and a limit 0.5 x ATR20 above the decision price, per-share risk at the limit is 2.5 / 2.0 = 1.25
times that at the decision price, so where the per-trade budget binds the quantity ratio should be
near 0.80 before costs and whole-share rounding. That expectation is stated here, not discovered.

## Fixed comparison

Population: the corrected G6 replay's SCREEN_PASS records (raw SHA-256 `9a71fcf3...`, the replay
whose provenance is in `shadow_replay_results.json`), with the frozen rulebook and cost config
recorded in that provenance and an empty hypothetical portfolio, exactly as screening sized them.
Execution inputs: follow-up 2's frozen per-pass next-session evidence
(`data/processed/desk_shadow_followup2_execution.jsonl`, SHA-256 recorded in
`shadow_replay_followup2_results.json`). No database access.

- Baseline quantity q = the corrected plan quantity. Parity check before anything else:
  `compute_position_size(decision price, stop, rulebook, 0, 0, 0, costs)` must equal q for every
  pass; any mismatch aborts.
- Limit price L = decision price + 0.5 x decision-time ATR20 (follow-up 2's limit).
- Variant quantity q_L = `compute_position_size(L, stop, rulebook, 0, 0, 0, costs)`: the same
  function and arguments with the entry replaced by L. Stop, ATR20, costs and rulebook unchanged.
  Checks that abort on failure: q_L <= q for every pass, and every decision-time cap measured at
  the decision price with q_L is within its cap.
- Execution: follow-up 2's limit rule and its recorded status per pass, unchanged. A pass is
  FILLED under the variant if follow-up 2 recorded FILL_OPEN or FILL_LIMIT and q_L >= 1; q_L = 0
  is an abstention (no order). Unknown execution inputs stay a separate count.

Primary period 2019-10-01 through 2025-12-31; 2026-01-01 through 2026-09-15 is the separate,
spent, descriptive hold-out. The shared outcome firewall rejects forward or out-of-period events
before any record is read. No outcome (labels, adverse moves, returns) is computed.

## Measures

For each period:
1. Size: distribution of the quantity ratio q_L / q over all passes (mean, median, p10, p25, p75,
   p90), the share of passes with q_L < q, and the count of abstentions (q_L = 0). Planned loss at
   the decision price under q_L and q, as a percentage of the per-trade cap (median, p90).
2. Fill rate: variant fills / all passes, beside follow-up 2's limit fill rate (identical except
   for abstentions), with the paired difference.
3. Per-trade cap at the fill: count and rate of variant fills whose cost-inclusive planned loss
   `planned_loss_inr(fill, min(stop, fill), q_L, costs)` exceeds the per-trade cap; and the budget
   used at the fill (median, p90 of planned loss / cap) beside follow-up 2's frozen-quantity fills.

Intervals: 2,000 event-date-cluster bootstrap replicates, seed 20261001, percentile 95%, NumPy
linear quantiles, all passes kept in the date sampling frame, statistics conditioned on their
stated denominators; warnings below 30 valid events or ten date clusters. No multiplicity
adjustment and no parameter selection follows results.

## Pass criteria, fixed now

- P1, construction: zero per-trade cap breaches at the fill among variant fills, in both periods.
  For any fill at or below L, planned loss cannot exceed planned loss at L, which the sizing keeps
  within the cap, provided costs are non-decreasing in price. A single breach means the
  implementation or that premise is wrong: FAIL, and it is logged as a defect.
- P2, practicality: primary-period variant fill rate of at least 60%, the same threshold the user
  set for the Strategy 0 entry rule.

Size reduction is reported for the user's judgement, not gated: no threshold for an acceptable
reduction has been approved. If P1 and P2 both pass, the results review PROPOSES, without
applying, Strategy 0 v2 (sizing against the limit price, everything else unchanged) and the
matching manual-convention change (size manual decisions against planned_entry + 0.5 x ATR20).
Whatever the result, write `shadow_replay_followup3_results.md` and JSON.

Tests before the real run: parity with the screening sizing, the variant's monotonicity, the
by-construction bound at fills at and below the limit, abstention handling, untouched and unknown
execution, shared date draws and the firewall. Commit the tested implementation before execution;
record raw, execution-evidence and source hashes, the implementation and preregistration commits,
and the reproducible command. No active rulebook, registry or paper convention changes.
