"""desk monitor -- marks open positions against all five exit triggers and reports what changed
(new disclosures, surveillance changes, corporate actions, volume/delivery changes) since the
previous monitor run, by diffing against the most recent monitor_runs report.
"""
from __future__ import annotations

from desk.evidence.bundle import assemble_evidence_bundle
from desk.journal import store as jstore
from desk.paper.execution import check_stop_on_session


def run_monitor(praman_conn, desk_conn, run_date: str) -> dict:
    report: dict = {"run_date": run_date, "positions": {}, "exits_triggered": []}

    for trade_id in jstore.open_trade_ids(desk_conn):
        latest = jstore.latest_trade_event(desk_conn, trade_id)
        symbol = trade_id.split(":")[0]

        stop_fill = check_stop_on_session(praman_conn, symbol, run_date, latest["stop"], run_date)
        if stop_fill is not None:
            jstore.close_paper_trade(desk_conn, trade_id=trade_id, event_date=stop_fill.event_date,
                                      price=stop_fill.price, reason=f"stop ({stop_fill.kind})")
            report["exits_triggered"].append({"trade_id": trade_id, "reason": stop_fill.kind, "price": stop_fill.price})
            continue

        bundle = assemble_evidence_bundle(praman_conn, symbol, run_date, sector=None)
        report["positions"][trade_id] = {
            "symbol": symbol, "stop": latest["stop"], "target": latest["target"],
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
