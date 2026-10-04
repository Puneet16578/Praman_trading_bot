"""Strategy 0 sealed paper engine, registry and seal (session item B4)."""
from datetime import date
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import yaml

from desk.automation import registry, seal, strategy0
from desk.automation.levels import AutomationRefused
from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import DeskRulebook
from src.bitemporal.schema import BHAVCOPY, CORPORATE_ACTIONS
from tests.desk_fixtures import make_test_costs

ROOT = Path(__file__).resolve().parents[1]
DAYS = [f'2026-10-{d:02d}' for d in (5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23)]


def rulebook(level='A1'):
    raw = yaml.safe_load((ROOT/'rulebook/desk_rulebook_v3.yaml').read_text(encoding='utf-8'))
    raw['automation_level'] = level
    return DeskRulebook.model_validate(raw)


class Store:
    """Minimal Praman fixture: bhavcopy + corporate actions."""

    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(BHAVCOPY.ddl)
        self.conn.execute(CORPORATE_ACTIONS.ddl)

    def bar(self, symbol, day, o, h, l, c, known=None):
        known = known or day
        self.conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,'
                          'prev_close,traded_qty,series,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                          (symbol, day, known, o, h, l, c, c, 1000, 'EQ', 'fixture', known))

    def market(self, day, symbols=('ZZZ',)):
        for s in symbols:
            self.bar(s, day, 100, 101, 99, 100)


def plan(price=100.0, atr=4.0, stop=92.0, qty=100, stress=12000.0):
    return dict(decision_price=price, atr20=atr, stop_level=stop, quantity=qty, adv_turnover=1e9,
                stress=dict(stress_loss_inr=stress, floor_component_inr=1, worst_gap_component_inr=None,
                            locked_circuit_loss_inr=None))


def opportunity(desk, symbol, day, p, state='SCREEN_PASS'):
    gates = {f'G{i}': dict(result='PASS', reasons=[]) for i in range(1, 9)}
    desk.execute('INSERT INTO opportunity_log(symbol,event_date,knowledge_date,recorded_at,inputs,evidence_bundle_hash,'
                 'gate_results,state,reasons,content_hash,code_commit,praman_watermark,desk_watermark,rulebook_hash,cost_config_hash) '
                 'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                 (symbol, day, day, day, json.dumps(dict(plan=p)), 'h', json.dumps(gates), state, '[]', f'{symbol}{day}',
                  'c', 'w', 'd', 'r', 'k'))
    desk.commit()


