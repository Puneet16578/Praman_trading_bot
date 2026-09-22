"""Phase 7b production event classifier -- GROUNDED / PARTIALLY_GROUNDED / UNEXPLAINED /
UNEXPLAINED_ISOLATED, plus the UNEXPLAINED_UNKNOWN_COVERAGE data-gap label for symbols with no
cached announcement data at all. Rules approved in docs/phase7b_classification_design.md, where
they were validated against all 75,300 real catalogued events (class shares, sanity bounds) before
this module existed -- this module APPLIES those same rules; it does not re-derive or re-tune them
(CLAUDE.md invariant 12 + explicit instruction: never tune thresholds to produce separation).

The classification is a coarse summary. Every event this module classifies also carries its own
raw signal fields regardless of which class it lands in -- volume_ratio, delivery percentile,
z-score, close-to-close, co-movement count, cap band, ASM/GSM stage as-of the event, and lead time
to any subsequent flag -- so a reader can independently re-derive or disagree with the thresholds
rather than trust this project's conjunction blindly.

PROVENANCE_NOTE is fixed, deterministic text meant to be rendered into every report's OUTPUT (not
only this module's docstring or the design doc) -- the classification rests on this project's own
thresholds, not a validated predictor. Phase 6's original 0.611-0.70 ceiling figure is WITHDRAWN
(P8-001, docs/DEFECT_REGISTER.md): its two dominant features reverse sign under a label that does
not share this classifier's own momentum anchor. Under that corrected label, this classifier's
top-scored tier shows no precision lift over its own base rate, and its aggregate Brier Skill
Score is ~1.8% vs. a constant baseline (docs/phase8_robustness_checks.md,
docs/phase8b_clean_label_features.md).
"""
from __future__ import annotations
import bisect
from dataclasses import dataclass

GROUNDED = "GROUNDED"
PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
UNEXPLAINED = "UNEXPLAINED"
UNEXPLAINED_ISOLATED = "UNEXPLAINED_ISOLATED"
UNEXPLAINED_UNKNOWN_COVERAGE = "UNEXPLAINED_UNKNOWN_COVERAGE"

ALL_CLASSES = (GROUNDED, PARTIALLY_GROUNDED, UNEXPLAINED, UNEXPLAINED_ISOLATED, UNEXPLAINED_UNKNOWN_COVERAGE)

PROVENANCE_NOTE = (
    "Classification uses this project's own thresholds (disclosure tier, momentum persistence vs. "
    "real per-cap-band medians, co-movement vs. this catalogue's own distribution) -- not a "
    "validated predictor. A robustness review (P8-001) found the original Phase 6/8 ceiling and "
    "top-tier precision figures were substantially an artifact of a label sharing this "
    "classifier's own momentum anchor: under a corrected, decoupled label, this classifier's "
    "top-scored tier shows NO precision lift over its own base rate, and its aggregate Brier "
    "Skill Score is approximately 1.8% versus a constant baseline. UNEXPLAINED and "
    "UNEXPLAINED_ISOLATED describe an absence of a substantive disclosure and where the measured "
    "signals fall -- they are not a finding about why the price moved, and carry no conclusion "
    "about the cause of the move."
)

# Measured directly (scripts/analyze_collapse_rate_confidence_intervals.py, 95% Wilson CIs,
# data/processed/collapse_rate_by_class.csv): GROUNDED and UNEXPLAINED_ISOLATED are the one pair
# in this five-class scheme whose 30/60/90-session collapse rates are NOT statistically
# distinguishable -- their CIs overlap in every one of 5 cap bands x 3 horizons checked (15/15).
# Every other pair (PARTIALLY_GROUNDED vs UNEXPLAINED included) separates cleanly, with disjoint
# CIs and gaps of 30+ points, in all 15 comparisons -- see docs/phase7b_classification_design.md.
#
# Decision (not a merge): GROUNDED and UNEXPLAINED_ISOLATED describe opposite findings -- a
# substantive disclosure vs. none at all -- so collapsing them would hide the one thing this
# classification exists to preserve (what was FOUND). They stay separate classes; this note is
# rendered at the point of classification (synthesis.py), not buried in a footnote, whenever an
# event lands in either of the two classes it concerns.
INDISTINGUISHABLE_PAIR = frozenset({GROUNDED, UNEXPLAINED_ISOLATED})
INDISTINGUISHABLE_PAIR_NOTE = (
    "GROUNDED and UNEXPLAINED_ISOLATED are not distinguishable by 30/60/90-session collapse rate "
    "in any market-cap band measured (95% confidence intervals overlap in all 5 bands and all 3 "
    "horizons checked). They differ in what was found -- a substantive disclosure versus none at "
    "all -- not in what followed."
)

