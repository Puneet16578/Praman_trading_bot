"""T1 rehearsal on synthetic fixtures: random labels, the real outcome sealed, nothing compared."""
import ast
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from desk import outcome_firewall
from desk.t1 import features as F
from desk.t1 import inputs as I
from desk.t1_outcome import reader as R
from desk.t1_outcome import rehearsal as H

ROOT = Path(__file__).resolve().parents[1]


def weekdays(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def fixture(n=220, m=12, low_scale=1.0, seed=7):
    rng = np.random.default_rng(seed)
    close = 100 + rng.random((n, m)) * 10
    low = close * 0.98 * low_scale
    breaks = np.zeros((n, m))
    breaks[120, 3] = 1                                           # an unadjustable action for stock 3
    for a in (close, low):
        a[90, 5] = np.nan                                        # stock 5 has no bar on session 90
    panel = F.Panel(sessions=weekdays('2020-01-01', n), symbols=[f'S{j}' for j in range(m)], raw_close=close.copy(),
                    close=close, high=close * 1.01, low=low, known=np.arange(n)[:, None] * np.ones((1, m)),
                    breaks=np.cumsum(breaks, axis=0), identity=np.full((n, m), F.EQUITY, dtype=np.int8),
                    open=close.copy())
    state_rng = np.random.default_rng(11)
    out = dict(atr_pct=1 + state_rng.random((n, m)) * 5,
               v1_adverse=np.where(np.arange(n) % 40 < 8, 1.0, 0.0),
               v2_adverse=np.where(np.arange(n) % 50 < 10, 1.0, np.where(np.arange(n) % 97 == 0, np.nan, 0.0)),
               v3_negative=(state_rng.random((n, m)) < 0.5).astype(float))
    cause = np.full((n, m), '', dtype=object)
    cause[:, 11] = 'identity_unknown'
    period = np.array(['outside'] * 10 + ['development'] * (n - 30) + ['development_purged'] * 20, dtype=object)
    bounds = [2.0, 3.0, 4.0, 5.0]
    return panel, out, cause, period, bounds


CHOICES = dict(seed=H.REHEARSAL_SEED, rate=H.REHEARSAL_RATE, usable='computable_with_sample_minimums',
               method='linear', coverage_numerator='state_known')


class SealTest(unittest.TestCase):
    def test_script_seals_even_input_loading_and_restores_reader_on_failure(self):
        from unittest.mock import patch
        from scripts import t1_rehearsal as script
        original = R.read_adverse20
        def accidental_outcome_read(*args):
            R.read_adverse20(None, {}, period='development')
        with patch.object(script.inputs, 'load', side_effect=accidental_outcome_read):
            with self.assertRaises(H.RealOutcomeSealed):
                script.main()
        self.assertIs(R.read_adverse20, original)

    def test_the_real_reader_and_the_firewall_raise_inside_the_seal_and_come_back_after(self):
        original = (R.read_adverse20, outcome_firewall.evaluate_event)
        with H.outcomes_sealed():
            with self.assertRaises(H.RealOutcomeSealed):
                R.read_adverse20(None, {}, period='development')
            with self.assertRaises(H.RealOutcomeSealed):
                outcome_firewall.evaluate_event('2020-01-01', lambda: None)
            with self.assertRaises(H.RealOutcomeSealed):
                outcome_firewall.require_outcome_access('2020-01-01')
        self.assertEqual((R.read_adverse20, outcome_firewall.evaluate_event), original)

    def test_the_rehearsal_runs_end_to_end_inside_the_seal(self):
        panel, out, cause, period, bounds = fixture()
        with H.outcomes_sealed():
            report = H.rehearse(panel, out, cause, period, bounds, **CHOICES)
        self.assertEqual(report['development_sessions'], 190)
        self.assertEqual(report['identity_excluded'], 190)              # stock 11 on every development day
        self.assertEqual(set(report['variants']), {'V1', 'V2', 'V3'})
        v1, v3 = report['variants']['V1'], report['variants']['V3']
        self.assertEqual((v1['block'], v3['block']), (60, 20))
        self.assertEqual(v1['usable_draws'] + v1['unusable_draws'], 2000)
        self.assertEqual(v1['coverage'], 1.0)
        self.assertLess(report['variants']['V2']['coverage'], 1.0)     # V2 has UNKNOWN sessions
        self.assertTrue(all(r['decision_step_ran'] for r in report['variants'].values()))
        self.assertIsNotNone(v1['spells'])
        self.assertIsNone(v3['spells'])                                # spells: V1 and V2 only

    def test_choices_must_be_given(self):
        panel, out, cause, period, bounds = fixture()
        with self.assertRaises(TypeError):
            H.rehearse(panel, out, cause, period, bounds)


class NothingComparedTest(unittest.TestCase):
    def test_empty_calendar_dates_stay_and_purged_bars_complete_last_decision(self):
        panel, out, cause, period, bounds = fixture()
        cause[50, :] = 'identity_unknown'
        dev, base, _, complete = H.development_rows(panel, out, cause, period, bounds, seed=1, rate=0.1)
        self.assertIn(50, dev)
        self.assertNotIn(list(dev).index(50), base['date_idx'])
        self.assertEqual(dev[-1], len(panel.sessions) - 21)
        self.assertTrue(complete[base['date_idx'] == len(dev) - 1].all())
        panel.open[-1, 0] = np.nan
        _, changed, _, complete = H.development_rows(panel, out, cause, period, bounds, seed=1, rate=0.1)
        self.assertFalse(complete[changed['date_idx'] == len(dev) - 1][0])

    def test_window_completeness_needs_every_bar_and_no_break_and_ignores_price_levels(self):
        panel, *_ = fixture()
        cols = np.arange(12)
        complete = H.complete_windows(panel, 80, cols)                   # window 81..100 contains session 90
        self.assertFalse(complete[5])
        self.assertTrue(complete[4])
        self.assertFalse(H.complete_windows(panel, 110, cols)[3])        # window 111..130 contains the break at 120
        self.assertTrue(H.complete_windows(panel, 121, cols)[3])         # the break is now before the window
        cheap, *_ = fixture(low_scale=0.01)                               # every low far below any threshold
        np.testing.assert_array_equal(H.complete_windows(cheap, 80, cols), complete)
        self.assertFalse(H.complete_windows(panel, len(panel.sessions) - 20, cols).any())   # no full window left

    def test_labels_are_the_same_whatever_the_prices(self):
        a = H.development_rows(*fixture(), seed=1, rate=0.1)
        b = H.development_rows(*fixture(low_scale=0.01), seed=1, rate=0.1)
        np.testing.assert_array_equal(a[1]['outcome'], b[1]['outcome'])
        np.testing.assert_array_equal(a[3], b[3])
        self.assertTrue(np.isnan(a[1]['outcome'][~a[3]]).all())        # no label without a full window
        self.assertTrue(set(np.unique(a[1]['outcome'][a[3]])) <= {0.0, 1.0})

    def test_neither_the_rehearsal_nor_its_script_names_the_real_label(self):
        banned = {'read_adverse20', '_labels', 'ADVERSE_FRACTION', 'tails', 'shadow_analysis', 'reader'}
        for path in (ROOT / 'desk' / 't1_outcome' / 'rehearsal.py', ROOT / 'scripts' / 't1_rehearsal.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
                    {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | \
                    {a.name.split('.')[-1] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                     for a in n.names} | \
                    {(n.module or '').split('.')[-1] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            with self.subTest(path=path.name):
                self.assertEqual(names & banned, set())


class WeekendCalendarTest(unittest.TestCase):
    def test_exclude_drops_stored_weekend_sessions_and_store_keeps_them(self):
        stored = {'2024-01-19', '2024-01-20', '2024-01-23'}
        index = {'2019-09-30', '2024-01-19', '2024-01-20', '2024-01-22', '2024-01-23'}
        kept, _, _ = F.build_calendar(stored, index, weekends='store')
        dropped, missing, specials = F.build_calendar(stored, index, weekends='exclude')
        self.assertIn('2024-01-20', kept)
        self.assertNotIn('2024-01-20', dropped)
        self.assertEqual((missing, specials), (['2024-01-22'], ['2024-01-20']))
        with self.assertRaises(ValueError):
            F.build_calendar(stored, index, weekends='maybe')

    def test_the_panel_leaves_the_weekend_bars_out(self):
        from desk.t1.panel import load_panel
        from src.bitemporal.connection import get_connection, init_db
        days = ['2024-01-18', '2024-01-19', '2024-01-20', '2024-01-23']          # 20 Jan 2024 was a Saturday
        with tempfile.TemporaryDirectory() as folder:
            conn = get_connection(str(Path(folder) / 'p.db'))
            init_db(conn)
            for d in days:
                conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                             'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                             "('AAA',?,?,10,10,10,10,10,1000,'EQ','fixture',?)", (d, d, d))
            conn.commit()
            index = {s: {d: dict(close=100.0) for d in days} for s in I.SERIES}
            kept = load_panel(conn, index, [], end=days[-1], weekends='store')
            dropped = load_panel(conn, index, [], end=days[-1], weekends='exclude')
            conn.close()
        self.assertIn('2024-01-20', kept.sessions)
        self.assertNotIn('2024-01-20', dropped.sessions)
        self.assertEqual(int(np.isfinite(dropped.raw_close).sum()), 3)


if __name__ == '__main__':
    unittest.main()
