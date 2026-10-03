# Follow-up interpretation and checks

Run on 2026-10-04. Protocol committed first as `bbd5268`; tested implementation
committed as `d6b7a0b` before running either analysis. Full results, denominators,
intervals and source hashes: [report](shadow_replay_followup_results.md) and
[JSON](shadow_replay_followup_results.json). No parameter or gate was tuned.

## What limits the conclusion

**The original fill-breach rate includes violations already present at the
decision.** P8-038 records 12,693 primary and 1,958 descriptive-2026 filled passes
whose planned loss including costs already exceeded the per-trade budget.
Original sizing uses the gross entry-stop distance; G6 does not enforce the
per-trade bound including costs. A synthetic active-config example yields
Rs 5,121.39357 of planned loss against a Rs 5,000 budget while G6 returns PASS.
The registered 90% variant enforces all six caps including costs; its benefit
therefore cannot be attributed solely to adding 10% headroom to an otherwise
correct original decision. Active sizing remains unchanged; P8-038 is open.

All original filled passes lack a known locked-circuit component. That original
coverage gap persists. Current identity mappings, event-bar inclusion in ATR,
raw-opening execution and the empty hypothetical portfolio are unchanged.
The 2026 sample remains descriptive, not an independent hold-out.

## A. Volatility control

Primary all-candidate FAIL-minus-PASS adverse-move gap:

| Comparison | Gap, percentage points | 95% date-cluster interval |
|---|---:|---:|
| Unstratified, same valid-volatility sample | +6.01 | +5.11 to +6.89 |
| Standardized across volatility quintiles | +0.74 | -0.28 to +1.72 |
| Attenuation | +5.27 | +4.55 to +6.09 |

Each primary quintile has a smaller point gap than the unstratified estimate:
Q1 +1.48, Q2 +0.77, Q3 +1.69, Q4 +1.28, Q5 -1.51 percentage points. Q1 and Q3
retain positive descriptive intervals; Q5 reverses direction with an interval
crossing zero. Filled-only sensitivity is similar: standardized gap +0.76 points
(-0.27 to +1.74). Missing decision volatility excludes 136 FAIL candidates, all
of which also lacked the original adverse20 outcome; no PASS control is missing.

These findings support the narrowing prediction and are consistent with the
gates acting mainly as a volatility filter for the aggregate comparison. They
do not demonstrate a uniformly zero residual effect: some strata retain a gap,
the standardized interval allows a modest positive difference, broad quintiles
leave residual confounding, and there is no multiplicity-adjusted discovery claim.

Descriptive 2026: +5.15 points unstratified becomes +1.46 (-0.30 to +3.21).
Thirty FAIL candidates lack the control and original outcome. All boundaries
come from the primary decision inputs and were reused unchanged.

## B. Cap sizes and fixed 90% variant

Primary any-cap breaches fall from 25,105/45,700 (54.93%) to 7,055/45,694 (15.44%).
Six original fills become zero-share abstentions. On the common executed sample,
the rate difference is -39.50 percentage points (95% interval -40.43 to -38.46).
There are no excluded unknown input records.

Sizes below are percent **over the breached cap**, conditional on breaching it:

| Cap | Original breaches | Original median / p90 excess | Variant breaches | Variant median / p90 excess |
|---|---:|---:|---:|---:|
| Per-trade planned risk | 15,080 | 11.63% / 40.71% | 7,055 | 10.15% / 41.31% |
| Open-risk stress budget | 3 | 0.22% / 4.39% | 0 | unavailable |
| Per-stock capital | 16,097 | 0.85% / 3.20% | 61 | 2.20% / 7.08% |
| Per-sector capital | 0 | unavailable | 0 | unavailable |
| Order / ADV | 128 | 1.30% / 5.57% | 2 | 1.38% / 1.44% |
| Stressed exit days | 0 | unavailable | 0 | unavailable |

The main report includes confidence intervals, small-sample warnings and
zero-inclusive sizes for each statistic. Counts overlap. Conditional size can
rise when a variant removes small breaches and leaves a few large ones; it must
not be confused with the breach rate or unconditional risk. Open-risk and variant
ADV size estimates are especially sparse. All remaining variant any-cap breaches
include the per-trade limit; 90% headroom does not eliminate them.

Descriptive 2026: 3,232/7,131 (45.32%) becomes 913/7,131 (12.80%), no abstentions.
The paired difference is -32.52 points (-34.82 to -30.32).

## Verification

- Frozen replay hash, original source hashes, event identities and original
  PASS/FAIL/fill counts verified before the analysis.
- Original fill-breach reasons and any-cap totals reproduced exactly.
- All 52,831 filled PASS variant quantities independently checked against affine
  cap bounds; every positive result fits 90% at the decision, and one more share
  fails a bound unless already at the original quantity.
- All cap counts, rates, conditional and zero-inclusive median/p90 values
  recomputed from the individual records; generated Markdown matches the renderer.
- Independent manual linear quintiles, 40 stratum rates/denominators/date counts,
  and all four standardized gaps agree. Both live-store watermarks are unchanged.
- No durable database is accessed by the analysis runner. Raw replay and original
  results are unchanged. Reproduce: `python -u scripts/desk_shadow_followup.py`.
- Final full suite: 626 tests in 112.249s, OK, Python exit 0. Existing SQLite
  ResourceWarnings remain. P8-036/P8-037 are fixed; P8-038 is explicitly open.
