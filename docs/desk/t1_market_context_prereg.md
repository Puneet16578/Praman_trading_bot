# T1 market and sector context preregistration

Registered 2026-10-04. DOCUMENTS ONLY. No T1 feature computation, fitting,
outcome comparison or implementation was performed for this registration.
The user reviews this protocol before a later implementation session.
Authority: CLAUDE.md, DESIGN.md constitution, TRADING_BLUEPRINT.md T1 and its
Praman amendments. Frozen forensic protocols/pipeline remain unchanged.

## Role and limits

T1 displays market/sector context and supplies deterministic risk-limit inputs.
It never determines LONG/SHORT direction, ranks trade recommendations, invents
probabilities or overrides an existing veto. Historical frequencies are sourced
FACTs; any model estimate remains display-only UNVALIDATED until T4. A finding
here does not establish profitability, calibration, readiness or permission to
change the active rulebook. No live sizing, gates or paper conventions change.
After separate policy approval, adverse market/breadth states may only tighten
existing per-trade/open-risk ceilings, never enlarge them; unknown context cannot
justify relaxation. The numerical risk-limit mapping requires a separately
approved rulebook proposal, not an outcome-selected parameter in this study.
This protocol tests associations, not returns of such a future policy.

## Periods and prior exposure

Development: 2019-10-01 through 2024-12-31. Calendar 2025 is reserved as the
trading hold-out under the blueprint: no feature, label, threshold, variant,
sector proxy or strategy selection using it. Lock implementation, coverage rules
and development results before a single 2025 evaluation. No 2026 sample is used.
Nothing on or after 2026-09-16 may be evaluated before 2027-06-01; use the shared
firewall before loading event outcomes. Purge development decisions whose 20th
forward global session enters 2025; count exclusions. 2025 decisions whose 20th
session enters 2026 are censored, never silently counted non-adverse.

**Exposure disclosure (clarified 2026-10-05):** Calendar 2025 is "partially exposed:
aggregate adverse-move rates were viewed in the shadow studies; no trading model
has been fitted or selected on it." It stays untouched for NEW T1 selection from
this registration onward. Results must disclose this partial exposure; 2025 is
not a previously unseen outcome sample for these questions. Decisive out-of-sample
evidence for any trading model must come from forward data, under a separately
registered evaluation after the firewall permits access. This clarification
changes no period, variant, metric, threshold or success criterion.

## Inputs, provenance, timing and availability

Every observation records series/security identity, event_date, knowledge_date,
publication timestamp where available, recorded_at, source and raw-content hash.
Select the latest vintage with knowledge_date <= decision cutoff; intraday
publication timestamps must also precede that cutoff. Restatements append; never
replace older values. Use only actions known by the decision to adjust inputs.
A final series downloaded today is not automatically a historical vintage.

Decisions are end-of-session, AFTER publication of inputs actually used; a close
that was not yet published is unavailable for that decision. When only a proven
publication DATE exists, make the value available at the next market session,
not at an invented same-day time. If even the publication date cannot be proven,
knowledge begins at first observed retrieval and earlier historical values remain
UNKNOWN. No publication-hour or archive-coverage assumption is treated as verified.

