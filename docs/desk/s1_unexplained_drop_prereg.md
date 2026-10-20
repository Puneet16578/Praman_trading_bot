# S1 / idea B: preregistration

Registered 19 October 2026. DOCUMENTS ONLY.

Approved by the user in their message of 19 October 2026.

Registration commit: `d176f414eb6371ddb6eccddff778ca19f41f9218` (19 October 2026). This hash was recorded after the registration commit was created.

No implementation, new research counts, outcome computation or trading is authorised.

Original counting baseline: 2d83e28c5d1d094fd1ee0be65b77a36f2355cb2e. Revision checked against checkout 0cd41bc4cf3ef5d3f26e841b5c6288b8ca854bfd. Repository paths are relative to D:/Agentic_ai_project/praman. Existing registrations, S0, rules, costs and the firewall remain unchanged.

## 1. Scope and resolution of C1–C6

S1 v1 / idea B is cash-equity delivery, LONG-only research. Hypothesis: after a large, high-volume catalogue drop with no visible explanation, the stock “rebounds over the next one to three sessions” by more than costs.

C1: every S1 identity decision uses T1's dated ISIN snapshots and availability ASSUMPTION: a snapshot dated S counts from the session after S. A symbol counts on D only if a snapshot known by D lists it with a non-fund ISIN. Carry the last known snapshot forward as in T1. This applies to event-stock eligibility, market/peer membership and other identity-based descriptive universes, including turnover bands. No present-day roster substitutes for historical eligibility. The stored catalogue remains the event source; its inherited identity stitching is a limitation, not repaired by this eligibility check. Implementation must freeze a new funnel version; existing A/B/C counts remain the pre-registration counting record, not counts of the revised S1 population.

C2: GSM is omitted from research-population selection in every period, including 2025. Neither known GSM status nor unknown GSM history excludes or admits an S1 event. There is no pre-2025 GSM history, and no assumption that unknown means not under GSM. The 2025 diagnostic is prior exposure only, never a justification for selection. Live G4 still applies GSM. This settles the earlier question 3.

C3: register h=1 and h=3 sessions separately. The blueprint's 1/3/5/10 list is a T2 programme aim; 5 and 10 are NOT ATTEMPTED for S1. There is no two-session primary.

C4: leave weekend sessions out of S1 decisions, entries, exits, holding counts and bootstrap dates, following T1 addendum 3(b). Exclude and count an event whose next session in the observed exchange calendar is a weekend session; do not shift its entry to Monday. The funnel's input calculations retain their frozen calendar, including their lookbacks. Weekday special sessions remain in S1 and are a disclosed limitation; their special hours have not been reconstructed.

C5: forward results are “closed until the firewall permits access: no earlier than 2027-06-01 (blueprint amendment 3) and no earlier than the binding evaluation (CLAUDE.md D7), whichever is later. This registration grants no release permission.”

C6: the expanded economics, tail-risk and breakdown measures below are descriptive. None adds a verdict criterion.

“Unexplained” means no explanation detected by these sources and exclusions, not proof that no explanation existed. The comparison is observational. Historical findings establish neither causation, T4 calibration, live readiness nor permission to change risk limits.

## 2. Periods and prior exposure

Development: 2019-10-01 through 2024-12-31. Catalogue events begin in 2020 in practice, with limited early peer history. Replication: calendar 2025, evaluated once after development implementation and results are locked, even if development fails. No 2026 evaluation sample.

Apply boundaries separately by horizon. Purge development trades and censor 2025 trades by their scheduled exit date. If an actual delayed exit would require a price from the next period, censor that trade and count it. Never read the next period's price. Boundary-censored trades have no return and are excluded from the missing-outcome denominator.

2025 is PARTIALLY EXPOSED: forensic research, shadow replays and follow-ups, and T1 have already used overlapping events/stock-days and outcomes. A/B/C sourcing exposed 2025 inputs, including market/peer and funnel counts, without subsequent outcomes. The former proposed sample floors were set after seeing 2025 counts and are withdrawn, not represented as pre-exposure choices. The replacement is T1's floor specified below.

GSM exposure only: the existing 2025 diagnostic recorded 94 entry checks across 23 stocks, one stock with a G5 pass, 34 BE/BZ-only checks, and 75 UNKNOWN checks, including 39 without a bar and two without sufficient EQ history. These are previously reported inputs, not new calculations, not evidence that GSM can be ignored safely, and not the basis for the research-population decision.

