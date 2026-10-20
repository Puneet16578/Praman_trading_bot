import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from desk.s1.reader import Bar, RealReader, OutcomeReadRefused, seal_real_reads, dividend_record_evidence
from desk.s1.execution import trade, run, path_label, benchmark
from desk.lib.costs import load_active_cost_config


def dates():
    return [(date(2024, 1, 1)+timedelta(days=i)).isoformat() for i in range(40)
            if (date(2024, 1, 1)+timedelta(days=i)).weekday() < 5]


def record(day=None, entry=None, scheduled=None, symbol="A"):
    c = dates()
    return dict(day=day or c[0], symbol=symbol, turnover_band=1, zscore_60d=-4.,
        entry_session=entry or c[1], scheduled_exits={"1": scheduled or c[2], "3": scheduled or c[4]},
        plan=dict(decision_price=100., atr20=5., stop_level=90., quantity=10, limit=102.5, limit_cap=None),
        exclusions={"unexplained": [], "explained": ["no_material"]})


class FakeReader:
    def __init__(self, bars, forbidden=()):
        self.bars, self.forbidden, self.calls = bars, forbidden, []
    def bar(self, event, symbol, day):
        if day in self.forbidden:
            raise AssertionError("Forbidden price requested")
        self.calls.append(day)
        return self.bars.get((symbol, day), self.bars.get(day))
    def market_members(self, event):
        return ["M", "MISSING"]
    def market_states(self, event, symbol):
        return dict(V1=False, V2=False, V3=True)
    def benchmark_open(self, event, symbol, day, fill):
        return None if symbol == "MISSING" else (100 if day == fill else 101)


