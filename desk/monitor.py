"""desk monitor -- completes any paper-trade entry OR exit left PENDING by a prior `paper open`/
`paper close` (Fix 2c, post-STOP-3 review; the close side added in the same spirit once manual
closes gained the identical anti-hindsight design), marks open positions against all five exit
triggers, and reports what changed (new disclosures, surveillance changes, corporate actions,
volume/delivery changes) since the previous monitor run, by diffing against the most recent
monitor_runs report.

Mechanical exits (P8-054): the stop, and the time exit at the open of the first session after the
thesis horizon, are checked on EVERY session from the entry session through the run date, in date
order, so a stop hit on an evening nobody ran the monitor is still found and filled at that
session's own price. The nightly ingestion runs this every evening. Targets and the evidence, risk
and portfolio exits stay the user's judgement.
"""
from __future__ import annotations

from desk.evidence.bundle import assemble_evidence_bundle
from desk.journal import store as jstore
from desk.paper.execution import Fill, basis_factor, check_stop_on_session, session_ohlc


def trade_horizon(desk_conn, trade_id: str) -> str | None:
    """The opening decision's thesis horizon, or None when the trade has no linked thesis."""
    row = desk_conn.execute(
        "SELECT t.horizon FROM paper_trade_events e JOIN decisions d ON d.decision_id = e.decision_id "
        "JOIN theses t ON t.thesis_id = d.thesis_id WHERE e.trade_id = ? AND e.event_type = 'OPEN'",
        (trade_id,)).fetchone()
    return row[0] if row else None


def first_mechanical_exit(praman_conn, desk_conn, trade_id: str, run_date: str):
    """(Fill, trigger) for the first mechanical exit from the entry session through `run_date`, in
    date order, or None. trigger 'price': the stop (gap at the open, else touch at the stop, the
    existing conservative rule). trigger 'time': the open of the first session after both the
    horizon and the entry session; on that session only its open counts (the position is gone
    afterwards), and an open at or below the stop is reported as the stop gap it also is. Each
    session uses the stop in force on that date. Raises UnadjustableWindowError where no adjustment
    factor exists."""
    from desk.paper.close import trade_basis_date
    from src.signals.event_catalogue import build_symbol_history

    events = [dict(r) for r in desk_conn.execute(
        'SELECT event_type, event_date, stop FROM paper_trade_events WHERE trade_id=? ORDER BY event_id', (trade_id,))]
    opened = next(e for e in events if e['event_type'] == 'OPEN')
    symbol = trade_id.split(':')[0]
    basis = trade_basis_date(desk_conn, trade_id)
    horizon = trade_horizon(desk_conn, trade_id)
    sessions = [d for d in build_symbol_history(praman_conn, symbol).trading_days if opened['event_date'] <= d <= run_date]
    for day in sessions:
        stop = [e['stop'] for e in events if e['event_date'] <= day][-1]
        # Never the entry session's own open: a limit entry fills after that open.
        if horizon is not None and day > horizon and day > opened['event_date']:
            row = session_ohlc(praman_conn, symbol, day, run_date)
            if row is None:
                return None          # the first session after the horizon is not known yet
            opening = row['open_price'] * basis_factor(praman_conn, symbol, basis, day)
            return (Fill(event_date=day, price=opening, kind='stop_gap'), 'price') if opening <= stop else \
                   (Fill(event_date=day, price=opening, kind='time_exit_open'), 'time')
        fill = check_stop_on_session(praman_conn, symbol, day, stop, run_date, basis_date=basis)
        if fill is not None:
            return fill, 'price'
    return None


def complete_pending_paper_opens(praman_conn, desk_conn, loaded_costs=None) -> list[dict]:
    """Completes any paper entry a prior `desk paper open` left PENDING, now that the target
    session's data might be in the store. NOT a new autonomous decision: the human already approved
    opening this exact decision (that's what the original `paper open` call recorded); this only
    finishes a fill that was blocked purely by Praman's own ingestion lag. Reuses
    `resume_pending_open`, which retries at the ORIGINAL frozen `not_before_date` -- never a fresh
    'now' -- so waiting for ingestion to catch up never silently pushes the target fill session
    forward. A decision that has since gone stale enough to be refused is reported, not raised, so
    one bad pending entry never stops the rest of a monitor run. `loaded_costs`, when omitted, is
    loaded from the active cost config here (a standalone call, e.g. from a test, doesn't need to
    load it itself); `run_monitor` loads it once and passes it to every function that needs it."""
    from desk.lib.costs import load_active_cost_config
    from desk.paper.open import NoFill, PaperOpenRefused, PendingOpen, resume_pending_open

    loaded_costs = loaded_costs or load_active_cost_config()

    completed = []
    for decision_id, not_before_date in jstore.pending_paper_opens(desk_conn):
        try:
            result = resume_pending_open(praman_conn, desk_conn, decision_id, not_before_date,
                                          costs=loaded_costs.costs, cost_config_hash=loaded_costs.sha256)
        except PaperOpenRefused as exc:
            completed.append({"decision_id": decision_id, "status": "REFUSED", "detail": str(exc)})
            continue
        if isinstance(result, PendingOpen):
            continue  # still pending -- the target session's data still isn't in the store
        if isinstance(result, NoFill):
            completed.append({"decision_id": decision_id, "status": "NO_FILL", "event_date": result.session,
                              "limit": result.limit, "detail": result.reason or result.status})
            continue
        completed.append({"decision_id": decision_id, "status": "FILLED",
                           "event_date": result.event_date, "price": result.price})
    return completed


