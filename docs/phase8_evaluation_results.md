# Phase 8 — Evaluation Results

**Hold-out discipline, stated up front, per instruction:** all classification thresholds used in
this evaluation (per-cap-band momentum medians, the isolated co-movement cutoff) were frozen using
only events with `event_date < 2026-01-01` (`scripts/phase8_freeze_thresholds.py`). 2026 was not
looked at, in any form, until the classification and metrics scripts below were run against it as
the final, single-pass hold-out. This is a real, disclosed departure from Phase 7b's production
thresholds, which are fit on the full available history (2019 through today) and remain correct
for a live system that legitimately uses everything it knows at the time it runs — the two are
different artifacts for different purposes, not one superseding the other. See "A note on
threshold vintages" near the end for the one place this distinction produced a measurable effect.

**Split sizes:** 64,450 TRAIN events (`event_date < 2026-01-01`) used only for freezing thresholds
and for deriving the (class, cap_band)/(disclosure_tier, cap_band) scoring tables Layer 2/3 use;
10,850 HOLD-OUT events (`event_date >= 2026-01-01`, roughly the first 8.5 months of 2026) are the
entire subject of every number in Layers 2 and 3 below.

**Never headlined: accuracy.** The class distribution is heavily imbalanced (GROUNDED ~44-47%
depending on period) and a bare accuracy number would be dominated by that imbalance, not by
anything this system does well or badly. Every metric below is either a rate within a stratum (with
n and a 95% Wilson confidence interval) or a proper scoring rule (Brier score). None of them is
"percent correct."

**Report failures first**, per instruction — three to report, all found and traced during this
evaluation, not before it, and all left in rather than smoothed over:

1. **Layer 1's one claim rejection.** Of 29,764 claims that reached output across 2,000 real
   events, exactly one claim was withheld — correctly, by design, not a defect. A real disclosure's
   own text quoted a news headline containing "fraudulent" (the company was denying involvement),
   and the banned-term lint has no way to distinguish a source document's own wording from this
   project's own assertion, so it drops the claim either way. See Layer 1 below for the full case.
2. `scripts/phase8_layer3_baselines.py`'s spot-check (100 real `MultiAgentOrchestrator` runs
   against the deterministic classifier's own output) found 99/100 matched and one did not —
   `CIEINDIA`/`2026-02-10`, classified `UNEXPLAINED` by the frozen-threshold deterministic rule and
   `PARTIALLY_GROUNDED` by the live agent system. Traced directly: this event's `abs(return_20d)`
   falls between the Mid-band momentum median under frozen thresholds (0.11949) and under
   production thresholds (0.11615) — the live orchestrator loads production thresholds (correct
   for a live system), this evaluation's baseline 4 uses frozen ones. Same logic, two threshold
   vintages, not a control-flow bug — but a real, quantified sensitivity (~1% of a 100-event
   sample) worth knowing about.
3. **The full classifier's raw Brier score (0.2024) does not beat predicting the flat 2026
   population base rate for every event with no information at all (Brier ≈ 0.192)** — found while
   assembling the Layer 3 baseline table, not anticipated going in. Directly explained by the
   calibration section's own finding (systematic under-confidence: 2026 ran hotter than the
   2019-2025 training period the scores were derived from) — see "Layer 3" for the full reasoning
   and why the classifier's real, positive contribution shows up in top-tier precision and lead
   time instead, not in this number.

---

## Layer 1 — Factual accuracy

