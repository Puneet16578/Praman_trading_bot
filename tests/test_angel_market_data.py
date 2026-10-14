"""Offline SDK mocks; ephemeral synthetic authentication values, never real credentials."""
import itertools
import ast
import contextlib
import io
import logging
import secrets
import subprocess
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from desk import angel_market_data as angel
from shared.market_time import IST

NOW = datetime(2026, 10, 13, 10, 0, tzinfo=IST)
DAY = NOW.date().isoformat()
FORBIDDEN = frozenset(('placeOrder', 'placeOrderFullResponse', 'modifyOrder', 'cancelOrder',
    'orderBook', 'tradeBook', 'position', 'holding', 'allholding', 'rmsLimit', 'convertPosition',
    'gttCreateRule', 'gttModifyRule', 'gttCancelRule', 'gttDetails', 'gttLists',
    'individual_order_details', 'getMarginApi', 'estimateCharges', 'getRMS', 'getHolding',
    'getAllHolding', 'getPosition', 'getOrderBook', 'getTradeBook', 'generateTPIN', 'verifyDis'))


def violations(source, is_wrapper=False):
    bad = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if not is_wrapper and any(a.name.split('.')[0] == 'SmartApi' for a in node.names):
                bad.append('SDK import')
        elif isinstance(node, ast.ImportFrom):
            if not is_wrapper and (node.module or '').split('.')[0] == 'SmartApi':
                bad.append('SDK import')
            if any(a.name in FORBIDDEN for a in node.names):
                bad.append('forbidden function import')
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN:
            bad.append('forbidden function')
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if '/' in node.value and node.value.rsplit('/', 1)[-1] in FORBIDDEN:
                bad.append('forbidden endpoint')
        elif isinstance(node, ast.Call):
            name = getattr(node.func, 'id', getattr(node.func, 'attr', ''))
            if name in FORBIDDEN:
                bad.append('forbidden function call')
            strings = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if name in ('getattr', 'setattr') and any(s in FORBIDDEN for s in strings):
                bad.append('dynamic forbidden function')
            if name in ('import_module', '__import__') and not is_wrapper and any(s.startswith('SmartApi') for s in strings):
                bad.append('dynamic SDK import')
    return bad


class AngelArchitectureTest(unittest.TestCase):
    def test_only_wrapper_imports_sdk_and_no_banned_function_references(self):
        root = Path(__file__).resolve().parents[1]
        bad = []
        listed = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.py'],
                                cwd=root, capture_output=True, check=True).stdout.decode().split('\0')
        for name in filter(None, listed):
            path = root / name
            found = violations(path.read_text(encoding='utf-8-sig'), path == root / 'desk/angel_market_data.py')
            if found:
                bad.append((name, found))
        self.assertEqual(bad, [])

    def test_guard_rejects_alias_dynamic_import_and_function_reference(self):
        for source in ('from SmartApi import SmartConnect as S', 'import SmartApi.smartConnect',
                       "importlib.import_module('SmartApi')", 'client.placeOrder',
                       "getattr(client, 'gttCreateRule')", "requests.post('https://example.invalid/placeOrder')"):
            with self.subTest(source=source):
                self.assertTrue(violations(source))

    def test_public_surface_is_exactly_the_seven_capabilities(self):
        names = {name for name in dir(angel.AngelMarketData()) if not name.startswith('_')}
        self.assertEqual(names, {'login', 'logout', 'profile', 'quote', 'candles', 'stream', 'download_scrip_master'})

    def test_transport_rejects_unknown_route_and_wrong_method_before_network(self):
        with patch.object(angel._requests, 'request') as request, patch.object(angel, '_pace') as pace:
            for route, method in [('api.not_allowed', 'POST'), ('api.market.data', 'DELETE')]:
                with self.assertRaises(angel.AngelError):
                    angel._request(None, route, method)
            request.assert_not_called()
            pace.assert_not_called()

    def test_rate_spacing_counts_failed_attempts_and_stays_below_profile_hourly_limit(self):
        with patch.object(angel, '_LAST_REQUEST', 10), patch.object(angel._time, 'monotonic', side_effect=[11, 14.1]), \
                patch.object(angel._time, 'sleep') as sleep:
            angel._pace()
            self.assertAlmostEqual(sleep.call_args.args[0], 3.1)
            self.assertEqual(angel._LAST_REQUEST, 14.1)
        self.assertLess(3600 / angel._REST_SPACING + 1, 1000)

    def test_sdk_constructor_is_never_used_and_import_lookup_is_offline(self):
        base = type('FakeSDK', (), {'__init__': Mock(side_effect=AssertionError('unsafe constructor'))})
        package = types.ModuleType('SmartApi')
        package.__path__ = []
        rest, feed = types.ModuleType('SmartApi.smartConnect'), types.ModuleType('SmartApi.smartWebSocketV2')
        rest.SmartConnect, feed.SmartWebSocketV2 = base, type('FakeFeed', (), {})
        package.smartConnect, package.smartWebSocketV2 = rest, feed
        logzero = types.ModuleType('logzero')
        logzero.logger = Mock()
        with patch.dict('sys.modules', {'SmartApi': package, 'SmartApi.smartConnect': rest,
                        'SmartApi.smartWebSocketV2': feed, 'logzero': logzero}), \
                patch.object(angel._metadata, 'version', return_value='1.5.5'), \
                patch.object(angel._requests, 'request') as network:
            sdk_type, _ = angel._sdk_types()
            sdk_type(secrets.token_urlsafe())
            base.__init__.assert_not_called()
            network.assert_not_called()
            self.assertIsInstance(rest.logger, angel._Silent)


