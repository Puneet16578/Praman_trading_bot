"""T1 outcome step on synthetic fixtures only: no store, no network, no real outcome."""
import ast
import math
import sqlite3
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np

from desk import shadow_analysis
from desk.lib.schema import init_desk_db
from desk.t1 import bootstrap as B
from desk.t1 import features as F
from desk.t1_outcome import contrasts as C
from desk.t1_outcome import reader as R
from desk.t1_outcome import uncertainty as U
from src.signals.event_catalogue import SymbolHistory

ROOT = Path(__file__).resolve().parents[1]


def weekdays(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def synthetic(start='2020-01-01', n=80):
    """One stock: a fall at sessions 20-24, a 1:2 split at 30, no bar at 47, a demerger at 52 and a
    second fall at 70-74 (raw prices, before any adjustment)."""
    days = weekdays(start, n)
    close = np.array([100.0 if i < 30 else 50.0 for i in range(n)])
    low = close * 0.99
    low[20:25] = 75.0
    low[70:75] = 38.0            # (slices past n are empty, so shorter fixtures simply lack the event)
    rows = {}
    for i, d in enumerate(days):
        if i == 47:
            continue
        rows[d] = dict(symbol='S0', open_price=close[i], high_price=close[i] * 1.01, low_price=low[i],
                       close_price=close[i])
    return days, rows


def as_history(days, rows):
    return SymbolHistory(symbol='S0', trading_days=sorted(rows), vintages={d: [(d, r)] for d, r in rows.items()},
                         factor_dates=[days[30]] if len(days) > 30 else [], factor_cum=[2.0] if len(days) > 30 else [],
                         structural_break_dates=[days[52]] if len(days) > 52 else [])


def as_panel(days, rows):
    n = len(days)
    raw = {k: np.full((n, 1), np.nan) for k in ('open_price', 'high_price', 'low_price', 'close_price')}
    for i, d in enumerate(days):
        if d in rows:
            for k in raw:
                raw[k][i, 0] = rows[d][k]
    logf = np.zeros((n, 1))
    if n > 30:
        logf[30, 0] = math.log(2.0)
    cum = np.cumsum(logf, axis=0)
    scale = np.exp(cum - cum[-1])
    brk = np.zeros((n, 1))
    if n > 52:
        brk[52, 0] = 1
    known = np.where(np.isfinite(raw['close_price']), np.arange(n)[:, None], np.inf)
    return F.Panel(sessions=days, symbols=['S0'], raw_close=raw['close_price'], close=raw['close_price'] * scale,
                   high=raw['high_price'] * scale, low=raw['low_price'] * scale, known=known.astype(float),
                   breaks=np.cumsum(brk, axis=0), identity=np.full((n, 1), F.EQUITY, dtype=np.int8),
                   open=raw['open_price'] * scale)


class ExistingDefinitionTest(unittest.TestCase):
    def test_labels_match_the_existing_adverse20_on_every_decision(self):
        days, rows = synthetic()
        hist, p = as_history(days, rows), as_panel(days, rows)
        desk = sqlite3.connect(':memory:')
        desk.row_factory = sqlite3.Row
        init_desk_db(desk)
        decisions = [d for i, d in enumerate(days[:-20]) if d in rows]
        ours = R.read_adverse20(p, {d: ['S0'] for d in decisions}, period='development')
        seen = set()
        for d in decisions:
            theirs = shadow_analysis.tails(hist, d, days, dict(decision_price=rows[d]['close_price'], stop_level=1.0),
                                           None, desk, '2099-01-01')['adverse20']
            mine = ours[d][0]
            with self.subTest(day=d):
                self.assertEqual(None if np.isnan(mine) else bool(mine), theirs)
            seen.add(theirs)
        self.assertEqual(seen, {True, False, None})          # the fixture exercises all three
        self.assertTrue(ours[days[26]][0] == 0.0)             # the split inside its window is adjusted away
        desk.close()

    def test_a_missing_decision_bar_and_a_missing_window_bar_are_unavailable_not_zero(self):
        days, rows = synthetic()
        p = as_panel(days, rows)
        out = R.read_adverse20(p, {days[47]: ['S0'], days[30]: ['S0']}, period='development')
        self.assertTrue(np.isnan(out[days[47]][0]) and np.isnan(out[days[30]][0]))


class GuardTest(unittest.TestCase):
    def setUp(self):
        days, rows = synthetic()
        self.days, self.p = days, as_panel(days, rows)

    def test_an_event_on_or_after_the_forward_start_is_refused_whatever_the_date_today(self):
        from desk import outcome_firewall
        for today in (date(2026, 10, 18), date(2027, 6, 2)):
            with self.subTest(today=today), patch.object(outcome_firewall, 'market_today', return_value=today):
                for day in (outcome_firewall.FORWARD_START.isoformat(), '2026-12-01'):
                    with self.assertRaises(R.OutcomeReadRefused):
                        R.read_adverse20(self.p, {day: ['S0']}, period='development')

    def test_every_event_goes_through_the_firewall(self):
        with patch.object(R, 'evaluate_event', wraps=R.evaluate_event) as gate:
            R.read_adverse20(self.p, {self.days[3]: ['S0'], self.days[5]: ['S0']}, period='development')
        self.assertEqual([c.args[0] for c in gate.call_args_list], [self.days[3], self.days[5]])

    def test_the_development_run_refuses_any_date_outside_2019_10_01_to_2024_12_31(self):
        early_days, early_rows = synthetic(start='2019-09-02', n=60)
        early = as_panel(early_days, early_rows)
        with self.assertRaises(R.OutcomeReadRefused):
            R.read_adverse20(early, {'2019-09-30': ['S0']}, period='development')
        R.read_adverse20(early, {'2019-10-01': ['S0']}, period='development')        # the first development day
        late_days, late_rows = synthetic(start='2024-11-01', n=43)                    # ends 2024-12-31
        late = as_panel(late_days, late_rows)
        self.assertEqual(late_days[-1], '2024-12-31')
        with self.assertRaises(R.OutcomeReadRefused):                                 # its 20th session is in 2025
            R.read_adverse20(late, {'2024-12-10': ['S0']}, period='development')
        into_2025_days, into_2025_rows = synthetic(start='2024-11-01', n=50)
        with self.assertRaises(R.OutcomeReadRefused):                                 # 2025 must not even be loaded
            R.read_adverse20(as_panel(into_2025_days, into_2025_rows), {'2024-11-04': ['S0']}, period='development')
        with self.assertRaises(R.OutcomeReadRefused):
            R.read_adverse20(self.p, {self.days[3]: ['S0']}, period='holdout_2025')   # no hold-out reader exists


def rows_from(cells_spec):
    """[(date, quintile, state, outcome), ...] to aligned arrays."""
    a = np.array(cells_spec, dtype=float)
    return dict(date_idx=a[:, 0].astype(int), quintile=a[:, 1].astype(int), state=a[:, 2], outcome=a[:, 3])


def balanced(rate_adverse, rate_other, n=100, dates=30, quintiles=C.QUINTILES):
    """n rows per state and quintile over `dates` dates, with the given adverse20 rates."""
    spec = []
    for q in quintiles:
        for s, rate in ((1.0, rate_adverse), (0.0, rate_other)):
            hits = round(rate * n)
            spec += [(k % dates, q, s, 1.0 if k < hits else 0.0) for k in range(n)]
    return rows_from(spec)


WEIGHTS = {q: 0.2 for q in C.QUINTILES}


class ContrastTest(unittest.TestCase):
    def test_the_standardised_difference_is_the_weighted_sum_and_never_renormalised(self):
        rows = balanced(0.30, 0.10)
        table = C.cells(rows)
        self.assertAlmostEqual(C.standardized(table, WEIGHTS), 0.20)
        self.assertEqual(table[(1.0, 3)]['candidates'], 100)
        self.assertAlmostEqual(table[('ratio', 3)], 3.0)
        self.assertIsNone(C.cells(balanced(0.30, 0.0))[('ratio', 3)])               # a zero rate: no ratio
        missing = rows_from([r for r in zip(rows['date_idx'], rows['quintile'], rows['state'], rows['outcome'])
                             if not (r[1] == 5 and r[2] == 1.0)])
        self.assertIsNone(C.standardized(C.cells(missing), WEIGHTS))                  # quintile 5 lacks one state
        self.assertAlmostEqual(C.standardized(C.cells(missing), {1: .25, 2: .25, 3: .25, 4: .25, 5: 0}), 0.20)

    def test_weights_are_development_candidate_shares_including_missing_outcomes(self):
        self.assertEqual(C.baseline_weights(np.array([1, 1, 2, 3, 4, 5, 5, 5, 0])),
                         {1: 2 / 8, 2: 1 / 8, 3: 1 / 8, 4: 1 / 8, 5: 3 / 8})

    def test_coverage_needs_its_numerator_chosen(self):
        rows = rows_from([(0, 1, 1.0, 1.0), (0, 1, np.nan, 0.0), (1, 2, 0.0, np.nan), (1, 2, 1.0, 0.0)])
        self.assertEqual(C.coverage(rows, numerator='state_known'), 0.75)
        self.assertEqual(C.coverage(rows, numerator='state_and_outcome_known'), 0.5)
        with self.assertRaises(TypeError):
            C.coverage(rows)
        with self.assertRaises(ValueError):
            C.coverage(rows, numerator='anything')

    def test_sample_minimums_are_100_valid_outcomes_and_30_dates_per_cell(self):
        self.assertEqual(C.sample_shortfalls(C.cells(balanced(0.3, 0.1, n=100, dates=30))), [])
        self.assertEqual(len(C.sample_shortfalls(C.cells(balanced(0.3, 0.1, n=99, dates=30)))), 10)
        self.assertEqual(len(C.sample_shortfalls(C.cells(balanced(0.3, 0.1, n=100, dates=29)))), 10)

    def test_spells_use_the_addendum_1_rule(self):
        def run(adverse, gap):
            return [(f'd{k}', True) for k in range(adverse)] + [(f'g{k}', False) for k in range(gap)]
        # AA, 19 known non-adverse, AA (merged: 1); 20 apart: new (2); A, 5 known + 30 UNKNOWN, A (merged
        # into 2: UNKNOWN never separates); then three more, 25 apart (3, 4, 5).
        states = run(2, 19) + run(2, 20) + run(1, 5) + [('u', None)] * 30 + run(1, 25) * 4
        self.assertEqual(C.spell_count(states), 5)

    def test_the_matched_baseline_uses_rows_with_a_known_state(self):
        rows = rows_from([(0, q, s, o) for q in C.QUINTILES for s, o in ((1.0, 1.0), (0.0, 0.0), (np.nan, 1.0))])
        out = C.matched_baseline(rows, WEIGHTS)
        self.assertEqual(out['rows'], 10)
        self.assertAlmostEqual(out['standardized_rate'], 0.5)


class DecisionTest(unittest.TestCase):
    def test_exactly_five_percent_unusable_is_allowed_but_more_is_inconclusive(self):
        self.assertEqual(C.decide('V1', **self.base(usable_draws=1900))['result'], 'SUCCESS')
        self.assertEqual(C.decide('V1', **self.base(usable_draws=1899))['result'], 'INCONCLUSIVE')

    def base(self, **change):
        table = C.cells(balanced(0.30, 0.10))
        kw = dict(table=table, standardized_difference=0.20, cover=0.9, usable_draws=2000,
                  family_interval=(0.05, 0.3), spells_in_period=6)
        kw.update(change)
        return kw

    def test_success_needs_magnitude_interval_and_sign_and_otherwise_is_not_success(self):
        self.assertEqual(C.decide('V1', **self.base())['result'], 'SUCCESS')
        self.assertEqual(C.decide('V3', **self.base(spells_in_period=None))['result'], 'SUCCESS')
        self.assertEqual(C.decide('V1', **self.base(standardized_difference=0.009))['result'], 'NOT_SUCCESS')
        self.assertEqual(C.decide('V1', **self.base(family_interval=(0.0, 0.3)))['result'], 'NOT_SUCCESS')
        flat = C.cells(balanced(0.10, 0.10))
        self.assertEqual(C.decide('V2', **self.base(table=flat))['result'], 'NOT_SUCCESS')

    def test_any_failed_requirement_makes_it_inconclusive(self):
        for change in (dict(cover=0.79), dict(usable_draws=1899), dict(spells_in_period=4),
                       dict(table=C.cells(balanced(0.3, 0.1, n=99))), dict(standardized_difference=None)):
            with self.subTest(change=list(change)):
                self.assertEqual(C.decide('V2', **self.base(**change))['result'], 'INCONCLUSIVE')
        self.assertEqual(C.decide('V3', **self.base(spells_in_period=4))['result'], 'SUCCESS')   # spells: V1, V2 only
        with self.assertRaises(ValueError):
            C.decide('V1', **self.base(spells_in_period=None))


class UncertaintyTest(unittest.TestCase):
    def test_each_block_length_has_its_own_seeded_draws_reused_by_every_contrast(self):
        draws = U.period_draws(300)
        np.testing.assert_array_equal(draws[60], B.block_draws(300, 60))
        np.testing.assert_array_equal(draws[20], B.block_draws(300, 20))
        self.assertEqual(draws[60].shape, (2000, 300))
        self.assertEqual((U.BLOCK['V1'], U.BLOCK['V2'], U.BLOCK['V3']), (60, 60, 20))
        self.assertAlmostEqual(U.FAMILY_LEVEL, 0.98333333, places=7)

    def test_a_replicate_counts_each_stock_day_as_often_as_its_date_is_drawn(self):
        rows = rows_from([(0, q, 1.0, 1.0) for q in C.QUINTILES] + [(1, q, 1.0, 0.0) for q in C.QUINTILES] +
                         [(0, q, 0.0, 0.0) for q in C.QUINTILES] + [(1, q, 0.0, 0.0) for q in C.QUINTILES])
        draws = np.array([[0, 0], [0, 1], [1, 1]])
        out = U.replicate_differences(rows, WEIGHTS, draws, usable='computable')
        np.testing.assert_allclose(out, [1.0, 0.5, 0.0])        # date 0 twice: rate 1; once each: 0.5
        draws = np.array([[0, 0]])
        only_adverse = rows_from([(0, q, 1.0, 1.0) for q in C.QUINTILES] + [(1, q, 0.0, 0.0) for q in C.QUINTILES])
        self.assertTrue(np.isnan(U.replicate_differences(only_adverse, WEIGHTS, draws, usable='computable')[0]))

    def test_the_stricter_usable_rule_also_needs_the_sample_minimums_in_the_replicate(self):
        rows = balanced(0.3, 0.1, n=100, dates=30)
        draws = np.tile(np.arange(30), (3, 1))
        draws[2, :] = 0                                           # one date only
        loose = U.replicate_differences(rows, WEIGHTS, draws, usable='computable')
        strict = U.replicate_differences(rows, WEIGHTS, draws, usable='computable_with_sample_minimums')
        self.assertTrue(np.all(np.isfinite(loose)))
        self.assertTrue(np.isfinite(strict[0]) and np.isnan(strict[2]))
        with self.assertRaises(TypeError):
            U.replicate_differences(rows, WEIGHTS, draws)

    def test_intervals_need_their_percentile_method_chosen(self):
        reps = np.concatenate([np.linspace(0, 1, 1999), [np.nan]])
        out = U.intervals(reps, method='linear')
        self.assertEqual(out['usable_draws'], 1999)
        self.assertAlmostEqual(out['descriptive_95'][0], 0.025, places=6)
        self.assertAlmostEqual(out['family'][0], 0.05 / 3 / 2, places=6)
        with self.assertRaises(TypeError):
            U.intervals(reps)
        self.assertEqual(U.intervals(np.full(5, np.nan), method='linear')['usable_draws'], 0)

    def test_the_matched_baseline_uses_the_same_draws(self):
        rows = rows_from([(0, q, 1.0, 1.0) for q in C.QUINTILES] + [(1, q, 0.0, 0.0) for q in C.QUINTILES])
        out = U.replicate_baseline(rows, WEIGHTS, np.array([[0, 0], [0, 1]]))
        np.testing.assert_allclose(out, [1.0, 0.5])


class NothingRealTest(unittest.TestCase):
    def test_the_outcome_step_opens_no_store_and_has_no_entry_point(self):
        banned = ('sqlite3', 'get_live_connection', 'get_connection', 'open_readonly', 'load_panel',
                  'get_desk_connection', 'requests', 'urlopen')
        for path in sorted((ROOT / 'desk' / 't1_outcome').glob('*.py')):
            text = path.read_text(encoding='utf-8')
            tree = ast.parse(text)
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
                    {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | \
                    {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | \
                    {n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            with self.subTest(path=path.name):
                self.assertFalse({b for b in banned if b in names})
                self.assertNotIn('__main__', text)
        self.assertFalse(list((ROOT / 'scripts').glob('*t1*outcome*')))


if __name__ == '__main__':
    unittest.main()