Exposure sources: docs/desk/abc_sourcing_check.md section 6, docs/desk/abc_followup_check.md, the locked T1 reports and the accompanying trading research registry. As T1 states:

> not a previously unseen outcome sample for these questions. Decisive out-of-sample
> evidence for any trading model must come from forward data, under a separately
> registered evaluation after the firewall permits access.

No new counts or outcomes are supplied in this revision.

## 3. Inputs, timing and provenance

Decision time: 18:00 IST on D. ASSUMPTION: D's full EQ bhavcopy is available at 18:00. This expressly extends T1 addendum 3(d)'s end-of-session assumption from the stock's own bar to every bar used in market and peer moves. It is not verified publication-time evidence.

At implementation, report from the nightly's own logs, metadata only, how often D's bhavcopy was in by 18:00. Do not inspect forward outcome payloads for that audit; log absence is not proof of public unavailability.

Timestamped filings after the cutoff cannot change the decision. Stored announcement timestamps are assumed IST; first-publication semantics remain unverified. Date-only evidence retains the funnel convention: available at 09:15 on the next observed EQ session. The explicit EQ-bar and dated-ISIN assumptions above are exceptions. T1 index/VIX inputs for descriptive market state stay on D−1.

Freeze implementation commit, source-file manifest and hashes, rulebook/cost hashes, category map, both calendars, timing and missing-data rules before S1 outcome access. Record event date, knowledge date, publication timestamp, recorded_at and provenance. Research timing is separate from the P8-084 recorded-row replay clock. No source download, repaired backfill, inferred SEBI-symbol link or dividend-parser change is authorised here.

## 4. Population and comparisons

Start with stored catalogue events having negative return_1d. Do not recompute catalogue direction or reconstruct the catalogue. Inherit repaired item 2 market/peer definitions and the nine-step funnel from scripts/abc_followup_counts.py at the counting baseline, subject to the explicit S1 changes here.

Settings: 18:00 on D; filing window from midnight on the fifth preceding observed EQ session through the cutoff; market-adjusted peer correlations over the preceding 250 sessions, with at least 200 paired observations. All historical memberships obey the dated-snapshot rule at the relevant date.

| Step | Exclude from the unexplained group |
|---|---|
| 1 | Equal-weight market move on D below −2%. |
| 2 | Same-symbol Material filing in the window, using the frozen category map. |
| 3 | Same-symbol Unclear filing in the window. |
| 4 | Same-symbol linked SEBI order in the frozen funnel window. |
| 5 | No filing of any category in the preceding 90 calendar days, excluding D. |
| 6 | D within 13 July–16 December 2022, inclusive. |
| 7 | Parsed likely dividend record/book-closure day or preceding EQ session, as the frozen input calculation flags it. |
| 8 | Peers explain at least half of the market-adjusted drop, or peer status is UNKNOWN. |
| 9 | Existing point-in-time G3 structure failure or G5 liquidity failure. Retain the screening check and recheck G5 at S0's limit-sized quantity, using decision-time inputs only. |

Also exclude unstable peer ratios (absolute market-adjusted move below 1%), unknown G3/G5, active ASM on D, ineligible/unknown dated identity, weekend decision events and events whose next observed session is a weekend. Count each exclusion and overlaps. GSM supplies no research selection filter.

Explained comparison: down events satisfying every other condition but with a Material filing in the window. Step 2 is reversed and step 3 waived for this group: an accompanying Unclear filing does not exclude a Material event. All other conditions apply symmetrically.

One open position per stock, applied separately within each group and each horizon experiment. Skip events while that group's position remains open, including an exit delayed within the period. No cross-group portfolio constraint. No portfolio budget affects the verdict; a simulation at S0's portfolio limits may be reported descriptively.

Retain A/B/C counts in their original reports as the counting record. They are not valid-trade counts and do not demonstrate that S1 meets any minimum. Revised population/exclusion counts await separately authorised implementation; fills, exit availability and returns await evaluation.

## 5. Execution, sizing, costs and data gaps

S0's registry entry-mechanics quote (desk/automation/registry.py):

