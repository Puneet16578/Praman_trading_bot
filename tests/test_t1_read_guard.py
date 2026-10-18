"""Pre-read isolation: no later payload opens or post-development SQL queries."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from desk.t1 import inputs as I
from desk.t1.panel import load_panel, snapshot_identities
from desk.t1.read_guard import T1ReadRefused


class ReadBoundaryTest(unittest.TestCase):
    def test_future_end_raises_before_any_sql(self):
        conn = Mock()
        with self.assertRaises(T1ReadRefused):
            load_panel(conn, {}, [], end='2025-01-01')
        conn.execute.assert_not_called()

    def test_no_post_end_calendar_query(self):
        from tests.test_t1_features import weekdays
        days = weekdays('2024-12-02', 22)
        class Connection:
            def execute(self, sql, args):
                if 'event_date > ?' in sql or any(v > '2024-12-31' for v in args):
                    raise AssertionError('post-development query attempted')
                if sql.startswith('SELECT DISTINCT'):
                    return [(d,) for d in days]
                if sql.startswith('SELECT symbol, action_type'):
                    return []
                class Cursor:
                    def fetchall(self):
                        return [('A', d, d, 10, 10, 10, 10) for d in days]
                return Cursor()
        p = load_panel(Connection(), {s: {} for s in I.SERIES}, [])
        self.assertEqual(p.forward_sessions, [])
        self.assertLessEqual(p.sessions[-1], '2024-12-31')

    def test_future_index_and_snapshot_arguments_are_refused(self):
        for index, snaps in [({'NIFTY 50': {'2025-01-01': {}}}, []),
                              ({}, [('2025-01-01', {})])]:
            conn = Mock()
            with self.assertRaises(T1ReadRefused):
                load_panel(conn, index, snaps)
            conn.execute.assert_not_called()

    def test_later_source_payloads_are_never_opened(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entries = [dict(label='history_NIFTY50_2025-01-01_2025-12-31', status=200, file='future.json'),
                       dict(label='snapshot_2025-01-01', status=200, file='future.csv')]
            (root/'requests.jsonl').write_text('\n'.join(map(json.dumps, entries)), encoding='utf-8')
            (root/'cm_2025-01-01.csv').touch()
            # Any payload read fails. The old code opens future.json / the later ISIN sidecar.
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('payload opened')):
                self.assertEqual(I.history_rows(root), [])
                self.assertEqual(I.snapshot_rows(root), [])
                self.assertEqual(snapshot_identities(root), [])

    def test_mixed_range_is_refused_before_payload_open(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = dict(label='history_NIFTY50_2024-01-01_2025-12-31', status=200, file='mixed.json')
            (root/'requests.jsonl').write_text(json.dumps(entry), encoding='utf-8')
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('payload opened')):
                with self.assertRaises(T1ReadRefused):
                    I.history_rows(root)

    def test_future_end_for_file_loaders_is_refused_before_metadata_read(self):
        with patch.object(Path, 'read_text', side_effect=AssertionError('metadata opened')):
            for fn in (I.load, I.history_rows, I.snapshot_rows, snapshot_identities):
                with self.subTest(loader=fn.__name__), self.assertRaises(T1ReadRefused):
                    fn(Path('not-opened'), end='2025-01-01')
