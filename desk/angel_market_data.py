"""Read-only Angel boundary. No SDK object, credentials or raw response escapes.

SDK: official smartapi-python 1.5.5, https://github.com/angel-one/smartapi-python
The pinned SDK logs credential-bearing errors and does an IP lookup on import.
Import is muted/offline; its constructor and HTTP dispatcher are replaced, while
its session/market-data methods and feed decoder are reused. One allowlisted
dispatcher requires TLS verification and disables redirects.
No SDK file or store is written. Launch Python with -B to prevent its import
caches too. Raw observations only; no return/outcome API exists.
"""
from __future__ import annotations

import datetime as _dt
import contextlib as _contextlib
import getpass as _getpass_module
import http.client as _http_client
import importlib.metadata as _metadata
import json as _json
import math as _math
import logging as _logging
import os as _os
import ssl as _ssl
import socket as _socket
import sys as _sys
import uuid as _uuid
import threading as _threading
import time as _time
import warnings as _warnings
from types import MappingProxyType as _MappingProxyType, SimpleNamespace as _Namespace
from unittest.mock import patch as _patch

import requests as _requests
from shared.market_time import IST as _IST

__all__ = ['AngelMarketData', 'AngelError', 'check_setup']

_SDK_VERSION = '1.5.5'
_ROOT = 'https://apiconnect.angelone.in'
_MASTER = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
_FEED = 'wss://smartapisocket.angelone.in/smart-stream'
_ROUTES = _MappingProxyType({
    'api.login': ('POST', '/rest/auth/angelbroking/user/v1/loginByPassword'),
    'api.logout': ('POST', '/rest/secure/angelbroking/user/v1/logout'),
    'api.user.profile': ('GET', '/rest/secure/angelbroking/user/v1/getProfile'),
    'api.market.data': ('POST', '/rest/secure/angelbroking/market/v1/quote'),
    'api.candle.data': ('POST', '/rest/secure/angelbroking/historical/v1/getCandleData'),
})
# Official SmartAPI Team table: login/logout 1/s; profile 3/s, 1000/h;
# quote 10/s, 500/min, 5000/h; candles 3/s, 180/min, 5000/h.
# https://smartapi.angelone.in/smartapi/forum/topic/4387/changes-in-api-rate-limit/5
# Conservative GLOBAL process spacing: <= 879 requests/hour across all endpoints,
# including generateSession's implicit profile call. No automatic retry bursts.
_REST_SPACING = 4.1
_REQUEST_LOCK = _threading.Lock()  # synchronization only; never starts a thread
_LAST_REQUEST = float('-inf')


class AngelError(RuntimeError):
    """Only static, credential-free errors cross this boundary."""
    category = 'unknown'


_ERRORS = _MappingProxyType({
    'http': 'HTTP failure', 'timeout': 'Network timeout',
    'tls': 'TLS verification or handshake failure', 'network': 'Network connection failure',
    'json': 'JSON decoding failure', 'structure': 'Unexpected response structure',
    'api_rejection': 'API rejection', 'ws_closed': 'WebSocket disconnected',
    'feed_parse': 'Feed parsing error', 'callback': 'Consumer callback error',
    'interrupted': 'Interrupted', 'unknown': 'Unexpected internal failure',
    'access_denied': 'Access denied; cause unclassified',
    'permission_denied': 'Broker reports permission denied',
    'authentication': 'Authentication or session rejected',
    'request_validation': 'Broker reports invalid request parameters',
    'broker_date': 'Broker reports invalid date or time format',
    'candle_date': 'Invalid candle date; use a completed session in YYYY-MM-DD format',
    'rate_limit': 'Server reports rate limiting',
})

# SDK 1.5.5 smartExceptions / official API error table. Only exact indicators
# become fixed categories; never surface broker messages or arbitrary error codes.
_BROKER_TYPES = _MappingProxyType({
    'PermissionException': 'permission_denied', 'TokenException': 'authentication',
    'InputException': 'request_validation',
})
_BROKER_CODES = _MappingProxyType({
    'AG8001': 'authentication', 'AG8002': 'authentication', 'AG8003': 'authentication',
    'AB1010': 'authentication', 'AB1011': 'authentication',
    'AB13000': 'broker_date', 'AB1021': 'rate_limit',
})


