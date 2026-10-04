"""Automation levels and deterministic kill switches (session item B2)."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import yaml

from desk.automation import kill_switches as ks
from desk.automation.levels import AutomationRefused, require_level
from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import DeskRulebook

ROOT = Path(__file__).resolve().parents[1]


def rulebook(level=None, version='v3'):
    raw = yaml.safe_load((ROOT/'rulebook/desk_rulebook_v3.yaml').read_text(encoding='utf-8'))
    raw['version'] = version
    if level is None:
        raw.pop('automation_level')
    else:
        raw['automation_level'] = level
    return DeskRulebook.model_validate(raw)


class AutomationLevelTest(unittest.TestCase):
    def test_v3_is_v2_plus_automation_level_only(self):
        v2 = yaml.safe_load((ROOT/'rulebook/desk_rulebook_v2.yaml').read_text(encoding='utf-8'))
        v3 = yaml.safe_load((ROOT/'rulebook/desk_rulebook_v3.yaml').read_text(encoding='utf-8'))
        self.assertEqual({k for k in set(v2) | set(v3) if v2.get(k) != v3.get(k)},
                         {'version', 'dated', 'automation_level'})
        self.assertEqual(v3['automation_level'], 'A1')

    def test_v3_must_state_level_and_old_versions_mean_a0(self):
        with self.assertRaises(ValueError):
            rulebook(None, 'v3')
        self.assertEqual(rulebook(None, 'v2').automation_level, 'A0')
        with self.assertRaises(ValueError):
            rulebook('A9')

    def test_actions_above_level_are_refused(self):
        self.assertEqual(require_level(rulebook('A1'), 'paper_auto'), 'A1')
        require_level(rulebook('A0'), 'research')
        with self.assertRaises(AutomationRefused):
            require_level(rulebook('A0'), 'paper_auto')
        for action in ('order_ticket', 'auto_order_small', 'auto_order_broad', 'invented_action'):
            with self.assertRaises(AutomationRefused):
                require_level(rulebook('A1'), action)

    def test_broker_api_refused_at_every_level(self):
        for level in ('A0', 'A1', 'A2', 'A3', 'A4'):
            with self.assertRaises(AutomationRefused) as raised:
                require_level(rulebook(level), 'broker_api_order')
            self.assertIn('SEBI', str(raised.exception))


class KillSwitchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.conn = get_desk_connection(Path(self.temp.name)/'desk.sqlite')

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_stale_or_inconsistent_data(self):
        plan = dict(decision_price=100, atr20=5, stop_level=90, quantity=10, stress=dict(stress_loss_inr=1))
        ok = ks.data_health('2026-10-05', '2026-10-05', '2026-10-06', 'OK', [('A', plan)], 7)
        self.assertFalse(ok.triggered)
        cases = [('2026-10-02', '2026-10-05', '2026-10-06', 'OK', []),     # not the latest session
                 ('2026-10-05', '2026-10-05', '2026-10-20', 'OK', []),     # too old
                 ('2026-10-05', None, '2026-10-06', 'OK', []),             # empty store
                 ('2026-10-05', '2026-10-05', '2026-10-06', 'ERROR', []),  # identity map
                 ('2026-10-05', '2026-10-05', '2026-10-06', 'OK', [('A', dict(plan, atr20=float('nan')))])]
        for args in cases:
            trip = ks.data_health(*args, 7)
            self.assertTrue(trip.triggered, args)
            self.assertEqual(trip.effect, 'NO_NEW_TRADES')

    def test_risk_state_unavailable(self):
        self.assertFalse(ks.risk_state({'P1': 100.0}, 25000).triggered)
        for losses, budget, error in [({'P1': None}, 25000, None), ({'P1': float('inf')}, 25000, None),
                                      ({}, 0, None), ({}, 25000, 'rulebook failed to load')]:
            trip = ks.risk_state(losses, budget, error)
            self.assertTrue(trip.triggered)
            self.assertEqual(trip.effect, 'NO_NEW_TRADES')

    def test_drawdown_and_losing_streak_brakes(self):
        args = dict(capital_inr=500000, drawdown_pct=6, streak_count=3, sealed=False)
        self.assertFalse(ks.drawdown_or_streak([('2026-10-01', -1000), ('2026-10-02', 500)], '2026-10-05', **args).triggered)
        month = ks.drawdown_or_streak([('2026-10-01', -30000)], '2026-10-05', **args)
        self.assertTrue(month.triggered)
        self.assertEqual(month.effect, 'FREEZE_ENTRIES')
        # Last month's loss does not count toward this month's brake.
        self.assertFalse(ks.drawdown_or_streak([('2026-09-30', -30000), ('2026-10-01', 10)], '2026-10-05', **args).triggered)
        streak = ks.drawdown_or_streak([('2026-10-01', -1), ('2026-10-02', -1), ('2026-10-03', -1)], '2026-10-05', **args)
        self.assertTrue(streak.triggered)
        self.assertTrue(streak.detail['losing_streak'])

    def test_operational_failures_disable_entries_at_three(self):
        fail, ok, skip = ks.OPERATIONAL_FAILURE, ks.ATTEMPT_OK, ks.NOT_ATTEMPTED
        self.assertFalse(ks.fill_failures([fail, fail], 3).triggered)
        trip = ks.fill_failures([ok, fail, fail, fail], 3)
        self.assertTrue(trip.triggered)
        self.assertEqual(trip.effect, 'DISABLE_AUTO_ENTRIES')
        self.assertEqual(trip.detail['consecutive_operational_failures'], 3)
        # A cancelled entry was never attempted: it neither counts nor ends the streak.
        self.assertTrue(ks.fill_failures([fail, skip, fail, skip, fail], 3).triggered)

    def test_untouched_limit_never_counts_toward_disabling(self):
        fail, ok = ks.OPERATIONAL_FAILURE, ks.ATTEMPT_OK
        self.assertFalse(ks.fill_failures([ok] * 50, 3).triggered)            # 50 NO_FILLs
        # A NO_FILL is a successful operation, so it ends a failure streak like a fill does.
        self.assertFalse(ks.fill_failures([fail, fail, ok, fail, fail], 3).triggered)
        with self.assertRaises(ValueError):
            ks.fill_failures(['ENTRY_NO_FILL'], 3)                             # raw types are refused

    def test_open_critical_defect_fails_operational_gate(self):
        self.assertFalse(ks.open_critical_defect([], []).triggered)
        for high, unknown in [(['P9-001'], []), ([], ['P9-002'])]:
            trip = ks.open_critical_defect(high, unknown)
            self.assertTrue(trip.triggered)
            self.assertEqual(trip.effect, 'OPERATIONAL_GATE_FAIL')

    def test_real_register_feeds_the_defect_switch(self):
        from desk.readiness import open_defects
        high, unknown = open_defects(ROOT/'docs/DEFECT_REGISTER.md')
        self.assertEqual(ks.open_critical_defect(high, unknown).triggered, bool(high or unknown))

    def test_calibration_switch_defined_but_inactive(self):
        trip = ks.calibration_degradation()
        self.assertFalse(trip.triggered)
        self.assertEqual(trip.effect, 'REVERT_TO_PAPER_ONLY')
        lines = ks.display_lines(self.conn, 'S0')
        self.assertTrue(any('CALIBRATION_EDGE_DEGRADATION: INACTIVE' in l for l in lines))

    def test_transitions_are_logged_append_only(self):
        trip = lambda on: ks.Trip('DATA_STALE_OR_INCONSISTENT', on, dict(problems=['x'] if on else []))
        self.assertEqual(ks.evaluate_and_log(self.conn, [trip(True)], scope='S0', run_date='2026-10-05'),
                         {'DATA_STALE_OR_INCONSISTENT': True})
        ks.evaluate_and_log(self.conn, [trip(True)], scope='S0', run_date='2026-10-06')   # unchanged: no row
        ks.evaluate_and_log(self.conn, [trip(False)], scope='S0', run_date='2026-10-07')
        rows = [r['state'] for r in self.conn.execute('SELECT state FROM kill_switch_events ORDER BY event_id')]
        self.assertEqual(rows, ['TRIGGERED', 'CLEARED'])
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE kill_switch_events SET state='CLEARED'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM kill_switch_events')

    def test_latched_switch_needs_human_reset_with_reason(self):
        trip = lambda on: ks.Trip('REPEATED_FILL_FAILURES', on, {})
        ks.evaluate_and_log(self.conn, [trip(True)], scope='S0', run_date='2026-10-05')
        self.assertTrue(ks.evaluate_and_log(self.conn, [trip(False)], scope='S0', run_date='2026-10-06')['REPEATED_FILL_FAILURES'])
        with self.assertRaises(ValueError):
            ks.reset(self.conn, 'REPEATED_FILL_FAILURES', scope='S0', run_date='2026-10-06', reason=' ')
        with self.assertRaises(ValueError):
            ks.reset(self.conn, 'DATA_STALE_OR_INCONSISTENT', scope='S0', run_date='2026-10-06', reason='x')
        ks.reset(self.conn, 'REPEATED_FILL_FAILURES', scope='S0', run_date='2026-10-06', reason='data repaired')
        self.assertFalse(ks.evaluate_and_log(self.conn, [trip(False)], scope='S0', run_date='2026-10-07')['REPEATED_FILL_FAILURES'])

    def test_strategy0_brake_displayed_as_exempt_until_seal_lifts(self):
        before = '\n'.join(ks.display_lines(self.conn, 'S0', today='2027-05-31'))
        self.assertIn('DRAWDOWN_OR_LOSING_STREAK: EXEMPT (P&L brakes exempt until 2027-06-01', before)
        after = '\n'.join(ks.display_lines(self.conn, 'S0', today='2027-06-01'))
        self.assertIn('DRAWDOWN_OR_LOSING_STREAK: clear (never triggered)', after)
        for scope in ('S1', 'manual'):     # any future strategy keeps the brake
            self.assertNotIn('EXEMPT', '\n'.join(ks.display_lines(self.conn, scope, today='2026-10-05')))

    def test_sealed_detail_is_not_displayed(self):
        trip = ks.Trip('DRAWDOWN_OR_LOSING_STREAK', True, dict(month_realized_pnl_inr=-31234.5), sealed=True)
        ks.evaluate_and_log(self.conn, [trip], scope='S1', run_date='2026-10-05')
        text = '\n'.join(ks.display_lines(self.conn, 'S1'))
        self.assertIn('DRAWDOWN_OR_LOSING_STREAK: ACTIVE -> FREEZE_ENTRIES', text)
        self.assertIn('detail sealed until 2027-06-01', text)
        self.assertNotIn('31234', text)
        stored = self.conn.execute('SELECT detail FROM kill_switch_events').fetchone()[0]
        self.assertEqual(json.loads(stored)['month_realized_pnl_inr'], -31234.5)


if __name__ == '__main__':
    unittest.main()
