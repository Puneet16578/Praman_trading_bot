"""Constraint 3 (read-only): demo/lib/store.py opens the demo database via SQLite's mode=ro URI,
never src.bitemporal.connection.get_connection. Verifies reads succeed and a write attempt fails,
against the REAL demo store when it exists; the missing-store error path is tested unconditionally
since it needs no real data at all.

Skipped (structural-cutoff/happy-path tests) if data/demo/praman_demo.sqlite does not exist yet --
run `python demo/build_demo_store.py` first. Same convention as
tests/test_event_catalogue_real_data_guard.py.
"""
from __future__ import annotations
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo.lib import store

_DEMO_DB_EXISTS = store.DEMO_DB_PATH.exists()


class MissingStoreTest(unittest.TestCase):
    def test_missing_store_raises_clear_error_not_a_silent_fallback(self):
        original = store.DEMO_DB_PATH
        try:
            store.DEMO_DB_PATH = Path("/definitely/does/not/exist/praman_demo.sqlite")
            with self.assertRaises(store.DemoStoreMissingError):
                store.get_demo_connection()
        finally:
            store.DEMO_DB_PATH = original


@unittest.skipUnless(_DEMO_DB_EXISTS, f"Demo store not found at {store.DEMO_DB_PATH}. Run demo/build_demo_store.py.")
class ReadOnlyGuardTest(unittest.TestCase):
    def test_read_succeeds(self):
        conn = store.get_demo_connection()
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM bhavcopy").fetchone()
            self.assertGreater(row["n"], 0)
        finally:
            conn.close()

    def test_write_attempt_fails(self):
        conn = store.get_demo_connection()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute(
                    "INSERT INTO corporate_actions (symbol, action_type, event_date, "
                    "knowledge_date, confidence_tier, source_file, recorded_at) VALUES "
                    "('TEST','BONUS','2020-01-01','2020-01-01','CONFIRMED','x','2020-01-01')"
                )
        finally:
            conn.close()

    def test_delete_attempt_fails(self):
        conn = store.get_demo_connection()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("DELETE FROM bhavcopy WHERE 1=1")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
