"""Follow-up 3 (preregistered b2df2a2): limit-price sizing, synthetic checks before the real run."""
import itertools
import unittest

from desk.risk.officer import compute_position_size, planned_loss_inr
from desk.shadow_followup2 import limit_fill
from desk.shadow_followup3 import ProtocolViolation, analyze, prepare, verdict
from tests.desk_fixtures import make_test_costs, make_test_rulebook

RB, COSTS = make_test_rulebook(), make_test_costs()
CAP = RB.risk.capital_allocated_inr * RB.risk.risk_per_trade_pct / 100


def plan(price=100.0, atr=4.0, multiple=2.0):
    stop = price - multiple * atr
    return dict(decision_price=price, atr20=atr, stop_level=stop,
                quantity=int(compute_position_size(price, stop, RB, 0, 0, 0, costs=COSTS)), adv_turnover=1e10,
                stress=dict(floor_component_inr=1.0, worst_gap_component_inr=None, locked_circuit_loss_inr=None))


def record(day, p, symbol='X'):
    return dict(symbol=symbol, event_date=day, state='SCREEN_PASS', plan=p)


def evidence(day, p, opening, low, symbol='X'):
    return dict(symbol=symbol, event_date=day, limit=limit_fill(p, opening, low))


class PrepareTest(unittest.TestCase):
    def test_parity_and_limit_sizing_is_smaller(self):
        # Per-trade budget binds (ATR20 8% of price): risk per share 2 vs 2.5 ATR, ratio near 0.8.
        p = plan(atr=8.0)
        row = prepare([record('2020-01-02', p)], [evidence('2020-01-02', p, 101, 99)], RB, COSTS)[0]
        self.assertAlmostEqual(row['limit_quantity'] / row['quantity'], 0.8, delta=0.02)
        # Per-stock cap binds (ATR20 4%): position value at the limit, ratio near 100 / 102.
        p4 = plan()
        row4 = prepare([record('2020-01-02', p4)], [evidence('2020-01-02', p4, 101, 99)], RB, COSTS)[0]
        self.assertAlmostEqual(row4['limit_quantity'] / row4['quantity'], 100 / 102, delta=0.01)
        bad = dict(p, quantity=p['quantity'] + 1)
        with self.assertRaises(ProtocolViolation):
            prepare([record('2020-01-02', bad)], [evidence('2020-01-02', bad, 101, 99)], RB, COSTS)

    def test_limit_must_match_follow_up_2_and_evidence_must_exist(self):
        p = plan()
        wrong = dict(symbol='X', event_date='2020-01-02', limit=dict(limit=999.0, fill=None, status='NO_FILL', reason=''))
        with self.assertRaises(ProtocolViolation):
            prepare([record('2020-01-02', p)], [wrong], RB, COSTS)
        with self.assertRaises(ProtocolViolation):
            prepare([record('2020-01-02', p)], [], RB, COSTS)

    def test_breach_at_fill_impossible_by_construction(self):
        for price, atr in itertools.product((5.0, 37.5, 100.0, 812.4, 4000.0), (0.1, 1.3, 4.0, 22.0)):
            if price - 2 * atr <= 0:
                continue
            p = plan(price, atr)
            limit = price + 0.5 * atr
            q = int(compute_position_size(limit, p['stop_level'], RB, 0, 0, 0, costs=COSTS))
            for fill in (limit, limit * 0.999, price, p['stop_level'] + 0.01, p['stop_level'], p['stop_level'] * 0.7):
                self.assertLessEqual(planned_loss_inr(fill, min(p['stop_level'], fill), q, COSTS), CAP + 1e-9,
                                     (price, atr, fill))

    def test_forward_event_rejected_before_reading(self):
        from datetime import date
        from unittest.mock import patch
        from desk.outcome_firewall import ForwardOutcomeBlocked
        with patch('desk.outcome_firewall.market_today', return_value=date(2026, 10, 4)), \
             self.assertRaises(ForwardOutcomeBlocked):
            prepare([record('2026-09-16', plan())], [], RB, COSTS)


class AnalyzeTest(unittest.TestCase):
    def rows(self, cases):
        out = []
        for i, (p, opening, low) in enumerate(cases):
            day = f'2020-01-{i + 2:02d}'
            out += prepare([record(day, p, f'S{i}')], [evidence(day, p, opening, low, f'S{i}')], RB, COSTS)
        return out

    def test_counts_abstentions_unknowns_and_fills(self):
        # Price 10,000, ATR20 2,200: one share risks ~4,400 at the decision price (within the
        # 5,000 budget) but ~5,500 at the 11,100 limit, so limit sizing abstains.
        abstain = plan(price=10000.0, atr=2200.0)
        rows = self.rows([(plan(), 101, 99), (plan(), 110, 105), (plan(), None, None), (abstain, 10050, 9900)])
        self.assertEqual((rows[3]['quantity'], rows[3]['limit_quantity']), (1, 0))
        result = analyze(rows, RB, COSTS, replicates=50)
        self.assertEqual(result['unknown_execution_inputs'], 1)
        self.assertEqual(result['follow_up_2_limit_fills'], 2)      # rows 0 and 3 fill under frozen sizing
        self.assertEqual(result['variant_fills'], 1)                 # row 3 abstains: no order
        self.assertEqual(result['abstentions'], 1)
        self.assertEqual(result['per_trade_breaches_at_fill'], 0)

    def test_shared_date_draws_make_identical_rates_differ_by_exactly_zero(self):
        rows = self.rows([(plan(), 101, 99), (plan(), 110, 105), (plan(), 101, 100), (plan(), 120, 119)])
        result = analyze(rows, RB, COSTS, replicates=200)
        self.assertEqual(result['fill_rate_difference']['estimate'], 0)
        self.assertEqual(result['fill_rate_difference']['interval95'], [0.0, 0.0])
        self.assertEqual(result['fill_rate']['estimate'], 0.5)       # 101 and 101 open under the 102 limit

    def test_verdict_rules(self):
        rows = self.rows([(plan(), 101, 99), (plan(), 101, 100)])
        good = dict(periods={'Primary 2019-2025': analyze(rows, RB, COSTS, replicates=20),
                             'Descriptive 2026': analyze(rows, RB, COSTS, replicates=20)})
        self.assertTrue(verdict(good)['passed'])
        bad = dict(periods={k: dict(v, per_trade_breaches_at_fill=1) for k, v in good['periods'].items()})
        self.assertFalse(verdict(bad)['P1_zero_per_trade_breaches_at_fill'])
        low = dict(periods={k: dict(v, fill_rate=dict(estimate=0.59)) for k, v in good['periods'].items()})
        self.assertFalse(verdict(low)['P2_primary_fill_rate_at_least_60pct'])


if __name__ == '__main__':
    unittest.main()
