"""Credential-free regressions for malformed master rows and transport diagnostics."""
import unittest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from desk import angel_market_data as a
from shared.market_time import IST
from scripts import angel_connection_test as smoke
from scripts import angel_stream_capacity_test as capacity

DAY = '2026-10-14'
NOW = datetime(2026, 10, 14, 10, tzinfo=IST)


class DiagnosticsTest(unittest.TestCase):
    def setUp(self):
        for p in (patch.object(a, '_now', return_value=NOW), patch.object(a, '_pace')):
            p.start()
            self.addCleanup(p.stop)
        self.client = a.AngelMarketData()

    def response(self, payload, status=200):
        r = MagicMock(status_code=status)
        r.__enter__.return_value = r
        r.json.return_value = payload
        return r

    def test_malformed_rows_do_not_destroy_valid_exact_mapping(self):
        rows = [None, [], 42, {'exch_seg': 'NSE', 'symbol': None},
                {'symbol': 'SBIN-EQ', 'token': '3045', 'exch_seg': 'NSE'},
                {'symbol': 'BAD-EQ', 'token': True, 'exch_seg': 'NSE'},
                {'symbol': 'ZERO-EQ', 'token': '0', 'exch_seg': 'NSE'}]
        with patch.object(a._requests, 'get', return_value=self.response(rows)):
            result = self.client.download_scrip_master(['SBIN', 'BAD', 'ZERO'], as_of=DAY)
        self.assertEqual(result['mapped'], {'SBIN': '3045'})
        self.assertEqual(result['unmapped'], ['BAD', 'ZERO'])

    def test_master_error_categories_and_no_stale_fallback(self):
        for error, category in ((a._requests.exceptions.Timeout('private'), 'timeout'),
                                (a._requests.exceptions.SSLError('private'), 'tls'),
                                (a._requests.exceptions.ConnectionError('private'), 'network')):
            with self.subTest(category=category), patch.object(a._requests, 'get', side_effect=error):
                self.client._master_day, self.client._master = '2026-10-13', {'SBIN': '3045'}
                with self.assertRaises(a.AngelError) as caught:
                    self.client.download_scrip_master(['SBIN'], as_of=DAY)
                self.assertEqual(caught.exception.category, category)
                self.assertNotIn('private', str(caught.exception))
                self.assertNotEqual(self.client._master_day, DAY)

    def test_http_json_and_structure_are_distinct(self):
        invalid = self.response(None)
        invalid.json.side_effect = ValueError('private')
        for response, category in ((self.response([], 503), 'http'), (invalid, 'json'),
                                   (self.response({}), 'structure')):
            with self.subTest(category=category), patch.object(a._requests, 'get', return_value=response):
                with self.assertRaises(a.AngelError) as caught:
                    self.client.download_scrip_master(['SBIN'], as_of=DAY)
                self.assertEqual(caught.exception.category, category)
                self.assertNotIn('private', str(caught.exception))

    def test_api_rejection_survives_sdk_call_boundary(self):
        sdk = SimpleNamespace(api_key='', access_token='', clientLocalIp='', clientPublicIp='', clientMacAddress='')
        response = self.response({'status': False, 'message': 'private', 'errorcode': 'private'})
        with patch.object(a._requests, 'request', return_value=response):
            with self.assertRaises(a.AngelError) as caught:
                self.client._call(lambda: a._request(sdk, 'api.candle.data', 'POST', {}))
        self.assertEqual(caught.exception.category, 'api_rejection')
        self.assertNotIn('private', str(caught.exception))

    def test_ambiguous_and_malformed_same_identity_fail_closed(self):
        rows = [{'symbol': s + '-EQ', 'token': t, 'exch_seg': 'NSE'} for s, t in
                [('SBIN', '3045'), ('SBIN', None), ('DUP', '1'), ('DUP', '2'),
                 ('ALIAS1', '3'), ('ALIAS2', '3'), ('UNICODE', '\u0661'), ('GOOD', '4')]]
        with patch.object(a._requests, 'get', return_value=self.response(rows)) as get:
            result = self.client.download_scrip_master(['SBIN', 'DUP', 'ALIAS1', 'ALIAS2', 'UNICODE', 'GOOD', 'MISSING'], as_of=DAY)
        self.assertEqual(result['mapped'], {'GOOD': '4'})
        self.assertEqual(len(result['unmapped']), 6)
        self.assertEqual(get.call_args.kwargs['timeout'], (10, 60))
        self.assertTrue(get.call_args.kwargs['verify'])
        self.assertFalse(get.call_args.kwargs['allow_redirects'])

    def test_rest_transport_status_and_json_categories(self):
        sdk = SimpleNamespace(api_key='', access_token='', clientLocalIp='', clientPublicIp='', clientMacAddress='')
        invalid = self.response(None)
        invalid.json.side_effect = ValueError('private')
        cases = [(self.response(None, 429), 'http'), (self.response(None, 302), 'http'),
                 (invalid, 'json'), (self.response([]), 'structure'),
                 (self.response({'status': True}), 'structure'),
                 (a._requests.exceptions.Timeout('private'), 'timeout'),
                 (a._requests.exceptions.SSLError('private'), 'tls')]
        for value, expected in cases:
            kwargs = {'side_effect': value} if isinstance(value, Exception) else {'return_value': value}
            with self.subTest(category=expected), patch.object(a._requests, 'request', **kwargs):
                with self.assertRaises(a.AngelError) as caught:
                    a._request(sdk, 'api.candle.data', 'POST')
                self.assertEqual(caught.exception.category, expected)
                self.assertNotIn('private', str(caught.exception))
                if expected == 'http':
                    self.assertEqual(caught.exception.http_status, value.status_code)

    def active_client(self):
        self.client._sdk = Mock(access_token='', feed_token='')
        self.client._client_id = self.client._api_key = ''
        self.client._session_day = NOW.date()
        self.client._master_day, self.client._master = DAY, {'SBIN': '3045'}
        return self.client

    def test_candle_parameters_date_validation_and_empty_rejection(self):
        client = self.active_client()
        for day in (DAY, '2026-10-15', '20261013', 'invalid', None):
            with self.subTest(day=day), self.assertRaises(a.AngelError):
                client.candles('SBIN', day, as_of=DAY)
        client._sdk.getCandleData.assert_not_called()
        client._sdk.getCandleData.return_value = {'status': True, 'data': [['2026-10-13T09:15:00+05:30', 10, 12, 9, 11, 1]]}
        result = client.candles('SBIN', '2026-10-13', as_of=DAY)
        client._sdk.getCandleData.assert_called_once_with({'exchange': 'NSE', 'symboltoken': '3045',
            'interval': 'ONE_MINUTE', 'fromdate': '2026-10-13 09:15', 'todate': '2026-10-13 15:30'})
        self.assertEqual(result[0]['knowledge_date'], DAY)
        self.assertEqual(result[0]['recorded_at'], NOW.isoformat())
        for data in ([], None, {}, [['2026-10-12T09:15:00+05:30', 10, 12, 9, 11, 1]]):
            client._sdk.getCandleData.return_value = {'status': True, 'data': data}
            with self.assertRaises(a.AngelError):
                client.candles('SBIN', '2026-10-13', as_of=DAY)

    def test_stream_parsing_callback_interrupt_and_transport_errors_are_safe(self):
        import websocket
        client = self.active_client()
        raw = {'token': '3045', 'exchange_type': 1, 'subscription_mode': 1,
               'exchange_timestamp': NOW.timestamp() * 1000, 'last_traded_price': 1000}
        for category in ('feed_parse', 'callback', 'interrupted', 'ws_closed', 'api_rejection'):
            sock, decoder, callback = Mock(), Mock(return_value=raw), Mock()
            sock.recv_data.return_value = (2, b'packet')
            if category == 'feed_parse':
                decoder.side_effect = ValueError('private')
            elif category == 'callback':
                callback.side_effect = a.AngelError('private')
            elif category == 'interrupted':
                sock.recv_data.side_effect = KeyboardInterrupt
            elif category == 'ws_closed':
                sock.recv_data.side_effect = websocket.WebSocketConnectionClosedException('private')
            else:
                sock.recv_data.return_value = (1, 'private')
            client._feed_type = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': decoder})
            with self.subTest(category=category), patch.object(websocket, 'create_connection', return_value=sock):
                with self.assertRaises(a.AngelError) as caught:
                    client.stream(['SBIN'], callback, as_of=DAY)
                self.assertEqual(caught.exception.category, category)
                self.assertNotIn('private', str(caught.exception))
                sock.close.assert_called_once()
                self.assertFalse(client._streaming)

    def test_control_only_feed_reaches_deadline(self):
        import websocket
        client = self.active_client()
        client._feed_type = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': Mock()})
        sock = Mock()
        sock.recv_data.return_value = (websocket.ABNF.OPCODE_PONG, b'private')
        with patch.object(websocket, 'create_connection', return_value=sock), \
                patch.object(a._time, 'monotonic', side_effect=[0, 0, 0, 0, 31]):
            client.stream(['SBIN'], Mock(), as_of=DAY)
        sock.recv_data.assert_called_once_with(control_frame=True)
        sock.send.assert_called_once_with('ping')
        sock.close.assert_called_once()

    def test_real_control_frames_and_close_are_distinguished(self):
        import websocket
        ws = websocket.WebSocket()
        frames = [websocket.ABNF.create_frame(b'private', op) for op in
                  (websocket.ABNF.OPCODE_PING, websocket.ABNF.OPCODE_PONG, websocket.ABNF.OPCODE_CLOSE)]
        self.client._sdk = SimpleNamespace(access_token='', feed_token='')
        self.client._client_id = self.client._api_key = ''
        self.client._session_day = NOW.date()
        self.client._master_day, self.client._master = DAY, {'SBIN': '3045'}
        decoder = Mock()
        self.client._feed_type = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': decoder})
        with patch.object(websocket, 'create_connection', return_value=ws), \
                patch.object(ws, 'recv_frame', side_effect=frames), patch.object(ws, 'pong') as pong, \
                patch.object(ws, 'send'), patch.object(ws, 'send_close'), patch.object(ws, 'settimeout'), \
                patch.object(ws, 'close') as close:
            with self.assertRaises(a.AngelError) as caught:
                self.client.stream(['SBIN'], Mock(), as_of=DAY)
        self.assertEqual(caught.exception.category, 'ws_closed')
        pong.assert_called_once_with(b'private')
        decoder.assert_not_called()
        close.assert_called_once()
        self.assertNotIn('private', str(caught.exception))