def complete_pending_paper_closes(praman_conn, desk_conn, loaded_costs=None) -> list[dict]:
    """Completes any manual close a prior `desk paper close` left PENDING, now that the target
    session's data might be in the store. NOT a new decision: the human already approved closing
    this exact trade (that's what the original `paper close` call recorded, reason and all); this
    only finishes a fill that was blocked purely by Praman's own ingestion lag. Reuses
    `resume_pending_close`, which retries at the ORIGINAL frozen `not_before_date`. A trade already
    closed by something else in the meantime (a real stop hit) is filtered out by
    `pending_paper_closes` before this is ever called, so it is never double-closed here."""
    from desk.lib.costs import load_active_cost_config
    from desk.paper.close import PaperCloseRefused, PendingClose, resume_pending_close

    loaded_costs = loaded_costs or load_active_cost_config()

    completed = []
    for trade_id, not_before_date, reason in jstore.pending_paper_closes(desk_conn):
        try:
            result = resume_pending_close(praman_conn, desk_conn, trade_id, not_before_date, reason,
                                           loaded_costs.costs, loaded_costs.sha256)
        except PaperCloseRefused as exc:
            completed.append({"trade_id": trade_id, "status": "REFUSED", "detail": str(exc)})
            continue
        if isinstance(result, PendingClose):
            continue  # still pending -- the target session's data still isn't in the store
        completed.append({"trade_id": trade_id, "status": "FILLED",
                           "event_date": result.event_date, "price": result.price})
    return completed


def run_monitor(praman_conn, desk_conn, run_date: str) -> dict:
    from desk.lib.costs import load_active_cost_config
    from desk.risk.officer import round_trip_cost_inr

    loaded_costs = load_active_cost_config()

    report: dict = {"run_date": run_date, "positions": {}, "exits_triggered": []}
    report["pending_opens_completed"] = complete_pending_paper_opens(praman_conn, desk_conn, loaded_costs)
    report["pending_closes_completed"] = complete_pending_paper_closes(praman_conn, desk_conn, loaded_costs)

    for trade_id in jstore.open_trade_ids(desk_conn):
        latest = jstore.latest_trade_event(desk_conn, trade_id)
        symbol = trade_id.split(":")[0]
        horizon = trade_horizon(desk_conn, trade_id)

        from src.signals.price_adjustment import UnadjustableWindowError
        try:
            found = first_mechanical_exit(praman_conn, desk_conn, trade_id, run_date)
        except UnadjustableWindowError as exc:
            # No adjustment factor exists, so the stop cannot be checked: report it, never guess.
            report["positions"][trade_id] = {"symbol": symbol, "stop": latest["stop"], "target": latest["target"],
                                             "horizon": horizon,
                                             "unadjustable": f"stop not checked: {exc}; review and close by hand"}
            continue
        if found is not None:
            # Decision-basis fill price, exactly like a manual close -- the round-trip SELL-side cost is its
            # own explicit field, computed the same way `paper close` computes it, never folded into
            # the price. Two identical trades therefore show identical P&L (desk/risk/officer.py:
            # realized_pnl_inr) whichever exit ended them.
            fill, trigger = found
            reason = f"stop ({fill.kind})" if trigger == "price" else f"time (first session after the {horizon} horizon)"
            sell_cost_inr = round_trip_cost_inr(fill.price, latest["quantity"], loaded_costs.costs, "sell")
            jstore.record_journal_event(desk_conn, event_type='EXIT_TRIGGER', trade_id=trade_id,
                                       detail={'trigger': trigger, 'event_date': fill.event_date}, reason=reason)
            jstore.close_paper_trade(desk_conn, trade_id=trade_id, event_date=fill.event_date,
                                      price=fill.price, reason=reason,
                                      sell_cost_inr=sell_cost_inr, cost_config_hash=loaded_costs.sha256)
            report["exits_triggered"].append({"trade_id": trade_id, "reason": fill.kind, "price": fill.price,
                                              "event_date": fill.event_date, "trigger": trigger})
            continue

        from desk.source_freshness import complete_through, market_coverage_from, required_through
        bundle = assemble_evidence_bundle(praman_conn, symbol, run_date, sector=None,
                                          disclosure_source_complete_through=complete_through(desk_conn, symbol),
                                          disclosure_market_coverage_start=market_coverage_from(desk_conn, required_through(run_date)))
        report["positions"][trade_id] = {
            "symbol": symbol, "stop": latest["stop"], "target": latest["target"], "horizon": horizon,
            "surveillance": _fact_or_unknown_repr(bundle.surveillance),
            "disclosures": _fact_or_unknown_repr(bundle.disclosures),
        }

    prior = _most_recent_report(desk_conn)
    report["what_changed"] = _diff_reports(prior, report) if prior else "no prior run to diff against"

    jstore.record_monitor_run(desk_conn, run_date=run_date, report=report)
    return report


def _fact_or_unknown_repr(evidence) -> str:
    from desk.evidence.types import Fact
    return evidence.claim.text if isinstance(evidence, Fact) else f"UNKNOWN: {evidence.detail}"


def _most_recent_report(desk_conn) -> dict | None:
    import json
    row = desk_conn.execute("SELECT report FROM monitor_runs ORDER BY run_id DESC LIMIT 1").fetchone()
    return json.loads(row["report"]) if row else None


def _diff_reports(prior: dict, current: dict) -> list[str]:
    changes = []
    for trade_id, pos in current.get("positions", {}).items():
        prior_pos = prior.get("positions", {}).get(trade_id)
        if prior_pos is None:
            changes.append(f"{trade_id}: new position since last run")
            continue
        for field in ("surveillance", "disclosures"):
            if prior_pos.get(field) != pos.get(field):
                changes.append(f"{trade_id}: {field} changed: {prior_pos.get(field)!r} -> {pos.get(field)!r}")
    return changes
