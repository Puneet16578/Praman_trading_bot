"""R1 capacity probe: offline only, with a fake client and clock; no login, network or real store."""
import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from desk.angel_market_data import AngelError
from scripts import angel_stream_capacity_test as probe
from shared.market_time import IST


def bhavcopy_db(path, symbols, today='2026-10-14', sessions=20):
    """A minimal bhavcopy store: `symbols` maps symbol -> daily turnover for the sessions before today."""
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE bhavcopy (row_id INTEGER PRIMARY KEY, symbol TEXT, series TEXT, event_date TEXT, '
                 'knowledge_date TEXT, close_price REAL, traded_qty REAL)')
    days, day = [], date.fromisoformat(today)
    while len(days) < sessions:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            days.append(day.isoformat())
    for symbol, turnover in symbols.items():
        for d in days:
            conn.execute('INSERT INTO bhavcopy (symbol, series, event_date, knowledge_date, close_price, traded_qty) '
                         "VALUES (?, 'EQ', ?, ?, 100, ?)", (symbol, d, d, turnover / 100))
    conn.commit()
    return conn, days


class LiquidityRankingTest(unittest.TestCase):
    def test_ranks_by_turnover_known_before_today_with_coverage_and_tie_break(self):
        with tempfile.TemporaryDirectory() as folder:
            conn, days = bhavcopy_db(Path(folder) / 'p.db', {'BBB': 200, 'AAA': 100, 'CCC': 100, 'FFF': 50, 'DDD': 500})
            today = '2026-10-14'
            conn.execute("DELETE FROM bhavcopy WHERE symbol = 'DDD' AND event_date IN (?, ?, ?)", tuple(days[:3]))
            conn.executemany('INSERT INTO bhavcopy (symbol, series, event_date, knowledge_date, close_price, traded_qty) '
                             'VALUES (?, ?, ?, ?, 100, ?)',
                             [('EEE', 'EQ', today, today, 1e9),            # today's session: unknown before the open
                              ('FFF', 'EQ', days[0], today, 1e9),          # a vintage recorded today: ignored
                              ('BEX', 'BE', days[0], days[0], 1e9)])       # not the EQ series
            conn.commit()
            self.assertEqual(probe.liquid_symbols(conn, today), ['BBB', 'AAA', 'CCC', 'FFF'])  # DDD has 17 of 20
            conn.close()


class PercentileTest(unittest.TestCase):
    def test_linear_interpolation_like_numpy(self):
        self.assertEqual(probe.percentile([4, 1, 3, 2], 50), 2.5)
        self.assertAlmostEqual(probe.percentile([1, 2, 3, 4], 95), 3.85)
        self.assertIsNone(probe.percentile([], 95))


class EvaluateTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = probe.TickStore(Path(folder.name) / 'ticks.sqlite')
        self.addCleanup(self.store.close)
        self.start = datetime(2026, 10, 14, 10, 0, tzinfo=IST)

    def tier(self, lag=lambda t: 0.3, seconds=300, symbols=('S1', 'S2'), skip=()):
        stats = probe.TierStats(2, list(symbols), self.store, self.start)
        for t in range(seconds):
            if t in skip:
                continue
            received = self.start + timedelta(seconds=t)
            for s in symbols:
                stats.on_tick(dict(symbol=s, price=10.0, recorded_at=received.isoformat(),
                                   timestamp=(received - timedelta(seconds=lag(t))).isoformat()))
        stats.finish(self.start + timedelta(seconds=seconds))
        return stats

    def test_steady_feed_passes(self):
        result = probe.evaluate(self.tier(), ['S1', 'S2'])
        self.assertEqual((result['outcome'], result['reasons']), ('PASS', []))
        self.assertAlmostEqual(result['lag_p95'], 0.3)
        self.assertEqual((result['initial_snapshots'], result['sentinels_ticking']), (2, 2))

    def test_each_failure_is_named(self):
        cases = [
            (dict(lag=lambda t: 2.5), 'receipt lag p95'),
            (dict(lag=lambda t: 0.3 if t < 280 else 30.0), 'receipt lag p99'),
            (dict(lag=lambda t: 0.1 + t / 60), 'receipt lag grew'),
            (dict(skip=range(100, 140)), 'no tick from any symbol for'),
        ]
        for kwargs, words in cases:
            with self.subTest(words=words):
                result = probe.evaluate(self.tier(**kwargs), ['S1', 'S2'])
                self.assertEqual(result['outcome'], 'FAIL')
                self.assertTrue(any(words in r for r in result['reasons']), result['reasons'])

    def test_feed_stop_and_silent_sentinel_fail(self):
        stats = self.tier()
        stats.feed_error = True
        self.assertIn('the feed stopped, failed or was interrupted', probe.evaluate(stats, ['S1'])['reasons'])
        quiet = self.tier(symbols=('S1',))
        quiet.counts['S9'] = 0
        result = probe.evaluate(quiet, ['S1', 'S9'])
        self.assertIn('1 liquid sentinel(s) never ticked', result['reasons'])

    def test_old_first_snapshot_and_negative_lags_stay_out_of_the_lag_statistics(self):
        stats = probe.TierStats(2, ['S1'], self.store, self.start)
        for t, lag in ((0, 900.0), (1, -0.5), (2, 0.2), (3, 0.2)):   # first: a minutes-old snapshot
            received = self.start + timedelta(seconds=t)
            stats.on_tick(dict(symbol='S1', price=1.0, recorded_at=received.isoformat(),
                               timestamp=(received - timedelta(seconds=lag)).isoformat()))
        stats.finish(self.start + timedelta(seconds=4))
        result = probe.evaluate(stats, ['S1'])
        self.assertEqual((result['initial_snapshots'], result['negative_lags'], result['lag_max']), (1, 1, 0.2))


class FakeClock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at


class FakeClient:
    """Login/logout/master/quote/stream with synthetic ticks; the clock moves with the stream."""

    def __init__(self, clock, lag_by_tier=None, fail_tiers=(), quote_age=5):
        self.clock, self.lag_by_tier, self.fail_tiers, self.quote_age = clock, lag_by_tier or {}, fail_tiers, quote_age
        self.calls = []

    def login(self):
        self.calls.append('login')

    def logout(self):
        self.calls.append('logout')

    def download_scrip_master(self, symbols, *, as_of):
        return dict(mapped={s: str(i) for i, s in enumerate(symbols) if s != 'NOMAP'},
                    unmapped=[s for s in symbols if s == 'NOMAP'], observed_at=self.clock().isoformat())

    def quote(self, symbol, *, as_of):
        return dict(exchange_timestamp=(self.clock() - timedelta(seconds=self.quote_age)).isoformat(),
                    price=1.0, recorded_at=self.clock().isoformat())

    def stream(self, symbols, on_tick, *, as_of, seconds):
        self.calls.append(('stream', len(symbols), seconds))
        if len(symbols) in self.fail_tiers:
            self.clock.at += timedelta(seconds=5)
            raise AngelError('Market feed stopped or failed.')
        lag, start = self.lag_by_tier.get(len(symbols), 0.2), self.clock()
        for t in range(seconds):
            received = start + timedelta(seconds=t)
            for s in symbols[:10] + [symbols[10 + t % (len(symbols) - 10)]]:
                on_tick(dict(symbol=s, price=123.45, recorded_at=received.isoformat(),
                             timestamp=(received - timedelta(seconds=lag)).isoformat()))
        self.clock.at = start + timedelta(seconds=seconds)


class ProbeRunTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        ranked = {f'S{i:03d}': 10_000 - i for i in range(120)} | {'NOMAP': 1}
        conn, _ = bhavcopy_db(self.root / 'praman.db', ranked)
        conn.close()
        self.nightly = Mock(return_value=False)
        for target, value in (('PRAMAN_DB', self.root / 'praman.db'), ('PROBE_DIR', self.root / 'probe'),
                              ('TIERS', (25, 50, 100)), ('TIER_SECONDS', 300), ('preflight', lambda: []),
                              ('nightly_running', self.nightly), ('_prevent_sleep', contextlib.nullcontext)):
            patcher = patch.object(probe, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_probe(self, client, clock, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = probe.run(client, now=clock, **kwargs)
        summaries = sorted(probe.logs_dir().glob('angel_capacity_*.json'))
        summary = json.loads(summaries[-1].read_text(encoding='utf-8')) if summaries else None
        for path in summaries:
            path.unlink()
        return code, summary, output.getvalue()

    def test_only_25_does_not_escalate_after_passing(self):
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock)
        code, summary, _ = self.run_probe(client, clock, tiers=(25,))
        self.assertEqual(code, 0)
        self.assertEqual([t['tier'] for t in summary['tiers']], [25])
        self.assertEqual([c for c in client.calls if c[0] == 'stream'], [('stream', 25, 300)])

    def test_safe_failure_category_is_persisted_and_printed(self):
        from desk.angel_market_data import _Failure
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock)
        client.stream = Mock(side_effect=_Failure('ws_closed'))
        _, summary, output = self.run_probe(client, clock, tiers=(25,))
        self.assertEqual(summary['tiers'][0]['feed_diagnostic'],
                         {'category': 'ws_closed', 'http_status': None})
        self.assertIn('feed category: ws_closed', output)

    def test_escalates_until_the_first_failed_tier_and_keeps_prices_out_of_the_summary(self):
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock, lag_by_tier={100: 3.0})
        code, summary, output = self.run_probe(client, clock)
        self.assertEqual(code, 0)
        self.assertEqual([(t['tier'], t['outcome']) for t in summary['tiers']], [(25, 'PASS'), (50, 'PASS'), (100, 'FAIL')])
        self.assertEqual((summary['stopped'], summary['largest_passing_tier']), ('tier 100 failed', 50))
        self.assertEqual(summary['sentinel_symbols'], [f'S{i:03d}' for i in range(10)])
        self.assertEqual((summary['mapped'], summary['unmapped']), (120, ['NOMAP']))   # reported, never streamed
        self.assertEqual([c for c in client.calls if c[0] == 'stream'], [('stream', 25, 300), ('stream', 50, 300),
                                                                         ('stream', 100, 300)])
        self.assertEqual((client.calls[0], client.calls[-1]), ('login', 'logout'))
        text = json.dumps(summary)
        self.assertNotIn('123.45', text)
        self.assertNotIn('price', text)
        self.assertNotIn('123.45', output)
        ticks = sqlite3.connect(summary['tick_file'])           # raw ticks only in the probe's own file
        try:
            self.assertEqual(ticks.execute('SELECT COUNT(*) FROM ticks').fetchone()[0],
                             sum(t['ticks'] for t in summary['tiers']))
        finally:
            ticks.close()

    def test_a_feed_failure_stops_escalation_and_still_logs_out(self):
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock, fail_tiers=(25,))
        code, summary, _ = self.run_probe(client, clock)
        self.assertEqual((code, summary['stopped'], summary['largest_passing_tier']), (0, 'tier 25 failed', None))
        self.assertIn('the feed stopped, failed or was interrupted', summary['tiers'][0]['reasons'])
        self.assertEqual(client.calls[-1], 'logout')

    def test_no_stream_without_a_fresh_quote_or_time_to_finish_by_close(self):
        for at, age, words in ((datetime(2026, 10, 14, 10, 0, tzinfo=IST), 600, 'market not confirmed open'),
                               (datetime(2026, 10, 14, 15, 26, tzinfo=IST), 5, 'could not finish by 15:30')):
            with self.subTest(words=words):
                clock = FakeClock(at)
                client = FakeClient(clock, quote_age=age)
                code, summary, _ = self.run_probe(client, clock)
                self.assertEqual(code, 0)
                self.assertIn(words, summary['stopped'])
                self.assertFalse([c for c in client.calls if c[0] == 'stream'])
                self.assertEqual(client.calls[-1], 'logout')

    def test_the_nightly_starting_between_tiers_stops_the_probe(self):
        self.nightly.side_effect = [False, True]
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock)
        _, summary, _ = self.run_probe(client, clock)
        self.assertEqual([t['tier'] for t in summary['tiers']], [25])
        self.assertIn('the nightly started', summary['stopped'])

    def test_refusals_happen_before_any_login(self):
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        for reasons, at in ((['HEAD is not master (other)'], clock.at), ([], datetime(2026, 10, 14, 9, 10, tzinfo=IST)),
                            ([], datetime(2026, 10, 17, 11, 0, tzinfo=IST))):          # 17 October 2026 is a Saturday
            with self.subTest(reasons=reasons, at=at), patch.object(probe, 'preflight', return_value=reasons):
                client = Mock()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(probe.run(client, now=FakeClock(at)), 2)
                client.login.assert_not_called()
                self.assertIn('Not started', output.getvalue())

    def test_an_interrupted_login_returns_failure_and_still_writes_the_summary(self):
        clock = FakeClock(datetime(2026, 10, 14, 10, 0, tzinfo=IST))
        client = FakeClient(clock)
        client.login = Mock(side_effect=KeyboardInterrupt)
        code, summary, output = self.run_probe(client, clock)
        self.assertEqual((code, summary['stopped']), (1, 'failed or interrupted (no detail is printed)'))
        self.assertNotIn('Traceback', output)


