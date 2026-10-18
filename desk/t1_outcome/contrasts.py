"""T1 contrasts: per-quintile tables, the standardised risk difference and the decision checks.

Rows are one period's eligible stock-days, as aligned arrays:
- `date_idx`: the row's decision date, as an index into the period's list of bootstrap dates;
- `quintile`: 1-5, from the frozen development boundaries;
- `state`: 1.0 adverse state, 0.0 the other state, NaN UNKNOWN (V1, V2 or V3);
- `outcome`: 1.0 adverse20, 0.0 not, NaN unavailable.
The predicted sign is positive for all three variants (pre-registration: "adverse regime has a
higher adverse20 rate", "weak breadth has a higher adverse20 rate", "negative relative strength
has a higher adverse20 rate"), so a risk difference is adverse state minus the other state.
"""
from __future__ import annotations

import numpy as np

from desk.t1.features import spells

QUINTILES = (1, 2, 3, 4, 5)
STATES = (1.0, 0.0)
COVERAGE_MIN = 0.80          # "coverage at least 80% of eligible stock-days in each evaluated period"
MIN_VALID, MIN_DATES = 100, 30   # "at least 100 valid outcomes and 30 distinct dates in EACH state in EACH quintile"
MIN_SPELLS = 5               # addendum 1: "at least 5 separate spells", V1 and V2 only
MIN_DIFFERENCE = 0.01        # "standardized risk difference >= 1 percentage point"
MIN_POSITIVE_QUINTILES = 4   # "the predicted positive sign in at least four of five quintiles"
SPELL_VARIANTS = ("V1", "V2")
COVERAGE_NUMERATORS = ("state_known", "state_and_outcome_known")   # open choice 1


def cells(rows: dict) -> dict:
    """Pre-registration: "For each variant, period, state and quintile report candidates,
    valid/missing outcomes, date clusters, adverse20 count/rate and risk difference (adverse minus
    other)." Date clusters are the distinct decision dates with a valid outcome in the cell."""
    out = {}
    valid = np.isfinite(rows["outcome"])
    for s in STATES:
        for q in QUINTILES:
            mask = (rows["state"] == s) & (rows["quintile"] == q)
            v = mask & valid
            n_valid, adverse = int(v.sum()), int((rows["outcome"][v] == 1).sum())
            out[(s, q)] = dict(candidates=int(mask.sum()), valid=n_valid, missing=int(mask.sum()) - n_valid,
                               dates=int(np.unique(rows["date_idx"][v]).size), adverse=adverse,
                               rate=adverse / n_valid if n_valid else None)
    for q in QUINTILES:
        a, o = out[(1.0, q)]["rate"], out[(0.0, q)]["rate"]
        out[("difference", q)] = None if a is None or o is None else a - o
        # "Report risk ratios only as secondary descriptive measures if both rates are nonzero."
        out[("ratio", q)] = a / o if a and o else None
    return out


def baseline_weights(quintile_of_development_candidates: np.ndarray) -> dict:
    """Pre-registration: "the development baseline candidate shares, fixed for both periods and all
    draws": each quintile's share of the development V0 candidates (every eligible development
    stock-day with a quintile, whether or not its outcome is valid)."""
    q = np.asarray(quintile_of_development_candidates)
    total = int(np.isin(q, QUINTILES).sum())
    return {k: int((q == k).sum()) / total for k in QUINTILES}


def standardized(table: dict, weights: dict) -> float | None:
    """Pre-registration: "Standardized primary difference = sum of quintile differences weighted by
    the development baseline candidate shares ... If either state lacks valid outcomes in a
    positive-weight quintile, standardized comparison is unavailable; never renormalize away that
    quintile." Returns None when unavailable."""
    total = 0.0
    for q in QUINTILES:
        if weights[q] > 0:
            d = table[("difference", q)]
            if d is None:
                return None
            total += weights[q] * d
    return total


