"""Flip attribution in the G6 old/new comparison audit."""
import unittest

from scripts.desk_g6_comparison import flip_attribution
from tests.desk_fixtures import make_test_rulebook, make_test_costs


def record(state, quantity, gates):
    plan = dict(decision_price=100, stop_level=90, quantity=quantity, adv_turnover=1e9,
                stress=dict(floor_component_inr=100, worst_gap_component_inr=None, locked_circuit_loss_inr=None))
    return dict(symbol='EXAMPLE', event_date='2020-01-02', state=state, plan=plan, gates=gates)


class FlipAttributionTest(unittest.TestCase):
    def test_reports_changed_gates_and_caps_at_each_quantity(self):
        rb, costs = make_test_rulebook(), make_test_costs()
        old = record('SCREEN_FAIL', 500, dict(G5=dict(result='PASS', reasons=[]),
                                              G6=dict(result='FAIL', reasons=['per-trade'])))
        new = record('SCREEN_PASS', 400, dict(G5=dict(result='PASS', reasons=[]),
                                              G6=dict(result='PASS', reasons=[])))
        flip = flip_attribution(old, new, rb, costs)
        self.assertEqual(flip['direction'], 'SCREEN_FAIL -> SCREEN_PASS')
        self.assertEqual(flip['changed_gates'], ['G6'])
        self.assertIn('per_trade', flip['old_caps_over'])
        self.assertEqual(flip['new_caps_over'], [])
        self.assertEqual(flip['old_reasons'], {'G6': ['per-trade']})
        self.assertEqual((flip['old_quantity'], flip['new_quantity']), (500, 400))

    def test_unmeasurable_plan_is_labelled_not_dropped(self):
        rb, costs = make_test_rulebook(), make_test_costs()
        old = record('SCREEN_PASS', 0, dict(G6=dict(result='PASS', reasons=[])))
        new = record('SCREEN_FAIL', 0, dict(G6=dict(result='FAIL', reasons=['x'])))
        flip = flip_attribution(old, new, rb, costs)
        self.assertTrue(flip['old_caps_over'][0].startswith('unmeasurable'))


if __name__ == '__main__':
    unittest.main()
