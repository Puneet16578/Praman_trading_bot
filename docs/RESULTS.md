# Praman — Results

A single top-level summary spanning Phase 6 (feature ceiling), Phase 7 (multi-agent evidence
layer), and Phase 8 (evaluation). Phase-specific detail lives in `docs/phase6_signals.md`,
`docs/phase7[abc]_*.md`, and `docs/phase8_evaluation_results.md`; this document is the one meant
to travel, and every number in it is checked against those sources directly, not re-typed from
memory.

**A correction, made before anything else, because several specific figures requested for this
document do not exist in this project's own real, computed output — checked directly, not assumed
correct or incorrect:**

- **P7-001 is not a real defect.** It was proposed twice earlier in Phase 7c/8 (a suspected
  `prev_close`-unadjusted bug in `close_to_close_60d`, then a "dead feature, contained by luck"
  framing). Both were checked directly: `scripts/compute_close_to_close.py` computes the value via
  `_return()`, the same corporate-action-adjusted function every other return feature uses;
  `prev_close` is referenced nowhere in `src/` or `scripts/` outside its own declaration and raw
  storage (confirmed by grep, and now permanently guarded by `tests/
  test_no_raw_prev_close_in_signals.py`). `close_to_close_60d`'s own measured standalone AUC —
  0.35-0.42 under the original, oriented convention this section is correcting — is now **0.5122
  [0.5075,0.5170] TRAIN / 0.4768 [0.4620,0.4915] HOLD-OUT** under Amendment 5's frozen, un-oriented
  label (`docs/phase10_preregistration_amendment5.md` §6; its own feature file was not rebuilt this
  session, an unchanged caveat carried from every prior correction round) — still one of the
  strongest single raw features this project found, not a dead one, now measured on a
  direction-consistent scale instead of an oriented one. See `docs/phase6_signals.md`'s own
  addendum for the full original trace. There is no P7-001 to report the Adversary catching, here
  or anywhere.
- **"Full system AUC 0.588 vs. disclosure-tier-alone AUC 0.588"** does not match any number this
  project has computed. The real Layer 3 comparison (Brier score + top-tier precision, categorical
  scoring, `docs/phase8_evaluation_results.md`) shows the full system's top-tier precision (90.6%)
  clearing disclosure-tier-alone's (78.7%) with non-overlapping CIs. The NEW volume_ratio-tie-broken
  precision@k test this document reports below (§2) is more nuanced than either "clearly beats" or
  "ties" — see that section for the real numbers and the decision actually taken.
