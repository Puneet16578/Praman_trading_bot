"""Adversarial path, temporal and cluster-resampling tests for the foreground replay."""
import ast
import copy
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from desk.evidence.bundle import daily_stat_at
from desk.research_snapshot import SnapshotQueries
from desk.shadow_analysis import tails, summarize, METRICS
from desk.circuit_bands import CircuitBand
from desk.gates.checks import g1_data_quality
from src.signals.event_catalogue import SymbolHistory, compute_daily_stats, build_symbol_history
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly
from desk.lib.store import PRODUCTION_DB_PATH


class ShadowAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.days = [(date(2021,1,1)+timedelta(days=i)).isoformat() for i in range(22)]
        self.rows = {d: dict(symbol='X',open_price=100.,high_price=102.,low_price=98.,close_price=100.) for d in self.days}
        self.hist = SymbolHistory('X',self.days,{d:[(d,r)] for d,r in self.rows.items()},[],[],[])
        self.plan = dict(decision_price=100.,stop_level=90.,quantity=10)
        self.obs = dict(fill_price=100.,fill_date=self.days[1])

    def run_tail(self, band=None):
        with patch('desk.shadow_analysis.band_as_of',return_value=band or CircuitBand()) as bands:
            result = tails(self.hist,self.days[0],self.days,self.plan,self.obs,None,self.days[-1])
        return result, bands

    def test_missing_global_session_is_not_replaced_by_security_day_21(self):
        del self.hist.vintages[self.days[5]]
        actual,_ = self.run_tail()
        self.assertTrue(actual['incomplete20'])
        self.assertEqual(actual['observed_sessions'],19)
        self.assertIsNone(actual['adverse20'])
        self.assertIsNone(actual['stop_gap'])
        self.assertFalse(actual['entry_gap'])

    def test_gap_after_prior_intraday_exit_does_not_count(self):
        self.rows[self.days[1]]['low_price'] = 89
        self.rows[self.days[2]].update(open_price=80,low_price=79)
        actual,_ = self.run_tail()
        self.assertFalse(actual['stop_gap'])
        self.assertTrue(actual['adverse20'])
        self.assertAlmostEqual(actual['mae_decision'],.21)

    def test_later_gap_before_exit_counts(self):
        self.rows[self.days[2]].update(open_price=85,low_price=84)
        actual,_ = self.run_tail()
        self.assertTrue(actual['stop_gap'])
        self.assertFalse(actual['entry_gap'])

    def test_entry_gap_counts(self):
        self.rows[self.days[1]].update(open_price=85,low_price=84)
        actual,_ = self.run_tail()
        self.assertTrue(actual['stop_gap'])
        self.assertTrue(actual['entry_gap'])

    def test_split_is_multiplication_onto_event_basis_and_fill_basis_is_separate(self):
        self.hist.factor_dates = [self.days[1]]
        self.hist.factor_cum = [2.]
        for d in self.days[1:]:
            self.rows[d].update(open_price=50,high_price=51,low_price=49,close_price=50)
        self.obs['fill_price'] = 50
        actual,_ = self.run_tail()
        self.assertFalse(actual['adverse20'])
        self.assertFalse(actual['entry_gap'])
        self.assertAlmostEqual(actual['mae_decision'],.02)
        self.assertAlmostEqual(actual['mae_fill'],.02)

    def test_band_uses_previous_global_report_and_requires_all_ohlc_locked(self):
        self.rows[self.days[1]].update(open_price=95,high_price=95,low_price=95,close_price=95)
        self.rows[self.days[3]]['low_price'] = 95 # touch alone is not a lock
        actual,bands = self.run_tail(CircuitBand('FIXED',5))
        self.assertEqual(actual['locked_days'],1)
        self.assertEqual(actual['band_covered'],20)
        self.assertEqual(bands.call_args_list[0].kwargs['report_date'],self.days[0])
        self.assertEqual(self.run_tail()[0]['band_unknown'],20)

    def test_structural_break_and_invalid_plan_stay_missing(self):
        self.hist.structural_break_dates = [self.days[10]]
        self.assertEqual(self.run_tail()[0]['tail_reason'],'structural_break')
        self.plan = dict(quantity=0)
        self.assertEqual(self.run_tail()[0]['tail_reason'],'invalid_plan')

    def test_cache_keeps_cutoffs_separate_and_cursor_consumption_independent(self):
        conn = sqlite3.connect(':memory:')
        self.addCleanup(conn.close)
        conn.execute('CREATE TABLE facts (knowledge_date TEXT)')
        conn.executemany('INSERT INTO facts VALUES (?)',[('2020-01-01',),('2022-01-01',)])
        cache = SnapshotQueries(conn)
        sql = 'SELECT * FROM facts WHERE knowledge_date<=?'
        a = cache.execute(sql,('2021-01-01',))
        a.fetchone()
        self.assertEqual(len(cache.execute(sql,('2021-01-01',)).fetchall()),1)
        self.assertEqual(len(cache.execute(sql,('2023-01-01',)).fetchall()),2)
        with self.assertRaises(ValueError):
            cache.execute('DELETE FROM facts')

    def test_g1_late_known_row_cannot_fill_historical_gap(self):
        conn = sqlite3.connect(':memory:')
        self.addCleanup(conn.close)
        conn.row_factory = sqlite3.Row
        conn.execute('CREATE TABLE bhavcopy (symbol TEXT,event_date TEXT,knowledge_date TEXT)')
        conn.executemany('INSERT INTO bhavcopy VALUES (?,?,?)',[
            ('X','2021-01-01','2021-01-01'),('X','2021-01-02','2022-01-01'),('Y','2021-01-02','2021-01-02')])
        self.assertEqual(g1_data_quality(conn,'X','2021-01-02').result,'FAIL')

    def test_cluster_bootstrap_shared_dates_preserves_exact_paired_difference(self):
        rows = []
        for day,value in zip(self.days[:3],[.1,.3,.9]):
            for state,shift in [('SCREEN_PASS',0),('SCREEN_FAIL',.2)]:
                r = dict(event_date=day,state=state,gates={},fill=100,plan=dict(quantity=1),
                         incomplete20=False,band_covered=0,band_unknown=20,locked_days=0,
                         execution={},label=dict(excluded_reason=None),tail_reason='')
                r.update({m:value+shift for m in METRICS if m!='locked_rate'})
                rows.append(r)
        result = summarize(rows)
        stat = result['SCREEN_FAIL']['metrics']['signed_return_90d']
        self.assertEqual(stat['n_events'],3)
        self.assertEqual(stat['date_clusters'],3)
        self.assertTrue(stat['small_sample_warning'])
        self.assertEqual(result['G3']['n'],0)
        self.assertAlmostEqual(stat['difference_vs_pass']['estimate'],.2)
        for bound in stat['difference_vs_pass']['interval95']:
            self.assertAlmostEqual(bound,.2)
        self.assertEqual(stat['difference_vs_pass']['usable_replicates'],2000)
        self.assertIsNone(result['SCREEN_PASS']['metrics']['locked_rate']['estimate'])
        self.assertEqual(result,summarize(rows))

    def test_absent_passes_and_missing_outcomes_do_not_become_zero(self):
        row = dict(event_date=self.days[0],state='SCREEN_FAIL',gates={},fill=None,plan=dict(quantity=0),
                   incomplete20=True,band_covered=0,band_unknown=20,locked_days=0,execution=None,
                   signed_return_90d=None,label=dict(excluded_reason='missing'),tail_reason='missing')
        result = summarize([row])
        stat = result['SCREEN_FAIL']['metrics']['signed_return_90d']
        self.assertEqual(stat['n_events'],0)
        self.assertIsNone(stat['estimate'])
        self.assertEqual(stat['difference_vs_pass']['usable_replicates'],0)

    def test_runner_parses_imports_and_has_no_process_pool(self):
        import scripts.desk_shadow_replay as runner
        tree = ast.parse(Path(runner.__file__).read_text(encoding='utf-8'))
        forbidden = {'multiprocessing','concurrent.futures','threading'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                self.assertNotIn(node.module,forbidden)
            if isinstance(node,ast.Import):
                self.assertFalse(forbidden.intersection(a.name for a in node.names))

    def test_single_day_stat_equals_full_pinned_computation_on_real_actions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'snapshot.sqlite'
            online_backup(PRODUCTION_DB_PATH,path)
            conn = open_readonly(path)
            try:
                for symbol,day in [('BAJFINANCE','2025-06-18'),('RELIANCE','2023-07-20'),('AXISBANK','2021-10-27')]:
                    hist = build_symbol_history(conn,symbol,extend_with_series=('BE','BZ'))
                    expected = {s.event_date:s for s in compute_daily_stats(hist)}
                    self.assertEqual(daily_stat_at(hist,day),expected.get(day))
                    self.assertIsNone(daily_stat_at(hist,hist.trading_days[0]))
                    self.assertIsNone(daily_stat_at(hist,'1900-01-01'))
            finally:
                conn.close()

    def test_cached_and_uncached_assessments_are_identical_and_alias_restored(self):
        from desk.research_snapshot import memoized_snapshot_histories
        from desk.screening_plan import screen_event
        from desk.lib.connection import get_desk_connection
        from tests.desk_fixtures import make_test_rulebook, make_test_costs
        import desk.evidence.bundle as bundle
        original = bundle.build_symbol_history
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'snapshot.sqlite'
            online_backup(PRODUCTION_DB_PATH,path)
            conn = open_readonly(path)
            desk = get_desk_connection(':memory:')
            try:
                cache = SnapshotQueries(conn)
                args = (desk,'BAJFINANCE','2025-06-18',make_test_rulebook(),make_test_costs())
                plain_plan,plain = screen_event(conn,*args)
                with memoized_snapshot_histories(cache):
                    cached_plan,cached = screen_event(cache,*args)
                    self.assertEqual(cached_plan,plain_plan)
                    self.assertEqual(cached.gate_results_json(),plain.gate_results_json())
                    self.assertEqual(cached.evidence_bundle.content_hash(),plain.evidence_bundle.content_hash())
                self.assertIs(bundle.build_symbol_history,original)
            finally:
                desk.close()
                conn.close()
