# Desk shadow replay preregistration

Dated 2026-10-01. Commit this document before running the shadow replay or
examining its outcome comparisons. The frozen Phase 10 preregistration and its
pinned pipeline remain unchanged.

## Question and prediction

Do opportunities rejected by the fixed Desk screening gates have worse downside
tails than opportunities passing them? The prediction is fatter left tails among
vetoed opportunities, while average outcomes may differ little. A null, reversed,
or inconclusive result will be reported. No gate, threshold, stop convention or
sample filter will be tuned after inspecting outcomes.

## Universe, periods and information

Reuse the existing final catalogue definition and functions without editing its
scripts: EQ equity universe, absolute 60-session z-score above 2.5, volume ratio
above 2, and the existing structural-break exclusion. Preserve delisted names
and the catalogue's identity/stitching rules. Record source file hashes, store
watermarks, code commit, rulebook and cost hashes with the run.

Primary period: events 2019-10-01 through 2025-12-31 inclusive. Events from
2026-01-01 through 2026-09-15 are the spent hold-out: descriptive results only,
reported separately and never used to select parameters. Exclude events dated
2026-09-16 onward entirely from this replay, including label reads. The shared
outcome boundary refuses such events before 2027-06-01.

Every screening input must have knowledge_date no later than the event date.
Recorded-at watermarks fix the database vintage. Unknown coverage stays unknown;
missing data is not a passing gate. Report exclusions and missingness by group.
Current identity maps and unavailable historical metadata must be disclosed;
do not describe reconstructed history as an actual contemporaneous live record.

## Fixed decision and execution convention

The event-day close is the DECISION price, by design. It is never replaced by
the fill. At that evening's cutoff, freeze:

- ATR20: arithmetic mean of 20 true ranges, requiring 21 as-of adjusted sessions.
  Each true range is max(high-low, abs(high-previous close), abs(low-previous
  close)). Adjust high, low and previous close onto the same event-day basis;
  never use raw_prev_close_unadjusted.
- Stop LEVEL: decision price minus 2 times ATR20. Invalid or unavailable plans
  cannot pass screening.
- Whole-share position size, planned loss, stress loss, and G5 liquidity result,
  using the rulebook and cost version frozen for that decision.
- G1-G6 results and reasons, evidence-bundle hash, and SCREEN_PASS only if all
  six pass. Otherwise SCREEN_FAIL, retaining every failing/unknown gate. G7 and
  G8 are NOT_APPLICABLE. This is a mechanical research convention, not a trade
  recommendation or a user-authored thesis.

The following night append a separate EXECUTION record. The fill is the next
market session's opening price; quantity and the decision stop stay unchanged.
Record fill minus decision price in rupees and percent. If the open is at or
below the stop, record immediate gap-through. Recheck applicable risk and capital
caps at the fill and flag breaches without resizing or retroactively changing
SCREEN_PASS/SCREEN_FAIL. If the security has no usable next-session opening
price, record NO_FILL and its observed reason; do not substitute a later open
or infer suspension without evidence. Until the next market session is available,
execution remains pending. Execution facts do not populate opportunity outcome
columns; the opportunity log has no outcome columns.

Use this identical convention for nightly scans and the historical replay.
Research candidates are assessed independently with an empty hypothetical
portfolio, with that assumption explicit; this replay is not a portfolio backtest.
Execution observations apply to screened candidates regardless of their state,
so rejected candidates have comparable counterfactual observations.

## Outcomes and denominators

Use the validated `compute_t0_relative` label from
`scripts/phase8_robustness_relabel_t0.py`: event-close anchor, 90 GLOBAL market
sessions, equal-weighted market-relative return, EQ/BE/BZ continuity, and maximum
ten-session endpoint staleness. Preserve its direction-aware signed primary
label and report the signed mean explicitly as such. It is separate from the
long-position execution/tail measures below. Missing labels remain missing.

Tail measures for the fixed long screening plan:

- Share whose adjusted low falls at least 20% below the decision price within
  the next 20 market sessions.
- Stop gap-through frequency: opening price at/below the frozen stop before
  any earlier stop exit, including the entry opening; also report entry-only
  gap-through separately. Intraday low at/below stop otherwise ends stop exposure.
