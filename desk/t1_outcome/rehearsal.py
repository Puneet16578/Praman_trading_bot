"""T1 rehearsal (user decision 2026-10-18): the whole development pipeline with the outcome replaced
by seeded random labels, to measure runtime, memory, coverage, sample sizes and usable draws.

No outcome is read. The only forward look is the one the user allowed: whether a decision's outcome
window has all 20 bars (each with a positive open, high, low and close) and no unadjustable action,
which the real reader requires before it would compute a label. No price is compared with another
price or with a threshold. Labels are then drawn from a seeded generator for every eligible
stock-day (the same draws whatever the prices) and kept only where the window is complete.
`outcomes_sealed()` makes the real reader and the firewall's evaluator raise for the whole
rehearsal; tests run the rehearsal inside it.

The choices passed in are those of the user's draft addendum 3 ((b), (e)-(h)); it is not yet
recorded in the pre-registration. Nothing here opens a store: scripts/t1_rehearsal.py loads the
panel and calls `rehearse`.
"""
from __future__ import annotations

from contextlib import contextmanager

import numpy as np

from desk.t1.features import FORWARD_SESSIONS, quintile
from desk.t1_outcome import contrasts as C
from desk.t1_outcome import uncertainty as U

REHEARSAL_SEED = 20261018
REHEARSAL_RATE = 0.10        # arbitrary: the labels are noise and say nothing about any stock
VARIANTS = ("V1", "V2", "V3")
_SEALED = (("desk.t1_outcome.reader", "read_adverse20"), ("desk.t1_outcome.reader", "_labels"),
           ("desk.t1_outcome.reader", "evaluate_event"), ("desk.outcome_firewall", "evaluate_event"),
           ("desk.outcome_firewall", "require_outcome_access"))


class RealOutcomeSealed(RuntimeError):
    """Raised if anything tries to read the real outcome during the rehearsal."""


@contextmanager
def outcomes_sealed():
    """For the rehearsal's duration, the real outcome reader and the firewall's entry points raise."""
    import importlib

    def refuse(*_args, **_kwargs):
        raise RealOutcomeSealed("The real T1 outcome is sealed during the rehearsal.")
    saved = []
    for module_name, attribute in _SEALED:
        module = importlib.import_module(module_name)
        saved.append((module, attribute, getattr(module, attribute)))
        setattr(module, attribute, refuse)
    try:
        yield
    finally:
        for module, attribute, original in saved:
            setattr(module, attribute, original)


def complete_windows(panel, i: int, cols: np.ndarray) -> np.ndarray:
    """True where decision session i's next 20 sessions all have a bar with a positive open, high, low
    and close, with no unadjustable action in the window and a positive decision close. Presence and
    positivity only: no price is compared with any other."""
    window = slice(i + 1, i + 1 + FORWARD_SESSIONS)
    if i + FORWARD_SESSIONS >= len(panel.sessions):
        return np.zeros(len(cols), dtype=bool)
    present = np.all([np.all(np.isfinite(b) & (np.nan_to_num(b) > 0), axis=0)
                      for b in (np.asarray(a[window][:, cols], dtype=float)
                                for a in (panel.open, panel.high, panel.low, panel.close))], axis=0)
    unbroken = (panel.breaks[i + FORWARD_SESSIONS, cols] - panel.breaks[i, cols]) == 0
    decision = panel.close[i, cols]
    return present & unbroken & np.isfinite(decision) & (np.nan_to_num(decision) > 0)


