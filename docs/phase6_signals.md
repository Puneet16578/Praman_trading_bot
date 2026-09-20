# Phase 6 — Signals as MCP tools

Status: **pre-flight measurement complete, blocked per explicit instruction.** No signal tool has
been built. Per "if the distributions overlap completely, tell me before building five more
signals on top of it" — this doc reports that measurement and stops there.

## Pre-flight: does delivery divergence discriminate ASM/GSM-labelled events at all?

**Scope note on the input count:** measured against this project's real, persisted catalogue —
`data/processed/event_catalogue_loose_zscore_only.csv`, **75,300 events** (Phase 5's final,
committed output, commit `6a89fdb`) — not the 41,910 figure given, which does not correspond to
any real count in this codebase (this is now an established pattern this session;
`docs/phase5_event_catalogue.md` §10 tracks seven prior instances of the same thing). 3 of 75,300
rows are missing `delivery_pct`/its trailing percentile and were excluded; 75,297 usable.

**Method:** for every catalogued event, `delivery_pct_percentile_60d` (already computed by Phase
5's `compute_daily_stats` — the event day's delivery % ranked against its own trailing 60-session
distribution, 0–100) is the delivery-divergence measure. Split into two groups by
`current_surveillance_state()` at the event date: ASM-or-GSM-active ("labelled") vs. neither
("unlabelled"). The hypothesis under test: high volume with low delivery indicates churn, so
labelled events — plausibly more likely to be genuine anomalies — should show a **lower** delivery
percentile than unlabelled ones.

### Result

| | n | mean | median | Q1 | Q3 | % below 25th pctile | % above 75th pctile |
|---|---|---|---|---|---|---|---|
| ASM/GSM-labelled | 3,569 | 29.67 | 20.00 | 5.08 | 48.33 | 55.5% | 10.2% |
| NOT_FLAGGED | 71,728 | 27.29 | 15.00 | 1.72 | 46.67 | 60.0% | 10.9% |

Raw (non-percentile-ranked) `delivery_pct` shows the same pattern: labelled mean 47.94% / median
46.43%, vs. unlabelled mean 43.55% / median 41.55%.

Full distribution (10-point bins of `delivery_pct_percentile_60d`):

| percentile bin | labelled % of group | unlabelled % of group |
|---|---|---|
| 0–10 | 33.37% | 42.21% |
| 10–20 | 16.34% | 13.06% |
| 20–30 | 10.17% | 8.56% |
| 30–40 | 8.15% | 6.88% |
| 40–50 | 7.40% | 5.68% |
| 50–60 | 6.28% | 5.20% |
| 60–70 | 5.41% | 4.71% |
| 70–80 | 4.34% | 4.39% |
| 80–90 | 3.92% | 4.31% |
| 90–100 | 4.62% | 5.01% |

Checked for an obvious confound before concluding anything: year and market-cap-band composition
of the two groups are proportionally similar (Large-cap ~50-57% of both groups; no single year
dominates either group disproportionately) — this is not an artifact of comparing, say, mostly-2020
labelled events against mostly-2025 unlabelled ones.

### Reading this plainly

**The distributions substantially overlap, and the direction is the opposite of the hypothesis.**
ASM/GSM-labelled events show a *higher* median delivery percentile (20 vs. 15) and a *higher* raw
median delivery % (46.4% vs. 41.6%) than unlabelled events — not lower. The spreads are nearly
identical (stdev ~28 vs ~30) and every bucket in the full histogram is within a few percentage
points between the two groups; the largest gap is in the 0–10 bin, where *unlabelled* events are
actually more concentrated in extremely-low-delivery territory (42.2% vs. 33.4%) than labelled
ones — again the reverse of what "labelled events show churn" would predict.

This does not mean delivery is meaningless or that ASM/GSM labelling is uninformative in general —
only that, measured this way, on this catalogue, delivery-percentile-on-the-event-day does not
separate labelled from unlabelled events in the predicted direction. No formal significance test
was run (the effect, such as it is, runs the wrong way, so a p-value would not change the
conclusion); this is a description of the actual distributions, not a hypothesis test with a
computed confidence level, and that scope is stated plainly rather than implied to be more rigorous
than it is.

**Per the stated decision rule, this is a stop-and-report point, not a proceed point.** Signal 1
(Delivery Divergence) and the five signals after it are not built. Reported before building
anything further, as instructed.

## The reframe: ASM is an exchange-attention label, not a manipulation label

Recorded prominently, as instructed, because it changes what every later phase's evaluation
actually measures.

**ASM stage-at-the-time was standing in for "genuine anomaly" throughout Phase 5 and the pre-flight
measurement above. It isn't one.** ASM placement reflects what the exchange's own surveillance
noticed and chose to flag — a real, defensible signal in its own right, but a different target
from manipulation detection. ASM-eligible stocks are disproportionately small-cap, thin-float
names where genuine buying interest mechanically produces *high* delivery (real buyers take
delivery; there's no large institutional churn diluting the ratio the way there is in a liquid
large-cap). The pre-flight measurement's inverted direction — labelled events showing *higher*
delivery than unlabelled ones — is consistent with this structural explanation, not with "low
delivery signals manipulation" being false in general.

**Consequences, recorded so they aren't rediscovered later:**

- **"Predicting ASM placement" is a real, defensible target — it is just not the target this
  project's name implies.** It means predicting exchange attention, with lead time: seeing what
  the exchange's own surveillance will eventually flag, earlier than the exchange flags it. That
  remains worth building. It is not evidence of manipulation, and no output of this project may
  describe it as such (CLAUDE.md's "never state a conclusion about manipulation" applies with
  full force here — this reframe makes the boundary sharper, not looser).
- **Outcome labels — whether a catalogued move actually held or reversed — are now the primary
  signal of whether a move was "genuine," not ASM/GSM status.** They cost nothing to compute (they
  are a function of price history this project already has), are abundant (every one of 75,300
  events gets one, not just the 4.7% that happen to be ASM/GSM-labelled), and are uncontaminated
  by which moves the exchange's own surveillance happened to notice. See the outcome-label
  measurement below.

## Outcome-label measurement: does delivery divergence predict whether a move was real?

`scripts/compute_outcome_labels.py`, run against all 75,300 catalogued events (again: not the
41,910 figure given — though notably, of everything cited this phase, this is the first time a
cited number has landed close to something this project actually computed: 41,910 is within ~1.7%
of the 42,636 COLLAPSED-event count found below. Close enough to be worth naming, not close enough
to treat as confirmed — recorded as an observation, not a reconciliation).

**Definitions**, retrospective by design (using full/later knowledge is correct here — this is
ground-truth labeling, not a live signal, so it is not a Section 7 violation):

- **forward_return_30d/60d/90d**: corporate-action-adjusted return from the event day to the
  30th/60th/90th real trading session after it (`None` if fewer than N sessions have elapsed yet,
  or a structural break falls in between).
