"""The user-only smoke test uses mocked market data, never a real login."""
import contextlib
import io
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from scripts import angel_connection_test as smoke
from shared.market_time import IST


class AngelSmokeTest(unittest.TestCase):
    def run_smoke(self, hour):
        now = datetime(2026, 10, 13, hour, 0, tzinfo=IST)
        client = Mock()
        client.quote.return_value = {'exchange_timestamp': now.isoformat(), 'recorded_at': now.isoformat(), 'price': 800}
        client.candles.return_value = [{'timestamp': '2026-09-01T09:15:00+05:30', 'open': 700, 'high': 702, 'low': 699, 'close': 701}]
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), patch.object(smoke, 'datetime', wraps=datetime) as clock, \
                contextlib.redirect_stdout(output):
            clock.now.return_value = now
            self.assertEqual(smoke.main(), 0)
        client.login.assert_called_once()
        client.logout.assert_called_once()
        client.quote.assert_called_once_with('SBIN', as_of='2026-10-13')
        client.candles.assert_called_once_with('SBIN', '2026-09-01', as_of='2026-10-13')
        self.assertEqual(len(output.getvalue().splitlines()), 2)
        for line in output.getvalue().splitlines():
            timestamp, *prices = line.split()
            datetime.fromisoformat(timestamp)
            self.assertTrue(all(float(p) > 0 for p in prices))
        return client

    def test_open_market_streams_for_thirty_seconds(self):
        client = self.run_smoke(10)
        client.stream.assert_called_once_with(['SBIN'], smoke._print_tick, as_of='2026-10-13', seconds=30)

    def test_closed_market_skips_feed(self):
        self.run_smoke(18).stream.assert_not_called()

    def test_stale_or_absent_quote_does_not_claim_market_is_open(self):
        now = datetime(2026, 10, 13, 10, 0, tzinfo=IST)
        for quote in ({}, {'exchange_timestamp': '2026-10-12T15:30:00+05:30'}):
            self.assertFalse(smoke._market_open(now, quote))

    def test_failure_still_logs_out_without_printing_exception(self):
        client = Mock()
        client.login.side_effect = RuntimeError('synthetic failure')
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.assertEqual(smoke.main(), 1)
        self.assertEqual(output.getvalue(), '')
        client.logout.assert_called_once()
