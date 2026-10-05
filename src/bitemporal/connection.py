"""SQLite connection + schema bootstrap. Local-first, matching InsightForge's default mode."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .schema import BITEMPORAL_TABLES, ANNOUNCEMENT_METADATA_COLUMNS
from shared.store_safety import install_guard, protect_connection

install_guard()

def get_connection(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    protect_connection(conn, db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    if db_path != ":memory:":
        # WAL (write-ahead log) is a per-database-file setting, not per-connection -- set once here
        # so it applies to every future connection to this file. Added for Phase 5's full bhavcopy
        # history ingestion (~4.5M rows projected, single long-running writer): WAL lets a separate
        # read-only process (a progress-check script) query the DB concurrently without blocking or
        # being blocked by the writer, which the default rollback-journal mode does not allow.
        conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in BITEMPORAL_TABLES.values():
        if table.name not in existing:
            conn.execute(table.ddl)
        if table.name == 'corporate_announcements':
            columns = {r['name'] for r in conn.execute('PRAGMA table_info(corporate_announcements)')}
            for column in ANNOUNCEMENT_METADATA_COLUMNS:
                if column not in columns:
                    conn.execute(f'ALTER TABLE corporate_announcements ADD COLUMN {column} TEXT')
        # Indices are derived, query-speed-only structures (schema.py's note on FactTable.indices)
        # -- created every call via IF NOT EXISTS regardless of whether the table itself is new, so
        # an index added to an existing FactTable definition still gets created on an old DB file.
        for index_ddl in table.indices:
            conn.execute(index_ddl)
        for trigger_ddl in table.triggers:
            conn.execute(trigger_ddl)
    conn.commit()