class AngelClientTest(unittest.TestCase):
    def setUp(self):
        self.clock = patch.object(angel, '_now', return_value=NOW).start()
        self.addCleanup(patch.stopall)
        self.secret = secrets.token_urlsafe()
        self.sdk = Mock()
        self.sdk.generateSession.return_value = {'status': True, 'data': {}}
        self.sdk.terminateSession.return_value = {'status': True, 'data': {}}
        self.sdk.access_token = self.sdk.refresh_token = self.sdk.feed_token = self.secret
        self.factory = patch.object(angel, '_sdk_types', return_value=(Mock(return_value=self.sdk), Mock())).start()
        self.prompt = patch.object(angel._getpass_module, 'getpass', return_value=self.secret).start()
        patch.dict(angel._os.environ, {'ANGEL_API_KEY': self.secret}).start()
        patch.object(angel, '_pace').start()
        self.client = angel.AngelMarketData()
        self.client.login()
        self.client._master_day = DAY
        self.client._master = {'SBIN': '3045'}

    def test_login_prompts_once_daily_and_does_not_print(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.client.login()
        self.assertEqual(self.prompt.call_count, 3)
        self.assertEqual(output.getvalue(), '')
        self.assertNotIn(self.secret, repr(self.client))

    def test_midnight_invalidates_before_read_and_next_login_prompts_again(self):
        self.clock.return_value = datetime(2026, 10, 14, 0, 0, tzinfo=IST)
        with self.assertRaises(angel.AngelError):
            self.client.quote('SBIN', as_of='2026-10-14')
        self.sdk.getMarketData.assert_not_called()
        self.assertIsNone(self.client._sdk)
        self.client.login()
        self.assertEqual(self.prompt.call_count, 6)

    def test_old_asof_at_midnight_also_clears_session(self):
        self.clock.return_value = datetime(2026, 10, 14, 0, 0, tzinfo=IST)
        with self.assertRaises(angel.AngelError):
            self.client.quote('SBIN', as_of=DAY)
        self.assertIsNone(self.client._sdk)

    def test_partial_login_failure_attempts_logout_before_discarding_token(self):
        self.client.logout()
        self.sdk.access_token = self.secret
        self.sdk.terminateSession.reset_mock()
        self.sdk.generateSession.side_effect = RuntimeError(self.secret)
        with self.assertRaises(angel.AngelError):
            self.client.login()
        self.sdk.terminateSession.assert_called_once()
        self.assertIsNone(self.client._sdk)

    def test_failed_logout_clears_secrets_and_hides_exception_text(self):
        self.sdk.terminateSession.side_effect = RuntimeError(self.secret)
        with self.assertRaises(angel.AngelError) as caught:
            self.client.logout()
        self.assertNotIn(self.secret, str(caught.exception))
        self.assertIsNone(self.client._sdk)
        self.assertIsNone(self.client._api_key)

    def test_getpass_echo_fallback_is_refused(self):
        self.client.logout()
        self.prompt.side_effect = angel._getpass_module.GetPassWarning(self.secret)
        with self.assertRaises(angel.AngelError) as caught:
            self.client.login()
        self.assertNotIn(self.secret, str(caught.exception))
        self.assertIsNone(self.client._sdk)

    def test_profile_and_quote_strip_tokens_and_derived_changes(self):
        self.sdk.getProfile.return_value = {'status': True, 'data': {'exchanges': ['NSE'], 'jwtToken': self.secret}}
        self.assertEqual(self.client.profile(as_of=DAY), {'exchanges': ['NSE']})
        self.sdk.getMarketData.return_value = {'status': True, 'data': {'fetched': [
            {'symbolToken': '3045', 'exchange': 'NSE', 'ltp': 800, 'tradeVolume': 100,
             'exchFeedTime': '13-Oct-2026 10:00:00', 'jwtToken': self.secret, 'percentChange': 4,
             'depth': {'buy': [{'price': 799}], 'sell': [{'price': 801}]}}]}}
        result = self.client.quote('SBIN', as_of=DAY)
        self.assertEqual((result['price'], result['bid'], result['ask']), (800, 799, 801))
        self.assertNotIn('percentChange', result)
        self.assertNotIn(self.secret, str(result))

    def test_historical_asof_and_unknown_symbol_are_refused_before_quote(self):
        for symbol, asof in [('SBIN', '2026-09-01'), ('UNKNOWN', DAY)]:
            with self.assertRaises(angel.AngelError):
                self.client.quote(symbol, as_of=asof)
        self.sdk.getMarketData.assert_not_called()

    def test_mapping_is_exact_eq_and_duplicates_are_reported(self):
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.json.return_value = [dict(symbol=s, token=t, exch_seg=e, expiry='', instrumenttype='') for s, t, e in
                                     [('SBIN-EQ', '3045', 'NSE'), ('SBIN-BE', '9', 'NSE'),
                                      ('OTHER-EQ', '1', 'NSE'), ('OTHER-EQ', '2', 'NSE'), ('NO-EQ', '3', 'BSE')]]
        self.client._master_day = None
        with patch.object(angel._requests, 'get', return_value=response) as get:
            result = self.client.download_scrip_master(['SBIN', 'OTHER', 'NO'], as_of=DAY)
            self.assertEqual(result['mapped'], {'SBIN': '3045'})
            self.assertEqual(result['unmapped'], ['NO', 'OTHER'])
            self.client.download_scrip_master(['SBIN'], as_of=DAY)
            get.assert_called_once()
            self.assertFalse(get.call_args.kwargs['allow_redirects'])

    def test_candles_are_raw_one_day_and_known_only_today(self):
        self.sdk.getCandleData.return_value = {'status': True, 'data': [['2026-09-01T09:15:00+05:30', 10, 12, 9, 11, 50]]}
        rows = self.client.candles('SBIN', '2026-09-01', as_of=DAY)
        self.assertEqual(rows[0]['knowledge_date'], DAY)
        self.assertEqual(rows[0]['close'], 11)
        self.assertNotIn('return', rows[0])
        self.sdk.getCandleData.return_value['data'][0][0] = '2026-09-02T09:15:00+05:30'
        with self.assertRaises(angel.AngelError):
            self.client.candles('SBIN', '2026-09-01', as_of=DAY)

    def test_transport_error_does_not_print_or_persist_credentials(self):
        sdk = types.SimpleNamespace(api_key=self.secret, access_token=self.secret,
                                    clientLocalIp='127.0.0.1', clientPublicIp='127.0.0.1', clientMacAddress='local')
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), \
                patch('builtins.open', side_effect=AssertionError('Unexpected file access')) as opened, \
                patch.object(angel._requests, 'request', side_effect=RuntimeError(self.secret)):
            with self.assertRaises(angel.AngelError) as caught:
                angel._request(sdk, 'api.login', 'POST', {'password': self.secret})
            opened.assert_not_called()
        self.assertEqual(output.getvalue(), '')
        self.assertNotIn(self.secret, str(caught.exception))

    def test_configured_http_debug_logging_cannot_expose_tokens(self):
        sdk = types.SimpleNamespace(api_key=self.secret, access_token=self.secret,
                                    clientLocalIp='local', clientPublicIp='public', clientMacAddress='mac')
        output = io.StringIO()
        logger = logging.getLogger('urllib3.connectionpool')
        handler = logging.StreamHandler(output)
        logger.addHandler(handler)
        old_level, old_disabled = logger.level, logging.root.manager.disable
        logger.setLevel(logging.DEBUG)
        logging.disable(logging.NOTSET)
        def noisy(*args, **kwargs):
            logger.debug(self.secret)
            self.assertEqual(angel._http_client.HTTPConnection.debuglevel, 0)
            raise RuntimeError(self.secret)
        try:
            with patch.object(angel._requests, 'request', side_effect=noisy), \
                    patch.object(angel._http_client.HTTPConnection, 'debuglevel', 1):
                with self.assertRaises(angel.AngelError):
                    angel._request(sdk, 'api.user.profile', 'GET', {'refreshToken': self.secret})
                self.assertEqual(angel._http_client.HTTPConnection.debuglevel, 1)
            self.assertEqual(output.getvalue(), '')
            self.assertEqual(logging.root.manager.disable, logging.NOTSET)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)
            logging.disable(old_disabled)

    def test_stream_closes_without_ticks_at_deadline_and_has_no_worker(self):
        class Timeout(Exception):
            pass
        sock = Mock()
        ticks = Mock()
        feed = type('Feed', (), {'subscribe': Mock()})
        self.client._feed_type = feed
        fake = types.SimpleNamespace(enableTrace=Mock(), create_connection=Mock(return_value=sock),
                                     WebSocketTimeoutException=Timeout, WebSocketConnectionClosedException=ConnectionError,
                                     ABNF=types.SimpleNamespace(OPCODE_CLOSE=8, OPCODE_PING=9, OPCODE_PONG=10, OPCODE_BINARY=2))
        sock.recv_data.side_effect = Timeout
        with patch.dict('sys.modules', {'websocket': fake}), \
                patch.object(angel._time, 'monotonic', side_effect=itertools.chain([0, 0, 0, 0], itertools.repeat(31)).__next__):
            self.client.stream(['SBIN'], ticks, as_of=DAY, seconds=30)
        sock.close.assert_called_once()
        ticks.assert_not_called()
        self.assertEqual(fake.create_connection.call_args.kwargs['redirect_limit'], 0)

    def test_stream_only_emits_validated_price_and_timestamps(self):
        sock = Mock()
        sock.recv_data.return_value = (2, b'packet')
        feed = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': Mock(return_value={
            'token': '3045', 'exchange_type': 1, 'subscription_mode': 1,
            'exchange_timestamp': int(NOW.timestamp() * 1000), 'last_traded_price': 80125,
            'jwtToken': self.secret})})
        self.client._feed_type = feed
        fake = types.SimpleNamespace(enableTrace=Mock(), create_connection=Mock(return_value=sock),
                                     WebSocketTimeoutException=TimeoutError, WebSocketConnectionClosedException=ConnectionError,
                                     ABNF=types.SimpleNamespace(OPCODE_CLOSE=8, OPCODE_PING=9, OPCODE_PONG=10, OPCODE_BINARY=2))
        emitted = []
        with patch.dict('sys.modules', {'websocket': fake}), \
                patch.object(angel._time, 'monotonic', side_effect=itertools.chain([0, 0, 0, 0], itertools.repeat(31)).__next__):
            self.client.stream(['SBIN'], emitted.append, as_of=DAY)
        self.assertEqual(emitted[0]['price'], 801.25)
        self.assertNotIn(self.secret, str(emitted))
        sock.close.assert_called_once()

    def test_stream_and_scrip_master_keep_certificate_verification(self):
        """967729e review: the feed keeps CERT_REQUIRED with hostname checks (the SDK itself uses
        CERT_NONE), and the public master keeps verify=True with no redirects."""
        import itertools, ssl
        class Timeout(Exception):
            pass
        sock = Mock()
        sock.recv_data.side_effect = Timeout
        self.client._feed_type = type('Feed', (), {'subscribe': Mock()})
        fake = types.SimpleNamespace(enableTrace=Mock(), create_connection=Mock(return_value=sock),
                                     WebSocketTimeoutException=Timeout, WebSocketConnectionClosedException=ConnectionError,
                                     ABNF=types.SimpleNamespace(OPCODE_CLOSE=8, OPCODE_PING=9, OPCODE_PONG=10, OPCODE_BINARY=2))
        clock = itertools.count(0, 5)
        with patch.dict('sys.modules', {'websocket': fake}), patch.object(angel._time, 'monotonic', side_effect=lambda: next(clock)):
            self.client.stream(['SBIN'], Mock(), as_of=DAY, seconds=30)
        self.assertEqual(fake.create_connection.call_args.kwargs['sslopt'], {'cert_reqs': ssl.CERT_REQUIRED, 'check_hostname': True})
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.json.return_value = [dict(symbol='SBIN-EQ', token='3045', exch_seg='NSE', expiry='', instrumenttype='')]
        self.client._master_day = None
        with patch.object(angel._requests, 'get', return_value=response) as get:
            self.assertEqual(self.client.download_scrip_master(['SBIN'], as_of=DAY)['mapped'], {'SBIN': '3045'})
        self.assertTrue(get.call_args.kwargs['verify'])
        self.assertFalse(get.call_args.kwargs['allow_redirects'])

    def test_tls_redirect_and_payload_are_fixed_at_the_dispatcher(self):
        sdk = types.SimpleNamespace(api_key=self.secret, access_token=self.secret,
                                    clientLocalIp='local', clientPublicIp='public', clientMacAddress='mac')
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.json.return_value = {'status': True, 'data': {}}
        with patch.object(angel._requests, 'request', return_value=response) as request:
            angel._request(sdk, 'api.market.data', 'POST', {'mode': 'FULL', 'exchangeTokens': {'NSE': ['3045']}})
        self.assertEqual(request.call_args.args[1], angel._ROOT + angel._ROUTES['api.market.data'][1])
        self.assertTrue(request.call_args.kwargs['verify'])
        self.assertFalse(request.call_args.kwargs['allow_redirects'])
