# Phase 7b — event classification design

Status: rules designed and validated against real data across two rounds. Not yet implemented as
a production module/agent, and no report has been generated — per instruction, this stops after
showing the design and its real class distribution.

## Two axes, one descriptive carve-out — not a flat mapping of disclosure tier to class

**Axis 1 — Disclosure tier** (`src/signals/disclosure_classification.py`, real, already built):
SUBSTANTIVE / ROUTINE_ONLY / NONE / UNKNOWN_COVERAGE (the latter kept as its own honest label for
the 8,294 events whose symbol has no cached announcement data — "not checked" must never read as
"checked, found nothing").

**Axis 2 — Momentum persistence**: `abs(return_20d_context_only)` vs. its real per-cap-band
median (Phase 6's strongest validated signal — high persistence predicts a move holds, low
predicts it reverses):

| Band | Median abs(return_20d) |
|---|---|
| Micro | 0.0918 |
| Small | 0.1133 |
| Mid | 0.1161 |
| Mega | 0.1249 |
| Large | 0.1251 |

**A third, purely descriptive field — same-date co-movement** — used only for one specific,
narrowly-defined carve-out (`UNEXPLAINED_ISOLATED`, below), never as a general classification
axis. Deliberately not folded into the two-axis system: Phase 6 found co-movement carries no
predictive power for whether a move holds, so it is used here to describe what was *observed*
("this move happened alongside few others that day"), never to imply a verdict.

## Round 1 → round 2: SIGNATURE_PRESENT retired

The original design's fourth class, `SIGNATURE_PRESENT`, was `NONE disclosure + low momentum` —
two conditions, not the four the round-2 critique described (this design never gated on volume or
market-cap band; those were always separate reported fields, not part of any class definition).
Retired anyway, for the more important reason: **the name implied a verdict.** "SIGNATURE_PRESENT"
reads as "a signature of manipulation is present" regardless of any disclaimer attached to it —
exactly what CLAUDE.md invariant 12 forbids. Replaced with **`UNEXPLAINED_ISOLATED`**, which
describes what was measured, not what it implies:

