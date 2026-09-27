"""Append-only reader/writer API for the Desk's own store. Every write stamps its own `recorded_at`
(store-owned, like Praman's `_now()` pattern in src/bitemporal/store.py) -- callers never supply it,
so the Desk's own timestamps are exactly as trustworthy as Praman's own for the same reason.

"Current state" for anything event-logged (a paper position) is always DERIVED by reading the latest
event row for a given trade_id -- there is no mutable "current stop" column anywhere; see
desk/lib/schema.py's module docstring.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone

from desk.lib.schema import DESK_TABLES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def desk_watermark(conn: sqlite3.Connection) -> str:
    """Maximum recorded_at across every Desk table, as visible through THIS connection --
    deliberately unqualified table names so this also works through a hypothetical filtered/replay
    view of the desk store, the same trick desk/lib/store.py uses for Praman's own watermark.
    Returns an epoch-zero sentinel if the desk store is empty (a brand-new desk has no prior state
    to bound -- G6/G7 then see an empty journal, not an error)."""
    values = []
    for table in DESK_TABLES:
        row = conn.execute(f"SELECT MAX(recorded_at) AS m FROM {table}").fetchone()
        if row["m"] is not None:
            values.append(row["m"])
    return max(values) if values else "1970-01-01T00:00:00.000000+00:00"


def record_decision(conn: sqlite3.Connection, *, symbol: str, as_of_date: str, thesis_id: int | None,
                     evidence_bundle_hash: str, gate_results: dict, state: str,
                     rulebook_version: str, rulebook_hash: str,
                     cost_config_version: str, cost_config_hash: str,
                     code_commit: str, praman_watermark: str, desk_watermark_value: str,
                     model_version: str | None = None, prompt_version: str | None = None,
                     override_reason: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO decisions
           (symbol, as_of_date, thesis_id, evidence_bundle_hash, gate_results, state,
            rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit,
            praman_watermark, desk_watermark, model_version, prompt_version, override_reason, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (symbol, as_of_date, thesis_id, evidence_bundle_hash, json.dumps(gate_results), state,
         rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit,
         praman_watermark, desk_watermark_value, model_version, prompt_version, override_reason, _now()),
    )
    conn.commit()
    return cur.lastrowid


def get_decision(conn: sqlite3.Connection, decision_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["gate_results"] = json.loads(d["gate_results"])
    return d


def record_thesis(conn: sqlite3.Connection, *, symbol: str, evidence_cutoff: str, hypotheses: list,
                   drivers: list, horizon: str, invalidation_conditions: list,
                   exit_price: str, exit_time: str, exit_evidence: str, exit_risk: str, exit_portfolio: str,
                   planned_entry: float, planned_stop: float, planned_target: float,
                   sector: str, prior_thesis_id: int | None = None, catalyst: str | None = None,
                   stress_loss: float | None = None, position_size: float | None = None,
                   portfolio_risk_added: float | None = None, user_probability: float | None = None,
                   paper_or_live: str = "PAPER") -> int:
    if paper_or_live != "PAPER":
        raise ValueError("Phase 1 rejects any thesis not marked PAPER -- live trades are not supported.")
    cur = conn.execute(
        """INSERT INTO theses
           (prior_thesis_id, symbol, evidence_cutoff, hypotheses, drivers, catalyst, horizon,
            invalidation_conditions, exit_price, exit_time, exit_evidence, exit_risk, exit_portfolio,
            planned_entry, planned_stop, planned_target, stress_loss, position_size,
            portfolio_risk_added, user_probability, sector, paper_or_live, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (prior_thesis_id, symbol, evidence_cutoff, json.dumps(hypotheses), json.dumps(drivers),
         catalyst, horizon, json.dumps(invalidation_conditions), exit_price, exit_time, exit_evidence,
         exit_risk, exit_portfolio, planned_entry, planned_stop, planned_target, stress_loss,
         position_size, portfolio_risk_added, user_probability, sector, paper_or_live, _now()),
    )
    conn.commit()
    return cur.lastrowid


