"""Acceptance test 5: a trade the planned-loss budget would allow is blocked by the stress-loss
budget; a split during a paper position (BAJFINANCE 2025) adjusts stop and quantity with no false
stop.
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.paper.execution import adjust_for_corporate_actions, check_stop_on_session
from desk.risk.officer import compute_stress_loss, planned_loss_inr

from tests.desk_fixtures import make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class StressLossExceedsPlannedLossTest(unittest.TestCase):
    def test_stress_loss_can_exceed_and_therefore_block_where_planned_loss_alone_would_not(self):
        """A tiny per-share stop distance keeps planned loss small, but a real historical overnight
        gap (or the rulebook floor) can still dominate stress loss -- confirms stress loss is not
        just an alias for planned loss."""
        conn = get_live_connection()
        try:
            costs = make_test_costs()
            rulebook = make_test_rulebook()
            entry, stop, quantity = 750.0, 749.5, 10  # a 0.5-rupee stop -- planned loss is tiny
            planned = planned_loss_inr(entry, stop, quantity, costs)
            result = compute_stress_loss(conn, "AXISBANK", "2021-10-27", entry, stop, quantity,
                                          costs, rulebook, stress_loss_floor_inr=1000.0)
            self.assertLess(planned, result.stress_loss_inr)
            self.assertGreaterEqual(result.stress_loss_inr, result.floor_component_inr)
        finally:
            conn.close()


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class BajfinanceSplitAdjustmentTest(unittest.TestCase):
    """The real, verified BAJFINANCE 2025 case: BONUS 4:1 + SPLIT 2:1 = 10x, ex-date 2025-06-16."""

    def test_split_scales_entry_stop_target_and_quantity_by_the_same_factor(self):
        conn = get_live_connection()
        try:
            adjusted = adjust_for_corporate_actions(
                conn, "BAJFINANCE", original_entry_date="2025-01-15",
                entry=7000.0, stop=6800.0, target=7500.0, quantity=10, as_of="2025-07-01",
            )
            self.assertEqual(adjusted.factor_applied, 10.0)
            self.assertAlmostEqual(adjusted.entry, 700.0)
            self.assertAlmostEqual(adjusted.stop, 680.0)
            self.assertAlmostEqual(adjusted.target, 750.0)
            self.assertAlmostEqual(adjusted.quantity, 100.0)
        finally:
            conn.close()

    def test_adjusted_stop_is_not_falsely_hit_by_the_post_split_price(self):
        """Before adjustment, a post-split price of ~700 looks like it blew through a pre-split
        stop of 6800 -- a false stop. After adjusting the stop by the same factor (680), the real
        post-split trading range must NOT read as a stop hit on a real post-split session."""
        conn = get_live_connection()
        try:
            adjusted = adjust_for_corporate_actions(
                conn, "BAJFINANCE", original_entry_date="2025-01-15",
                entry=7000.0, stop=6800.0, target=7500.0, quantity=10, as_of="2025-07-01",
            )
            fill = check_stop_on_session(conn, "BAJFINANCE", "2025-07-01", adjusted.stop, "2025-07-01")
            self.assertIsNone(fill, "Adjusted stop was falsely triggered by real post-split trading.")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
