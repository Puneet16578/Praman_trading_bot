"""desk paper close -- mirrors desk/paper/open.py's anti-hindsight design. `desk paper close` used
to take `--price` and `--event-date` directly from the human, which meant any exit price could be
recorded on any past date -- the exact same loophole already closed for entries. There is no
price/event_date parameter anywhere in this module, by design: the fill uses the store's own real
price for the first session strictly AFTER the close command's own recorded_at (never a session
that has already happened by the time you run this), exactly like `open_approved_decision`'s entry
fill.

Recorded price is ALWAYS the store's raw price -- never cost-adjusted (post-STOP-3-plus consistency
fix, reversing this module's own earlier "net of cost" design: netting cost into price ONLY for
manual closes meant two identical trades could show different P&L depending on how they closed, and
made a stop-out look artificially cheaper than a manual close of the same trade at the same price).
The real round-trip SELL-side cost (STT, exchange/SEBI charges, brokerage, GST, and the depository
charge) is computed from the ACTIVE cost config at fill time and recorded in its OWN field, alongside
that config's hash -- exactly the same treatment `open_approved_decision`'s entry fill now gives the
BUY-side cost. Realized P&L for ANY exit (this module's or `desk monitor`'s automatic stop-fill) is
computed by the one shared `desk/risk/officer.py:realized_pnl_inr`, never by comparing raw prices.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from shared.market_time import market_date
from src.signals.event_catalogue import build_symbol_history

from .open import first_session_strictly_after


class PaperCloseRefused(RuntimeError):
    """A hard refusal -- no reason given, or no open position for this trade_id."""


@dataclass
class PendingClose:
    trade_id: str
    not_before_date: str
    reason: str


def check_can_close(latest_event: dict | None, trade_id: str) -> None:
    if latest_event is None:
        raise PaperCloseRefused(f"No position was ever opened for trade_id {trade_id!r}.")
    if latest_event["event_type"] == "CLOSE":
        raise PaperCloseRefused(f"trade_id {trade_id!r} is already closed.")


def _attempt_close_fill(praman_conn, desk_conn, trade_id: str, quantity: float, reason: str,
                         costs, cost_config_hash: str, not_before_date: str):
    """Shared by `close_approved_trade` (a fresh human-initiated `paper close`) and
    `resume_pending_close` (a later automatic retry of an already-PENDING one) -- identical fill
    logic either way; only WHERE `not_before_date` comes from differs."""
    from desk.journal import store as jstore
    from desk.paper.execution import Fill
    from desk.risk.officer import round_trip_cost_inr

    symbol = trade_id.split(":")[0]
    fill_date = first_session_strictly_after(praman_conn, symbol, not_before_date)
    if fill_date is None:
        return PendingClose(trade_id=trade_id, not_before_date=not_before_date, reason=reason)

    hist = build_symbol_history(praman_conn, symbol)
    row = hist.price_row_as_of(fill_date, fill_date)
    if row is None:
        return PendingClose(trade_id=trade_id, not_before_date=not_before_date, reason=reason)
    fill_price = row["open_price"] * hist.cum_factor_up_to(fill_date)  # raw -- never cost-adjusted
    sell_cost_inr = round_trip_cost_inr(fill_price, quantity, costs, "sell")

    jstore.close_paper_trade(desk_conn, trade_id=trade_id, event_date=fill_date, price=fill_price,
                              reason=reason, sell_cost_inr=sell_cost_inr, cost_config_hash=cost_config_hash)
    return Fill(event_date=fill_date, price=fill_price, kind="exit_open")


def close_approved_trade(praman_conn, desk_conn, trade_id: str, *, reason: str, costs,
                          cost_config_hash: str, now: datetime | None = None):
    """The one entry point for a human-initiated `desk paper close`. `reason` is mandatory --
    there is no default and no way to omit it. Returns a `Fill` on success, or a `PendingClose` if
    the next eligible session's data does not exist in the store yet. Raises `PaperCloseRefused` if
    there is no open position for `trade_id`, or no reason was given. `costs`/`cost_config_hash` are
    the ACTIVE cost config at fill time (loaded by the caller) -- required, not defaulted."""
    from desk.journal import store as jstore

    if not reason:
        raise PaperCloseRefused("reason is required to close a paper trade.")

    latest = jstore.latest_trade_event(desk_conn, trade_id)
    check_can_close(latest, trade_id)

    now = now or datetime.now(timezone.utc)
    not_before_date = market_date(now).isoformat()
    return _attempt_close_fill(praman_conn, desk_conn, trade_id, latest["quantity"], reason,
                                costs, cost_config_hash, not_before_date)


def resume_pending_close(praman_conn, desk_conn, trade_id: str, not_before_date: str, reason: str,
                          costs, cost_config_hash: str):
    """Retries a PENDING close using the ORIGINAL `not_before_date` frozen at the first `paper
    close` attempt -- never a fresh `now` -- for exactly the same reason `resume_pending_open`
    (desk/paper/open.py) doesn't either: waiting for Praman's own ingestion to catch up must not
    silently push the target fill session forward. `costs`/`cost_config_hash` are the ACTIVE cost
    config AT RESUME TIME (a real fact about current broker rates, not something hindsight could
    game). Called by `desk monitor` (`desk/monitor.py:complete_pending_paper_closes`), never by a
    human directly. If the position was already closed by something else in the meantime (e.g. a
    real stop hit in a normal monitor run), `desk/journal/store.py:pending_paper_closes` already
    filters this trade_id out before this is ever called."""
    from desk.journal import store as jstore

    latest = jstore.latest_trade_event(desk_conn, trade_id)
    check_can_close(latest, trade_id)
    return _attempt_close_fill(praman_conn, desk_conn, trade_id, latest["quantity"], reason,
                                costs, cost_config_hash, not_before_date)