def get_thesis(conn: sqlite3.Connection, thesis_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM theses WHERE thesis_id = ?", (thesis_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["hypotheses"] = json.loads(d["hypotheses"])
    d["drivers"] = json.loads(d["drivers"])
    d["invalidation_conditions"] = json.loads(d["invalidation_conditions"])
    return d


def _record_trade_event(conn: sqlite3.Connection, *, trade_id: str, decision_id: int | None,
                         event_type: str, event_date: str, price: float, quantity: float,
                         stop: float, target: float, reason: str) -> None:
    conn.execute(
        """INSERT INTO paper_trade_events
           (trade_id, decision_id, event_type, event_date, price, quantity, stop, target, reason, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trade_id, decision_id, event_type, event_date, price, quantity, stop, target, reason, _now()),
    )
    conn.commit()


def open_paper_trade(conn: sqlite3.Connection, *, trade_id: str, decision_id: int, event_date: str,
                      price: float, quantity: float, stop: float, target: float,
                      reason: str = "entry") -> None:
    if latest_trade_event(conn, trade_id) is not None:
        raise ValueError(f"trade_id {trade_id!r} already has events -- OPEN must be the first event.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=decision_id, event_type="OPEN",
                         event_date=event_date, price=price, quantity=quantity, stop=stop,
                         target=target, reason=reason)


def adjust_paper_trade(conn: sqlite3.Connection, *, trade_id: str, event_date: str, price: float,
                        quantity: float, stop: float, target: float, reason: str) -> None:
    prior = latest_trade_event(conn, trade_id)
    if prior is None or prior["event_type"] == "CLOSE":
        raise ValueError(f"trade_id {trade_id!r} has no open position to adjust.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=None, event_type="ADJUST",
                         event_date=event_date, price=price, quantity=quantity, stop=stop,
                         target=target, reason=reason)


def close_paper_trade(conn: sqlite3.Connection, *, trade_id: str, event_date: str, price: float,
                       reason: str) -> None:
    prior = latest_trade_event(conn, trade_id)
    if prior is None or prior["event_type"] == "CLOSE":
        raise ValueError(f"trade_id {trade_id!r} has no open position to close.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=None, event_type="CLOSE",
                         event_date=event_date, price=price, quantity=0.0, stop=prior["stop"],
                         target=prior["target"], reason=reason)


def latest_trade_event(conn: sqlite3.Connection, trade_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM paper_trade_events WHERE trade_id = ? ORDER BY event_id DESC LIMIT 1",
        (trade_id,),
    ).fetchone()
    return dict(row) if row else None


def open_trade_ids(conn: sqlite3.Connection) -> list[str]:
    """Every trade_id whose latest event is not CLOSE."""
    rows = conn.execute(
        """SELECT trade_id FROM paper_trade_events pte
           WHERE event_id = (SELECT MAX(event_id) FROM paper_trade_events WHERE trade_id = pte.trade_id)
             AND event_type != 'CLOSE'"""
    ).fetchall()
    return [r["trade_id"] for r in rows]


def record_journal_event(conn: sqlite3.Connection, *, event_type: str, detail: dict,
                          trade_id: str | None = None, decision_id: int | None = None,
                          reason: str | None = None) -> None:
    if event_type in ("G7_OVERRIDE",) and not reason:
        raise ValueError(f"{event_type} requires a logged reason -- an override with no reason is not a valid journal entry.")
    conn.execute(
        """INSERT INTO journal_events (event_type, trade_id, decision_id, detail, reason, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (event_type, trade_id, decision_id, json.dumps(detail), reason, _now()),
    )
    conn.commit()


def record_opportunity(conn: sqlite3.Connection, *, symbol: str, as_of_date: str, inputs: dict, state: str) -> None:
    conn.execute(
        "INSERT INTO opportunities (symbol, as_of_date, inputs, state, recorded_at) VALUES (?, ?, ?, ?, ?)",
        (symbol, as_of_date, json.dumps(inputs), state, _now()),
    )
    conn.commit()


def record_monitor_run(conn: sqlite3.Connection, *, run_date: str, report: dict) -> int:
    cur = conn.execute(
        "INSERT INTO monitor_runs (run_date, report, recorded_at) VALUES (?, ?, ?)",
        (run_date, json.dumps(report), _now()),
    )
    conn.commit()
    return cur.lastrowid