class SessionSelectionTest(unittest.TestCase):
    def test_observed_sessions_exclude_today_future_knowledge_wrong_series_and_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.db'
            conn = sqlite3.connect(path)
            conn.execute('CREATE TABLE bhavcopy(symbol TEXT, series TEXT, event_date TEXT, knowledge_date TEXT)')
            conn.executemany('INSERT INTO bhavcopy VALUES (?, ?, ?, ?)', [
                ('SBIN', 'EQ', '2026-10-09', '2026-10-09'),
                ('SBIN', 'EQ', '2026-10-12', '2026-10-15'),
                ('SBIN', 'BE', '2026-10-13', '2026-10-13'),
                ('SBIN', 'EQ', DAY, DAY), ('OTHER', 'EQ', '2026-10-13', '2026-10-13')])
            conn.commit()
            conn.close()
            with patch.object(smoke, 'PRAMAN_DB', path):
                self.assertEqual(smoke.recent_session(DAY), '2026-10-09')
                with self.assertRaises(a.AngelError):
                    smoke.recent_session('2026-11-14')
            with patch.object(smoke, 'PRAMAN_DB', Path(folder) / 'absent.db'):
                with self.assertRaises(a.AngelError):
                    smoke.recent_session(DAY)

    def test_capacity_rejects_early_clean_return_and_retains_safe_category(self):
        stats = capacity.TierStats(25, ['SBIN'], Mock(pending=[]), NOW)
        stats.on_tick({'symbol': 'SBIN', 'timestamp': NOW.isoformat(), 'recorded_at': NOW.isoformat(), 'price': 1})
        from datetime import timedelta
        stats.finish(NOW + timedelta(seconds=1))
        result = capacity.evaluate(stats, ['SBIN'], required_seconds=600)
        self.assertEqual(result['outcome'], 'FAIL')
        self.assertIn('the feed did not complete the required duration', result['reasons'])
        self.assertEqual(a.error_details(a.AngelError('private')), {'category': 'unknown', 'http_status': None})
        stats.feed_diagnostic = a.error_details(a._Failure('callback'))
        self.assertEqual(capacity.evaluate(stats, ['SBIN'])['feed_diagnostic']['category'], 'callback')