class PreflightTest(unittest.TestCase):
    def test_dirty_tree_other_branch_or_nightly_state_refuse(self):
        cases = [(dict(branch='other'), 'HEAD is not master (other)'),
                 (dict(dirty=['desk/x.py']), 'uncommitted changes: desk/x.py'),
                 (dict(dirty=None), 'the working tree could not be checked'),
                 (dict(running=True), 'the nightly is running'),
                 (dict(running=None), "the nightly's state could not be read")]
        for change, words in cases:
            state = dict(branch='master', dirty=[], running=False) | change
            with self.subTest(words=words), patch.object(probe, 'head_branch', return_value=state['branch']), \
                    patch.object(probe, 'uncommitted_nightly_inputs', return_value=state['dirty']), \
                    patch.object(probe, 'nightly_running', return_value=state['running']):
                self.assertEqual(probe.preflight(), [words])
        with patch.object(probe, 'head_branch', return_value='master'), \
                patch.object(probe, 'uncommitted_nightly_inputs', return_value=[]), \
                patch.object(probe, 'nightly_running', return_value=False):
            self.assertEqual(probe.preflight(), [])

    def test_nightly_state_is_read_with_schtasks_only(self):
        done = Mock(returncode=0, stdout='"\\PramanDailyIngest","14-10-2026 18:00:00","Running"\n')
        with patch.object(probe.subprocess, 'run', return_value=done) as run:
            self.assertTrue(probe.nightly_running())
        self.assertEqual(run.call_args.args[0][:2], ['schtasks', '/Query'])
        done.stdout = '"\\PramanDailyIngest","14-10-2026 18:00:00","Ready"\n'
        with patch.object(probe.subprocess, 'run', return_value=done):
            self.assertFalse(probe.nightly_running())
        with patch.object(probe.subprocess, 'run', side_effect=OSError):
            self.assertIsNone(probe.nightly_running())


if __name__ == '__main__':
    unittest.main()


class FeedCloseTextTest(unittest.TestCase):
    def test_the_tier_line_says_who_ended_the_feed(self):
        self.assertEqual(probe.feed_close_text(dict(closed_by='client', connected_seconds=41.04, close_code=None,
                                                    stopped_because='unexpected text message',
                                                    stopped_message_bytes=37)),
                         ' | feed stopped by us: unexpected text message (37 bytes, text never shown) after 41.0 s')
        self.assertEqual(probe.feed_close_text(dict(closed_by='client', connected_seconds=600.0, close_code=None,
                                                    stopped_because='time up', stopped_message_bytes=None)),
                         ' | feed stopped by us: time up after 600.0 s')
        self.assertEqual(probe.feed_close_text(dict(closed_by='server', connected_seconds=239.4, close_code=1008)),
                         ' | feed closed by server after 239.4 s (code 1008)')
        self.assertEqual(probe.feed_close_text(dict(closed_by='client', connected_seconds=600.0, close_code=None)),
                         ' | feed closed by client after 600.0 s (code none)')     # summaries written before P8-079
        self.assertEqual(probe.feed_close_text(None), '')
