"""Real-price ATR proof and adversarial decision/execution separation checks."""
import copy
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desk.lib.store import get_live_connection
from desk.screening_plan import decision_plan, execution_observation, screen_event
from desk.outcome_firewall import evaluate_event, ForwardOutcomeBlocked
from src.bitemporal.guard import latest_as_of
from src.signals.price_adjustment import compute_adjustment_factor
from desk.lib.connection import get_desk_connection
from tests.desk_fixtures import make_test_costs, make_test_rulebook
from desk.opportunity_store import append_opportunity, append_execution
from desk.risk.officer import worst_overnight_gap_loss_inr


class ScreeningPlanTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_live_connection()
        self.addCleanup(self.conn.close)
        self.desk = get_desk_connection(":memory:")
        self.addCleanup(self.desk.close)
        self.rb, self.costs = make_test_rulebook(), make_test_costs()

    def test_atr_uses_adjusted_ohlc_across_real_split_and_bonus(self):
        symbol, day = "BAJFINANCE", "2025-06-18"
        rows = sorted((r for r in latest_as_of(self.conn, "bhavcopy", day, symbol=symbol, series="EQ")
                       if r["event_date"] <= day), key=lambda r: r["event_date"])[-21:]
        scaled = [{k: r[k] / compute_adjustment_factor(self.conn, symbol, r["event_date"], day)
                   for k in ("high_price", "low_price", "close_price")} for r in rows]
        ranges = [max(scaled[i]["high_price"], scaled[i-1]["close_price"])
                  - min(scaled[i]["low_price"], scaled[i-1]["close_price"]) for i in range(1, 21)]
        expected = sum(ranges)/20
        actual = decision_plan(self.conn, symbol, day)
        self.assertAlmostEqual(actual["atr20"], expected)
        self.assertAlmostEqual(actual["stop_level"], rows[-1]["close_price"]-2*expected)
        # The forbidden previous-close source must have no influence at all.
        poisoned = copy.deepcopy(rows)
        for row in poisoned:
            row["raw_prev_close_unadjusted"] = 1e12
        with patch("desk.screening_plan.latest_as_of", return_value=poisoned):
            self.assertEqual(actual, decision_plan(self.conn, symbol, day))
        self.assertTrue(any(compute_adjustment_factor(self.conn, symbol, r["event_date"], day) != 1 for r in rows))


    def test_next_open_cannot_change_frozen_decision(self):
        plan, result = screen_event(self.conn, self.desk, "AXISBANK", "2021-10-27", self.rb, self.costs)
        before = copy.deepcopy(plan)
        execution = execution_observation(self.conn, "AXISBANK", "2021-10-27", "2021-10-28", plan, self.rb, self.costs)
        raw = latest_as_of(self.conn, "bhavcopy", "2021-10-28", symbol="AXISBANK", event_date="2021-10-28", series="EQ")[0]
        self.assertEqual(execution["fill"], raw["open_price"])
        self.assertEqual(execution["quantity"], plan["quantity"])
        self.assertEqual(plan, before)
        self.assertAlmostEqual(execution["gap_inr"], raw["open_price"]-plan["decision_price"])
        self.assertEqual(result.gate_results["G7"].result, "NOT_APPLICABLE")
        self.assertEqual(result.gate_results["G8"].result, "NOT_APPLICABLE")
        self.assertEqual(set(result.gate_results), {f"G{i}" for i in range(1, 9)})

    def test_missing_next_session_is_pending_and_missing_security_is_no_fill(self):
        plan, _ = screen_event(self.conn, self.desk, "AXISBANK", "2021-10-27", self.rb, self.costs)
        self.assertIsNone(execution_observation(self.conn, "AXISBANK", "2021-10-27", "2021-10-27", plan, self.rb, self.costs))
        with patch("desk.screening_plan.latest_as_of", return_value=[]):
            result = execution_observation(self.conn, "AXISBANK", "2021-10-27", "2021-10-28", plan, self.rb, self.costs)
        self.assertEqual(result["status"], "NO_FILL")
        self.assertIn("cause unverified", result["reason"])

    def test_gap_through_and_cap_breach_do_not_resize(self):
        plan, _ = screen_event(self.conn, self.desk, "AXISBANK", "2021-10-27", self.rb, self.costs)
        for opening in (plan["stop_level"] / 2, plan["decision_price"] * 10):
            with self.subTest(opening=opening), patch("desk.screening_plan.latest_as_of", return_value=[{"series": "EQ", "open_price": opening}]):
                result = execution_observation(self.conn, "AXISBANK", "2021-10-27", "2021-10-28", plan, self.rb, self.costs)
                self.assertEqual(result["quantity"], plan["quantity"])
                self.assertEqual(result["immediate_gap_through"], opening <= plan["stop_level"])
                if opening > plan["decision_price"]:
                    self.assertTrue(result["cap_breaches"])

    def test_append_records_and_replay_without_mutating_decision(self):
        plan, assessment = screen_event(self.conn, self.desk, "AXISBANK", "2021-10-27", self.rb, self.costs)
        provenance = {key: "fixture" for key in ("code_commit", "praman_watermark", "desk_watermark", "rulebook_hash", "cost_config_hash")}
        args = dict(symbol="AXISBANK", event_date="2021-10-27", plan=plan, assessment=assessment, provenance=provenance)
        identity, inserted = append_opportunity(self.desk, **args)
        self.assertTrue(inserted)
        self.assertEqual(append_opportunity(self.desk, **args), (identity, False))
        before = dict(self.desk.execute("SELECT * FROM opportunity_log").fetchone())
        observation = execution_observation(self.conn, "AXISBANK", "2021-10-27", "2021-10-28", plan, self.rb, self.costs)
        self.assertTrue(append_execution(self.desk, identity, observation))
        self.assertFalse(append_execution(self.desk, identity, observation))
        self.assertEqual(before, dict(self.desk.execute("SELECT * FROM opportunity_log").fetchone()))
        altered = copy.deepcopy(plan)
        altered["quantity"] += 1
        with self.assertRaises(ValueError):
            append_opportunity(self.desk, **(args | {"plan": altered}))

    def test_opportunity_table_has_only_declared_input_and_provenance_columns(self):
        columns = {row["name"] for row in self.desk.execute("PRAGMA table_info(opportunity_log)")}
        self.assertEqual(columns, {"opportunity_id", "symbol", "event_date", "knowledge_date", "recorded_at",
                                  "inputs", "evidence_bundle_hash", "gate_results", "state", "reasons", "content_hash",
                                  "code_commit", "praman_watermark", "desk_watermark", "rulebook_hash", "cost_config_hash"})


class OutcomeFirewallTest(unittest.TestCase):
    def test_refuses_before_any_outcome_loader_is_called(self):
        callback = Mock()
        with patch("desk.outcome_firewall.market_today", return_value=date(2027, 5, 31)):
            for day in ("2026-09-16", "2027-01-01"):
                with self.assertRaises(ForwardOutcomeBlocked):
                    evaluate_event(day, callback)
        callback.assert_not_called()

    def test_boundary_and_historical_access(self):
        callback = Mock(return_value="loaded")
        with patch("desk.outcome_firewall.market_today", return_value=date(2027, 6, 1)):
            self.assertEqual(evaluate_event("2026-09-16", callback), "loaded")
        with patch("desk.outcome_firewall.market_today", return_value=date(2026, 10, 1)):
            self.assertEqual(evaluate_event("2026-09-15", callback), "loaded")
