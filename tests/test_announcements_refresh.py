"""P8-021: non-200 responses raise, backfill failures are visible, and the weekly refresh is bounded."""
import contextlib
from datetime import date
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from src.bitemporal.connection import get_connection, init_db
from src.ingestion.nse_market_data import announcements as ann
import ingest_announcements_recent as recent

END = date(2026, 10, 4)


class Response:
    def __init__(self, status, payload):
        self.status_code, self._payload = status, payload

    def json(self):
        return self._payload


class Session:
    """Fake NSE session: per-symbol responses, recording every request."""

    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url, params, timeout):
        self.calls.append(params)
        status, payload = self.responses[params['symbol']]
        return Response(status, payload)


def item(seq, when):
    return dict(seq_id=seq, sort_date=when, desc='Updates', attchmntText=f'Announcement {seq}')


class FetchTest(unittest.TestCase):
    def test_failed_responses_raise_instead_of_looking_empty(self):
        session = Session({'A': (503, []), 'B': (200, {'error': 'x'}), 'C': (200, [item('1', '2026-10-01 10:00:00')]), 'D': (200, [])})
        for symbol in ('A', 'B'):
            with self.assertRaises(ann.AnnouncementFetchError):
                ann.fetch_symbol_announcements(session, symbol, END, END)
        self.assertEqual(len(ann.fetch_symbol_announcements(session, 'C', END, END)), 1)
        self.assertEqual(ann.fetch_symbol_announcements(session, 'D', END, END), [])   # a real empty history


class RefreshTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.conn = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.conn)
        for symbol, day in [('EQ1', '2026-10-01'), ('EQ2', '2026-10-01'), ('ETF1', '2026-10-01'), ('OLD', '2026-01-02')]:
            self.conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,'
                              'prev_close,traded_qty,series,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                              (symbol, day, day, 10, 11, 9, 10, 10, 100, 'EQ', 'fixture', day))
        self.conn.commit()
        rows = ann.build_announcement_rows('EQ1', [item('100', '2026-09-17 09:00:00')], 'nse_corporate_announcements_live')
        rows += ann.build_announcement_rows('ETF1', [item('200', '2026-09-17 09:00:00')], 'nse_corporate_announcements_live')
        rows += ann.build_announcement_rows('OLD', [item('300', '2025-12-01 09:00:00')], 'nse_corporate_announcements_live')
        from src.bitemporal.store import write_facts
        write_facts(self.conn, 'corporate_announcements', rows)
        self.isin = dict(EQ1='INE000000001', EQ2='INE000000002', ETF1='INF000000003', OLD='INE000000004')
        self.state = Path(self.temp.name) / 'state.json'

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def run_refresh(self, session, **kw):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            summary = recent.main(END, mode='per_symbol', conn=self.conn, session=session, isin_map=self.isin, state_path=self.state, **kw)
        return summary, out.getvalue()

    def count(self, symbol):
        return self.conn.execute('SELECT COUNT(*) FROM corporate_announcements WHERE symbol=?', (symbol,)).fetchone()[0]

    def test_first_run_scope_window_and_duplicates(self):
        session = Session({'EQ1': (200, [item('100', '2026-09-17 09:00:00'), item('101', '2026-09-25 15:30:00'),
                                         item('102', '2026-10-01 18:00:00')])})
        summary, out = self.run_refresh(session)
        # Only active equities with stored rows: no fund unit, no inactive symbol, no never-fetched symbol.
        self.assertEqual([c['symbol'] for c in session.calls], ['EQ1'])
        self.assertEqual((session.calls[0]['from_date'], session.calls[0]['to_date']), ('10-09-2026', '04-10-2026'))
        self.assertEqual((summary['inserted'], summary['skipped_duplicate'], summary['status']), (2, 1, 'COMPLETE'))
        self.assertEqual(summary['universe']['without_stored_rows'], 1)                 # EQ2 left to the backfill
        self.assertEqual(self.count('EQ1'), 3)
        known = dict(self.conn.execute("SELECT seq_id, knowledge_date FROM corporate_announcements WHERE symbol='EQ1'").fetchall())
        self.assertEqual(known['101'], '2026-09-25')                                    # publication date, not fetch date
        self.assertEqual(json.loads(self.state.read_text())['last_complete'], '2026-10-04')
        self.assertNotIn('WARN', out)

    def test_failure_is_visible_and_not_marked_complete(self):
        summary, out = self.run_refresh(Session({'EQ1': (503, [])}))
        self.assertEqual((summary['status'], summary['failed']), ('PARTIAL', 1))
        self.assertIn('WARN announcements refresh: FAILED EQ1: AnnouncementFetchError', out)
        self.assertFalse(self.state.exists())
        sys.path.insert(0, str(ROOT / 'scripts'))
        import weekly_ingest
        from desk.lib.connection import get_desk_connection
        desk_path = Path(self.temp.name) / 'desk.sqlite'          # never the production Desk store
        replay_partial = lambda: (print(out), summary)[1]
        with patch('ingest_announcements_recent.main', side_effect=replay_partial), \
             patch('desk.lib.connection.get_desk_connection', side_effect=lambda: get_desk_connection(desk_path)):
            self.assertEqual(weekly_ingest._run_capturing('announcements_recent', weekly_ingest.step_announcements_recent)['status'], 'WARN')
        from desk.source_freshness import BACKFILL_COMPLETE_THROUGH, complete_through
        desk = get_desk_connection(desk_path)
        try:
            self.assertEqual(complete_through(desk, 'EQ1'), BACKFILL_COMPLETE_THROUGH)   # failed symbol stays stale
        finally:
            desk.close()

    def test_nightly_cadence_and_later_window(self):
        # Daily: a refresh already complete today is not repeated; yesterday's is due again.
        self.state.write_text(json.dumps(dict(last_complete='2026-10-04')), encoding='utf-8')
        session = Session({'EQ1': (200, [])})
        summary, _ = self.run_refresh(session)
        self.assertEqual((summary['status'], session.calls), ('NOT_DUE', []))
        self.state.write_text(json.dumps(dict(last_complete='2026-10-03')), encoding='utf-8')
        summary, _ = self.run_refresh(session)
        self.assertEqual(session.calls[0]['from_date'], '26-09-2026')                   # last complete minus 7 days
        self.assertEqual((summary['status'], summary['failed_symbols']), ('COMPLETE', []))

    def test_missing_isin_map_refuses(self):
        with patch.object(recent, 'ISIN_MAP_PATH', Path(self.temp.name) / 'absent.json'), self.assertRaises(Exception):
            recent.main(END, mode='per_symbol', conn=self.conn, session=Session({}), state_path=self.state)


class BackfillVisibilityTest(unittest.TestCase):
    def test_backfill_failures_print_warn_lines(self):
        import ingest_announcements_full_history as backfill
        with tempfile.TemporaryDirectory() as temp:
            conn = get_connection(str(Path(temp) / 'praman.db'))
            init_db(conn)
            conn.execute("INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,"
                         "prev_close,traded_qty,series,source_file,recorded_at) VALUES ('NEW','2026-10-01','2026-10-01',1,1,1,1,1,1,'EQ','f','t')")
            conn.commit()
            with patch.object(backfill, 'get_connection', return_value=conn), patch.object(backfill, 'init_db'), \
                 patch.object(backfill, '_session_with_cookie', return_value=Session({'NEW': (500, [])})), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                backfill.main(END)
        self.assertIn('WARN announcements backfill: FAILED NEW: AnnouncementFetchError', out.getvalue())
        self.assertIn('WARN announcements backfill: 1 symbols FAILED', out.getvalue())


if __name__ == '__main__':
    unittest.main()
