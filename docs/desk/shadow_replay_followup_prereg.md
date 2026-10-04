# Shadow replay follow-up preregistration

Dated 2026-10-04. Commit this document before implementing or running the two
follow-up analyses. These questions were requested after the original aggregate
results were known: the primary adverse-move gap was about 6.01 percentage points
and 54.93% of filled passes breached at least one cap. This is a registered
follow-up to known results, not a claim that the original outcomes were unseen.
No quintile results, cap-excess distributions or 90%-variant results have been
computed in this session. The 90% parameter will not be tuned after the run.

## Fixed inputs and inherited boundaries

Reuse the completed event records at
`data/processed/desk_shadow_replay_round2.jsonl`, raw SHA-256
`aa619d2e23f113c46e4b4df11307b18bc371837ed5d6bf7069a7d140204acb3d`,
and the provenance/rulebook/costs in `docs/desk/shadow_replay_results.json`
committed at `64ac2f1`. Verify the hash, event identities, original summary counts
and quantitative reconstruction of existing breach flags before accepting results.
No fresh ingestion, new price path, or live journal write is required.

Keep the original primary period (2019-10-01 through 2025-12-31) and descriptive
spent hold-out (2026-01-01 through 2026-09-15) separate. Reject out-of-period
records. Use the single `desk.outcome_firewall.require_outcome_access` before
interpreting any event's outcomes. The frozen Phase 10 preregistration and pinned
pipeline are unchanged. The stored Amendment 5 `compute_t0_relative` label,
signed convention, 90-global-session horizon and missingness are retained without
relabeling; the volatility question uses the original separate `adverse20` field.

The original event-close decision, next-session raw opening fill, frozen stop,
whole-share quantity, corporate-action conventions and empty hypothetical
portfolio remain. Current identity mapping and unavailable historical map
freshness remain limitations. No trade recommendation or readiness claim follows.

## A. Volatility control

**Question/prediction.** The rejected-minus-passed gap in the rate of a low at least
20% below the decision price over the next 20 global market sessions will narrow
within volatility quintiles. If the gap disappears after control, this is
consistent with the gates acting mainly as a volatility filter in this sample.
It is not proof of a causal mechanism or equivalence from a nonsignificant test.

Volatility is `100 * frozen ATR20 / frozen decision_price`. Both values were known
at the decision. The original ATR window ends on the event date and therefore
includes its bar: this is a decision-time, pre-execution control, not an ATR
recomputed to exclude the event bar. No future prices enter the control.

Define the 20th, 40th, 60th and 80th percentiles from all primary-period candidates
with finite positive ATR20 and decision price, pooling PASS and FAIL and including
those with missing outcomes. Use NumPy's linear quantile convention. Freeze these
four boundaries for descriptive 2026 and filled-only sensitivity results. Assign
ties on a boundary to the upper interval (`searchsorted(..., side='right')`);
never split equal values to force equal counts. Report actual boundaries/counts
and retain empty quintiles if boundaries tie.

In each quintile report PASS/FAIL candidate counts, valid-outcome and missing
counts, event-date clusters, adverse-move rates, FAIL minus PASS, 95% intervals
and usable bootstrap replicates. Invalid/unavailable volatility is excluded from
the controlled comparison with counts and outcome missingness reported by state;
it is not assigned to the lowest quintile or silently counted as low risk.
Missing `adverse20` remains missing, matching the original full-window requirement.

Report the unstratified gap in the same valid-volatility population, plus a
standardized gap: weighted mean of quintile-specific differences using the pooled
candidate share in each quintile, fixed within that period/cohort. If any positive-
weight quintile lacks a valid PASS or FAIL outcome, the overall standardized
comparison is unavailable; do not renormalize away a missing group. Also report
unstratified minus standardized gap, with paired bootstrap intervals. The all-
candidate cohort is primary; the original filled-only cohort is a sensitivity.

Interpret the direction and magnitude of residual gaps and attenuation together.
If intervals are wide or overlap zero, explicitly distinguish uncertainty from
evidence that the effect is zero. No equivalence margin or threshold will be
chosen after seeing results. ATR and the adverse-move outcome still share price
inputs; broad quintiles do not remove all confounding.

## B. Breach sizes and the one 90% variant

Primary population: original SCREEN_PASS candidates with an observed original
fill in each period. Report original passes, NO_FILL and excluded/unknown inputs
as well. Do not promote failed candidates, rerun gates to choose a new sample,
change stops, or resize after observing the fill. Reuse frozen decision inputs.

Evaluate all six applicable caps, separately:

1. Planned loss including original round-trip costs / per-trade risk budget.
2. Stress loss / open-risk budget (empty prior portfolio).
3. Position value / per-stock capital cap.
4. Position value / per-sector capital cap (the original independent-candidate assumption).
5. Order value / permitted fraction of frozen average daily turnover.
6. Stressed days to exit / maximum allowed sessions, with original participation
   and stressed-volume assumptions unchanged.

