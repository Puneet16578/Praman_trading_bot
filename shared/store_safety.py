"""Reject destructive filesystem operations on the two durable stores.

Install when opening a Desk connection or running the test suite. Experiments
must use temporary copies; this is a Python guard, not an OS permission policy.
"""
import os
import sys
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = (ROOT / 'data/desk/desk.sqlite', ROOT / 'data/processed/praman.db')
_installed = False


def check_operation(event, args, protected=PROTECTED):
    def contains_store(value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        path = Path(os.fsdecode(value)).resolve()
        return any(path == p.resolve() or path in p.resolve().parents for p in protected)

    if event in ('os.remove', 'os.rmdir', 'os.rename'):
        paths = args[:2] if event == 'os.rename' else args[:1]
        if any(contains_store(p) for p in paths):
            raise PermissionError('Durable stores cannot be removed, moved, or replaced; use a temporary copy.')
    if event == 'open' and contains_store(args[0]):
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in 'wax')) or (flags or 0) & os.O_TRUNC:
            raise PermissionError('Durable stores cannot be truncated or recreated; use a temporary copy.')


def install_guard():
    global _installed
    if not _installed:
        sys.addaudithook(check_operation)
        _installed = True


def protect_connection(conn, path):
    """Keep durable tables append-only even when a caller bypasses the journal."""
    if str(path) == ':memory:' or Path(path).resolve() not in PROTECTED:
        return
    denied = {sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_TRIGGER,
              sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_VIEW}

    def authorize(action, table, column, database, source):
        if database == 'main':
            if action in denied:
                return sqlite3.SQLITE_DENY
            if action in (sqlite3.SQLITE_DELETE, sqlite3.SQLITE_UPDATE) and table not in ('sqlite_master', 'sqlite_sequence'):
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    conn.set_authorizer(authorize)