- **z_score vs. volume_ratio precision@k at "40% vs 65%"**, and a Phase 6 "volume_ratio 0.586-0.607,
  the feature that survived stratification" — checked directly against `docs/phase6_signals.md`:
  `volume_ratio` is below 0.50 in every single reported cut, pooled and by band, and explicitly did
  NOT survive stratification. `return_20d_context_only`/`close_to_close_60d` did (0.53-0.58 by
  band). This project's own real, computed precision@20 (`scripts/
  phase8_precision_at_k_alternative_orderings.py`): correctly directed, z_score 90.0%, volume_ratio
  85.0%, return_20d 95.0%; naively directed, 20.0% / 35.0% / 5.0%. Reported in full in §5.
- **"Lead time led by p25 = 14 sessions"** — the real p25 is 3 sessions; 14 is the real median.
  Both are reported, correctly labeled, in §5 and in `docs/phase8_evaluation_results.md`.
- **The clean-label feature AUC table cited below (§ "zscore_60d falls to 15.0%... pooled hold-out
  AUC (0.537)") is now superseded twice over, and the current numbers are FROZEN, not provisional.**
  It was first re-run on Amendment 4's equity-only/ISIN-corrected data (`zscore_60d` HOLD-OUT 0.5234
  [0.5081,0.5387], `docs/phase10_amendment4_prep3.md` §3) — itself superseded before Amendment 4 was
  even committed, once Amendment 5 (`P8-014`, `docs/DEFECT_REGISTER.md`) fixed a second, unrelated
  defect in the outcome label's own EQ/BE/BZ bridging. **The final, frozen table**
  (`docs/phase10_preregistration_amendment5.md` §6, `scripts/phase10_amendment4_phase8b_reauc.py`,
  re-run against the `P8-014`-corrected label, TRAIN n=59,899 / HOLD-OUT n=5,966 unless noted):

  | Feature | TRAIN AUC [95% CI] | HOLD-OUT AUC [95% CI] | Excludes 0.5? |
  |---|---|---|---|
  | `zscore_60d` | 0.5285 [0.5238,0.5332] | 0.5250 [0.5104,0.5397] | Yes (both) |
  | `volume_ratio` | 0.5765 [0.5719,0.5811] | 0.5374 [0.5227,0.5520] | Yes (both) |
  | `delivery_pct_percentile_60d` | 0.4217 [0.4170,0.4264] | 0.4683 [0.4536,0.4830] | Yes (both) |
  | `return_20d_context_only` | 0.5253 [0.5206,0.5300] | 0.4853 [0.4706,0.5000] | HOLD-OUT borderline — upper CI is exactly 0.5000 |
  | `close_to_close_60d`* | 0.5122 [0.5075,0.5170] | 0.4768 [0.4620,0.4915] | Yes (both) |
  | `same_date_event_count` | 0.4776 [0.4729,0.4823] | 0.4835 [0.4688,0.4982] | Yes (both) |
  | `asm_gsm_labelled` | 0.5000 [0.4952,0.5047] | 0.5061 [0.4914,0.5208] | No (both) |

  *`close_to_close_60d`'s own feature file was not rebuilt this session — an unchanged caveat
  carried from every prior correction round. **No feature reverses direction across any correction
  round** — the qualitative narrative in this section and in §5 below stands; only the decimal
  figures were superseded, and are now frozen along with the rest of the Phase 10 pre-registration
  (`docs/phase10_preregistration_amendment5.md`, closing section). The precision@20 figures
  (15.0%/40.0%/80.0%/95.0%, from a separate script, `scripts/phase8_robustness_check1_direction.py`)
  have never been re-run against any corrected data — a real, standing gap, named here rather than
  silently dropped.

---

## 1. Headline — the original result was a label artifact, retracted under `P8-001`

**This retraction is the headline of this document.** The original finding below ("the full
system's top-tier precision clears disclosure-tier-alone's") was produced by mechanical coupling
between the outcome label and the classifier's own momentum input — not by the classifier adding
real information over disclosure tier. Under a label that removes that coupling, **neither
disclosure tier nor the classifier shows top-tier lift over its own base rate.** See `P8-001`
(`docs/DEFECT_REGISTER.md`) and the full analysis in `docs/phase8_robustness_checks.md` and
`docs/phase8b_clean_label_features.md`.

**What was found, precisely.** Phase 8's Layers 2/3 scored against the raw `collapsed_90d` label —
the exact label `docs/phase6_signals.md` had already shown "was tracking market drift, not move
authenticity" — and that label shares its `close(event_date − 20)` anchor with
`return_20d_context_only`, the input the classifier's `momentum_high`/`UNEXPLAINED` logic is built
on (numerically confirmed: 0/15 spot-checked events mismatched, exact to 1e-6). Re-scored under a
pre-registered, event-day-anchored, market-relative label that removes that shared anchor:
disclosure-tier-alone's top-tier precision falls from 78.7% to 51.1% — exactly its own 51.0% base
rate, zero lift — and the classifier's falls from 90.6% (n=255) to 28.6% (n=7, actually *below*
base rate, on a tiny, internally inconsistent cell).

**The decomposition, on a corrected, comparable footing (LIFT over each label's own base rate, not
raw Brier — an earlier draft's "drift correction improves the numbers" framing compared Brier
scores across labels with different base rates, which is not valid, and is withdrawn):**
correcting market drift alone barely moves the classifier's own lift (+16.4pp under the raw label →
+15.9pp once drift is corrected, same t−20 anchor); only removing the shared anchor collapses it
(to −22.5pp / +6.7pp under the two decoupled thresholds tested). **Mechanical coupling, not market
drift, drove the original headline.** A cap-band-only baseline (no disclosure tier, no
classification — just size) goes Brier-skill-negative under the clean label, while the classifier's
own aggregate skill barely survives (BSS 1.8%) even as its specific top tier fails — traced further
in `docs/phase8b_clean_label_features.md`, which also found the classifier's current core axis
(`return_20d_context_only`/`momentum_high`) reverses sign on real 2026 hold-out data once measured
against the decoupled label.

**Layer 1 (factual accuracy — 100% of 29,764 claims verified, one correctly withheld) is
unaffected by any of this and should be read as still fully standing.** Layer 1 tests the
report-generation pipeline's transcription and derivation correctness against raw source data; it
does not use `collapsed_90d`, `return_20d`, or any classification-performance metric at all. Nothing
in `P8-001` bears on it.

**The 2026 hold-out is now spent for model selection, as of this correction (2026-09-22).**
`docs/phase8b_clean_label_features.md`'s item 3 used 2026 hold-out AUCs to decide which features
generalize under the clean label — that is model selection informed by test-set performance, not a
clean walk-forward measurement anymore. **2026 cannot be used again as a hold-out for any model
whose feature set was chosen using that analysis**, including any future redesign that acts on it.
`docs/phase10_preregistration.md` commits to a FORWARD-only evaluation (events after 2026-09-15,
once their own 90-session outcomes exist) for exactly this reason.

**The original Layer 3 paragraph, kept verbatim below rather than deleted, so the retraction is
auditable against what it retracts:**

> On the categorical, per-class scoring already established (Layer 3, Phase 8): the full system's
> top-tier precision (90.6%, n=255) clears disclosure-tier-alone's (78.7%, n=362) with
> non-overlapping 95% CIs, and its Brier score is marginally better (0.2024 vs. 0.2091). Disclosure
> tier remains the dominant single input by a wide margin over random/naive baselines, exactly as
> Phase 6 predicted it would be — but on this specific test, the full system is not redundant with
> it.

**On the new test this document was specifically asked to run — precision@k at k=10/20/50/100,
both baselines ranked by the same categorical TRAIN score with volume_ratio as the tie-break — the
picture is more honest and more mixed, and is reported as such, not folded into the headline
above.** See §2 for the full mechanical decision and the real numbers.

**The structural point is real regardless of which way the numbers land:** `GROUNDED` — 43-47% of
all events depending on period — is gated entirely on disclosure tier, with no other signal input
at all (`GROUNDED_LIMITATION_NOTE`, Phase 7c). A large share of the classifier's own decision
surface routes through the same variable baseline 3 uses directly. That structural fact is true
independent of which baseline wins any specific precision@k test.

## 2. Precision@k: baseline 3 vs. baseline 5, decision rule applied mechanically

Script: `scripts/phase8_baseline3_vs_5_precision_at_k.py`. Both baselines ranked by their own
categorical TRAIN-period score (disclosure_tier×cap_band for baseline 3; classification×cap_band
for baseline 5), with volume_ratio as the tie-break (ascending — low volume_ratio ranks first,
the empirically-correct direction established in §5). 2026 hold-out, n=6,049, 90-session horizon,
base rate 74.1%.

| k | Baseline 3 | Baseline 5 | Gap | CI of B5 clears CI of B3? |
|---|---|---|---|---|
| 10 | 6/10 = 60.0% [31.3, 83.2] | 9/10 = 90.0% [59.6, 98.2] | +30.0pp | no |
| 20 | 14/20 = 70.0% [48.1, 85.5] | 18/20 = 90.0% [69.9, 97.2] | +20.0pp | no |
| 50 | 39/50 = 78.0% [64.8, 87.2] | 47/50 = 94.0% [83.8, 97.9] | +16.0pp | no |
| 100 | 79/100 = 79.0% [70.0, 85.8] | 94/100 = 94.0% [87.5, 97.2] | +15.0pp | **YES** |

**Decision rule as specified: baseline 5 must clear baseline 3's CI at BOTH k=20 and k=50 to take
the narrow-claim branch.** It clears at neither (though it comes closer at k=50 than k=20, and
clears cleanly at k=100). **Per the rule, mechanically applied: the null branch is taken.** The
architecture is not shown, by this specific test, to add ranking power beyond what disclosure tier
already provides at k=20/50 — its demonstrated value in this evaluation is verification and
reporting (§3), not classification ranking at these k.

**Reported honestly rather than left at the bare branch decision:** baseline 5's POINT ESTIMATE
exceeds baseline 3's at every single k tested (by 30, 20, 16, and 15 percentage points), and the
gap does clear the same non-overlap bar at k=100. The CIs are wide at small k (n=10-20) — this
reads as "a real, consistently-observed gap that this specific hold-out's size cannot yet
confirm with a strict non-overlap test at k=20/50," not as "no gap exists." The rule was specified
in advance and is applied as written; the honest color around it is reported alongside it, not
in place of it.

**Caveat added per `P8-001` (§1): this table is scored against the same raw `collapsed_90d` label
Check 1 found to be both market-drift-contaminated and anchor-coupled to `return_20d`, and it was
NOT independently re-run under the corrected label as part of that check.** Given §1's finding that
the categorical (classification, cap_band) score's top tier collapses under the corrected label,
this table's own gap — built from the same categorical score, just tie-broken by `volume_ratio` —
should be treated as open, not confirmed, until it is re-tested the same way. It already lands on
the "null branch" (no confirmed advantage at k=20/50) even under the raw label; the robustness
check gives a specific, structural reason that null result might understate how little this ranking
carries, rather than a reason to expect it would reverse into a stronger finding.

## 3. What the architecture contributes (independent of §1/§2)

- **100% of the 29,764 claims that reached output across a real, unmodified 2,000-event sample were
  verified** — 100% transcription (re-run the same derivation function, catches mistranscription),
  and for the two claim types with an independent second implementation (`volume_ratio`,
  `delivery_pct_percentile_60d`), a seeded ~20% sample (786 of 4,000 eligible claims, 19.65%) was
  independently RECOMPUTED from raw `bhavcopy` via a separate SQL path
  (`src/agent/derivation_check.py`) that never calls the shared derivation function at all — every
  one agreed within tolerance. This is what makes the 100% figure a correctness check, not merely a
  transcription check, for those two claim types; it is explicitly NOT derivation-verified for
  `zscore_60d`, `return_20d`, or the disclosure/surveillance claim types (25,764 of 29,764 claims
  are `NOT_APPLICABLE` at that tier) — stated as a real scope boundary, not implied away.
  Full detail: `docs/phase8_evaluation_results.md` §Layer 1.
- **Exactly one claim, across that entire sample, was withheld** — correctly, by the banned-term
  lint, because a real disclosure's own text quoted a news headline containing "fraudulent" (the
  company was denying involvement). The lint cannot distinguish a source's own wording from this
  project's assertion, so it drops either way — the safety mechanism working as intended, at a real
  (0.016%) completeness cost, now documented.
- **Reports state their own limits, in their own output, not only in docs**: every generated report
  carries the Phase 6 discriminative-power ceiling (0.611-0.70) and, where applicable, the
  GROUNDED-proportionality limitation and the GROUNDED/UNEXPLAINED_ISOLATED statistical
  indistinguishability — attached at the point of classification (`src/agent/synthesis.py`), not in
  a footnote a reader could miss.

## 4. The measured ceiling — WITHDRAWN, `P8-001`

**Every number in this section is withdrawn, not merely caveated.** Both figures below were
measured against `collapsed_relative`, anchored at `close(event_date − 20)` — and the two features
that drive the higher figure (`return_20d_context_only`, `close_to_close_60d`) are exactly the two
`docs/phase8b_clean_label_features.md` (item 3) shows REVERSE SIGN on real 2026 hold-out data once
scored against a label anchored away from that same point. A ceiling built substantially on two
features shown not to generalize is not a number to plan around. Dated correction:
`docs/phase6_signals.md`'s own top note; full detail: `docs/phase8_robustness_checks.md`,
`docs/phase8b_clean_label_features.md`.

**Kept below verbatim, as originally computed, for auditability — not to be read as current:**

**AUC 0.611, held out on 2025-2026 data** (`docs/phase6_signals.md`), rising to 0.7009-0.7037 with
`return_20d_context_only`/`close_to_close_60d` added — both variations on the same momentum-
persistence signal, correlated 0.74 with each other, not independent evidence.

**5 of NSE's own 8 published ASM/GSM surveillance criteria are computable from data this project
already ingests** — price variation, volume variation, delivery percentage, high-low variation,
close-to-close variation. **3 are structurally unavailable, each for a specific, named reason, not
merely unbuilt:**
- **Client concentration** (top-25-clients' share of volume) — by NSE's own framework, **the
  closest thing to a direct manipulation signal on their published list** (few accounts driving
  most of the volume is a more specific tell than aggregate volume alone) — not published in
  bhavcopy or anything else this project ingests.
- **PE ratio** and the book-value/net-fixed-assets inputs GSM's own criteria use — requires
  financial-statement data never ingested.
- **True market capitalisation** — this project uses turnover (`close_price × traded_qty`) as a
  proxy, not real free-float/total market cap (needs shares-outstanding, never ingested).

## 5. Findings

- **Delivery divergence — refuted, direction inverted from the hypothesis.** ASM/GSM-labelled
  events show a HIGHER, not lower, delivery percentile than unlabelled ones (median 20 vs. 15) —
  "the distributions substantially overlap, and the direction is the opposite of the hypothesis"
  (`docs/phase6_signals.md`).
- **ASM/GSM status — reframed, not a manipulation label.** ASM placement reflects what the
  exchange's own surveillance chose to flag — a real signal in its own right, structurally
  correlated with small-cap/thin-float names, not a ground-truth label for "genuine anomaly."
  Consequence: outcome labels (`collapsed_Nd`), not ASM status, became this project's primary
  signal of whether a move was "real."
- **Cross-stock co-movement — a real Simpson's paradox, caught and corrected, not just noted.** A
  pooled result was trusted too quickly in an earlier session before being diagnosed and corrected
  — recorded in full, including the fact that the pooled result was believed for one session first
  (`docs/phase6_signals.md`, "Simpson's paradox — what was actually found, including the pooled
  result trusted too quickly").
- **Precision@k ordering direction, not feature identity, determines whether a raw feature looks
  useful — the real (not the cited) numbers:**

  | Feature | Correctly directed (TRAIN-determined) | Naively directed (always "high = suspicious") |
  |---|---|---|
  | zscore_60d | 90.0% | 20.0% |
  | volume_ratio | 85.0% | 35.0% |
  | return_20d_context_only | 95.0% | 5.0% |

  All three collapse well below the 74.1% base rate under the naive direction and land at or above
  the categorical classifier's own precision (90.6%) under the correct one. `return_20d_context_only`
  is both the best performer here AND the one Phase 6's real numbers show survived stratification —
  not `volume_ratio`.

  **Caveat added per `P8-001` (§1): all three numbers above are measured under the raw
  `collapsed_90d` label, which Check 1(b) confirms shares its anchor with `return_20d_context_only`
  itself.** Re-run under the corrected, event-day-anchored label
  (`docs/phase8_robustness_checks.md`, `docs/phase8b_clean_label_features.md`), every feature's
  empirically-correct direction *flips* (TRAIN AUC moves from "low value predicts collapse" to
  "high value predicts collapse" for all three). `return_20d_context_only` — cited above as the best
  performer and the one that survived stratification — is now shown to REVERSE SIGN on real 2026
  hold-out data (pooled AUC 0.475, CI entirely below 0.5) and falls to 40.0% at precision@20, below
  the new label's 51.0% base rate: not weaker evidence, but the opposite direction, and it is
  withdrawn as a load-bearing feature (`docs/phase6_signals.md`'s own dated correction). `volume_ratio`
  (80.0% at precision@20) is weak but consistent under the clean label — real in 3 of 5 cap bands,
  chance in Micro/Mid — the ORIGINAL design hypothesis, not "confirmed" outright.
  `zscore_60d` falls to 15.0%, but its own pooled hold-out AUC (0.537) is still weak-but-consistent
  in the collapse-predicting direction — the two numbers describe different parts of its
  distribution (AUC: the bulk; P@20: the extreme tail), not a contradiction.
- **Lead time — led with the near-term spread, not the bare median.** Of 2,906 real 2026 events not
  already under surveillance but later flagged: **p10=2, p25=3, p50=14, p75=52, p90=95, max=168.**
  44.4% flagged within 10 sessions, 56.3% within 20. Not classically bimodal — a heavily front-
  loaded decay, no second peak. 385 events (3.5% of the full 10,850-event hold-out) were already
  under surveillance at `event_date` — not a warning, stated plainly and excluded from the lead-time
  pool by construction, not folded in as a zero. Full spread and by-class breakdown:
  `docs/phase8_evaluation_results.md` §Layer 2.

  **This describes only events that WERE flagged — it says nothing about whether classification
  predicts WHICH events get flagged (`docs/phase8_robustness_checks.md` Check 3).** Measured
  unconditionally (all eligible hold-out events, right-censored per horizon against the data's own
  2026-09-15 end): `UNEXPLAINED` is flagged by the exchange *less* often than `GROUNDED` at every
  horizon (11.2% vs. 16.6% within 20 sessions; 20.8% vs. 24.3% within 60), and far less often than
  `PARTIALLY_GROUNDED` (27.6%/38.1%/50.7% at 20/60/120 sessions — the highest of any class, a new
  finding this check was not looking for). ASM criteria are themselves price/volume-variation
  rules, so a flag a few sessions after a catalogued move can be the same rule firing on the same
  move after a publication lag — detection, not early warning. The flag rates do differ meaningfully
  by class, so the early-warning claim is not simply false — but not in the direction the original
  framing assumed. Separately: ~7% of the full hold-out (770 of 10,850) is excluded from every
  outcome label in this evaluation because the symbol's own trading history ends inside the
  90-session window while the broader market keeps trading — a real, disclosed survivorship gap
  that skews toward undercounting genuine collapses, not a neutral exclusion.
- **The naive 10%-move threshold (Baseline 2) — its real measured cost, not an assumed AUC.** No
  0.522-pooled AUC figure for this baseline exists in this project's output; what was measured is
  Brier 0.6553 (dramatically worse than random's 0.3328) — because almost every event in this
  z-score/volume-selected catalogue already clears a 10% one-day move, so the naive rule flags
  nearly everything and is punished hard by the ~26% that don't collapse. The COMPOSITION point is
  real even without that specific cited number: this catalogue's own selection criteria make a
  naive magnitude threshold nearly useless as a further filter.
- **A second Brier finding, not anticipated going in — and corrected by `docs/phase8_robustness_checks.md`
  Check 2.** The full classifier's raw Brier score (0.2024) does not beat predicting 2026's own true
  base rate for every event with no information at all (≈0.192) — directly explained by systematic
  under-confidence (2026 ran hotter than the 2019-2025 training period the scores were derived
  from). **That 0.192 figure is an ORACLE — it uses 2026's own realized mean, unknowable as of
  2025-12-31 — not a fair comparison.** The only constant baseline actually computable in advance
  (the real 2019-2025 base rate, 60.21%) scores **0.2111** on the same 6,049 events — worse than
  both the classifier (0.2024) and disclosure-tier-alone (0.2091). Against anything an evaluator
  could actually have used without seeing 2026, both beat the naive alternative; they only lose to
  a number computed from the answer key. Full reasoning: `docs/phase8_evaluation_results.md`
  §Layer 3; the corrected baseline table: `docs/phase8_robustness_checks.md` Check 2.

## 6. Limitations

- **Proportionality is not measured anywhere in this evaluation.** A `GROUNDED` disclosure and a
  move's actual magnitude are never compared. A 15% move on a disclosure worth 0.3% of revenue
  scores identically to one the disclosure plausibly justifies, in every metric in this document.
- **`collapsed_Nd` is a price-reversion proxy, not a determination of anything.** It is this
  project's own definition (does the price cross back through a pre-move base within N sessions),
  not a regulatory or expert judgment. A move that holds for reasons this project cannot observe
  (sector rotation, broad market conditions) scores identically to one that holds because a real,
  material disclosure caused it. The lead-time result is comparatively cleaner evidence because it
  is anchored to the exchange's own independent action, not to this proxy.
- **The 2026 hold-out window is short (~8.5 months) and this bounds what several measurements can
  show.** Lead time cannot structurally show a tail longer than the window itself — a real,
  multi-year long-tail pattern, if one exists in the full history, is invisible to this specific
  measurement. `UNEXPLAINED_ISOLATED`'s per-band cells in Layer 2 are thin (n=4-7) for the same
  reason — a short window simply does not produce many of an already-rare class.
- **Calibration against a train-derived score is close to tautological by construction**, and is
  reported as such, not as an independent finding — the ONE place it is genuinely informative is
  exactly where the tautology breaks (the documented under-confidence), because that is the one
  thing a frequency-based score evaluated on a held-out period can actually discover that isn't
  true by construction.
- **Threshold vintages differ between this evaluation and the live system**, and the one place this
  produced a measurable effect is documented (`docs/phase8_evaluation_results.md`, "A note on
  threshold vintages") — a 100-event spot-check of the real live agent system against the frozen-
  threshold deterministic rule found 99/100 matched, the one mismatch traced directly to a
  band-median boundary the two threshold vintages disagree on by a small amount.
- **The naive "just scale up predicted probabilities" fix to the Brier/calibration finding would
  mechanically improve the number without adding real information** — named explicitly here so it
  is never done and mistaken for an improvement.
- **Precision@k's dependence on scoring coarseness is real and only partially resolved.** The
  categorical score alone produces a 25-value ceiling and ties everything at the max (255 events
  tied, an arbitrary 20-of-255 "top 20"). The volume_ratio tie-break in §2 resolves ties but does
  not change the underlying categorical score's own coarseness — a genuinely fine-grained ranking
  would need a continuous primary score, which this project's classifier does not produce and was
  not asked to produce here.
- **This project observes only dates, never the exchange's reasoning.** The lead-time result shows
  when NSE acted relative to this system's own classification — it is not a claim about what NSE's
  surveillance actually looked at, weighed, or decided, none of which is visible to this project.
- **Every number here rests on this project's own bitemporal store and its own feature
  definitions.** No external audit, regulatory record, or independent dataset has checked any of
  these labels, features, or outcomes against ground truth outside this project's own construction
  of them.

## 7. The Phase 10 forward pre-registration — frozen, nothing evaluated yet

**A separate, new evaluation design from the Phase 6-8 classifier above, built because §1's
retraction showed that classifier's core axis (`momentum_high`/`return_20d_context_only`) does not
survive a clean label.** `docs/phase10_preregistration.md` and five amendments
(`docs/phase10_preregistration_amendments.md` through
[`_amendment5.md`](docs/phase10_preregistration_amendment5.md)) specify a new, four-input logistic
scoring function, fit once on 2019-2025 TRAIN data, evaluated **FORWARD-only** — 2026 is spent for
model selection (Evaluation Integrity note above) and is never reused as a hold-out for this design.

**Frozen inputs and coefficients** (`docs/phase10_preregistration_amendment5.md` §5, TRAIN
n=59,896): `delivery_low` (`delivery_pct_percentile_60d < 15.0`, coefficient +0.430, z=+23.88),
`isolated` (`same_date_event_count < 47`, +0.005, z=+0.30 — not distinguishable from zero, kept per
the original spec but not weighted as evidence), `volume_ratio_high_band_eligible` (Small/Large/Mega
only, +0.186, z=+9.36), and one-hot disclosure tier against a `NONE` reference
(`SUBSTANTIVE` −0.218 z=−8.88, `ROUTINE_ONLY` −0.062 z=−2.40, `UNKNOWN_COVERAGE` −0.162 z=−3.75),
intercept +0.262.

**Missing-data threshold: 4.3%** (TRAIN's final missing rate, 1.310%, plus a 3-point margin) — below
even the original pre-registration's speculative 5%, after `P8-012`/`P8-013`/`P8-014` together cut
what would otherwise have been a 6.838% TRAIN missing rate (a defect Amendment 4 asserted was
already unbiased without measuring it, and Amendment 5 found was not — `docs/DEFECT_REGISTER.md`
`P8-014`) down to 1.310%, with the gap that originally motivated this whole investigation (HOLD-OUT
missing far more than TRAIN) closed to 0.413pp.

**Evaluation window: 2026-09-16 through 2027-01-15 (~5,100 events expected), running no earlier than
~early June 2027** (10 sessions past the window's last event's own 90-session global horizon).
**Success requires BOTH**: a bootstrap 95% CI on Brier Skill Score (vs. a FAIR constant baseline)
that excludes zero, AND the new design's top-decile LIFT beating the CURRENT classifier's own
top-decile LIFT with a paired-bootstrap CI lower bound strictly above zero
(`docs/phase10_preregistration.md`; `docs/phase10_preregistration_amendments.md` §2;
`docs/phase10_preregistration_amendment2.md` §1).

**Pinned commit for the entire forward pipeline: `afe3e2bd07abe8b602c4119b916f7696a3c12131`**
(`docs/phase10_preregistration_amendment5.md` §9). **No forward outcome has existed at any point
this pre-registration was written or amended.** As of Amendment 5, it is declared FROZEN: a sixth
amendment is warranted only for a defect that would make the evaluation impossible to run, not for
further refinement of numbers already measured and settled.

**35 defects are logged against this project as a whole** (`docs/DEFECT_REGISTER.md`): 5 in NSE
ingestion (Phase 2), 3 in corporate-actions parsing (Phase 3, deferred/low severity), 13 in ASM/GSM
surveillance ingestion (Phase 4), and 14 across the evaluation and Phase 10 redesign work (Phase
8-10). The most recent, `P8-014`, is also the most structurally instructive: a fix for one
outcome-label selection bias (`P8-013`) silently introduced a second, worse one on exactly the
dimension it existed to fix, caught only because Amendment 5 measured the first fix's own effect
rather than assuming it had worked.

---

## The 2026 hold-out, run and reported

**Already run — this is not a pending step.** Every number in §1, §2, and the lead-time/collapse-
rate/calibration findings in §5 above IS the 2026 hold-out result; it is not a train-period result
awaiting a final pass. The full detail (10,850 hold-out events, thresholds frozen on 2019-2025
before 2026 was touched, per `scripts/phase8_freeze_thresholds.py`) lives in
`docs/phase8_evaluation_results.md`. Reported here even where it complicates the headline, per
instruction: the null-branch precision@k decision in §2, and the Brier-score finding in §5, are
both real 2026 hold-out results that do not flatter this project's own architecture, and both are
reported in full rather than smoothed into the headline.

---

## Summary (plain text, for pasting)

**Updated after `docs/phase8_robustness_checks.md` and `docs/phase8b_clean_label_features.md`
(`P8-001`) — this is the headline of the whole document now, not a late correction to it.** A
pre-registered check found Phase 8 scored against a label (`collapsed_90d`) that Phase 6 had
already shown tracks market drift, and that shares its own anchor with `return_20d_context_only`,
the classifier's core momentum input. Re-scored under a corrected, event-day-anchored,
market-relative label: disclosure-tier-alone's top-tier precision falls from 78.7% to 51.1%
(exactly its base rate — zero lift), and the classifier's falls from 90.6% to 28.6% on a tiny,
noisy cell (n=7, below base rate). On a corrected, comparable footing (lift over each label's own
base rate, since raw Brier/precision are not comparable across labels with different base rates —
an earlier framing that read drift-correction as "improving" the numbers is itself withdrawn),
drift-correction alone barely moves the classifier's lift (+16.4pp → +15.9pp); only removing the
shared anchor collapses it. **Layer 1 (100% of 29,764 claims verified) does not depend on this
label at all and is unaffected.** The follow-up feature re-analysis found the classifier's own core
axis (`return_20d_context_only`) reverses sign on real 2026 data under the clean label, that
`delivery_pct_percentile_60d` — unused in the classifier today — shows a real signal the coupled
label had hidden, and that the `PARTIALLY_GROUNDED` flag-rate finding is overwhelmingly a
`momentum_high` effect that cuts across disclosure tiers (even `GROUNDED`, which doesn't depend on
momentum at all, shows the same gap), not a disclosure-content finding.

Ran the specified decision rule on real 2026 hold-out data: baseline 5 (full system) beats
baseline 3 (disclosure tier alone) in point estimate at every k tested (10/20/50/100: +30/+20/+16/
+15 percentage points), but only clears the pre-specified CI-non-overlap bar at k=100, not at the
required k=20 AND k=50. Per the rule as written, that is the null branch: architecture adds nothing
confirmed at those k; its real value here is verification (100% of 29,764 claims checked, 786
independently re-derived from raw data) and honest reporting, not ranking power. **This test was
not independently re-run under the corrected label; §1/§2 note that its own categorical score is
exposed to the same anchor-coupling problem.**

Several specific figures in the request (P7-001 as a real defect, a 0.588/0.588 AUC tie, z_score
vs volume_ratio at 40%/65%, lead time p25=14) do not match this project's real computed output and
are not in this document. Real numbers used instead throughout, all traceable to source.

**A separate, forward-only redesign (`docs/phase10_preregistration.md` and five amendments) is now
FROZEN**, not evaluated: a four-input logistic scoring function fit on 2019-2025 TRAIN data,
missing-data threshold 4.3%, evaluation window 2026-09-16 through 2027-01-15, earliest possible run
~early June 2027, pinned to commit `afe3e2bd07abe8b602c4119b916f7696a3c12131`. Getting there took
five rounds of amendment because the pre-registration's own outcome label carried two real,
sequentially-discovered defects (`P8-013`, then `P8-014` — a fix for the first quietly introducing
a second, worse one) — both found by measuring the label's own statistical properties against model
inputs, not by looking at any forward result, since none exists yet.

What surprised me: baseline 5's point-estimate lead is real and consistent at every single k, wide
enough to look meaningful, but this hold-out (n=6,049) is too small to confirm it at k=20/50 under
a strict non-overlap test — a case where "the effect looks real but the sample can't confirm it
yet" is itself the honest, reportable finding, not a reason to loosen the rule after seeing the
data. **What surprised me more, from the robustness check: the effect that WAS confirmed (baseline
4 vs. 3 in Layer 3, non-overlapping CIs) turned out to be the one that didn't survive — and the
reason turned out to be a specific, findable mechanical artifact (a shared anchor point) rather
than a vague "labels are noisy" caveat, which is exactly the kind of thing a pre-registered
adversarial check is supposed to catch before a headline ships.**