A breach is strictly `usage > cap`. Its size is `100 * (usage / cap - 1)` among
breaches of that cap. Report denominator, breach count/rate, conditional median
and 90th percentile of excess, with confidence intervals. Report zero-inclusive
median/p90 of `max(0, excess)` over evaluable fills too, so a few large breaches
cannot be confused with a typical fill. An empty breach group has unavailable
conditional sizes, not zero; unknown/nonpositive caps or missing inputs are
explicit exclusions, not passes. Use the linear quantile convention.

**Fixed variant.** At the decision price choose the largest integer quantity
between zero and the original quantity that fits at or below 90% of *every*
applicable cap above. Do not simply multiply quantity by 0.9: fixed costs and
whichever cap binds must be respected. Keep allocated capital, stop, cost rates,
participation rate and volatility assumptions unchanged. Use exact monotone
integer search and the existing `planned_loss_inr` cost function. Recompute
planned loss for the new quantity; scale the original floor, worst-gap and
locked-circuit components by new/original quantity. Stress is their maximum and
the recomputed planned loss. An unavailable locked component stays unavailable
under the original convention and is disclosed; no new band data is invented.

Freeze the resulting quantity before seeing the opening price. At that opening,
reprice the frozen non-planned stress components by fill/decision price, and
recompute planned loss with `min(stop, fill)` exactly as the original execution
observer does. Compare with the original **100%** caps at execution. Record
variant breach rates and excess sizes using the same definitions. This variant
is research only; it does not modify the active rulebook or live sizing code.

If the variant sizes to zero, report abstention and exclude it from its executed-
fill denominator. Do not describe abstentions as successful nonbreaching fills.
Show baseline/variant rates on their respective executed populations and paired
rate differences on candidates executed in both; also report the number of
original fills declined. Size differences compare the two conditional excess
distributions (whose members can differ), not only breaches common to both.
Prediction: headroom reduces breach rate; the change in excess sizes is reported
without an additional directional claim. Corporate-action raw-fill conventions
and the original missing-band limitation remain explicit.

## Uncertainty, verification and reporting

Use 2,000 event-date-cluster bootstrap replicates, seed 20261001, percentile 95%
intervals and paired draws for PASS/FAIL, unstratified/standardized, and baseline/
variant comparisons. Sample the period/cohort's event dates with replacement and
retain all their rows; do not resample individual securities independently.
Quintile boundaries and standardization weights stay fixed across replicates.
Recompute conditional breach-size quantiles within each draw with exact repeated-
observation multiplicities. Record usable draws for every interval; unavailable
comparisons remain unavailable. Warn below 30 valid events or ten date clusters
for the specific statistic, including conditional breach-size statistics.
Intervals are descriptive, with no adjustment for multiple comparisons.

Before any real follow-up calculation, test tied/empty quintiles, missing controls
and outcomes, weighted quantiles versus explicit replicated samples, whole-share
headroom with fixed costs, frozen quantities, cap parity with existing checks,
zero-size abstention, paired cluster behavior, and the firewall. Record any defect
and its repair. Commit tested implementation before the real analysis.

Write `docs/desk/shadow_replay_followup_results.md` and a JSON companion whatever
the findings, including null/reversed/unavailable results, input hashes, code and
preregistration commits, periods, thresholds, denominators and reproducible command.
Update HANDOFF, run the full suite, commit and push. Do not tune this protocol or
the 90% factor after outcomes are inspected; any necessary correctness repair
must be disclosed separately.

## 2026-10-04 addendum: P8-038 decision-time cap correction

Registered before corrected historical replay or follow-up calculations. The first
follow-up exposed 12,693 primary and 1,958 descriptive filled SCREEN_PASS events
whose decision-time planned loss exceeded the per-trade cap. Sizing omitted
round-trip fees and G6 did not independently enforce this cap. The rulebook's
both-side-cost definition is authoritative; the follow-up calculation is retained.

Correct sizing to the largest whole-share quantity within the existing budgets
including both-side costs, and enforce the per-trade cap independently in G6.
Do not change the active rulebook, costs, thresholds or paper entry convention.
Historical quantities and potentially screening states will change. Rerun the
original replay and first follow-up on the same catalogue and read-only store
snapshots, preserving previous raw records/reports under a pre_g6 suffix and
reporting old/new results and state transitions. All periods, firewall, labels,
bootstrap settings, volatility boundaries and the fixed 90% variant stay unchanged.
Corrected records replace the original frozen-input hash for the corrected run;
record their hash, source hashes and implementation commit explicitly. The original
hash and commits above remain the provenance of the superseded results. This
correction is disclosed after seeing the original findings, not a fresh blind test.
