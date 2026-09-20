"""Fixture tests for src/agent/derivation_check.py -- the independent, second-implementation
recomputation the Adversary's DERIVATION tier relies on. These tests use a hand-built fixture with
values chosen so the expected result can be computed by hand and checked directly, independent of
any of this project's own derivation code (compute_daily_stats is never imported here)."""
from __future__ import annotations
import datetime
import unittest

from src.agent.derivation_check import (
    independent_delivery_percentile, independent_volume_ratio, is_sampled_for_derivation, values_agree,
)
from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_facts

SYMBOL = "DERIVTEST"

def _weekday_dates(n: int, start: datetime.date) -> list[str]:
    dates = []
    d = start
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return dates

class DerivationCheckFixtureTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        self.days = _weekday_dates(61, datetime.date(2024, 1, 1))
        self.event_date = self.days[-1]
        rows = []
        for i, d in enumerate(self.days[:-1]):  # 60 trailing days
            rows.append({
                "symbol": SYMBOL, "event_date": d, "knowledge_date": d,
                "open_price": 10.0, "high_price": 10.0, "low_price": 10.0, "close_price": 10.0,
                "prev_close": 10.0, "traded_qty": 100 * (i + 1), "delivery_qty": 1,
                "delivery_pct": float(i), "series": "EQ", "source_file": "fixture",
            })
        # event day: traded_qty chosen so volume_ratio is an exact, hand-checkable value
        rows.append({
            "symbol": SYMBOL, "event_date": self.event_date, "knowledge_date": self.event_date,
            "open_price": 10.0, "high_price": 10.0, "low_price": 10.0, "close_price": 10.0,
            "prev_close": 10.0, "traded_qty": 30500, "delivery_qty": 1,
            "delivery_pct": 30.0, "series": "EQ", "source_file": "fixture",
        })
        write_facts(self.conn, "bhavcopy", rows)

    def test_independent_volume_ratio_matches_hand_computed_value(self):
        # trailing traded_qty = 100, 200, ..., 6000 (60 values); median = avg(3000, 3100) = 3050
        # event day traded_qty = 30500 -> ratio = 30500 / 3050 = 10.0 exactly
        result = independent_volume_ratio(self.conn, SYMBOL, self.event_date)
        self.assertAlmostEqual(result, 10.0, places=9)

    def test_independent_delivery_percentile_matches_hand_computed_value(self):
        # trailing delivery_pct = 0..59 (60 distinct values); event day = 30.0
        # below = 30 (values 0..29), tied = 1 (value 30 itself), n=60
        # percentile = 100*(30 + 0.5)/60 = 50.833...
        result = independent_delivery_percentile(self.conn, SYMBOL, self.event_date)
        self.assertAlmostEqual(result, 100 * 30.5 / 60, places=9)

    def test_insufficient_history_returns_none_not_a_wrong_number(self):
        short_date = self.days[10]  # only 10 prior trading days -- far short of the 60 required
        self.assertIsNone(independent_volume_ratio(self.conn, SYMBOL, short_date))
        self.assertIsNone(independent_delivery_percentile(self.conn, SYMBOL, short_date))

    def test_unknown_symbol_returns_none(self):
        self.assertIsNone(independent_volume_ratio(self.conn, "NOSUCHSYMBOL", self.event_date))

class ValuesAgreeTest(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(values_agree(3.2, 3.2))

    def test_within_tolerance(self):
        self.assertTrue(values_agree(3.2, 3.2 + 1e-12))

    def test_outside_tolerance_disagrees(self):
        self.assertFalse(values_agree(3.2, 9.0))

    def test_both_none_agrees(self):
        self.assertTrue(values_agree(None, None))

    def test_one_none_disagrees(self):
        self.assertFalse(values_agree(3.2, None))

    def test_both_zero_agrees(self):
        self.assertTrue(values_agree(0.0, 0.0))

class SamplingRateTest(unittest.TestCase):
    def test_empirical_rate_is_approximately_20_percent(self):
        n = 5000
        sampled = sum(1 for i in range(n) if is_sampled_for_derivation(f"SYM{i}:2024-01-01:volume_ratio"))
        rate = sampled / n
        self.assertGreater(rate, 0.15)
        self.assertLess(rate, 0.25)

    def test_deterministic_across_calls(self):
        claim_id = "ANY:2024-01-01:volume_ratio"
        results = {is_sampled_for_derivation(claim_id) for _ in range(10)}
        self.assertEqual(len(results), 1)

if __name__ == "__main__":
    unittest.main()
