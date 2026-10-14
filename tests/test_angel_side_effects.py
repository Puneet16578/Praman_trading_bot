"""Side-effect proof with synthetic secrets and completely mocked transports."""
import itertools
import contextlib
import io
import json
import logging
import os
import secrets
import subprocess
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from desk import angel_market_data as angel
from shared.market_time import IST


class AngelSideEffectsTest(unittest.TestCase):
    def test_fresh_wrapper_import_under_supported_launcher_has_no_io_side_effects(self):
        script = '''
import os, sys
def audit(event, args):
    if event == 'open':
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError('Unexpected file write')
    if event in ('os.mkdir', 'os.rename', 'os.remove', 'socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'subprocess.Popen'):
        raise AssertionError('Unexpected external side effect')
sys.addaudithook(audit)
import desk.angel_market_data
assert not any(n.startswith('SmartApi') for n in sys.modules)
'''
        result = subprocess.run([sys.executable, '-B', '-c', script],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, '')

    def test_sdk_import_blocks_ip_dns_hardware_probe_and_bytecode_writes(self):
        import builtins
        original = builtins.__import__
        rest = types.SimpleNamespace(SmartConnect=type('SDK', (), {}))
        feed = types.SimpleNamespace(SmartWebSocketV2=type('Feed', (), {}))
        package = types.SimpleNamespace(smartConnect=rest, smartWebSocketV2=feed)
        probes = []

        def importing(name, *args, **kwargs):
            if name.startswith('SmartApi'):
                self.assertTrue(sys.dont_write_bytecode)
                probes.append(angel._requests.get('https://example.invalid/ip').text)
                self.assertEqual(angel._socket.gethostbyname('example.invalid'), '127.0.0.1')
                self.assertEqual(angel._uuid.getnode(), 0)
                return package
            return original(name, *args, **kwargs)

        logzero = types.SimpleNamespace(logger=Mock())
        with patch.dict(sys.modules, {'logzero': logzero}), \
                patch.object(angel._metadata, 'version', return_value='1.5.5'), \
                patch('builtins.__import__', side_effect=importing), \
                patch.object(angel._requests, 'request', side_effect=AssertionError('Network')), \
                patch.object(angel._socket, 'gethostbyname', side_effect=AssertionError('DNS')), \
                patch.object(angel._uuid, 'getnode', side_effect=AssertionError('Hardware probe')):
            before = sys.dont_write_bytecode
            sdk_type, _ = angel._sdk_types()
            self.assertEqual(sys.dont_write_bytecode, before)
            sdk = sdk_type(secrets.token_urlsafe())
            self.assertEqual(sdk.clientLocalIp, '127.0.0.1')
            self.assertEqual(sdk.clientPublicIp, '127.0.0.1')
            self.assertEqual(sdk.clientMacAddress, '00:00:00:00:00:00')
        self.assertEqual(probes, ['127.0.0.1', '127.0.0.1'])

    def test_entire_mocked_session_has_no_writes_or_credential_logs(self):
        client_id, pin, otp, key, jwt, refresh, feed_token = [secrets.token_urlsafe() for _ in range(7)]
        private = (client_id, pin, otp, key, jwt, refresh, feed_token)
        now = datetime(2026, 10, 13, 10, tzinfo=IST)
        output, logs = io.StringIO(), io.StringIO()
        logger = logging.getLogger('praman_angel_transport_test')
        handler = logging.StreamHandler(logs)
        logger.addHandler(handler)
        previous_level = logger.level
        logger.setLevel(logging.DEBUG)
        self.addCleanup(logger.removeHandler, handler)
        self.addCleanup(logger.setLevel, previous_level)
        calls = []

        def transport(method, url, **kwargs):
            self.assertTrue(url.startswith(angel._ROOT + '/rest/'))
            calls.append(url)
            logger.critical(repr(kwargs))
            if url.endswith('loginByPassword'):
                self.assertEqual(json.loads(kwargs['data']), {'clientcode': client_id, 'password': pin, 'totp': otp})
                data = {'jwtToken': jwt, 'refreshToken': refresh, 'feedToken': feed_token}
            elif url.endswith('getProfile'):
                data = {'clientcode': client_id, 'exchanges': ['NSE'], 'refreshToken': refresh}
            elif url.endswith('quote'):
                data = {'fetched': [{'symbolToken': '3045', 'exchange': 'NSE', 'ltp': 10,
                                    'exchFeedTime': now.isoformat(), 'jwtToken': jwt}]}
            elif url.endswith('getCandleData'):
                data = [['2026-09-01T09:15:00+05:30', 10, 11, 9, 10, 1]]
            else:
                self.assertTrue(url.endswith('logout'))
                data = {}
            response = MagicMock(status_code=200)
            response.__enter__.return_value = response
            response.json.return_value = {'status': True, 'data': data}
            return response

        class SDK:
            clientLocalIp = clientPublicIp = '127.0.0.1'
            clientMacAddress = '00:00:00:00:00:00'

            def __init__(self, api_key):
                self.api_key = api_key
                self.access_token = self.refresh_token = self.feed_token = None

            def generateSession(self, client, password, totp):
                result = angel._request(self, 'api.login', 'POST', dict(clientcode=client, password=password, totp=totp))
                self.access_token, self.refresh_token, self.feed_token = jwt, refresh, feed_token
                return self.getProfile(refresh)

            def getProfile(self, token):
                return angel._request(self, 'api.user.profile', 'GET', {'refreshToken': token})

            def getMarketData(self, mode, tokens):
                return angel._request(self, 'api.market.data', 'POST', {'mode': mode, 'exchangeTokens': tokens})

            def getCandleData(self, params):
                return angel._request(self, 'api.candle.data', 'POST', params)

            def terminateSession(self, client):
                return angel._request(self, 'api.logout', 'POST', {'clientcode': client})

        sock = Mock()
        sock.recv_data.return_value = (2, b'packet')
        feed = type('Feed', (), {'subscribe': Mock(), '_parse_binary_data': Mock(return_value={
            'token': '3045', 'exchange_type': 1, 'subscription_mode': 1,
            'exchange_timestamp': now.timestamp() * 1000, 'last_traded_price': 1000, 'feedToken': feed_token})})

        def connect(url, **kwargs):
            self.assertEqual(url, angel._FEED)
            logger.critical(repr(kwargs))
            return sock

        websocket = types.SimpleNamespace(enableTrace=Mock(), create_connection=connect, WebSocketTimeoutException=TimeoutError, WebSocketConnectionClosedException=ConnectionError,
                                     ABNF=types.SimpleNamespace(OPCODE_CLOSE=8, OPCODE_PING=9, OPCODE_PONG=10, OPCODE_BINARY=2))
        with contextlib.ExitStack() as stack:
            for target in ('builtins.open', 'io.open', 'os.open', 'os.mkdir', 'os.makedirs'):
                stack.enter_context(patch(target, side_effect=AssertionError('Unexpected file/folder access')))
            stack.enter_context(patch.object(angel._socket, 'connect', create=True, side_effect=AssertionError('Network')))
            stack.enter_context(patch.object(angel._socket.socket, 'connect', side_effect=AssertionError('Network')))
            stack.enter_context(patch.object(angel._requests, 'get', side_effect=AssertionError('Unexpected HTTP GET')))
            stack.enter_context(patch.object(angel._requests, 'request', side_effect=transport))
            stack.enter_context(patch.object(angel, '_sdk_types', return_value=(SDK, feed)))
            stack.enter_context(patch.object(angel, '_now', return_value=now))
            stack.enter_context(patch.object(angel, '_pace'))
            stack.enter_context(patch.object(angel._getpass_module, 'getpass', side_effect=[client_id, pin, otp]))
            stack.enter_context(patch.dict(os.environ, {'ANGEL_API_KEY': key}))
            stack.enter_context(patch.dict(sys.modules, {'websocket': websocket}))
            stack.enter_context(contextlib.redirect_stdout(output))
            stack.enter_context(contextlib.redirect_stderr(output))
            client = angel.AngelMarketData()
            client.login()
            client._master_day, client._master = '2026-10-13', {'SBIN': '3045'}
            clean = [client.quote('SBIN', as_of='2026-10-13'), client.candles('SBIN', '2026-09-01', as_of='2026-10-13')]
            with patch.object(angel._time, 'monotonic', side_effect=itertools.chain([0, 0, 0, 0], itertools.repeat(31)).__next__):
                client.stream(['SBIN'], clean.append, as_of='2026-10-13')
            client.logout()
        self.assertEqual(len(calls), 5)
        self.assertEqual(output.getvalue() + logs.getvalue(), '')
        for value in private + ('Authorization', 'X-PrivateKey', 'x-feed-token'):
            self.assertNotIn(value, repr(clean))
        sock.close.assert_called_once()
