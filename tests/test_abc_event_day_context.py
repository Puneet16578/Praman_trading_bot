from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.abc_event_day_context import calculate, calculate_repaired, _bucket, _repaired_correlations, _calendar


class CalendarIndependentOfRequestsTest(unittest.TestCase):
    """P8-093: a session is in the calendar only if an EQ bar is known on its own day, whatever
    dates a run requests. On the old code, a session published two days late entered the calendar
    once a request reached its knowledge date."""

    def test_a_late_published_session_is_never_admitted_whatever_the_request(self):
        conn = sqlite3.connect(':memory:')
        try:
            conn.execute('CREATE TABLE bhavcopy (symbol TEXT, series TEXT, event_date TEXT, knowledge_date TEXT)')
            days = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-08']
            rows = [(s, 'EQ', d, d) for d in days for s in ('A', 'B') if d != '2024-01-03']
            rows += [('A', 'EQ', '2024-01-03', '2024-01-05'), ('B', 'EQ', '2024-01-03', '2024-01-08')]   # known late
            conn.executemany('INSERT INTO bhavcopy VALUES (?,?,?,?)', rows)
            expected = ['2024-01-01', '2024-01-02', '2024-01-04', '2024-01-05', '2024-01-08']
            for through in ('2024-01-03', '2024-01-04', '2024-01-05', '2024-01-08', '2030-01-01'):
                with self.subTest(through=through):
                    self.assertEqual(_calendar(conn, '', through), [d for d in expected if d <= through])
            chunked = _calendar(conn, '', '2024-01-02') + _calendar(conn, '2024-01-02', '2024-01-04') + \
                _calendar(conn, '2024-01-04', '2024-01-08')
            self.assertEqual(chunked, expected)                       # any chunking gives the same list
        finally:
            conn.close()


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
                        (6, "FUND", "2024-01-02", "2024-01-02", 103.0),
                    ],
                )
                conn.executemany(
                    "INSERT INTO bhavcopy VALUES (?, ?, 'EQ', ?, ?, ?)",
                    [
                        (4, "FOCAL", "2024-01-01", "2024-01-01", 100.0),
                        (5, "PEER", "2024-01-01", "2024-01-01", 200.0),
                        (7, "FUND", "2024-01-01", "2024-01-01", 100.0),
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

            # The follow-up path uses the same strict event-date boundary.
            conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            repaired_statements: list[str] = []
            conn.set_trace_callback(repaired_statements.append)
            try:
                repaired = calculate_repaired(
                    conn, {"FOCAL": "INE000000001", "PEER": "INE000000002", "FUND": "INF000000001"},
                    catalogue, sanity_date=None,
                )
            finally:
                conn.close()
            self.assertEqual(repaired["market"][0]["catalogue_event_days"], 1)
            self.assertAlmostEqual(repaired["market"][0]["mean_of_daily_market_means"], 0.01)
            self.assertEqual(repaired["identity_universe"]["fund_isin_symbols_excluded"], 1)
            repaired_selects = [sql.lower() for sql in repaired_statements
                                if "select" in sql.lower() and "bhavcopy" in sql.lower()]
            self.assertTrue(repaired_selects)
            self.assertTrue(all("2024-01-03" not in sql for sql in repaired_selects))

    def test_a_one_year_repaired_run_gives_the_full_run_rows_for_that_year(self):
        """`--years` (2026-10-19): a one-year run streams every session, so its rows for that year, the
        identity universe and the sanity check equal the all-years run's."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db_path = root / "fixture.sqlite"
            catalogue = root / "events.csv"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("CREATE TABLE bhavcopy (row_id INTEGER, symbol TEXT, series TEXT, event_date TEXT, knowledge_date TEXT, close_price REAL)")
                conn.execute("CREATE TABLE corporate_actions (row_id INTEGER, symbol TEXT, action_type TEXT, event_date TEXT, knowledge_date TEXT, ratio_numerator REAL, ratio_denominator REAL)")
                days = ["2023-12-27", "2023-12-28", "2023-12-29", "2024-01-01", "2024-01-02"]
                prices = {"FOCAL": [100, 98, 95, 97, 92], "PEER": [200, 199, 196, 198, 195], "OTHER": [50, 51, 50, 52, 51]}
                conn.executemany(
                    "INSERT INTO bhavcopy VALUES (?, ?, 'EQ', ?, ?, ?)",
                    [(i * 10 + j, symbol, day, day, float(close)) for j, (symbol, closes) in enumerate(prices.items())
                     for i, (day, close) in enumerate(zip(days, closes))],
                )
                conn.commit()
            finally:
                conn.close()
            with catalogue.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["symbol", "event_date", "return_1d"])
                writer.writeheader()
                writer.writerow({"symbol": "FOCAL", "event_date": "2023-12-29", "return_1d": -0.03})
                writer.writerow({"symbol": "FOCAL", "event_date": "2024-01-02", "return_1d": -0.05})
            identities = {"FOCAL": "INE000000001", "PEER": "INE000000002", "OTHER": "INE000000003"}
            conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                full = calculate_repaired(conn, identities, catalogue, sanity_date="2024-01-02")
                one = calculate_repaired(conn, identities, catalogue, sanity_date="2024-01-02", years={2024})
            finally:
                conn.close()
            self.assertEqual({row["year"] for row in full["market"]}, {2023, 2024})
            self.assertEqual(one["market"], [row for row in full["market"] if row["year"] == 2024])
            self.assertEqual(one["peers"], [row for row in full["peers"] if row["year"] == 2024])
            self.assertTrue(one["peers"])
            for key in ("identity_universe", "sanity", "sanity_date"):
                self.assertEqual(one[key], full[key])

    def test_adjustment_uses_only_visible_point_in_time_action(self):
        from scripts.abc_event_day_context import _return

        previous = ("2024-01-01", 100.0)
        visible = [{"event_date": "2024-01-02", "action_type": "BONUS",
                    "ratio_numerator": 1.0, "ratio_denominator": 1.0}]
        self.assertAlmostEqual(_return(previous, "2024-01-02", 50.5, visible), 0.01)
        self.assertAlmostEqual(_return(previous, "2024-01-02", 50.5, ()), -0.495)

    def test_repaired_peer_minimum_and_current_day_candidate_filter(self):
        x = np.linspace(-0.02, 0.02, 200)
        history = np.column_stack((x, x * 2, -x))
        peers = _repaired_correlations(history, ["FOCAL", "P1", "P2"], "FOCAL", {"P2"}, 200)
        self.assertEqual([item[2] for item in peers], ["P2"])
        self.assertEqual(_repaired_correlations(history, ["FOCAL", "P1", "P2"], "FOCAL", {"P2"}, 201), [])

    def test_ratio_bucket_boundaries(self):
        self.assertEqual(_bucket(-0.01), "counter")
        self.assertEqual(_bucket(0.0), "under25")
        self.assertEqual(_bucket(0.25), "25_50")
        self.assertEqual(_bucket(0.5), "50_75")
        self.assertEqual(_bucket(0.75), "50_75")
        self.assertEqual(_bucket(0.75001), "over75")


if __name__ == "__main__":
    unittest.main()
