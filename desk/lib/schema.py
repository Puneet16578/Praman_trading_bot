"""Desk store schema (data/desk/desk.sqlite) -- a separate database from Praman's, owned entirely
by the Desk. Every table is APPEND-ONLY, enforced by SQLite triggers (not by convention, not by
"the code just doesn't call UPDATE"): a BEFORE UPDATE and a BEFORE DELETE trigger on every table
abort with RAISE(ABORT, ...) unconditionally. A revised fact is a new row referencing the old one
(the same "restatements never overwrite" discipline CLAUDE.md invariant 8 states for Praman itself,
applied here to the Desk's own store -- Desk invariant D1).

Consequence for tables that have "current state" (an open paper position, for instance):
paper_trade_events is an EVENT LOG, not a mutable row -- opening, adjusting (a corporate action, a
manual stop widen), and closing a position are each a new row sharing the same trade_id. "The
current stop for trade X" is "the stop on the latest event row for trade_id=X", derived by query,
never stored as a single updatable field.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DeskTable:
    name: str
    ddl: str
    indices: tuple[str, ...] = field(default_factory=tuple)


DECISIONS = DeskTable(
    name="decisions",
    ddl="""
        CREATE TABLE decisions (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            thesis_id INTEGER,
            evidence_bundle_hash TEXT NOT NULL,
            gate_results TEXT NOT NULL,        -- JSON: {"G1": {"result": "PASS", "reasons": [...]}, ...}
            state TEXT NOT NULL,
            rulebook_version TEXT NOT NULL,
            rulebook_hash TEXT NOT NULL,
            cost_config_version TEXT NOT NULL,
            cost_config_hash TEXT NOT NULL,
            code_commit TEXT NOT NULL,
            praman_watermark TEXT NOT NULL,
            desk_watermark TEXT NOT NULL,
            model_version TEXT,                -- NULL in Phase 1 (no LLM)
            prompt_version TEXT,               -- NULL in Phase 1
            override_reason TEXT,              -- non-NULL only for a logged G7 override
            recorded_at TEXT NOT NULL
        )
    """,
    indices=(
        "CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_decisions_recorded_at ON decisions(recorded_at)",
    ),
)

THESES = DeskTable(
    name="theses",
    ddl="""
        CREATE TABLE theses (
            thesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prior_thesis_id INTEGER,           -- non-NULL for an amendment; the amended row is never touched
            symbol TEXT NOT NULL,
            evidence_cutoff TEXT NOT NULL,
            hypotheses TEXT NOT NULL,          -- JSON list of {statement, test, monitor}
            drivers TEXT NOT NULL,             -- JSON list
            catalyst TEXT,
            horizon TEXT NOT NULL,             -- ISO date the thesis expires if no entry
            invalidation_conditions TEXT NOT NULL,  -- JSON list
            exit_price TEXT,                   -- JSON: {trigger description}
            exit_time TEXT,
            exit_evidence TEXT,
            exit_risk TEXT,
            exit_portfolio TEXT,
            planned_entry REAL NOT NULL,
            planned_stop REAL NOT NULL,
            planned_target REAL NOT NULL,
            stress_loss REAL,
            position_size REAL,
            portfolio_risk_added REAL,
            user_probability REAL,             -- flagged SUBJECTIVE at the point of use, never treated as calibrated
            sector TEXT NOT NULL,              -- user-supplied in Phase 1
            paper_or_live TEXT NOT NULL,       -- 'PAPER' only in Phase 1
            recorded_at TEXT NOT NULL
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_theses_symbol ON theses(symbol)",),
)

PAPER_TRADE_EVENTS = DeskTable(
    name="paper_trade_events",
    ddl="""
        CREATE TABLE paper_trade_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT NOT NULL,            -- stable across every event for one position
            decision_id INTEGER,               -- the ELIGIBLE decision that opened this trade (OPEN events)
            event_type TEXT NOT NULL,          -- OPEN / ADJUST / CLOSE
            event_date TEXT NOT NULL,          -- trading-calendar date of the fill
            price REAL NOT NULL,
            quantity REAL NOT NULL,            -- absolute post-event quantity (0 after CLOSE)
            stop REAL NOT NULL,
            target REAL NOT NULL,
            reason TEXT NOT NULL,              -- e.g. "entry", "corporate action: SPLIT 2:1", "stop hit", "manual stop widen"
            recorded_at TEXT NOT NULL
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_paper_trade_events_trade_id ON paper_trade_events(trade_id)",),
)

JOURNAL_EVENTS = DeskTable(
    name="journal_events",
    ddl="""
        CREATE TABLE journal_events (
            journal_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,          -- e.g. STOP_WIDENED, G7_OVERRIDE, DRAWDOWN_BRAKE_TRIGGERED
            trade_id TEXT,
            decision_id INTEGER,
            detail TEXT NOT NULL,              -- JSON
            reason TEXT,                       -- required (enforced in code) for an override event
            recorded_at TEXT NOT NULL
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_journal_events_trade_id ON journal_events(trade_id)",),
)

OPPORTUNITIES = DeskTable(
    name="opportunities",
    ddl="""
        CREATE TABLE opportunities (
            opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            inputs TEXT NOT NULL,              -- JSON snapshot, nightly log -- inputs and state only
            state TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_opportunities_symbol ON opportunities(symbol)",),
)

MONITOR_RUNS = DeskTable(
    name="monitor_runs",
    ddl="""
        CREATE TABLE monitor_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            report TEXT NOT NULL,              -- JSON: what-changed per symbol
            recorded_at TEXT NOT NULL
        )
    """,
)

DESK_TABLES: dict[str, DeskTable] = {
    t.name: t for t in (DECISIONS, THESES, PAPER_TRADE_EVENTS, JOURNAL_EVENTS, OPPORTUNITIES, MONITOR_RUNS)
}


def _append_only_trigger_sql(table_name: str) -> tuple[str, str]:
    update_trigger = f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table_name}_no_update
        BEFORE UPDATE ON {table_name}
        BEGIN
            SELECT RAISE(ABORT, '{table_name} is append-only: UPDATE is not permitted');
        END
    """
    delete_trigger = f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table_name}_no_delete
        BEFORE DELETE ON {table_name}
        BEGIN
            SELECT RAISE(ABORT, '{table_name} is append-only: DELETE is not permitted');
        END
    """
    return update_trigger, delete_trigger


def init_desk_db(conn: sqlite3.Connection) -> None:
    """Idempotent, like Praman's own init_db(): creates each table and its append-only triggers if
    not already present, adds indices unconditionally (IF NOT EXISTS)."""
    existing = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in DESK_TABLES.values():
        if table.name not in existing:
            conn.execute(table.ddl)
        for index_ddl in table.indices:
            conn.execute(index_ddl)
        for trigger_sql in _append_only_trigger_sql(table.name):
            conn.execute(trigger_sql)
    conn.commit()