# Attached to EVERY report next to its classification, not only inside the longer PROVENANCE_NOTE
# paragraph above -- a reader looking at one event's report should see the system's measured
# discriminative power at the exact point it presents a classification, not have to find it in a
# general disclaimer. Same correction as PROVENANCE_NOTE (P8-001, docs/DEFECT_REGISTER.md); stated
# again here, standalone, because "wherever it presents a classification" was explicit. The
# original Phase 6 AUC 0.611-0.70 figure this note used to cite is WITHDRAWN -- see
# docs/phase8_robustness_checks.md and docs/phase8b_clean_label_features.md for the full
# re-measurement.
DISCRIMINATIVE_POWER_NOTE = (
    "Measured discriminative power of this classification (P8-001 correction): under a "
    "robustness-corrected label, this classifier's top-scored tier shows NO precision lift over "
    "its own base rate, and its aggregate Brier Skill Score is approximately 1.8% versus a "
    "constant baseline -- read this classification as directional evidence at best, not a "
    "reliable predictor of whether this specific move held or reversed."
)

# The real Phase 5 catalogue-membership rule (scripts/build_final_event_catalogue.py:is_event(),
# the single source of truth -- these two numbers are duplicated here, not re-derived, matching
# this project's existing convention for approved constants, e.g. ISOLATED_COMOVEMENT_THRESHOLD in
# scripts/build_event_classifications.py). It is a strict AND, not an OR: EVERY catalogued event
# satisfies BOTH |z-score(60d)| > 2.5 AND volume_ratio > 2.0x by construction -- there is no such
# thing as an event that "qualified on z-score alone" in this catalogue. A report that only shows
# one of the two numbers invites exactly that wrong reading; stating both, and that both are
# required, lets a reader verify catalogue membership themselves instead of assuming either an OR
# or a single deciding criterion.
CATALOGUE_Z_THRESHOLD = 2.5
CATALOGUE_VOL_THRESHOLD = 2.0

# GROUNDED is gated entirely on disclosure tier, with no check of whether the disclosure's
# apparent materiality is proportionate to the move's size -- a "Board Meeting Intimation" (which
# discloses only that a meeting will occur, not what was decided) and a major order win are both
# SUBSTANTIVE under this project's category mapping (docs/phase7a_disclosure_sourcing.md), and
# nothing in this design distinguishes a proportionate explanation from a token one. This was the
# original spec's core question and this design does not answer it -- stated here so it renders in
# the report's own output (attached whenever classification is GROUNDED), not only in the design
# doc's limitations section.
GROUNDED_LIMITATION_NOTE = (
    "GROUNDED means a substantive disclosure was found in the pre-event window -- it does NOT mean "
    "the disclosure's apparent materiality is proportionate to the size of this move. A Board "
    "Meeting Intimation (which discloses only that a meeting will occur, not its outcome) and a "
    "major order win are both classified SUBSTANTIVE under this project's category mapping; this "
    "report does not distinguish a disclosure that plausibly explains the move's magnitude from "
    "one that does not. See the disclosure list above for what was actually found, and judge "
    "proportionality directly from it."
)

# Phase 8's stated job, not yet done -- named explicitly here so a reader does not mistake the
# absence of a comparison for evidence the classifier is doing well (or poorly): no random,
# naive-threshold, disclosure-tier-only, or plain-deterministic-classifier baseline has been
# computed yet. Once Phase 8 produces them, this note is where the real comparison belongs.
BASELINE_COMPARISON_NOTE = (
    "No comparable baseline (random, naive single-threshold, disclosure-tier-only, or a simpler "
    "deterministic classifier) has been computed against this system yet -- Phase 8 scope, not "
    "done here. This classification's measured discriminative power (above) is not yet compared "
    "against what a simpler method would achieve on the same data."
)

@dataclass(frozen=True)
class ClassificationThresholds:
    """Real, measured thresholds this module classifies against -- computed once per catalogue
    snapshot by scripts/build_event_classifications.py from the real data, never re-derived per
    event and never tuned to move any class's share."""
    band_median_abs_return_20d: dict[str, float]
    isolated_comovement_threshold: int