def matched_baseline(rows: dict, weights: dict) -> dict:
    """Pre-registration: "Compare V1-V3 to V0 on matched available rows and show those rows'
    baseline rate and coverage": the V0 (volatility-quintile) adverse20 rate on the rows whose
    variant state is known, per quintile and standardised with the same weights."""
    known = np.isfinite(rows["state"]) & np.isfinite(rows["outcome"])
    per_q = {}
    for q in QUINTILES:
        m = known & (rows["quintile"] == q)
        per_q[q] = float(rows["outcome"][m].mean()) if m.any() else None
    standard = None if any(per_q[q] is None for q in QUINTILES if weights[q] > 0) else \
        sum(weights[q] * per_q[q] for q in QUINTILES if weights[q] > 0)
    return dict(rows=int(known.sum()), rate_by_quintile=per_q, standardized_rate=standard)


def coverage(rows: dict, *, numerator: str) -> float:
    """The share of the period's eligible stock-days that the contrast covers. Open choice 1: the
    text does not say whether a covered row needs only its state, or its state and a valid outcome."""
    if numerator not in COVERAGE_NUMERATORS:
        raise ValueError(f"numerator must be one of {COVERAGE_NUMERATORS}")
    covered = np.isfinite(rows["state"])
    if numerator == "state_and_outcome_known":
        covered &= np.isfinite(rows["outcome"])
    return float(covered.mean()) if covered.size else 0.0


def sample_shortfalls(table: dict) -> list[str]:
    """Each state in each quintile needs 100 valid outcomes and 30 distinct dates."""
    short = []
    for s in STATES:
        for q in QUINTILES:
            c = table[(s, q)]
            if c["valid"] < MIN_VALID or c["dates"] < MIN_DATES:
                short.append(f"{'adverse' if s == 1.0 else 'other'} state, quintile {q}: "
                             f"{c['valid']} valid outcomes, {c['dates']} dates")
    return short


def spell_count(states_by_date: list) -> int:
    """Addendum 1: spells on the decision dates the period evaluates, counted before any outcome is
    loaded (desk.t1.features.spells: runs under 20 known non-adverse sessions apart merge; UNKNOWN
    never separates)."""
    return len(spells(states_by_date))


def positive_quintiles(table: dict) -> int:
    return sum(1 for q in QUINTILES if table[("difference", q)] is not None and table[("difference", q)] > 0)


def decide(variant: str, *, table: dict, standardized_difference, cover: float, usable_draws: int,
           family_interval, spells_in_period: int | None) -> dict:
    """Pre-registration "Success criteria": a contrast failing any coverage, sample or draw
    requirement (or addendum 1's spell rule) is INCONCLUSIVE, "not a passed test or evidence of no
    association". Otherwise development success needs all three of: standardised difference >= 1
    percentage point, family-adjusted interval strictly above zero, positive sign in >= 4 of 5
    quintiles."""
    reasons = []
    if cover < COVERAGE_MIN:
        reasons.append(f"coverage {cover:.4f} below {COVERAGE_MIN}")
    reasons += sample_shortfalls(table)
    if usable_draws < 1900:
        reasons.append(f"{usable_draws} usable bootstrap draws, fewer than 1,900")
    if variant in SPELL_VARIANTS:
        if spells_in_period is None:
            raise ValueError(f"{variant} needs its spell count (addendum 1)")
        if spells_in_period < MIN_SPELLS:
            reasons.append(f"{spells_in_period} spells, fewer than {MIN_SPELLS}")
    if standardized_difference is None:
        reasons.append("standardised difference unavailable")
    if reasons:
        return dict(variant=variant, result="INCONCLUSIVE", reasons=reasons)
    failed = []
    if standardized_difference < MIN_DIFFERENCE:
        failed.append(f"standardised difference {standardized_difference:.4f} below {MIN_DIFFERENCE}")
    if not family_interval[0] > 0:
        failed.append(f"family-adjusted interval lower bound {family_interval[0]:.4f} not above zero")
    if positive_quintiles(table) < MIN_POSITIVE_QUINTILES:
        failed.append(f"positive sign in {positive_quintiles(table)} of 5 quintiles")
    return dict(variant=variant, result="NOT_SUCCESS" if failed else "SUCCESS", reasons=failed)