def development_rows(panel, out, cause, period, bounds, *, seed: int, rate: float):
    """The development period's eligible stock-days as aligned arrays, with random labels.
    Draft addendum 3 (h): the bootstrap's dates are the development calendar (after (b)) from its
    first session up to the last before the purged sessions, i.e. the sessions labelled
    "development"; a date with no usable observation stays in the list and contributes nothing."""
    dev = np.flatnonzero(period == "development")
    rng = np.random.default_rng(seed)
    date_idx, quint, v3, outcome, complete_all = [], [], [], [], []
    for k, i in enumerate(dev):
        cols = np.flatnonzero(cause[i] == "")
        if cols.size == 0:
            continue
        complete = complete_windows(panel, int(i), cols)
        draws = rng.random(cols.size)                     # drawn for every eligible row, prices unseen
        labels = np.full(cols.size, np.nan)
        labels[complete] = (draws[complete] < rate).astype(float)
        date_idx.append(np.full(cols.size, k))
        quint.append(quintile(out["atr_pct"][i, cols], bounds))
        v3.append(out["v3_negative"][i, cols])
        outcome.append(labels)
        complete_all.append(complete)
    date_idx = np.concatenate(date_idx)
    base = dict(date_idx=date_idx, quintile=np.concatenate(quint), outcome=np.concatenate(outcome))
    states = {"V1": out["v1_adverse"][dev][date_idx], "V2": out["v2_adverse"][dev][date_idx], "V3": np.concatenate(v3)}
    return dev, base, states, np.concatenate(complete_all)


def _state_list(values):
    return [None if not np.isfinite(v) else bool(v) for v in values]


def rehearse(panel, out, cause, period, bounds, *, seed: int, rate: float, usable: str, method: str,
             coverage_numerator: str) -> dict:
    """Everything the development run would compute, on random labels. Reports only what does not
    depend on the labels: coverage, outcome-window availability, sample sizes, spells, usable draws,
    and which input-only requirements fail."""
    dev, base, states, complete = development_rows(panel, out, cause, period, bounds, seed=seed, rate=rate)
    weights = C.baseline_weights(base["quintile"])
    draws = U.period_draws(len(dev))
    report = dict(development_sessions=int(len(dev)), first_session=panel.sessions[dev[0]],
                  last_session=panel.sessions[dev[-1]], eligible_stock_days=int(len(base["date_idx"])),
                  complete_windows=int(complete.sum()), weights=weights,
                  identity_excluded=int(((period == "development")[:, None] & (cause == "identity_unknown")).sum()),
                  variants={})
    for v in VARIANTS:
        rows = dict(base, state=states[v])
        table = C.cells(rows)
        availability = {}
        for name, mask in (("adverse", rows["state"] == 1.0), ("other", rows["state"] == 0.0),
                           ("unknown", ~np.isfinite(rows["state"]))):
            availability[name] = dict(stock_days=int(mask.sum()),
                                      complete_windows=int(np.isfinite(rows["outcome"][mask]).sum()))
        spells = C.spell_count(list(zip([panel.sessions[i] for i in dev],
                                        _state_list(out[f"{v.lower()}_adverse"][dev])))) if v in C.SPELL_VARIANTS else None
        replicates = U.replicate_differences(rows, weights, draws[U.BLOCK[v]], usable=usable)
        bands = U.intervals(replicates, method=method)
        verdict = C.decide(v, table=table, standardized_difference=C.standardized(table, weights),
                           cover=C.coverage(rows, numerator=coverage_numerator), usable_draws=bands["usable_draws"],
                           family_interval=bands["family"] or (float("nan"), float("nan")), spells_in_period=spells)
        # An INCONCLUSIVE verdict rests only on inputs (coverage, sample sizes, usable draws, spells, an
        # unavailable difference); SUCCESS or NOT_SUCCESS would rest on the random labels, so it is not kept.
        label_free = verdict["reasons"] if verdict["result"] == "INCONCLUSIVE" else []
        report["variants"][v] = dict(
            coverage=C.coverage(rows, numerator=coverage_numerator), availability=availability,
            cells={f"{'adverse' if s == 1.0 else 'other'} q{q}": {k: table[(s, q)][k] for k in ("candidates", "valid", "dates")}
                   for s in C.STATES for q in C.QUINTILES},
            sample_shortfalls=C.sample_shortfalls(table), spells=spells, block=U.BLOCK[v],
            usable_draws=bands["usable_draws"], unusable_draws=int(len(replicates) - bands["usable_draws"]),
            input_only_failures=label_free, decision_step_ran=True)
    return report
