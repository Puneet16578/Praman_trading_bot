"""P8-069: a filing published during the refresh no longer voids the night's certification.

The whole/split comparison covers completed days only; the open day's filings are stored, and the
night's receipt certifies through the day before (P8-049). No network: fetch_window is faked.
"""
from datetime import date, datetime
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desk.lib.connection import get_desk_connection
from desk.source_freshness import complete_through, record_refresh
from scripts import ingest_announcements_recent as recent
from shared.market_time import IST
from src.bitemporal.connection import get_connection, init_db
from src.ingestion.nse_market_data.announcements_bulk import AnnouncementFetchError, fetch_checked_window

OPEN_DAY = date(2026, 10, 13)


def filing(seq, when, symbol='AAA'):
    return dict(seq_id=str(seq), symbol=symbol, sm_isin='INE000000001', sort_date=when, desc='Updates',
                attchmntText=f'disclosure {seq}', attchmntFile=f'https://example.test/{seq}.pdf')


COMPLETED = [filing(1, '2026-10-12 11:00:00'), filing(2, '2026-10-12 19:30:00')]
EARLY_TODAY = filing(3, '2026-10-13 18:05:15')
RACE = filing(4, '2026-10-13 18:06:54')        # in the whole response, not yet in the single-day one


def fake_fetch(rows, missing_from_split=()):
    def fetch_window(client, start, end, *, component='backfill', label='bulk'):
        picked = [r for r in rows if start <= date.fromisoformat(r['sort_date'][:10]) <= end]
        if label == 'check':
            picked = [r for r in picked if r not in missing_from_split]
        return picked
    return fetch_window


class OpenDayComparisonTest(unittest.TestCase):
    def check(self, rows, missing_from_split=(), open_day=OPEN_DAY):
        with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_window',
                   side_effect=fake_fetch(rows, missing_from_split)):
            return fetch_checked_window(None, date(2026, 10, 12), date(2026, 10, 13), open_day=open_day)

    def test_a_filing_arriving_between_the_two_requests_no_longer_fails_the_window(self):
        rows = COMPLETED + [EARLY_TODAY, RACE]
        with self.assertRaisesRegex(AnnouncementFetchError, 'Whole/split'):      # the 13 Oct failure, before
            self.check(rows, missing_from_split=[RACE], open_day=None)
        stored = self.check(rows, missing_from_split=[RACE])
        self.assertEqual(sorted(r['seq_id'] for r in stored), ['1', '2', '3', '4'])

    def test_an_open_day_filing_only_the_split_saw_is_stored_too(self):
        def fetch_window(client, start, end, *, component='backfill', label='bulk'):
            picked = [r for r in COMPLETED + [EARLY_TODAY, RACE] if start <= date.fromisoformat(r['sort_date'][:10]) <= end]
            return picked if label == 'check' else [r for r in picked if r is not RACE]
        with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_window', side_effect=fetch_window):
            stored = fetch_checked_window(None, date(2026, 10, 12), date(2026, 10, 13), open_day=OPEN_DAY)
        self.assertEqual(sorted(r['seq_id'] for r in stored), ['1', '2', '3', '4'])

    def test_a_difference_on_a_completed_day_still_fails(self):
        with self.assertRaisesRegex(AnnouncementFetchError, 'Whole/split'):
            self.check(COMPLETED + [EARLY_TODAY], missing_from_split=[COMPLETED[1]])


class OpenDayRefreshTest(unittest.TestCase):
    def test_the_night_completes_and_its_receipt_certifies_only_the_day_before(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state, identity = root / 'state.json', root / 'identity'
            identity.mkdir()
            state.write_text(json.dumps(dict(last_complete='2026-10-12', coverage_from='2026-09-10')), encoding='utf-8')
            conn = get_connection(':memory:')
            init_db(conn)

            class Client:
                directory = root
                trace = []
            rows = COMPLETED + [EARLY_TODAY, RACE]
            with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_window',
                       side_effect=fake_fetch(rows, missing_from_split=[RACE])), \
                    patch.object(recent, 'market_today', return_value=OPEN_DAY), \
                    contextlib.redirect_stdout(io.StringIO()):
                summary = recent.main(OPEN_DAY, conn=conn, client=Client(), state_path=state, identity_dir=identity)
            self.assertEqual((summary['status'], summary['failed_windows']), ('COMPLETE', []))
            last = summary['windows'][-1]
            self.assertEqual((last['open_day'], last['open_day_rows']), ('2026-10-13', 2))
            stored = {r[0] for r in conn.execute('SELECT seq_id FROM corporate_announcements')}
            self.assertTrue({'1', '2', '3', '4'} <= stored)
            conn.close()
            desk = get_desk_connection(root / 'desk.sqlite')
            try:
                record_refresh(desk, through_date='2026-10-13', status='COMPLETE', failed_symbols=[], summary=summary,
                               now=datetime(2026, 10, 13, 18, 7, tzinfo=IST))
                self.assertEqual(complete_through(desk, 'AAA'), '2026-10-12')       # never the open day itself
            finally:
                desk.close()


if __name__ == '__main__':
    unittest.main()