def _broker_category(result):
    if not isinstance(result, dict):
        return None
    categories = set()
    for field, choices in (('error_type', _BROKER_TYPES), ('errorcode', _BROKER_CODES)):
        value = result.get(field)
        if isinstance(value, str) and value in choices:
            categories.add(choices[value])
    # Conflicting indicators cannot reliably identify a cause.
    return next(iter(categories)) if len(categories) == 1 else None


class _Failure(AngelError):
    """Only enumerated categories and validated HTTP integers may be exposed."""
    def __init__(self, category, status=None):
        self.category = category if category in _ERRORS else 'unknown'
        self.http_status = status if type(status) is int and 100 <= status <= 599 else None
        super().__init__(_ERRORS[self.category] +
                         (f' (HTTP {self.http_status})' if self.http_status is not None else '') + '.')


def _transport_failure(exc):
    # Optional websocket module is loaded only by stream(); classify without importing the SDK.
    ws = _sys.modules.get('websocket')
    if ws is not None:
        if isinstance(exc, ws.WebSocketConnectionClosedException):
            return _Failure('ws_closed')
        if isinstance(exc, ws.WebSocketTimeoutException):
            return _Failure('timeout')
        if isinstance(exc, getattr(ws, 'WebSocketBadStatusException', ())):
            return _Failure('http', getattr(exc, 'status_code', None))
    if isinstance(exc, (_requests.exceptions.SSLError, _ssl.SSLError)):
        return _Failure('tls')
    if isinstance(exc, (_requests.exceptions.Timeout, TimeoutError)):
        return _Failure('timeout')
    if isinstance(exc, (_requests.exceptions.ConnectionError, ConnectionError, OSError)):
        return _Failure('network')
    return _Failure('unknown')


def error_details(exc):
    """Safe summary metadata; never serialize arbitrary exception attributes or text. A feed
    failure also carries its close summary (numbers and fixed words only)."""
    if type(exc) is _Failure:
        details = {'category': exc.category, 'http_status': exc.http_status}
        if isinstance(getattr(exc, 'stream_summary', None), dict):
            details['stream'] = exc.stream_summary
        return details
    return {'category': 'unknown', 'http_status': None}


def _response_json(response, *, api_errors=False):
    if response.status_code != 200:
        status = response.status_code
        category = 'http'
        if api_errors and 400 <= status < 500:
            category = {401: 'authentication', 403: 'access_denied', 429: 'rate_limit'}.get(status, 'http')
            try:
                category = _broker_category(response.json()) or category
            except Exception:
                # HTML/empty/malformed error bodies must not erase the HTTP status.
                # This exact gateway indicator is observed on the official support forum;
                # it reports a server claim, not proof that this client exceeded its quota.
                content = response.content
                if (status == 403 and isinstance(content, bytes)
                        and content.strip() == b'Access denied because of exceeding access rate'):
                    category = 'rate_limit'
        raise _Failure(category, status) from None
    try:
        return response.json()
    except ValueError:
        raise _Failure('json') from None


def _api_result(result, http_status=None):
    if not isinstance(result, dict):
        raise _Failure('structure')
    if result.get('status') is False or result.get('error_type'):
        raise _Failure(_broker_category(result) or 'api_rejection', http_status)
    if result.get('status') is not True:
        raise _Failure('structure')
    if 'data' not in result:
        raise _Failure('structure')
    return result


def _now():
    return _dt.datetime.now(_IST)


def _pace():
    global _LAST_REQUEST
    with _REQUEST_LOCK:
        delay = _REST_SPACING - (_time.monotonic() - _LAST_REQUEST)
        if delay > 0:
            _time.sleep(delay)
        _LAST_REQUEST = _time.monotonic()  # failed attempts also consume the budget


@_contextlib.contextmanager
def _quiet_transport():
    """Also suppress configured HTTP debug tracing (profile URLs contain a token).

    This client is foreground-only. Restore the caller's logging configuration
    even when transport fails; never replace credentials with loggable placeholders.
    """
    previous = _logging.root.manager.disable
    try:
        _logging.disable(_logging.CRITICAL)
        with _contextlib.ExitStack() as stack:
            for cls in (_http_client.HTTPConnection, _http_client.HTTPSConnection,
                        _requests.packages.urllib3.connection.HTTPConnection,
                        _requests.packages.urllib3.connection.HTTPSConnection):
                stack.enter_context(_patch.object(cls, 'debuglevel', 0))
            yield
    finally:
        _logging.disable(previous)


