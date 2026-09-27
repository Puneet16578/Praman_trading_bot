"""Confirms the COMMITTED, active cost config (config/costs_india_delivery_v1.yaml) produces the
round-trip cost the user hand-calculated against Zerodha's published charges, for a Rs 50,000
delivery trade (price=500, quantity=100, so both the buy and the sell leg turn over Rs 50,000).

The expected figure below is written out from scratch in this test -- component by component --
rather than derived by calling the function under test, so this is a real check against an
independent hand calculation, not a tautology.

Hand calculation (Rs 50,000 turnover per leg):
    STT              50,000 * 0.1%    per leg, both legs        = Rs 50.00 buy, Rs 50.00 sell
    NSE transaction  50,000 * 0.00307% per leg, both legs        = Rs 1.535 buy, Rs 1.535 sell
    SEBI fee         50,000 * 0.0001% per leg, both legs         = Rs 0.05 buy, Rs 0.05 sell
    Brokerage        Rs 0 per order (Zerodha delivery), both legs = Rs 0 buy, Rs 0 sell
    Stamp duty       50,000 * 0.015%, BUY SIDE ONLY               = Rs 7.50 buy, Rs 0 sell
    GST              18% of (brokerage + NSE + SEBI), both legs   = 18% * 1.585 = Rs 0.2853 each leg
    DP charge        Rs 15.34 flat, SELL SIDE ONLY, GST-inclusive = Rs 0 buy, Rs 15.34 sell

    Buy leg total  = 50.00 + 1.535 + 0.05 + 0 + 7.50 + 0.2853 + 0      = Rs 59.3703
    Sell leg total = 50.00 + 1.535 + 0.05 + 0 + 0    + 0.2853 + 15.34  = Rs 67.2103
    Round trip     = 59.3703 + 67.2103                                = Rs 126.5806
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.costs import VersionedConfigError, load_active_cost_config
from desk.risk.officer import round_trip_cost_inr

PRICE = 500.0
QUANTITY = 100.0  # turnover = 500 * 100 = Rs 50,000 per leg

EXPECTED_BUY_LEG = 50.00 + 1.535 + 0.05 + 0.0 + 7.50 + 0.2853 + 0.0
EXPECTED_SELL_LEG = 50.00 + 1.535 + 0.05 + 0.0 + 0.0 + 0.2853 + 15.34
EXPECTED_ROUND_TRIP = EXPECTED_BUY_LEG + EXPECTED_SELL_LEG  # Rs 126.5806


class CommittedCostConfigRoundTripTest(unittest.TestCase):
    def setUp(self):
        try:
            self.loaded = load_active_cost_config()
        except VersionedConfigError as exc:
            self.skipTest(f"Active cost config not loadable (not committed/clean yet?): {exc}")

    def test_round_trip_cost_of_a_50000_rupee_delivery_trade_matches_hand_calculation(self):
        costs = self.loaded.costs
        buy_leg = round_trip_cost_inr(PRICE, QUANTITY, costs, "buy")
        sell_leg = round_trip_cost_inr(PRICE, QUANTITY, costs, "sell")

        self.assertAlmostEqual(buy_leg, EXPECTED_BUY_LEG, places=4)
        self.assertAlmostEqual(sell_leg, EXPECTED_SELL_LEG, places=4)
        self.assertAlmostEqual(buy_leg + sell_leg, EXPECTED_ROUND_TRIP, places=4)
        self.assertAlmostEqual(buy_leg + sell_leg, 126.5806, places=4)

    def test_depository_charge_is_not_double_taxed_with_gst(self):
        """The Rs 15.34 DP charge is already GST-inclusive (CDSL Rs 3.50 + Zerodha Rs 9.50 +
        GST Rs 2.34) -- GST must be computed only on (brokerage + exchange + SEBI), never on the
        depository charge, or the sell leg would silently overcharge by 18% of Rs 15.34."""
        costs = self.loaded.costs
        sell_leg = round_trip_cost_inr(PRICE, QUANTITY, costs, "sell")
        overcharged = EXPECTED_SELL_LEG + (costs.depository_charges.rate * costs.gst.rate / 100.0)
        self.assertNotAlmostEqual(sell_leg, overcharged, places=4)

    def test_stamp_duty_is_buy_side_only_and_dp_charge_is_sell_side_only(self):
        """buy_leg carries stamp duty but not the DP charge; sell_leg is the reverse -- so the
        difference between the two legs is exactly (stamp duty - DP charge)."""
        costs = self.loaded.costs
        buy_leg = round_trip_cost_inr(PRICE, QUANTITY, costs, "buy")
        sell_leg = round_trip_cost_inr(PRICE, QUANTITY, costs, "sell")
        stamp_component = PRICE * QUANTITY * costs.stamp_duty.rate / 100.0
        dp_component = costs.depository_charges.rate
        self.assertAlmostEqual(buy_leg - sell_leg, stamp_component - dp_component, places=4)


if __name__ == "__main__":
    unittest.main()
