"""desk paper open -- executes an ALREADY-APPROVED decision exactly as persisted; it never
re-assesses (integrity fix b). The recorded fill price is ALWAYS the store's raw price -- never
cost-adjusted (post-STOP-3-plus consistency fix); the round-trip BUY-side cost is computed
separately, from the caller-supplied active cost config, and recorded in its own field alongside
the cost config's own hash, so every fill (open or close, manual or automatic) carries the same two
explicit cost fields rather than folding cost into price for some fills and not others.

Two guards against hindsight (integrity fix a):

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


def _attempt_fill(praman_conn, desk_conn, decision: dict, thesis: dict, not_before_date: str,
                   costs, cost_config_hash: str):
    """Shared by `open_approved_decision` (a fresh human-initiated `paper open`) and
    `resume_pending_open` (a later automatic retry of an already-PENDING one) -- the only
    difference between them is WHERE `not_before_date` comes from; the fill logic itself, and its
    guarantee of using only the decision's own persisted `position_size` and the thesis's
    `planned_stop`/`planned_target`, is identical either way."""
    from desk.journal import store as jstore
    from desk.paper.execution import Fill
    from desk.risk.officer import round_trip_cost_inr

    fill_date = first_session_strictly_after(praman_conn, decision["symbol"], not_before_date)
    if fill_date is None:
        return PendingOpen(decision_id=decision["decision_id"], not_before_date=not_before_date)

    hist = build_symbol_history(praman_conn, decision["symbol"])
    row = hist.price_row_as_of(fill_date, fill_date)
    if row is None:
        return PendingOpen(decision_id=decision["decision_id"], not_before_date=not_before_date)
    fill_price = row["open_price"] * hist.cum_factor_up_to(fill_date)  # raw -- never cost-adjusted
    quantity = decision["position_size"]
    buy_cost_inr = round_trip_cost_inr(fill_price, quantity, costs, "buy")

    trade_id = f"{decision['symbol']}:{decision['thesis_id']}"
    jstore.open_paper_trade(
        desk_conn, trade_id=trade_id, decision_id=decision["decision_id"], event_date=fill_date,
        price=fill_price, quantity=quantity, stop=thesis["planned_stop"],
        target=thesis["planned_target"], buy_cost_inr=buy_cost_inr, cost_config_hash=cost_config_hash,
    )
    return Fill(event_date=fill_date, price=fill_price, kind="entry")


def _get_decision_and_thesis(desk_conn, decision_id: int) -> tuple[dict, dict]:
    from desk.journal import store as jstore

    decision = jstore.get_decision(desk_conn, decision_id)
    if decision is None:
        raise PaperOpenRefused(f"No decision {decision_id}.")
    thesis = jstore.get_thesis(desk_conn, decision["thesis_id"]) if decision["thesis_id"] else None
    if thesis is None or decision["position_size"] is None:
        raise PaperOpenRefused("Decision has no persisted thesis or position size -- cannot open.")
    return decision, thesis


def open_approved_decision(praman_conn, desk_conn, decision_id: int, *, costs, cost_config_hash: str,
                            now: datetime | None = None):
    """Returns a `Fill` (desk.paper.execution.Fill) on success, or a `PendingOpen` if the next
    eligible session's data does not exist in the store yet. Raises PaperOpenRefused on any of the
    guards above. Uses ONLY the decision's own persisted `position_size` and the linked thesis's
    `planned_stop`/`planned_target` -- it never calls run_assessment. `costs`/`cost_config_hash` are
    the ACTIVE cost config at fill time (loaded by the caller) -- required, not defaulted, so a
    caller can never forget to load one and silently record a fill with no cost fields.

    A `PendingOpen` here freezes `not_before_date` at THIS call's own `now` -- the caller (desk/
    cli.py's `cmd_paper_open`) records it in a PAPER_OPEN_PENDING journal event so `desk monitor`
    can complete the fill later via `resume_pending_open`, using that SAME frozen date rather than a
    fresh `now` (see that function's docstring for why: recomputing `now` on every retry would keep
    pushing the target fill session forward for as long as ingestion stays behind)."""
    decision, thesis = _get_decision_and_thesis(desk_conn, decision_id)

    now = now or datetime.now(timezone.utc)
    check_can_open(decision, now)

    not_before_date = now.date().isoformat()
    return _attempt_fill(praman_conn, desk_conn, decision, thesis, not_before_date, costs, cost_config_hash)


def resume_pending_open(praman_conn, desk_conn, decision_id: int, not_before_date: str, *,
                         costs, cost_config_hash: str):
    """Retries a PENDING open using the ORIGINAL `not_before_date` frozen at the first `paper open`
    attempt -- never a fresh `now`. Waiting for Praman's store to catch up must not silently push
    the target fill session forward: the human already approved opening this exact decision (that's
    what the earlier `paper open` call WAS); this call exists purely because the fill session's data
    was not in the store yet, not because there is a new decision to approve. Consequently it does
    NOT re-run `check_can_open`'s state/staleness checks -- those were already satisfied by the
    original attempt, and re-applying a wall-clock staleness check on every automatic retry would
    eventually refuse a still-legitimately-pending trade for no reason but Praman's own ingestion
    lag. `costs`/`cost_config_hash` are the ACTIVE cost config AT RESUME TIME -- economically
    correct, since transaction costs are a real fact about broker rates in effect now, not something
    hindsight could game. Called by `desk monitor`
    (`desk/monitor.py:complete_pending_paper_opens`), never by a human directly."""
    decision, thesis = _get_decision_and_thesis(desk_conn, decision_id)
    return _attempt_fill(praman_conn, desk_conn, decision, thesis, not_before_date, costs, cost_config_hash)