> Limit = decision price + 0.5 x ATR20 on the next global session only: fill at the open if at or below the limit, else at the limit if the session low reaches it, else NO_FILL. Missing or unusable bars are a fill FAILURE. Pending entries are cancelled if an entry-blocking kill switch is active.

Historical S1 reconstructs no operational kill switch or other live operational state; none is treated as active in the past. Live and paper books apply their own switches. This limits the historical reconstruction; the S0 quotation above does not import live operational state into S1.

Apply that next-session limit model on S1's calendar. Cancel if unfilled on D+1. Cap the buy limit at the next-session upper band when known at decision time. A limit above a band not known then is a rejected order, a normal no-fill, under S0's locked-circuit rules.

Quantity uses S0's current V2_SIZING definition, retained by v3. Verbatim operative excerpts from the registry, omitting its historical result parenthesis:

> At acceptance, re-size with the rulebook sizing function (cost-inclusive, G6 fix 7801550) at the entry LIMIT price, decision price + 0.5 x ATR20, instead of the screening quantity sized at the decision price

> Every decision-time cap is re-checked at the limit price; zero shares at the limit is a logged rejection. Never above the screening quantity and never resized after acceptance.

Recheck G5 at that accepted quantity using decision-time information. Quantity remains frozen after acceptance; share-basis changes for corporate actions are not discretionary resizing.

Stop: frozen plan stop = decision close − 2 × decision ATR20, adjusted for corporate actions. S0's registry says:

> Frozen plan stop, adjusted for corporate actions with the store adjustment factor. Monitoring starts the session after the fill: open at or below the stop fills at the open, else a low at or below the stop fills at the stop.

There is no stop on the fill session. At a later session, an open at/below the stop exits at the open; otherwise a low at/below it exits at the stop, subject to circuit restrictions.

Time exit: open of D+1+h in S1's calendar. Thus h=1 exits at D+2 open and h=3 at D+4 open. If stop and time exit coincide at the same open, label STOP. A low later on the time-exit day cannot retrospectively turn an open exit into a stop.

No target in the trading rule. Descriptively record which barrier, fill ± 2 × decision ATR20, was touched first: upper first, STOP first, or neither (TIMEOUT). Leave out the fill session for both barriers, because its high can come before the fill. Observe the high and low of every full S1-calendar session after the fill session and before the scheduled exit session, then the scheduled exit session's open. The label always ends at the scheduled horizon, whatever the trade's actual exit; delays do not extend it. If one observation touches both barriers, count STOP first. This label cannot trigger an exit, change the return or affect the verdict.

Locked circuits use S0's rules: no buy at an all-day upper lock; no sell at an all-day lower lock; assume a flat bar locked when band or tick size is unknown. A blocked exit retries at the next session's open, subject to the same restriction. Delays can extend the scheduled holding horizon; disclose them and apply the boundary-censoring rule.

Costs: freeze config/COSTS_ACTIVE and costs_india_delivery_v1.yaml. Apply existing delivery charges at the frozen quantity. These are configured research rates, not verified historical broker schedules; GST retains TO_VERIFY status.

Documented slippage model: no slippage on limit entries. On market-type exits, including stops and time exits, apply the config's slippage bucket for the stock's liquidity tier. The inspected config supplies rates but no mapping from stocks to tiers, so the specified fallback is 0.15% on every exit, with 0.40% as a one-change sensitivity. Slippage is adverse to the sell price and included once in net returns; do not silently treat the existing fee routine as applying it. This is an ASSUMPTION and satisfies the blueprint requirement to document the model.

Data gaps: no bar on the fill session is a fill FAILURE, not a normal untouched-limit no-fill. A session with no bar inside a hold is skipped. Checks resume at the next available bar, open first, so a gap-through-stop is caught there. No bar on an exit session carries that exit to the next available open, subject to circuits and period boundaries. If an exit cannot execute within 10 S1-calendar sessions after its scheduled exit session because the stock has no bars, the outcome is MISSING and counted. No later price is used. Locked circuits keep retrying as S0 does, subject to the period boundary, because those losses are real and must stay in. An unadjustable corporate action during the hold makes the outcome MISSING. A MISSING outcome closes the position for the one-position rule at the session it became missing: the cap session or the action's ex-date. Dividends inside the hold are not credited. Count every case, including dividend-bearing holds, and report overlapping reasons separately. Never replace a missing return with zero.