def _request(sdk, route, method, parameters=None):
    allowed = _ROUTES.get(route)
    if allowed is None or method != allowed[0]:
        raise AngelError('SmartAPI operation is not permitted.')
    _pace()
    headers = {'Content-type': 'application/json', 'Accept': 'application/json',
               'X-PrivateKey': sdk.api_key, 'X-UserType': 'USER', 'X-SourceID': 'WEB',
               'X-ClientLocalIP': sdk.clientLocalIp, 'X-ClientPublicIP': sdk.clientPublicIp,
               'X-MACAddress': sdk.clientMacAddress}
    if sdk.access_token:
        headers['Authorization'] = 'Bearer ' + sdk.access_token
    try:
        # Match the pinned SDK's parameter serialization, without its unsafe logging.
        with _quiet_transport(), _requests.request(method, _ROOT + allowed[1], headers=headers,
                               data=_json.dumps(parameters or {}) if method == 'POST' else None,
                               params=_json.dumps(parameters or {}) if method == 'GET' else None,
                               timeout=15, verify=True, allow_redirects=False) as response:
            result = _response_json(response, api_errors=True)
        return _api_result(result, http_status=200)
    except _Failure:
        raise
    except Exception as exc:
        raise _transport_failure(exc) from None


class _Silent:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


def _sdk_types():
    """The ONLY SDK import site. Import-time IP lookup never reaches the network."""
    previous_bytecode = _sys.dont_write_bytecode
    _sys.dont_write_bytecode = True
    try:
        if _metadata.version('smartapi-python') != _SDK_VERSION:
            raise AngelError('Install the pinned optional Angel requirements.')
        import logzero
        with _patch.object(_requests, 'get', return_value=_Namespace(text='127.0.0.1')), \
                _patch.object(logzero, 'logger', _Silent()), \
                _patch.object(_socket, 'gethostbyname', return_value='127.0.0.1'), \
                _patch.object(_uuid, 'getnode', return_value=0):
            import SmartApi.smartConnect as rest
            import SmartApi.smartWebSocketV2 as feed
        rest.logger = rest.log = feed.logger = _Silent()

        class _ReadOnlySDK(rest.SmartConnect):
            clientLocalIp = clientPublicIp = '127.0.0.1'
            clientMacAddress = '00:00:00:00:00:00'

            def __init__(self, api_key):
                # Do not call the SDK constructor: it creates credential-bearing log files.
                self.api_key = api_key
                self.access_token = self.refresh_token = self.feed_token = self.userId = None

            def _request(self, route, method, parameters=None):
                return _request(self, route, method, parameters)

        return _ReadOnlySDK, feed.SmartWebSocketV2
    except Exception:
        raise AngelError('Install the pinned optional Angel requirements.') from None
    finally:
        _sys.dont_write_bytecode = previous_bytecode


def check_setup():
    """Offline setup check for the user's terminal (P8-071): never reads ANGEL_API_KEY or any other
    credential and never contacts Angel. [(item, ok, detail)] for the Python in use, the pinned SDK,
    its two optional dependencies, and loading the SDK the way the wrapper does (network, logging
    and bytecode blocked)."""
    results = [('Python', True, f'{_sys.executable} {_sys.version.split()[0]}')]
    for name, required in (('smartapi-python', _SDK_VERSION), ('logzero', None), ('websocket-client', None)):
        try:
            version = _metadata.version(name)
        except _metadata.PackageNotFoundError:
            results.append((name, False, 'not installed: see setup step 1'))
            continue
        if required and version != required:
            results.append((name, False, f'{version} installed, {required} required: see setup step 1'))
        else:
            results.append((name, True, version))
    try:
        _sdk_types()
        results.append(('SDK load', True, 'loads offline through the wrapper'))
    except AngelError:
        results.append(('SDK load', False, 'the SDK could not be loaded: see setup step 1'))
    return results


