"""Synthetic checks for the registered controls, cap headroom and uncertainty."""
import copy
from datetime import date
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.outcome_firewall import ForwardOutcomeBlocked
from desk.screening_plan import execution_observation
from desk.shadow_followup import (CAPS, DateBootstrap, assert_original_flags,
    buffered_quantity, cap_analysis, cap_measurements, check_event,
    quintile_boundaries, repeated_quantiles, volatility_analysis)
from desk.shadow_followup_report import report_markdown
from scripts.desk_shadow_followup import load_records


def row(day='2021-01-01', passed=True, atr=1., outcome=False):
    return dict(symbol='TEST', event_date=day, state='SCREEN_PASS' if passed else 'SCREEN_FAIL',
                plan=dict(atr20=atr, decision_price=100.), adverse20=outcome, fill=100.)


class FollowupStatisticsTest(unittest.TestCase):
    def test_runner_load_refuses_forward_record_before_selecting_outcomes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'records.jsonl'
            # No outcome fields: the firewall must reject before their lookup.
            path.write_text('{"event_date":"2026-09-17","state":"SCREEN_PASS"}\n', encoding='utf-8')
            with patch('desk.outcome_firewall.market_today', return_value=date(2026, 10, 4)):
                with self.assertRaises(ForwardOutcomeBlocked):
                    load_records(path)

    def test_empty_groups_render_as_unavailable_not_zero(self):
        result = dict(boundaries_pct=[1, 2, 3, 4], provenance={}, periods={
            'Empty synthetic period': dict(n=0, missing90=0,
                volatility={'All candidates':volatility_analysis([], np.arange(1, 5), replicates=10)},
                caps=cap_analysis([], None, None, replicates=10))})
        rendered = report_markdown(result)
        self.assertIn('unavailable', rendered)
        self.assertIn('variant abstentions 0', rendered)
        self.assertNotRegex(rendered, r'(?i)\bnan\b')

    def test_repeated_quantiles_equal_explicit_resampled_multiset(self):
        values = np.array([-2., 0., 3., 7., 100.])
        for counts in ([0, 2, 1, 0, 1], [1, 0, 0, 0, 0], [3, 1, 4, 2, 8]):
            expected = np.quantile(np.repeat(values, counts), [.5, .9])
            np.testing.assert_allclose(repeated_quantiles(values, counts), expected)
        self.assertTrue(np.isnan(repeated_quantiles(values, [0] * 5)).all())

    def test_primary_boundaries_ignore_descriptive_extremes_and_ties_stay_together(self):
        rows = [row(atr=2.) for _ in range(10)] + [row('2026-01-02', atr=999.)]
        bounds = quintile_boundaries(rows)
        np.testing.assert_equal(bounds, [2.] * 4)
        report = volatility_analysis(rows[:10], bounds, replicates=20)
        self.assertEqual([q['pass_candidates'] for q in report['quintiles']], [0, 0, 0, 0, 10])
        self.assertIsNone(report['standardized']['estimate'])

    def test_missing_volatility_and_outcomes_have_explicit_denominators(self):
        rows = [row(atr=1., outcome=True), row(passed=False, atr=1., outcome=None),
                row(atr=None, outcome=False)]
        result = volatility_analysis(rows, np.array([2., 3., 4., 5.]), replicates=20)
        self.assertEqual(result['missing_volatility']['SCREEN_PASS']['n'], 1)
        q = result['quintiles'][0]
        self.assertEqual(q['passed']['n_events'], 1)
        self.assertEqual(q['fail_missing'], 1)
        self.assertIsNone(q['difference']['estimate'])
        self.assertIsNone(result['standardized']['estimate'])
        self.assertEqual(result['standardized']['usable_replicates'], 0)

    def test_standardization_removes_a_synthetic_composition_gap(self):
        rows = []
        for i in range(5):
            # Each stratum has the same rate for PASS/FAIL, but the mixture differs.
            for passed, count in [(True, 2 * (5 - i)), (False, 2 * (i + 1))]:
                rows += [row(f'2021-01-{i+1:02}', passed, atr=i+1., outcome=i >= 3)] * count
        report = volatility_analysis(rows, np.array([1.5, 2.5, 3.5, 4.5]), replicates=50)
        self.assertGreater(report['unstratified']['difference']['estimate'], 0)
        self.assertAlmostEqual(report['standardized']['estimate'], 0)
        self.assertGreater(report['attenuation']['estimate'], 0)

    def test_date_cluster_draws_keep_same_day_events_together_and_pair_comparisons(self):
        rows = [row(), row(), row('2021-01-02'), row('2021-01-02')]
        boot = DateBootstrap(rows, replicates=3)
        boot.weights = np.array([[2, 0], [0, 2], [1, 1]])
        stat, draws = boot.mean([0., 0., 1., 1.])
        np.testing.assert_equal(draws, [0., 1., .5])
        self.assertEqual(stat['date_clusters'], 2)
        qs, qdraws = boot.quantiles(np.array([0., 10., 20., 30.]), np.ones(4, dtype=bool))
        np.testing.assert_allclose(qdraws[0], np.quantile([0, 10, 0, 10], [.5, .9]))
        np.testing.assert_allclose(qdraws[1], np.quantile([20, 30, 20, 30], [.5, .9]))

    def test_all_followup_entrypoints_refuse_forward_outcomes(self):
        unsafe = row('2026-09-17')
        with patch('desk.outcome_firewall.market_today', return_value=date(2026, 10, 4)):
            for action in (lambda: check_event(unsafe), lambda: quintile_boundaries([unsafe]),
                           lambda: volatility_analysis([unsafe], np.arange(4)),
                           lambda: cap_analysis([unsafe], None, None)):
                with self.assertRaises(ForwardOutcomeBlocked):
                    action()


