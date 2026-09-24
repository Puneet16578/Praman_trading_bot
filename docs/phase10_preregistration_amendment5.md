# Phase 10 Pre-registration — Amendment 5

**Dated 2026-09-24. Amends `docs/phase10_preregistration.md` and Amendments 1-4 without editing
any of them, per their own immutability notices.** Amendment 4 is not reopened or edited — it
remains the historical record of what was committed and why, including the claim this amendment
corrects. Amendment 5 is a separate, new document, exactly as every prior correction in this
project's history has been handled.

**No forward outcome exists yet, as of this commit.** Nothing below was found or decided by
looking at a forward outcome — every change here was found by measuring the label's own
statistical properties against historical data, the same discipline every prior amendment in this
series has followed.

## Summary (read this first)

**Amendment 4 asserted, without measuring it, that the redefined (`P8-013`) outcome label's
missingness "isn't correlated with the model's own inputs."** It had only measured OLD-vs-NEW
label AGREEMENT (98.73%, correctly) and the label's own TRAIN-vs-HOLD-OUT rate comparison (0.176pp
gap, correctly) — neither check actually establishes whether the NEW label's own missing events are
a random subset of the population. Measuring that directly (`scripts/phase10_amendment5_
measure.py`) found the claim was **false**: TRAIN's missing rate under `P8-013` was **6.838%** (4.3x
the rate before `P8-013`), and its `cap_band` gradient was a clean, steep monotonic function —
Micro 16.0% down to Mega 1.9%, a **14.1pp spread**, WORSE than the own-session definition's own
0.9pp spread. `P8-013`'s own fix had, on the exact dimension it existed to fix, made things worse.

**Root cause, confirmed directly (`P8-014`): `P8-012`'s series-extension logic only bridged a
PERMANENT move to `BE`/`BZ`, not a TEMPORARY stint that resumes EQ afterward.** 92.37% of the
TRAIN events missing due to the staleness cap had a real `BE`/`BZ` close in the exact window the
old logic never looked at — a surveillance-driven trade-for-trade period, followed by a return to
normal trading, is the ordinary shape for exactly the volatile micro-caps this project's classifier
flags, and the old fix silently excluded them.

**Fixed at the root, verified before adopting.** Prototyped a full per-date bridge (any date the
primary series lacks, filled from an extension series, primary always wins on a shared date)
read-only first, against the exact decision rule set in advance: TRAIN missing rate must fall by
≥1.0pp AND the Micro-minus-Mega gap must narrow. Both passed decisively (missing rate fell 6.42pp
to 0.414% in the prototype; the gap narrowed from 14.1pp to 0.4pp) — **adopted, implemented in the
pinned pipeline code with tests, and re-verified against the real, rebuilt label**: TRAIN missing
rate **1.310%**, HOLD-OUT **0.897%** (gap 0.413pp — still comfortably inside the 2.0pp commit bar
from Amendment 4), Micro-minus-Mega gap **0.214pp** (essentially flat).

**Refit and Phase 8b re-run under the final label**: no coefficient or feature-direction conclusion
changes from Amendment 4. **Missing-data threshold reset to 4.3%** (TRAIN's own final rate, 1.310%,
plus the 3-point margin) — LOWER than even the ORIGINAL pre-registration's 5%, reflecting a label
whose missingness is now both rare and (to the extent checked) not concentrated in any particular
part of the population. Pinned commit updated to `afe3e2bd07abe8b602c4119b916f7696a3c12131`.

**The pre-registration is now FROZEN.** No further amendment is anticipated. A future amendment is
warranted only for a defect discovered before the forward evaluation runs that would make the
evaluation impossible to run at all (e.g., a code or data-availability failure) — not for further
refinement of numbers already measured and settled here.

---

## 1. What was wrong in Amendment 4, precisely

