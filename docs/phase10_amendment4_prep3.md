# Amendment 4 Prep, Round 3 — Measure the Plateau, Don't Assume It

Round 2 diagnosed two real mechanisms behind HOLD-OUT's elevated missing-outcome rate and fixed
one of them for real (`P8-012`), but picked its 20-session buffer and 11.4% threshold by matching
the fix's own stated delay — not by measuring where the artifact actually stops mattering. This
round attempted that measurement directly, as instructed, and it did not converge. **Per the
review's own decision rule, Amendment 4 is NOT committed this round.**

## Summary (read this first)

**No plateau within 120 sessions.** Measured the missing-outcome rate's decay curve by buffer band
on the TRAIN replicate (artificial truncation at 2024-06-30, with `P8-012`'s series extension
applied): 0-15→4.945%, 15-30→10.386%, 30-45→9.001%, 45-60→12.817%, 60-75→7.290%, 75-90→5.784%,
90-120→4.222%, 120+→1.163% (reference). Every band below 120 sessions differs from the 120+
reference by 3.1-11.7 percentage points — no band comes within the required 1.0pp, and the shape
is non-monotonic, not a clean decay. **Diagnosed why, not left unexplained**: on a single fixed
truncation date, each buffer band corresponds to a narrow, non-overlapping 2-6-week window of real
event dates (confirmed directly — e.g. the 45-60 band is entirely 2023-11-20 through 2023-12-11).
Buffer and calendar time are the same variable up to a fixed 90-session offset in this design, so
it cannot separate "the boundary artifact fading with more slack" from "whatever else varied by
calendar period" — most plausibly a real, transient trading-density dip across many smallcaps in
late 2023/early 2024. **Confirmed the underlying mechanism is still genuine**: every "lacking"
event checked in the worst band (45-60, 12.8%) DOES have a real, computable outcome once the
artificial truncation is lifted (e.g. `AAKASH` 2023-12-04: real `forward_return_90d` = +57.6%,
`ADANIPOWER` 2023-11-28: +59.1%) — these are genuine truncation artifacts, not real gaps. But the
curve's shape cannot be read cleanly off one truncation date; a proper measurement needs several
truncation dates, spread across different calendar periods, averaged together, so calendar-specific
noise cancels and only the buffer-dependent shape remains. **Not attempted this round** — flagged
as the concrete next step.

**Consequence, applied exactly as the decision rule specified**: since no plateau was reached by
120 sessions, §4's timing (buffer B) and missing-data threshold are NOT finalized and Amendment 4
is NOT committed. The second revision's 20-session/11.4% figures are kept in the draft only as an
explicitly-flagged PROVISIONAL placeholder, not a result.

**Everything else requested this round is done and does not depend on the plateau question:**
Hanley-McNeil 95% CIs added to every row of the Phase 8b re-run table (TRAIN and HOLD-OUT) — every
feature's CI excludes 0.5 except `asm_gsm_labelled`, which straddles it in both populations,
consistent with "adds nothing." A real imprecision in round 2's own language was caught and
corrected while adding the CIs: `same_date_event_count`'s univariate AUC CI DOES exclude 0.5 (a
real, if small, marginal association) even though its multivariate coefficient (`isolated`) is not
significant — these are compatible, not contradictory, findings (ordinary multicollinearity, a
weak-but-real signal made redundant by stronger correlated features already in the model), and
round 2's "directly consistent... not coincidental" phrasing had blurred this distinction.
`docs/RESULTS.md` updated to cite the corrected AUC figures where it previously cited the
pre-correction ones (its precision@20 figures, from a different, un-re-run script, are unchanged
and explicitly left as such). The considered-and-rejected alternative (redefining the outcome at a
fixed 90-GLOBAL-session horizon using the last available close, which would remove the artifact at
its root but retroactively changes the label definition and forces a full relabel/refit) is now
named explicitly in the draft, not adopted.

**No pipeline code changed this round** (only a new read-only diagnostic script and
documentation) — the pinned commit from round 2 (`97a459e429f0dde5ae18a10e3cf1ce375df8259d`)
stands unchanged; nothing needed re-pinning.

**Final commit hash for this round's own work**: see below (Part 1 measurement script, `RESULTS.md`
fix, and this document are committed as their own commit; the amendment draft itself remains
uncommitted, exactly as in rounds 1 and 2, per "the amendment is committed only after review" —
this round did not reach a state that passes that review).

---

## 1. The decay curve, measured

`scripts/phase10_amendment4_decay_curve.py`. TRAIN events near the artificial 2024-06-30
truncation, banded by sessions of slack between their naive global t+90 and the truncation,
computed under the truncated view WITH `P8-012`'s `("BE","BZ")` series extension applied (the same
logic production `compute_outcome_labels.py` now uses, restricted to rows dated on/before the
truncation):

| Band (sessions before truncation) | n | Lacking | Rate | \|dev from 120+\| |
|---|---|---|---|---|
| 0-15 | 1,092 | 54 | 4.945% | 3.78pp |
| 15-30 | 751 | 78 | 10.386% | 9.22pp |
| 30-45 | 911 | 82 | 9.001% | 7.84pp |
| 45-60 | 671 | 86 | 12.817% | 11.65pp |
| 60-75 | 631 | 46 | 7.290% | 6.13pp |
| 75-90 | 657 | 38 | 5.784% | 4.62pp |
| 90-120 | 1,729 | 73 | 4.222% | 3.06pp |
| 120+ (reference) | 35,606 | 414 | 1.163% | — |

**Plateau rule applied exactly as specified** (smallest buffer beyond which every band from there
up is within 1.0pp of the 120+ rate): no band below 120 qualifies. **B is not reached within the
tested range.**

## 2. Why the curve doesn't converge — diagnosed, not left as noise

Checked directly: the event-date range within each band.

```
0-15:    2024-01-24 .. 2024-02-14   (n=1,092)
15-30:   2024-01-03 .. 2024-01-23   (n=751)
30-45:   2023-12-12 .. 2024-01-02   (n=911)
45-60:   2023-11-20 .. 2023-12-11   (n=671)
60-75:   2023-10-30 .. 2023-11-17   (n=631)
75-90:   2023-10-05 .. 2023-10-26   (n=657)
90-120:  2023-08-22 .. 2023-10-04   (n=1,729)
120+:    2020-01-01 .. 2023-08-21   (n=35,606)
```

Each band (other than 120+, which aggregates nearly 4 years) is a distinct, essentially
non-overlapping few-week slice of calendar time. This is a structural property of measuring
"buffer before ONE fixed truncation date," not a coding error: buffer = (truncation index) −
(event's own naive t+90 index), so for a fixed truncation, buffer and event_date move together
one-for-one. Any calendar-period-specific effect (e.g. a real, temporary dip in trading frequency
across many smallcap names in Q4 2023/Q1 2024 — plausible given several bands cluster right around
that period, though not independently confirmed beyond this observation) shows up as a buffer-band
effect and cannot be distinguished from genuine boundary-artifact decay using only this design.

**Verified the mechanism is still real, not a phantom.** Sampled the highest-rate band (45-60,
12.8%) and checked every one of its 86 "lacking" events against the REAL, untruncated
`outcome_labels.csv`:

```
AAATECH    2023-12-11  real forward_return_90d=+43.1%  real collapsed=False
AAKASH     2023-12-04  real forward_return_90d=+57.6%  real collapsed=False
AAKASH     2023-12-05  real forward_return_90d=+46.7%  real collapsed=False
ADANIPOWER 2023-11-28  real forward_return_90d=+59.1%  real collapsed=False
ALMONDZ    2023-12-01  real forward_return_90d=+31.6%  real collapsed=False
```

Every one has a genuine, computable outcome once the artificial truncation is lifted — confirming
these are real boundary-truncation artifacts (the mechanism is real), just not cleanly measurable
as a smooth function of buffer alone from a single truncation date.

**What would resolve this, not attempted here**: repeat this same measurement at several
DIFFERENT artificial truncation dates (spread across different years/seasons of TRAIN's history)
and average the resulting rate per buffer band across all of them — calendar-specific noise
specific to any one truncation's own nearby period would then average out, leaving (if it exists)
a genuine, buffer-dependent decay shape. A concrete next step for a future session, not guessed at
or approximated here.

## 3. Phase 8b re-run, with confidence intervals

Every row of `scripts/phase10_amendment4_phase8b_reauc.py`'s output, with Hanley-McNeil 95% CIs
(already computed by the script; round 2's table only surfaced the point estimate):

| Feature | TRAIN AUC [95% CI] (n) | Excludes 0.5? | HOLD-OUT AUC [95% CI] (n) | Excludes 0.5? |
|---|---|---|---|---|
| `zscore_60d` | 0.5293 [0.5246,0.5340] (59,730) | Yes | 0.5234 [0.5081,0.5387] (5,486) | Yes |
| `volume_ratio` | 0.5787 [0.5741,0.5833] (59,730) | Yes | 0.5390 [0.5238,0.5543] (5,486) | Yes |
| `delivery_pct_percentile_60d` | 0.4202 [0.4155,0.4249] (59,727) | Yes | 0.4618 [0.4465,0.4771] (5,486) | Yes |
| `return_20d_context_only` | 0.5241 [0.5193,0.5288] (59,462) | Yes | 0.4760 [0.4606,0.4913] (5,485) | Yes |
| `close_to_close_60d`* | 0.5127 [0.5080,0.5175] (59,207) | Yes | 0.4665 [0.4511,0.4818] (5,467) | Yes |
| `same_date_event_count` | 0.4755 [0.4708,0.4802] (59,730) | Yes | 0.4814 [0.4660,0.4967] (5,486) | Yes (barely) |
| `asm_gsm_labelled` | 0.5002 [0.4955,0.5050] (59,730) | **No** | 0.5028 [0.4875,0.5181] (5,486) | **No** |

*not rebuilt this session (stale feature file, out of scope — caveat unchanged from round 2).

**Every feature's CI excludes 0.5 in both TRAIN and HOLD-OUT except `asm_gsm_labelled`**, which
straddles 0.5 in both — the only feature genuinely indistinguishable from chance, matching the
pre-registration's own "adds nothing" conclusion.

**Correction to round 2's own language**: `same_date_event_count`'s CI excluding 0.5 (a real
marginal signal, even though weak) and its regression coefficient `isolated` not being
significant in the §3 multivariate fit (z=+1.12) are NOT restating the same finding — round 2's
"directly consistent... not coincidental" phrasing implied they were. They measure different
things: marginal (univariate) association vs. incremental (conditional-on-other-features)
contribution. A weak-but-genuine univariate signal becoming statistically redundant once
correlated, stronger features are already in the model is ordinary multicollinearity, not a
restatement of the same fact twice.

## 4. `RESULTS.md` updated

Added a dated correction bullet (matching the document's own existing convention) pointing at the
one place `RESULTS.md` cited a specific pre-correction clean-label AUC figure (`zscore_60d`
HOLD-OUT, "0.537") — now states the corrected 0.5234 [0.5081,0.5387] and points to this document
and the draft amendment §6 for the full table. Explicitly does NOT touch the separate precision@20
figures cited in the same paragraph (15.0%/40.0%/80.0%/95.0%, from `scripts/phase8_robustness_
check1_direction.py`), since that script was not re-run this session — stated as such, not
silently left ambiguous.

## 5. Considered alternative, named and rejected

**Redefining the outcome at a fixed 90-GLOBAL-session horizon, using the last available close for
a symbol that isn't trading on that exact session, instead of requiring the symbol's own 90th real
EQ session.** This would remove the boundary artifact at its root — "fully elapsed" and "outcome
computable" become the identical condition by construction, no diagnosis or buffer needed. **Not
adopted**: it changes what `relative_t0_primary` MEANS (return to a fixed calendar point using a
possibly-stale price, not return to the security's own next real trading milestone), not just when
it can be evaluated — a materially different label definition that would require relabeling the
entire TRAIN population and refitting §3's coefficients under the new definition, a bigger change
than a timing/threshold adjustment. Recorded in the draft amendment (§4c) as a live option for the
project owner to decide explicitly, not silently ruled out or adopted by default.

---

## Decision, applied exactly as instructed

**No plateau reached by 120 sessions → STOP and report, per the decision rule given.** Amendment 4
is NOT committed this round. `docs/phase10_preregistration_amendment4.md` (now its third revision)
remains on disk, uncommitted, with §4 explicitly marked provisional and every other section
finalized. This round's own real, standalone contributions — the decay-curve script, the corrected
Phase 8b CI table, and the `RESULTS.md` fix — are committed on their own, separately from the
still-open amendment.

**Final commit hash for this round's work**: `<filled in by the commit below>`.
