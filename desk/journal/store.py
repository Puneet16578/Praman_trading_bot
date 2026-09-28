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
                     as_of_is_live: bool, isin_map_built_at: str,
                     position_size: float | None = None, stress_loss_inr: float | None = None,
                     model_version: str | None = None, prompt_version: str | None = None,
                     override_reason: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO decisions
           (symbol, as_of_date, thesis_id, evidence_bundle_hash, gate_results, state,
            rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit,
            praman_watermark, desk_watermark, model_version, prompt_version, override_reason,
            position_size, stress_loss_inr, as_of_is_live, recorded_at, isin_map_built_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (symbol, as_of_date, thesis_id, evidence_bundle_hash, json.dumps(gate_results), state,
         rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit,
         praman_watermark, desk_watermark_value, model_version, prompt_version, override_reason,
         position_size, stress_loss_inr, int(bool(as_of_is_live)), _now(), isin_map_built_at),
    )
    conn.commit()
    return cur.lastrowid


def get_decision(conn: sqlite3.Connection, decision_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["gate_results"] = json.loads(d["gate_results"])
    d["as_of_is_live"] = bool(d["as_of_is_live"])
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
                         stop: float, target: float, reason: str,
                         buy_cost_inr: float | None = None, sell_cost_inr: float | None = None,
                         cost_config_hash: str | None = None) -> None:
    """`price` is ALWAYS the store's raw price -- never cost-adjusted (post-STOP-3-plus consistency
    fix). `buy_cost_inr`/`sell_cost_inr`/`cost_config_hash` are the separate, explicit cost fields:
    OPEN populates buy_cost_inr, CLOSE populates sell_cost_inr, ADJUST populates neither."""
    conn.execute(
        """INSERT INTO paper_trade_events
           (trade_id, decision_id, event_type, event_date, price, quantity, stop, target, reason,
            buy_cost_inr, sell_cost_inr, cost_config_hash, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trade_id, decision_id, event_type, event_date, price, quantity, stop, target, reason,
         buy_cost_inr, sell_cost_inr, cost_config_hash, _now()),
    )
    conn.commit()


def open_paper_trade(conn: sqlite3.Connection, *, trade_id: str, decision_id: int, event_date: str,
                      price: float, quantity: float, stop: float, target: float,
                      reason: str = "entry", buy_cost_inr: float | None = None,
                      cost_config_hash: str | None = None) -> None:
    if latest_trade_event(conn, trade_id) is not None:
        raise ValueError(f"trade_id {trade_id!r} already has events -- OPEN must be the first event.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=decision_id, event_type="OPEN",
                         event_date=event_date, price=price, quantity=quantity, stop=stop,
                         target=target, reason=reason, buy_cost_inr=buy_cost_inr,
                         cost_config_hash=cost_config_hash)


def adjust_paper_trade(conn: sqlite3.Connection, *, trade_id: str, event_date: str, price: float,
                        quantity: float, stop: float, target: float, reason: str) -> None:
    prior = latest_trade_event(conn, trade_id)
    if prior is None or prior["event_type"] == "CLOSE":
        raise ValueError(f"trade_id {trade_id!r} has no open position to adjust.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=None, event_type="ADJUST",
                         event_date=event_date, price=price, quantity=quantity, stop=stop,
                         target=target, reason=reason)


def close_paper_trade(conn: sqlite3.Connection, *, trade_id: str, event_date: str, price: float,
                       reason: str, sell_cost_inr: float | None = None,
                       cost_config_hash: str | None = None) -> None:
    prior = latest_trade_event(conn, trade_id)
    if prior is None or prior["event_type"] == "CLOSE":
        raise ValueError(f"trade_id {trade_id!r} has no open position to close.")
    _record_trade_event(conn, trade_id=trade_id, decision_id=None, event_type="CLOSE",
                         event_date=event_date, price=price, quantity=0.0, stop=prior["stop"],
                         target=prior["target"], reason=reason, sell_cost_inr=sell_cost_inr,
                         cost_config_hash=cost_config_hash)


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


def pending_paper_opens(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """(decision_id, not_before_date) for every decision with a PAPER_OPEN_PENDING journal event and
    no OPEN paper_trade_event yet for its own trade_id. `not_before_date` is read back from that
    event's own `detail` -- the date FROZEN when `desk paper open` first returned PENDING, never
    recomputed from a later 'now' (see desk/paper/open.py:resume_pending_open for why that matters).
    Used by `desk monitor` to complete a paper entry automatically once the target session's data
    has been ingested -- not a new autonomous decision, since the human already approved opening
    this exact decision via the original `desk paper open` call that logged the PENDING event."""
    rows = conn.execute(
        """SELECT decision_id, detail FROM journal_events
           WHERE event_type = 'PAPER_OPEN_PENDING' AND decision_id IS NOT NULL
           ORDER BY journal_event_id"""
    ).fetchall()
    latest_not_before: dict[int, str] = {}
    for row in rows:
        latest_not_before[row["decision_id"]] = json.loads(row["detail"])["not_before_date"]

    pending = []
    for decision_id, not_before_date in latest_not_before.items():
        decision = get_decision(conn, decision_id)
        if decision is None or decision["thesis_id"] is None:
            continue
        trade_id = f"{decision['symbol']}:{decision['thesis_id']}"
        already_open = conn.execute(
            "SELECT 1 FROM paper_trade_events WHERE trade_id = ? AND event_type = 'OPEN' LIMIT 1", (trade_id,)
        ).fetchone()
        if already_open is None:
            pending.append((decision_id, not_before_date))
    return pending


def pending_paper_closes(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """(trade_id, not_before_date, reason) for every trade with an unresolved PAPER_CLOSE_PENDING
    journal event -- "unresolved" meaning the trade's LATEST event still isn't CLOSE. A trade closed
    by something else entirely in the meantime (a real stop hit in a normal monitor run) is not an
    error and not returned here; it's simply already resolved. Mirrors `pending_paper_opens` above
    for exactly the same reason: `desk monitor` (desk/paper/close.py:resume_pending_close) retries
    each of these at its OWN frozen `not_before_date`, never a freshly-recomputed one."""
    rows = conn.execute(
        """SELECT trade_id, detail FROM journal_events
           WHERE event_type = 'PAPER_CLOSE_PENDING' AND trade_id IS NOT NULL
           ORDER BY journal_event_id"""
    ).fetchall()
    latest_detail: dict[str, dict] = {}
    for row in rows:
        latest_detail[row["trade_id"]] = json.loads(row["detail"])

    pending = []
    for trade_id, detail in latest_detail.items():
        current = latest_trade_event(conn, trade_id)
        if current is not None and current["event_type"] != "CLOSE":
            pending.append((trade_id, detail["not_before_date"], detail["reason"]))
    return pending


def record_monitor_run(conn: sqlite3.Connection, *, run_date: str, report: dict) -> int:
    cur = conn.execute(
        "INSERT INTO monitor_runs (run_date, report, recorded_at) VALUES (?, ?, ?)",
        (run_date, json.dumps(report), _now()),
    )
    conn.commit()
    return cur.lastrowid
