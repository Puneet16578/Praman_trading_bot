# Follow-up 3 review: size against the limit price

Dated 2026-10-04. Interpretation of `shadow_replay_followup3_results.md` / `.json`, produced by
`python -u scripts/desk_shadow_followup3.py` at `bc46648` from the preregistration `b2df2a2`
(7 seconds, frozen artifacts only, no database access, no outcomes computed). This document
proposes; it applies nothing. The rulebook, the strategy registry and both paper conventions are
unchanged.

## Provenance checked

Corrected replay raw SHA-256 `9a71fcf3…` and follow-up 2 execution evidence `16b6d228…` match
their recorded provenance; all seven source hashes match the committed files; the preregistration
is byte-identical to `b2df2a2`. Before measuring anything, the runner reproduced every one of the
52,912 corrected quantities with the screening sizing function (parity), confirmed limit sizing
never exceeded decision sizing, and confirmed every decision-time cap still holds with the
smaller quantities.

## Verdict: PASS

| Preregistered criterion | Primary 2019-2025 | Descriptive 2026 |
|---|---|---|
| P1: per-trade breaches at the fill | **0** of 44,442 fills | **0** of 6,972 fills |
| P2: fill rate >= 60% | **97.10%** [96.78, 97.37] | 97.62% |

## What it costs (primary; 2026 agrees)

| | Limit-sized | Frozen (follow-up 2) |
|---|---|---|
| Quantity ratio q_L / q, mean | 0.907 [0.904, 0.910] | 1 |
| Quantity ratio, median | 0.943 [0.933, 0.952] | 1 |
| Quantity ratio p10 / p25 / p75 / p90 | 0.801 / 0.804 / 0.984 / 1.000 | |
| Passes with a smaller position | 89.95% | |
| Abstentions (zero shares at the limit) | 1 of 45,770 | |
| Fill rate | 97.10% | 97.10% (difference −0.002 pp) |
| Planned loss at decision, median % of cap | 79.2% | 84.2% |
| Planned loss at the fill, median % of cap | 78.6% | 86.1% |
| Planned loss at the fill, p90 % of cap | 95.8% | 113.2% |

Reading it plainly:

1. **The per-trade cap now holds at the fill by construction, and the data confirm it: zero
   breaches in 51,414 fills across both periods**, against 27.47% (primary) of follow-up 2's
   frozen-size fills.
2. **The cost is modest: positions are on average about 9% smaller.** The reduction is bimodal,
   for a reason found in the tests before the run and visible here. Where the per-trade budget
   binds (wide stops, ATR20 above roughly 5% of price; the bottom quartile of ratios), positions
   shrink by about 20%, the arithmetic 2.0 / 2.5 ATR stated in the preregistration. Where the
   10% per-stock position cap binds instead (tighter ATR20), they shrink only by the decision /
   limit price ratio, about 2%.
3. **Fills are unaffected**, apart from one abstention, because the limit rule decides fills and
   quantity does not.
4. Budget use at the fill falls from a median of 86% to 79% of the cap, and its worst decile from
   113% to 96%: the risk actually taken becomes both lower and bounded.

Limits of the evidence: daily bars cannot establish tradability or intraday order; follow-up 2's
execution conventions (raw next-session prices, EQ/BE/BZ priority) are inherited unchanged;
other caps at the fill (open-risk stress, ADV) were not part of this registered question.

## Proposals (not applied; each needs the user's approval)

**1. Strategy 0 v2.** Identical to v1 except sizing: at acceptance, size each candidate with the
rulebook sizing function at its limit price (decision price + 0.5 × ATR20) instead of using the
screening quantity sized at the decision price, then re-check every decision-time cap (they can
only loosen). Its stress loss scales down with the quantity, so the open-risk budget admits
slightly more concurrent positions. Registered as a new version; v1 stays in the registry. Note on
timing: Strategy 0 v1 has not yet been registered in production (no nightly run since Part B), so
if this is approved before the first nightly run, the burn-in could start directly on v2 and v1
would be registered only as a superseded definition, never run.

**2. Matching manual-convention change.** In `desk assess`, size manual decisions against the
order's limit price (thesis `planned_entry` + 0.5 × ATR20 at the decision date) instead of
`planned_entry`, so that G6's per-trade check holds for any limit fill. The limit order itself is
unchanged. It touches G6's sizing input for non-screening decisions, so it would be recorded in
the DESIGN.md changelog and the paper-trading guide when applied.

If both are applied, P8-043 (at-fill per-trade breaches) can be closed for both books with this
result as the evidence. Until then it stays open.
