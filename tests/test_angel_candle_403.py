"""Offline historical HTTP rejection regressions; no credential input or API calls."""
import contextlib
import io
import json
import secrets
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from desk import angel_market_data as a
from scripts import angel_connection_test as smoke
from shared.market_time import IST


class Candle403Test(unittest.TestCase):
    def setUp(self):
        self.secret = secrets.token_urlsafe()
        self.sdk = SimpleNamespace(api_key=self.secret, access_token=self.secret,
                                   clientLocalIp='127.0.0.1', clientPublicIp='127.0.0.1',
                                   clientMacAddress='00:00:00:00:00:00')
        p = patch.object(a, '_pace')
        p.start()
        self.addCleanup(p.stop)

    def response(self, status, payload=None, content=b''):
        r = MagicMock(status_code=status, content=content)
        r.__enter__.return_value = r
        r.json.return_value = payload
        if payload is None:
            r.json.side_effect = ValueError(self.secret)
        return r

    def failure(self, response):
        output = io.StringIO()
        with patch.object(a._requests, 'request', return_value=response) as request, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            with self.assertRaises(a.AngelError) as caught:
                a.AngelMarketData()._call(lambda: a._request(self.sdk, 'api.candle.data', 'POST', {}))
        request.assert_called_once()
        self.assertTrue(request.call_args.kwargs['verify'])
        self.assertFalse(request.call_args.kwargs['allow_redirects'])
        self.assertEqual(output.getvalue(), '')
        self.assertNotIn(self.secret, str(caught.exception) + repr(a.error_details(caught.exception)))
        return caught.exception

    def test_sdk_error_types_survive_http_403_without_message_or_headers(self):
        for kind, category in (('PermissionException', 'permission_denied'),
                               ('TokenException', 'authentication'), ('InputException', 'request_validation')):
            with self.subTest(kind=kind):
                exc = self.failure(self.response(403, {'error_type': kind, 'message': self.secret,
                                                       'headers': {'Authorization': self.secret}}))
                self.assertEqual(a.error_details(exc), {'category': category, 'http_status': 403})

    def test_unknown_empty_html_and_malformed_denials_remain_unclassified(self):
        for payload in (None, {}, [], {'message': 'permission ' + self.secret},
                        {'error_type': self.secret, 'errorcode': self.secret},
                        {'error_type': ['PermissionException'], 'errorcode': {}}):
            with self.subTest(payload_type=type(payload).__name__):
                exc = self.failure(self.response(403, payload, ('<html>' + self.secret).encode()))
                self.assertEqual(exc.category, 'access_denied')
                self.assertEqual(exc.http_status, 403)

    def test_status_never_becomes_success_even_with_success_shaped_json(self):
        exc = self.failure(self.response(403, {'status': True, 'data': []}))
        self.assertEqual(exc.category, 'access_denied')

    def test_success_status_with_sdk_error_envelope_is_still_a_rejection(self):
        exc = self.failure(self.response(200, {'error_type': 'PermissionException', 'message': self.secret}))
        self.assertEqual(exc.category, 'permission_denied')
        self.assertEqual(exc.http_status, 200)

    def test_public_master_does_not_use_authenticated_error_classification(self):
        response = self.response(403, {'error_type': 'PermissionException', 'message': self.secret})
        with self.assertRaises(a.AngelError) as caught:
            a._response_json(response)
        self.assertEqual(caught.exception.category, 'http')
        response.json.assert_not_called()

    def test_allowlisted_broker_codes_on_200_and_403(self):
        for code, category in (('AG8002', 'authentication'), ('AB1010', 'authentication'),
                               ('AB13000', 'broker_date'), ('AB1021', 'rate_limit')):
            for status in (200, 403):
                with self.subTest(code=code, status=status):
                    exc = self.failure(self.response(status, {'status': False, 'errorcode': code,
                                                              'message': self.secret, 'data': None}))
                    self.assertEqual(exc.category, category)

    def test_rate_limit_indicator_requires_exact_match_and_never_retries(self):
        for body in (b'Access denied because of exceeding access rate', b'  ACCESS DENIED because of exceeding access rate. ',
                     b'Access denied because of exceeding rate limit'):
            with self.subTest(body=body):
                exc = self.failure(self.response(403, content=body))
                self.assertEqual((exc.category, exc.http_status), ('rate_limited', 403))
                self.assertNotIn('access rate', str(exc).replace('"exceeding access rate"', ''))
        exc = self.failure(self.response(403, {'status': False, 'message': 'Access denied because of exceeding access rate',
                                               'errorcode': '', 'data': None}))
        self.assertEqual(exc.category, 'rate_limited')
        marker = b'Access denied because of exceeding access rate'
        self.assertEqual(self.failure(self.response(403, content=marker + self.secret.encode())).category,
                         'access_denied')
        self.assertEqual(self.failure(self.response(429)).category, 'rate_limit')

    def test_conflicting_error_indicators_do_not_guess_a_cause(self):
        exc = self.failure(self.response(403, {'error_type': 'PermissionException', 'errorcode': 'AG8002'}))
        self.assertEqual(exc.category, 'access_denied')

    def test_local_bad_date_stops_before_any_request(self):
        now = datetime(2026, 10, 14, 11, tzinfo=IST)
        client = a.AngelMarketData()
        client._sdk, client._session_day = self.sdk, now.date()
        with patch.object(a, '_now', return_value=now), patch.object(a._requests, 'request') as network:
            for day in ('20261013', '2026-10-14', self.secret):
                with self.assertRaises(a.AngelError) as caught:
                    client.candles('SBIN', day, as_of='2026-10-14')
                self.assertEqual(caught.exception.category, 'candle_date')
                self.assertNotIn(self.secret, str(caught.exception))
        network.assert_not_called()

    def test_smoke_reports_window_and_stops_before_stream_then_logs_out(self):
        client = Mock()
        client.quote.return_value = {'exchange_timestamp': '2026-10-14T11:22:28+05:30', 'price': 946.90}
        client.candles.side_effect = self.failure(self.response(403))
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), \
                patch.object(smoke, 'check_setup', return_value=[]), \
                contextlib.redirect_stdout(output):
            self.assertEqual(smoke.main([]), 1)
        client.candles.assert_called_once()
        client.stream.assert_not_called()
        client.logout.assert_called_once()
        text = output.getvalue()
        self.assertIn('2026-09-01 09:15-15:30 IST, one request, no retry', text)
        self.assertIn('Market open at that moment: ', text)
        self.assertIn('HTTP 403', text)
        self.assertIn('cause unclassified', text)
        self.assertNotIn(self.secret, text)

    def smoke_lines(self, now, reply):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now
        client = Mock()
        client.quote.return_value = {'exchange_timestamp': (now.replace(second=0)).isoformat(), 'price': 946.90}
        client.candles.side_effect = self.failure(reply)
        output = io.StringIO()
        with patch.object(smoke, 'AngelMarketData', return_value=client), \
                patch.object(smoke, 'check_setup', return_value=[]), patch.object(smoke, 'datetime', Clock), \
                contextlib.redirect_stdout(output):
            self.assertEqual(smoke.main([]), 1)
        client.candles.assert_called_once_with('SBIN', '2026-09-01', as_of=now.date().isoformat())
        client.stream.assert_not_called()
        return output.getvalue().splitlines()

    def test_failure_line_names_the_category_and_whether_the_market_was_open(self):
        throttled = self.smoke_lines(datetime(2026, 10, 14, 11, 22, 40, tzinfo=IST),
                                     self.response(403, content=b'Access denied because of exceeding access rate'))
        self.assertEqual(throttled[-2:], [
            'Candle request: NSE SBIN ONE_MINUTE 2026-09-01 09:15-15:30 IST, one request, no retry.',
            'Stopped at candles: RATE_LIMITED (Angel\'s "exceeding access rate" reply) (HTTP 403). '
            'Market open at that moment: yes (weekday 09:15-15:30 IST with a fresh quote).'])
        self.assertNotIn('access denied because', '\n'.join(throttled).lower())
        closed = self.smoke_lines(datetime(2026, 10, 14, 15, 45, 10, tzinfo=IST), self.response(403))
        self.assertEqual(closed[-1], 'Stopped at candles: Access denied; cause unclassified (HTTP 403). Verify app '
                         'access and registered static IP with Angel support; do not retry in a loop. '
                         'Market open at that moment: no (weekday 09:15-15:30 IST with a fresh quote).')
        self.assertNotIn('RATE_LIMITED', '\n'.join(closed))

    def test_pinned_sdk_quote_and_candle_wire_contract(self):
        try:
            sdk_type, _ = a._sdk_types()
        except a.AngelError:
            self.skipTest('Optional pinned SDK is not installed')
        sdk = sdk_type(self.secret)
        sdk.access_token = self.secret
        payload = {'exchange': 'NSE', 'symboltoken': '3045', 'interval': 'ONE_MINUTE',
                   'fromdate': '2026-10-13 09:15', 'todate': '2026-10-13 15:30'}
        r = self.response(200, {'status': True, 'data': []})
        with patch.object(a._requests, 'request', return_value=r) as request:
            sdk.getMarketData('FULL', {'NSE': ['3045']})
            sdk.getCandleData(payload)
        quote, candle = request.call_args_list
        self.assertEqual(candle.args, ('POST', a._ROOT + '/rest/secure/angelbroking/historical/v1/getCandleData'))
        self.assertEqual(quote.args, ('POST', a._ROOT + '/rest/secure/angelbroking/market/v1/quote'))
        self.assertEqual(candle.kwargs['headers'], quote.kwargs['headers'])
        self.assertEqual(json.loads(candle.kwargs['data']), payload)
        self.assertEqual(json.loads(quote.kwargs['data']), {'mode': 'FULL', 'exchangeTokens': {'NSE': ['3045']}})
        for call in (quote, candle):
            self.assertIsNone(call.kwargs['params'])
            self.assertEqual(call.kwargs['headers']['Authorization'], 'Bearer ' + self.secret)
            self.assertEqual(call.kwargs['headers']['Content-type'], 'application/json')
            self.assertEqual(call.kwargs['headers']['X-PrivateKey'], self.secret)
            self.assertEqual(call.kwargs['headers']['X-UserType'], 'USER')
            self.assertEqual(call.kwargs['headers']['X-SourceID'], 'WEB')
            self.assertEqual(call.kwargs['timeout'], 15)
            self.assertTrue(call.kwargs['verify'])
            self.assertFalse(call.kwargs['allow_redirects'])
