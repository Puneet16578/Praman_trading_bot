"""Feed keepalive and close summary (user request 2026-10-14, the 239-second drop). Offline only:
a fake server and a fake clock; no real waiting, no network, no login."""
import inspect
import json
import secrets
import types
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import websocket as real_ws

from desk import angel_market_data as angel
from shared.market_time import IST

NOW = datetime(2026, 10, 14, 10, 0, tzinfo=IST)
DAY = NOW.date().isoformat()
ABNF = real_ws.ABNF


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class FakeServer:
    """Drops the connection with CLOSE 1008 when no protocol PING arrived for `drop_after` seconds;
    otherwise delivers its scheduled frames, and waits out each read timeout on the fake clock."""
    def __init__(self, clock, *, drop_after=30.0, frames=(), close_reason=b''):
        self.clock, self.drop_after, self.close_reason = clock, drop_after, close_reason
        self.frames = sorted(frames)               # (time, opcode, payload)
        self.last_ping = 0.0
        self.pings, self.text_sent, self.closed, self.timeout = [], [], False, 1.0

    def ping(self, payload=''):
        self.pings.append(self.clock.t)
        self.last_ping = self.clock.t

    def send(self, payload, opcode=ABNF.OPCODE_TEXT):
        self.text_sent.append((self.clock.t, payload))

    def settimeout(self, value):
        self.timeout = value

    def recv_data(self, control_frame=False):
        drop_at = self.last_ping + self.drop_after
        due = self.frames[0][0] if self.frames else float('inf')
        horizon = self.clock.t + self.timeout
        if drop_at <= min(due, horizon):
            self.clock.t = max(self.clock.t, drop_at)
            return ABNF.OPCODE_CLOSE, (1008).to_bytes(2, 'big') + self.close_reason
        if due <= horizon:
            self.clock.t = max(self.clock.t, due)
            _, opcode, payload = self.frames.pop(0)
            return opcode, payload
        self.clock.t = horizon
        raise real_ws.WebSocketTimeoutException('quiet')

    def close(self):
        self.closed = True


class KeepaliveTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(angel, '_now', return_value=NOW).start()
        self.secret = secrets.token_urlsafe()
        sdk = Mock()
        sdk.generateSession.return_value = {'status': True, 'data': {}}
        sdk.terminateSession.return_value = {'status': True, 'data': {}}
        sdk.access_token = sdk.refresh_token = sdk.feed_token = self.secret
        patch.object(angel, '_sdk_types', return_value=(Mock(return_value=sdk), Mock())).start()
        patch.object(angel._getpass_module, 'getpass', return_value=self.secret).start()
        patch.dict(angel._os.environ, {'ANGEL_API_KEY': self.secret}).start()
        patch.object(angel, '_pace').start()
        self.client = angel.AngelMarketData()
        self.client.login()
        self.client._master_day, self.client._master = DAY, {'SBIN': '3045'}
        self.client._feed_type = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': Mock(return_value={
            'token': '3045', 'exchange_type': 1, 'subscription_mode': 1,
            'exchange_timestamp': int(NOW.timestamp() * 1000), 'last_traded_price': 80125})})
        self.clock = FakeClock()
        patch.object(angel._time, 'monotonic', self.clock).start()

    def stream(self, server, seconds):
        fake = types.SimpleNamespace(enableTrace=Mock(), create_connection=Mock(return_value=server), ABNF=ABNF,
                                     WebSocketTimeoutException=real_ws.WebSocketTimeoutException,
                                     WebSocketConnectionClosedException=real_ws.WebSocketConnectionClosedException)
        ticks = []
        with patch.dict('sys.modules', {'websocket': fake}):
            result = self.client.stream(['SBIN'], ticks.append, as_of=DAY, seconds=seconds)
        return result, ticks

    def test_a_server_that_drops_quiet_clients_keeps_our_feed_for_ten_fake_minutes(self):
        server = FakeServer(self.clock, drop_after=30)
        summary, _ = self.stream(server, 600)
        self.assertEqual((summary['closed_by'], summary['close_reason']), ('client', 'deadline'))
        self.assertGreaterEqual(summary['connected_seconds'], 600)
        gaps = [b - a for a, b in zip(server.pings, server.pings[1:])]
        self.assertTrue(server.pings and max(gaps) <= 10.0 + 1e-9)            # a protocol PING every 10 s
        self.assertTrue(all(payload == 'ping' for _, payload in server.text_sent))   # Angel's text heartbeat too
        self.assertTrue(server.closed)

    def test_without_protocol_pings_the_same_server_drops_us_at_30_seconds(self):
        server = FakeServer(self.clock, drop_after=30)
        server.ping = lambda payload='': None                                  # the pre-fix wrapper sent none
        with self.assertRaises(angel.AngelError) as caught:
            self.stream(server, 600)
        details = angel.error_details(caught.exception)
        self.assertEqual(details['category'], 'ws_closed')
        self.assertEqual((details['stream']['closed_by'], details['stream']['close_code']), ('server', 1008))
        self.assertAlmostEqual(details['stream']['connected_seconds'], 30.0)

    def test_server_pings_and_text_pongs_are_never_ticks_and_other_text_stops_safely(self):
        frames = [(5, ABNF.OPCODE_PING, b'hb'), (6, ABNF.OPCODE_TEXT, b'pong'), (7, ABNF.OPCODE_BINARY, b'packet'),
                  (8, ABNF.OPCODE_PONG, b''), (9, ABNF.OPCODE_TEXT, b'PONG ')]
        summary, ticks = self.stream(FakeServer(self.clock, frames=frames), 20)
        self.assertEqual(len(ticks), 1)
        self.assertEqual(summary['frames'], dict(binary=1, text_pong=2, text_other=0, server_ping=1, pong=1))
        self.assertAlmostEqual(summary['seconds_since_pong_received'], 12.0)
        server = FakeServer(self.clock, frames=[(self.clock.t + 1, ABNF.OPCODE_TEXT, b'{"error": "x"}')])
        with self.assertRaises(angel.AngelError) as caught:
            self.stream(server, 20)
        details = angel.error_details(caught.exception)
        self.assertEqual((details['category'], details['stream']['frames']['text_other']), ('api_rejection', 1))

    def test_the_close_summary_has_the_requested_fields_and_no_secrets(self):
        server = FakeServer(self.clock, drop_after=30, close_reason=self.secret.encode())
        server.ping = lambda payload='': None
        with self.assertRaises(angel.AngelError) as caught:
            self.stream(server, 100)
        summary = angel.error_details(caught.exception)['stream']
        self.assertEqual(set(summary), {'closed_by', 'close_code', 'close_reason', 'close_reason_bytes',
                                        'connected_seconds', 'seconds_since_last_message', 'seconds_since_ping_sent',
                                        'seconds_since_pong_received', 'seconds_since_text_ping_sent',
                                        'seconds_since_text_pong_received', 'frames'})
        self.assertEqual((summary['close_reason'], summary['close_reason_bytes']), ('withheld', len(self.secret)))
        self.assertNotIn(self.secret, json.dumps(summary))
        self.assertNotIn(self.secret, str(caught.exception))


class LibraryBehaviourTest(unittest.TestCase):
    """What the wrapper relies on in websocket-client 1.8.0 itself."""

    def test_recv_data_answers_a_server_ping_with_a_pong(self):
        sock = real_ws.WebSocket()
        frames = iter([ABNF.create_frame(b'hb', ABNF.OPCODE_PING), ABNF.create_frame(b'packet', ABNF.OPCODE_BINARY)])
        with patch.object(sock, 'recv_frame', side_effect=lambda: next(frames)), patch.object(sock, 'pong') as pong:
            self.assertEqual(sock.recv_data(control_frame=True), (ABNF.OPCODE_PING, b'hb'))
            pong.assert_called_once_with(b'hb')
            self.assertEqual(sock.recv_data(control_frame=True), (ABNF.OPCODE_BINARY, b'packet'))

    def test_the_plain_socket_never_closes_itself_for_a_late_pong(self):
        """Only WebSocketApp.run_forever(ping_timeout=...) closes on a late PONG; the wrapper uses
        create_connection's plain WebSocket, whose source has no pong-timeout logic at all."""
        source = inspect.getsource(real_ws._core)
        self.assertNotIn('ping_timeout', source)
        self.assertNotIn('last_pong', source)
        self.assertEqual(real_ws.__version__, '1.8.0')


if __name__ == '__main__':
    unittest.main()
