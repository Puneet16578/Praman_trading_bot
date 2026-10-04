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
            isin_map_built_at TEXT,             -- NULL on decisions predating the freshness gate
            position_size REAL,                -- PERSISTED at assessment time -- `paper open` reads
            stress_loss_inr REAL,              -- this, and stop/target on the linked thesis, and
                                                -- NEVER re-runs the assessment (integrity fix b)
            as_of_is_live INTEGER NOT NULL,    -- 1 if as_of_date was the live/latest available
                                                -- trading day at ASSESSMENT time (0 = an explicit
                                                -- historical --as-of -- such a decision can never
                                                -- be paper-opened; that would be backtesting)
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
            price REAL NOT NULL,               -- ALWAYS the store's raw price -- NEVER cost-adjusted
                                                -- (post-STOP-3-plus consistency fix: costs are their
                                                -- own explicit fields below, never folded into price)
            quantity REAL NOT NULL,            -- absolute post-event quantity (0 after CLOSE)
            stop REAL NOT NULL,
            target REAL NOT NULL,
            reason TEXT NOT NULL,              -- e.g. "entry", "corporate action: SPLIT 2:1", "stop hit", "manual stop widen"
            buy_cost_inr REAL,                 -- round-trip BUY-side cost, recorded on OPEN only
            sell_cost_inr REAL,                -- round-trip SELL-side cost (incl. DP charge), CLOSE only
            cost_config_hash TEXT,             -- which cost config computed the above, OPEN/CLOSE only
            recorded_at TEXT NOT NULL
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_paper_trade_events_trade_id ON paper_trade_events(trade_id)",),
)