| Input | Planned source and computation | Publication timing / knowledge rule | History availability at registration |
|---|---|---|---|
| NIFTY 50 price-index close | Official NSE/NSE Indices dated index-close reports and historical archive | End-of-session report, actual release timestamp/date under the rule above | Not ingested as an official bitemporal index; archive range/vintages NOT VERIFIED. Require 2019-2025 coverage plus warm-up before analysis |
| Broad index: NIFTY 500 price-index close | Same official publisher; this is the FIXED broad benchmark, no substitution chosen from results | Same release rule | Not ingested; historical publication evidence/coverage NOT VERIFIED. Missing coverage blocks corresponding tests |
| India VIX close | Official NSE India VIX daily historical reports | Post-session published value; no same-day availability assumed without evidence | Not ingested; required 2019-2025 and 252-session warm-up availability NOT VERIFIED |
| Sector classification and sector return | Dated NSE industry/sector classification and constituent/change notices. Sector = publisher's sector-level classification, version and exact code retained. Equal-weight basket of other eligible stocks in that dated sector | Membership usable only after both effective and publication dates; daily basket known after all used prices publish | Historical point-in-time membership MAY NOT BE RECONSTRUCTABLE. Current classifications must never be backfilled. Missing membership => UNKNOWN and no sector test for that row |
| Stock OHLC and identity | Existing NSE bhavcopy, dated equity ISIN/identity evidence and corporate-action store | Existing event/knowledge dates, actual public availability; no later-known action in an earlier input | Correctly dated bhavcopy starts 2019-10-01. No earlier stock history; per-symbol gaps, suspensions, identity vintages and unadjustable windows remain exclusions |
| Advance/decline breadth | Equal-weight counts of eligible equities with positive/negative adjusted close-to-close return; flat counted separately; net breadth = (advances-declines)/valid count | Available only after the contributing reports publish | Derived from store, not computed now; starts only where adjacent global-session prices/identity are available |
| Shares above 50-/200-session averages | Fraction with adjusted close strictly above arithmetic mean of last 50/200 global-session closes including the decision close; own denominator for each horizon | Same input publication cutoff | Derived from store; 49/199 prior valid global sessions needed; no shorter-window replacement or stale-price filling |
| New highs/lows | Close strictly above/below previous 252 global-session adjusted closes, excluding today's close; rates over eligible full-window stocks | Same cutoff, prior closes adjusted using actions known now | Derived; first 252 prior stock sessions are warm-up. Never call a short-history maximum a 52-week high |
| Cross-sectional dispersion | Population standard deviation of same-session adjusted one-day returns across eligible equities (equal weights) | After contributing reports publish | Derived from store; valid constituent count and exclusions recorded per date |
| Stock relative to market, 1/5/20/60 sessions | Stock cumulative adjusted simple return MINUS NIFTY 50 cumulative simple return over identical global-session endpoints; percentage-point difference | All prices/actions/index observations visible at decision | Derived only over complete intervals; official benchmark unavailable until above sourcing is proven |
| Stock relative to sector, 1/5/20/60 sessions | Stock cumulative return minus compounded equal-weight daily return of its point-in-time sector peers, excluding the focal stock on every day | Dated membership and prices must be known on each basket date; require at least five other valid peers per day | UNKNOWN where historical membership cannot be proven; no present-day proxy in primary analysis |
| Decision volatility | ATR20 / decision close * 100, arithmetic true range over 20 sessions using 21 visible adjusted OHLC bars | Decision information only | Derived from store; invalid/nonpositive prices or unavailable adjustment => UNKNOWN |

The existing market_index.csv is an equal-weight research proxy, NOT NIFTY 50 or
NIFTY 500. Its builder uses FAR_FUTURE_AS_OF; it cannot be reused as point-in-time
T1 input. No new source was fetched or archive verified for T1 in this session.
Before outcome access, publish coverage/missingness and provenance by input/year,
including first/last usable date and every unknown publication/membership case.
Do not substitute a different source/benchmark after seeing outcome comparisons.

## Population and fixed feature definitions

Primary population: all eligible equity stock-days in the existing price store,
not only anomaly-catalogue events or SCREEN_PASS decisions. Equity status and
identity must be known at that date; exclude fund units, not delisted companies.
Retain historical listings and suspended identities. A stock needs a valid
current EQ close and 21-session ATR window; expose exclusions by cause. Corporate
identity stitching must use dated mappings, not the current universe. A stock
without a price on a global session has missing input; never forward-fill it into
breadth or the study. Evaluate all stocks equally, not by market capitalization.

Breadth denominators use all such contemporaneous equities with the particular
input window, excluding unavailable/unadjustable bars and identities. Report
numerators and denominators, plus fractions of the base universe excluded.
Sector baskets rebalance equally each day using that day's known membership.
A stock changing sector within a relative-return window has UNKNOWN sector
relative strength for that window; no retroactive reclassification.

Development volatility quintiles: pooled eligible development stock-days with
valid ATR percentage, including rows with missing outcomes. NumPy linear 20/40/60/80
percentiles; freeze for 2025 and bootstrap draws. Ties go to the upper quintile.
These NEW development-only boundaries are distinct from the already published
2019-2025 assessment-context boundaries: using those would import 2025 inputs.

## Four fixed variants; three directional predictions

Exactly FOUR variants including baseline. No threshold sweep, alternate horizon,
feature subset search, fitted prediction model or post-result sector proxy.

