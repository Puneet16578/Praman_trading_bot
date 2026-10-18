"""Fixture-only validation of the one-shot development assembly and rendering."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

from desk.t1 import features as F
from desk.t1_outcome import development as D, reader as R
from tests.test_t1_rehearsal import fixture


class DevelopmentTest(unittest.TestCase):
    def test_labels_are_aligned_to_eligible_rows_and_all_tables_render(self):
        panel, out, cause, period, bounds = fixture()
        # Use actual feature computation for the descriptive fields; synthetic states
        # provide both groups without requiring hundreds of index warm-up sessions.
        actual = F.compute(panel)
        actual.update(out)
        with patch.object(D.R, 'read_adverse20', wraps=R.read_adverse20) as called:
            result = D.evaluate(panel, actual, cause, period, bounds)
        called.assert_called_once()
        self.assertEqual(result['eligible'], 190*11)
        self.assertEqual(result['identity_excluded'], 190)
        self.assertEqual(sum(c['candidates'] for c in result['baseline'].values()), 190*11)
        self.assertEqual(result['variants']['V1']['positive_quintiles'], 0)
        for variant in result['variants'].values():
            self.assertEqual(sum(c['candidates'] for c in variant['availability'].values()), 190*11)
            self.assertEqual(variant['intervals']['usable_draws']+variant['unusable_draws'], 2000)
            self.assertIn(variant['verdict'], ('FAIL', 'INCONCLUSIVE'))
        json.dumps(result, allow_nan=False)
        text = D.render(result, dict(code_commit='fixture', inputs={}))
        for expected in ('PARTIALLY EXPOSED', 'V0 q1', 'unknown', 'Risk difference pp',
                         'Matched V0', 'Input manifest', 'V1', 'V2', 'V3', '**190**'):
            self.assertIn(expected, text)
        self.assertNotIn("; '\n", text)

    def test_later_panel_is_refused_before_reader(self):
        panel, out, cause, period, bounds = fixture()
        panel.sessions[-1] = '2025-01-01'
        with patch.object(D.R, 'read_adverse20') as called:
            with self.assertRaises(R.OutcomeReadRefused):
                D.evaluate(panel, out, cause, period, bounds)
        called.assert_not_called()

    def test_no_future_tail_changes_any_prior_feature_or_threshold(self):
        from tests.test_t1_features import panel, ramp
        n, extra = 300, 25
        index = {s: np.arange(n+extra, dtype=float)+100 for s in ('NIFTY 50','NIFTY 500','INDIA VIX')}
        short = panel(ramp(n, 3), index={s:x[:n] for s,x in index.items()})
        long = panel(ramp(n+extra, 3), index=index)
        long.close[n:] *= 50
        for x in long.index.values():
            x[n:] *= 99
        a, b = F.compute(short), F.compute(long)
        for key in a:
            with self.subTest(feature=key):
                np.testing.assert_array_equal(a[key], b[key][:n])

    def test_attempt_marker_prevents_second_run_before_opening_store(self):
        from scripts import t1_development as script
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'data/t1').mkdir(parents=True)
            (root/'data/t1/development_20261018.started.json').write_text('{}')
            def git(args, **kwargs):
                answer = '' if args[1] == 'status' else ('master' if args[1] == 'branch' else 'fixture')
                return type('Result', (), {'stdout':answer})()
            with patch.object(script, 'ROOT', root), patch.object(script.subprocess, 'run', side_effect=git), \
                 patch.object(script, 'open_readonly') as opened:
                with self.assertRaises(FileExistsError):
                    script.main()
            opened.assert_not_called()