# Columns added to paper_trade_events after its original release (post-STOP-3-plus consistency fix).
# CREATE TABLE IF NOT EXISTS does NOT retroactively add columns to an already-existing table, so any
# desk.sqlite created before this fix needs an explicit, non-destructive ALTER TABLE ADD COLUMN --
# safe here specifically because every new column is nullable and no existing row is touched.
_PAPER_TRADE_EVENTS_ADDED_COLUMNS = (
    ("buy_cost_inr", "REAL"),
    ("sell_cost_inr", "REAL"),
    ("cost_config_hash", "TEXT"),
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

CIRCUIT_BANDS = DeskTable(
    name="circuit_bands",
    ddl="""
        CREATE TABLE circuit_bands (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            series TEXT NOT NULL,
            security_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            knowledge_date TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            band_kind TEXT NOT NULL CHECK(band_kind IN ('FIXED', 'DYNAMIC')),
            band_pct REAL,
            remarks TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            published_at TEXT NOT NULL,
            CHECK((band_kind='FIXED' AND band_pct > 0 AND band_pct <= 100)
                  OR (band_kind='DYNAMIC' AND band_pct IS NULL)),
            UNIQUE(symbol, series, event_date, knowledge_date, source_sha256)
        )
    """,
    indices=("CREATE INDEX IF NOT EXISTS idx_circuit_bands_asof ON circuit_bands(symbol,event_date,knowledge_date)",),
)

OPPORTUNITY_LOG = DeskTable(
    name="opportunity_log",
    ddl="""CREATE TABLE opportunity_log (
        opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        event_date TEXT NOT NULL,
        knowledge_date TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        inputs TEXT NOT NULL,
        evidence_bundle_hash TEXT NOT NULL,
        gate_results TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('SCREEN_PASS', 'SCREEN_FAIL')),
        reasons TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        code_commit TEXT NOT NULL,
        praman_watermark TEXT NOT NULL,
        desk_watermark TEXT NOT NULL,
        rulebook_hash TEXT NOT NULL,
        cost_config_hash TEXT NOT NULL,
        UNIQUE(symbol, event_date)
    )""",
)

OPPORTUNITY_EXECUTIONS = DeskTable(
    name="opportunity_executions",
    ddl="""CREATE TABLE opportunity_executions (
        execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL REFERENCES opportunity_log(opportunity_id),
        event_date TEXT NOT NULL,
        knowledge_date TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        record_type TEXT NOT NULL CHECK(record_type='EXECUTION'),
        observation TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        UNIQUE(opportunity_id)
    )""",
)

# Automation framework (TRADING_BLUEPRINT.md; session items B2-B4). Append-only like every other
# Desk table: a status change or a cleared kill switch is a new row, never an edit.
KILL_SWITCH_EVENTS = DeskTable(
    name="kill_switch_events",
    ddl="""CREATE TABLE kill_switch_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        switch TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('TRIGGERED', 'CLEARED', 'RESET')),
        effect TEXT NOT NULL,
        scope TEXT NOT NULL,               -- strategy_id, or 'desk'
        run_date TEXT NOT NULL,
        detail TEXT NOT NULL,              -- JSON; sealed detail is stored but never displayed early
        sealed INTEGER NOT NULL CHECK(sealed IN (0, 1)),
        reason TEXT,                       -- required for a human RESET
        recorded_at TEXT NOT NULL
    )""",
    indices=("CREATE INDEX IF NOT EXISTS idx_kill_switch_events_switch ON kill_switch_events(switch, scope)",),
)

TRADING_STRATEGIES = DeskTable(
    name="trading_strategies",
    ddl="""CREATE TABLE trading_strategies (
        row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT NOT NULL,
        version INTEGER NOT NULL CHECK(version >= 1),
        revision INTEGER NOT NULL CHECK(revision >= 1),  -- a status change appends a new revision
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        purpose TEXT NOT NULL,
        definition TEXT NOT NULL,          -- JSON: rules, entry policy and its justification
        content_hash TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        UNIQUE(strategy_id, version, revision)
    )""",
)

STRATEGY_RUNS = DeskTable(
    name="strategy_runs",
    ddl="""CREATE TABLE strategy_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT NOT NULL,
        strategy_version INTEGER NOT NULL,
        run_date TEXT NOT NULL,
        automation_level TEXT NOT NULL,
        rulebook_hash TEXT NOT NULL,
        cost_config_hash TEXT NOT NULL,
        code_commit TEXT NOT NULL,
        praman_watermark TEXT NOT NULL,
        operational TEXT NOT NULL,         -- JSON, operational metrics only (never P&L)
        recorded_at TEXT NOT NULL,
        UNIQUE(strategy_id, strategy_version, run_date)
    )""",
)

STRATEGY_PAPER_EVENTS = DeskTable(
    name="strategy_paper_events",
    ddl="""CREATE TABLE strategy_paper_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT NOT NULL,
        strategy_version INTEGER NOT NULL,
        run_id INTEGER NOT NULL REFERENCES strategy_runs(run_id),
        position_id TEXT,                  -- NULL for a rejected candidate
        opportunity_id INTEGER REFERENCES opportunity_log(opportunity_id),
        symbol TEXT NOT NULL,
        decision_date TEXT NOT NULL,
        event_type TEXT NOT NULL CHECK(event_type IN (
            'CANDIDATE_ACCEPTED', 'CANDIDATE_REJECTED', 'ENTRY_FILLED', 'ENTRY_NO_FILL',
            'ENTRY_FILL_FAILED', 'MONITORED', 'EXIT_ORDERED', 'EXIT_FILLED')),
        event_date TEXT NOT NULL,
        detail TEXT NOT NULL,              -- JSON
        recorded_at TEXT NOT NULL
    )""",
    indices=(
        "CREATE INDEX IF NOT EXISTS idx_strategy_paper_events_position ON strategy_paper_events(strategy_id, position_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_paper_events_candidate "
        "ON strategy_paper_events(strategy_id, strategy_version, opportunity_id) "
        "WHERE event_type IN ('CANDIDATE_ACCEPTED', 'CANDIDATE_REJECTED')",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_paper_events_once "
        "ON strategy_paper_events(strategy_id, position_id, event_type) "
        "WHERE event_type IN ('ENTRY_FILLED', 'ENTRY_NO_FILL', 'ENTRY_FILL_FAILED', 'EXIT_ORDERED', 'EXIT_FILLED')",
    ),
)

DECISION_CONTRACTS = DeskTable(
    name="decision_contracts",
    ddl="""CREATE TABLE decision_contracts (
        contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
        decision_id INTEGER REFERENCES decisions(decision_id),
        strategy_event_id INTEGER REFERENCES strategy_paper_events(event_id),
        contract TEXT NOT NULL,            -- JSON, blueprint candidate schema (section 3)
        content_hash TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        CHECK((decision_id IS NULL) != (strategy_event_id IS NULL))
    )""",
)

DESK_TABLES: dict[str, DeskTable] = {
    t.name: t for t in (DECISIONS, THESES, PAPER_TRADE_EVENTS, JOURNAL_EVENTS, OPPORTUNITIES, MONITOR_RUNS, CIRCUIT_BANDS,
                        OPPORTUNITY_LOG, OPPORTUNITY_EXECUTIONS, KILL_SWITCH_EVENTS, TRADING_STRATEGIES,
                        STRATEGY_RUNS, STRATEGY_PAPER_EVENTS, DECISION_CONTRACTS)
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


def _add_missing_columns(conn: sqlite3.Connection, table_name: str, added_columns: tuple) -> None:
    """ALTER TABLE ADD COLUMN for whichever of `added_columns` (name, sql_type) pairs the table
    doesn't already have -- safe and non-destructive (every added column here is nullable), and
    necessary because CREATE TABLE IF NOT EXISTS never retroactively adds a column to a table that
    already existed under an earlier schema version."""
    existing_cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}
    for name, sql_type in added_columns:
        if name not in existing_cols:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {sql_type}")


def _paper_trade_events_insert_validation_triggers() -> tuple:
    """Insert-time hardening (post-STOP-3-plus review), enforced in the database itself rather than
    trusted to every caller: an OPEN row with no buy_cost_inr/cost_config_hash, a CLOSE row with no
    sell_cost_inr/cost_config_hash, or ANY row with a non-integer quantity, is rejected outright. No
    behaviour change for any currently-exercised code path -- every real insert site
    (desk/journal/store.py) already always supplies these; this only turns "should never happen" into
    "cannot happen." Defined here, not in _append_only_trigger_sql, since these are specific to this
    one table's own columns, not a generic property every desk table shares. Must run AFTER
    _add_missing_columns -- a trigger referencing NEW.buy_cost_inr etc. cannot be created before
    those columns exist on the table."""
    require_open_costs = """
        CREATE TRIGGER IF NOT EXISTS trg_paper_trade_events_require_open_costs
        BEFORE INSERT ON paper_trade_events
        WHEN NEW.event_type = 'OPEN' AND (NEW.buy_cost_inr IS NULL OR NEW.cost_config_hash IS NULL)
        BEGIN
            SELECT RAISE(ABORT, 'paper_trade_events: an OPEN row requires buy_cost_inr and cost_config_hash (never NULL)');
        END
    """
    require_close_costs = """
        CREATE TRIGGER IF NOT EXISTS trg_paper_trade_events_require_close_costs
        BEFORE INSERT ON paper_trade_events
        WHEN NEW.event_type = 'CLOSE' AND (NEW.sell_cost_inr IS NULL OR NEW.cost_config_hash IS NULL)
        BEGIN
            SELECT RAISE(ABORT, 'paper_trade_events: a CLOSE row requires sell_cost_inr and cost_config_hash (never NULL)');
        END
    """
    require_integer_quantity = """
        CREATE TRIGGER IF NOT EXISTS trg_paper_trade_events_require_integer_quantity
        BEFORE INSERT ON paper_trade_events
        WHEN NEW.quantity != CAST(NEW.quantity AS INTEGER)
        BEGIN
            SELECT RAISE(ABORT, 'paper_trade_events: quantity must be a whole number (NSE trades in whole shares)');
        END
    """
    return require_open_costs, require_close_costs, require_integer_quantity


def migrate_decisions_isin_map(conn: sqlite3.Connection) -> tuple[int, int]:
    """Explicit additive migration, checked against the existing decision row count."""
    conn.execute("SAVEPOINT decisions_isin_map_migration")
    try:
        before = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(decisions)")}
        if "isin_map_built_at" not in columns:
            conn.execute("ALTER TABLE decisions ADD COLUMN isin_map_built_at TEXT")
        after = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        if before != after:
            raise RuntimeError("Decision row count changed during ISIN metadata migration")
    except Exception:
        conn.execute("ROLLBACK TO decisions_isin_map_migration")
        raise
    finally:
        conn.execute("RELEASE decisions_isin_map_migration")
    return before, after


def init_desk_db(conn: sqlite3.Connection) -> None:
    """Idempotent, like Praman's own init_db(): creates each table and its append-only triggers if
    not already present, adds indices unconditionally (IF NOT EXISTS), migrates any column added to
    a table's shape after that table's original release (see _PAPER_TRADE_EVENTS_ADDED_COLUMNS), and
    (re)creates paper_trade_events' own insert-time validation triggers."""
    existing = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in DESK_TABLES.values():
        if table.name not in existing:
            conn.execute(table.ddl)
        for index_ddl in table.indices:
            conn.execute(index_ddl)
        for trigger_sql in _append_only_trigger_sql(table.name):
            conn.execute(trigger_sql)
    _add_missing_columns(conn, "paper_trade_events", _PAPER_TRADE_EVENTS_ADDED_COLUMNS)
    migrate_decisions_isin_map(conn)
    for trigger_sql in _paper_trade_events_insert_validation_triggers():
        conn.execute(trigger_sql)
    conn.commit()