Amendment 4 §4 stated: *"old-vs-new label agreement is 98.73% overall... confirming the
redefinition changes exactly the population it should... not everything indiscriminately"* and
separately *"the new definition's missing-outcome rate is 6.838% (TRAIN) vs. 6.661% (HOLD-OUT) — a
0.176pp gap."* Both of these specific numbers were real and correctly computed. **The error was in
what was concluded from them**: TRAIN-vs-HOLD-OUT closeness shows the label behaves consistently
across time periods; it says nothing about whether, WITHIN either period, the label's missingness
is spread evenly across `cap_band`/`volume_ratio`/other model inputs or concentrated in a subset of
them. That second, different question was never asked before Amendment 4 committed language
implying it had been answered favorably.

## 2. Measured: the selection problem on the `P8-013` label (before this amendment's fix)

`scripts/phase10_amendment5_measure.py`, TRAIN, side by side with the OLD (own-session) definition
for comparison:

| cap_band | `P8-013` (pre-fix) n | missing | rate | OLD (own-session) rate |
|---|---|---|---|---|
| Micro | 12,142 | 1,944 | **16.011%** | 2.092% |
| Small | 12,139 | 1,060 | **8.732%** | 1.837% |
| Mid | 12,138 | 565 | **4.655%** | 1.458% |
| Large | 12,139 | 349 | **2.875%** | 1.359% |
| Mega | 12,136 | 232 | **1.912%** | 1.195% |

**`P8-013` (pre-fix) Micro-minus-Mega gap: 14.099pp. OLD definition's own gap: 0.897pp — the new
label was WORSE on this dimension than the one it replaced.**

```
volume_ratio_high:  LOW 5.035% (n=30,346)     HIGH 8.640% (n=30,348)
delivery_low:       HIGH/NORMAL 7.862% (n=30,794)   LOW 5.783% (n=29,897)
ASM/GSM at event_date:  NOT_FLAGGED 6.440% (n=57,499)   FLAGGED 13.991% (n=3,195)
```

**Surveillance-flagged events were more than twice as likely to lack an outcome** — the exact
population (surveillance-affected micro-caps) this project's classifier most wants to keep, was
being disproportionately excluded by its own outcome label.

**Mechanism check (item 1b):** of 3,672 TRAIN events missing specifically due to the `P8-013`
staleness cap, **92.37%** had a real `BE`/`BZ` close for the same security within the 10-session
staleness window before `target_date` — a close the pre-fix extension logic never looked at.

## 3. The bridge, prototyped and adopted

**Design**: the outcome uses the last available close on or before `target_date`, taken from the
UNION of EQ/BE/BZ rows for the security, with EQ preferred on any date more than one series has a
close (`scripts/phase10_amendment5_bridge_prototype.py`, read-only, no pipeline change, run before
any code was touched).

**Decision rule, applied exactly as specified**: ADOPT if TRAIN missing rate falls by ≥1.0pp AND
the Micro-minus-Mega gap narrows.

```
Prototype result:
  TRAIN missing rate:  6.838% -> 0.414%   (fell 6.42pp -- rule requires >=1.0pp)
  Micro-minus-Mega gap: 14.099pp -> 0.395pp   (narrowed decisively)
  HOLD-OUT missing rate: 0.150%; TRAIN/HOLD-OUT gap: 0.264pp
Both criteria pass decisively -> ADOPT.
```

