"""T1 probe limits, offline: a fake session, a temporary output folder, no network."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from scripts import t1_source_probe as probe


class FakeResponse:
    def __init__(self, status=200, body=b'a,b\n1,2\n', headers=None):
        self.status_code, self.content = status, body
        self.headers = {'Date': 'Wed, 14 Oct 2026 01:00:00 GMT', 'Last-Modified': 'Mon, 03 Sep 2018 12:30:00 GMT'} \
            | (headers or {})


class ProbeLimitsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        out = Path(folder.name)
        for name, value in (('OUT', out), ('LEDGER', out / 'requests.jsonl'), ('nightly_running', lambda: False)):
            patcher = patch.object(probe, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.sleeps = []
        self.session = Mock()
        self.session.request.return_value = FakeResponse()
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.addCleanup(self.quiet.__exit__, None, None, None)

    def fetch(self, label='x'):
        return probe.fetch(self.session, label, 'GET', 'https://example.invalid/x.csv', ext='csv',
                           sleep=self.sleeps.append)

    def test_each_request_keeps_its_headers_hash_and_file(self):
        entry = self.fetch('snapshot')
        (line,) = probe.ledger()
        self.assertEqual(line['headers']['Last-Modified'], 'Mon, 03 Sep 2018 12:30:00 GMT')
        self.assertEqual(line['headers']['Date'], 'Wed, 14 Oct 2026 01:00:00 GMT')
        self.assertEqual((line['status'], line['bytes'], entry['body']), (200, 8, b'a,b\n1,2\n'))
        self.assertEqual((probe.OUT / line['file']).read_bytes(), b'a,b\n1,2\n')
        self.assertEqual(len(line['sha256']), 64)

    def test_requests_are_spaced_at_least_ten_seconds(self):
        self.fetch('one')
        self.fetch('two')
        self.assertEqual(len(self.sleeps), 1)
        self.assertGreater(self.sleeps[0], 9.0)

    def test_the_budget_is_enforced_across_invocations(self):
        probe.LEDGER.parent.mkdir(parents=True, exist_ok=True)
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        probe.LEDGER.write_text(''.join(json.dumps(dict(n=i, status=200, started_at=old)) + '\n'
                                        for i in range(1, probe.BUDGET + 1)), encoding='utf-8')
        with self.assertRaisesRegex(probe.ProbeStopped, 'budget is used'):
            self.fetch()
        self.session.request.assert_not_called()

    def test_a_403_or_429_stops_this_and_every_later_request(self):
        self.session.request.return_value = FakeResponse(status=429)
        with self.assertRaisesRegex(probe.ProbeStopped, 'HTTP 429'):
            self.fetch()
        self.session.request.return_value = FakeResponse()
        with self.assertRaisesRegex(probe.ProbeStopped, 'refused'):
            self.fetch()
        self.assertEqual(self.session.request.call_count, 1)

    def test_no_request_in_the_nightly_hours_or_while_it_runs(self):
        evening = datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc)        # 18:30 IST
        with self.assertRaisesRegex(probe.ProbeStopped, 'nightly'):
            probe.check_allowed(evening, [])
        for state in (True, None):
            with self.subTest(state=state), patch.object(probe, 'nightly_running', return_value=state):
                with self.assertRaisesRegex(probe.ProbeStopped, 'nightly'):
                    probe.check_allowed(datetime(2026, 10, 14, 4, 0, tzinfo=timezone.utc), [])

    def test_a_network_error_is_logged_by_type_only(self):
        self.session.request.side_effect = ConnectionError('secret detail')
        entry = self.fetch()
        (line,) = probe.ledger()
        self.assertEqual((line['status'], line['error_type'], entry['body']), (None, 'ConnectionError', None))
        self.assertNotIn('secret detail', probe.LEDGER.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