def _number(value):
    if isinstance(value, bool):
        raise AngelError('Invalid market data.')
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise AngelError('Invalid market data.') from None
    if not _math.isfinite(number) or number < 0:
        raise AngelError('Invalid market data.')
    return number


def _exchange_time(value):
    if not value:
        return None
    try:
        stamp = _dt.datetime.fromisoformat(value)
    except (ValueError, TypeError):
        try:
            stamp = _dt.datetime.strptime(value, '%d-%b-%Y %H:%M:%S')
        except (ValueError, TypeError):
            raise AngelError('Invalid exchange timestamp.') from None
    return (stamp if stamp.tzinfo else stamp.replace(tzinfo=_IST)).astimezone(_IST).isoformat()


HEARTBEAT_SECONDS = 10      # protocol PING and text "ping"; Angel documents "every 30 sec" for the text one


def _is_text_pong(message):
    if isinstance(message, str):
        message = message.encode('utf-8', 'replace')
    return isinstance(message, (bytes, bytearray)) and bytes(message).strip().lower() == b'pong'


class _FeedLog:
    """Close summary for one feed connection: numbers and fixed words only, never frame text."""
    def __init__(self, started):
        self.started = started
        self.last_message = self.ping_sent = self.pong_received = None
        self.text_ping_sent = self.text_pong_received = None
        self.frames = dict(binary=0, text_pong=0, text_other=0, server_ping=0, pong=0)
        self.closed_by = self.close_code = self.reason_kind = None
        self.reason_bytes = 0
        self.ended = None

    def count(self, kind):
        self.frames[kind] += 1

    def close(self, side, at, frame=None, reason_kind=None):
        if self.closed_by is not None:
            return
        self.closed_by, self.ended, self.reason_kind = side, at, reason_kind
        if isinstance(frame, (bytes, bytearray)) and len(frame) >= 2:
            code = int.from_bytes(bytes(frame[:2]), 'big')
            self.close_code = code if 1000 <= code <= 4999 else None
            self.reason_bytes = len(frame) - 2
            self.reason_kind = 'withheld' if self.reason_bytes else 'none'

    def _since(self, mark):
        return None if mark is None or self.ended is None else round(self.ended - mark, 3)

    def summary(self):
        return {'closed_by': self.closed_by, 'close_code': self.close_code, 'close_reason': self.reason_kind,
                'close_reason_bytes': self.reason_bytes, 'connected_seconds': self._since(self.started),
                'seconds_since_last_message': self._since(self.last_message),
                'seconds_since_ping_sent': self._since(self.ping_sent),
                'seconds_since_pong_received': self._since(self.pong_received),
                'seconds_since_text_ping_sent': self._since(self.text_ping_sent),
                'seconds_since_text_pong_received': self._since(self.text_pong_received),
                'frames': dict(self.frames)}

    def attach(self, failure):
        failure.stream_summary = self.summary()
        return failure


