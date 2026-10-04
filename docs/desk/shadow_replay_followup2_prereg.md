# Shadow replay follow-up 2 preregistration

Dated 2026-10-04. Commit before implementing or calculating this experiment.
Earlier results and the decision-time G6 defect are known. Use the corrected G6
replay, whose correction is registered in both earlier preregistration addenda.
No limit-entry results have been computed. Parameters will not be tuned.

## Fixed comparison

Use corrected SCREEN_PASS decisions, unchanged quantities/stops/costs and an empty
hypothetical portfolio. Baseline is the original next-global-session raw opening
fill. Variant limit = decision price + 0.5 * decision-time ATR20. On that same next
session: if open <= limit, fill at open; otherwise if low <= limit, fill at limit;
otherwise NO_FILL. No later-session order, resizing, 90% headroom combination,
price improvement assumption or change to paper trading is permitted. Missing
bars, invalid prices or unavailable low when required are explicit unavailable
execution inputs; report separately from an observed untouched limit. Retain the
original EQ/BE/BZ row priority and raw-price/corporate-action conventions.

Primary period is 2019-10-01 through 2025-12-31; 2026-01-01 through 2026-09-15 is
separate descriptive spent hold-out. Use the same catalogue, store watermarks,
identity mapping and shared outcome firewall. Reject forward/out-of-period events
before reading outcomes. The pinned Phase 10 pipeline and pre-registration stay
unchanged. Retain the original Amendment 5 label function and its missingness;
for this question use the original adverse20 outcome: a low at least 20% below
DECISION price within the next 20 global sessions with the original full-window
requirement. Report its rate among each convention's fills. It is not a return
measured from fill, and no intraday order of extremes is inferred from daily bars.

Report candidate/fill/no-fill/unknown counts and fill rate over all passes, with
unavailable input counts visible. For each convention's fills report per-trade
planned-loss cap breach count/rate, and conditional median and 90th percentile
of 100*(cost-inclusive planned loss / cap - 1), restricted to breaches. Use
planned_loss_inr(fill, min(stop, fill), quantity, costs). Empty breach groups have
unavailable conditional sizes. Report adverse20 valid/missing denominators and
rate among fills. Include variant-minus-baseline differences, stating that the
fill cohorts can differ, and a common-fill sensitivity for breach/adverse rates.

Use 2,000 event-date-cluster bootstrap replicates, seed 20261001, paired draws for
both conventions, percentile 95% confidence intervals, NumPy linear quantiles and
exact repeated-row multiplicities for size statistics. Retain all pass events in
the date sampling frame and condition on valid fills/outcomes for each statistic.
Report usable draws and warnings below 30 valid events or ten date clusters.
No multiplicity adjustment or parameter selection follows results.

Test open-at-limit, open below, intraday touch, no touch, missing bars, conditional
sizes, fixed quantity, shared-date draws and firewall before the real run. Commit
tested implementation before execution. Preserve baseline artifacts and record
raw/source hashes, implementation/preregistration commits, reproducible command,
periods and exclusions. Write shadow_replay_followup2_results.md and JSON whatever
the results. Daily OHLC cannot establish tradability, queues or intraday timing;
missing bands remain unknown. No active rulebook or paper convention changes.