class EngineFixture(unittest.TestCase):
    """Shared setup only; no tests, so subclasses never rerun the engine tests."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desk = get_desk_connection(Path(self.temp.name)/'desk.sqlite')
        self.store = Store()
        self.defects = Path(self.temp.name)/'defects.md'
        self.defects.write_text('# none open\n', encoding='utf-8')
        self.costs = make_test_costs()

    def tearDown(self):
        self.desk.close()
        self.store.conn.close()
        self.temp.cleanup()

    def run_day(self, day, rb=None, today=None, **kw):
        return strategy0.run(self.store.conn, self.desk, day, rulebook=rb or rulebook(), costs=self.costs,
                             rulebook_file='desk_rulebook_v3.yaml', rulebook_hash='r', cost_config_hash='k',
                             code_commit='c', praman_watermark='w', today=today or day, defect_path=self.defects,
                             isin_status='OK', **kw)

    def events(self, *types):
        rows = self.desk.execute('SELECT * FROM strategy_paper_events ORDER BY event_id').fetchall()
        return [dict(r) | dict(detail=json.loads(r['detail'])) for r in rows if not types or r['event_type'] in types]



class EngineTest(EngineFixture):
    def test_full_lifecycle_budget_rejection_and_idempotence(self):
        d0 = DAYS[0]
        self.store.market(d0)
        for s in ('AAA', 'BBB', 'CCC'):
            self.store.bar(s, d0, 100, 101, 99, 100)
            opportunity(self.desk, s, d0, plan(qty=600))
        ops = self.run_day(d0)
        self.assertEqual((ops['candidates'], ops['accepted']), (3, 2))
        self.assertEqual(ops['rejected'], {'OPEN_RISK_BUDGET': 1})
        rejected = self.events('CANDIDATE_REJECTED')[0]
        self.assertEqual(rejected['symbol'], 'CCC')
        self.assertIn('budget 25000.00', rejected['detail']['reasons'][0])
        self.assertEqual(self.run_day(d0)['status'], 'ALREADY_RUN')
        self.assertEqual(len(self.events()), 3)
        contracts = [json.loads(r[0]) for r in self.desk.execute('SELECT contract FROM decision_contracts ORDER BY contract_id')]
        self.assertEqual([c['state']['value'] for c in contracts], ['WATCH', 'WATCH', 'VETO'])
        self.assertEqual(contracts[0]['calibrated_probability']['status'], 'UNKNOWN')

        # Next session: AAA opens under the limit (102); BBB opens above, low touches it.
        d1 = DAYS[1]
        self.store.market(d1)
        self.store.bar('AAA', d1, 101, 104, 100, 103)
        self.store.bar('BBB', d1, 105, 106, 101, 104)
        ops = self.run_day(d1)
        fills = {e['symbol']: e['detail'] for e in self.events('ENTRY_FILLED')}
        self.assertEqual(fills['AAA']['price'], 101)
        self.assertEqual((fills['BBB']['price'], fills['BBB']['status']), (102, 'FILL_LIMIT'))
        self.assertEqual(ops['entries_filled'], 2)
        self.assertEqual(ops['cap_breaches_at_fill'], 2)   # 600 shares x 9-10 points of stop > Rs 5,000 cap
        self.assertTrue(fills['AAA']['per_trade_cap_breach_at_fill'])

        # AAA hits its stop by gapping below it; BBB is held until the time limit.
        d2 = DAYS[2]
        self.store.market(d2)
        self.store.bar('AAA', d2, 91, 92, 90, 91)
        self.store.bar('BBB', d2, 103, 104, 101, 103)
        self.run_day(d2)
        stop = self.events('EXIT_FILLED')[0]
        self.assertEqual((stop['symbol'], stop['detail']['kind'], stop['detail']['price']), ('AAA', 'stop_gap', 91))
        for day in DAYS[3:12]:
            self.store.market(day)
            self.store.bar('BBB', day, 103, 104, 101, 103)
            self.run_day(day)
        ordered = self.events('EXIT_ORDERED')
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]['detail']['reason'], 'TIME_LIMIT')
        self.assertEqual(ordered[0]['detail']['sessions_held'], 10)
        exit_day = DAYS[12]
        self.store.market(exit_day)
        self.store.bar('BBB', exit_day, 99, 100, 98, 99)
        self.run_day(exit_day)
        filled = [e for e in self.events('EXIT_FILLED') if e['symbol'] == 'BBB'][0]
        self.assertEqual((filled['event_date'], filled['detail']['price'], filled['detail']['reason']), (exit_day, 99, 'TIME_LIMIT'))
        book = strategy0.load_book(self.desk, 1)
        self.assertEqual(sorted(p['status'] for p in book.values()), ['CLOSED', 'CLOSED'])

    def test_stale_data_blocks_entries_and_cancels_pending(self):
        d0, d1 = DAYS[0], DAYS[1]
        self.store.market(d0)
        opportunity(self.desk, 'AAA', d0, plan())
        self.run_day(d0)
        self.store.market(d1)
        self.store.bar('AAA', d1, 100, 101, 99, 100)
        opportunity(self.desk, 'BBB', d1, plan())
        ops = self.run_day(d1, today='2026-10-30')       # 24 days stale
        self.assertIn('DATA_STALE_OR_INCONSISTENT', ops['entry_blocked_by'])
        self.assertEqual(ops['entries_cancelled'], 1)
        self.assertEqual(ops['rejected'], {'KILL_SWITCH': 1})
        self.assertEqual(self.events('ENTRY_NO_FILL')[0]['detail']['reason'], 'CANCELLED: kill switch DATA_STALE_OR_INCONSISTENT')

    def test_repeated_fill_failures_disable_automatic_entries(self):
        for i in range(4):
            day, nxt = DAYS[i], DAYS[i + 1]
            self.store.market(day)
            opportunity(self.desk, f'S{i}', day, plan())   # never any bar for S{i}: every fill fails
            self.run_day(day)
        self.store.market(DAYS[4])
        ops = self.run_day(DAYS[4])
        # Switches are evaluated before entries settle: three failures trip it, so the fourth
        # pending entry is cancelled rather than attempted.
        self.assertEqual(len(self.events('ENTRY_FILL_FAILED')), 3)
        self.assertEqual(ops['entries_cancelled'], 1)
        self.assertIn('REPEATED_FILL_FAILURES', ops['kill_switches_active'])
        row = self.desk.execute("SELECT * FROM kill_switch_events WHERE switch='REPEATED_FILL_FAILURES'").fetchone()
        self.assertEqual(row['state'], 'TRIGGERED')

    def test_inconsistent_candidate_plan_blocks_entries(self):
        d0 = DAYS[0]
        self.store.market(d0)
        opportunity(self.desk, 'AAA', d0, plan(stress=float('nan')))
        ops = self.run_day(d0)
        self.assertEqual(ops['accepted'], 0)
        self.assertIn('DATA_STALE_OR_INCONSISTENT', ops['entry_blocked_by'])

    def test_risk_state_unavailable_blocks_entries(self):
        d0, d1 = DAYS[0], DAYS[1]
        self.store.market(d0)
        self.run_day(d0)
        # A corrupt book: an accepted position without a stress loss.
        run_id = self.desk.execute('SELECT run_id FROM strategy_runs').fetchone()[0]
        self.desk.execute("INSERT INTO strategy_paper_events (strategy_id,strategy_version,run_id,position_id,opportunity_id,"
                          "symbol,decision_date,event_type,event_date,detail,recorded_at) VALUES "
                          "('S0',1,?,'S0:QQQ:2026-10-05',NULL,'QQQ','2026-10-05','CANDIDATE_ACCEPTED','2026-10-05',?,'t')",
                          (run_id, json.dumps(dict(stress_loss_inr=None, decision_price=100, atr20=4, stop_level=92, quantity=1))))
        self.desk.commit()
        self.store.market(d1)
        opportunity(self.desk, 'AAA', d1, plan())
        ops = self.run_day(d1)
        self.assertIn('RISK_STATE_UNAVAILABLE', ops['entry_blocked_by'])
        self.assertEqual(ops['rejected'], {'KILL_SWITCH': 1})

    def test_open_critical_defect_only_fails_operational_gate(self):
        self.defects.write_text('## P9-999 - fixture (open)\n\n**Severity.** Critical.\n', encoding='utf-8')
        self.store.market(DAYS[0])
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        ops = self.run_day(DAYS[0])
        self.assertIn('OPEN_CRITICAL_DEFECT', ops['kill_switches_active'])
        self.assertEqual(ops['accepted'], 1)

    def _two_large_losses_then_candidate(self, days):
        self.store.market(days[0])
        for s in ('AAA', 'BBB'):
            opportunity(self.desk, s, days[0], plan(qty=2000, stress=12000))
        self.run_day(days[0])
        self.store.market(days[1])
        for s in ('AAA', 'BBB'):
            self.store.bar(s, days[1], 100, 101, 99, 100)
        self.run_day(days[1])
        self.store.market(days[2])
        for s in ('AAA', 'BBB'):
            self.store.bar(s, days[2], 80, 81, 79, 80)    # both gap through: about -Rs 40,000 each
        self.run_day(days[2])
        self.store.market(days[3])
        opportunity(self.desk, 'CCC', days[3], plan())
        return self.run_day(days[3])

    def test_strategy0_exempt_from_pnl_brakes_while_sealed(self):
        with patch('desk.automation.seal.realized_pnl', side_effect=AssertionError('sealed P&L read')):
            ops = self._two_large_losses_then_candidate(DAYS)
        self.assertEqual(len(self.events('EXIT_FILLED')), 2)
        self.assertNotIn('DRAWDOWN_OR_LOSING_STREAK', ops['kill_switches_active'])
        self.assertIn('exempt until 2027-06-01', ops['exempt_switches']['DRAWDOWN_OR_LOSING_STREAK'])
        self.assertEqual((ops['accepted'], ops['rejected']), (1, {}))
        self.assertIsNone(self.desk.execute("SELECT 1 FROM kill_switch_events WHERE switch='DRAWDOWN_OR_LOSING_STREAK'").fetchone())
        with self.assertRaises(seal.SealedOutcome):
            seal.brake_inputs(strategy0.load_book(self.desk, 1), 'S0', today=DAYS[3])

    def test_brake_code_exercised_after_seal_lifts_synthetic(self):
        june = ['2027-06-01', '2027-06-02', '2027-06-03', '2027-06-04']   # synthetic post-seal dates
        ops = self._two_large_losses_then_candidate(june)
        self.assertEqual(ops['exempt_switches'], {})
        self.assertIn('DRAWDOWN_OR_LOSING_STREAK', ops['entry_blocked_by'])
        self.assertEqual(ops['rejected'], {'KILL_SWITCH': 1})
        row = self.desk.execute("SELECT * FROM kill_switch_events WHERE switch='DRAWDOWN_OR_LOSING_STREAK'").fetchone()
        self.assertEqual((row['state'], row['sealed']), ('TRIGGERED', 0))
        self.assertLess(json.loads(row['detail'])['month_realized_pnl_inr'], -30000)

    def test_engine_errors_are_operational_failures(self):
        real = strategy0.limit_fill
        def broken(plan_, opening, low):
            raise ZeroDivisionError('fixture')
        for i in range(4):
            self.store.market(DAYS[i])
            if i:
                self.store.bar(f'E{i - 1}', DAYS[i], 100, 101, 99, 100)  # data present: the engine fails
            opportunity(self.desk, f'E{i}', DAYS[i], plan())
            with patch('desk.automation.strategy0.limit_fill', side_effect=broken):
                self.run_day(DAYS[i])
        self.store.market(DAYS[4])
        self.store.bar('E3', DAYS[4], 100, 101, 99, 100)
        with patch('desk.automation.strategy0.limit_fill', side_effect=real):
            ops = self.run_day(DAYS[4])
        failed = self.events('ENTRY_FILL_FAILED')
        self.assertEqual([e['detail']['failure'] for e in failed], ['ENGINE_ERROR'] * 3)
        self.assertEqual(failed[0]['detail']['error_type'], 'ZeroDivisionError')
        self.assertIn('REPEATED_FILL_FAILURES', ops['kill_switches_active'])

    def test_untouched_limits_never_disable_entries(self):
        for i in range(6):
            self.store.market(DAYS[i])
            if i:
                self.store.bar(f'N{i - 1}', DAYS[i], 110, 112, 109, 111)  # open and low above the 102 limit
            opportunity(self.desk, f'N{i}', DAYS[i], plan())
            ops = self.run_day(DAYS[i])
        self.assertEqual(len(self.events('ENTRY_NO_FILL')), 5)
        self.assertEqual(len(self.events('ENTRY_FILL_FAILED')), 0)
        self.assertNotIn('REPEATED_FILL_FAILURES', ops['kill_switches_active'])
        self.assertEqual(ops['accepted'], 1)

    def test_crashed_nightly_run_counts_as_operational_failure(self):
        from desk.automation import nightly
        path = Path(self.temp.name)/'nightly.sqlite'
        own = Store()                      # run_auto_paper closes the connection it is given
        own.market(DAYS[0])
        with patch('desk.automation.nightly.get_live_connection', return_value=own.conn), \
             patch('desk.automation.nightly.max_recorded_at', return_value='w'), \
             patch('desk.automation.strategy0.run', side_effect=RuntimeError('fixture crash')):
            with self.assertRaises(RuntimeError):
                nightly.run_auto_paper(DAYS[0], desk_db_path=path)
        conn = get_desk_connection(path)
        try:
            row = conn.execute('SELECT * FROM journal_events WHERE event_type=?', (strategy0.RUN_FAILED_EVENT,)).fetchone()
            self.assertEqual(json.loads(row['detail']), dict(run_date=DAYS[0], error_type='RuntimeError'))
            self.assertEqual(strategy0._entry_outcomes_since(conn, 1, None), ['OPERATIONAL_FAILURE'])
        finally:
            conn.close()

    def test_split_between_decision_and_fill_uses_decision_basis(self):
        self.store.market(DAYS[0])
        opportunity(self.desk, 'SPL', DAYS[0], plan())             # decision 100, ATR 4 -> limit 102; stop 92
        self.run_day(DAYS[0])
        self.store.conn.execute('INSERT INTO corporate_actions (symbol,action_type,event_date,knowledge_date,ratio_numerator,'
                                "ratio_denominator,confidence_tier,details,source_file,recorded_at) VALUES "
                                "('SPL','SPLIT',?,?,10,1,'HIGH','fixture','fixture',?)", (DAYS[1], DAYS[0], DAYS[0]))
        self.store.market(DAYS[1])
        self.store.bar('SPL', DAYS[1], 10.15, 10.3, 10.0, 10.2)    # raw post-split prices
        self.run_day(DAYS[1])
        fill = self.events('ENTRY_FILLED')[0]['detail']
        self.assertAlmostEqual(fill['price'], 101.5)                # 10.15 x 10 on the decision basis, not 10.15
        self.assertEqual((fill['basis_factor'], fill['quantity'], fill['status']), (10.0, 100, 'FILL_OPEN'))
        self.store.market(DAYS[2])
        self.store.bar('SPL', DAYS[2], 9.9, 10.0, 9.5, 9.8)        # 99 / 95 on the decision basis: above the stop
        self.run_day(DAYS[2])
        monitored = self.events('MONITORED')[-1]['detail']
        self.assertAlmostEqual(monitored['stop'], 9.2)
        self.assertEqual(monitored['factor'], 10.0)
        self.assertEqual(self.events('EXIT_FILLED'), [])

    def test_refused_above_automation_level(self):
        with self.assertRaises(AutomationRefused):
            self.run_day(DAYS[0], rb=rulebook('A0'))
        self.assertEqual(self.desk.execute('SELECT COUNT(*) FROM strategy_runs').fetchone()[0], 0)

    def test_operational_summary_has_no_outcomes(self):
        self.store.market(DAYS[0])
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        ops = self.run_day(DAYS[0])
        stored = strategy0.latest_operational(self.desk)['operational']
        self.assertEqual(stored, json.loads(json.dumps(ops)))
        for word in ('pnl', 'profit', 'exit_price', 'return'):
            self.assertNotIn(word, json.dumps(stored).lower())
        self.assertFalse(stored['no_trade'])


class RegistryAndSealTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desk = get_desk_connection(Path(self.temp.name)/'desk.sqlite')

    def tearDown(self):
        self.desk.close()
        self.temp.cleanup()

    def test_strategy0_registered_with_rule_based_entry_policy(self):
        row = registry.ensure_registered(self.desk)
        self.assertEqual((row['strategy_id'], row['name'], row['status']), ('S0', 'baseline screen', 'PAPER_BURN_IN'))
        self.assertIn('NOT expected to be profitable', row['purpose'])
        entry = row['definition']['entry']
        self.assertEqual(entry['policy'], 'LIMIT_DECISION_PLUS_0.5_ATR20')
        self.assertTrue(all(entry['evaluation'][k] for k in ('lower_breach_rate', 'interval_entirely_below_zero',
                                                              'fill_rate_at_least_60pct')))
        self.assertEqual(registry.current(self.desk, 'manual')['status'], 'ACTIVE_MANUAL')
        registry.ensure_registered(self.desk)   # idempotent
        self.assertEqual(self.desk.execute('SELECT COUNT(*) FROM trading_strategies').fetchone()[0], 2)

    def test_entry_rule_falls_back_when_conditions_fail(self):
        source = json.loads(registry.FOLLOWUP2.read_text(encoding='utf-8'))
        for change in ('interval', 'fill'):
            data = json.loads(json.dumps(source))
            period = data['periods'][registry.PRIMARY]
            if change == 'interval':
                period['differences']['per_trade_breach_rate']['interval95'] = [-0.03, 0.001]
            else:
                period['variants']['limit']['fill_rate']['estimate'] = 0.59
            path = registry.ROOT/'scratch'/f'_followup2_{change}.json'
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data), encoding='utf-8')
            try:
                self.assertEqual(registry.entry_policy(path)['policy'], 'NEXT_OPEN')
            finally:
                path.unlink()

    def test_registry_is_versioned_and_never_deleted(self):
        registry.ensure_registered(self.desk)
        with self.assertRaises(registry.RegistryError):
            registry.register(self.desk, **registry.STRATEGY_0, definition=dict(changed=True))
        registry.set_status(self.desk, 'S0', 1, 'RETIRED')
        self.assertEqual(registry.current(self.desk, 'S0')['status'], 'RETIRED')
        self.assertEqual(self.desk.execute("SELECT COUNT(*) FROM trading_strategies WHERE strategy_id='S0'").fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.desk.execute("DELETE FROM trading_strategies WHERE strategy_id='S0'")

    def test_seal_blocks_outcomes_until_june_2027(self):
        positions = {'S0:AAA:2026-10-05': dict(decision_date='2026-10-05',
                     entry=dict(price=100, quantity=10, buy_cost_inr=1), exit=dict(price=90, quantity=10, sell_cost_inr=1))}
        with self.assertRaises(seal.SealedOutcome):
            seal.position_outcomes(positions, 'S0', today=date(2027, 5, 31))
        self.assertEqual(seal.position_outcomes(positions, 'S0', today=date(2027, 6, 1)), {'S0:AAA:2026-10-05': -102})
        self.assertEqual(seal.position_outcomes(positions, 'manual', today=date(2026, 10, 6)), {'S0:AAA:2026-10-05': -102})
        old = {'x': dict(positions['S0:AAA:2026-10-05'], decision_date='2026-09-15')}
        self.assertEqual(seal.position_outcomes(old, 'S0', today=date(2026, 10, 6)), {'x': -102})



class NightlyTest(unittest.TestCase):
    def test_auto_paper_runs_after_scan_with_no_human_step(self):
        import contextlib, io, sys
        sys.path.insert(0, str(ROOT/'scripts'))
        import weekly_ingest
        labels = [label for label, _ in weekly_ingest.STEPS]
        self.assertLess(labels.index('desk_scan'), labels.index('auto_paper'))
        self.assertLess(labels.index('auto_paper'), labels.index('backups'))
        ops = dict(run_date='2026-10-05', candidates=3, accepted=1, rejected={'OPEN_RISK_BUDGET': 2},
                   kill_switches_active=[])
        with patch('desk.automation.nightly.run_auto_paper', return_value=ops) as called,              patch('builtins.input', side_effect=AssertionError('no human step allowed')),              contextlib.redirect_stdout(io.StringIO()) as out:
            weekly_ingest.step_auto_paper()
        called.assert_called_once_with()
        self.assertIn('3 candidates, 1 accepted', out.getvalue())


if __name__ == '__main__':
    unittest.main()
