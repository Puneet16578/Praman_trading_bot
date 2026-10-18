"""Bootstrap uncertainty for T1 contrasts.

Pre-registration, "Outcome, metrics and uncertainty": "Bootstrap: 2,000 replicates, seed 20261001,
resampling complete market-date clusters in MOVING BLOCKS ... Carry every stock-day on each sampled
date, including multiplicities and missingness. Reuse draws for all paired contrasts within a
period. No cross-period blocks or individual-stock resampling. Quintile boundaries and development
weights remain fixed. Report percentile 95% intervals descriptively and 98.333333% two-sided
intervals (Bonferroni family of THREE primary contrasts) for the fixed success criteria. Report
usable draws; require at least 1,900 usable draws for a decision."
Addendum 1: "V1 and V2 use moving blocks of 60 consecutive global sessions; V3 keeps 20 ... Each
block length has its own set of draws from its own generator, seeded 20261001. A contrast and its
matched V0 comparison use the draws of that variant's block length."
The draws themselves are desk/t1/bootstrap.py (built and tested with the features).
"""
from __future__ import annotations

import numpy as np

from desk.t1.bootstrap import BLOCK_V1_V2, BLOCK_V3, block_draws, multiplicities
from desk.t1_outcome.contrasts import MIN_DATES, MIN_VALID, QUINTILES, STATES

BLOCK = {"V1": BLOCK_V1_V2, "V2": BLOCK_V1_V2, "V3": BLOCK_V3}
FAMILY = 3
DESCRIPTIVE_LEVEL = 0.95
FAMILY_LEVEL = 1 - 0.05 / FAMILY                  # 98.333333%
USABLE_RULES = ("computable", "computable_with_sample_minimums")   # open choice 2
PERCENTILE_METHODS = ("linear", "lower", "higher", "nearest", "midpoint", "inverted_cdf",
                      "averaged_inverted_cdf", "closest_observation", "interpolated_inverted_cdf",
                      "hazen", "weibull", "median_unbiased", "normal_unbiased")   # open choice 3 (NumPy's)


def period_draws(n_dates: int) -> dict:
    """One set of draws per block length for a period, reused by every contrast in it."""
    return {block: block_draws(n_dates, block) for block in (BLOCK_V1_V2, BLOCK_V3)}


def _per_date_counts(rows: dict, n_dates: int):
    """[state, quintile, date] valid and adverse counts."""
    valid = np.zeros((len(STATES), len(QUINTILES), n_dates))
    adverse = np.zeros_like(valid)
    ok = np.isfinite(rows["outcome"])
    for a, s in enumerate(STATES):
        for b, q in enumerate(QUINTILES):
            m = ok & (rows["state"] == s) & (rows["quintile"] == q)
            valid[a, b] = np.bincount(rows["date_idx"][m], minlength=n_dates)
            adverse[a, b] = np.bincount(rows["date_idx"][m], weights=rows["outcome"][m], minlength=n_dates)
    return valid, adverse


def replicate_differences(rows: dict, weights: dict, draws: np.ndarray, *, usable: str) -> np.ndarray:
    """The standardised difference in each replicate (NaN when the replicate is not usable).
    Every stock-day on a drawn date counts as many times as the date is drawn. Open choice 2: a
    replicate is usable when the standardised difference is computable in it ("computable"), or only
    when every state-quintile cell also meets 100 valid outcomes and 30 distinct dates
    ("computable_with_sample_minimums")."""
    if usable not in USABLE_RULES:
        raise ValueError(f"usable must be one of {USABLE_RULES}")
    n_dates = draws.shape[1]
    weight = multiplicities(draws, n_dates)                       # [replicate, date]
    valid, adverse = _per_date_counts(rows, n_dates)
    v = np.einsum("rt,sqt->rsq", weight, valid)
    a = np.einsum("rt,sqt->rsq", weight, adverse)
    with np.errstate(invalid="ignore", divide="ignore"):
        rate = np.where(v > 0, a / v, np.nan)
    w = np.array([weights[q] for q in QUINTILES])
    positive = w > 0
    diff = rate[:, 0, :] - rate[:, 1, :]                          # adverse state minus other
    ok = np.all(np.isfinite(diff[:, positive]), axis=1)
    if usable == "computable_with_sample_minimums":
        dates = np.einsum("rt,sqt->rsq", (weight > 0).astype(float), (valid > 0).astype(float))
        ok &= np.all((v >= MIN_VALID) & (dates >= MIN_DATES), axis=(1, 2))
    out = np.full(draws.shape[0], np.nan)
    out[ok] = np.nansum(diff[ok][:, positive] * w[positive], axis=1)
    return out


def intervals(replicates: np.ndarray, *, method: str) -> dict:
    """Percentile intervals over the usable replicates. Open choice 3: the text says "percentile"
    intervals but not how a percentile between two draws is taken."""
    if method not in PERCENTILE_METHODS:
        raise ValueError(f"method must be one of NumPy's percentile methods: {PERCENTILE_METHODS}")
    usable = replicates[np.isfinite(replicates)]
    if usable.size == 0:
        return dict(usable_draws=0, descriptive_95=None, family=None)

    def band(level):
        tail = (1 - level) / 2 * 100
        return tuple(float(x) for x in np.percentile(usable, [tail, 100 - tail], method=method))
    return dict(usable_draws=int(usable.size), descriptive_95=band(DESCRIPTIVE_LEVEL), family=band(FAMILY_LEVEL))


def replicate_baseline(rows: dict, weights: dict, draws: np.ndarray) -> np.ndarray:
    """The matched V0 comparison on the same draws (addendum 1): the standardised V0 adverse20 rate
    on rows whose variant state and outcome are known, per replicate (NaN when a positive-weight
    quintile has no such row in the replicate). Descriptive only."""
    n_dates = draws.shape[1]
    weight = multiplicities(draws, n_dates)
    known = np.isfinite(rows["state"]) & np.isfinite(rows["outcome"])
    w = np.array([weights[q] for q in QUINTILES])
    rates = []
    for q in QUINTILES:
        m = known & (rows["quintile"] == q)
        v = weight @ np.bincount(rows["date_idx"][m], minlength=n_dates)
        a = weight @ np.bincount(rows["date_idx"][m], weights=rows["outcome"][m], minlength=n_dates)
        with np.errstate(invalid="ignore", divide="ignore"):
            rates.append(np.where(v > 0, a / v, np.nan))
    rates = np.stack(rates, axis=1)                                # [replicate, quintile]
    positive = w > 0
    ok = np.all(np.isfinite(rates[:, positive]), axis=1)
    out = np.full(draws.shape[0], np.nan)
    out[ok] = rates[ok][:, positive] @ w[positive]
    return out
