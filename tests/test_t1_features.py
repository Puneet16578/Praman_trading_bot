"""T1 inputs and features on synthetic panels (no store, no network, no outcome).

The pre-registration's listed tests: knowledge-date guards, corporate actions, missing bars,
warm-up, bootstrap multiplicities and the firewall; plus the V1/V2/V3 definitions, spells,
periods and quintiles.
"""
import ast
from datetime import date, timedelta
from pathlib import Path
import unittest

import numpy as np

from desk.t1 import bootstrap as B
from desk.t1 import features as F
from desk.t1 import inputs as I

ROOT = Path(__file__).resolve().parents[1]


def weekdays(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def panel(closes, *, known_lag=None, breaks=None, identity=None, index=None, start='2020-01-01'):
    """closes: [session][symbol] (NaN = no bar); high/low = close +/- 1%."""
    c = np.asarray(closes, dtype=float)
    n, m = c.shape
    known = np.where(np.isnan(c), np.inf, np.arange(n)[:, None] + (0 if known_lag is None else np.asarray(known_lag)))
    return F.Panel(sessions=weekdays(start, n), symbols=[f'S{j}' for j in range(m)], raw_close=c, close=c.copy(),
                   high=c * 1.01, low=c * 0.99, known=known.astype(float),
                   breaks=np.zeros((n, m)) if breaks is None else np.cumsum(np.asarray(breaks, dtype=float), axis=0),
                   identity=np.full((n, m), F.EQUITY, dtype=np.int8) if identity is None else np.asarray(identity),
                   index=index or {})


def ramp(n, m, base=100.0, step=0.5):
    return [[base + step * i + j for j in range(m)] for i in range(n)]


class KnowledgeGuardTest(unittest.TestCase):
    def test_a_bar_known_a_session_later_is_unusable_at_its_own_decision_only(self):
        closes = ramp(30, 3)
        lag = np.zeros((30, 3))
        lag[25, 0] = 1                                   # S0's bar for session 25 published the next day
        p = panel(closes, known_lag=lag)
        cause = F.exclusion_causes(p)
        self.assertEqual(cause[25, 0], 'bar_not_known_by_decision')
        v21 = F.window_valid(p, 21)
        self.assertFalse(v21[25, 0])                     # its own decision cannot use it
        self.assertTrue(v21[26, 0])                      # the next decision can
        out = F.compute(p)
        self.assertTrue(np.isnan(out['atr_pct'][25, 0]) and np.isfinite(out['atr_pct'][26, 0]))

    def test_the_basket_for_an_earlier_day_counts_once_its_bars_are_known(self):
        closes = ramp(30, 4)
        lag = np.zeros((30, 4))
        lag[20, :] = 1                                   # a whole session published the next morning
        out = F.compute(panel(closes, known_lag=lag))
        self.assertTrue(np.isnan(out['rel_ew_5'][20, 1]))           # at session 20 nothing of 20 is known
        self.assertTrue(np.isfinite(out['rel_ew_5'][23, 1]))        # by 23 it is, inside the window

    def test_an_index_close_for_d_is_never_used_at_d(self):
        n = 300
        n500 = np.linspace(100, 200, n)
        n500[-1] = 1.0                                   # a crash printed on the last session
        vix = np.full(n, 15.0)
        p = panel(ramp(n, 2), index={'NIFTY 500': n500, 'INDIA VIX': vix, 'NIFTY 50': n500})
        out = F.compute(p)
        self.assertEqual(out['v1_adverse'][n - 1], 0)   # decided on closes through D-1: no crash yet
        self.assertEqual(out['n500_prev'][n - 1], n500[n - 2])


class CorporateActionTest(unittest.TestCase):
    def test_a_split_inside_the_window_is_adjusted_and_a_demerger_makes_it_unknown(self):
        n, m = 40, 3
        raw = np.array(ramp(n, m), dtype=float)
        raw[30:, 0] /= 2                                 # 2:1 split, ex-date session 30
        p = panel(raw)
        scale = np.ones((n, m))
        scale[:30, 0] = 0.5                              # back-adjusted to the post-split basis
        p.close, p.high, p.low = raw * scale, raw * scale * 1.01, raw * scale * 0.99
        out = F.compute(p)
        self.assertLess(abs(out['rel_ew_5'][32, 0] - out['rel_ew_5'][32, 2]), 0.02)   # no fake -50%
        brk = np.zeros((60, m))
        brk[30, 1] = 1                                   # demerger ex-date for S1
        q = panel(ramp(60, m), breaks=brk)
        cause = F.exclusion_causes(q)
        self.assertEqual(cause[35, 1], 'atr_window_unadjustable')
        self.assertEqual(cause[35, 0], '')
        self.assertEqual(cause[30 + 21, 1], '')          # a window starting after the ex-date is fine


class MissingBarTest(unittest.TestCase):
    def test_a_missing_bar_is_never_filled_and_leaves_the_denominators(self):
        closes = ramp(60, 3)
        closes[55][2] = np.nan
        p = panel(closes)
        out = F.compute(p)
        self.assertEqual(out['ad_valid'][55], 2)                   # S2 not in that day's breadth
        self.assertEqual(out['ad_valid'][56], 2)                   # nor the next day's return
        self.assertFalse(F.window_valid(p, 21)[59, 2])             # every window across it is UNKNOWN
        self.assertTrue(np.isnan(out['atr_pct'][59, 2]))

    def test_a_session_missing_for_every_stock_blocks_windows_across_it(self):
        closes = ramp(60, 3)
        closes[40] = [np.nan] * 3
        out = F.compute(panel(closes))
        self.assertTrue(np.isnan(out['rel_ew_20'][50]).all())
        self.assertTrue(np.isfinite(out['rel_ew_5'][50]).all())


class WarmUpTest(unittest.TestCase):
    def test_each_feature_starts_only_once_its_window_is_full(self):
        n = 300
        vix = np.linspace(10, 20, n)
        idx = {'NIFTY 500': np.linspace(100, 200, n), 'INDIA VIX': vix, 'NIFTY 50': np.linspace(100, 200, n)}
        out = F.compute(panel(ramp(n, 3), index=idx))
        self.assertTrue(np.isnan(out['share_above50'][48]) and np.isfinite(out['share_above50'][49]))   # 49 prior + D
        self.assertTrue(np.isnan(out['atr_pct'][19, 0]) and np.isfinite(out['atr_pct'][20, 0]))         # 21 bars
        self.assertTrue(np.isnan(out['n500_sma200_prev'][199]) and np.isfinite(out['n500_sma200_prev'][200]))
        self.assertTrue(np.isnan(out['vix_p80_prev'][252]) and np.isfinite(out['vix_p80_prev'][253]))
        self.assertAlmostEqual(out['vix_p80_prev'][253], np.percentile(vix[0:252], 80, method='linear'))


class StateDefinitionTest(unittest.TestCase):
    def test_v1_needs_both_inputs_and_either_condition(self):
        n = 300
        n500 = np.linspace(100, 200, n)
        vix = np.full(n, 15.0)
        vix[n - 2] = 30.0                                          # VIX spike on D-1 only
        out = F.compute(panel(ramp(n, 2), index={'NIFTY 500': n500, 'INDIA VIX': vix, 'NIFTY 50': n500}))
        self.assertEqual(out['v1_adverse'][n - 1], 1)
        self.assertEqual(out['v1_adverse'][n - 2], 0)
        vix2 = vix.copy()
        vix2[n - 2] = np.nan
        out = F.compute(panel(ramp(n, 2), index={'NIFTY 500': n500, 'INDIA VIX': vix2, 'NIFTY 50': n500}))
        self.assertTrue(np.isnan(out['v1_adverse'][n - 1]))       # both inputs required

    def test_v2_is_weak_breadth_below_40_percent_and_negative_net(self):
        n, m = 60, 5
        c = np.array(ramp(n, m), dtype=float)
        c[59, :3] = c[58, :3] * 0.5                                # 3 of 5 fall hard on the last day
        out = F.compute(panel(c))
        self.assertEqual((out['adv'][59], out['dec'][59]), (2, 3))
        self.assertAlmostEqual(out['share_above50'][59], 0.4)       # 2 of 5 above: not below 40%
        self.assertEqual(out['v2_adverse'][59], 0)
        c[59, :4] = c[58, :4] * 0.5
        out = F.compute(panel(c))
        self.assertEqual(out['v2_adverse'][59], 1)

    def test_v3_is_the_stock_against_the_other_stocks_equal_weight_return(self):
        n = 30
        c = np.ones((n, 3)) * 100.0
        c[:, 0] = 100 * 1.01 ** np.arange(n)                       # S0 +1%/day; others flat
        out = F.compute(panel(c))
        self.assertAlmostEqual(out['rel_ew_20'][25, 0], 1.01 ** 20 - 1, places=9)   # focal excluded: market 0
        self.assertLess(out['rel_ew_20'][25, 1], 0)
        self.assertEqual(out['v3_negative'][25, 1], 1)
        self.assertEqual(out['v3_negative'][25, 0], 0)


class BootstrapTest(unittest.TestCase):
    def test_blocks_are_contiguous_bounded_truncated_and_reproducible(self):
        draws = B.block_draws(250, 60, replicates=50)
        self.assertEqual(draws.shape, (50, 250))
        blocks = draws[:, :240].reshape(50, 4, 60)
        self.assertTrue((np.diff(blocks, axis=2) == 1).all())
        self.assertTrue((blocks[:, :, 0] <= 250 - 60).all() and (draws >= 0).all())
        self.assertTrue((B.block_draws(250, 60, replicates=50) == draws).all())          # seed 20261001
        self.assertFalse((B.block_draws(250, 20, replicates=50) == draws).all())         # its own draws

    def test_every_stock_day_on_a_date_is_carried_at_its_multiplicity(self):
        draws = np.array([[0, 0, 2, 2, 2]])
        mult = B.multiplicities(draws, 5)
        self.assertEqual(mult.tolist(), [[2, 0, 3, 0, 0]])
        stock_days = np.array([10, 7, 4, np.nan, 1])                # a date with missing values still carries 0
        self.assertEqual(B.replicate_totals(draws, stock_days).tolist(), [2 * 10 + 3 * 4])
        with self.assertRaises(ValueError):
            B.block_draws(10, 20)


class SpellPeriodQuintileTest(unittest.TestCase):
    def test_spells_merge_under_20_known_sessions_and_unknown_never_splits(self):
        states = ([('a', True)] + [('x', False)] * 19 + [('b', True)] + [('u', None)] * 50 + [('c', True)]
                  + [('y', False)] * 20 + [('d', True)])
        spells = F.spells(states)
        self.assertEqual([(s['first'], s['last'], s['adverse_sessions']) for s in spells], [('a', 'c', 3), ('d', 'd', 1)])

    def test_periods_purge_the_last_development_sessions_and_censor_2025_tails(self):
        sessions = weekdays('2024-11-01', 60) + weekdays('2025-12-01', 23)
        forward = weekdays('2026-01-01', 30)
        per = F.periods(sessions, forward)
        dec31 = sessions.index('2024-12-31')
        self.assertEqual(per[dec31], 'development_purged')
        self.assertEqual(per[dec31 - 25], 'development')
        self.assertEqual(per[sessions.index('2025-12-31')], 'holdout_censored')

    def test_quintile_ties_go_up(self):
        q = F.quintile(np.array([1.0, 2.0, 2.5, 4.0, 9.0, np.nan]), [2.0, 3.0, 4.0, 5.0])
        self.assertEqual(q[:5].tolist(), [1.0, 2.0, 2.0, 4.0, 5.0])
        self.assertTrue(np.isnan(q[5]))


class FirewallTest(unittest.TestCase):
    def test_nothing_after_the_study_and_no_outcome_anywhere_in_t1(self):
        with self.assertRaises(F.StudyWindowRefused):
            F.refuse_outside_study('2026-09-16')
        banned = ('adverse20', 'compute_outcome_labels', 'outcome_label', 'relabel_t0', 'collapsed_90d',
                  'forward_return', 'require_outcome_access')
        for path in list((ROOT / 'desk' / 't1').glob('*.py')) + [ROOT / 'scripts' / 't1_build.py']:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
                    {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | \
                    {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | \
                    {n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            with self.subTest(path=path.name):
                self.assertFalse({b for b in banned if any(b in x for x in names)})


class PanelLoaderTest(unittest.TestCase):
    def test_snapshot_is_unknown_on_its_date_then_carried_forward(self):
        from desk.t1.panel import identity_matrix
        days = ['2024-01-18', '2024-01-19', '2024-01-23', '2024-01-24']
        snapshots = [('2024-01-19', {'A': 'INE1'}), ('2024-01-23', {'B': 'INF2'})]
        ident = identity_matrix(days, ['A', 'B', 'C'], snapshots)
        self.assertEqual(ident[:, 0].tolist(), [F.UNKNOWN, F.UNKNOWN, F.EQUITY, F.EQUITY])
        self.assertEqual(ident[:, 1].tolist(), [F.UNKNOWN] * 3 + [F.FUND])
        self.assertTrue((ident[:, 2] == F.UNKNOWN).all())
        # A file dated on a non-session becomes available on the next actual session.
        weekend = identity_matrix(days, ['A'], [('2024-01-20', {'A': 'INE1'})])
        np.testing.assert_array_equal(weekend[:, 0], ident[:, 0])

    def test_default_calendar_excludes_weekends_but_retains_missing_weekdays(self):
        sessions, missing, _ = F.build_calendar({'2024-01-19', '2024-01-20'},
                                               {'2024-01-19', '2024-01-20', '2024-01-23'})
        self.assertEqual(sessions, ['2024-01-19', '2024-01-23'])
        self.assertEqual(missing, ['2024-01-23'])

    def test_store_bars_actions_knowledge_and_dated_identity_load_point_in_time(self):
        import tempfile
        from desk.t1.panel import identity_matrix, load_panel
        from src.bitemporal.connection import get_connection, init_db
        days = weekdays('2019-10-01', 6)
        with tempfile.TemporaryDirectory() as folder:
            conn = get_connection(str(Path(folder) / 'p.db'))
            init_db(conn)
            for i, d in enumerate(days):
                for sym, close in (('SPL', 200.0 if i < 3 else 100.0), ('DEM', 50.0), ('NEW', 10.0)):
                    known = days[min(i + 1, 5)] if (sym == 'NEW' and i == 4) else d
                    conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                                 'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                                 "(?,?,?,?,?,?,?,?,1000,'EQ','fixture',?)", (sym, d, known, close, close, close, close, close, known))
            for sym, kind, ex, num, den in (('SPL', 'SPLIT', days[3], 2, 1), ('DEM', 'DEMERGER', days[2], None, None)):
                conn.execute('INSERT INTO corporate_actions (symbol,action_type,event_date,knowledge_date,ratio_numerator,'
                             'ratio_denominator,confidence_tier,details,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                             (sym, kind, ex, days[0], num, den, 'HIGH', 'fixture', 'fixture', days[0]))
            conn.commit()
            index = {s: {d: dict(close=100.0) for d in days} for s in I.SERIES}
            p = load_panel(conn, index, [(days[2], {'SPL': 'INE000000001', 'DEM': 'INF000000002'})], end=days[-1])
            conn.close()
        j = {s: p.symbols.index(s) for s in ('SPL', 'DEM', 'NEW')}
        self.assertEqual(p.close[:, j['SPL']].tolist(), [100.0] * 6)        # 2:1 split back-adjusted
        self.assertEqual(p.raw_close[0, j['SPL']], 200.0)
        self.assertEqual(p.breaks[:, j['DEM']].tolist(), [0, 0, 1, 1, 1, 1])
        self.assertEqual(p.known[4, j['NEW']], 5)                          # known the next session
        self.assertEqual(p.identity[:, j['SPL']].tolist(), [F.UNKNOWN] * 3 + [F.EQUITY] * 3)
        self.assertEqual(p.identity[3, j['DEM']], F.FUND)
        self.assertEqual(p.identity[5, j['NEW']], F.UNKNOWN)                # no snapshot lists it


class InputsTest(unittest.TestCase):
    def test_snapshots_fill_history_gaps_and_close_mismatches_are_reported(self):
        def row(series, day, close, kind):
            return dict(series=series, event_date=day, open=close, high=close, low=close, close=close, source_kind=kind,
                        source_url='u', source_sha256='h', source_last_modified=None, retrieved_at=None)
        hist = [row('INDIA VIX', '2021-04-23', 20.0, 'historical-data')]
        snaps = [row('INDIA VIX', '2021-04-26', 21.0, 'daily-snapshot'), row('INDIA VIX', '2021-04-23', 20.5, 'daily-snapshot')]
        combined, mismatches = I.combine(hist, snaps)
        self.assertEqual(combined['INDIA VIX']['2021-04-26']['source_kind'], 'daily-snapshot')
        self.assertEqual(mismatches, [dict(series='INDIA VIX', event_date='2021-04-23', history=20.0, snapshot=20.5)])

    def test_the_calendar_keeps_store_sessions_adds_missing_weekdays_and_drops_unstored_weekends(self):
        sessions, missing, specials = F.build_calendar({'2022-08-05', '2022-08-10', '2024-01-20'},
                                                       {'2019-09-30', '2022-08-05', '2022-08-08', '2022-08-10',
                                                        '2024-01-20', '2025-02-01'}, weekends='store')
        self.assertEqual(sessions, ['2019-09-30', '2022-08-05', '2022-08-08', '2022-08-10', '2024-01-20'])
        self.assertEqual((missing, specials), (['2022-08-08'], ['2024-01-20', '2025-02-01']))


if __name__ == '__main__':
    unittest.main()
