"""P8-064: no paper sell at an all-day lower lock, no paper buy at an upper lock, both books.

Synthetic stores only. Bands live in the Desk store (price-band report dated the session before),
ticks in `tick_sizes`; the reference price is the previous session's close.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from desk.automation import strategy0
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.paper import locks
from desk.tick_sizes import ingest_master, parse_master, tick_for_session
from src.bitemporal.connection import get_connection, init_db
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, make_test_costs
from tests.test_strategy0_engine import DAYS, EngineFixture, ist, opportunity, plan


def band(desk, symbol, report_date, pct, *, series='EQ', recorded_at=None, kind='FIXED'):
    desk.execute("INSERT INTO circuit_bands (symbol,series,security_name,event_date,knowledge_date,recorded_at,band_kind,"
                 "band_pct,remarks,source_url,source_sha256,published_at) VALUES (?,?,?,?,?,?,?,?,'-','fixture',?,?)",
                 (symbol, series, symbol, report_date, report_date, recorded_at or f'{report_date}T12:30:00+00:00', kind,
                  pct if kind == 'FIXED' else None, f'h{report_date}', f'{report_date}T17:30:00+05:30'))
    desk.commit()


def tick(desk, symbol, session, rupees=0.05):
    desk.execute("INSERT INTO tick_sizes (symbol,event_date,knowledge_date,recorded_at,tick_rupees,tick_paise,source_url,"
                 "source_last_modified,source_sha256) VALUES (?,?,?,?,?,?,'fixture','x',?)",
                 (symbol, session, session, f'{session}T13:00:00+00:00', rupees, rupees * 100, f't{session}'))
    desk.commit()


class TickMasterTest(unittest.TestCase):
    MASTER = json.dumps([
        dict(token='1', symbol='AAA-EQ', exch_seg='NSE', expiry='', instrumenttype='', tick_size='5.000000'),
        dict(token='2', symbol='BBB-EQ', exch_seg='NSE', expiry='', instrumenttype='', tick_size='1.000000'),
        dict(token='3', symbol='DUP-EQ', exch_seg='NSE', expiry='', instrumenttype='', tick_size='5.000000'),
        dict(token='4', symbol='DUP-EQ', exch_seg='NSE', expiry='', instrumenttype='', tick_size='10.000000'),
        dict(token='5', symbol='AAA-EQ', exch_seg='BSE', expiry='', instrumenttype='', tick_size='1.000000'),
        dict(token='6', symbol='FUT', exch_seg='NFO', expiry='27OCT2026', instrumenttype='FUTSTK', tick_size='10'),
    ]).encode()

    def test_ticks_are_in_paise_unique_eq_only_and_dated_by_the_generation_morning(self):
        self.assertEqual(parse_master(self.MASTER), {'AAA': 5.0, 'BBB': 1.0})       # DUP disagrees: skipped
        with tempfile.TemporaryDirectory() as folder:
            desk = get_desk_connection(Path(folder) / 'd.sqlite')
            try:
                stamp = 'Tue, 13 Oct 2026 02:30:07 GMT'                           # 08:00 IST on 13 Oct
                recorded = datetime(2026, 10, 13, 13, 0, tzinfo=timezone.utc)
                self.assertEqual(ingest_master(desk, self.MASTER, stamp, recorded_at=recorded), 2)
                self.assertEqual(ingest_master(desk, self.MASTER, stamp, recorded_at=recorded), 0)   # idempotent
                self.assertEqual(tick_for_session(desk, 'AAA', '2026-10-13', '2026-10-13'), 0.05)
                self.assertIsNone(tick_for_session(desk, 'AAA', '2026-10-14', '2026-10-14'))       # that day only
                self.assertIsNone(tick_for_session(desk, 'AAA', '2026-10-13', '2026-10-12'))       # not yet known
                with self.assertRaises(ValueError):                                                 # future header
                    ingest_master(desk, self.MASTER, 'Wed, 14 Oct 2026 02:30:07 GMT', recorded_at=recorded)
            finally:
                desk.close()


class TickNightlyStepTest(unittest.TestCase):
    def test_step_runs_before_both_books_and_a_failure_is_a_warn(self):
        import contextlib, io, sys
        from unittest.mock import patch
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        import weekly_ingest
        labels = [label for label, _ in weekly_ingest.STEPS]
        self.assertEqual(labels.index('tick_sizes'), labels.index('circuit_bands') + 1)
        self.assertLess(labels.index('tick_sizes'), min(labels.index('auto_paper'), labels.index('manual_monitor')))
        with tempfile.TemporaryDirectory() as folder, \
                patch('desk.lib.connection.get_desk_connection', return_value=get_desk_connection(Path(folder) / 'd.sqlite')), \
                patch('desk.tick_sizes.fetch_and_record', side_effect=OSError('no route')):
            result = weekly_ingest._run_capturing('tick_sizes', weekly_ingest.step_tick_sizes)
        self.assertEqual(result['status'], 'WARN')
        self.assertIn("WARN tick sizes not recorded (OSError); this session's ticks stay UNKNOWN", result['output'])
        self.assertNotIn('no route', result['output'])

    def test_fetch_records_the_master_under_its_last_modified_session(self):
        from unittest.mock import Mock
        from desk.tick_sizes import fetch_and_record
        response = Mock(status_code=200, content=TickMasterTest.MASTER,
                        headers={'Last-Modified': 'Tue, 13 Oct 2026 02:30:07 GMT'})
        session = Mock()
        session.get.return_value = response
        with tempfile.TemporaryDirectory() as folder:
            desk = get_desk_connection(Path(folder) / 'd.sqlite')
            try:
                line = fetch_and_record(desk, session)
                self.assertIn('2 rows recorded for 2026-10-13', line)
                self.assertEqual(session.get.call_args.kwargs['allow_redirects'], False)
                response.headers = {}
                with self.assertRaisesRegex(ValueError, 'no Last-Modified'):
                    fetch_and_record(desk, session)
            finally:
                desk.close()


class LockStateTest(EngineFixture):
    def bar(self, symbol, day, o, h, l, c):
        self.store.bar(symbol, day, o, h, l, c)
        return dict(open_price=o, high_price=h, low_price=l, close_price=c, series='EQ')

    def state(self, bar, day=DAYS[1]):
        return locks.lock_state(self.store.conn, self.desk, 'AAA', day, bar, day)

    def test_lower_and_upper_locks_need_all_four_prices_within_a_tick(self):
        self.bar('AAA', DAYS[0], 100, 101, 99, 100)                          # reference close 100
        band(self.desk, 'AAA', DAYS[0], 10)                                  # limits 90 and 110 on DAYS[1]
        tick(self.desk, 'AAA', DAYS[1])
        self.assertEqual(self.state(dict(open_price=90, high_price=90.05, low_price=90, close_price=90, series='EQ')).state,
                         locks.LOCKED_LOWER)
        self.assertEqual(self.state(dict(open_price=110, high_price=110, low_price=110, close_price=110, series='EQ')).state,
                         locks.LOCKED_UPPER)
        self.assertEqual(self.state(dict(open_price=90, high_price=93, low_price=90, close_price=91, series='EQ')).state,
                         locks.NOT_LOCKED)                                   # touched the band, traded above it
        self.assertEqual(self.state(dict(open_price=97, high_price=97, low_price=97, close_price=97, series='EQ')).state,
                         locks.NOT_LOCKED)                                   # flat, but nowhere near a limit

    def test_a_flat_bar_with_any_limit_input_unknown_is_assumed_locked(self):
        flat = dict(open_price=95, high_price=95, low_price=95, close_price=95, series='EQ')
        moving = dict(open_price=95, high_price=96, low_price=94, close_price=95, series='EQ')
        self.bar('AAA', DAYS[0], 100, 101, 99, 100)
        self.assertEqual(self.state(flat).state, locks.FLAT_UNKNOWN)          # no band report, no tick
        self.assertEqual(self.state(moving).state, locks.NOT_LOCKED)
        band(self.desk, 'AAA', DAYS[0], 10)
        check = self.state(flat)
        self.assertEqual((check.state, check.limits.unknown), (locks.FLAT_UNKNOWN, ('tick size unknown',)))
        self.assertTrue(check.blocks_buy and check.blocks_sell)
        tick(self.desk, 'AAA', DAYS[1])
        self.store.conn.execute('INSERT INTO corporate_actions (symbol,action_type,event_date,knowledge_date,ratio_numerator,'
                                "ratio_denominator,confidence_tier,details,source_file,recorded_at) VALUES "
                                "('AAA','SPLIT',?,?,2,1,'HIGH','fixture','fixture',?)", (DAYS[1], DAYS[0], DAYS[0]))
        self.assertIn('corporate action with ex-date on the session (reference reset)', self.state(flat).limits.unknown)

    def test_dynamic_band_on_a_flat_bar_is_assumed_locked(self):
        self.bar('AAA', DAYS[0], 100, 101, 99, 100)
        band(self.desk, 'AAA', DAYS[0], None, kind='DYNAMIC')
        tick(self.desk, 'AAA', DAYS[1])
        check = self.state(dict(open_price=95, high_price=95, low_price=95, close_price=95, series='EQ'))
        self.assertEqual((check.state, check.limits.unknown), (locks.FLAT_UNKNOWN, ('dynamic band',)))

    def test_the_buy_cap_uses_only_a_band_recorded_by_decision_time(self):
        self.bar('AAA', DAYS[0], 100, 101, 99, 100)
        tick(self.desk, 'AAA', DAYS[0])
        band(self.desk, 'AAA', DAYS[0], 1, recorded_at=f'{DAYS[0]}T12:30:00+00:00')          # 18:00 IST
        cap = locks.buy_cap_at_decision(self.store.conn, self.desk, 'AAA', DAYS[0], f'{DAYS[0]}T13:30:00+00:00')
        self.assertAlmostEqual(cap['cap'], 101.0)
        self.assertIsNone(locks.buy_cap_at_decision(self.store.conn, self.desk, 'AAA', DAYS[0], f'{DAYS[0]}T12:00:00+00:00'))


class StrategyZeroLockTest(EngineFixture):
    """Both sides in the engine: deferred sells, upper-lock no-fills, the cap and the rejection."""

    def days(self, upto, special=None, symbol='AAA'):
        """Market and a normal AAA bar for DAYS[0..upto]; `special` maps index -> (o, h, l, c)."""
        for i in range(upto + 1):
            self.store.market(DAYS[i])
            o, h, l, c = (special or {}).get(i, (100, 101, 99, 100))
            self.store.bar(symbol, DAYS[i], o, h, l, c)

    def fill_aaa(self):
        """Decision on DAYS[0] (limit 102, stop 92); entry at DAYS[1]'s open 101."""
        self.days(0)
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        self.run_day(DAYS[0])
        self.store.market(DAYS[1])                                  # each session stored before its own run
        self.store.bar('AAA', DAYS[1], 101, 104, 100, 103)
        self.run_day(DAYS[1])
        self.assertEqual([e['symbol'] for e in self.events('ENTRY_FILLED')], ['AAA'])

    def events(self, *types):
        rows = self.desk.execute('SELECT * FROM strategy_paper_events ORDER BY event_id').fetchall()
        return [dict(r) | dict(detail=json.loads(r['detail'])) for r in rows if not types or r['event_type'] in types]

    def test_a_stop_hit_at_a_lower_lock_is_not_filled_and_the_stop_is_checked_again(self):
        self.fill_aaa()
        band(self.desk, 'AAA', DAYS[1], 20)                        # reference 103: lower limit 82.40 on DAYS[2]
        tick(self.desk, 'AAA', DAYS[2])
        for i, bar in ((2, (82.4, 82.4, 82.4, 82.4)), (3, (95, 96, 93, 95)), (4, (90, 91, 89, 90))):
            self.store.market(DAYS[i])
            self.store.bar('AAA', DAYS[i], *bar)
        ops = self.run_day(DAYS[2])
        self.assertEqual(ops['sells_blocked_by_lock'], [dict(position_id=f'S0:AAA:{DAYS[0]}', session=DAYS[2])])
        self.assertEqual(self.events('EXIT_FILLED'), [])
        (locked,) = [e for e in self.events('MONITORED') if e['event_date'] == DAYS[2]]
        self.assertEqual((locked['detail']['stop_hit_not_filled'], locked['detail']['lock_state']), ('stop_gap', 'LOCKED_LOWER'))
        from desk.brief import build_brief
        from tests.test_strategy0_engine import rulebook
        text = build_brief(self.store.conn, self.desk, DAYS[2], rulebook=rulebook(), health_lines=[])
        self.assertIn(f'Sells not filled at a lower lock (retried next session): 1 ({DAYS[2]})', text)
        self.run_day(DAYS[3])                                       # recovered above the stop: still open
        self.assertEqual(self.events('EXIT_FILLED'), [])
        self.run_day(DAYS[4])                                       # opens below the stop: the same rule fills
        (exit_,) = self.events('EXIT_FILLED')
        self.assertEqual((exit_['event_date'], exit_['detail']['kind'], exit_['detail']['price']), (DAYS[4], 'stop_gap', 90))

    def test_a_flat_bar_with_unknown_limits_blocks_the_sell_too(self):
        self.fill_aaa()
        self.store.market(DAYS[2])
        self.store.bar('AAA', DAYS[2], 85, 85, 85, 85)            # no band report, no tick: assume locked
        self.run_day(DAYS[2])
        self.assertEqual(self.events('EXIT_FILLED'), [])
        (locked,) = [e for e in self.events('MONITORED') if e['event_date'] == DAYS[2]]
        self.assertEqual(locked['detail']['lock_state'], 'FLAT_UNKNOWN')

    def test_a_pending_exit_waits_through_a_locked_session_and_fills_at_the_next_open(self):
        self.fill_aaa()
        for i in range(2, 12):                                     # the 10-session time limit is reached on DAYS[11]
            self.store.market(DAYS[i])
            self.store.bar('AAA', DAYS[i], 100, 101, 99, 100)
            self.run_day(DAYS[i])
        self.assertEqual([e['event_date'] for e in self.events('EXIT_ORDERED')], [DAYS[11]])
        band(self.desk, 'AAA', DAYS[11], 10)                        # lower limit 90 on DAYS[12]
        tick(self.desk, 'AAA', DAYS[12])
        self.store.market(DAYS[12])
        self.store.bar('AAA', DAYS[12], 90, 90, 90, 90)
        self.store.market(DAYS[13])
        self.store.bar('AAA', DAYS[13], 93, 94, 92.5, 93)
        self.run_day(DAYS[12])
        self.assertEqual(self.events('EXIT_FILLED'), [])
        deferred = [e for e in self.events('MONITORED') if e['detail'].get('exit_deferred')]
        self.assertEqual([(e['event_date'], e['detail']['lock_state']) for e in deferred], [(DAYS[12], 'LOCKED_LOWER')])
        self.run_day(DAYS[13])
        (exit_,) = self.events('EXIT_FILLED')
        self.assertEqual((exit_['event_date'], exit_['detail']['price'], exit_['detail']['reason']), (DAYS[13], 93, 'TIME_LIMIT'))

    def test_no_buy_at_an_upper_lock_and_it_counts_as_a_normal_no_fill(self):
        self.days(0)
        band(self.desk, 'AAA', DAYS[0], 2)                          # upper limit 102 = the limit: no cap binds
        tick(self.desk, 'AAA', DAYS[1])
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        self.run_day(DAYS[0])
        self.assertNotIn('limit_cap', self.events('CANDIDATE_ACCEPTED')[0]['detail'])
        self.store.market(DAYS[1])
        self.store.bar('AAA', DAYS[1], 102, 102, 102, 102)
        self.run_day(DAYS[1])
        (no_fill,) = self.events('ENTRY_NO_FILL')
        self.assertTrue(no_fill['detail']['reason'].startswith('LOCKED_UPPER'))
        self.assertEqual(strategy0.classify_entry('ENTRY_NO_FILL', no_fill['detail']), strategy0.ks.ATTEMPT_OK)

    def test_a_band_known_at_decision_caps_the_limit(self):
        self.days(0)
        band(self.desk, 'AAA', DAYS[0], 1)                          # 18:00 IST; decided 19:00 IST: upper 101
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        self.run_day(DAYS[0])
        cap = self.events('CANDIDATE_ACCEPTED')[0]['detail']['limit_cap']
        self.assertAlmostEqual(cap['cap'], 101.0)
        self.store.market(DAYS[1])
        self.store.bar('AAA', DAYS[1], 101.5, 103, 100.5, 101)      # uncapped: FILL_OPEN 101.5; capped: limit 101
        self.run_day(DAYS[1])
        (entry,) = self.events('ENTRY_FILLED')
        self.assertEqual((entry['detail']['status'], entry['detail']['price']), ('FILL_LIMIT', 101.0))
        self.assertEqual((entry['detail']['limit'], entry['detail']['uncapped_limit']), (101.0, 102.0))

    def test_a_limit_above_a_band_unknown_at_decision_is_a_rejected_order(self):
        self.days(0)
        band(self.desk, 'AAA', DAYS[0], 1, recorded_at=f'{DAYS[0]}T15:00:00+00:00')   # 20:30 IST: after deciding
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        self.run_day(DAYS[0])
        self.assertNotIn('limit_cap', self.events('CANDIDATE_ACCEPTED')[0]['detail'])
        self.store.market(DAYS[1])
        self.store.bar('AAA', DAYS[1], 100.5, 101, 100, 100.8)
        self.run_day(DAYS[1])
        (no_fill,) = self.events('ENTRY_NO_FILL')
        self.assertTrue(no_fill['detail']['reason'].startswith('REJECTED'))
        self.assertEqual(strategy0.classify_entry('ENTRY_NO_FILL', no_fill['detail']), strategy0.ks.ATTEMPT_OK)