class FollowupCapTest(unittest.TestCase):
    def setUp(self):
        self.rb = load_active_rulebook().rulebook.model_copy(deep=True)
        self.costs = load_active_cost_config().costs.model_copy(deep=True)
        for key in ('securities_transaction_tax', 'stamp_duty', 'exchange_transaction_charges',
                    'sebi_turnover_fee', 'gst', 'depository_charges', 'brokerage'):
            getattr(self.costs, key).rate = 0.
        self.costs.depository_charges.rate = 5.
        self.rb.risk.capital_allocated_inr = 1000.
        self.rb.risk.risk_per_trade_pct = 1.
        self.rb.risk.max_open_risk_pct = 100.
        self.rb.risk.max_per_stock_pct = 100.
        self.rb.risk.max_per_sector_pct = 100.
        self.plan = dict(decision_price=10., stop_level=9., quantity=10, atr20=.5,
                         adv_turnover=100000., stress=dict(floor_component_inr=0.,
                         worst_gap_component_inr=0., locked_circuit_loss_inr=None))

    def test_headroom_accounts_for_fixed_costs_not_just_ninety_percent_shares(self):
        # Risk cap=10; 90% cap=9; loss=q+5, hence four shares, not nine.
        self.assertEqual(buffered_quantity(self.plan, self.rb, self.costs), 4)
        m = cap_measurements(self.plan, 10., 4, self.rb, self.costs)
        self.assertEqual(m['per_trade']['usage'], 9.)

    def test_integer_search_matches_exhaustive_cap_feasibility(self):
        for price, adv in [(10., 1000.), (35., 10000.), (2., 10.)]:
            plan = copy.deepcopy(self.plan)
            plan.update(decision_price=price, stop_level=price * .9, adv_turnover=adv)
            feasible = [0] + [q for q in range(1, plan['quantity'] + 1)
                             if all(v['usage'] <= .9 * v['cap']
                                    for v in cap_measurements(plan, price, q, self.rb, self.costs).values())]
            self.assertEqual(buffered_quantity(plan, self.rb, self.costs), max(feasible))

    def test_all_caps_measured_and_quantity_is_not_resized_at_fill(self):
        quantity = buffered_quantity(self.plan, self.rb, self.costs)
        before = copy.deepcopy(self.plan)
        measurements = cap_measurements(self.plan, 100., quantity, self.rb, self.costs)
        self.assertGreater(measurements['per_trade']['ratio'], 1)
        self.assertEqual(quantity, 4)
        self.assertEqual(self.plan, before)
        self.assertEqual(set(measurements), set(CAPS))

    def test_each_of_six_caps_can_independently_limit_the_variant(self):
        for cap in CAPS:
            rb = self.rb.model_copy(deep=True)
            plan = copy.deepcopy(self.plan)
            rb.risk.risk_per_trade_pct = rb.risk.max_open_risk_pct = 100.
            rb.liquidity.max_order_pct_of_adv = 100.
            if cap == 'per_trade':
                rb.risk.risk_per_trade_pct = 1.
            elif cap == 'open_risk':
                rb.risk.max_open_risk_pct = 1.
            elif cap == 'per_stock':
                rb.risk.max_per_stock_pct = 5.
            elif cap == 'per_sector':
                rb.risk.max_per_sector_pct = 5.
            elif cap == 'order_adv':
                rb.liquidity.max_order_pct_of_adv = .05
            else:
                plan['adv_turnover'] = 600.
            with self.subTest(cap=cap):
                self.assertEqual(buffered_quantity(plan, rb, self.costs), 4)

    def observation(self, plan, fill):
        conn = MagicMock()
        conn.execute.return_value.fetchall.return_value = [('2021-01-02',)]
        with patch('desk.screening_plan.latest_as_of', return_value=[{'series':'EQ','open_price':fill}]):
            return execution_observation(conn, 'TEST', '2021-01-01', '2021-01-02', plan, self.rb, self.costs)

    def test_quantitative_caps_match_existing_observer_including_gap_through(self):
        for fill in (8., 10., 12., 200.):
            obs = self.observation(self.plan, fill)
            r = row()
            r.update(plan=self.plan, fill=fill, execution=obs)
            measures = cap_measurements(self.plan, fill, 10, self.rb, self.costs)
            assert_original_flags(r, measures, self.rb, self.costs)

    def test_zero_size_is_abstention_and_empty_breach_size_is_unavailable(self):
        self.costs.depository_charges.rate = 9.5
        self.plan['quantity'] = 1
        self.plan['stop_level'] = 9.9
        obs = self.observation(self.plan, 10.)
        r = row()
        r.update(plan=self.plan, fill=10., execution=obs)
        report = cap_analysis([r], self.rb, self.costs, replicates=10)
        self.assertEqual(report['variant_abstentions'], 1)
        self.assertEqual(report['variant_fills'], 0)
        self.assertIsNone(report['any_cap']['variant']['estimate'])
        self.assertIsNone(report['caps']['per_stock']['baseline']['conditional_excess_pct']['median']['estimate'])

    def test_corrupt_original_flags_are_rejected(self):
        r = row()
        r.update(plan=self.plan, fill=20., execution={'cap_breach_reasons':[]})
        with self.assertRaisesRegex(ValueError, 'does not match'):
            cap_analysis([r], self.rb, self.costs, replicates=10)

    def test_unknown_adv_is_excluded_not_counted_as_a_success(self):
        r = row()
        r.update(plan=dict(self.plan, adv_turnover=None), fill=10., execution={})
        report = cap_analysis([r], self.rb, self.costs, replicates=10)
        self.assertEqual(report['unknown_inputs'], 1)
        self.assertEqual(report['any_cap']['baseline']['n_events'], 0)


if __name__ == '__main__':
    unittest.main()
