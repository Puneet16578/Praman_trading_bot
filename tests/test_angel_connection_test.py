"""The user-only smoke test uses mocked market data, never a real login."""
import contextlib
import io
import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from desk import angel_market_data as angel
from desk.angel_market_data import AngelError
from scripts import angel_connection_test as smoke
from shared.market_time import IST

READY = [('Python', True, 'x'), ('smartapi-python', True, '1.5.5'), ('logzero', True, '1.7.0'),
         ('websocket-client', True, '1.8.0'), ('SDK load', True, 'ok')]


class AngelSmokeTest(unittest.TestCase):
    def run_smoke(self, hour):
        now = datetime(2026, 10, 13, hour, 0, tzinfo=IST)
        client = Mock()
        client.quote.return_value = {'exchange_timestamp': now.isoformat(), 'recorded_at': now.isoformat(), 'price': 800}
        client.candles.return_value = [{'timestamp': '2026-09-01T09:15:00+05:30', 'open': 700, 'high': 702, 'low': 699, 'close': 701}]
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), patch.object(smoke, 'datetime', wraps=datetime) as clock, \
                patch.object(smoke, 'check_setup', return_value=READY), \
                patch.object(smoke, 'recent_session', return_value='2026-10-12'), contextlib.redirect_stdout(output):
            clock.now.return_value = now
            self.assertEqual(smoke.main([]), 0)
        client.login.assert_called_once()
        client.logout.assert_called_once()
        client.quote.assert_called_once_with('SBIN', as_of='2026-10-13')
        client.candles.assert_called_once_with('SBIN', '2026-10-12', as_of='2026-10-13')
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines[:2]:
            timestamp, *prices = line.split()
            datetime.fromisoformat(timestamp)
            self.assertTrue(all(float(p) > 0 for p in prices))
        self.assertTrue(lines[2].startswith('Connection test completed: login, quote, candles'))
        return client, lines[2]

    def test_open_market_streams_for_thirty_seconds(self):
        client, last = self.run_smoke(10)
        client.stream.assert_called_once_with(['SBIN'], smoke._print_tick, as_of='2026-10-13', seconds=30)
        self.assertIn('30 seconds of live feed', last)

    def test_closed_market_skips_feed(self):
        client, last = self.run_smoke(18)
        client.stream.assert_not_called()
        self.assertIn('live feed skipped', last)

    def test_stale_or_absent_quote_does_not_claim_market_is_open(self):
        now = datetime(2026, 10, 13, 10, 0, tzinfo=IST)
        for quote in ({}, {'exchange_timestamp': '2026-10-12T15:30:00+05:30'}):
            self.assertFalse(smoke._market_open(now, quote))

    def stop_line(self, error, stage='login'):
        client = Mock()
        client.login.side_effect = error
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), patch.object(smoke, 'check_setup', return_value=READY), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.assertEqual(smoke.main([]), 1)
        client.logout.assert_called_once()
        return output.getvalue().splitlines()

    def test_a_failure_says_why_in_one_plain_line_and_still_logs_out(self):
        """P8-071: the exit used to be silent."""
        lines = self.stop_line(RuntimeError('synthetic secret-bearing failure'))
        self.assertEqual(lines, ['Stopped at login: unexpected error (RuntimeError)'])
        for error, words in ((AngelError('Set ANGEL_API_KEY in the environment.'), 'ANGEL_API_KEY is not set in this window'),
                             (AngelError('Install the pinned optional Angel requirements.'), 'Angel library not installed'),
                             (AngelError('Login failed; use a private interactive terminal.'), 'login failed'),
                             (KeyboardInterrupt(), 'interrupted')):
            with self.subTest(words=words):
                (line,) = self.stop_line(error)
                self.assertTrue(line.startswith('Stopped at login: ') and words in line, line)

    def test_an_incomplete_setup_stops_before_any_login(self):
        output = io.StringIO()
        missing = READY[:1] + [('smartapi-python', False, 'not installed: see setup step 1')] + READY[2:]
        with patch.object(smoke, 'AngelMarketData') as constructor, patch.object(smoke, 'check_setup', return_value=missing), \
                contextlib.redirect_stdout(output):
            self.assertEqual(smoke.main([]), 1)
        constructor.assert_not_called()
        self.assertEqual(output.getvalue().splitlines(),
                         ['Stopped before login: Angel library not installed or incomplete: '
                          'smartapi-python (not installed: see setup step 1)'])