2,000 events (seed=42, sampled from the full 2019-2026 catalogue — see the plan discussion for why
this layer, unlike 2/3, is not restricted to the 2026 hold-out: it tests the report-generation
pipeline's own correctness, not predictive generalization). Real, unmodified `MultiAgentOrchestrator`
runs, no caching shortcuts — 11,183 seconds (~3.1 hours) wall-clock. Zero orchestrator exceptions.

**Claims verified, by type:**

| Claim type | n | Transcription | Derivation |
|---|---|---|---|
| announcement (per-disclosure existence) | 6,269 | 100% PASS | N/A (not yet implemented for this type) |
| volume_ratio | 2,000 | 100% PASS | 391 PASS / 1,609 not sampled (19.6% sample rate) |
| delivery_pct_percentile_60d | 2,000 | 100% PASS | 395 PASS / 1,605 not sampled (19.75% sample rate) |
| delivery_pct, zscore, return_20d, raw_ohlc, catalogue_membership, asm_stage, gsm_stage, lead_time, disclosure_tier, no_coverage, attachment_url_unavailable | 17,495 (combined) | 100% PASS | N/A (no independent derivation implemented for these types — Phase 7c's stated scope, not silently expanded here) |
| **Total** | **29,764** | **100% PASS (29,764/29,764)** | **786 PASS, 0 FAIL, rest N/A or not sampled** |

**Zero transcription failures. Zero derivation failures.** Of the 4,000 claims eligible for the
derivation tier (volume_ratio + delivery_pct_percentile_60d, 2,000 each), 786 (19.65%) were sampled
and independently re-derived from raw bhavcopy via a separate code path — matching the ~20% target
rate at scale, not just in the small samples checked during Phase 7c.

**Any claim that reached output unverified: zero.** Every one of the 29,764 claims in the output
carries an explicit transcription verdict and an explicit derivation verdict (PASS, NOT_SAMPLED, or
NOT_APPLICABLE) — no claim's verification status is missing or ambiguous.

**The boundary of what "100%" establishes here, stated explicitly so it isn't read as a stronger
guarantee than it is.** Transcription alone proves every claim was copied faithfully from the
function that produced it — it CANNOT catch a bug inside that shared function, since it re-runs
the exact same code and compares the result to itself (Phase 7c's own finding, the reason the
derivation tier exists at all). The 20% derivation sample is what makes this a check on
CORRECTNESS, not just transcription: 786 of those 29,764 claims were independently recomputed from
raw `bhavcopy` rows via a separate, hand-written SQL implementation (`src/agent/derivation_check.py`)
that never calls `build_symbol_history`/`compute_daily_stats` at all, and every one of those 786
agreed with the shared function's output within tolerance. That is real evidence the shared
formula itself is correct, not merely that specialist agents transcribe it faithfully — but it
covers only `volume_ratio` and `delivery_pct_percentile_60d` (the two claim types with an
independent second implementation). `zscore_60d`, `return_20d`, and the disclosure/surveillance
claim types have NO derivation-tier coverage at all (25,764 of 29,764 claims are `NOT_APPLICABLE`
at that tier) — for those, "100%" means "100% transcribed correctly," not "100% independently
proven correct." That gap is named, not implied away.

**Failures, individually, with cause — there is exactly one, and it is not a fabrication bug:**

`HAPPSTMNDS`/`2024-06-10`, a `DISCLOSURE` agent claim for a real announcement (seq_id
`105871507`), was REJECTED by the `conclusion_language` check — the banned-term lint flagged the
word "fraudulent." Traced directly: the real NSE announcement's own text is *"Happiest Minds
Technologies Limited has informed the Exchange regarding a press release ... titled 'Clarification
regarding news relating to fraudulent diversion of Karnataka government funds'"* — the company's
own press release, **quoting the title of a news story it was clarifying/denying involvement in**.
The word appears in a source document being cited, not in any assertion this project made. The
lint has no mechanism to distinguish "the disclosure's own text contains this word" from "this
project is asserting a verdict" — it doesn't try to; it drops the claim either way, which is the
conservative, fail-closed design CLAUDE.md invariant 12 calls for. **This is the safety mechanism
working as intended, not a defect** — but it is also a real, honest completeness cost worth naming:
a legitimate disclosure record was silently absent from that one report because of this. Across
6,269 real announcement claims in this sample, this happened exactly once (0.016%). No other
claim, of any type, was rejected for any reason in this 2,000-event sample.

**Bottom line: 100% of claims that reached output were verified (0 fabrications, 0 unverified
claims); 1 claim was correctly withheld by design, for a real and now-documented reason.**

---

## Layer 2 — Classification performance (2026 hold-out, frozen thresholds)

**Not a sample of any size — the entire 2026 hold-out**, all 10,850 events with
`event_date >= 2026-01-01`, classified once, per the discipline above. Layer 1's 2,000-event
figure belongs to a separate, unrelated sample (the report-generation pipeline correctness check,
drawn from the full 2019-2026 catalogue) and has no bearing on Layer 2 or 3's population, which is
never subsampled: every hold-out event that has a computable outcome label at a given horizon is
included in that horizon's numbers. `UNEXPLAINED_ISOLATED` is real but genuinely rare in this
9-month window — 119 of 10,850 hold-out events (1.1%), which is why its per-band cells in the
table below sit at n=4-7 rather than being artificially thinned by sampling.

### Collapse rate by class × cap-band × horizon

Full 75-cell table (5 bands × 5 classes × 3 horizons) in
`data/processed/phase8_2026_outcomes.csv`; representative slice at the 90-session horizon:

| Band | GROUNDED | PARTIALLY_GROUNDED | UNEXPLAINED | UNEXPLAINED_ISOLATED | UNKNOWN_COVERAGE |
|---|---|---|---|---|---|
| Large | 74.1% [70.5,77.5] n=588 | 43.2% [35.8,50.9] n=162 | 85.9% [81.4,89.5] n=284 | 75.0% [30.1,95.4] n=4 | 75.4% [66.9,82.3] n=118 |
| Mega | 63.6% [59.8,67.2] n=648 | 39.6% [32.0,47.7] n=144 | 78.4% [72.4,83.4] n=213 | 28.6% [8.2,64.1] n=7 | 82.7% [73.1,89.4] n=81 |
| Micro | 77.9% [72.7,82.4] n=281 | 75.4% [70.7,79.6] n=350 | 90.6% [86.4,93.6] n=255 | 100.0% [51.0,100.0] n=4 | 71.5% [66.7,75.9] n=362 |
| Mid | 75.9% [72.2,79.3] n=565 | 70.7% [64.7,76.1] n=239 | 86.1% [81.9,89.5] n=317 | 57.1% [25.0,84.2] n=7 | 66.3% [59.0,72.9] n=175 |
| Small | 79.8% [75.6,83.5] n=396 | 76.5% [71.0,81.3] n=260 | 89.5% [85.6,92.5] n=306 | 20.0% [3.6,62.4] n=5 | 64.7% [59.0,70.1] n=278 |

`UNEXPLAINED_ISOLATED`'s cells are thin here (n=4-7 per band at 90d — a single ~9-month hold-out
period simply doesn't produce many of this already-rare class) — read these as directional at
best, not as a repeat of the 15/15-band-horizon confirmation Phase 7b ran on the full 2019-2026
population. The ordering `PARTIALLY_GROUNDED < GROUNDED < UNEXPLAINED` from Phase 7b holds in every
band with adequate n here too.

### Precision@20

Score = TRAIN-period (2019-2025) 90-session collapse rate for the event's own (classification,
cap_band) cell. **Caveat stated directly, not hidden:** this score has only 25 distinct values, so
"top 20" is an arbitrary 20 of 255 events tied at the maximum score (0.869), not a fine-grained
ranking — the coarseness is a real property of a 5-class × 5-band scoring scheme, not a computation
error.

| | n | Collapse rate | 95% CI |
|---|---|---|---|
| Arbitrary 20 of the max-score tier | 20 | 85.0% | [64.0%, 94.8%] |
| **Full max-score tier (the meaningful number)** | **255** | **90.6%** | **[86.4%, 93.6%]** |

#### Precision@20 under alternative continuous orderings, tested before publishing

A follow-up review asked whether the categorical (class, cap_band) score's precision@20 result was
an artifact of ranking by a variable known to carry no signal, and specifically asked for
z_score and volume_ratio orderings run side by side, with neither result dropped.

**Correction needed first, since it changes which feature the test is really about:** the AUC
figures the request cited (z_score 0.495-0.522; volume_ratio "the one feature that survived
stratification," 0.586-0.607) do not match this project's own published Phase 6 numbers. Checked
directly against `docs/phase6_signals.md`: `volume_ratio` is below 0.50 in every single reported
cut (pooled and by-band, both labels) and explicitly did NOT survive stratification ("does not
cleanly hold or collapse... close to a coin flip" in Small/Mid). `zscore_60d` is also consistently
below 0.50 — and Phase 6's own doc already flagged this exact "0.495-0.522" range once before as
not matching its real numbers. The feature that DID survive stratification, in Phase 6's own words
("does not degrade by band, unlike volume_ratio"), is `return_20d_context_only` /
`close_to_close_60d` (0.53-0.58 by band). Run anyway exactly as asked — z_score and volume_ratio,
neither dropped — plus `return_20d_context_only` in place of "the Phase 6 ensemble score" (never
persisted as a reusable artifact; refitting one was out of scope for this specific request).
Script: `scripts/phase8_precision_at_k_alternative_orderings.py`.

**Step 1 — which direction does TRAIN data actually support for each feature?** Determined
directly (rank-sum AUC on 2019-2025 data), not assumed. All three come back BELOW 0.50 for the
naive "high value predicts collapse" direction — meaning the true, TRAIN-validated relationship for
every one of them is inverted: a SMALLER initial move (lower |z-score|, lower volume_ratio, lower
|return_20d|) is what predicts a subsequent collapse, not a larger one. This matches Phase 6's own
already-published finding that momentum/volatility persistence predicts a move HOLDING, not
collapsing.

| Feature | TRAIN AUC (naive "high value → collapse" direction) | Empirically correct ranking |
|---|---|---|
| zscore_60d | 0.4420 | rank LOW \|z-score\| as more collapse-prone |
| volume_ratio | 0.4005 | rank LOW volume_ratio as more collapse-prone |
| return_20d_context_only | 0.2446 | rank LOW \|return_20d\| as more collapse-prone |

**Step 2 — precision@20 on the 2026 hold-out, each feature ranked in its own empirically-correct
direction** (n=6,049; a real top 20 this time, not a tied group — these are continuous scores):

| Ordering | Hits/20 | Precision | 95% CI |
|---|---|---|---|
| zscore_60d (low) | 18/20 | 90.0% | [69.9%, 97.2%] |
| volume_ratio (low) | 17/20 | 85.0% | [64.0%, 94.8%] |
| return_20d_context_only (low) | 19/20 | 95.0% | [76.4%, 99.1%] |
| *(for comparison: the categorical class×band score, above)* | 231/255 | 90.6% | [86.4%, 93.6%] |

Base rate on this subset: 74.1%. **All three continuous orderings, correctly directed, land at or
above the categorical score's own precision** — this distinguishes the two possibilities the review
asked for cleanly: the CLASS is not uninformative, but ranking direction matters enormously, and a
simple correctly-oriented single feature does at least as well as the categorical score on this
specific top-20 slice.

**Step 3 — what happens under the naive "high value = more suspicious" direction, ignoring what
TRAIN data says:** this is the exact failure mode the review warned about, and it is real —
**every single feature falls WELL below the 74.1% base rate when ranked the naive way:**

| Ordering (naive, always-descending) | Hits/20 | Precision | 95% CI |
|---|---|---|---|
| zscore_60d (high) | 4/20 | 20.0% | [8.1%, 41.6%] |
| volume_ratio (high) | 7/20 | 35.0% | [18.1%, 56.7%] |
| return_20d_context_only (high) | 1/20 | 5.0% | [0.9%, 23.6%] |

**Reported as a genuine finding, not discarded despite going against the "headline":** ranking any
of these three features by raw magnitude — the single most natural, intuitive thing to do with a
"how extreme was this move" number — gives precision far below random on this hold-out. The
project's own classifier never makes this mistake, because `momentum_high` is defined using the
TRAIN-validated direction (persistence predicts holding) rather than the naive one — but a reader
building a simpler system on top of these same raw features, using the intuitive direction, would
get a result actively worse than a coin flip. That is a real, load-bearing design choice this
evaluation now has direct evidence for, not an assumption.

**A follow-up review proposed reading this as "volume_ratio (live) vs. z_score (dead)" and adopting
volume_ratio as the default ordering downstream. The real numbers above do not support that
reading, and it is not adopted.** In the correctly-directed comparison, z_score (90.0%) and
return_20d_context_only (95.0%) both land AHEAD of volume_ratio (85.0%) — volume_ratio is not the
standout here. **The real finding is that DIRECTION, not feature choice, is what determines whether
any of these three looks useful**: every one of them scores 85-95% correctly directed and 5-35%
naively directed, the same pattern regardless of which feature. If a single default continuous
ordering is wanted for anything downstream, `return_20d_context_only` is the better-supported
choice on two independent grounds: it is the top scorer in this exact test (95.0%), and it is the
feature Phase 6's own real, published numbers identify as surviving cap-band stratification
(0.53-0.58 by band) — `volume_ratio` is not.

### Calibration (Brier score + binned table)

**How the "predicted probability" was derived, and what that means for how to read this section.**
The classifier outputs a category, not a probability — there is no model output here to calibrate
in the usual sense. The score plotted against outcomes below is each event's own (classification,
cap_band) cell's TRAIN-period (2019-2025) collapse rate, i.e. exactly the same table Precision@20
uses. **This makes calibration close to tautological, not an independent finding, and it is
reported that way rather than as evidence of a well-calibrated model:** if 2019-2025 and 2026 came
from the same stable distribution, a frequency measured on one part of it and evaluated on another
part would calibrate well almost by definition — that is what the frequency estimator is FOR. The
one genuinely informative part of this section is exactly where the tautology breaks: **the 2026
hold-out itself is the single meaningful calibration test this evaluation runs** — everything
about the score is fixed and known before 2026 is ever touched, so the ONLY thing this section can
actually discover is whether 2026 behaved like a stable continuation of 2019-2025 or not. It did
not (the systematic under-confidence documented below). A calibration table built this way cannot
show a WELL-calibrated system as a meaningful achievement (that would be closer to a definitional
near-certainty, given how the score itself is constructed); it CAN, and did, show a real, dated
deviation from the training period's own base rate — which is exactly what the one non-tautological
test available here was capable of finding.

**Brier score: 0.2024** (n=6,049 events with a known 90-session outcome; 0 = perfect, 1 = perfectly
wrong). Better than predicting a flat 0.5 for everyone (0.25) — but see Layer 3 below for a more
demanding, and more honest, comparison: predicting this hold-out's own true base rate for every
event beats this number too. The comparison worth trusting is the RANKING the score implies, shown
directly in the calibration table's own ordering (below) and in Layer 3's baseline table.

| Predicted score bin | n | Mean predicted | Observed | 95% CI |
|---|---|---|---|---|
| [0.2, 0.4) | 144 | 0.366 | 0.396 | [0.320, 0.477] |
| [0.4, 0.6) | 3,482 | 0.538 | 0.701 | [0.685, 0.716] |
| [0.6, 0.8) | 1,545 | 0.682 | 0.783 | [0.762, 0.803] |
| [0.8, 1.0) | 878 | 0.835 | 0.886 | [0.863, 0.905] |

**Reading this plainly: the system is systematically UNDER-confident in 2026, not over-confident.**
Every bin's observed collapse rate exceeds its mean predicted rate, by a widening margin in the
higher bins. This is consistent with, not contradictory to, a finding already on record
(`docs/phase6_signals.md`: "the raw collapsed label swings 50.6%-74.1% by year — it was tracking
market drift, not move authenticity") — 2026 appears to have run at a structurally higher collapse
rate than the 2019-2025 training period the scores were derived from. This is a real, disclosed
limitation of frequency-based calibration against a non-stationary base rate, not a claim that the
underlying ranking is wrong (the *ordering* implied by the scores still tracks observed outcomes
correctly bin-to-bin — 0.396 < 0.701 < 0.783 < 0.886 — only the absolute level is off).

### Lead time to subsequent surveillance flag

**A correction before the numbers, since a follow-up review cited a median of 187 sessions and
claimed it was dragged long by events years before an unrelated flag:** that figure does not match
this evaluation's real, persisted output (`data/processed/phase8_lead_time.csv`) — the real overall
median is 14 sessions, and the real maximum in the whole table is 168 sessions, not "years." A
"years later" tail is structurally impossible here regardless: this measurement is scoped to the
2026 hold-out only (event dates spanning roughly 8.5 months, through the data's own most recent
bhavcopy on 2026-09-15), so no lead time in this table CAN exceed the width of that window. That is
itself a real, disclosed scope limit (stated in the new subsection below), not a defense of a
number that was never produced.

**All 10,850 hold-out events fall into exactly three buckets, reported here as requested rather
than only the subset that produced a lead time:**

| Bucket | n | % of hold-out |
|---|---|---|
| Already under surveillance AT event_date — not a warning, correctly excluded from "lead time" | 385 | 3.5% |
| Flagged later; a real, computable lead time | 2,906 | 26.8% |
| Not flagged as of the data's own most recent date (2026-09-15) — may still be flagged later, unknown | 7,551 | 69.6% |
| Flag found but the exact session gap wasn't computable (a real, small trading-calendar data gap, 2 symbols) | 8 | 0.1% |

The first bucket is the direct answer to "state that count plainly": 385 events (3.5%) were already
under surveillance when this system saw them — for those, there is nothing to warn about, and they
are excluded from every lead-time number below by construction, not folded in as if they were
zero-session warnings. The 69.6% "not yet flagged" bucket is NOT evidence those moves are
unremarkable — the hold-out window is short, and the exchange may simply not have acted (or not
yet, as of this data's own cutoff) inside it; this bucket is honestly unresolved, not silently
counted as either a hit or a miss.

**Full percentile spread of the 2,906 events with a real lead time**, not just the median:

| | n | p10 | p25 | p50 | p75 | p90 | max |
|---|---|---|---|---|---|---|---|
| **Overall** | 2,906 | 2 | 3 | 14 | 52 | 95 | 168 |

**Is it bimodal?** Not in the classic two-separate-peaks sense — but it is heavily front-loaded,
not a smooth spread, which matters for the same reason bimodality would: **44.4% (1,290/2,906) of
all real lead times fall within the first 10 sessions**, and 56.3% (1,636/2,906) within the first
20, then the count decays session-by-session with no second peak (322 in [10,20), 203 in [20,30),
142 in [30,40), continuing to decay through the 160s). Read plainly: the near-term cluster is real
and large; the "tail" is a genuine decay, not a separate later population.

**Within a plausible near-term window (≤120 sessions, roughly six months):** 2,763 of 2,906 events
with a lead time (95.1%) fall inside it; 143 (4.9%) take longer, up to the real maximum of 168.
Restricting to just this ≤120-session subset barely moves the center at all (subset median 12
sessions, subset p25 3 — both close to the full pool's 14/3) precisely because the subset already
contains 95.1% of the data; there is no separate, meaningfully-different "near-term population" to
isolate here beyond what the full distribution already shows. There is no multi-year tail to
explain away either, because the window this evaluation can observe is itself under a year wide —
a real scope limit, not a favorable result.

**The defensible claim, scoped to what the near-term cluster actually shows:** of the 2,906 events
with a computable lead time, a plurality (44.4%) were followed by an exchange surveillance flag
within 10 real trading sessions, and 95.1% within roughly six months. This is a "we saw it early,
relative to when the exchange acted" result for the near-term cluster specifically — it is not a
claim this system predicts flags nine months out, and the median (14 sessions) undersells how
front-loaded the real distribution is just as much as a naive "years later" framing would have
oversold its tail.

**By classification** (same n=2,906 pool, split):

| | n | p10 | p25 | p50 | p75 | p90 | max |
|---|---|---|---|---|---|---|---|
| GROUNDED | 1,430 | 2 | 3 | 12 | 47 | 91 | 167 |
| PARTIALLY_GROUNDED | 845 | 2 | 3 | 9 | 48 | 86 | 160 |
| UNEXPLAINED | 574 | 3 | 7 | 33 | 68 | 118 | 168 |
| UNEXPLAINED_ISOLATED | 33 | 2 | 3 | 10 | 47 | 62 | 82 |
| UNEXPLAINED_UNKNOWN_COVERAGE | 24 | 1 | 2 | 3 | 5 | 12 | 83 |

`UNEXPLAINED` events (no substantive disclosure found, low momentum) took distinctly longer to get
externally flagged than `GROUNDED` or `PARTIALLY_GROUNDED` ones across the whole spread, not only
at the median (p25 7 vs. 3/3, p50 33 vs. 12/9, p90 118 vs. 91/86) — this system's own classification
is separating exactly this profile of move earlier than the exchange's own mechanism did, on real,
already-realized 2026 outcomes. This is a lead-time result, not a claim about why the exchange
acted when it did — the exchange's own criteria and process are not observed by this project, only
the dates.

### A real scope limit on this measurement

Stated once, applying to every number in this subsection: because Phase 8's hold-out discipline
restricts this measurement to 2026 events only, no lead time here can exceed roughly the width of
the 2026 hold-out window itself (~180 trading sessions). A genuine long-tail pattern (events flagged
a year or more later) — if one exists in the full multi-year history — is structurally invisible to
this specific measurement. This evaluation does not claim one doesn't exist; it only reports what
can be seen inside the window the hold-out discipline allows it to look at.

---

## Layer 3 — Baselines, all five, identical 2026 hold-out set (n=6,049, 90-session horizon)

n=6,049 is not a sample either — it is the full 10,850-event hold-out restricted to events with a
computable 90-session outcome as of today's data (2026-09-15's most recent bhavcopy), the same
restriction Layer 2's 90-session numbers use. All five baselines score the identical 6,049 events.

**On "volume_ratio ordering throughout":** none of these five baselines are built on a raw
continuous-feature ordering in the first place, so there is no z_score-vs-volume_ratio choice to
make here. Baseline 3 (disclosure tier alone) and baseline 4/5 (the classifier) are each scored by
their OWN natural categorical TRAIN-period rate — (disclosure_tier, cap_band) and (classification,
cap_band) respectively — exactly as Layer 2 already defined them. The z_score/volume_ratio/
return_20d comparison above is a separate side analysis of Layer 2's precision@20 ranking
specifically, and does not change how any Layer 3 baseline is constructed.

| Baseline | Brier score | Precision (max score tier) | n (tier) |
|---|---|---|---|
| 1. Random | 0.3328 | 0/1 = 0.0% [0.0%, 79.3%] | 1 |
| 2. Naive threshold (\|return_1d\| > 10%) | 0.6553 | 929/1,337 = 69.5% [67.0%, 71.9%] | 1,337 |
| **3. Disclosure tier alone** | 0.2091 | 285/362 = 78.7% [74.2%, 82.6%] | 362 |
| **4. Deterministic classifier (rules, no agents)** | **0.2024** | **231/255 = 90.6% [86.4%, 93.6%]** | 255 |
| 5. Full agent system | *(identical to 4 by construction — see below)* | | |

Base rate (unconditional 90-session collapse rate across the whole hold-out): **74.1%** (n=6,049).

**The headline finding, stated as instructed, not buried:** the full classification system beats
disclosure-tier-alone on this hold-out. Brier 0.2024 vs. 0.2091 (a real if modest gain), and at the
top-scored tier the gap is larger and the confidence intervals do not overlap: 90.6% [86.4%, 93.6%]
vs. 78.7% [74.2%, 82.6%]. Disclosure tier alone is still clearly the dominant single input — it
already beats the naive and random baselines by a wide margin, exactly as Phase 6/7b's own findings
said it should — but the momentum and isolation axes this project added on top of it are not dead
weight on this hold-out; they measurably separate a tighter, more precise top tier than disclosure
tier can alone.

**That relative win needs the next paragraph's caveat immediately, not after a comfortable gap:**
"beats disclosure tier alone" is a comparison between two imperfect scores, and neither of them
beats a trivial baseline that uses no per-event information whatsoever. Read on before treating
0.2024 as a good absolute number.

**A second failure to report, found while assembling this table, not before:** predicting the flat
population base rate (74.1%) for every single event, with NO per-event information at all, gives
Brier = p(1-p) = 0.741 x 0.259 ≈ **0.192** — better (lower) than every real baseline in the table
above, including the full classifier (0.2024) and disclosure tier alone (0.2091). A strategy that
uses no information whatsoever beats this project's own classifier on raw Brier score.

This is not a contradiction of the calibration section above — it is the same finding restated as
a single number. The calibration table showed every predicted-probability bin under-predicting
2026's actual collapse rate (e.g. mean predicted 0.538 against an observed 0.701 in the largest
bin); a constant prediction fixed AT the true 2026 base rate cannot make that specific error,
because it never predicts anything but the (retrospectively known) right average. The classifier's
scores are TRAIN-derived and 2026 ran hotter than train — exactly the non-stationary-base-rate risk
named in the limitations section. **Stated plainly: on raw Brier score alone, this evaluation's own
classifier does not beat "know nothing except the year's true average and predict that."** Its real,
positive contributions in this evaluation are the top-tier precision (90.6%, clearly above the
74.1% base rate, CI non-overlapping with disclosure-tier-alone's 78.7%) and the lead-time result —
both of which depend on the classifier's RANKING/GROUPING being informative, which the calibration
table confirms (0.396 < 0.701 < 0.783 < 0.886, correctly ordered) even while the absolute
probability LEVEL is miscalibrated. Random scoring (0.3328) and the naive threshold (0.6553) are
both worse than the constant-base-rate strategy too, for the same underlying reason in weaker form
(random) or a different one (naive: it flags nearly every event as certain to collapse, and is
punished hard by the ~26% that don't).

**Baseline 4 vs. 5:** not independently re-run at full 10,850-event scale (`Synthesis.render()`
calls the same `classify_event()` rule regardless of which claims the Adversary accepted or
rejected, so the two are identical by construction GIVEN the same thresholds). A real, seeded
100-event spot-check running the actual `MultiAgentOrchestrator` found 99/100 matched; the one
mismatch is the threshold-vintage effect described at the top of this document, not a logic
difference between "with agents" and "without." If the frozen thresholds were ever deployed to
production (they are not; production intentionally keeps using the full-history thresholds), 4 and
5 would match on every event.

---

## A note on threshold vintages

Documented once, referenced from both places it matters (Layer 3's baseline 4/5 note, and the
top-of-document failure report): this evaluation's frozen thresholds
(`data/processed/phase8_frozen_thresholds.json`, 2019-2025 only) and the live system's production
thresholds (`data/processed/classification_thresholds.json`, full history) are close but not
identical (Mid-band momentum median 0.1195 vs. 0.1161; isolated co-movement cutoff 35 vs. 36).
Neither is "wrong" — they answer different questions (this evaluation's genuine walk-forward test
vs. a live system using everything it currently knows) — but a reader comparing this document's
numbers against a live report generated today should expect occasional small classification
differences right at a band-median boundary, and now knows why.

---

## Limitations (written directly, not deferred to a future phase)

- **What this does not measure.** Nothing here evaluates whether a `GROUNDED` disclosure was
  actually proportionate to the move's magnitude (the proportionality gap named in
  `GROUNDED_LIMITATION_NOTE`, Phase 7c) — Layer 2's collapse-rate and calibration numbers are blind
  to that distinction entirely, since two GROUNDED events with wildly different disclosure/move
  ratios are scored identically here.
- **Where the labels are weak.** `collapsed_Nd` is itself a proxy for "the move was genuine,"
  built on this project's own price-reversion definition (Phase 6) — not a regulatory or expert
  determination of anything. A move that held for reasons this project cannot see (broad market
  conditions, sector rotation) scores identically to one that held because the disclosure was real
  and material. The lead-time result is comparatively cleaner evidence, because it is anchored to
  the exchange's own real, independent action (an ASM/GSM placement), not to this project's own
  price-based proxy.
- **What could make these numbers look better than they are.** (1) The calibration under-
  confidence finding above means a naive "just scale up the predicted probabilities" fix would
  mechanically improve the Brier score without adding any real information — flagged explicitly so
  it is never done and called an improvement. (2) The precision@20/max-tier numbers use a score
  DERIVED FROM 2019-2025 outcomes and evaluated on 2026 outcomes that are not independent of the
  same underlying market/regulatory regime — a genuinely out-of-regime year (a period NSE changed
  its own surveillance criteria, for instance) would look like a Phase 8 failure or success for
  reasons having nothing to do with this classifier. (3) `UNEXPLAINED_ISOLATED`'s thin per-band
  cells in Layer 2 (n=4-7) mean any single-band number for that class in this hold-out period is
  not something to build a further claim on; the class-level (not per-band) pattern is more
  trustworthy here given the small n.
- **Precision@k's coarseness.** Stated already above, repeated here because it is a real
  methodological limit, not a footnote: a 5-class × 5-band score has only 25 possible values.
  "Precision@20" as literally specified is close to meaningless with this score (an arbitrary
  20-of-255 tie); the full-tier number is the one to trust, and any future refinement that wants a
  genuine fine-grained ranking will need a continuous score, not this project's categorical one.
