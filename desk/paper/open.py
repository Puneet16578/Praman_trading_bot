"""desk paper open -- executes an ALREADY-APPROVED decision exactly as persisted; it never
re-assesses (integrity fix b). Two guards against hindsight (integrity fix a):

1. A decision can only be paper-opened if it was a LIVE assessment (`as_of_date` was the latest
   available trading day AT ASSESSMENT TIME -- `decisions.as_of_is_live`). A decision made with an
   explicit historical `--as-of` is backtesting, not paper trading, and can never be opened.
2. A decision refuses to open once too much WALL-CLOCK time has passed since assessment (more than
   `STALE_AFTER_DAYS` calendar days) -- re-assess fresh instead of opening on stale context.
   Deliberately a CALENDAR-day threshold, not a trading-session-aware one -- a known Phase-1
   simplification (a Friday decision opened Monday would technically read as 3 days stale even
   though zero trading sessions elapsed) -- a real limitation, named here rather than hidden. A
   trading-calendar-aware version needs a reliable "what is today's session, if any" source Phase 1
   does not have (Praman's own ingestion is nightly batch, not live).
3. The fill itself can only use a session strictly AFTER the CALENDAR DATE this command itself runs
   on (`now`, defaulting to wall-clock UTC) -- never a session whose own trading day has already
   started/happened by the time you click "open". Concretely: if `now` falls on D+1 (one day after
   the decision's `as_of_date`, D), D+1's own session has already begun/happened in the real world
   by the time you're clicking "open" -- so the fill skips to D+2, never D+1, regardless of whether
   Praman's own (nightly-batch) store has ingested D+1's data yet.

Consequence, stated plainly rather than hidden: if the eligible fill session's data is not yet in
the store (a real possibility -- Praman's ingestion is nightly, not live), this returns PENDING
rather than a fill. Phase 1 does not build a background resolver for this; re-running
`desk paper open` once that session's data has been ingested completes the fill. A real deferred/
async resolution path (e.g. wired into `desk monitor`) is a named, deliberate gap for a later phase.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone

from src.signals.event_catalogue import build_symbol_history

STALE_AFTER_DAYS = 1  # PROPOSED: allow opening a decision made "today" or with one calendar day of
                       # lag (e.g. assessed in the evening, opened the next day before that day's
                       # own EOD data exists) -- two or more days elapsed requires a fresh assessment.


class PaperOpenRefused(RuntimeError):
    """A hard refusal -- decision not ELIGIBLE, not a live assessment, or now stale."""


@dataclass
class PendingOpen:
    decision_id: int
    not_before_date: str


def is_as_of_live(conn, as_of_date: str) -> bool:
    """True if `as_of_date` is the current latest available trading day in `conn`'s own bhavcopy --
    used at ASSESSMENT time to stamp `decisions.as_of_is_live` (an explicit historical --as-of
    stamps False)."""
    row = conn.execute("SELECT MAX(event_date) AS m FROM bhavcopy").fetchone()
    return row["m"] == as_of_date


def first_session_strictly_after(conn, symbol: str, after_date: str) -> str | None:
    hist = build_symbol_history(conn, symbol)
    for d in hist.trading_days:
        if d > after_date:
            return d
    return None


def check_can_open(decision: dict, now: datetime) -> None:
    if decision["state"] != "ELIGIBLE":
        raise PaperOpenRefused(f"Decision {decision['decision_id']} is {decision['state']}, not ELIGIBLE.")
    if not decision["as_of_is_live"]:
        raise PaperOpenRefused(
            "This decision was assessed with an explicit historical --as-of date -- that is "
            "backtesting, not paper trading. A paper trade can only be opened from a live assessment."
        )
    as_of = date.fromisoformat(decision["as_of_date"])
    age_days = (now.date() - as_of).days
    if age_days > STALE_AFTER_DAYS:
        raise PaperOpenRefused(
            f"Decision as-of date {decision['as_of_date']!r} is {age_days} calendar day(s) old "
            f"(limit {STALE_AFTER_DAYS}) -- re-assess fresh rather than opening a stale decision."
        )


def open_approved_decision(praman_conn, desk_conn, decision_id: int, *, now: datetime | None = None):
    """Returns a `Fill` (desk.paper.execution.Fill) on success, or a `PendingOpen` if the next
    eligible session's data does not exist in the store yet. Raises PaperOpenRefused on any of the
    guards above. Uses ONLY the decision's own persisted `position_size` and the linked thesis's
    `planned_stop`/`planned_target` -- it never calls run_assessment."""
    from desk.journal import store as jstore
    from desk.paper.execution import Fill

    decision = jstore.get_decision(desk_conn, decision_id)
    if decision is None:
        raise PaperOpenRefused(f"No decision {decision_id}.")

    now = now or datetime.now(timezone.utc)
    check_can_open(decision, now)

    thesis = jstore.get_thesis(desk_conn, decision["thesis_id"]) if decision["thesis_id"] else None
    if thesis is None or decision["position_size"] is None:
        raise PaperOpenRefused("Decision has no persisted thesis or position size -- cannot open.")

    not_before_date = now.date().isoformat()
    fill_date = first_session_strictly_after(praman_conn, decision["symbol"], not_before_date)
    if fill_date is None:
        return PendingOpen(decision_id=decision_id, not_before_date=not_before_date)

    hist = build_symbol_history(praman_conn, decision["symbol"])
    row = hist.price_row_as_of(fill_date, fill_date)
    if row is None:
        return PendingOpen(decision_id=decision_id, not_before_date=not_before_date)
    fill_price = row["open_price"] * hist.cum_factor_up_to(fill_date)

    trade_id = f"{decision['symbol']}:{decision['thesis_id']}"
    jstore.open_paper_trade(
        desk_conn, trade_id=trade_id, decision_id=decision_id, event_date=fill_date, price=fill_price,
        quantity=decision["position_size"], stop=thesis["planned_stop"], target=thesis["planned_target"],
    )
    return Fill(event_date=fill_date, price=fill_price, kind="entry")
