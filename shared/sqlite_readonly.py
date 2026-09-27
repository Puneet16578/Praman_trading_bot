"""The one place that knows how to open a SQLite file read-only via URI mode=ro. Extracted from
demo/lib/store.py (which used to inline this) because the Desk needs the identical mechanism
against a different file (the real production store, not the demo's cutoff-truncated copy) --
duplicating six lines twice was the wrong call once a second caller needed it.

No project-specific path constants live here on purpose: this module doesn't know about
data/demo/ or data/processed/ or any Desk path. Each caller (demo/lib/store.py, desk/lib/store.py)
owns its own path constant and its own "missing/wrong file" error type, since what a missing store
means is different for each (the demo tells you to run its build script; the Desk tells you
production doesn't exist yet).
"""
from __future__ import annotations
import sqlite3
from pathlib import Path


def open_readonly(path: Path) -> sqlite3.Connection:
    """Opens `path` via SQLite's mode=ro URI (read succeeds, any write raises
    sqlite3.OperationalError: attempt to write a readonly database -- verified directly against a
    real store, tests/test_demo_readonly_guard.py). Does not check the file exists first -- sqlite3
    itself raises a clear sqlite3.OperationalError ("unable to open database file") if it doesn't,
    which is enough; callers wanting a friendlier, project-specific message check existence
    themselves before calling this, since only the caller knows what "missing" should tell the user
    to do about it."""
    uri = f"file:{Path(path).as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
