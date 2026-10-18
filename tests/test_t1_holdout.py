"""Hold-out bounds, frozen constants, unchanged development, and once-only protections."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import numpy as np

from desk.t1 import features as F, inputs as I
from desk.t1.panel import load_panel, snapshot_identities
from desk.t1.provenance import input_hashes
from desk.t1.read_guard import HOLDOUT_END, T1ReadRefused, check_date, holdout_reads
from desk.t1_outcome import development as D, holdout as H, reader as R, rehearsal as RH
from tests.test_t1_rehearsal import fixture, weekdays, CHOICES


def holdout_fixture():
    panel, out, cause, period, bounds = fixture()
    panel.sessions = weekdays('2025-01-01', len(panel.sessions))
    period[period == 'development'] = 'holdout_2025'
    period[period == 'development_purged'] = 'holdout_censored'
    actual = F.compute(panel)
    actual.update(out)
    return panel, actual, cause, period, bounds


class BoundTest(unittest.TestCase):
    def test_holdout_scope_accepts_2025_but_restores_development_ceiling(self):
        with self.assertRaises(T1ReadRefused):
            check_date('2025-01-01')
        with holdout_reads():
            self.assertEqual(check_date(HOLDOUT_END), HOLDOUT_END)
            with self.assertRaises(T1ReadRefused):
                check_date('2026-01-01')
        with self.assertRaises(T1ReadRefused):
            check_date('2025-01-01')

    def test_2026_refused_before_sql_or_metadata_access(self):
        conn = Mock()
        with holdout_reads(), patch.object(Path, 'read_text', side_effect=AssertionError('metadata read')):
            for fn in (I.load, I.history_rows, I.snapshot_rows, snapshot_identities):
                with self.subTest(fn=fn.__name__), self.assertRaises(T1ReadRefused):
                    fn(Path('absent'), end='2026-01-01')
            with self.assertRaises(T1ReadRefused):
                load_panel(conn, {}, [], end='2026-01-01')
            with self.assertRaises(T1ReadRefused):
                input_hashes(conn, Path('absent'), Path('absent'), end='2026-01-01')
        conn.execute.assert_not_called()

    def test_later_payloads_and_isin_sidecars_never_opened_in_holdout_scope(self):
        with tempfile.TemporaryDirectory() as td, holdout_reads():
            p = Path(td)
            entries = [dict(label='history_NIFTY50_2026-01-01_2026-12-31', status=200, file='future.json'),
                       dict(label='snapshot_2026-01-01', status=200, file='future.csv')]
            (p/'requests.jsonl').write_text('\n'.join(map(json.dumps, entries)))
            (p/'cm_2026-01-01.csv').touch()
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('future payload opened')):
                self.assertEqual(I.history_rows(p, end=HOLDOUT_END), [])
                self.assertEqual(I.snapshot_rows(p, end=HOLDOUT_END), [])
                self.assertEqual(snapshot_identities(p, end=HOLDOUT_END), [])

    def test_mixed_file_refused_before_open(self):
        with tempfile.TemporaryDirectory() as td, holdout_reads():
            p = Path(td)
            (p/'requests.jsonl').write_text(json.dumps(dict(label='history_NIFTY50_2025-01-01_2026-01-01',
                                                          status=200, file='mixed.json')))
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('payload opened')):
                with self.assertRaises(T1ReadRefused):
                    I.history_rows(p, end=HOLDOUT_END)

    def test_2025_sql_is_bounded_in_panel_and_manifest(self):
        class Connection:
            def execute(self, sql, args):
                self_test.assertNotIn('event_date > ?', sql)
                self_test.assertTrue(all(v <= HOLDOUT_END for v in args))
                self_test.assertIn(HOLDOUT_END, args)
                if sql.startswith('SELECT DISTINCT'):
                    return [('2025-12-30',), ('2025-12-31',)]
                if 'FROM corporate_actions' in sql:
                    return []
                rows = [('A','2025-12-31','2025-12-31',10,10,10,10)]
                class Cursor(list):
                    def fetchall(self):
                        return self
                return Cursor(rows)
        self_test = self
        with tempfile.TemporaryDirectory() as td, holdout_reads():
            p = load_panel(Connection(), {s:{} for s in I.SERIES}, [], end=HOLDOUT_END)
            result = input_hashes(Connection(), Path(td), Path(td), end=HOLDOUT_END)
        self.assertEqual(p.sessions[-1], HOLDOUT_END)
        self.assertEqual(p.forward_sessions, [])
        self.assertEqual(result['logical_store_rows']['eq_bars']['rows'], 1)

    def test_reader_checks_window_and_keeps_firewall(self):
        p, *_ = holdout_fixture()
        with patch.object(R, 'evaluate_event', side_effect=RuntimeError('firewall')) as guarded:
            with self.assertRaisesRegex(RuntimeError, 'firewall'):
                R.read_adverse20(p, {p.sessions[10]: ['S0']}, period='holdout_2025')
            guarded.assert_called_once()
        with self.assertRaises(R.OutcomeReadRefused):
            R.read_adverse20(p, {p.sessions[-20]: ['S0']}, period='holdout_2025')
        p.sessions[-1] = '2026-01-01'
        with patch.object(R, '_labels') as labels:
            with self.assertRaises(R.OutcomeReadRefused):
                R.read_adverse20(p, {p.sessions[10]: ['S0']}, period='holdout_2025')
            labels.assert_not_called()


class FrozenTest(unittest.TestCase):
    def test_constants_are_read_exactly_and_tampering_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root/'data/t1/development_20261018.json'
            p.parent.mkdir(parents=True)
            value = dict(bounds=[1.123456789012345,2.,3.,4.], weights={'1':.1,'2':.15,'3':.2,'4':.25,'5':.3})
            p.write_text(json.dumps(value))
            expected = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()}
            with patch.object(H, 'DEVELOPMENT_HASHES', expected):
                bounds, weights = H.locked_constants(root)
                self.assertEqual(bounds, value['bounds'])
                self.assertEqual(weights, {int(q):v for q,v in value['weights'].items()})
                p.write_text('{}')
                with self.assertRaises(ValueError):
                    H.locked_constants(root)

    def test_evaluation_and_rehearsal_never_estimate_holdout_weights(self):
        args = holdout_fixture()
        weights = {1:.1,2:.15,3:.2,4:.25,5:.3}
        with patch.object(D.C, 'baseline_weights', side_effect=AssertionError('weights recomputed')):
            with RH.outcomes_sealed():
                rehearsal = RH.rehearse(*args, **CHOICES, evaluated_period='holdout_2025', locked_weights=weights)
            result = D.evaluate(*args, evaluated_period='holdout_2025', locked_weights=weights)
        self.assertEqual(result['weights'], weights)
        self.assertEqual(rehearsal['weights'], weights)
        text = D.render(result, dict(code_commit='fixture', inputs={}))
        self.assertIn('PARTIALLY EXPOSED', text)
        self.assertNotIn('no hold-out evaluation was performed', text)
        self.assertTrue(all(r['verdict'] in ('replication success','not met','INCONCLUSIVE') for r in result['variants'].values()))
        with patch.object(R, 'read_adverse20') as reader:
            with self.assertRaises(ValueError):
                D.evaluate(*args, evaluated_period='holdout_2025')
            reader.assert_not_called()

    def test_marker_refuses_repeat_before_store_read(self):
        from scripts import t1_holdout as script
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'data/t1').mkdir(parents=True)
            (root/'data/t1/holdout_2025.started.json').write_text('{}')
            with patch.object(script, 'ROOT', root), patch.object(script, 'git', side_effect=['master','']), \
                 patch.object(script, 'open_readonly') as opened:
                with self.assertRaises(FileExistsError):
                    script.main(['evaluate'])
                opened.assert_not_called()

    def test_rehearsal_seals_loading(self):
        from scripts import t1_holdout as script
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(script, 'ROOT', root), patch.object(H, 'check_development_rehearsal', return_value={}), \
                 patch.object(H, 'development_hashes', return_value={}), patch.object(H, 'locked_constants', return_value=([1,2,3,4],{q:.2 for q in range(1,6)})), \
                 patch.object(H, 'source_hashes', return_value={}), patch.object(script, 'git', return_value='fixture'), \
                 patch.object(script, 'open_readonly', side_effect=lambda *a: R.read_adverse20(None,{},period='holdout_2025')):
                with self.assertRaises(RH.RealOutcomeSealed):
                    script.main(['rehearse','--development-rehearsal','fixture'])


if __name__ == '__main__':
    unittest.main()