class CheckModeTest(unittest.TestCase):
    def test_check_reports_each_item_and_never_reads_the_key(self):
        class NoKey(dict):
            def _guard(self, key):
                if key == 'ANGEL_API_KEY':
                    raise AssertionError('the check read ANGEL_API_KEY')
            def get(self, key, default=None):
                self._guard(key)
                return super().get(key, default)
            def __getitem__(self, key):
                self._guard(key)
                return super().__getitem__(key)
            def __contains__(self, key):
                self._guard(key)
                return super().__contains__(key)
        output = io.StringIO()
        with patch.object(angel._os, 'environ', NoKey(os.environ)), patch.object(angel, '_sdk_types', return_value=(None, None)), \
                patch.object(angel._metadata, 'version', side_effect=lambda n: {'smartapi-python': '1.5.5'}.get(n, '1.0')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(smoke.main(['--check']), 0)
        text = output.getvalue()
        self.assertIn('OK      smartapi-python: 1.5.5', text)
        self.assertIn('Setup ready for the connection test.', text)
        self.assertIn('ANGEL_API_KEY: not checked here', text)

    def test_a_wrong_or_missing_package_is_missing(self):
        def version(name):
            if name == 'logzero':
                raise angel._metadata.PackageNotFoundError(name)
            return '1.5.4' if name == 'smartapi-python' else '1.0'
        with patch.object(angel._metadata, 'version', side_effect=version), \
                patch.object(angel, '_sdk_types', side_effect=AngelError('Install the pinned optional Angel requirements.')):
            results = {item: (ok, detail) for item, ok, detail in angel.check_setup()}
        self.assertEqual(results['smartapi-python'], (False, '1.5.4 installed, 1.5.5 required: see setup step 1'))
        self.assertEqual(results['logzero'], (False, 'not installed: see setup step 1'))
        self.assertFalse(results['SDK load'][0])
        output = io.StringIO()
        with patch.object(smoke, 'check_setup', return_value=[('logzero', False, 'not installed: see setup step 1')]), \
                contextlib.redirect_stdout(output):
            self.assertEqual(smoke.main(['--check']), 1)
        self.assertIn('MISSING logzero: not installed: see setup step 1', output.getvalue())


if __name__ == '__main__':
    unittest.main()


class FeedCloseLineTest(unittest.TestCase):
    def test_a_feed_failure_prints_one_close_summary_line_without_text(self):
        failure = angel._Failure('ws_closed')
        failure.stream_summary = dict(closed_by='server', close_code=1008, close_reason='withheld', close_reason_bytes=12,
                                      connected_seconds=239.4, seconds_since_last_message=0.4, seconds_since_ping_sent=9.1,
                                      seconds_since_pong_received=None, seconds_since_text_ping_sent=9.1,
                                      seconds_since_text_pong_received=19.0,
                                      frames=dict(binary=900, text_pong=23, text_other=0, server_ping=0, pong=0))
        client = Mock()
        now = datetime(2026, 10, 13, 10, 0, tzinfo=IST)
        client.quote.return_value = {'exchange_timestamp': now.isoformat(), 'recorded_at': now.isoformat(), 'price': 800}
        client.candles.return_value = [{'timestamp': '2026-09-01T09:15:00+05:30', 'open': 700, 'high': 702, 'low': 699, 'close': 701}]
        client.stream.side_effect = failure
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), patch.object(smoke, 'datetime', wraps=datetime) as clock,                 patch.object(smoke, 'check_setup', return_value=READY), patch.object(smoke, 'recent_session', return_value='2026-10-12'),                 contextlib.redirect_stdout(output):
            clock.now.return_value = now
            self.assertEqual(smoke.main([]), 1)
        lines = output.getvalue().splitlines()
        self.assertEqual(lines[-2], 'Stopped at live feed: WebSocket disconnected.')
        self.assertTrue(lines[-1].startswith('Feed close: by server, code 1008, reason withheld (12 bytes, text never shown); '
                                             'connected 239.4s; since last message 0.4s, PING sent 9.1s, PONG back never'))
