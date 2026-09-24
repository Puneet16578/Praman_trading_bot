# Phase 10 Amendment 5 — Prep Notes

## Summary

Amendment 4, as committed, asserted the redefined (`P8-013`) global-horizon outcome label's
missingness "isn't correlated with the model's own inputs" — but that claim had never actually been
measured; round 4's step 1 checked only the OLD own-session definition's gradient. Measuring the
NEW definition directly this round found the claim **false**: TRAIN missing rate was 6.838% (4.3x
the pre-`P8-013` rate), with a clean, steep 14.1pp Micro-minus-Mega gradient — WORSE than the label
`P8-013` replaced. Root cause (`P8-014`): `P8-012`'s series-extension logic bridged a PERMANENT
EQ→BE/BZ migration but not a TEMPORARY EQ→BE→EQ stint that resumes normal trading — exactly the
surveillance-driven pattern common to the volatile micro-caps this project most needs to keep.
92.37% of TRAIN's staleness-cap-missing events had a real, unused BE/BZ close in the window the old
logic never examined.

Prototyped a full per-date bridge read-only first, against the pre-specified decision rule (TRAIN
missing rate must fall ≥1.0pp AND the Micro-minus-Mega gap must narrow) — both passed decisively
(6.42pp fall; gap 14.1pp→0.4pp) — then implemented it in the pinned pipeline
(`src/signals/event_catalogue.py`'s `build_symbol_history`), added tests, relabeled, refit, and
re-ran Phase 8b, all under the corrected label. Final numbers: TRAIN missing rate 1.310%, HOLD-OUT
0.897% (gap 0.413pp, well inside the 2.0pp bar), Micro-minus-Mega gap 0.214pp. No coefficient or
feature-direction conclusion changed from Amendment 4. Missing-data threshold reset to 4.3%
(1.310% + 3.0pp) — now lower than even the original pre-registration's speculative 5%. Pinned
commit updated to `afe3e2bd07abe8b602c4119b916f7696a3c12131`.

`docs/phase10_preregistration_amendment5.md` committed as its own document (Amendment 4 not
reopened, per its own immutability notice) and states explicitly that no forward outcome existed
at commit. The pre-registration is now declared **FROZEN**: further amendments are warranted only
for a defect that would make the evaluation impossible to run, not for further refinement of
numbers already measured and settled.

Also registered in `docs/DEFECT_REGISTER.md`: a new `P8-014` entry (root cause, fix, before/after
numbers) and a correction appended to the existing `P8-013` entry noting its original claim was
never actually checked against the new label's own missingness — both committed as `be0a669`,
before this round's amendment document was written.

## What was done, in order

1. **Measured (read-only)**, per item 1: new-definition TRAIN missing rate by `cap_band`,
   `volume_ratio_high`, `delivery_low`, and ASM/GSM status, side by side with the OLD definition's
   gradient (`scripts/phase10_amendment5_measure.py`); and the share of new-definition MISSING
   events with an unused BE/BZ close inside the staleness window (92.37%).
2. **Prototyped the bridge**, per item 2, with no pipeline change yet
   (`scripts/phase10_amendment5_bridge_prototype.py`): TRAIN missing rate 6.838%→0.414%, gap
   14.099pp→0.395pp, HOLD-OUT 0.150%, TRAIN/HOLD-OUT gap 0.264pp.
3. **Applied the decision rule**, per item 3: both criteria (≥1.0pp fall; gap narrows) passed
   decisively → ADOPT.
4. **Implemented the bridge** in `src/signals/event_catalogue.py`'s `build_symbol_history`
   (`extend_with_series` now bridges per date across the full calendar via a `covered_dates` set,
   rather than only appending rows strictly after the primary series' own last date), added
   `test_temporary_stint_bridged_not_just_the_tail` and renamed the pre-existing conflict test to
   `test_same_date_conflict_primary_series_wins` in `tests/test_event_catalogue.py`. Full suite:
   367/367 pass.
5. **Relabeled** by re-running `scripts/phase8_robustness_relabel_t0.py` against the fixed
   pipeline: HOLD-OUT `possible_delisting_or_suspension` flags fell from 368 to 9.
6. **Refit** the identical specification via `scripts/phase10_fit_scoring_function.py`: TRAIN
   n=59,896 (up from 56,541), coefficients and SEs reported beside Amendment 4's in the amendment
   document §5. No sign or significance conclusion changed; `isolated` remains indistinguishable
   from zero (z=+0.30).
7. **Re-ran Phase 8b** via `scripts/phase10_amendment4_phase8b_reauc.py` under the corrected label
   (TRAIN n=59,899, HOLD-OUT n=5,966), full CI table in the amendment document §6, flagging
   `return_20d_context_only`'s HOLD-OUT CI as touching 0.5000 exactly rather than confidently
   "excluding" it.
8. **Computed final real missing-data numbers** directly from the rebuilt
   `data/processed/phase8_relabel_t0_relative.csv`: TRAIN 1.310% (795/60,694), HOLD-OUT 0.897%
   (54/6,020), gap 0.413pp, Micro-minus-Mega gap 0.214pp — confirming the difference from the
   prototype's 0.414% is fully explained by 589 legitimate "structural break inside the label
   window" exclusions, unrelated to this fix.
9. **Set the new threshold**: 1.310% + 3.0pp = 4.310%, stated as 4.3%.
10. **Wrote and committed** `docs/phase10_preregistration_amendment5.md` (this session, commit
    `8173097`) — the amendment itself, per the commit rule (both decision-rule criteria passed, so
    the ADOPT branch's full implement-relabel-refit-repin-commit sequence applied).
11. **Declared the pre-registration FROZEN**, per the closing instruction, in the amendment
    document's final section.

## Not done this round, noted rather than actioned

- `scripts/compute_outcome_labels.py` (the Phase 6 outcome-labels script, distinct from the
  pre-registration's own `phase8_robustness_relabel_t0.py`) uses the same `extend_with_series`
  mechanism and benefits automatically from the fix at its next run, but was not re-run this round
  — it was not named in this round's item list, and it does not feed the pre-registration's own
  pinned label. Left as a candidate for a future, separately-scoped session.

## Final commit hash

`afe3e2bd07abe8b602c4119b916f7696a3c12131` — the pipeline code fix (`build_symbol_history`'s
per-date bridge). This is the value recorded in `docs/phase10_preregistration_amendment5.md` §9 as
the new pinned commit for the forward evaluation.

Doc commit hashes: amendment document `81730977f77bfee55f9d524b9dda7db85d675fa6`; this prep doc
itself `cad54af97537f02e3da03c78738e3be58e555bcc`.
