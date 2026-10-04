"""Decision-time cap regression: real gate orchestration and independent budgets."""
import tempfile
import unittest
from pathlib import Path

from desk.gates.checks import g6_risk
from desk.gates.engine import run_assessment, _average_daily_volume_and_turnover
from desk.lib.connection import get_desk_connection
from desk.lib.store import get_live_connection
from desk.risk.officer import compute_position_size, planned_loss_inr
from desk.screening_plan import screen_event
from desk.shadow_followup import cap_measurements
from tests.desk_fixtures import make_test_rulebook, make_test_costs, COMPLETE_AXISBANK_THESIS


class DecisionCapsTest(unittest.TestCase):
    def test_g6_independently_rejects_cost_inclusive_excess(self):
        rb, costs = make_test_rulebook(), make_test_costs()
        loss = planned_loss_inr(100, 90, 500, costs)
        self.assertGreater(loss, 5000)
        self.assertEqual(g6_risk(loss, loss, 0, 50000, 50000, rb).result, 'FAIL')
        self.assertEqual(g6_risk(5000, 5000, 0, 50000, 50000, rb).result, 'PASS')

    def test_size_respects_costs_and_is_maximal(self):
        rb, costs = make_test_rulebook(), make_test_costs()
        for entry, stop in [(100, 90), (100, 99.99), (1, .5), (10000, 5000)]:
            for used in (0, 24000, 24990):
                q = compute_position_size(entry, stop, rb, used, 0, 0, costs=costs)
                cap = min(5000, 25000-used)
                if q:
                    self.assertLessEqual(planned_loss_inr(entry, stop, q, costs), cap)
                self.assertTrue(planned_loss_inr(entry, stop, q+1, costs) > cap
                                or (q+1)*entry > 50000)

    def test_real_screen_and_assess_passes_obey_all_six_caps(self):
        rb, costs = make_test_rulebook(), make_test_costs()
        with tempfile.TemporaryDirectory() as temp:
            desk = get_desk_connection(Path(temp)/'desk.sqlite')
            conn = get_live_connection()
            try:
                passes = 0
                for day in ('2021-10-27', '2023-01-27', '2025-01-27'):
                    plan, result = screen_event(conn, desk, 'AXISBANK', day, rb, costs)
                    if result.state == 'SCREEN_PASS':
                        passes += 1
                        for key, value in cap_measurements(plan, plan['decision_price'], plan['quantity'], rb, costs).items():
                            self.assertLessEqual(value['usage'], value['cap'], key)
                self.assertGreater(passes, 0)
                # Risk cap binds here, reproducing the original cost-sizing defect.
                thesis = dict(COMPLETE_AXISBANK_THESIS, planned_entry=100, planned_stop=90)
                result = run_assessment(conn, desk, symbol='AXISBANK', as_of_date='2021-10-27',
                    sector='Financials', thesis=thesis, rulebook=rb, costs=costs)
                self.assertEqual(result.state, 'ELIGIBLE')
                from dataclasses import asdict
                _, adv = _average_daily_volume_and_turnover(conn, 'AXISBANK', '2021-10-27', 60)
                plan = dict(decision_price=100, stop_level=90, quantity=int(result.position_size),
                            stress=asdict(result.stress_loss), adv_turnover=adv)
                for key, value in cap_measurements(plan, 100, int(result.position_size), rb, costs).items():
                    self.assertLessEqual(value['usage'], value['cap'], key)
            finally:
                conn.close()
                desk.close()
