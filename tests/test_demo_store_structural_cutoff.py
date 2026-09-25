"""Constraint 2 (forward-window cutoff), the STRUCTURAL layer: the demo store itself must contain
no row past the cutoff in any fact table, and the demo's own rebuilt picker catalogue must not be
able to reveal a post-cutoff fact even indirectly (a session-count with no date embedded in it --
exactly the pattern-filter blind spot tests/test_demo_cutoff_redaction.py documents and does not
close).

Skipped entirely if data/demo/ has not been built yet -- run `python demo/build_demo_store.py`.
"""
from __future__ import annotations
import csv
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo.lib import catalogue, store
from demo.lib.cutoff import DEMO_DATA_CUTOFF

_DEMO_DB_EXISTS = store.DEMO_DB_PATH.exists()
_DEMO_CSV_EXISTS = store.DEMO_CLASSIFICATIONS_PATH.exists()

FACT_TABLES = ("bhavcopy", "corporate_actions", "surveillance_flags", "corporate_announcements", "sebi_orders")


@unittest.skipUnless(_DEMO_DB_EXISTS, f"Demo store not found at {store.DEMO_DB_PATH}. Run demo/build_demo_store.py.")
class DemoStoreDatesTest(unittest.TestCase):
    def test_every_table_capped_at_cutoff(self):
        conn = sqlite3.connect(f"file:{store.DEMO_DB_PATH.as_posix()}?mode=ro", uri=True)
        try:
            for table in FACT_TABLES:
                row = conn.execute(f"SELECT MAX(event_date) me, MAX(knowledge_date) mk FROM {table}").fetchone()
                max_event_date, max_knowledge_date = row
                if max_event_date is not None:
                    self.assertLessEqual(max_event_date, DEMO_DATA_CUTOFF, f"{table}.event_date exceeds cutoff")
                if max_knowledge_date is not None:
                    self.assertLessEqual(max_knowledge_date, DEMO_DATA_CUTOFF, f"{table}.knowledge_date exceeds cutoff")
        finally:
            conn.close()


@unittest.skipUnless(_DEMO_CSV_EXISTS, f"Demo picker catalogue not found at {store.DEMO_CLASSIFICATIONS_PATH}. Run demo/build_demo_store.py.")
class LeakTest(unittest.TestCase):
    """ASHOKAMET/2026-09-11 (real data): its actual first surveillance flag, in the UNTRUNCATED
    production store, lands on 2026-09-16 -- one day after the demo cutoff (2026-09-15). If the
    demo's picker catalogue were built from the full-knowledge production data (or patched only by
    pattern-matching rendered dates), this event would show a real, post-cutoff-revealing lead-time
    session count. Built from the truncated demo store instead, the flag record itself does not
    exist in the data build_event_classifications.py saw -- it must render exactly what a symbol
    with genuinely no subsequent flag renders."""

    def test_ashokamet_2026_09_11_shows_no_subsequent_flag_not_a_leaked_session_count(self):
        rows = [r for r in catalogue.load_rows() if r["symbol"] == "ASHOKAMET" and r["event_date"] == "2026-09-11"]
        self.assertEqual(len(rows), 1, "Expected exactly one ASHOKAMET/2026-09-11 row in the demo catalogue.")
        row = rows[0]
        self.assertIn(row["sessions_to_subsequent_flag"], ("", None),
                      f"Expected no session count (the real flag is past the cutoff), got {row['sessions_to_subsequent_flag']!r}")
        self.assertEqual(row["subsequent_flag_note"], "no subsequent flag as of latest data",
                          "For the demo store, 'latest data' IS the cutoff -- this is the real, "
                          "unmodified event_classifier.py wording, not a demo-specific string.")


if __name__ == "__main__":
    unittest.main()