**Implemented in the pinned pipeline** (`src/signals/event_catalogue.py`'s `build_symbol_history`):
`extend_with_series` now bridges per date across the whole calendar — a `covered_dates` set tracks
which dates the primary series, then each extension series (in the order given), already fills, so
a later series only contributes dates still missing, regardless of whether they fall before,
during, or after the primary series' own range; the primary series always wins on a shared date.
This correctly bridges a temporary `EQ -> BE -> EQ` stint, which the prior "append only after the
primary series' last date" logic could not see.

**Tests**: `ExtendWithSeriesTest` gained `test_temporary_stint_bridged_not_just_the_tail` (an
`EQ -> BE-only-stint -> EQ` fixture: all dates present, a return spanning the whole stint
computable, and a target date landing INSIDE the stint resolving to the real bridged close, not a
stale pre-stint one) and `test_same_date_conflict_primary_series_wins` (the pre-existing
same-date-conflict assertion, confirmed to still hold under the new per-date-merge logic). Full
suite: 367/367 pass.

## 4. Real effect, measured after implementation (not just the prototype)

```
TRAIN:    n=60,694  missing=795  rate=1.310%
HOLD-OUT: n=6,020   missing=54   rate=0.897%
Gap: 0.413pp  (Amendment 4's commit bar: <=2.0pp -- still passes comfortably)

By cap_band (TRAIN):
  Micro   n=12,142  missing=171  rate=1.408%
  Small   n=12,139  missing=175  rate=1.442%
  Mid     n=12,138  missing=149  rate=1.228%
  Large   n=12,139  missing=155  rate=1.277%
  Mega    n=12,136  missing=145  rate=1.195%
Micro-minus-Mega gap: 0.214pp  (down from 14.099pp)
```

Exclusion-reason breakdown confirms the remaining missingness is unremarkable: 589 of the total are
"structural break inside the label window" (a real, expected, pre-existing exclusion category —
demergers/rights/ratio-conflicts — unrelated to this fix), and the residual "stale beyond cap"
cases are now a long, thin tail (single digits per specific staleness value) rather than a
systematic gap.

## 5. Scoring function, refit under the final label

**Identical specification** (unregularized logistic regression, the same four inputs, the same
median rule, the same Small/Large/Mega interaction, `NONE` disclosure as reference). Thresholds
unchanged (computed from features, not the label): `delivery_low` 13.3333, `isolated` 45.0,
`volume_ratio` band medians as in Amendment 4 §3.

**TRAIN population: 59,896 of 60,694** (up from Amendment 4's 56,541 — the direct, expected
consequence of the missing rate falling from 6.838% to 1.310%).

```
                                   Amendment 4        This amendment    SE        z
intercept:                        +0.282662          +0.262231       0.023458  +11.18
delivery_low:                     +0.441680          +0.430341       0.018024  +23.88
isolated:                         +0.012487          +0.005139       0.017001   +0.30
volume_ratio_high_band_eligible:  +0.189702          +0.185603       0.019827   +9.36
disclosure_SUBSTANTIVE:           -0.239005          -0.217863       0.024546   -8.88
disclosure_ROUTINE_ONLY:          -0.066848          -0.062078       0.025881   -2.40
disclosure_UNKNOWN_COVERAGE:      -0.172378          -0.162133       0.043193   -3.75
```

**These coefficients are BINDING.** `isolated`'s coefficient is now even more clearly not
distinguishable from zero (z=+0.30, down from +0.71 and +1.12 in earlier rounds — consistent across
every post-correction fit, on progressively cleaner data). Every other coefficient remains
significant at `|z|>2.4` and stable within one SE of both Amendment 4's and every earlier round's
value. `disclosure_UNKNOWN_COVERAGE` remains at roughly 40% of its pre-correction (Amendment 1)
magnitude.

**FAIR baseline: 59.78%** (TRAIN `relative_t0_primary` rate). **In-sample AUC 0.5768, Brier
0.2362** — record only, not a forward-generalization claim.

## 6. Phase 8b re-run under the final label

No feature's direction reverses from any prior round.

| Feature | TRAIN AUC [95% CI] (n) | Excl. 0.5? | HOLD-OUT AUC [95% CI] (n) | Excl. 0.5? |
|---|---|---|---|---|
| `zscore_60d` | 0.5285 [0.5238,0.5332] (59,899) | Yes | 0.5250 [0.5104,0.5397] (5,966) | Yes |
| `volume_ratio` | 0.5765 [0.5719,0.5811] (59,899) | Yes | 0.5374 [0.5227,0.5520] (5,966) | Yes |
| `delivery_pct_percentile_60d` | 0.4217 [0.4170,0.4264] (59,896) | Yes | 0.4683 [0.4536,0.4830] (5,966) | Yes |
| `return_20d_context_only` | 0.5253 [0.5206,0.5300] (59,632) | Yes | 0.4853 [0.4706,0.5000] (5,965) | **Borderline** (upper CI = 0.5000) |
| `close_to_close_60d`* | 0.5122 [0.5075,0.5170] (59,376) | Yes | 0.4768 [0.4620,0.4915] (5,947) | Yes |
| `same_date_event_count` | 0.4776 [0.4729,0.4823] (59,899) | Yes | 0.4835 [0.4688,0.4982] (5,966) | Yes |
| `asm_gsm_labelled` | 0.5000 [0.4952,0.5047] (59,899) | No | 0.5061 [0.4914,0.5208] (5,966) | No |

*not rebuilt this session, unchanged caveat from prior rounds.

`return_20d_context_only`'s HOLD-OUT CI touches 0.5 at the printed precision — reported as a
genuine borderline case rather than forced into "excludes," consistent with this project's practice
of not overstating precision. Every other feature's CI excludes 0.5 except `asm_gsm_labelled`,
unchanged from every prior round.

## 7. Missing-data threshold and evaluation timing

**Threshold: 4.3%** — TRAIN's own final missing rate (1.310%) plus the instructed 3-point margin
(1.310% + 3.0pp = 4.310%). **This replaces Amendment 4's 9.8% and is now LOWER than even the
original pre-registration's 5%** (Amendment 2 §4) — a label whose missingness is genuinely rare and
not concentrated in a particular part of the population supports a tighter bar than the original
speculative one did.

**Timing: unchanged from Amendment 4 — the binding evaluation runs no earlier than 10 sessions past
the last window event's own GLOBAL t+90** (the staleness cap itself did not change, only how
thoroughly the code looks for a close within it). Estimated date: still roughly **early June 2027**.

