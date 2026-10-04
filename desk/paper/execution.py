"""Deterministic, conservative paper fills (item 9). Entry and every non-price exit fill at the
NEXT session's open; a stop fill uses the conservative of "gapped through" (fill at that open, worse
for the trader than the stop) vs. "touched intraday" (fill at the stop itself).

Share basis (P8-044, 2026-10-04): every price of a paper position -- entry, stop, target, exits --
is kept on the share basis of its DECISION date, so quantity, stop and P&L stay comparable. A
session's raw price is put on that basis with `basis_factor`, the store's own point-in-time
adjustment factor over (decision date, session date]. Without a bonus or split in between it is
exactly 1.0, so the recorded price is the raw store price. The earlier code multiplied raw prices
by the history-wide cumulative factor (`cum_factor_up_to`), which re-expressed them in the
history's EARLIEST share basis: for any symbol with a past bonus or split, fills, costs and P&L
were scaled by that factor and stops compared against the wrong price level.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.bitemporal.guard import latest_as_of
from src.signals.event_catalogue import build_symbol_history
from src.signals.price_adjustment import compute_adjustment_factor


def basis_factor(conn, symbol: str, basis_date: str | None, session_date: str) -> float:
    """Multiplier putting `session_date`'s raw prices on `basis_date`'s share basis: the product of
    every BONUS/SPLIT factor with an ex-date in (basis_date, session_date], known by session_date.
    1.0 when `basis_date` is None (raw prices) or no such action exists. Raises
    UnadjustableWindowError when a demerger (or other unadjustable action) falls in that window --
    never silently priced."""
    if basis_date is None or basis_date >= session_date:
        return 1.0
    return compute_adjustment_factor(conn, symbol, basis_date, session_date)


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
    basis_open = row["open_price"] * basis_factor(conn, symbol, decision_date, next_date)
    price = basis_open * (1.0 + slippage_pct / 100.0)  # buying: slippage makes the fill worse (higher)
    return Fill(event_date=next_date, price=price, kind="entry")


def check_stop_on_session(conn, symbol: str, event_date: str, stop: float, as_of: str,
                          basis_date: str | None = None) -> Fill | None:
    """Conservative rule: if the session's own open already gapped through the stop, fill there
    (worse for a long than the stop itself); otherwise, if the session's low touched the stop, fill
    AT the stop, never at a more favorable price the position never actually had a chance at.
    `stop` and the returned price are on `basis_date`'s share basis (raw when it is None)."""
    row = session_ohlc(conn, symbol, event_date, as_of)
    if row is None:
        return None
    factor = basis_factor(conn, symbol, basis_date, event_date)
    adj_open = row["open_price"] * factor
    adj_low = row["low_price"] * factor
    if adj_open <= stop:
        return Fill(event_date=event_date, price=adj_open, kind="stop_gap")
    if adj_low <= stop:
        return Fill(event_date=event_date, price=stop, kind="stop_touch")
    return None


def fill_non_price_exit(conn, symbol: str, trigger_date: str, as_of: str, basis_date: str | None = None) -> Fill | None:
    """Time / evidence / risk / portfolio exits all fill at the next session's open -- no slippage
    assumption is specified for these in item 9, so none is applied here (unlike entry)."""
    next_date = next_trading_session(conn, symbol, trigger_date, as_of)
    if next_date is None:
        return None
    row = session_ohlc(conn, symbol, next_date, as_of)
    if row is None:
        return None
    price = row["open_price"] * basis_factor(conn, symbol, basis_date, next_date)
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