- V0: volatility-quintile baseline. Report adverse20 frequency in each quintile.
- V1: adverse market regime if NIFTY 500 close is below its inclusive 200-session
  arithmetic average OR India VIX close is above its previous 252-session linear
  80th percentile (exclude current VIX from that threshold). Require both inputs
  available even when one condition is true. Prediction: adverse regime has a
  higher adverse20 rate within volatility quintiles.
- V2: weak breadth if the share above the 50-session average is below 40% AND net
  advance/decline breadth is negative. Prediction: weak breadth has a higher
  adverse20 rate within volatility quintiles.
- V3: negative 20-session stock-minus-sector return versus zero or positive.
  Prediction: negative relative strength has a higher adverse20 rate after
  volatility control. Twenty sessions is fixed; the requested 1/5/60-session
  relative strengths are recorded/displayed, not extra hypothesis tests.

The 200-session breadth, new highs/lows, dispersion, NIFTY 50 trend, and remaining
relative-return horizons are descriptive context only. Display their coverage and
input distributions without running additional outcome contrasts in this study.
No composite V1+V2+V3 policy is tested or selected.

## Outcome, metrics and uncertainty

Y=1 if any action-adjusted low in the next 20 GLOBAL market sessions is at or below
80% of decision close. Use the existing adverse20 label definition on a common
share basis; all 20 bars required for both outcomes. Structural breaks and missing
paths are unavailable, not zero. No fills, P&L, execution simulation, forensic
label changes or new trading labels are part of T1.

ATR, breadth, relative returns and adverse20 all share price inputs and the
current-price anchor. Quintiles reduce broad volatility imbalance, but do not
remove mechanical coupling or prove causation. VIX and index context also share
market shocks with outcomes. These are conditional historical associations.

For each variant, period, state and quintile report candidates, valid/missing
outcomes, date clusters, adverse20 count/rate and risk difference (adverse minus
other). Standardized primary difference = sum of quintile differences weighted
by the development baseline candidate shares, fixed for both periods and all draws.
If either state lacks valid outcomes in a positive-weight quintile, standardized
comparison is unavailable; never renormalize away that quintile. Compare V1-V3 to
V0 on matched available rows and show those rows' baseline rate and coverage.

Bootstrap: 2,000 replicates, seed 20261001, resampling complete market-date clusters
in MOVING BLOCKS of 20 consecutive global sessions to address overlapping outcomes.
Choose block starts uniformly among all T-19 valid starts, with replacement;
concatenate ceil(T/20) blocks and truncate to T dates. Carry every stock-day on each
sampled date, including multiplicities and missingness. Reuse draws for all paired
contrasts within a period. No cross-period blocks or individual-stock resampling.
Quintile boundaries and development weights remain fixed. Report percentile 95%
intervals descriptively and 98.333333% two-sided intervals (Bonferroni family of
THREE primary contrasts) for the fixed success criteria. Report usable draws;
require at least 1,900 usable draws for a decision. Report risk ratios only as
secondary descriptive measures if both rates are nonzero; no accuracy headline.

## Success criteria and decision discipline

For EACH V1-V3 contrast separately: coverage at least 80% of eligible stock-days
in each evaluated period; at least 100 valid outcomes and 30 distinct dates in
EACH state in EACH quintile; at least 1,900 valid bootstrap draws. Otherwise
INCONCLUSIVE, not a passed test or evidence of no association.

Development success requires standardized risk difference >= 1 percentage point,
its family-adjusted interval strictly above zero, and the predicted positive sign
in at least four of five quintiles. Freeze all code/results, then evaluate all
three variants once on 2025, even development failures. A 2025 replication success
requires those same magnitude, interval, consistency and coverage criteria.
Report each result independently; never announce a blanket T1 success because
one selected comparison passes. Failure/reversal/null/missing results are published.
Because of prior 2025 exposure, even replication success is not independent proof
of new trading edge and cannot activate risk limits or satisfy T4/readiness.

No data-dependent threshold adjustment, expanded variant family or repeated
hold-out peeking. Any correctness repair requires a dated committed addendum,
old/new impact and an explicit exposure record before a rerun. Implementation
must test knowledge-date guards, action adjustments, membership changes, missing
bars, warm-up, bootstrap multiplicities and firewall before any outcome analysis.
Publish immutable input hashes, code/preregistration commits, coverage and full
results whatever they show. Implementation awaits user review in a later session.
