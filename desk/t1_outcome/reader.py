"""adverse20 for T1 decisions, read only through the outcome firewall.

Pre-registration, "Outcome, metrics and uncertainty": "Y=1 if any action-adjusted low in the next
20 GLOBAL market sessions is at or below 80% of decision close. Use the existing adverse20 label
definition on a common share basis; all 20 bars required for both outcomes. Structural breaks and
missing paths are unavailable, not zero."

The existing definition is desk/shadow_analysis.py `tails`: the 20 global sessions after the
decision; every one needs a stored bar with a positive open, high, low and close; lows are put on
the decision's share basis with the bonus and split factors; a demerger, capital reduction,
rights issue or ratio conflict with its ex-date in the window makes it unavailable (the same four
types as src STRUCTURAL_BREAK_ACTION_TYPES and T1's unadjustable actions). On T1's panel the
prices are already fully back-adjusted, so low/close ratios are on a common basis; a test checks
the labels against `tails` itself.

Guards (user, 2026-10-18): an event on or after the forward window's start is refused here
whatever the date today, and every event also passes the firewall's own check
(desk.outcome_firewall.evaluate_event); a development run refuses any decision date, and any
forward session, outside 2019-10-01 to 2024-12-31, and refuses a panel holding a later session,
so 2025 is never loaded.
"""
from __future__ import annotations

from datetime import date

import numpy as np

from desk.outcome_firewall import FORWARD_START, evaluate_event
from desk.t1.features import DEVELOPMENT_END, FORWARD_SESSIONS, STUDY_START

ADVERSE_FRACTION = 0.8
# "Development: 2019-10-01 through 2024-12-31." Only the development period exists here: there is
# no reader for the 2025 hold-out (it stays untouched until the development results are locked).
PERIODS = {"development": (STUDY_START, DEVELOPMENT_END)}


class OutcomeReadRefused(ValueError):
    """An outcome read outside what T1 may see."""


def _refuse_event(day: str, period: str) -> None:
    if date.fromisoformat(day) >= FORWARD_START:
        raise OutcomeReadRefused(f"T1 reads no outcome for an event on or after {FORWARD_START.isoformat()} ({day}).")
    first, last = PERIODS[period]
    if not first <= day <= last:
        raise OutcomeReadRefused(f"{day} is outside the {period} period ({first} to {last}).")


def _labels(panel, i: int, cols: np.ndarray) -> np.ndarray:
    """1.0 adverse, 0.0 not, NaN unavailable, for decision session i and the given symbol columns."""
    window = slice(i + 1, i + 1 + FORWARD_SESSIONS)
    out = np.full(len(cols), np.nan)
    decision = panel.close[i, cols]
    bars = [np.asarray(a[window][:, cols], dtype=float) for a in (panel.open, panel.high, panel.low, panel.close)]
    complete = np.all([np.all(np.isfinite(b) & (np.nan_to_num(b) > 0), axis=0) for b in bars], axis=0)
    unbroken = (panel.breaks[i + FORWARD_SESSIONS, cols] - panel.breaks[i, cols]) == 0
    usable = complete & unbroken & np.isfinite(decision) & (np.nan_to_num(decision) > 0)
    lows = np.min(np.where(np.isfinite(bars[2]), bars[2], np.inf), axis=0)
    out[usable] = (lows[usable] <= ADVERSE_FRACTION * decision[usable]).astype(float)
    return out


def read_adverse20(panel, decisions: dict[str, list[str]], *, period: str) -> dict[str, np.ndarray]:
    """{decision session: labels aligned with its symbols}. Every session is checked by the guards
    above and then read through the firewall, one event date at a time."""
    if period not in PERIODS:
        raise OutcomeReadRefused(f"No outcome reader for period {period!r}; only {sorted(PERIODS)}.")
    first, last = PERIODS[period]
    if panel.sessions[-1] > last:
        raise OutcomeReadRefused(f"The panel holds sessions after {last} (to {panel.sessions[-1]}); "
                                 f"a {period} run must not load them.")
    if panel.open is None:
        raise OutcomeReadRefused("The panel carries no open prices; the existing label checks them.")
    pos = {d: k for k, d in enumerate(panel.sessions)}
    col = {s: j for j, s in enumerate(panel.symbols)}
    out = {}
    for day in sorted(decisions):
        _refuse_event(day, period)
        if day not in pos:
            raise OutcomeReadRefused(f"{day} is not a session of the panel's calendar.")
        i = pos[day]
        if i + FORWARD_SESSIONS >= len(panel.sessions) or panel.sessions[i + FORWARD_SESSIONS] > last:
            raise OutcomeReadRefused(f"The 20th session after {day} is beyond {last}: purge the decision first.")
        cols = np.array([col[s] for s in decisions[day]], dtype=int)
        out[day] = evaluate_event(day, _labels, panel, i, cols)
    return out