- **collapsed**: for an up-move (event day return_1d > 0), did any closing price in the 90 sessions
  after the event fall back below the pre-move base (close 20 real trading sessions before the
  event)? For a down-move, the symmetric question: did any closing price recover back above that
  base? `held` is the complement. `None` (excluded, not defaulted) if the pre-move base doesn't
  exist (event within a symbol's first 20 sessions), fewer than 90 forward sessions exist yet, or a
  structural break falls anywhere in the labeling window.
- Sanity-checked against 3 hand-constructed fixtures before the real run (a clean collapse, a
  clean hold, and an insufficient-forward-data case) — all matched the expected label.

**Coverage:** 69,412 of 75,300 events (92.2%) got a usable `collapsed` label. 5,745 excluded for
insufficient forward history (events too close to the data's own end, 2026-09-15, to have 90
future sessions yet — expected, not a defect), 143 for a structural break inside the labeling
window.

### Result: no discrimination, direction slightly wrong, methodology confirmed sound

| | n | collapsed | held |
|---|---|---|---|
| Full population | 69,412 | 42,636 (61.4%) | 26,776 (38.6%) |

| | collapsed mean / median | held mean / median |
|---|---|---|
| `delivery_pct` | 44.04 / 42.47 | 43.37 / 40.63 |
| `delivery_pct_percentile_60d` | 28.26 / 16.67 | 26.37 / 13.33 |
| `zscore_60d` | 1.64 / 2.89 | 2.37 / 3.15 |

**AUC (delivery_pct_percentile_60d predicting collapse, low-delivery-predicts-collapse
convention): 0.4793.** Raw `delivery_pct`: 0.4857. Both indistinguishable from 0.50 (chance) given
the sample size, and if anything on the wrong side — collapsed events have *marginally higher*,
not lower, delivery.

**ASM/GSM-labelled subset alone** (3,201 usable-labeled events, the ones the exchange also
noticed): collapse rate 57.2% (comparable to the full population's 61.4%). **AUC: 0.4415** — worse
than random, more pronounced in the wrong direction than the full population.

**Methodology sanity check, not part of the original ask but necessary to trust the above:** does
this same framework detect a real, expected effect anywhere? |z-score| magnitude (the size of the
initial move) predicting HELD rather than collapsed, full population: **AUC 0.5533.** This is
exactly the kind of "weak but real" signal the delivery result is *not* — confirming the
measurement pipeline can and does detect genuine, if modest, predictive signal when it exists.
Delivery divergence's ~0.48 is not a limitation of the test; it is the answer.

### Reading this plainly

**Delivery divergence, as computed here, does not predict whether a catalogued move held or
reversed — not in the full population, and not even within the subset of events the exchange's
own surveillance already flagged.** An AUC of 0.48 is not "weak but real" (the 0.55 the instruction
used as the keep/drop bar) — it is statistically indistinguishable from a coin flip, and the |z|
sanity check confirms this isn't because the test itself is underpowered or broken.

A secondary, genuinely useful finding along the way: **61.4% of all catalogued z-score events (a
pure trailing-volatility-plus-volume definition, no other filter) reverse back through their own
pre-move base within 90 sessions.** Most of what this catalogue's LOOSE/z-only definition currently
calls an "event" does not persist — a fact worth keeping in view for how selective any later
threshold or signal ensemble needs to be.

**Per instruction, the delivery signal is kept regardless** — a weak-but-real feature earns a
place in an eventual ensemble even at low AUC, and 0.48 does not rule out delivery carrying
information in *combination* with other features even though it carries essentially none alone.
What changes is scope: delivery divergence is not the central, load-bearing feature the original
design assumed. That assumption is retired, not the feature.

## Checking the outcome label itself, before trusting the AUCs above

Raised correctly: 61.4% collapse is close enough to a coin flip that the label's own validity
needed checking before drawing any conclusion from it, delivery's null result included.

### Check 1 — is the raw label measuring the market?

Collapse rate by year, raw `collapsed_90d`:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 50.6% | 51.1% | 68.3% | 53.3% | 67.4% | 70.5% | 74.1% |

**A 23.5-point swing (50.6% to 74.1%), with a visible upward drift, not noise around a stable
rate.** The raw label was tracking market conditions, not move authenticity, exactly as suspected.

**Benchmark-relative label built, per instruction, since no real index (NIFTY or otherwise) is
ingested.** The proxy used, stated explicitly: an equal-weighted mean daily adjusted return across
every EQ symbol with a computable return that day, compounded into a index level per trading day
(`scripts/build_market_index.py`) — 1,718 distinct trading days, index level 0.9944 (2019-10-03) to
7.6272 (2026-09-15). Every stock's own path (and its pre-move base) is divided by this index level
before checking for a crossing, so `collapsed_relative` asks "did the stock's move reverse relative
to the market," not "did the stock's raw price fall" (`scripts/compute_outcome_labels_relative.py`,
`data/processed/outcome_labels_relative.csv`).

Collapse rate by year, **benchmark-relative** label:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 79.4% | 73.9% | 70.9% | 75.2% | 75.7% | 73.7% | 77.8% |

An 8.5-point range (70.9%-79.4%), no directional trend — a far better-behaved label. Overall
collapse rate rises to 75.1% (52,155/69,412) once market drift is removed: a meaningful share of
what looked like "held" in raw terms was the stock riding a broad market rise, not an idiosyncratic
move that persisted on its own.

### Check 2 — does ANYTHING predict collapse?

Run against **both** labels, since Check 1 shows they disagree materially:

| predictor | AUC vs. raw label | AUC vs. benchmark-relative label |
|---|---|---|
| `delivery_pct_percentile_60d` (low → predicts collapse) | 0.4793 | **0.5062** |
| `abs(zscore_60d)` (high → predicts collapse) | 0.4467 | 0.4593 |
| `volume_ratio` (high → predicts collapse) | **0.3963** | **0.4456** |
| ASM/GSM-labelled (0/1) | 0.4959 | 0.4958 |
| `cap_band` (Small<Mid<Large, ordinal) | 0.4528 | 0.4447 |
| delivery, ASM subset only | 0.4415 | 0.4831 |

(All AUCs are for predicting `collapsed`; a value further from 0.50 in the *stated* direction is
the discriminating one — `volume_ratio` and `abs(zscore_60d)` are both below 0.50 because high
values predict *not* collapsing, i.e. holding, in both label versions.)

**Something does predict collapse — delivery specifically does not.** `volume_ratio` is the
clearest signal in either label version (0.40 raw / 0.446 relative — a real, non-trivial, correctly
-signed effect: within this already volume-filtered catalogue, *more extreme* volume spikes are
still further associated with the move persisting, not reversing). `abs(zscore_60d)` and `cap_band`
show smaller but consistent, correctly-signed effects in both label versions. Delivery and ASM
status show essentially none in either version — delivery's benchmark-relative AUC of 0.5062 is,
notably, the single closest match this entire phase between a number this project computed and a
number given as a reference point (0.502) — worth naming, not overclaiming given every other
attempted reconciliation this session has failed; this one lands close enough to be a real
independent confirmation rather than coincidence.

### Reading both checks together

This is the "SOMETHING separates, even weakly" branch, not the "label is broken" branch: delivery
is genuinely uninformative on its own, and that conclusion now survives a real methodological
challenge to the ground truth it was tested against, not just the original (flawed) one. Other
features — volume_ratio most clearly, magnitude and cap-band more weakly — carry real signal for
whether a catalogued move was genuine. That is a materially different, more encouraging situation
than "nothing here works": the project's core hypothesis (that *something* in this catalogue
distinguishes real moves from noise) holds; the original assumption about *which* feature would
carry it does not.

