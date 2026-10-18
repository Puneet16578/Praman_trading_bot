from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.abc_event_day_context import calculate


class AbcEventDayContextReadOnlyTest(unittest.TestCase):
    def test_event_day_calculation_never_queries_later_bars(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db_path = root / "fixture.sqlite"
            catalogue = root / "events.csv"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE bhavcopy (row_id INTEGER, symbol TEXT, series TEXT, event_date TEXT, knowledge_date TEXT, close_price REAL)")
                conn.execute("CREATE TABLE corporate_actions (row_id INTEGER, symbol TEXT, action_type TEXT, event_date TEXT, knowledge_date TEXT, ratio_numerator REAL, ratio_denominator REAL)")
                conn.executemany(
                    "INSERT INTO bhavcopy VALUES (?, ?, 'EQ', ?, ?, ?)",
                    [
                        (1, "FOCAL", "2024-01-02", "2024-01-02", 101.0),
                        (2, "PEER", "2024-01-02", "2024-01-02", 202.0),
                        (3, "FUTURE", "2024-01-03", "2024-01-03", 10000.0),
                    ],
                )
                conn.executemany(
                    "INSERT INTO bhavcopy VALUES (?, ?, 'EQ', ?, ?, ?)",
                    [
                        (4, "FOCAL", "2024-01-01", "2024-01-01", 100.0),
                        (5, "PEER", "2024-01-01", "2024-01-01", 200.0),
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            with catalogue.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["symbol", "event_date", "return_1d"])
                writer.writeheader()
                writer.writerow({"symbol": "FOCAL", "event_date": "2024-01-02", "return_1d": 0.01})

            conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            statements: list[str] = []
            conn.set_trace_callback(statements.append)
            try:
                market, _ = calculate(conn, catalogue)
                repeated_market, _ = calculate(conn, catalogue)
            finally:
                conn.close()

            self.assertEqual(market[0]["events"], 1)
            self.assertEqual(market, repeated_market)
            self.assertEqual(market[0]["up"], 0)
            self.assertEqual(market[0]["down"], 0)
            selects = [sql.lower() for sql in statements if "select" in sql.lower() and "bhavcopy" in sql.lower()]
            self.assertTrue(selects)
            self.assertTrue(all("2024-01-03" not in sql for sql in selects))

    def test_adjustment_uses_only_visible_point_in_time_action(self):
        from scripts.abc_event_day_context import _return

        previous = ("2024-01-01", 100.0)
        visible = [{"event_date": "2024-01-02", "action_type": "BONUS",
                    "ratio_numerator": 1.0, "ratio_denominator": 1.0}]
        self.assertAlmostEqual(_return(previous, "2024-01-02", 50.5, visible), 0.01)
        self.assertAlmostEqual(_return(previous, "2024-01-02", 50.5, ()), -0.495)


if __name__ == "__main__":
    unittest.main()
