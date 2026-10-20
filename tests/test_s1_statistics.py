import unittest
from datetime import date, timedelta
import numpy as np

from desk.s1 import statistics as S


def calendar():
    return [(date(2024, 1, 1)+timedelta(days=i)).isoformat() for i in range(140)
            if (date(2024, 1, 1)+timedelta(days=i)).weekday() < 5]


def row(day, value=.01, group="unexplained", status="VALID"):
    return dict(day=day, net_return=value if status == "VALID" else None, group=group,
                horizon=1, status=status, filled=status in ("VALID", "MISSING"))


class StatisticsTest(unittest.TestCase):
    def test_small_comparator_does_not_invalidate_a_and_family_fixed(self):
        cal = calendar()
        rows = [row(d) for d in cal[:80] for _ in range(4)]
        rows += [row(cal[0], group="explained")]
        result = S.evaluate(rows, cal, "development", 1)
        self.assertEqual(result["a"]["state"], "PASS")
        self.assertEqual(result["b"]["state"], "INCONCLUSIVE")
        self.assertEqual(len(result["family"]), 4)
        self.assertGreaterEqual(result["a"]["usable_draws"], 1900)
        self.assertEqual(result["verdict"], "FAIL")  # only one positive development year

    def test_bootstrap_copies_not_distinct_dates(self):
        cal = calendar()[:40]
        rows = [row(cal[0])]
        weights = np.zeros((1, 40), dtype=int)
        weights[0, 0] = 200
        _, usable, reasons = S.group_draws(rows, cal, weights)
        self.assertFalse(usable[0])
        self.assertEqual(reasons["distinct_dates_below_30"], 1)
        self.assertEqual(reasons["valid_trades_below_100"], 0)

    def test_missing_denominator_and_censored_not_missing(self):
        cal = calendar()[:40]
        rows = [row(cal[i % 40]) for i in range(190)] + [row(cal[0], status="MISSING") for _ in range(10)]
        rows += [row(cal[0], status="CENSORED") for _ in range(100)]
        stats = S.describe(rows)
        self.assertEqual((stats["filled_denominator"], stats["missing_rate"]), (200, .05))
        _, usable, _ = S.group_draws(rows, cal, np.ones((1, 40), dtype=int))
        self.assertTrue(usable[0])
        rows.append(row(cal[0], status="MISSING"))
        _, usable, _ = S.group_draws(rows, cal, np.ones((1, 40), dtype=int))
        self.assertFalse(usable[0])

    def test_usable_draw_floor_is_test_specific(self):
        from unittest.mock import patch
        cal = calendar()
        rows = [row(d) for d in cal[:80] for _ in range(4)]
        means, usable = np.full(2000, .01), np.arange(2000) < 1899
        with patch.object(S, "group_draws", return_value=(means, usable, {})):
            result = S.evaluate(rows, cal, "development", 1)
        self.assertEqual(result["a"]["state"], "INCONCLUSIVE")

    def test_zero_and_low_count_years_and_halfyears(self):
        rows = [row(f"{year}-01-02", 0) for year in range(2021, 2025) for _ in range(30)]
        self.assertEqual(S.consistency(rows, "development")["state"], "FAIL")
        rows = [row("2025-01-02") for _ in range(30)]+[row("2025-07-02") for _ in range(29)]
        self.assertEqual(S.consistency(rows, "2025")["state"], "INCONCLUSIVE")

    def test_percentile_type7_and_undefined_ratios(self):
        out = S.intervals(np.array([0., 1., 2.]), np.ones(3, dtype=bool))
        self.assertAlmostEqual(out["family_interval"][0], .0125)
        self.assertEqual(S.describe([row("2024-01-01")])["profit_factor"], "undefined")

    def test_calendar_keeps_empty_dates_and_purges_scheduled_boundary(self):
        cal = ["2024-12-26", "2024-12-27", "2024-12-30", "2024-12-31", "2025-01-01"]
        self.assertEqual(S.period_calendar(cal, "development", 1), cal[:2])
        with self.assertRaises(ValueError):
            S.period_calendar(cal, "development", 5)