class AngelMarketData:
    """Seven explicit capabilities; all state is private and remains in memory.

    as_of is mandatory for reads. Live endpoints cannot satisfy a historical as-of:
    it must equal today's IST date. Historical candles retain their event timestamp
    but are newly observed today, never presented as knowledge available in the past.
    Run only one broker client process per account; throttling is process-wide.
    """
    def __init__(self):
        self._sdk = self._feed_type = None
        self._session_day = self._master_day = None
        self._master = {}
        self._master_observed_at = None
        self._client_id = self._api_key = None
        self._streaming = False

    def _as_of(self, as_of):
        if as_of != _now().date().isoformat():
            raise AngelError('Live market data requires today as the knowledge date.')

    def _clear(self):
        if self._sdk is not None:
            for name in ('api_key', 'access_token', 'refresh_token', 'feed_token', 'userId'):
                setattr(self._sdk, name, None)
        self._sdk = self._client_id = self._api_key = self._session_day = None

    def _active(self, as_of):
        if self._session_day != _now().date() or self._sdk is None:
            self._clear()
            raise AngelError('Log in for the current IST day.')
        self._as_of(as_of)

    def _call(self, method, *args):
        try:
            return _api_result(method(*args))['data']
        except _Failure:
            raise
        except Exception as exc:
            raise _transport_failure(exc) from None

    def login(self):
        """Prompt in the user's terminal only. Reuse an active same-day session."""
        day = _now().date()
        if self._sdk is not None and self._session_day == day:
            return
        self._clear()
        key = _os.environ.get('ANGEL_API_KEY')
        if not key:
            raise AngelError('Set ANGEL_API_KEY in the environment.')
        sdk_type, self._feed_type = _sdk_types()
        try:
            # Never accept getpass's fallback to echoed input.
            with _warnings.catch_warnings():
                _warnings.simplefilter('error', _getpass_module.GetPassWarning)
                client = _getpass_module.getpass('Angel client ID: ')
                pin = _getpass_module.getpass('Angel PIN: ')
                otp = _getpass_module.getpass('Angel TOTP: ')
            if not client or not pin or not otp:
                raise AngelError('Login input is required.')
            self._sdk = sdk_type(key)
            self._client_id, self._api_key = client, key
            self._call(self._sdk.generateSession, client, pin, otp)
            if _now().date() != day:
                raise AngelError('Login crossed the IST session boundary.')
            self._session_day = day
        except (Exception, KeyboardInterrupt) as exc:
            # Login can have minted a token before its implicit profile read fails.
            # Best-effort revoke that partial session, then always clear local state.
            try:
                if self._sdk is not None and self._sdk.access_token:
                    self._call(self._sdk.terminateSession, self._client_id)
            except Exception:
                pass
            self._clear()
            if isinstance(exc, _Failure):
                raise exc from None
            raise AngelError('Login failed; use a private interactive terminal.') from None

    def logout(self):
        """Attempt logout once, then discard all local credentials even on failure."""
        try:
            if self._sdk is not None and self._session_day == _now().date():
                self._call(self._sdk.terminateSession, self._client_id)
        finally:
            self._clear()

    def profile(self, *, as_of):
        self._active(as_of)
        data = self._call(self._sdk.getProfile, self._sdk.refresh_token)
        self._active(as_of)
        # Session responses may contain credentials. Return only a bounded profile field.
        return {'exchanges': [x for x in data.get('exchanges', []) if x in ('NSE', 'BSE', 'NFO', 'BFO', 'MCX', 'CDS')]}

    def download_scrip_master(self, symbols, *, as_of):
        """Exact current NSE EQ matches only; ambiguous/missing symbols are listed."""
        self._as_of(as_of)
        if self._master_day != as_of:
            _pace()
            try:
                with _quiet_transport(), _requests.get(_MASTER, timeout=(10, 60), verify=True,
                                                       allow_redirects=False) as response:
                    rows = _response_json(response)
                if not isinstance(rows, list):
                    raise _Failure('structure')
                candidates, invalid = {}, set()
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    name, token = row.get('symbol'), row.get('token')
                    if (row.get('exch_seg') != 'NSE' or not isinstance(name, str)
                            or not name.endswith('-EQ') or len(name) <= 3
                            or row.get('expiry') or row.get('instrumenttype', '') not in ('', 'EQ')):
                        continue
                    symbol = name[:-3]
                    if (type(token) not in (str, int) or not str(token).isascii()
                            or not str(token).isdigit() or len(str(token)) > 20 or int(token) <= 0):
                        invalid.add(symbol)
                        continue
                    candidates.setdefault(symbol, set()).add(str(token))
                # A token shared by different identities is not a usable exact mapping.
                owners = {}
                for symbol, tokens in candidates.items():
                    for token in tokens:
                        owners.setdefault(token, set()).add(symbol)
                self._as_of(as_of)
                self._master = {s: next(iter(v)) for s, v in candidates.items()
                                if s not in invalid and len(v) == 1 and len(owners[next(iter(v))]) == 1}
                self._master_day = as_of
                self._master_observed_at = _now().isoformat()
            except AngelError:
                raise
            except Exception as exc:
                raise _transport_failure(exc) from None
        requested = sorted(set(symbols))
        return {'mapped': {s: self._master[s] for s in requested if s in self._master},
                'unmapped': [s for s in requested if s not in self._master], 'observed_at': self._master_observed_at}

    def _token(self, symbol, as_of):
        result = self.download_scrip_master([symbol], as_of=as_of)
        if result['unmapped']:
            raise AngelError('NSE EQ symbol has no unique scrip-master match.')
        return result['mapped'][symbol]

    def quote(self, symbol, *, as_of):
        self._active(as_of)
        token = self._token(symbol, as_of)
        data = self._call(self._sdk.getMarketData, 'FULL', {'NSE': [token]})
        self._active(as_of)
        try:
            rows = data['fetched']
            if len(rows) != 1 or str(rows[0]['symbolToken']) != token or rows[0]['exchange'] != 'NSE':
                raise AngelError('Quote identity mismatch.')
            row = rows[0]
            depth = row.get('depth') or {}
            def best(side):
                levels = depth.get(side) or []
                return _number(levels[0]['price']) if levels else None
            return {'symbol': symbol, 'price': _number(row['ltp']), 'bid': best('buy'), 'ask': best('sell'),
                    'volume': _number(row['tradeVolume']) if row.get('tradeVolume') is not None else None,
                    'exchange_timestamp': _exchange_time(row.get('exchFeedTime')),
                    'recorded_at': _now().isoformat(), 'knowledge_date': as_of}
        except Exception:
            raise AngelError('Invalid quote response.') from None

    def candles(self, symbol, day, *, as_of):
        """One day of one-minute raw bars; no changes, returns or outcome labels."""
        self._active(as_of)
        try:
            event_day = _dt.date.fromisoformat(day)
        except (ValueError, TypeError):
            raise _Failure('candle_date') from None
        if day != event_day.isoformat():
            raise _Failure('candle_date')
        if event_day >= _now().date():
            raise _Failure('candle_date')
        token = self._token(symbol, as_of)
        data = self._call(self._sdk.getCandleData, {'exchange': 'NSE', 'symboltoken': token,
                          'interval': 'ONE_MINUTE', 'fromdate': day + ' 09:15', 'todate': day + ' 15:30'})
        self._active(as_of)
        try:
            if not isinstance(data, list):
                raise _Failure('structure')
            rows, seen = [], set()
            for bar in data:
                if not isinstance(bar, list) or len(bar) != 6:
                    raise _Failure('structure')
                stamp = _exchange_time(bar[0])
                moment = _dt.datetime.fromisoformat(stamp)
                if moment.date() != event_day or not _dt.time(9, 15) <= moment.time() <= _dt.time(15, 30) or stamp in seen:
                    raise AngelError('Invalid candle timestamp.')
                seen.add(stamp)
                values = [_number(value) for value in bar[1:6]]
                if len(values) != 5:
                    raise AngelError('Invalid candle data.')
                rows.append(dict(timestamp=stamp, open=values[0], high=values[1], low=values[2],
                                 close=values[3], volume=values[4], knowledge_date=as_of,
                                 recorded_at=_now().isoformat()))
            if not rows:
                raise AngelError('No candle data returned.')
            return sorted(rows, key=lambda row: row['timestamp'])
        except AngelError:
            raise
        except Exception:
            raise AngelError('Invalid or unavailable candle data.') from None

    def stream(self, symbols, on_tick, *, as_of, seconds=30):
        """Foreground feed, bounded duration; no worker, timer or reconnect loop.

        One connection, one subscription mode, <= 1000 symbols. Official quota:
        https://smartapi.angelone.in/smartapi/forum/topic/1861/user-feedback-websocket-2-0-beta-rollout-python-language/1
        SDK decoder and subscribe framing; verified TLS websocket transport with
        finite reads also stops on quiet feeds, interruption or IST midnight.
        """
        self._active(as_of)
        symbols = sorted(set(symbols))
        if not symbols or len(symbols) > 1000 or not 0 < seconds <= 86400 or self._streaming:
            raise AngelError('Invalid or concurrent feed request.')
        mapped = self.download_scrip_master(symbols, as_of=as_of)
        if mapped['unmapped']:
            raise AngelError('Feed contains unmapped NSE EQ symbols.')
        reverse = {token: symbol for symbol, token in mapped['mapped'].items()}
        with _quiet_transport():
            sock = log = None
            self._streaming = True
            try:
                import websocket
                websocket.enableTrace(False)
                sock = websocket.create_connection(_FEED, timeout=min(10, seconds), redirect_limit=0,
                        sslopt={'cert_reqs': _ssl.CERT_REQUIRED, 'check_hostname': True},
                        header={'Authorization': 'Bearer ' + self._sdk.access_token, 'x-api-key': self._api_key,
                                'x-client-code': self._client_id, 'x-feed-token': self._sdk.feed_token})
                # Only the decoder/subscription methods are needed; the SDK constructor writes logs.
                parser = self._feed_type.__new__(self._feed_type)
                parser.wsapp, parser.input_request_dict = sock, {}
                parser.subscribe('praman', 1, [{'exchangeType': 1, 'tokens': list(reverse)}])
                log = _FeedLog(_time.monotonic())
                deadline = log.started + seconds
                heartbeat = log.started
                while _time.monotonic() < deadline:
                    self._active(as_of)
                    now = _time.monotonic()
                    if now >= heartbeat:
                        # Protocol PING (the SDK's run_forever(ping_interval=10)) and Angel's documented
                        # text heartbeat ("ping" at least every 30 seconds; "pong" comes back).
                        sock.ping()
                        sock.send('ping')
                        log.ping_sent = log.text_ping_sent = now
                        heartbeat = now + HEARTBEAT_SECONDS
                    sock.settimeout(max(0.001, min(deadline - now, heartbeat - now, 1)))
                    try:
                        # recv_data answers the server's PINGs itself (websocket-client 1.8.0
                        # recv_data_frame) and returns control frames so they can be counted.
                        opcode, message = sock.recv_data(control_frame=True)
                    except websocket.WebSocketTimeoutException:
                        continue
                    except websocket.WebSocketConnectionClosedException:
                        log.close('connection_lost', _time.monotonic())
                        raise log.attach(_Failure('ws_closed')) from None
                    log.last_message = _time.monotonic()
                    if opcode == websocket.ABNF.OPCODE_CLOSE:
                        log.close('server', log.last_message, message)
                        raise log.attach(_Failure('ws_closed'))
                    if opcode == websocket.ABNF.OPCODE_PING:
                        log.count('server_ping')
                        continue
                    if opcode == websocket.ABNF.OPCODE_PONG:
                        log.count('pong')
                        log.pong_received = log.last_message
                        continue
                    if _is_text_pong(message):
                        log.count('text_pong')
                        log.text_pong_received = log.last_message
                        continue
                    if opcode != websocket.ABNF.OPCODE_BINARY or not isinstance(message, bytes):
                        log.count('text_other')
                        log.close('client', log.last_message)
                        raise log.attach(_Failure('api_rejection'))
                    log.count('binary')
                    try:
                        raw = parser._parse_binary_data(message)
                        token = raw.get('token')
                        if token not in reverse or raw.get('exchange_type') != 1 or raw.get('subscription_mode') != 1:
                            raise ValueError
                        stamp = _dt.datetime.fromtimestamp(_number(raw['exchange_timestamp']) / 1000, _IST)
                        tick = {'symbol': reverse[token], 'timestamp': stamp.isoformat(),
                                'price': _number(raw['last_traded_price']) / 100,
                                'recorded_at': _now().isoformat(), 'knowledge_date': as_of}
                    except Exception:
                        log.close('client', _time.monotonic())
                        raise log.attach(_Failure('feed_parse')) from None
                    self._active(as_of)
                    try:
                        on_tick(tick)
                    except Exception:
                        log.close('client', _time.monotonic())
                        raise log.attach(_Failure('callback')) from None
                log.close('client', _time.monotonic(), reason_kind='deadline')
                return log.summary()
            except AngelError as exc:
                if log is not None and getattr(exc, 'stream_summary', None) is None:
                    log.close('client', _time.monotonic())
                    log.attach(exc)
                raise
            except KeyboardInterrupt:
                failure = _Failure('interrupted')
                if log is not None:
                    log.close('client', _time.monotonic(), reason_kind='interrupted')
                    log.attach(failure)
                raise failure from None
            except Exception as exc:
                failure = _transport_failure(exc)
                if log is not None:
                    log.close('connection_lost' if failure.category in ('ws_closed', 'network') else 'client',
                              _time.monotonic())
                    log.attach(failure)
                raise failure from None
            finally:
                self._streaming = False
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass
