# Phase 10 Pre-registration — Amendment 2

**Dated 2026-09-22. Amends `docs/phase10_preregistration.md` and Amendment 1 without editing
either, per their own immutability notices. This amendment is not edited after its own commit
either — a future correction is Amendment 3, in a new file.**

**Transparency note, stated because nothing in the earlier documents said it: as of this commit,
the repository has NOT yet been pushed to a private remote, and the pre-registration/amendment
commit hashes have NOT yet been recorded with any third party.** That is a real, open gap, not a
silent omission — flagged here plainly rather than left for a reader to infer from absence. See
the closing confirmation section below.

## Summary (read this first)

Five gaps closed, none requiring new computation beyond a git-hash lookup and citing numbers
Amendment 1 already computed: (1) **success criterion 2 gets a noise margin** — top-decile
precision on ~510 events has a standard error too large for a bare point comparison to mean
anything; replaced with a paired-bootstrap 95% CI of the LIFT difference that must exclude zero,
using the same 2,000 resamples (now seeded) as criterion 1. (2) **the feature pipeline is pinned**
to commit `a01eda4` — the forward evaluation runs against that exact code regardless of what
changes in this repo before 2027. (3) **`UNKNOWN_COVERAGE` gets a pre-specified sensitivity
analysis** (secondary only) since its coefficient is the model's largest and reflects data
coverage, not behavior. (4) **a missing-data rule**: more than 5% of the window missing inputs or
outcome reports the evaluation COMPROMISED, neither pass nor fail. (5) **an ingestion schedule**:
weekly, from now through window close, not one 2027 backfill.

---

## 1. Success criterion 2: a noise margin via paired bootstrap

**Problem.** The top-decile evaluation set is ~510 events (10% of the expected ~5,100). A
proportion's standard error at that size is `sqrt(0.5×0.5/510) ≈ 2.2pp` — two models with
genuinely identical true performance would satisfy a bare "new LIFT > current LIFT" point
comparison about half the time, by chance alone. A success criterion that can't distinguish signal
from that noise floor is not a real criterion.

**Fix.** Success criterion 2 (`docs/phase10_preregistration.md`, § Success criterion) is replaced:

> The new design's success on criterion 2 requires the paired-bootstrap 95% confidence interval of
> `(new design's top-decile LIFT − current classifier's top-decile LIFT)` to exclude zero, with
> the interval's lower bound strictly greater than zero (i.e. favoring the new design, not merely
> "different from zero" in either direction).

**Bootstrap procedure, fully specified now, one shared seed for both criteria (fixing the gap
Amendment 1 left open — it specified "2,000 resamples" for criterion 1's BSS CI but never stated a
seed):**

```
BOOTSTRAP_SEED = 2027   (the evaluation year -- chosen for no reason beyond being memorable and
                          stated in advance; any fixed integer would serve identically)
rng = numpy.random.default_rng(BOOTSTRAP_SEED)
n = size of the forward evaluation set (§3 of Amendment 1: events 2026-09-16 through 2027-01-15
    with a computable 90-session outcome)
resamples = [rng.integers(0, n, size=n) for _ in range(2000)]   # 2000 index arrays, generated ONCE
```

These 2,000 index arrays are reused for EVERY bootstrap CI this evaluation reports:
- **Criterion 1** (`docs/phase10_preregistration.md`): for each of the 2,000 resamples, recompute
  the new design's Brier score and the FAIR baseline's Brier score on the resampled rows, and BSS
  from those two; the CI is the 2.5/97.5 percentile of the 2,000 resulting BSS values.
- **Criterion 2** (this amendment): for each of the SAME 2,000 resamples, recompute both the new
  design's and the current classifier's top-decile LIFT **on the identical resampled rows** (a
  paired bootstrap, not two independently resampled ones — this is what "identical resample
  indices for both models" means, and is the correct method for a difference-of-two-correlated-
  estimators CI, not an incidental detail). The CI is the 2.5/97.5 percentile of the 2,000
  resulting `(new LIFT − current LIFT)` differences. The top-decile tie-break within each resample
  uses `SEED = 42` (Amendment 1, unchanged) applied independently inside each resample.

**Not run today.** No forward data exists; this section specifies the procedure and freezes the
seed, exactly as thresholds and coefficients were frozen without being applied to unseen data in
the original pre-registration and Amendment 1.

## 2. The feature pipeline is pinned

**Pinned commit: `a01eda422475c7eb914e9fd615511ea2c1d52aec`** (this repository's `HEAD` at the time
this amendment was written — the parent of this amendment's own commit, which touches only this
document). The forward evaluation computes every input — the event catalogue, delivery
percentile, co-movement count, volume ratio, disclosure-tier mapping, cap-band quintiles, and the
`relative_t0_primary` label itself — using the code AT THIS COMMIT, specifically:

| Input | Pinned source |
|---|---|
| Event catalogue / raw signals (`volume_ratio`, `delivery_pct_percentile_60d`, `zscore_60d`) | `src/signals/event_catalogue.py` (`compute_daily_stats`), `scripts/build_final_event_catalogue.py` |
| Co-movement (`same_date_event_count`) | `scripts/compute_clustering.py` |
| Disclosure-tier mapping | `src/signals/disclosure_classification.py` |
| Cap-band quintiles | `scripts/build_event_classifications.py` / `scripts/phase8_classify_holdout.py`'s shared `compute_quintile_bands` logic |
| Label (`relative_t0_primary`) | `scripts/phase8_robustness_relabel_t0.py` |
| Scoring function coefficients / thresholds | `docs/phase10_preregistration.md`, this amendment's §1 |

**If any of this code changes in this repository before the forward evaluation runs, the BINDING
evaluation still runs against the pinned commit** (e.g. via `git worktree`/`git checkout` of
`a01eda4` at evaluation time, or an equivalent snapshot) — not against whatever `master` has
become by 2027. Any evaluation ALSO run against later code may be reported, but only as a
separate, explicitly-labeled secondary comparison, never blended into or substituted for the
pinned-commit result.

## 3. `UNKNOWN_COVERAGE` sensitivity analysis — pre-specified, secondary only

**Why:** `disclosure_UNKNOWN_COVERAGE`'s fitted coefficient (`-0.396295`, Amendment 1 §1) is the
largest-magnitude coefficient in the model — larger than `delivery_low`'s. It reflects an absence
of cached announcement data for a symbol, a data-coverage fact about this project's own ingestion,
not a market-behavior signal. A forward window with an unusually high or low
`UNKNOWN_COVERAGE` share could move the model's aggregate score for reasons having nothing to do
with whether the redesign works.

**Pre-specified, before any forward data exists:**
1. **Report `UNKNOWN_COVERAGE`'s prevalence in the forward window directly against TRAIN's own
   10.2%** (Amendment 1 §1, `disclosure_UNKNOWN_COVERAGE mean=0.1021`, n=64,450) — no threshold for
   "too different" is set now; the comparison is reported, not gated, consistent with this
   project's practice of reporting a number before deciding it's disqualifying.
2. **A secondary analysis, excluding every `UNKNOWN_COVERAGE` event from the forward evaluation
   set, recomputing BSS (criterion 1) and top-decile LIFT (criterion 2) on the remaining subset.**
   Reported alongside the full-window result, not in place of it.

**This is secondary only. The binding success criteria (§1 above, and
`docs/phase10_preregistration.md`) are evaluated on the FULL forward window, `UNKNOWN_COVERAGE`
included, exactly as originally specified.** The secondary analysis exists to show whether a
pass or fail was driven by coverage composition, not to create a second path to a passing result.

## 4. Missing-data rule — pre-specified

**TRAIN excluded 1.7% of events for missing inputs** (Amendment 1 §1: 63,360 of 64,450 usable,
1,090 excluded — `1,090 / 64,450 = 1.69%`, matching "1.7%"). NSE's own archive has served
incorrect data before, silently, under conditions this project has already found and logged
(`P2-003`, `docs/DEFECT_REGISTER.md`: a real bhavcopy request returned a different date's file, a
95-day-old mismatch, with no error).

**Rule:** if more than **5%** of catalogued events in the forward window (2026-09-16 through
2027-01-15) lack a required input (`delivery_pct_percentile_60d`, `volume_ratio`,
`same_date_event_count`, `disclosure_tier`) OR lack a computable 90-session `relative_t0_primary`
outcome, **the evaluation is reported as COMPROMISED — not as a pass or a fail.** A compromised
evaluation does not retry with a laxer threshold or a different window silently; it is reported as
compromised, with the actual missing-data rate stated, and the decision about what to do next
(wait for cleaner data, investigate an ingestion defect, or accept the compromise and report both
readings) is made explicitly at that point, not pre-decided here.

## 5. Ingestion schedule — pre-specified

**Bhavcopy, corporate announcements, and ASM/GSM circulars are ingested on a regular weekly
schedule from the date of this amendment through the end of the evaluation window (2027-01-15),
not as a single backfill attempt after the window closes.** A weekly cadence surfaces an
ingestion failure (a `P2-001`/`P2-003`-shaped silent bad fetch, a schema drift, a source outage)
within days of when it happens, while it is still cheap to investigate and re-fetch — a single
2027 backfill would discover the same failure four months late, with a much larger window of
affected dates and far less specific information about when or why it started.

---

## Confirmations, answered directly

**Is the repository pushed to a private remote, are the commit hashes recorded with a third
party?** **No, neither has happened.** This repository has no git remote configured as of this
commit, and no `gh` CLI or equivalent is available in this environment to create one. The commit
hashes for the pre-registration and both amendments are listed below for the user to push and
record themselves, or to supply a remote URL for this session to push to directly:

| Document | Commit |
|---|---|
| `docs/phase10_preregistration.md` | `86585092648f2df0270743f553904856f6aa8d76` |
| Amendment 1 | `d98c1dbd1c0cf90999d636b2e99791477cd7e3a6` |
| P8-003 fix (pinned feature-pipeline commit, §2 above) | `a01eda422475c7eb914e9fd615511ea2c1d52aec` |
| This amendment (Amendment 2) | *(the commit that introduces this file — see the repository log)* |

**Is P8-003 resolved via the template route, not an expanded word list?** **Confirmed.**
`src/agent/banned_terms.py` was NOT modified toward broader coverage. The resolution
(`docs/DEFECT_REGISTER.md` `P8-003`, `CLAUDE.md`'s "LLM narrative scope" note under invariant 2) is
architectural: confirmed by direct grep that zero LLM-provider-calling code exists anywhere in
`src/` as of the pinned commit above — every `EvidenceClaim.text` a symbol-naming report renders is
a deterministic Python template over data (`src/agent/specialists.py`), and `synthesis.py` never
calls a provider. `CLAUDE.md` now states this as binding policy for any future work: an
LLM-narrative capability, if ever added, must be local/dev-only and must never reach shareable
output. `banned_terms.py` itself is unchanged, kept only as a backstop, with both its 0/5
(Phase 7c) and 0/11 (Phase 9) catch rates recorded plainly beside it rather than hidden or treated
as the primary control.
