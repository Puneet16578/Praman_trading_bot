"""SQLite connection + schema bootstrap. Local-first, matching InsightForge's default mode."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .schema import BITEMPORAL_TABLES

def get_connection(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
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
    conn.commit()
