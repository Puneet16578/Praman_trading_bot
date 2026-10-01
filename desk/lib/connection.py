"""The Desk's own store connection -- a completely separate SQLite file (data/desk/desk.sqlite)
from Praman's. Read-write for the Desk process itself (it needs to INSERT), but every table's
append-only triggers (schema.py) make UPDATE/DELETE abort regardless of this connection's own
permissions -- the guarantee lives in the database, not in which connection mode opens it.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

from .schema import init_desk_db
from shared.store_safety import install_guard, protect_connection

install_guard()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESK_DB_PATH = PROJECT_ROOT / "data" / "desk" / "desk.sqlite"


def get_desk_connection(db_path: Path | str = DESK_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    protect_connection(conn, db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    init_desk_db(conn)
    return conn
