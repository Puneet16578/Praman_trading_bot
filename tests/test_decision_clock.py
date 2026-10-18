"""P8-084: Praman's two clocks. Research reads use the source's date; a replay of Praman's own
decision for a past session sees only rows stored by the end of that day (recorded_at)."""
import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from desk.gates.engine import AssessmentResult
from desk.journal import store as jstore
from desk.lib import store
from desk.lib.connection import get_desk_connection

# Like 15 and 16 Oct 2026: sessions whose bhavcopy was stored late, on Monday 19 Oct.
ROWS = [('SBIN', 'EQ', '2026-10-14', '2026-10-14', 820.0, '2026-10-14T14:00:00+00:00'),
        ('SBIN', 'EQ', '2026-10-15', '2026-10-15', 821.0, '2026-10-19T13:00:00+00:00'),
        ('SBIN', 'EQ', '2026-10-16', '2026-10-16', 822.0, '2026-10-19T13:00:01+00:00'),
        ('SBIN', 'EQ', '2026-10-19', '2026-10-19', 823.0, '2026-10-19T13:00:02+00:00')]


def sessions(conn):
    return [r[0] for r in conn.execute("SELECT event_date FROM bhavcopy ORDER BY event_date")]


class ClockTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        praman = self.root / 'praman.db'
        conn = sqlite3.connect(praman)
        conn.execute('CREATE TABLE bhavcopy (symbol TEXT, series TEXT, event_date TEXT, knowledge_date TEXT, '
                     'close_price REAL, recorded_at TEXT)')
        conn.executemany('INSERT INTO bhavcopy VALUES (?,?,?,?,?,?)', ROWS)
        conn.commit()
        conn.close()
        patcher = patch.object(store, 'PRODUCTION_DB_PATH', praman)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.desk_path = self.root / 'desk.sqlite'
        get_desk_connection(self.desk_path).close()

    def test_the_decision_watermark_is_the_end_of_that_ist_day(self):
        mark = store.decision_watermark('2026-10-15')
        self.assertEqual(mark, '2026-10-15T18:29:59.999999+00:00')
        self.assertRegex(mark, store._WATERMARK_RE)
        live = store.get_live_connection()
        self.assertEqual(store.past_session_watermark(live, '2026-10-15'), mark)
        self.assertIsNone(store.past_session_watermark(live, '2026-10-19'))          # the latest session: live
        self.assertIsNone(store.past_session_watermark(live, None))
        live.close()

    def test_a_bhavcopy_stored_late_is_invisible_to_a_replay_dated_before_it_was_stored(self):
        live = store.get_live_connection()
        self.assertEqual(sessions(live), ['2026-10-14', '2026-10-15', '2026-10-16', '2026-10-19'])   # research clock
        live.close()
        for day in ('2026-10-15', '2026-10-16'):
            with self.subTest(day=day):
                replay = store.get_replay_connection(store.decision_watermark(day))
                self.assertEqual(sessions(replay), ['2026-10-14'])
                self.assertEqual(store.max_recorded_at(replay), '2026-10-14T14:00:00+00:00')
                replay.close()
        audit = store.get_replay_connection('2026-10-16T14:05:00.000000+00:00')    # a decision recorded on 16 Oct
        self.assertEqual(sessions(audit), ['2026-10-14'])
        audit.close()

    def run_assess(self, as_of):
        seen = {}

        def assess(praman_conn, desk_conn, **kw):
            seen.update(praman=sessions(praman_conn), as_of=kw['as_of_date'],
                        desk_temp_views=[r[0] for r in desk_conn.execute(
                            "SELECT name FROM sqlite_temp_master WHERE type='view'")])
            return AssessmentResult('WATCH', {}, None)
        from desk import cli
        desk = get_desk_connection(self.desk_path)
        with patch.object(cli, 'get_desk_connection', return_value=desk), \
                patch.object(cli, 'run_assessment', side_effect=assess), \
                patch.object(cli, 'assessment_context', return_value=SimpleNamespace(display=lambda: 'context')), \
                patch.object(cli, 'record_context'), \
                patch('desk.decision_contract.assessment_contract', side_effect=RuntimeError('not under test')), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            cli.cmd_assess(SimpleNamespace(symbol='SBIN', as_of=as_of, thesis=None))
        check = get_desk_connection(self.desk_path)
        decision = dict(check.execute('SELECT * FROM decisions ORDER BY decision_id DESC LIMIT 1').fetchone())
        check.close()
        return seen, decision

    def test_desk_assess_for_a_past_session_reads_only_what_was_stored_by_then(self):
        seen, decision = self.run_assess('2026-10-15')
        self.assertEqual(seen['praman'], ['2026-10-14'])                # the late 15 Oct bar is invisible
        self.assertTrue(seen['desk_temp_views'])                        # Desk reads go through the replay views
        self.assertEqual(decision['as_of_date'], '2026-10-15')
        self.assertEqual(decision['praman_watermark'], '2026-10-14T14:00:00+00:00')
        self.assertLessEqual(decision['desk_watermark'], store.decision_watermark('2026-10-15'))

    def test_desk_assess_for_the_latest_session_stays_live(self):
        seen, decision = self.run_assess(None)
        self.assertEqual(seen['as_of'], '2026-10-19')
        self.assertEqual(seen['praman'], ['2026-10-14', '2026-10-15', '2026-10-16', '2026-10-19'])
        self.assertEqual(seen['desk_temp_views'], [])
        self.assertEqual(decision['praman_watermark'], '2026-10-19T13:00:02+00:00')

    def test_a_past_scan_screens_with_the_decision_clock_and_observes_fills_live(self):
        from desk import scan
        seen = {}

        def events(conn, days):
            seen['screening'] = sessions(conn)
            return [SimpleNamespace(symbol='SBIN', event_date='2026-10-15')]

        def observe(conn, *args):
            seen['observing'] = sessions(conn)
            return None
        plan = dict(decision_price=821, atr20=5, quantity=1)
        assessment = AssessmentResult('SCREEN_PASS', {}, SimpleNamespace(content_hash=lambda: 'fixture'))
        with patch.object(scan, 'catalogue_events', side_effect=events), \
                patch.object(scan, 'screen_event', return_value=(plan, assessment)) as screen, \
                patch.object(scan, 'execution_observation', side_effect=observe), \
                patch.object(scan, 'assessment_context', return_value=SimpleNamespace(display=lambda: 'context')), \
                patch.object(scan, 'record_context'), contextlib.redirect_stdout(io.StringIO()):
            inserted = scan.run_scan_range(['2026-10-15'], desk_db_path=self.desk_path,
                                           stored_by=store.decision_watermark('2026-10-15'))
        self.assertEqual(inserted, 1)
        self.assertEqual(seen['screening'], ['2026-10-14'])
        self.assertEqual(seen['observing'], ['2026-10-14', '2026-10-15', '2026-10-16', '2026-10-19'])
        desk_read = screen.call_args.args[1]
        self.assertIsNot(desk_read, None)
        check = get_desk_connection(self.desk_path)
        row = check.execute('SELECT * FROM opportunity_log').fetchone()
        check.close()
        self.assertEqual(row['event_date'], '2026-10-15')

    def test_the_scan_command_passes_the_decision_clock_for_a_past_date_only(self):
        from desk import cli
        for date, expected in (('2026-10-15', store.decision_watermark('2026-10-15')), (None, None)):
            with self.subTest(date=date), patch('desk.scan.run_scan', return_value=0) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                cli.cmd_scan(SimpleNamespace(date=date))
            self.assertEqual(run.call_args.kwargs['stored_by'], expected)

    def test_an_audit_replay_reads_the_decisions_own_thesis_by_id(self):
        """A past-dated assessment records its thesis after its decision watermark; the replay must
        still find it (through the watermark-limited views it would be invisible)."""
        from desk import replay
        from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS
        desk = get_desk_connection(self.desk_path)
        fields = {k: v for k, v in COMPLETE_AXISBANK_THESIS.items() if k in (
            'evidence_cutoff', 'hypotheses', 'drivers', 'catalyst', 'horizon', 'invalidation_conditions',
            'exit_price', 'exit_time', 'exit_evidence', 'exit_risk', 'exit_portfolio', 'planned_entry',
            'planned_stop', 'planned_target', 'sector')}
        fields.setdefault('evidence_cutoff', '2026-10-15')
        thesis_id = jstore.record_thesis(desk, symbol='SBIN', **fields)        # recorded now
        desk.commit()
        early = '2026-10-15T18:29:59.999999+00:00'                            # the decision's desk watermark
        limited = replay.get_desk_replay_connection(self.desk_path, early)
        self.assertIsNone(jstore.get_thesis(limited, thesis_id))              # invisible through the views
        limited.close()
        desk.close()
        captured = {}

        def assess(praman_conn, desk_conn, **kw):
            captured['thesis'] = kw['thesis']
            return AssessmentResult('WATCH', {}, None)
        decision = dict(symbol='SBIN', as_of_date='2026-10-15', thesis_id=thesis_id, code_commit='abc',
                        rulebook_hash='h', cost_config_hash='ch', praman_watermark='2026-10-14T14:00:00+00:00',
                        desk_watermark=early, gate_results={}, state='WATCH', isin_map_built_at=None)
        with patch.object(replay, 'current_git_head', return_value='abc'),                 patch.object(replay, 'get_decision', return_value=decision),                 patch.object(replay, 'run_assessment', side_effect=assess):
            try:
                replay.replay_decision(1, desk_db_path=self.desk_path, rulebook_override=Mock(), costs_override=Mock())
            except Exception:
                pass                                    # comparing the full record is not under test here
        self.assertIsNotNone(captured['thesis'])
        self.assertEqual(captured['thesis']['thesis_id'], thesis_id)


if __name__ == '__main__':
    unittest.main()