- Maximum adverse excursion from the decision price over those 20 sessions,
  and from fill for filled candidates, reported separately.
- Number of observed locked lower-circuit sessions in that window where dated
  fixed-band history exists. Use the preceding session's published band snapshot.
  Daily OHLC at the lower limit is only a daily-data proxy for a locked session;
  it cannot establish intraday order-book availability. Dynamic ranges and
  missing reports are unknown, never zero. Report the covered denominator.

Report all-candidate and filled-only counts, NO_FILL, zero-size/invalid plans,
incomplete 20-session windows, missing 90-session labels, and band coverage.
No silent complete-case denominator or zero imputation.

## Comparisons and uncertainty

Compare SCREEN_PASS against each veto gate/reason, with n for every statistic.
Reasons may overlap; state that these groups are not independent or additive.
Report absolute group statistics and differences versus SCREEN_PASS. If there
are no passes or insufficient observations, report comparisons as unavailable.
Use 2,000 bootstrap replicates with seed 20261001, resampling event-date clusters
to preserve within-day dependence; report percentile 95% intervals and the count
of usable replicates. Intervals are descriptive, with no multiplicity-adjusted
claim of discovery. Warn on fewer than 30 events or ten date clusters.

Shared inputs: catalogue selection, ATR, liquidity and stress gates use price
and volume; tail measures also use price, and the decision close anchors both
screening and the validated label. ATR-driven stops mechanically affect stop-hit
rates. These comparisons are observational and partly mechanically coupled;
they cannot establish a causal benefit or independent predictive edge.

Write `docs/desk/shadow_replay_results.md` whatever the findings, including
coverage failures, missing comparisons, provenance and reproducible commands.

## Addendum: Stress loss calculation fix (2026-10-01)

Before any replay outcome was computed, a code defect (P8-024) in the overnight-gap stress loss was fixed. The original code multiplied the decision-date raw close by the cumulative corporate-action factor before applying the percentage gap. This falsely inflated the stress loss for any stock with past splits or bonuses (e.g., BAJFINANCE used ₹9,190 instead of ₹919). The fix applies the gap fraction directly to the current unscaled close, ensuring stress loss is in current rupees. This change is committed before any shadow replay results are generated.

## Addendum: Research sector applicability repair (2026-10-01, round 2)

Inputs-only diagnosis found G2 required user-supplied sector on every mechanical
research candidate although screening always supplies no sector. Sector is now
not applicable to research G2. It remains Unknown in the evidence bundle, never
invented as a Fact. Normal user assessments still require sector. G1 and G3-G6
are unchanged; G7/G8 remain not applicable. The ATR20 entry/stop plan supplies
G5/G6 inputs; missing or invalid plans still cannot pass. Empty hypothetical
portfolio and single-candidate sector-cap assumptions remain explicit.

Nightly scans check verified current ISIN metadata. Reconstructed historical
screening cannot establish historical map freshness and records that limitation;
it uses the current identity map and no fabricated historical build date.
This repair is based only on gate inputs, before this review computes any label
spot-check or replay outcome. Prior background replay results are not used.
No gate thresholds, outcome definitions, periods or bootstrap settings change.

## Addendum: temporal availability queries (2026-10-02)

Source review before the full replay found G1's four direct availability queries
omitted `knowledge_date <= event_date`. They now apply that cutoff, so a later
publication cannot fill an apparent historical data gap. A synthetic late-known
row test proves the boundary. This correctness repair follows the five requested
label-equivalence spot checks; no replay comparisons have been inspected or used.
It changes no threshold. The evidence path also calls the unchanged daily-stat
function on its exact 62-date window; full-history equality is tested across real
split/bonus and demerger examples. The runner uses immutable temporary database
copies and exact SQL/parameter caching, including the as-of date.

Reason comparisons group the same semantic check across varying symbols and
numeric magnitudes; exact reason text is retained in event records. Missing
20-session paths are excluded explicitly from full-window statistics. The
first-session gap remains observable independently. All-candidate results are
primary, and filled-only results are also reported. These denominator details
implement the registered missingness requirements without changing the outcomes.