**Worst-case sensitivity: kept exactly as drafted in Amendments 4/2** — every forward-window event
still missing its outcome is re-scored as `label = 1` in a sensitivity pass, reported alongside,
never blended into, the binding result.

## 8. Secondary comparison model, Phase 8b table's `RESULTS.md` citation, derived-artifacts policy

**Unchanged in substance from Amendment 4 §§5, 7** — Amendment 1's complete original scoring
function (old thresholds AND old coefficients together) remains the secondary comparison, now
scored against this amendment's final label; the derived-artifacts rebuild policy stands, with this
session's own P8-014 discovery as further, independent motivation (a THIRD real instance this
session of a component's own output needing direct verification rather than being assumed correct
because an earlier fix addressed a related problem). `docs/RESULTS.md`'s existing correction
(citing 0.5234 for `zscore_60d`'s HOLD-OUT AUC under Amendment 4's label) is superseded by this
amendment's 0.5250 — both close to each other and both far from the pre-correction 0.537; not
updated again in `RESULTS.md` itself, since the existing correction bullet already points readers
to the amendment series for the current number rather than hardcoding one that would need updating
a third time.

## 9. Pinned commit

**Pinned commit: `afe3e2bd07abe8b602c4119b916f7696a3c12131`** (supersedes Amendment 4 §8's
`c4925b6` — `build_symbol_history`'s `extend_with_series` logic changed this round). Pinned sources
otherwise unchanged from Amendment 4 §8, with the label row updated:

| Input | Pinned source |
|---|---|
| Label (`relative_t0_primary`) | `scripts/phase8_robustness_relabel_t0.py` (`P8-013` global-horizon definition, 10-session staleness cap, `P8-012`/`P8-014` full per-date EQ/BE/BZ bridge) |
| (all other inputs) | unchanged from Amendment 4 §8 |

---

## The pre-registration is now frozen

**No further amendment is anticipated.** Every input, threshold, coefficient, and evaluation
procedure this pre-registration needs is now measured, verified, and pinned. A future amendment is
warranted only for a defect discovered before the forward evaluation runs that would make the
evaluation impossible to run at all — a code failure, a data-availability failure, or an
equivalent blocking problem — not for further refinement of numbers already measured and settled
across this amendment series. The next real action on this pre-registration is the evaluation
itself, no earlier than ~early June 2027.