**`UNEXPLAINED_ISOLATED`** = disclosure tier NONE **and** `same_date_event_count` below 36 (the
real p25 of that field across all 75,300 catalogued events — "isolated" relative to this
catalogue's own real distribution, not a round number). Exactly two conditions.

**Design choice within the NONE-disclosure tier, stated so it can be corrected:** co-movement is
checked *first* — a NONE-disclosure event with low co-movement is `UNEXPLAINED_ISOLATED`
regardless of its own momentum. A NONE-disclosure event that is *not* isolated (co-movement at or
above the threshold) falls back to the momentum-based split carried over from round 1: high
momentum → `PARTIALLY_GROUNDED`, low momentum → plain `UNEXPLAINED`. The `ROUTINE_ONLY` branch is
unchanged from round 1.

## The full rule table

| Disclosure | Co-movement | Momentum | → Class |
|---|---|---|---|
| SUBSTANTIVE | — | — | **GROUNDED** |
| ROUTINE_ONLY | — | HIGH | **PARTIALLY_GROUNDED** |
| ROUTINE_ONLY | — | LOW | **UNEXPLAINED** |
| NONE | isolated (<36) | — | **UNEXPLAINED_ISOLATED** |
| NONE | not isolated | HIGH | **PARTIALLY_GROUNDED** *(open judgment call, see below)* |
| NONE | not isolated | LOW | **UNEXPLAINED** |
| UNKNOWN_COVERAGE | — | — | **UNEXPLAINED_UNKNOWN_COVERAGE** |

**Still an open judgment call, not settled unilaterally:** `NONE disclosure + not isolated + high
momentum` → `PARTIALLY_GROUNDED`. No disclosure was found, but the move shows real sustained
persistence (Phase 6's own validated signal that this predicts genuineness). Calling it
`UNEXPLAINED` would ignore that signal; calling it `GROUNDED` would claim a disclosure that wasn't
found. Flagged for explicit sign-off before this is final.

## Real class distribution — all 75,133 usable events

| Class | Count | Share |
|---|---|---|
| GROUNDED | 32,978 | 43.9% |
| PARTIALLY_GROUNDED | 16,139 | 21.5% |
| UNEXPLAINED | 15,086 | 20.1% |
| UNEXPLAINED_UNKNOWN_COVERAGE | 8,294 | 11.0% |
| UNEXPLAINED_ISOLATED | 2,636 | **3.5%** |

`UNEXPLAINED_ISOLATED` lands inside the requested 2-8% band. Every class clears the 2%-50% sanity
bound. `scripts/design_classification_rules.py` is the design-check script that produced this —
not the production classifier; re-run it directly to re-validate any future threshold change
before touching the real module.

## GROUNDED's real limitation, stated explicitly rather than left implicit

`GROUNDED` is gated **entirely** on disclosure tier — no signal input at all. This is defensible
(a substantive disclosure genuinely is the explanation a report should lead with), but it means
`GROUNDED` says nothing about whether the *size* of the move was proportionate to the news. A 15%
move on a disclosure amounting to 0.3% of revenue is `GROUNDED` under this design, identically to
a 15% move on a disclosure that plausibly justifies it — the class does not distinguish them. This
is the specific gap where a disproportionate reaction to a real-but-minor disclosure hides. No
proportionality check exists in this design; a future refinement could compare move magnitude
against disclosure type/materiality, but that is not attempted here and is not implied by the
`GROUNDED` label as currently defined.

**Since Phase 7c, this limitation is stated in the report's own output, not only here.**
`GROUNDED_LIMITATION_NOTE` (`src/classification/event_classifier.py`) is attached to
`EventReport.classification_notes` whenever `classification == GROUNDED` -- a reader sees it at
the point of classification, alongside the full list of disclosures actually found (date,
category, per-row substantive/routine tier, and any available description text), so they can
judge proportionality directly from the evidence rather than trust the class label alone.

## Every event reports its signal fields, regardless of class

Per instruction: the classification is a coarse summary; the underlying fields are the evidence,
and must be on every event's output so a reader can re-derive their own thresholds rather than
trust this project's conjunction. Required on every report, not gated by class:

- `volume_ratio`, `delivery_pct` / `delivery_pct_percentile_60d`, `close_to_close_60d`,
  `zscore_60d` — all already computed per event (Phase 5/6).
- `same_date_event_count` (co-movement) — already computed (Phase 6, `clustering.csv`).
- `cap_band` — already computed (5-way quintile, Phase 6 methodology).
- ASM/GSM status *as-of* the event date — already available (`current_surveillance_state()`,
  Phase 5).
- **Lead time to any subsequent flag** — **not yet built.** `current_surveillance_state()`
  answers "what was the status as of this date"; it does not answer "how many sessions later did
  the exchange first flag this symbol, if it wasn't already flagged." This needs a new, small
  query (first ASM/GSM transition strictly after `event_date`, if any) before the Disclosure/
  Surveillance agent can report it. Named here so it is not silently missing from the eventual
  report.

## Provenance note — to be rendered into every report's output, not just this doc

Fixed, deterministic text block, independent of whether a provider is configured:

> *Classification uses this project's own thresholds (disclosure tier, momentum persistence vs.
> real per-band medians, co-movement vs. this catalogue's own distribution) — not a validated
> predictor. Phase 6 measured the combined signal ceiling at 0.611-0.70 held-out. UNEXPLAINED /
> UNEXPLAINED_ISOLATED mean "no substantive disclosure found, signals in these ranges" — not
> "likely manipulated."*

## Collapse rate by class -- measured after implementation, before any report generation

Per instruction, one measurement was run before generating any report: does the classification
separate on real outcomes (`collapsed_30d/60d/90d`, computed fresh for this measurement --
Phase 6's own `compute_outcome_labels.py` only persisted the fixed 90-session definition), and
does that separation survive stratifying by market-cap band the way Phase 6's own Simpson's-
paradox finding says a pooled comparison alone cannot be trusted to show.
`scripts/measure_collapse_rate_by_class.py` is the measurement; full cell-level output in
`data/processed/collapse_rate_by_class.csv`.

**Pooled result, all three horizons, real numbers:**

| Class | n (90d) | 30d | 60d | 90d |
|---|---|---|---|---|
| PARTIALLY_GROUNDED | 15,184 | 30.8% | 41.5% | 47.3% |
| GROUNDED | 30,058 | 45.9% | 54.1% | 58.9% |
| UNEXPLAINED_ISOLATED | 2,510 | 49.4% | 58.4% | 62.7% |
| UNEXPLAINED_UNKNOWN_COVERAGE | 7,486 | 51.5% | 58.7% | 62.4% |
| UNEXPLAINED | 14,174 | 71.3% | 78.3% | 81.1% |

**The separation survives stratification.** Checked across all 5 cap bands (Micro/Small/Mid/Large/
Mega) and all 3 horizons -- 15 stratified comparisons -- the ordering
`PARTIALLY_GROUNDED < GROUNDED < UNEXPLAINED` holds in every single one, with no exceptions and no
band where the gap collapses to noise. Smallest cell in any stratified comparison is n=317
(Mega/UNEXPLAINED_ISOLATED/90d); every cell used above has n well into the hundreds or thousands.
This is not the pooled-comparison composition artifact Phase 6's Simpson's-paradox finding warned
about -- the gap is real within bands, not an artifact of, e.g., UNEXPLAINED being micro-skewed
against a GROUNDED population that's Large/Mega-skewed.

**Two honest caveats, stated so this isn't oversold:**

1. **PARTIALLY_GROUNDED's low collapse rate is substantially circular, not new evidence.** The
   class is gated on `momentum_high` (`abs(return_20d_context_only)` at/above its cap-band
   median) -- exactly the feature Phase 6 already validated as the project's strongest predictor
   of a move holding. Finding that PARTIALLY_GROUNDED events collapse less often is close to
   re-confirming Phase 6's own already-measured momentum signal, filtered through a class that
   was partly defined using it. It is genuine and consistent, not fabricated, but it should not be
   read as an independent new finding.
2. **GROUNDED vs. UNEXPLAINED is the more interesting, non-circular part.** `GROUNDED`'s
   definition never touches momentum or co-movement -- it is gated on disclosure tier alone (see
   the GROUNDED-limitation note above). That a disclosure-tier-only class still shows a real,
   band-consistent ~20-25-percentage-point lower collapse rate than `UNEXPLAINED` is a genuine
   signal-shaped result: substantive disclosure correlates with a move holding, independent of the
   momentum gate used elsewhere in this design.

### Confidence intervals on every cell, and a correction to the framing above

A follow-up review asked for 95% confidence intervals (Wilson score, correct at small n and near
0/1) on every cell of the stratified table, flagged a possible Small-band monotonicity break
(UNEXPLAINED dipping below PARTIALLY_GROUNDED), flagged Mega-band cells as too thin to report
(cited n=45 and n=17), and proposed reframing the finding as "disclosure tier carries the signal;
isolation is a modest refinement, not a distinct phenomenon" because the three non-grounded
classes supposedly sit within a few points of each other.

**None of those three specific claims match this project's own data**
(`scripts/analyze_collapse_rate_confidence_intervals.py`, run directly against
`data/processed/collapse_rate_by_class.csv` -- the same real, already-verified per-event rows
behind the table above, this time with 95% Wilson intervals on all 75 cells: 5 bands x 5 classes x
3 horizons). Recorded plainly rather than silently reconciled, per this project's verification
standard:

- **No cell is thin.** The smallest cell in the entire table is n=317 (Mega/UNEXPLAINED_ISOLATED/
  90d); every other cell is in the hundreds to thousands. Nothing resembling n=45 or n=17 exists
  in this data at any horizon or band. `INSUFFICIENT_N = 50` was applied as an explicit floor and
  zero cells fell below it.
- **No monotonicity break exists.** PARTIALLY_GROUNDED vs. UNEXPLAINED was checked directly across
  all 5 bands x 3 horizons (15 comparisons) -- UNEXPLAINED is higher than PARTIALLY_GROUNDED in
  every single one, by a minimum gap of ~30 percentage points (Small/30d: 34.0% vs. 75.7%). No
  reversal, in Small or anywhere else.
- **The three non-grounded classes are NOT clustered together -- they are the most clearly
  separated part of the table.** In all 15 band/horizon combinations, PARTIALLY_GROUNDED vs.
  UNEXPLAINED_ISOLATED, PARTIALLY_GROUNDED vs. UNEXPLAINED, and UNEXPLAINED_ISOLATED vs.
  UNEXPLAINED all have disjoint 95% CIs -- every pairwise distinction among the three holds up.

**What the data actually shows, and it points the opposite direction from "disclosure tier alone
carries the signal":** in every one of the 15 band/horizon combinations, it is **GROUNDED vs.
UNEXPLAINED_ISOLATED specifically** whose CIs overlap -- the one pair in the whole table that is
NOT reliably distinguishable. GROUNDED is reliably distinguishable from both PARTIALLY_GROUNDED
and UNEXPLAINED; UNEXPLAINED_ISOLATED sits statistically indistinguishable from GROUNDED instead
of from the other two NONE-disclosure-tier classes it shares a disclosure tier with.

The likely reason, stated as a compositional explanation rather than a new predictive claim (co-
movement isolation was deliberately kept out of the momentum axis -- Phase 6 found it carries no
predictive power on its own, see the design section above): `UNEXPLAINED_ISOLATED` is the one
class whose definition never checks `momentum_high` -- isolation is tested first in the NONE-tier
branch, so this class mixes both high- and low-momentum events. `GROUNDED` is the OTHER class
that never checks momentum. Two momentum-agnostic class definitions landing in a similar middle
range, while the two momentum-gated classes (PARTIALLY_GROUNDED, UNEXPLAINED) diverge sharply
toward the extremes, is consistent with momentum being the dominant driver of where a cell sits --
not evidence that isolation newly acquired predictive power Phase 6 didn't find.

**Representative cells (90-session horizon, Wilson 95% CI):**

| Band | GROUNDED | PARTIALLY_GROUNDED | UNEXPLAINED_ISOLATED | UNEXPLAINED |
|---|---|---|---|---|
| Large | 55.2% [54.0, 56.4] (n=6,613) | 41.4% [39.7, 43.2] (n=2,950) | 57.9% [53.0, 62.6] (n=399) | 78.8% [77.3, 80.2] (n=2,971) |
| Mega | 54.3% [53.2, 55.5] (n=7,697) | 36.9% [35.0, 38.8] (n=2,558) | 59.0% [53.5, 64.3] (n=317) | 74.3% [72.5, 75.9] (n=2,549) |
| Micro | 65.8% [64.4, 67.3] (n=4,272) | 58.8% [57.1, 60.5] (n=3,233) | 70.7% [67.1, 74.0] (n=658) | 87.2% [85.9, 88.5] (n=2,525) |
| Mid | 60.2% [59.0, 61.5] (n=6,042) | 46.9% [45.2, 48.7] (n=3,205) | 57.9% [53.6, 62.0] (n=522) | 81.5% [80.1, 82.8] (n=3,062) |
| Small | 62.9% [61.6, 64.2] (n=5,434) | 49.9% [48.2, 51.6] (n=3,238) | 63.2% [59.3, 66.9] (n=614) | 83.8% [82.4, 85.1] (n=3,067) |

Full 75-cell table (all 3 horizons, all pairwise distinguishability checks) is the direct output of
`scripts/analyze_collapse_rate_confidence_intervals.py`, not reproduced in full here.

**Revised framing:** disclosure tier is not a clean single axis that alone explains the ordering.
Momentum (which two of the four classes are gated on, and two are not) appears to be the dominant
driver of where a class's collapse rate lands; isolation, specifically, does not behave as a small
refinement on top of disclosure tier -- it behaves like a momentum-agnostic class that happens to
land near GROUNDED, not near its own disclosure-tier siblings.

### Decision: keep GROUNDED and UNEXPLAINED_ISOLATED as separate classes, state the finding explicitly

A follow-up review asked, given the indistinguishability just measured, whether to (a) merge the
indistinguishable pair into one class, with the distinction surviving only as a reported field, or
(b) keep them separate on the grounds that they describe genuinely different observations, with
the indistinguishability stated prominently in the report OUTPUT rather than a footnote. The
review's own lean was (b) -- but framed against PARTIALLY_GROUNDED/UNEXPLAINED, which is the wrong
pair per the measurement above.

Applied to the real indistinguishable pair (GROUNDED, UNEXPLAINED_ISOLATED), the case for (b) is
stronger than it would have been for the originally-proposed pair, not weaker: these two classes
sit on OPPOSITE ends of the disclosure-tier axis -- a substantive disclosure was found vs. none at
all. Merging them would hide exactly the distinction this classification exists to preserve (what
was FOUND), and the fact that they happen to share a similar 90-day collapse rate does not make
"a real disclosure existed" and "no disclosure was found" the same observation. **Decision: (b),
kept separate.**

Implemented directly in the classifier, not just this doc: `src/classification/
event_classifier.py` defines `INDISTINGUISHABLE_PAIR = {GROUNDED, UNEXPLAINED_ISOLATED}` and
`INDISTINGUISHABLE_PAIR_NOTE`; `SynthesisAgent.render()` (`src/agent/synthesis.py`) attaches that
note to `EventReport.classification_note` whenever an event's final classification is GROUNDED or
UNEXPLAINED_ISOLATED -- rendered at the point of classification in the report's own output
structure, never a footnote a reader could miss, and `None` for every other class. Verified against
real data (`tests/test_orchestrator_real_data_guard.py` covers both classes) and unit-tested
directly (`tests/test_synthesis.py`), including that the note text itself is banned-term-lint
clean. Exact text:

> *GROUNDED and UNEXPLAINED_ISOLATED are not distinguishable by 30/60/90-session collapse rate in
> any market-cap band measured (95% confidence intervals overlap in all 5 bands and all 3 horizons
> checked). They differ in what was found -- a substantive disclosure versus none at all -- not in
> what followed.*

**What this is not:** a collapse-rate gap of this size, even where consistent, is small next to the
overall noise -- every class still collapses in more than a third of its events at every horizon,
including the "best" class (PARTIALLY_GROUNDED, 30.8-47.3%). This is separation, not prediction --
fully consistent with Phase 6's measured 0.611-0.70 AUC ceiling, not a contradiction of it. No
threshold in this design was tuned to produce this result; it is what the already-approved rules,
applied and then measured, actually gave. Per instruction, this is recorded here regardless of
which way it came out, and belongs in report output as population base-rate context (e.g. "GROUNDED
events collapse within 90 sessions in 58.9% of cases on this catalogue, n=30,058 -- a population
base rate for the class, not a probability for this specific event"), not as a claim about any one
event's authenticity.

## Still open before implementation

- The `NONE + not-isolated + high-momentum → PARTIALLY_GROUNDED` judgment call (above).
- The lead-time-to-subsequent-flag computation (above) — needed before every event's required
  field set is actually available.
- No production classifier module, agent, or report renderer has been written. This doc and
  `scripts/design_classification_rules.py` are the design and its validation only.