class ExecutionTest(unittest.TestCase):
    def setUp(self):
        self.c = dates()
        self.costs = load_active_cost_config().costs
        self.bars = {d: Bar(100, 104, 99, 102) for d in self.c}

    def test_no_stop_on_fill_and_mae_never_uses_exit_day_low(self):
        self.bars[self.c[1]] = Bar(100, 110, 80, 100)
        self.bars[self.c[2]] = Bar(101, 105, 1, 100)
        reader = FakeReader(self.bars, forbidden=self.c[3:])
        result = trade(record(), 1, self.c, reader, self.costs)
        self.assertEqual(result["reason"], "TIME")
        self.assertAlmostEqual(result["mae"], .2)
        self.assertEqual(reader.calls, self.c[1:3])

    def test_blocked_stop_stays_pending_when_price_recovers(self):
        self.bars[self.c[2]] = Bar(85, 85, 85, 85, blocks_sell=True)
        self.bars[self.c[3]] = Bar(105, 106, 104, 105)
        result = trade(record(), 3, self.c, FakeReader(self.bars), self.costs)
        self.assertEqual((result["reason"], result["exit_price"], result["closed_on"]), ("STOP", 105, self.c[3]))
        self.assertEqual(result["circuit_delays"], [self.c[2]])

    def test_time_stop_priority_uses_only_open(self):
        self.bars[self.c[2]] = Bar(89, 110, 88, 100)
        result = trade(record(), 1, self.c, FakeReader(self.bars), self.costs)
        self.assertEqual(result["reason"], "STOP")
        self.assertTrue(result["gap_through_stop"])

    def test_limit_and_fill_failure_and_locks(self):
        self.bars[self.c[1]] = Bar(110, 112, 103, 111)
        self.assertEqual(trade(record(), 1, self.c, FakeReader(self.bars), self.costs)["status"], "NO_FILL")
        self.bars[self.c[1]] = None
        self.assertEqual(trade(record(), 1, self.c, FakeReader(self.bars), self.costs)["status"], "FILL_FAILURE")
        self.bars[self.c[1]] = Bar(100, 100, 100, 100, blocks_buy=True)
        self.assertEqual(trade(record(), 1, self.c, FakeReader(self.bars), self.costs)["status"], "NO_FILL")

    def test_missing_cap_no_later_price_and_unadjustable_closes(self):
        reader = FakeReader({self.c[1]: self.bars[self.c[1]]}, forbidden=self.c[13:])
        result = trade(record(), 1, self.c, reader, self.costs)
        self.assertEqual((result["status"], result["closed_on"]), ("MISSING", self.c[12]))
        self.bars[self.c[2]] = Bar(0, 0, 0, 0, unadjustable=True)
        result = trade(record(), 3, self.c, FakeReader(self.bars), self.costs)
        self.assertEqual((result["status"], result["closed_on"]), ("MISSING", self.c[2]))

    def test_interior_missing_resumes_open_first(self):
        self.bars[self.c[2]] = None
        self.bars[self.c[3]] = Bar(80, 100, 75, 90)
        result = trade(record(), 3, self.c, FakeReader(self.bars), self.costs)
        self.assertEqual(result["exit_price"], 80)

    def test_boundary_does_not_query_next_period(self):
        c = ["2024-12-27", "2024-12-30", "2024-12-31", "2025-01-01"]
        r = record(day=c[0], entry=c[1], scheduled=c[2])
        reader = FakeReader({c[1]: Bar(100, 102, 99, 101), c[2]: Bar(80, 80, 80, 80, blocks_sell=True)}, [c[3]])
        result = trade(r, 1, c, reader, self.costs)
        self.assertEqual(result["status"], "CENSORED")
        r["scheduled_exits"]["1"] = c[3]
        reader.calls.clear()
        self.assertEqual(trade(r, 1, c, reader, self.costs)["status"], "CENSORED")
        self.assertEqual(reader.calls, [])

    def test_path_stop_first_both_touch_and_scheduled_open_only(self):
        self.bars[self.c[2]] = Bar(100, 112, 89, 100)
        reader = FakeReader(self.bars)
        result = trade(record(), 3, self.c, reader, self.costs)
        self.assertEqual(path_label(result, self.c, reader)["label"], "STOP")
        result["scheduled_exit"] = self.c[2]
        self.assertEqual(path_label(result, self.c, reader)["label"], "TIMEOUT")

    def test_real_guard_precedes_any_database_operation_and_captured_alias(self):
        conn = Mock()
        reader = RealReader(conn, conn, "2025-12-31", authorized=True)
        with self.assertRaises(OutcomeReadRefused):
            reader.bar("2025-12-30", "A", "2026-01-01")
        alias = reader.bar
        with seal_real_reads(), self.assertRaises(OutcomeReadRefused):
            alias("2025-01-01", "A", "2025-01-02")
        conn.execute.assert_not_called()
        with self.assertRaises(OutcomeReadRefused):
            RealReader(conn, conn, "2024-12-31").market_members("2024-01-01")

    def test_actual_occupancy_early_exit_and_separate_groups_horizons(self):
        a, b = record(), record(day=self.c[2], entry=self.c[3], scheduled=self.c[4])
        a["exclusions"]["explained"] = []
        b["exclusions"]["explained"] = []
        result = run([b, a], self.c, FakeReader(self.bars), self.costs)
        self.assertEqual(sum(r["status"] == "POSITION_SKIPPED" for r in result), 2)
        # An early stop frees the stock by the decision on c[2].
        self.bars[self.c[2]] = Bar(89, 100, 85, 95)
        result = run([b, a], self.c, FakeReader(self.bars), self.costs)
        self.assertFalse(any(r["status"] == "POSITION_SKIPPED" for r in result))

    def test_costs_slippage_once_and_benchmark_endpoint_coverage(self):
        result = trade(record(), 1, self.c, FakeReader(self.bars), self.costs)
        self.assertAlmostEqual(result["slipped_exit"], 99.85)
        self.assertAlmostEqual(result["net_return"], -.0015-result["costs_inr"]/1000)
        b = benchmark(result, FakeReader(self.bars))
        self.assertEqual((b["members"], b["missing"]), (2, 1))
        self.assertAlmostEqual(b["relative"], result["net_return"]-.01)

    def test_fixed_horizons(self):
        with self.assertRaises(ValueError):
            trade(record(), 5, self.c, FakeReader(self.bars), self.costs)

    def test_absent_dividend_source_is_unknown_and_parser_is_unchanged(self):
        self.assertIsNone(dividend_record_evidence([], self.c[1], self.c))
        row = dict(category="Dividend", description="Dividend record date 02-Jan-2024",
                   sort_timestamp="2024-01-01 16:00:00", knowledge_date="2024-01-01")
        self.assertTrue(dividend_record_evidence([row], "2024-01-02", self.c))
        result = trade(record(), 1, self.c, FakeReader(self.bars), self.costs)
        self.assertEqual(result["dividend_unknown_sessions"], self.c[1:3])