### Addendum 1 (20 October 2026): blocked exits

Approved by the user before any S1 outcome was seen. Once a stop or time exit
triggers and selling is blocked by a lock, the exit stays pending and executes at
the open of the next S1-calendar session not locked for selling, subject to missing
bars and the period boundary. S1 does not clear or re-arm a triggered stop as S0's
current implementation does. "As S0 does" means only that S1 keeps trying through
locks, subject to the period boundary. S0's code remains unchanged. This addendum
changes no other rule.

## 6. Outcomes and descriptive measures

Primary outcome: net percentage return per valid filled trade after execution, fees and slippage, divided by invested entry value. Trades have equal weight in group means. A hit is net return strictly above zero; exactly zero is not a hit.

Report mean, median, hit rate, stop-out rate and missing-outcome rate, plus:

- Profit factor and payoff ratio use trade net percentage returns per group, horizon and period. Profit factor = sum of gains / absolute sum of losses. Payoff ratio = mean gain / absolute mean loss. With no losses or no gains, report "undefined" with the counts, never infinity or zero.
- Benchmark-relative return: net return minus the equal-weight return of item 2's market universe. Members are fixed at the fill session from the dated-identity market universe known at D, with no rebalancing. Each member's open-to-open return runs from the fill session's open to the open of the trade's actual exit session, adjusted for corporate actions as in item 2. Members without an open at either end are left out of that trade's benchmark and counted. For an intraday stop exit, the benchmark ends at that session's open; disclose the mismatch.
- Maximum adverse excursion is the lowest price the position was exposed to: the minimum of the fill session's low, the low of every full S1-calendar session after the fill session and before the exit session, and the exit price. Measure it against the fill price; it is zero if none is below the fill. The fill session's low always comes at or after the fill: an open fill is the session's first trade, and a limit fill below the open is touched before the low is reached. It therefore counts even though the stop is not monitored that day. Never use a price after the exit. On a stop-exit day use the exit price, not that day's low. For h=1 with a time exit, MAE uses the fill session's low and D+2's open.
- Stop-out rate: stop exits, including gap-through opens, over valid filled trades with a realised outcome.
- Severe loss: a net return below −1.5 times the planned net loss. Planned net loss = (fill − plan stop) / fill, plus round-trip costs at the frozen quantity, plus the 0.15% exit slippage. A trade filled at or below its plan stop is flagged, counted and left out of this measure only.
- Counts of gap-through-stop exits, circuit-delayed exits, no-fills and fill failures.
- Breakdowns by year, turnover band, drop-size tercile and T1's market state on D. Drop size is the catalogue's absolute 60-session z-score on D. Fit tercile boundaries once on the pooled development population of both groups (events, before fills), using type-7 quantiles with ties to the upper band, then freeze them for 2025. T1 market state means the V1, V2 and V3 states exactly as T1 defines them, with T1's timing.
- The descriptive barrier-path label and data-gap/boundary counts.

These additional measures and breakdowns never alter the verdict.

Turnover bands retain the funnel calculation: decision-date cross-sectional quintiles of trailing 60-observation average close × traded quantity, type-7 boundaries, ties to the upper band, UNKNOWN without sufficient history. Apply C1 to this universe too; the original all-EQ/fund-inclusive counting record remains unchanged. Use only decision-time inputs and the frozen input calendar.

Shared inputs: event selection, ATR, market/peer measures and returns share prices and anchors. Filing coverage and liquidity filters select a non-random population. Differences between explained and unexplained groups do not identify a causal value of the label.

## 7. Bootstrap, tests and minimums

Use T1's base bootstrap: 2,000 draws, seed 20261001, moving blocks of 20 consecutive weekday sessions. Draw starts uniformly from valid 20-session blocks, with replacement; concatenate ceil(T/20) blocks and truncate to T dates. Carry complete decision-date clusters, both groups, multiplicities and missingness. Empty dates stay; purged dates are excluded. No cross-period blocks or individual-stock resampling. Apply each horizon's boundary calendar and pair its groups on the same draws.

Use Hyndman–Fan type-7 percentiles. The family comprises four interval tests: (a) and (b), each at h=1 and h=3. Bonferroni-adjusted two-sided intervals are 98.75%, with endpoints 0.625% and 99.375%. Report 95% intervals descriptively. Do not shrink the family if a horizon or comparison is unavailable. Apply the same fixed family in development and replication.

