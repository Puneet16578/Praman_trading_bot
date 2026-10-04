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
from desk.risk.officer import compute_position_size, compute_stress_loss, planned_loss_inr

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
            result = compute_stress_loss(conn, "AXISBANK", "2021-10-27", entry, stop, quantity, costs, rulebook)
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


class WholeShareSizingTest(unittest.TestCase):
    """Fix 1 (post-STOP-3 review): NSE trades in whole shares -- compute_position_size is a pure
    function (no store access), so this exercises the flooring directly rather than through a full
    real-data assessment (test_desk_states_real_data.py covers the end-to-end VETO case)."""

    def test_fractional_raw_size_floors_down_not_rounds(self):
        rulebook = make_test_rulebook()
        # entry=750, stop=700 -> per_share_risk=50; stock cap (10% of Rs 500,000 / 750) = 66.6667,
        # the binding cap here -- must floor to 66, never round to 67.
        size = compute_position_size(750.0, 700.0, rulebook, open_risk_used_inr=0.0,
                                      capital_at_stock_inr=0.0, capital_at_sector_inr=0.0)
        self.assertEqual(size, 66.0)

    def test_a_single_share_exceeding_the_tightest_cap_floors_to_zero_not_negative(self):
        rulebook = make_test_rulebook()
        # entry=60000, stop=59000 -> one share (Rs 60,000) alone exceeds the per-stock cap
        # (10% of Rs 500,000 = Rs 50,000) -- must floor to 0, never negative, never round up.
        size = compute_position_size(60000.0, 59000.0, rulebook, open_risk_used_inr=0.0,
                                      capital_at_stock_inr=0.0, capital_at_sector_inr=0.0)
        self.assertEqual(size, 0.0)


if __name__ == "__main__":
    unittest.main()

@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class StressLossScaleBugTest(unittest.TestCase):
    def test_bajfinance_overnight_gap_stress_loss_uses_current_price_scale(self):
        """P8-024: BAJFINANCE on 2025-06-18 has a cumulative factor of 10. The risk must be 
        calculated using the unscaled decision-date close (e.g. 919), not the normalized 9,190."""
        from src.bitemporal.guard import latest_as_of
        from src.signals.price_adjustment import compute_adjustment_factor
        from desk.risk.officer import worst_overnight_gap_loss_inr
        
        conn = get_live_connection()
        try:
            symbol, day = "BAJFINANCE", "2025-06-18"
            rows = sorted((r for r in latest_as_of(conn, "bhavcopy", day, symbol=symbol, series="EQ")
                           if r["event_date"] <= day), key=lambda r: r["event_date"])[-21:]
            factors = [compute_adjustment_factor(conn, symbol, r["event_date"], day) for r in rows]
            gaps = [(rows[i]["open_price"]/factors[i]) / (rows[i-1]["close_price"]/factors[i-1])-1
                    for i in range(1, len(rows))]
            expected = abs(min(0, *gaps)) * rows[-1]["close_price"] * 10
            self.assertGreater(expected, 0)
            self.assertAlmostEqual(worst_overnight_gap_loss_inr(conn, symbol, day, 10, 20), expected)
        finally:
            conn.close()

    def test_stress_loss_is_invariant_to_synthetic_splits(self):
        """A stock's stress loss is the same whether or not it has historical splits."""
        from unittest.mock import patch
        from desk.risk.officer import worst_overnight_gap_loss_inr
        
        conn = get_live_connection()
        try:
            symbol, day = "AXISBANK", "2021-10-27"
            base_loss = worst_overnight_gap_loss_inr(conn, symbol, day, 10, 20)
            
            # Synthetic 2:1 split 5 days ago
            original_factor = __import__("src.signals.price_adjustment", fromlist=["compute_adjustment_factor"]).compute_adjustment_factor
            original_adj_close = __import__("src.signals.price_adjustment", fromlist=["adjusted_close"]).adjusted_close
            
            def mock_factor(conn, sym, ev_date, as_of):
                f = original_factor(conn, sym, ev_date, as_of)
                # If event date is before 2021-10-20, apply 2.0 factor
                return f * (2.0 if ev_date < "2021-10-20" else 1.0)
                
            def mock_adj_close(conn, sym, ev_date, as_of):
                c = original_adj_close(conn, sym, ev_date, as_of)
                # If event date is before 2021-10-20, price would be halved in adjusted terms
                return c / (2.0 if ev_date < "2021-10-20" else 1.0)

            with patch("desk.risk.officer.compute_adjustment_factor", side_effect=mock_factor), \
                 patch("desk.risk.officer.adjusted_close", side_effect=mock_adj_close):
                 
                synthetic_loss = worst_overnight_gap_loss_inr(conn, symbol, day, 10, 20)
                self.assertAlmostEqual(base_loss, synthetic_loss)
        finally:
            conn.close()