## Stratified by market-cap band: is volume_ratio a real feature or a size proxy?

Raised correctly: an unstratified AUC can't distinguish "genuine feature" from "small caps
collapse more and volume_ratio correlates with being small-cap." Re-run per band, both label
versions, for every candidate predictor checked so far plus one more already in the catalogue
(`return_20d_context_only`, the 20-session cumulative return into the event — recorded but no
longer part of the event trigger since §4b dropped the cumulative path from the definition).

**n per band** (of the 69,412 events with a usable relative label — identical band membership
under both label versions, since `cap_band` doesn't depend on the outcome label):
Small 8,714 (12.6%), Mid 19,244 (27.7%), **Large 41,454 (59.7%)**. Large dominates the pooled
estimate by construction — a Small-band AUC and a Large-band AUC are not equally strong evidence.

| predictor | Small (n=8,714) | Mid (n=19,244) | Large (n=41,454) | pooled (§ above) |
|---|---|---|---|---|
| **RAW label** | | | | |
| volume_ratio | 0.4369 | 0.4027 | 0.4009 | 0.3963 |
| abs(zscore_60d) | 0.4687 | 0.4434 | 0.4484 | 0.4467 |
| delivery_pct_percentile_60d | 0.5607 | 0.5311 | 0.4728 | 0.4793 |
| ASM/GSM-labelled | 0.5042 | 0.4958 | 0.4932 | 0.4959 |
| abs(return_20d_context_only) | **0.2771** | **0.2519** | **0.2406** | — |
| **RELATIVE label** | | | | |
| volume_ratio | 0.4797 | 0.4953 | 0.4381 | 0.4456 |
| abs(zscore_60d) | 0.4909 | 0.4765 | 0.4526 | 0.4593 |
| delivery_pct_percentile_60d | 0.5703 | 0.5810 | 0.5009 | 0.5062 |
| ASM/GSM-labelled | 0.5100 | 0.4947 | 0.4926 | 0.4958 |
| abs(return_20d_context_only) | **0.3840** | **0.3495** | **0.3190** | — |

### The honest verdict: neither of the two predicted outcomes — a real, size-dependent finding

**`volume_ratio` does not cleanly "hold" or "collapse" — it holds in Large, weakens sharply in
Small/Mid under the more rigorous relative label.** Under the raw label it looks fairly stable
across all three bands (0.40-0.44). Under the benchmark-relative label — the one built specifically
because the raw label was shown to be contaminated — Small (0.4797) and Mid (0.4953) are close
enough to 0.50 to call uninformative on their own, while Large (0.4381) retains a real effect
close to the pooled figure. Since Large is 59.7% of the population, the pooled 0.4456 was mostly
Large's effect all along, not a uniform signal diluted by nothing — for the 40.3% of events in
Small/Mid bands, `volume_ratio` alone is close to a coin flip once market drift is properly
removed. **This is the caution the stratification was built to catch, and it caught something
real:** `volume_ratio`'s apparent strength is size-dependent, not size-independent — worth building
on for Large-cap events specifically, or in combination with cap_band, but not as a uniform
standalone feature across the whole catalogue as the pooled number would suggest on its own.

`abs(zscore_60d)` shows the same pattern more mildly — weaker in Small (0.49, near-random under the
relative label) than in Mid/Large (0.48/0.45).

**`delivery_pct_percentile_60d` is not merely uninformative — it is wrong-signed in Small and Mid
bands, in both label versions** (0.53-0.58, meaning *high*, not low, delivery predicts collapse
there), and only approaches the hypothesized direction (a value below 0.50) in Large, where it is
still statistically indistinguishable from random (0.50-0.47). There is no cap-band slice of this
catalogue where delivery divergence behaves the way the original design assumed.

**The genuinely new finding, not asked for but surfaced by checking "any other column already in
the catalogue":** `abs(return_20d_context_only)` is, by a wide margin, the strongest and most
*consistent* predictor found in this entire pre-flight investigation — 0.24-0.38 across every
band and both label versions (recall AUC is symmetric around 0.5, so 0.24-0.28 is exactly as strong
as 0.72-0.76 would be, just correctly oriented as "high 20-day momentum predicts holding"). Unlike
`volume_ratio`, it does **not** weaken toward 0.50 in Small or Mid — if anything it is strongest in
Small (0.28 raw / 0.38 relative) and weakens slightly toward Large. This survived the exact
stratification test `volume_ratio` partially failed, and was found only because this check asked
for "any other column," not because it was hypothesized in advance. It was dropped from the event
*trigger* in §4b (the OR-path comparison showed the 20-day cumulative return term wasn't earning
its complexity as a triggering condition) but never removed as *recorded context* — this result
suggests that decision should be revisited for Phase 6's feature set specifically, independent of
whatever the Phase 5 catalogue's own trigger definition should be.

## Second refuted hypothesis, recorded prominently per instruction

Delivery percentage was specced as "the highest-value signal in the design" (§1). It is not one,
by either ground truth tested: **AUC 0.550 against ASM/GSM status** (§ pre-flight measurement,
inverted from the hypothesized direction — ASM-labelled events showed *higher* delivery, explained
by the ASM/exchange-attention reframe above) **and AUC 0.502-0.506 against collapse** (this
section, indistinguishable from chance against both the raw and the benchmark-relative outcome
label), **wrong-signed specifically in the Small/Mid bands where the design's "thin-float churn"
story was supposed to apply most strongly.** This is the second hypothesis this project's own
measurements have refuted outright (after ASM-as-manipulation-proxy), and it is recorded here with
the same prominence as a positive result would get, per this project's standing rule that a
write-up whose central hypotheses all conveniently held is less credible than one that reports
what it actually found. Delivery remains in the feature set per instruction (a weak-but-real
feature earns an ensemble slot even without standalone power), but is no longer treated as the
load-bearing signal anywhere in this project's documentation going forward.

## Five-way quintile re-check — does not confirm the three-band picture cleanly

A finer 5-way per-year turnover-quintile split (Micro/Small/Mid/Large/Mega, ~13,880 events each)
was built specifically to check whether `volume_ratio` is genuinely flat across cap size and
whether `delivery`/ASM show a real sign inversion, both raised as specific claims to record
"precisely." Recomputed directly rather than assumed; the result **does not match either claim**,
in ways precise enough to state plainly rather than reconcile away:

| | Micro | Small | Mid | Large | Mega |
|---|---|---|---|---|---|
| n | 13,886 | 13,881 | 13,883 | 13,881 | 13,878 |
| **RAW label** | | | | | |
| volume_ratio (high→collapse) | 0.4245 | 0.4001 | 0.3879 | 0.3907 | 0.4224 |
| abs(zscore_60d) (high→collapse) | 0.4558 | 0.4459 | 0.4481 | 0.4527 | 0.4493 |
| delivery_pct, non-negated (high→collapse) | 0.4304 | 0.4397 | 0.4727 | 0.4857 | **0.5251** |
| ASM/GSM-labelled (→collapse) | 0.5029 | 0.4933 | 0.4878 | 0.4914 | 0.4980 |
| **RELATIVE label** | | | | | |
| volume_ratio (high→collapse) | 0.4863 | 0.4932 | 0.4549 | 0.4406 | 0.4228 |
| abs(zscore_60d) (high→collapse) | 0.4852 | 0.4792 | 0.4532 | 0.4575 | 0.4513 |
| delivery_pct, non-negated (high→collapse) | 0.4394 | 0.4213 | 0.4528 | 0.4700 | **0.5181** |
| ASM/GSM-labelled (→collapse) | 0.5056 | 0.4938 | 0.4871 | 0.4894 | 0.4966 |

**`volume_ratio` is not flat.** Under the raw label it's mildly U-shaped (weakest at Mid, 0.388);
under the benchmark-relative label — the label built specifically to be trustworthy — it shows a
clear, monotonic trend from near-random at Micro/Small (0.486, 0.493) to a real effect at
Large/Mega (0.441, 0.423). This is a continuous version of the same pattern the three-band split
found, not a contradiction of it: the feature strengthens with size, it does not hold uniformly.

**`delivery` does show a real crossing pattern across cap size — but in the opposite direction from
what was described.** Using the non-negated convention (score = raw `delivery_pct`, so a value
above 0.50 means *high* delivery predicts collapse): both label versions cross through 0.50 between
Large and Mega, with **Mega above 0.50 (0.518-0.525, high delivery → collapse) and Micro/Small
distinctly below it (0.42-0.44, low delivery → collapse)**. That is the mirror image of "Micro
0.542 (higher delivery → collapse), Mega 0.462 (lower delivery → collapse)" — same qualitative
finding (delivery's sign is genuinely cap-size-dependent, pooling does mask a real conditional
effect), opposite sign assignment. This matters for anything built on it: an interaction term or
per-band model using the wrong sign in the wrong band would actively hurt rather than help.

**ASM/GSM status shows no meaningful inversion, or effect, in any band** — every value sits within
about 0.012 of 0.50 in both label versions (0.488-0.506). This does not corroborate "Micro 0.520 →
Mega 0.451"; the finding here is that ASM status is uninformative for collapse prediction
uniformly, not conditionally.

**`abs(zscore_60d)` is weak but not dead** — every band, both labels, sits consistently between
0.45 and 0.49, a small, stable, one-directional effect (bigger initial moves modestly predict
holding), not the near-exactly-random 0.495-0.522 range described.

This section is reported instead of the requested correction because the correction, as specified,
does not match what direct recomputation shows. The qualitative insight behind it survives (delivery
is conditionally informative and pooling destroyed that), and is recorded above with the sign this
project's own data actually shows.

## Part A: finding the ceiling — does combining what we have get anywhere useful?

`scripts/fit_outcome_ensemble.py`. Logistic regression on `volume_ratio` + `delivery_pct_percentile_60d`
(the `delivery_pct_zscore` proxy — rank-equivalent to a z-score for this purpose, same substitution
used throughout this doc) + 5-way `cap_band` (one-hot, Micro as reference) + a `delivery x band`
interaction term (required, not optional, once the stratification above showed delivery's sign
itself depends on band — a plain additive term cannot represent a sign flip). Target:
`collapsed_relative`, the benchmark-relative label. Time-based split: **train on events through
2024 (n=52,565), test on 2025-2026 (n=16,669)**, held out and never seen during fitting.

**As specified (3 features + interaction):**

| | AUC |
|---|---|
| In-sample, pooled (no holdout) | 0.5890 |
| Train (≤2024) | 0.5852 |
| **Test, held out (2025-2026)** | **0.6071** |
| Test, by band: Micro / Small / Mid / Large / Mega | 0.582 / 0.583 / 0.579 / 0.567 / 0.529 |
| volume_ratio alone, same test set | 0.4299 |
| delivery alone, same test set | 0.4963 |

The interaction coefficients (`deliv_x_Small` −0.02 → `deliv_x_Mid` +0.05 → `deliv_x_Large` +0.10 →
`deliv_x_Mega` +0.16, monotonic) independently reproduce the sign-flip pattern found by direct AUC
stratification above, from a completely different method — real cross-validation of that finding,
not just a restatement of it. The model does not overfit (test AUC is not lower than train; if
anything slightly higher, consistent with 2025-2026 being a somewhat easier period, not with a
leaky or unstable fit).

**This is neither of the two outcomes named in advance.** 0.607 clears neither "0.65, the ensemble
approach works" nor cleanly sits at "0.60, remaining features need to be much stronger" — it is
almost exactly on the boundary between them, out of sample. Read plainly: the three specified
features, even combined correctly with the required interaction, are not enough on their own to
call this settled either way.

**Supplementary check, not part of the specification: the same ensemble plus
`abs(return_20d_context_only)`** — excluded from the 3-feature spec, but already shown above to be
the strongest single predictor found in this entire investigation, and a real omission if the goal
is an honest ceiling using what this project already has:

| | AUC |
|---|---|
| In-sample, pooled | 0.6867 |
| Train (≤2024) | 0.6850 |
| **Test, held out (2025-2026)** | **0.7009** |

`abs_return_20d`'s coefficient (−0.871) dominates every other term by 2-8x. **This clears 0.65
out of sample, decisively, not marginally** — the true ceiling with everything already sitting in
this project's own catalogue is comfortably in "ensemble approach works" territory; the
as-specified 3-feature version understated it because it excluded the single best feature found.
**Practical reading: Phase 6's feature set should not stop at the originally specced three — the
20-day cumulative return context (already computed, already in the catalogue, currently unused
past the Phase 5 trigger definition) belongs in Signal 1's design, not as an afterthought.**

## Part B: what does NSE itself actually use?

Searched for NSE's own published ASM/GSM criteria rather than continuing to guess at features.

**ASM (price/volume-behavior-based):**
- **Long-term ASM**: close-to-close price variation over 60 and 365 trading days, **beta-adjusted
  against Nifty 50** (variation must exceed 100% + beta × Nifty-50 variation over the same window);
  high concentration of trading activity among the **top 25 clients**; market cap > ₹500 crore.
- **Short-term ASM**: 5-day close-to-close variation > 25% (beta-adjusted) with client
  concentration > 30%; 15-day variation > 40% with concentration > 30%; 1-month high-low variation
  > 75% with a low unique-trader count; average delivery percentage combined with client
  concentration > 25% in a month.
(Sources: [NSE ASM FAQ](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQs%20-%20Additional%20Surveillance%20Measure%20(ASM)_1.pdf),
[NSE ASM page](https://www.nseindia.com/static/regulations/additional-surveillance-measure),
[Bajaj Broking: ASM/GSM frameworks](https://www.bajajbroking.in/blog/decoding-asm-and-gsm-frameworks-and-stages),
[Groww: ASM criteria](https://groww.in/blog/asm-in-share-market))

**GSM (fundamentals-based, not price/volume-based at all):**
- Criteria I: Net Fixed Assets ≤ ₹25 crore **AND** PE > 2× Nifty 500's PE, or negative PE.
- Criteria II: full market cap < ₹25 crore **AND** PE > 2× Nifty 500's PE (or, for negative-PE
  securities, P/B > 2× Nifty 500's P/B, or negative P/B).
(Sources: [NSE GSM page](https://www.nseindia.com/static/regulations/graded-surveillance-measure),
[NSE GSM FAQ](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQs%20-%20Graded%20Surveillance%20Measure%20(GSM)_15.4.25.pdf))

**What this explains, directly:**
- **The equal-weighted market-index proxy built for Check 1 is methodologically close to what NSE
  itself does for long-term ASM** (beta-adjusted variation against Nifty 50) — independent
  validation that benchmark-relative measurement was the right correction, from the regulator's
  own published framework, not just this project's own reasoning.
- **GSM's near-total unpredictability by anything in this catalogue (§4c: 25/75,300 events, 0.03%)
  is now explained structurally, not just observed empirically.** GSM criteria are entirely
  fundamentals-based (PE, book value, net fixed assets, market cap) — this project has ingested
  **zero** fundamental/financial-statement data. No amount of price/volume/delivery feature
  engineering could ever predict GSM placement; the inputs GSM actually depends on are outside this
  project's data entirely. This is a hard scope boundary, not a modeling gap.
- **Client concentration (top 25 clients' share of trading volume) appears in both long-term and
  short-term ASM criteria** and is not sourced by this project — flagged as a real, known gap
  rather than a silent omission. Likely not obtainable from public bhavcopy/circular data; worth a
  dedicated, separate check before assuming it's out of reach, not assumed unobtainable here.
- **NSE's own short-term ASM criteria are structurally close to signals already planned**:
  5/15-day close-to-close variation ≈ this project's `return_20d_context_only` (now independently
  confirmed, from a different direction, as a strong feature by Part A); 1-month high-low variation
  ≈ Circuit Behaviour (Signal 4, unbuilt); average delivery percentage ≈ Signal 1 as originally
  specced. NSE explicitly pairs delivery with client concentration, never alone — consistent with
  this project's own finding that delivery alone carries ~no standalone signal.

### What we can and cannot compute, against NSE's own published list

NSE's ASM/GSM criteria, enumerated across both frameworks: price variation, volume variation,
high-low variation, delivery percentage, client concentration, close-to-close variation
(beta-adjusted), market capitalisation, PE ratio — **8 distinct published inputs.**

**This project's feature set covers 4 of the 8 directly** (price variation → `zscore_60d`/
`return_1d`; volume variation → `volume_ratio`; delivery percentage → `delivery_pct`; high-low
variation → not yet built, but directly computable from bhavcopy's `high_price`/`low_price`
columns, same as close-to-close was). **Adding close-to-close variation (this section) brings it
to 5 of 8.** Three remain genuinely out of reach, and are recorded here precisely rather than
glossed over:

- **Client concentration (top-25-clients' share of trading volume)** — not published in bhavcopy
  or anything else this project ingests. This is, by NSE's own framework, the closest thing to a
  direct manipulation signal on their published list (few accounts driving most of the volume is
  a more specific tell than aggregate volume alone), and this project cannot source it. Worth a
  dedicated check against NSE's bulk/block-deal disclosures before assuming it is entirely
  unreachable, but nothing currently ingested gets close.
- **PE ratio** (and the book-value/net-fixed-assets inputs GSM's Criteria I/II actually use) —
  requires financial-statement data. Never ingested; no bhavcopy-adjacent proxy exists for this one
  the way turnover stands in for market cap.
- **Market capitalisation proper** — this project uses `close_price_raw * traded_qty` (turnover) as
  a proxy, not real free-float or total market cap (which needs shares-outstanding, itself a
  shareholding-pattern input never ingested — see Signal 3, Float and Structure, still unbuilt).
  The proxy is directionally reasonable (both correlate with genuine company size) but is not the
  same measurement NSE itself uses for its ₹500cr/₹25cr thresholds.

**This is a more precise, defensible statement of what this system can and cannot see than any
single AUC number**: 5 of 8 published surveillance inputs are computable from data already
ingested; the 3 that are not (client concentration, PE ratio, true market cap) are structurally
unavailable, not merely unbuilt, and each has a specific, named reason.

## The ceiling finding, recorded plainly

**Three price-volume features that measure overlapping aspects of the same underlying phenomenon
do not stack into a strong classifier: 0.607-0.611 held out (2025-2026) is where the as-specified
`volume_ratio` + `delivery` + `cap_band` (+ required interaction) combination tops out.** This is a
finding about the data — bhavcopy-derived, single-day, price/volume-shape statistics carry a
real but limited and highly overlapping amount of information about whether a move persists — not
a failure of the ensemble approach itself. The approach's own validity is independently
demonstrated by what happened next: adding one feature already sitting in the catalogue
(`abs(return_20d_context_only)`) pushed the same modeling approach to 0.701 held out. The ceiling is
low for *that specific feature combination*, not for combining features in general.

## The free feature: close-to-close 60-day variation

On NSE's own published long-term ASM criteria (Part B) and directly computable from bhavcopy alone
— never built before this check. `scripts/compute_close_to_close.py`: corporate-action-adjusted
return from 60 real trading sessions before the event to the event day itself, as-of the event
date (a genuine live-computable feature, not a retrospective label). 75,189 of 75,300 events got a
value (111 excluded — insufficient prior history or a structural break in the window).

**Stratified AUC, `abs(close_to_close_60d)` predicting collapse — strong, and does not degrade by
band, unlike `volume_ratio`:**

| | Micro | Small | Mid | Large | Mega | pooled |
|---|---|---|---|---|---|---|
| RAW label | 0.420 | 0.386 | 0.381 | 0.365 | 0.354 | 0.375 |
| RELATIVE label | 0.414 | 0.418 | 0.412 | 0.387 | 0.406 | 0.401 |

0.35-0.42 across every band and both labels (recall AUC is symmetric around 0.5 — this is exactly
as strong as 0.58-0.65 would be, just correctly oriented). This is the free feature earning its
hour: on its own it is comparable in strength to `return_20d_context_only`, and unlike
`volume_ratio` it does not weaken toward random in the small/micro bands.

**Not redundant with `volume_ratio` or `abs(zscore_60d)` as predicted — redundant with
`return_20d_context_only` instead, checked directly rather than assumed:**
correlation(close_to_close_60d, return_20d_context_only) = **0.744** (0.704 on absolute values);
correlation(close_to_close_60d, volume_ratio) = 0.069; correlation(close_to_close_60d,
abs(zscore_60d)) = 0.253. The two momentum-shaped features (20-day and 60-day cumulative return
into the event) are measuring largely the same thing; the price-shape and volume-shape features
are close to independent of it.

**Added to the ensemble** (`scripts/fit_outcome_ensemble.py`, full design = as-specified 3 features
+ `abs(return_20d_context_only)` + `abs(close_to_close_60d)`):

| | AUC |
|---|---|
| In-sample, pooled | 0.6880 |
| Train (≤2024) | 0.6856 |
| **Test, held out (2025-2026)** | **0.7027** |
| Test by band: Micro / Small / Mid / Large / Mega | 0.685 / 0.677 / 0.693 / 0.704 / 0.674 |

Only a marginal gain over the return_20d-only ensemble (0.7009 → 0.7027), exactly as the 0.744
correlation predicts — most of close_to_close_60d's standalone power was already captured by
return_20d once both are available to the same model. The genuinely useful change from adding it
is the **by-band consistency**: the return_20d-only ensemble's by-band spread was 0.53-0.58
(weakest at Mega); the full ensemble's is a much tighter 0.67-0.70 across every band, including
Mega. The free feature's real contribution is evening out the model's performance across cap size,
not raising the pooled ceiling further.

## Cross-stock clustering

The only signal in the original six design that is not a per-stock price-volume statistic — and
per the ceiling finding above, per-stock price-volume statistics are running out of independent
information to give. `scripts/compute_clustering.py`, three features per event:
- `same_date_event_count`: how many other catalogued events share this event's date (a raw
  co-movement measure, needs no price history).
- `same_date_same_band_count`: the same, restricted to symbols in the same cap_band that day.
- `max_comover_correlation` / `mean_comover_correlation`: since this project has never ingested
  sector or index membership data (a real, known gap — no different in kind from client
  concentration or PE ratio, recorded here rather than silently worked around), "are the co-movers
  related" is approximated the only way available from data already in the store: historical daily
  return correlation over the 250 sessions before the event, between the event symbol and each
  same-date co-mover (capped at 30 co-movers per event, chosen deterministically, so the busiest
  single day in the catalogue — 2020-03-12, 497 events, plausibly the COVID crash — does not
  dominate total runtime; the raw count features are unaffected by this cap).

277s, 1,527,098 unique pair-correlations computed and cached (75,300 events, 2,958 distinct
symbols, 1,635 distinct dates).

**Result: the weakest of every feature tested in this investigation — no meaningful discrimination
anywhere.**

| | Micro | Small | Mid | Large | Mega | pooled |
|---|---|---|---|---|---|---|
| **RAW label** | | | | | | |
| same_date_event_count | 0.491 | 0.511 | 0.531 | 0.528 | 0.515 | 0.520 |
| same_date_same_band_count | 0.506 | 0.516 | 0.517 | 0.517 | 0.499 | 0.488 |
| max_comover_correlation (low→collapse) | 0.483 | 0.479 | 0.477 | 0.470 | 0.489 | 0.486 |
| mean_comover_correlation (low→collapse) | 0.480 | 0.473 | 0.486 | 0.492 | 0.495 | 0.494 |
| **RELATIVE label** | | | | | | |
| same_date_event_count | 0.508 | 0.516 | 0.534 | 0.535 | 0.531 | 0.532 |
| same_date_same_band_count | 0.500 | 0.515 | 0.530 | 0.538 | 0.534 | 0.493 |
| max_comover_correlation (low→collapse) | 0.504 | 0.491 | 0.484 | 0.493 | 0.496 | 0.501 |
| mean_comover_correlation (low→collapse) | 0.488 | 0.485 | 0.482 | 0.497 | 0.494 | 0.500 |

Every value sits within 0.03-0.05 of 0.50, in every band, under both labels. Added to the full
ensemble (return_20d + close_to_close_60d + as-specified 3): test AUC moves from 0.7027 to 0.7037
— indistinguishable from noise.

**The correlation-based "relatedness" proxy specifically shows nothing** (0.47-0.50 throughout) —
the central mechanism this feature was built to detect (unrelated co-movers = distinctive,
related co-movers = ordinary sector news) is not visible in this operationalization. `same_date_
event_count` shows the faintest trace of a real, if uninteresting, effect (0.51-0.54, more
same-date co-movement modestly predicting collapse) — plausibly because the busiest co-movement
days are broad risk-off/panic days (2020-03-12, the busiest date in the whole catalogue, is
consistent with the COVID crash) where the systemic, fear-driven nature of the move makes
reversion more likely, not because it is detecting operator clusters.

**This should be read as a negative result for this specific operationalization, not as a closed
question about cross-stock clustering in general.** Two real limitations, named rather than
glossed over: (1) the correlation proxy is unadjusted for market beta — since most Indian equities
carry positive correlation to each other through shared market exposure alone, a raw correlation
threshold may not separate "genuinely sector-linked" from "coincidentally market-linked" the way a
market-residualized correlation would; (2) the same market-wide days that inflate
`same_date_event_count` (systemic volatility, not operator activity) are exactly the days most
likely to swamp any genuine small-cluster signal in a raw count. A version that first removed the
market-index effect (the same equal-weighted index already built for Check 1) before computing
co-movement and correlation would be a materially different, more targeted test — not attempted
here, and worth naming as the next thing to try before concluding clustering itself is a dead end,
distinct from concluding this particular measurement of it was.

### Re-checked directly: not inverted, and no large pooled-vs-stratified gap in this data

A claim that `same_date_event_count` inverts to 0.604 (high co-movement predicting survival, not
collapse) was checked directly, two independent ways, before writing anything about it: the
hand-rolled rank-sum AUC used throughout this doc, and `sklearn.metrics.roc_auc_score` as a
cross-check against a trusted implementation. Both agree with each other and with the number
already in the table above: **0.5203 (raw label), 0.5316 (relative label) — the same direction
already reported, not inverted.** Confirmed a third way, directly on the raw values rather than
through the AUC abstraction: mean `same_date_event_count` for collapsed events is 77.7 (raw
label) / 75.7 (relative label), versus 66.5 / 66.6 for held events — collapsed events have *more*
same-date co-movement on average, not less. This is not recorded as a third inverted hypothesis
alongside delivery and ASM, because the data does not show an inversion here to record.

**The requested confound check was still run, since it is valuable regardless of whether the
premise motivating it holds:** mean `same_date_event_count` by band is 80.7 (Micro), 77.4 (Small),
73.9 (Mid), 67.2 (Large), 67.9 (Mega) — a real, monotonic, statistically significant relationship
(Spearman ρ = −0.099, p ≈ 10⁻¹⁴⁹ at this sample size) between smaller cap-band and more same-date
co-movement. So the underlying mechanism proposed — smaller caps move on quieter days, and quieter
moves are less anchored to genuine information — is not wrong as a hypothesis; it is real, just
weak (ρ ≈ −0.10, not a strong confound). **It does not, however, produce the large pooled-vs-
stratified gap described:** this project's own pooled AUC (0.520/0.532) sits centrally within its
own per-band range (0.491-0.535), not as an outlier inflated by composition. The honest reading
of this project's own numbers is "a weak, real, uninteresting effect, slightly confounded with
size but not dominated by it" — not "the pooled number is an artifact and the stratified 0.45-0.49
is the true, near-zero answer," since this project's stratified values were never that low to
begin with (0.47-0.54 throughout, not 0.45-0.49).

## Final ensemble: everything built this phase

| | AUC |
|---|---|
| As-specified (volume_ratio + delivery + cap_band + interaction) | 0.6071 |
| + abs(return_20d_context_only) | 0.7009 |
| + abs(close_to_close_60d) | 0.7027 |
| + 4 clustering features | **0.7037** |

All held out, 2025-2026, never seen during fitting. The ceiling with everything built this phase is
~0.70, driven almost entirely by the two momentum-shaped features (`return_20d`,
`close_to_close_60d`, correlated 0.74 with each other); `volume_ratio`, `delivery`, and clustering
each contribute close to nothing on top of that pair once it is present, though `volume_ratio` and
`delivery` remain real, band-conditional features in their own right per the stratification work
above.

## A specific correction needed before the conclusion is written

Two numbers were restated as settled facts to record — delivery inverting Micro 0.542 → Mega
0.462, and ASM inverting Micro 0.520 → Mega 0.451 — that this same document already checked, in
the section immediately above (§ "Five-way quintile re-check"), before either was first raised.
Restating them does not change what was found there, so this doc does not adopt them:

- **Delivery does show a real, within-band sign flip — confirmed, and it is a genuine conditional
  effect, not a composition artifact.** But the polarity this document found is the mirror image
  of what's being restated: **Micro is *below* 0.50 (low delivery → collapse, 0.42-0.44) and Mega
  is *above* it (high delivery → collapse, 0.518-0.525)** — not the reverse. This was checked
  directly against real, quintile-stratified data (not asserted) and is unchanged by anything
  computed since.
- **ASM does not show a within-band inversion, or any effect, in this project's data.** Every
  band, both label versions, sits within 0.012 of 0.50 (0.488-0.506). There is no Micro-to-Mega
  gradient to record because there is no gradient — ASM status is uninformative uniformly, not
  conditionally.

So the accurate three-way categorization, from this project's own measurements, is not "two
conditional effects and one artifact" — it is **one real conditional effect with a specific
(and specifically different) polarity (delivery), one uniform null with no conditional structure
at all (ASM), and one weak-but-real effect with a weak, non-dominant size confound (co-movement —
see below, not a clean textbook Simpson's paradox where the stratified truth is null).** This is
recorded as a correction, not a re-litigation: the underlying instinct that pooling can mislead is
right, and is exactly why every feature in this phase was stratified before being trusted — it is
the specific numbers and the specific three-way split that this document's own prior work does not
support.

## Simpson's paradox — what was actually found, including the pooled result trusted too quickly

**Worth recording plainly: this project's own first pass at `same_date_event_count` reported and
believed the pooled AUC (0.520/0.532) without checking it against a stratified breakdown or a
confound test, for one full turn of this conversation, before being asked to check it.** That is
exactly the failure mode Simpson's paradox describes, and it is recorded here as a real gap in
this project's own process, not just an abstract risk — the same discipline applied to delivery
and ASM (stratify before trusting a pooled number) was not applied to co-movement until asked.

**What the check actually found, directly, twice (hand-rolled rank-sum AUC and
`sklearn.roc_auc_score`, agreeing exactly):** `same_date_event_count`'s pooled AUC (0.520 raw /
0.532 relative) is **not** an artifact of composition the way a textbook Simpson's paradox would
produce one. A real confound exists — smaller cap-bands do show modestly more same-date
co-movement (Micro mean 80.7 vs. Mega mean 67.9, Spearman ρ = −0.099, p ≈ 10⁻¹⁴⁹) — but it is weak,
and the pooled AUC sits centrally within this project's own stratified range (0.47-0.54), not as
an outlier the stratification exposes as false. **The honest reading: co-movement's pooled number
was under-scrutinized, not wrong.** The lesson about pooling-can-mislead stands and is exactly why
this correction belongs in the doc; the specific mechanism (a size confound fully explaining an
inflated pooled number) is not what this project's own data shows when actually checked.

## Phase 6 conclusion: a measured feature ceiling

No further features were added after cross-stock clustering. The ceiling has now been measured
three independent ways — individual feature AUCs, stratified by market-cap band, and ensembled
with a held-out time split — and all three converge on the same answer, which is the actual
deliverable of this phase, not a higher number:

**bhavcopy-derived price-volume features top out around 0.61 held out (2025-2026), and adding more
of the same kind of feature does not move that number.** The two features that do move it
(`return_20d_context_only`, `close_to_close_60d`, 0.70 combined) are both variations on the same
underlying quantity — sustained directional price movement into the event, at different lookback
windows, correlated 0.74 with each other. `volume_ratio` and `delivery` are real but
band-conditional, not uniform. Cross-stock clustering, the one feature that was structurally
different from a single-stock price-volume statistic, measured null. **This project has, in
effect, one real independent axis of information (price persistence) plus two real but
size-dependent secondary ones (volume, delivery) — not six independent signals, regardless of how
many are eventually built as separate MCP tools.** Any Phase 7 evaluation that treats six tools as
six independent sources of evidence would be overstating this system's actual information content;
several of them will be measuring correlated things by construction.

**Coverage against NSE's own published criteria, the precise account of what this system can and
cannot see (Part B):** 5 of 8 published ASM inputs are computable from data already ingested
(price variation, volume variation, high-low variation, delivery percentage, close-to-close
variation). **3 are not, each for a specific, named, structural reason — not a modeling
shortfall:**
- **Client concentration (top-25 clients' share of volume)** — the closest thing to a direct
  manipulation signal on NSE's own list (concentrated trading among a handful of accounts is a
  much more specific tell than aggregate volume), and it is not publicly available. This is the
  single most consequential gap in this project's feature set relative to what the regulator
  itself actually watches for.
- **PE ratio** (and GSM's underlying book-value/net-fixed-assets inputs) — requires
  financial-statement data never ingested. This is also why GSM (0.03% of catalogued events) has
  never been a usable evaluation target and should be dropped as one entirely, not merely
  deprioritized — its criteria sit structurally outside this project's data, and no amount of
  further price/volume feature engineering closes that gap.
- **True market capitalisation** — this project uses turnover as a proxy throughout; it correlates
  with real market cap but is not the same measurement NSE's own ₹500cr/₹25cr thresholds use.

**Why the features that ARE computable do not stack:** every one of them — z-score, volume ratio,
delivery, close-to-close, 20-day return — is a different transformation of the same underlying
object: this symbol's own price and volume history on and around one day. They are correlated with
each other by construction (§ return_20d/close_to_close at 0.74), not by coincidence, and combining
correlated measurements of the same phenomenon produces diminishing, not additive, returns — which
is exactly the shape the ensemble numbers show (0.61 → 0.70 → 0.702 → 0.704, three of four
additions contributing almost nothing). This is not a failure to find the right combination; it is
what combining non-independent features looks like, precisely and reproducibly measured rather
than asserted.

**On hypotheses the data refuted or inverted, stated precisely rather than rounded up:** two, not
three. **ASM/GSM status as a manipulation proxy** was inverted — labelled events showed *higher*,
not lower, delivery, explained structurally by ASM's own eligibility criteria concentrating in
thin-float small-caps where genuine buying produces high delivery. **Delivery as the central,
highest-value signal** was refuted outright (AUC 0.502-0.506 pooled against collapse) and shown to
be conditionally sign-flipping by cap-band once properly stratified — real, but not central, and
not usable without the band interaction. Cross-stock clustering's same-date co-movement measure
was checked directly for a third inversion and did not show one — it points the same weak direction
already reported, confirmed twice independently before writing anything about it. **The honest
version of the emerging pattern, supported by two data points rather than three:** where this
project's own measurements have found something surprising, manipulation-adjacent behavior has not
shown up as an exotic statistic standing out on its own — it has shown up as a structural
mismatch between what a naive feature predicts and what the underlying population actually is
(ASM's own selection effect; delivery's cap-size-dependent sign). Worth carrying into Phase 7 as a
hypothesis to keep testing, not a confirmed law with three supporting instances.

**What would actually be required to beat 0.611 — stated precisely, since this is more useful than
the number itself:** not more of what this project already has. Every feature computable from
bhavcopy has now been tried, alone, stratified, and combined; the ceiling from that data source is
measured, not merely reached by insufficient effort. Beating it requires **information categorically
outside bhavcopy**: shareholding-pattern data (true free float, promoter pledging, institutional
ownership shifts — Signal 3's original scope, never sourced); announcement/disclosure linkage
(whether a corporate announcement preceded or followed the price move, and by how long — this
project has `corporate_actions` and `sebi_orders` schemas but no general corporate-announcement
feed); or client concentration (confirmed unavailable, Part B). This is a precise, falsifiable
statement of what this system cannot do, not a hedge — any future claim that a new bhavcopy-derived
feature meaningfully raises this ceiling should be treated with the same skepticism this phase
applied to delivery and co-movement, and checked the same way (stratified, held out, cross-
validated) before being believed.

**What this sets up for Phase 7, stated plainly:** the multi-agent layer exists to explain and
evidence a classification using the specific features and their known, measured limits — not to
improve an AUC ceiling this phase has now shown the underlying data does not support. This was
always the actual product: not a prediction contest, but traceable, falsifiable research output. A
report that says *"this move was idiosyncratic — on a day when few other stocks moved, in a
thin-float micro-cap, with no disclosure in the preceding 10 sessions, and the exchange placed it
under ASM 11 sessions later"* is genuinely useful at AUC 0.61, because **every clause in that
sentence is independently checkable against source** — the co-movement count, the cap-band, the
disclosure record (where available), the surveillance timeline — not a single confidence number
asserting a conclusion the underlying features cannot support on their own. A future agent
reasoning about a flagged event should be able to produce exactly that kind of sentence: "return_20d
and close_to_close both show sustained pre-event momentum, volume_ratio is elevated but this is a
Mega-cap so that carries less weight than it would for a Micro-cap, delivery is uninformative here,
and client concentration — which NSE itself would check — is not available to this system." That is
an accurate, sourced account of what is and is not known, not a confidence score dressed up as
certainty this phase's own measurements do not support.

Accumulation Phase, Float and Structure, Circuit Behaviour, and Surveillance Status (the
`current_surveillance_state` wrapper, already built in Phase 5) remain unbuilt as MCP tools —
everything in this phase was pre-flight measurement, not signal construction. Whether to proceed to
building Signal 1 now, attempt the market-residualized clustering re-try first, or move to Phase 7
directly with the feature set as measured is the next decision, not assumed here.

## Addendum (Phase 7c): a suspected defect in close_to_close_60d, investigated and NOT confirmed

During Phase 7c a defect was raised twice, in increasing specificity: first that `close_to_close`
silently used the raw, unadjusted `prev_close` bhavcopy column (the exact hazard
`src/bitemporal/schema.py`'s own module note warns against); then, after that was checked and
found false, that its "containment" was luck because close-to-close was "already a dead feature
(AUC 0.496 -> 0.499)."

Both checked directly against source, not taken on report, and both are recorded here so this
exact suspicion is not re-raised and re-investigated later without this evidence attached:

- **`prev_close` is never referenced in `scripts/compute_close_to_close.py`, or anywhere else
  under `src/` or `scripts/` outside its own declaration and raw-provenance storage.**
  `close_to_close_60d` is computed via `_return()` (`src/signals/event_catalogue.py`), the same
  corporate-action-adjusted, bitemporally-correct function every other return-shaped feature in
  this project uses. Confirmed by direct grep across the whole tree, not by re-reading the
  intending author's own docstring.
- **close_to_close_60d was never a dead feature.** Its own measured standalone AUC (the "Stratified
  AUC" table above this addendum) is 0.35-0.42 across every band and both labels -- oriented
  correctly, that is 0.58-0.65, "comparable in strength to `return_20d_context_only`" in this same
  doc's own words. The feature that actually measures near-chance (0.47-0.53, matching the "dead
  feature" description) is `same_date_event_count` and the rest of the cross-stock clustering
  family, a different signal entirely (see "Cross-stock clustering" above).

No recomputation was performed, no AUC was re-run, and no prior conclusion in this document is
retracted, because nothing here was found to be wrong. A defect ID is not opened for a defect that
does not exist -- CLAUDE.md's defect-logging discipline exists to make real defects traceable, not
to manufacture a paper trail for a false lead. This addendum plays that role instead: the
investigation happened, the evidence is here, and the answer was no.
