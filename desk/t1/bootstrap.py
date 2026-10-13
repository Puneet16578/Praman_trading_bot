"""Moving-block date bootstrap for T1 (pre-registration and addendum 1). Built and tested now;
nothing here touches an outcome. Replicates resample complete market-date clusters: every
stock-day on a sampled date is carried, as many times as the date is drawn."""
from __future__ import annotations

import math

import numpy as np

REPLICATES, SEED = 2000, 20261001
BLOCK_V1_V2, BLOCK_V3 = 60, 20


def block_draws(n_dates: int, block: int, replicates: int = REPLICATES, seed: int = SEED) -> np.ndarray:
    """[replicate, n_dates] date indices: ceil(T/block) blocks of `block` consecutive dates, starts
    uniform among the T-block+1 valid starts with replacement, concatenated and truncated to T.
    Each call has its own generator, so each block length has its own draws (addendum 1)."""
    if n_dates < block:
        raise ValueError(f"{n_dates} dates cannot hold a {block}-session block")
    rng = np.random.default_rng(seed)
    k = math.ceil(n_dates / block)
    starts = rng.integers(0, n_dates - block + 1, size=(replicates, k))
    return (starts[:, :, None] + np.arange(block)).reshape(replicates, -1)[:, :n_dates]


def multiplicities(draws: np.ndarray, n_dates: int) -> np.ndarray:
    """[replicate, date] how many times each date is carried in each replicate."""
    return np.stack([np.bincount(d, minlength=n_dates) for d in draws])


def replicate_totals(draws: np.ndarray, per_date: np.ndarray) -> np.ndarray:
    """Per-replicate totals of a per-date quantity (for example a count of stock-days), with every
    date's stock-days carried at its multiplicity, including dates whose values are missing (NaN
    contributes nothing to the total but its stock-days still count where the caller counts them)."""
    weights = multiplicities(draws, len(per_date))
    return weights @ np.nan_to_num(np.asarray(per_date, dtype=float))
