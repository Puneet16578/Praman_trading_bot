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
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in BITEMPORAL_TABLES.values():
        if table.name not in existing:
            conn.execute(table.ddl)
    conn.commit()