| Test | Criterion, separately at each horizon |
|---|---|
| (a) Strategy | Unexplained mean net return ≥ +0.25% per trade and family-adjusted interval strictly above zero. |
| (b) Label | Unexplained minus explained mean net return ≥ +0.25 percentage points and family-adjusted interval strictly above zero. |
| (c) Consistency | Development unexplained mean strictly positive in at least three of 2021, 2022, 2023 and 2024. |

Minimums: at least 100 valid trades and 30 distinct decision dates per group, horizon and period. Missing outcomes must be at most 5%; denominator is filled trades excluding boundary-censored trades. No-fills/fill failures are not filled trades.

A draw is usable for a test only if it meets that test's sample minimums. Each test needs at least 1,900 usable draws, otherwise it is INCONCLUSIVE. Test (a) requires only the unexplained group; (b) requires both. An inadequate explained group must not invalidate (a). Count distinct original decision dates, not repeated bootstrap copies as new dates.

For development consistency, a year with fewer than 30 valid trades counts as not positive. In 2025, each half-year needs at least 30 valid unexplained trades; otherwise replication consistency is INCONCLUSIVE. With sufficient trades, both January–June and July–December means must be strictly positive. Exactly zero is not positive.

## 8. Verdicts and replication

At each horizon, S1 PASS requires (a) and (c), with its applicable information requirements satisfied. With adequate information, failure of either means FAIL. Failure of an applicable information minimum means INCONCLUSIVE, not evidence of no effect.

Report (b) separately as LABEL SHOWN or NOT SHOWN when evaluable, otherwise INCONCLUSIVE. It does not decide S1 PASS. If not shown, state: “The rebound is not shown to depend on the drop being unexplained.”

Evaluate 2025 once, regardless of development verdict. Apply the same magnitude, interval, information and half-year consistency requirements. Report replication success, not met or INCONCLUSIVE at each horizon, and the separate label result. Do not select a winning horizon and claim blanket S1 success.

## 9. Sensitivities

One change at a time from the primary for each horizon, with the same execution and costs except the expressly specified slippage sensitivity. Sensitivities never determine the verdict.

Retain 09:00 next-session and 23:59 on D filing cutoffs; one-/ten-session filing lookbacks; 120-session minimum peer overlap; inclusion of unstable-ratio events; omission of each year's most crowded date, leaving out all tied dates; and exit slippage 0.40% instead of 0.15%.

The former one-/three-session sensitivities are now the registered horizons. The old next-open-entry sensitivity is superseded by the same-execution instruction and is not part of the revised sensitivity set.

## 10. Reporting, limitations and implementation order

Required future reporting: provenance and hashes; periods and exposure; identity/calendar exclusions; group and date counts; G3/G5 and other exclusion reasons; skipped positions; fills, no-fills and failures; scheduled boundary removals and delayed-exit censoring; missing outcomes and denominator; dividends not credited; all descriptive measures and their coverage; all tests, intervals, usable-draw counts/reasons, consistency cells, sensitivities and per-horizon verdict checks.

Limitations include inherited catalogue identity stitching, assumed snapshot/bhavcopy availability, unverified announcement publication semantics, frozen funnel calendar versus S1 calendar, weekday special sessions, absent historical GSM, no dividend credit, configured rather than historical costs, daily-bar path ambiguity and partially exposed 2025. Weekend sessions inside a hold are not observed for stops, MAE or the path label. Historical S1 reconstructs no operational kill switch or other live operational state; live and paper books apply their own switches.

This text is registered. Implementation and evaluation remain separate tasks requiring separate authorisation. After separate authorisation: freeze new funnel/runner and adversarial checks; publish input-only provenance/coverage and metadata timing audit; rehearse with seeded random labels and real outcome readers blocked; lock one development evaluation; evaluate 2025 once and lock it. A crash or defect stops work; no autonomous repair-and-rerun. Never tune after seeing S1 outcomes; retain failures in the registry.

If development and replication pass, the next step is a separately registered forward paper book, not activation. Its results are closed until the firewall permits access: no earlier than 2027-06-01 (blueprint amendment 3) and no earlier than the binding evaluation (CLAUDE.md D7), whichever is later. This registration grants no release permission.