def classify_event(
    *, disclosure_tier: str, has_coverage: bool, momentum_high: bool | None,
    same_date_event_count: int | None, thresholds: ClassificationThresholds,
) -> tuple[str, bool | None]:
    """Pure rule application. `disclosure_tier` is one of SUBSTANTIVE/ROUTINE_ONLY/NONE (from
    classify_disclosure_window); `has_coverage=False` short-circuits straight to
    UNEXPLAINED_UNKNOWN_COVERAGE regardless of the other arguments, since a symbol with no cached
    announcement data was never actually checked for a disclosure -- "not checked" must never be
    conflated with "checked, found nothing" (disclosure_tier "NONE").

    Returns (classification, is_isolated). is_isolated is always computed and returned (even for
    SUBSTANTIVE/ROUTINE_ONLY events where it wasn't the deciding factor) because it is one of the
    signal fields every event reports regardless of class.

    momentum_high=None (return_20d unavailable) is treated the same as momentum_high=False --
    the conservative default (CLAUDE.md invariant 12: missing evidence must never inflate a
    grounded-adjacent classification)."""
    if not has_coverage:
        return UNEXPLAINED_UNKNOWN_COVERAGE, None

    is_isolated = (
        same_date_event_count is not None
        and same_date_event_count < thresholds.isolated_comovement_threshold
    )

    if disclosure_tier == "SUBSTANTIVE":
        return GROUNDED, is_isolated
    if disclosure_tier == "ROUTINE_ONLY":
        return (PARTIALLY_GROUNDED if momentum_high is True else UNEXPLAINED), is_isolated
    # NONE
    if is_isolated:
        return UNEXPLAINED_ISOLATED, is_isolated
    return (PARTIALLY_GROUNDED if momentum_high is True else UNEXPLAINED), is_isolated

def momentum_is_high(abs_return_20d: float | None, cap_band: str, thresholds: ClassificationThresholds) -> bool | None:
    if abs_return_20d is None:
        return None
    median = thresholds.band_median_abs_return_20d.get(cap_band)
    if median is None:
        return None
    return abs_return_20d >= median

@dataclass
class EventSignals:
    """Every field here is reported on every classified event, regardless of class -- the
    classification is a summary; these fields are the evidence a reader can check independently."""
    symbol: str
    event_date: str
    classification: str
    disclosure_tier: str          # SUBSTANTIVE / ROUTINE_ONLY / NONE / UNKNOWN_COVERAGE
    momentum_high: bool | None
    is_isolated: bool | None
    cap_band: str
    volume_ratio: float | None
    delivery_pct: float | None
    delivery_pct_percentile_60d: float | None
    zscore_60d: float | None
    close_to_close_60d: float | None
    same_date_event_count: int | None
    asm_stage_as_of: str | None
    gsm_stage_as_of: str | None
    sessions_to_subsequent_flag: int | None
    subsequent_flag_note: str

def sessions_to_subsequent_flag(
    *, timeline, event_date: str, trading_days: list[str],
    asm_stage_as_of: str | None, gsm_stage_as_of: str | None,
) -> tuple[int | None, str]:
    """Sessions between event_date and the first ASM/GSM ENTRY strictly after it, using
    `timeline` (a SurveillanceTimeline, src/signals/surveillance_state.py) built once per symbol
    with full retrospective knowledge -- correct here because this is a backward-looking "what
    actually happened later" measurement, not a live signal (Section 7 governs prediction as-of a
    date, not labeling).

    `asm_stage_as_of`/`gsm_stage_as_of` are the catalogue's OWN already-computed, bitemporally
    correct as-of-event_date fields (event_catalogue_loose_zscore_only.csv) -- reused here rather
    than recomputed, both for consistency and because re-deriving "was this symbol flagged as of
    event_date" from scratch would duplicate logic that already exists and is already tested.

    Returns (None, "already under surveillance as of event_date") if either mechanism shows a
    non-null stage as of the event -- there is no lead time to measure, it was already flagged.
    Returns (None, "no subsequent flag as of latest data") if never flagged afterward.
    Otherwise returns the real trading-session gap and a descriptive note naming the mechanism,
    stage, and date of that first subsequent flag.
    """
    if asm_stage_as_of or gsm_stage_as_of:
        return None, "already under surveillance as of event_date"

    entry = timeline.first_entry_after(event_date)
    if entry is None:
        return None, "no subsequent flag as of latest data"

    flag_date = entry["event_date"]
    idx_event = bisect.bisect_left(trading_days, event_date)
    idx_flag = bisect.bisect_left(trading_days, flag_date)
    if (idx_event >= len(trading_days) or trading_days[idx_event] != event_date
            or idx_flag >= len(trading_days) or trading_days[idx_flag] != flag_date):
        return None, (f"subsequent flag on {flag_date} ({entry['mechanism']} {entry['to_stage']}) "
                       f"but session gap not computable from this symbol's own trading calendar")
    gap = idx_flag - idx_event
    return gap, f"first flagged {gap} session(s) after event_date ({entry['mechanism']} {entry['to_stage']}, {flag_date})"