class ManualBookLockTest(unittest.TestCase):
    DAYS = ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06']

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        self.costs = make_test_costs()

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def bar(self, day, o, h, l, c, symbol='MANU'):
        self.praman.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                            'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                            "(?,?,?,?,?,?,?,?,1000,'EQ','fixture',?)", (symbol, day, day, o, h, l, c, c, day))
        self.praman.commit()

    def trade(self):
        d = self.DAYS
        thesis_id = jstore.record_thesis(
            self.desk, symbol='MANU', evidence_cutoff=d[0], hypotheses=[dict(statement='s', test='t', monitor='m')],
            drivers=['d'], horizon='2026-12-31', invalidation_conditions=['i'], exit_price='stop or target',
            exit_time='exit at the next session open after the horizon', exit_evidence='e', exit_risk='r',
            exit_portfolio='p', planned_entry=100.0, planned_stop=92.0, planned_target=120.0, sector='Test')
        decision_id = jstore.record_decision(
            self.desk, symbol='MANU', as_of_date=d[0], thesis_id=thesis_id, evidence_bundle_hash='h', gate_results={},
            state='ELIGIBLE', rulebook_version='v', rulebook_hash='r', cost_config_version='c', cost_config_hash='k',
            code_commit='c', praman_watermark='w', desk_watermark_value='d', as_of_is_live=True, isin_map_built_at='x',
            position_size=10, stress_loss_inr=100.0)
        trade_id = f'MANU:{thesis_id}'
        jstore.open_paper_trade(self.desk, trade_id=trade_id, decision_id=decision_id, event_date=d[1], price=100.0,
                                quantity=10, stop=92.0, target=120.0, buy_cost_inr=1.0, cost_config_hash='k')
        return trade_id

    def close_event(self, trade_id):
        row = self.desk.execute("SELECT event_date, price FROM paper_trade_events WHERE trade_id=? AND event_type='CLOSE'",
                                (trade_id,)).fetchone()
        return tuple(row) if row else None

    def test_monitor_skips_a_lower_lock_and_fills_the_stop_on_the_next_session(self):
        from desk.brief import manual_monitor_lines
        from desk.monitor import run_monitor
        d = self.DAYS
        self.bar(d[0], 100, 101, 99, 100)
        self.bar(d[1], 100, 101, 99, 100)
        self.bar(d[2], 90, 90, 90, 90)                              # band 10% on reference 100: locked at 90
        self.bar(d[3], 88, 89, 87, 88)
        band(self.desk, 'MANU', d[1], 10)
        tick(self.desk, 'MANU', d[2])
        trade_id = self.trade()
        report = run_monitor(self.praman, self.desk, d[3])
        self.assertEqual([(x['session'], x['exit'], x['lock_state']) for x in report['sells_blocked_by_lock']],
                         [(d[2], 'stop (stop_gap)', 'LOCKED_LOWER')])
        self.assertEqual(self.close_event(trade_id), (d[3], 88.0))
        self.assertIn(f'{trade_id}: stop (stop_gap) exit not filled on {d[2]}: LOCKED_LOWER',
                      '\n'.join(manual_monitor_lines(self.desk, d[3])))

    def test_a_manual_close_waits_through_a_lower_lock(self):
        from desk.paper.close import PendingClose, close_approved_trade, resume_pending_close
        d = self.DAYS
        for day, bar in ((d[0], (100, 101, 99, 100)), (d[1], (100, 101, 99, 100)), (d[2], (95, 95, 95, 95)),
                         (d[3], (96, 97, 95, 96))):
            self.bar(day, *bar)
        trade_id = self.trade()                                      # d[2] flat, no band: assume locked
        first = close_approved_trade(self.praman, self.desk, trade_id, reason='done', costs=self.costs,
                                     cost_config_hash='k', now=datetime.fromisoformat(d[1] + 'T12:00:00+00:00'))
        self.assertIsInstance(first, PendingClose)
        deferred = self.desk.execute("SELECT detail FROM journal_events WHERE event_type='PAPER_CLOSE_DEFERRED'").fetchall()
        self.assertEqual([json.loads(r['detail'])['session'] for r in deferred], [d[2]])
        resume_pending_close(self.praman, self.desk, trade_id, d[1], 'done', self.costs, 'k')
        self.assertEqual(self.close_event(trade_id), (d[3], 96.0))


class ManualOpenLockTest(unittest.TestCase):
    """A manual buy at an upper lock is a normal no-fill (P8-064)."""

    def test_paper_open_does_not_fill_at_an_upper_lock(self):
        from tests.test_paper_limit_entry import D, F, PaperLimitEntryTest      # its fixture: ATR20 = 4
        from desk.paper.open import NoFill, open_approved_decision
        case = PaperLimitEntryTest()
        case.setUp()
        self.addCleanup(case.tearDown)
        band(case.desk, 'LIMITCO', D, 2)                            # upper 102 = the limit 100 + 0.5 x ATR 4
        tick(case.desk, 'LIMITCO', F)
        case.bar(F, 102, 102, 102, 102)
        decision_id = case.decision()
        result = open_approved_decision(case.praman, case.desk, decision_id, costs=case.costs, cost_config_hash='c',
                                        now=datetime.fromisoformat(D + 'T12:00:00+00:00'))
        self.assertIsInstance(result, NoFill)
        self.assertTrue(result.reason.startswith('LOCKED_UPPER'))


if __name__ == '__main__':
    unittest.main()
