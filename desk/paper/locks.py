"""Execution availability at the daily circuit limits (P8-064; user decision 2026-10-14). Both books.

A session locked all day at its lower limit has no buyers, so a paper sell cannot fill there; one
locked all day at its upper limit has no sellers, so a paper buy cannot. Daily bars cannot show the
queue, so the rule is conservative:

- The band in force on session S is NSE's price-band report dated the trading session before S
  (docs/desk/price_band_source.md), with that session's raw close of the same series as the
  reference price. The limits are reference x (1 -/+ band %).
- LOCKED_LOWER / LOCKED_UPPER: all four raw prices within one tick of that limit. That needs a FIXED
  band, the reference close, S's tick size (desk/tick_sizes.py) and no corporate action with
  ex-date S (which resets the reference).
- If any of those is unknown and the bar is exactly flat (open = high = low = close), assume it may
  be locked: FLAT_UNKNOWN blocks both a buy and a sell that session.
- Any other bar is NOT_LOCKED and the existing fill rules apply unchanged.

A buy limit above the next session's upper limit could not have been placed: when that band was
known at decision time the limit is capped at the upper limit (`buy_cap_at_decision`); when it was
not, a limit found above it is a rejected order, a normal no-fill (`buy_rejected`).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from desk.circuit_bands import band_as_of
from desk.tick_sizes import tick_for_session
from src.bitemporal.guard import latest_as_of

NOT_LOCKED, LOCKED_LOWER, LOCKED_UPPER, FLAT_UNKNOWN = 'NOT_LOCKED', 'LOCKED_LOWER', 'LOCKED_UPPER', 'FLAT_UNKNOWN'


@dataclass(frozen=True)
class Limits:
    lower: float | None = None
    upper: float | None = None
    tick: float | None = None
    band_pct: float | None = None
    report_date: str | None = None
    reference_close: float | None = None
    unknown: tuple = field(default_factory=tuple)      # why the limits are not fully known

    def evidence(self) -> dict:
        return dict(lower=self.lower, upper=self.upper, tick=self.tick, band_pct=self.band_pct,
                    band_report=self.report_date, reference_close=self.reference_close, unknown=list(self.unknown))


@dataclass(frozen=True)
class LockCheck:
    state: str
    limits: Limits

    @property
    def blocks_sell(self) -> bool:
        return self.state in (LOCKED_LOWER, FLAT_UNKNOWN)

    @property
    def blocks_buy(self) -> bool:
        return self.state in (LOCKED_UPPER, FLAT_UNKNOWN)

    def evidence(self) -> dict:
        return dict(lock_state=self.state, **self.limits.evidence())


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x) and x > 0


def previous_session(praman_conn, session: str, as_of: str) -> str | None:
    """The global trading session before `session` (any symbol's bhavcopy), known by `as_of`."""
    row = praman_conn.execute("SELECT MAX(event_date) FROM bhavcopy WHERE event_date < ? AND knowledge_date <= ?",
                              (session, as_of)).fetchone()
    return row[0] if row else None


def _close(praman_conn, symbol: str, day: str, series: str, as_of: str) -> float | None:
    rows = [r for r in latest_as_of(praman_conn, 'bhavcopy', as_of, symbol=symbol, event_date=day)
            if r['series'] == series]
    return rows[0]['close_price'] if rows and _finite(rows[0]['close_price']) else None


def _action_on(praman_conn, symbol: str, day: str, as_of: str) -> bool:
    row = praman_conn.execute("SELECT 1 FROM corporate_actions WHERE symbol=? AND event_date=? AND knowledge_date<=? "
                              "LIMIT 1", (symbol, day, as_of)).fetchone()
    return row is not None


def _band_and_reference(praman_conn, desk_conn, symbol: str, report_session: str, series: str, as_of: str,
                        recorded_by: str | None) -> tuple:
    """(band, reference close, unknown reasons) for the limits in force on the session after
    `report_session`: that session's band report and close, known by `as_of` (and recorded by
    `recorded_by` when given)."""
    unknown = []
    band = band_as_of(desk_conn, symbol, as_of, report_date=report_session)
    if band.kind != 'FIXED':
        unknown.append('band report missing' if band.kind == 'UNKNOWN' else 'dynamic band')
    elif band.series != series:
        unknown.append(f'band is for series {band.series}, the bar is {series}')
    elif recorded_by is not None and not _band_recorded_by(desk_conn, symbol, report_session, band, recorded_by):
        unknown.append('band not yet recorded at decision time')
    reference = _close(praman_conn, symbol, report_session, series, as_of)
    if reference is None:
        unknown.append('no reference close on the previous session')
    return band, reference, unknown


def session_limits(praman_conn, desk_conn, symbol: str, session: str, series: str, as_of: str) -> Limits:
    """The lower and upper limits in force on `session`, from what was known by `as_of`. Unknown
    parts are named, never guessed."""
    previous = previous_session(praman_conn, session, as_of)
    if previous is None:
        return Limits(unknown=('no previous session',))
    band, reference, unknown = _band_and_reference(praman_conn, desk_conn, symbol, previous, series, as_of, None)
    if _action_on(praman_conn, symbol, session, as_of):
        unknown.append('corporate action with ex-date on the session (reference reset)')
    tick = tick_for_session(desk_conn, symbol, session, as_of)
    if tick is None:
        unknown.append('tick size unknown')
    if band.kind != 'FIXED' or band.series != series or reference is None:
        return Limits(tick=tick, report_date=previous, reference_close=reference, unknown=tuple(unknown))
    return Limits(lower=reference * (1 - band.percent / 100), upper=reference * (1 + band.percent / 100), tick=tick,
                  band_pct=band.percent, report_date=previous, reference_close=reference, unknown=tuple(unknown))


def _band_recorded_by(desk_conn, symbol, report_date, band, recorded_by) -> bool:
    row = desk_conn.execute("SELECT 1 FROM circuit_bands WHERE symbol=? AND series=? AND event_date=? AND source_sha256=? "
                            "AND recorded_at<=? LIMIT 1", (symbol, band.series, report_date, band.source_sha256,
                                                           recorded_by)).fetchone()
    return row is not None


def lock_state(praman_conn, desk_conn, symbol: str, session: str, bar: dict, as_of: str) -> LockCheck:
    """Classify one session's raw bar (open/high/low/close and series as stored)."""
    prices = [bar.get(k) for k in ('open_price', 'high_price', 'low_price', 'close_price')]
    if not all(_finite(p) for p in prices):
        return LockCheck(NOT_LOCKED, Limits(unknown=('unusable bar',)))      # existing missing-bar rules apply
    limits = session_limits(praman_conn, desk_conn, symbol, session, bar.get('series') or 'EQ', as_of)
    if limits.unknown:
        flat = len(set(prices)) == 1
        return LockCheck(FLAT_UNKNOWN if flat else NOT_LOCKED, limits)
    if all(abs(p - limits.lower) <= limits.tick for p in prices):
        return LockCheck(LOCKED_LOWER, limits)
    if all(abs(p - limits.upper) <= limits.tick for p in prices):
        return LockCheck(LOCKED_UPPER, limits)
    return LockCheck(NOT_LOCKED, limits)


def buy_cap_at_decision(praman_conn, desk_conn, symbol: str, decision_date: str, decided_at: str,
                        series: str = 'EQ') -> dict | None:
    """The next session's upper limit as known at decision time: the band report dated the
    decision session and recorded by `decided_at`, over the decision session's close, rounded down
    to the decision session's tick when known. None when that band was not known then."""
    band, reference, unknown = _band_and_reference(praman_conn, desk_conn, symbol, decision_date, series,
                                                   decision_date, decided_at)
    if unknown:
        return None
    upper = reference * (1 + band.percent / 100)
    tick = tick_for_session(desk_conn, symbol, decision_date, decision_date)
    cap = upper if tick is None else math.floor(upper / tick + 1e-9) * tick
    return dict(cap=cap, band_pct=band.percent, band_report=decision_date, reference_close=reference, tick=tick)


def buy_rejected(limit: float, check: LockCheck) -> bool:
    """A limit above the session's known upper limit could not have been placed: the exchange
    rejects prices outside the band."""
    upper = check.limits.upper
    return upper is not None and limit > upper + 1e-9
