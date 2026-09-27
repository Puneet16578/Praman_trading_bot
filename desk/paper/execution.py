"""Deterministic, conservative paper fills (item 9). Entry and every non-price exit fill at the
NEXT session's open; a stop fill uses the conservative of "gapped through" (fill at that open, worse
for the trader than the stop) vs. "touched intraday" (fill at the stop itself). Corporate actions
during a position are absorbed via Praman's own adjustment factor -- a split changes the position's
entry/stop/target/quantity by the same factor, so the stop's real economic level never moves and a
split never reads as a false stop hit.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.bitemporal.guard import latest_as_of
from src.signals.event_catalogue import build_symbol_history
from src.signals.price_adjustment import compute_adjustment_factor


def next_trading_session(conn, symbol: str, after_date: str, as_of: str) -> str | None:
    hist = build_symbol_history(conn, symbol)
    days = hist.trading_days
    for d in days:
        if d > after_date:
            return d
    return None


def session_ohlc(conn, symbol: str, event_date: str, as_of: str) -> dict | None:
    hist = build_symbol_history(conn, symbol)
    return hist.price_row_as_of(event_date, as_of)


@dataclass
class Fill:
    event_date: str
    price: float
    kind: str  # "entry" / "stop_gap" / "stop_touch" / "exit_open"


def fill_entry(conn, symbol: str, decision_date: str, slippage_pct: float, as_of: str) -> Fill | None:
    next_date = next_trading_session(conn, symbol, decision_date, as_of)
    if next_date is None:
        return None
    row = session_ohlc(conn, symbol, next_date, as_of)
    if row is None:
        return None
    hist = build_symbol_history(conn, symbol)
    adjusted_open = row["open_price"] * hist.cum_factor_up_to(next_date)
    price = adjusted_open * (1.0 + slippage_pct / 100.0)  # buying: slippage makes the fill worse (higher)
    return Fill(event_date=next_date, price=price, kind="entry")


def check_stop_on_session(conn, symbol: str, event_date: str, stop: float, as_of: str) -> Fill | None:
    """Conservative rule: if the session's own open already gapped through the stop, fill there
    (worse for a long than the stop itself); otherwise, if the session's low touched the stop, fill
    AT the stop, never at a more favorable price the position never actually had a chance at."""
    row = session_ohlc(conn, symbol, event_date, as_of)
    if row is None:
        return None
    hist = build_symbol_history(conn, symbol)
    factor = hist.cum_factor_up_to(event_date)
    adj_open = row["open_price"] * factor
    adj_low = row["low_price"] * factor
    if adj_open <= stop:
        return Fill(event_date=event_date, price=adj_open, kind="stop_gap")
    if adj_low <= stop:
        return Fill(event_date=event_date, price=stop, kind="stop_touch")
    return None


def fill_non_price_exit(conn, symbol: str, trigger_date: str, as_of: str) -> Fill | None:
    """Time / evidence / risk / portfolio exits all fill at the next session's open -- no slippage
    assumption is specified for these in item 9, so none is applied here (unlike entry)."""
    next_date = next_trading_session(conn, symbol, trigger_date, as_of)
    if next_date is None:
        return None
    row = session_ohlc(conn, symbol, next_date, as_of)
    if row is None:
        return None
    hist = build_symbol_history(conn, symbol)
    price = row["open_price"] * hist.cum_factor_up_to(next_date)
    return Fill(event_date=next_date, price=price, kind="exit_open")


@dataclass
class AdjustedPosition:
    entry: float
    stop: float
    target: float
    quantity: float
    factor_applied: float


def adjust_for_corporate_actions(conn, symbol: str, original_entry_date: str, entry: float, stop: float,
                                  target: float, quantity: float, as_of: str) -> AdjustedPosition:
    """Re-expresses entry/stop/target/quantity in terms comparable to `as_of`, using the SAME
    adjustment factor Praman's own price series uses (compute_adjustment_factor) -- a 2:1 split
    halves entry/stop/target and doubles quantity, so the position's real economic exposure and the
    stop's real economic level are both unchanged; it never reads as a stop hit."""
    factor = compute_adjustment_factor(conn, symbol, original_entry_date, as_of)
    if factor == 1.0:
        return AdjustedPosition(entry=entry, stop=stop, target=target, quantity=quantity, factor_applied=1.0)
    return AdjustedPosition(
        entry=entry / factor, stop=stop / factor, target=target / factor,
        quantity=quantity * factor, factor_applied=factor,
    )
