"""Stable IDs, dated identities, retained universe and all-or-nothing freshness."""
from datetime import date
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.bitemporal.connection import get_connection, init_db
from src.ingestion.nse_market_data.announcements import ingest_symbol_announcements
from src.ingestion.nse_market_data.announcements_bulk import (
    ingest_bulk, stable_id, resolve_publication_identity, read_equity_announcements,
    CaptureSession, RequestBudgetExceeded, fetch_checked_window, AnnouncementFetchError)
from scripts import ingest_announcements_recent as recent


def snapshot(day, **symbols):
    return dict(event_date=day, knowledge_date=day,
                records=[dict(symbol=s, isin=i, series='EQ') for s, i in symbols.items()])


def raw(seq='1', symbol='OLD', isin='INE000000001', day='2026-09-12'):
    return dict(seq_id=seq, symbol=symbol, sm_isin=isin, sort_date=day+' 12:00:00',
                desc='Updates', attchmntText='The same disclosure', attchmntFile='https://example.test/a.pdf')


class IdentityTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(':memory:')
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_real_rename_pairs_cannot_duplicate_even_via_legacy_fallback(self):
        f = json.loads((Path(__file__).parent/'fixtures/announcements_bulk_reconciliation.json').read_text(encoding='utf-8'))
        snapshots = [snapshot('2026-09-07', **f['old_symbol_isins'])]
        first = ingest_bulk(self.conn, f['bulk_renames'], snapshots=snapshots, fetched_on='2026-10-05', source_file='test')
        self.assertEqual(first['inserted'], 5)
        for stored in f['stored_renames']:
            item = next(r for r in f['bulk_renames'] if r['seq_id']==stored['seq_id'])
            item = dict(item, symbol=stored['symbol'])
            self.assertEqual(ingest_bulk(self.conn, [item], snapshots=snapshots,
                fetched_on='2026-10-05', source_file='test')['inserted'], 0)
            self.assertEqual(ingest_symbol_announcements(self.conn, 'OTHER_ALIAS', [item], 'legacy').inserted, 0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM corporate_announcements').fetchone()[0], 5)
        self.assertEqual({r[0] for r in self.conn.execute('SELECT DISTINCT symbol FROM corporate_announcements')}, {'HEG','SANGINITA'})

    def test_hash_fallback_survives_rename_and_future_identity_does_not_leak(self):
        a, b = raw(seq=None), raw(seq=None, symbol='NEW')
        self.assertEqual(stable_id(a), stable_id(b))
        snapshots = [snapshot('2026-09-11', OLD='INE000000001'), snapshot('2026-09-20', NEW='INE000000001')]
        self.assertEqual(resolve_publication_identity(b, snapshots)[:3], ('OLD','INE000000001','2026-09-11'))
        self.assertIsNone(resolve_publication_identity(b, snapshots[1:])[1])
        ingest_bulk(self.conn, [a,b], snapshots=snapshots, fetched_on='2026-10-05', source_file='test')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM corporate_announcements').fetchone()[0], 1)

    def test_dated_isin_beats_current_isin_and_fund_is_only_filtered_on_read(self):
        snapshots = [snapshot('2026-09-11', OLD='INE000000001', FUND='INF000000002')]
        ingest_bulk(self.conn, [raw(isin='INE_NEW_AFTER_SPLIT'), raw('2','FUND','INF000000002')],
                    snapshots=snapshots, fetched_on='2026-10-05', source_file='test')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM corporate_announcements').fetchone()[0], 2)
        self.assertEqual(read_equity_announcements(self.conn,'FUND','2026-09-13',snapshots=snapshots), [])
        rows = read_equity_announcements(self.conn,'OLD','2026-09-13',snapshots=snapshots)
        self.assertEqual(rows[0]['isin'], 'INE000000001')

    def test_revision_appends_later_knowledge_without_changing_original(self):
        snapshots = [snapshot('2026-09-11', OLD='INE000000001')]
        item = raw()
        ingest_bulk(self.conn,[item],snapshots=snapshots,fetched_on='2026-09-13',source_file='test')
        original = dict(self.conn.execute('SELECT * FROM corporate_announcements').fetchone())
        ingest_bulk(self.conn,[dict(item,attchmntText='Corrected')],snapshots=snapshots,fetched_on='2026-10-05',source_file='test')
        self.assertEqual(dict(self.conn.execute('SELECT * FROM corporate_announcements WHERE row_id=?',(original['row_id'],)).fetchone()), original)
        self.assertEqual(read_equity_announcements(self.conn,'OLD','2026-09-13',snapshots=snapshots)[0]['description'], 'The same disclosure')
        self.assertEqual(read_equity_announcements(self.conn,'OLD','2026-10-05',snapshots=snapshots)[0]['description'], 'Corrected')

    def test_additive_migration_preserves_legacy_duplicates_and_blocks_new_ones(self):
        c = get_connection(':memory:')
        try:
            c.execute('CREATE TABLE corporate_announcements (row_id INTEGER PRIMARY KEY,symbol TEXT,event_date TEXT,'
                      'knowledge_date TEXT,seq_id TEXT,category TEXT,description TEXT,sort_timestamp TEXT,source_file TEXT,recorded_at TEXT)')
            for n,s in enumerate(['OLD','NEW'],1):
                c.execute('INSERT INTO corporate_announcements VALUES (?,?,?,?,?,?,?,?,?,?)',
                          (n,s,'2026-09-12','2026-09-12','1','Updates','same','2026-09-12 12:00:00','old','old'))
            before = [tuple(r) for r in c.execute('SELECT * FROM corporate_announcements')]
            init_db(c)
            init_db(c)
            self.assertEqual([tuple(r)[:10] for r in c.execute('SELECT * FROM corporate_announcements')],before)
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO corporate_announcements (symbol,event_date,knowledge_date,seq_id) VALUES ('THIRD','2026-09-12','2026-09-12','1')")
        finally:
            c.close()

    def test_identity_facts_obey_recorded_at_replay_and_knowledge_cutoffs(self):
        from src.bitemporal.store import write_facts
        write_facts(self.conn,'security_identities',[
            dict(symbol='OLD',isin='INE000000001',series='EQ',event_date='2026-09-11',knowledge_date='2026-09-11',source_file='test'),
            dict(symbol='NEW',isin='INE000000001',series='EQ',event_date='2026-09-20',knowledge_date='2026-09-20',source_file='test')])
        ingest_bulk(self.conn,[raw()],snapshots=[snapshot('2026-09-11',OLD='INE000000001')],
                    fetched_on='2026-10-05',source_file='test')
        self.assertEqual(len(read_equity_announcements(self.conn,'NEW','2026-09-21')),1)
        self.assertEqual(read_equity_announcements(self.conn,'NEW','2026-09-15'),[])
        self.conn.execute("CREATE TEMP VIEW security_identities AS SELECT * FROM main.security_identities WHERE recorded_at<'1900-01-01'")
        self.assertEqual(read_equity_announcements(self.conn,'NEW','2026-09-21'),[])

    def test_ingestion_identity_comes_from_the_fact_table_as_of_the_run(self):
        from src.bitemporal.store import write_facts
        from src.ingestion.nse_market_data.announcements_bulk import identity_snapshots_from_store
        write_facts(self.conn,'security_identities',[
            dict(symbol='OLD',isin='INE000000001',series='EQ',event_date='2026-09-11',knowledge_date='2026-09-11',source_file='t'),
            dict(symbol='LATER',isin='INE000000009',series='EQ',event_date='2026-10-06',knowledge_date='2026-10-06',source_file='t')])
        snapshots = identity_snapshots_from_store(self.conn, '2026-10-05')
        self.assertEqual([(s['event_date'], [r['symbol'] for r in s['records']]) for s in snapshots], [('2026-09-11', ['OLD'])])
        ingest_bulk(self.conn, [raw()], snapshots=snapshots, fetched_on='2026-10-05', source_file='test')
        row = self.conn.execute('SELECT symbol, isin, identity_status FROM corporate_announcements').fetchone()
        self.assertEqual(tuple(row), ('OLD', 'INE000000001', 'DATED_SYMBOL'))
        # Under a replay view recorded before the facts existed, no identity evidence is visible.
        self.conn.execute("CREATE TEMP VIEW security_identities AS SELECT * FROM main.security_identities WHERE recorded_at<'1900-01-01'")
        self.assertEqual(identity_snapshots_from_store(self.conn, '2026-10-05'), [])

    def test_equity_read_keeps_dvr_class_and_excludes_fund_units(self):
        snapshots = [snapshot('2026-09-11', DVRCO='IN9000000001', FUNDCO='INF000000002')]
        ingest_bulk(self.conn, [raw('7', 'DVRCO', 'IN9000000001'), raw('8', 'FUNDCO', 'INF000000002')],
                    snapshots=snapshots, fetched_on='2026-10-05', source_file='test')
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM corporate_announcements').fetchone()[0], 2)  # all stored
        self.assertEqual(len(read_equity_announcements(self.conn, 'DVRCO', '2026-09-13', snapshots=snapshots)), 1)
        self.assertEqual(read_equity_announcements(self.conn, 'FUNDCO', '2026-09-13', snapshots=snapshots), [])


class RefreshTest(unittest.TestCase):
    def test_middle_window_failure_preserves_global_watermark_and_warns(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); state=root/'state.json'; identity=root/'identity'; identity.mkdir()
            initial=json.dumps(dict(last_complete='2026-09-10',coverage_from='2026-09-10'))
            state.write_text(initial,encoding='utf-8')
            conn=get_connection(':memory:'); init_db(conn)
            class Client:
                directory=root
                trace=[]
            def fetch(client,first,last):
                if first==date(2026,9,17):
                    raise AnnouncementFetchError('fixture middle failure')
                return [raw(str(first),day=first.isoformat())]
            with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_checked_window',side_effect=fetch), contextlib.redirect_stdout(io.StringIO()) as out:
                result=recent.main(date(2026,9,30),conn=conn,client=Client(),state_path=state,identity_dir=identity)
            self.assertEqual(result['status'],'PARTIAL')
            self.assertIn('WARN',out.getvalue())
            self.assertEqual(state.read_text(encoding='utf-8'),initial)
            self.assertEqual(result['inserted'],2)
            with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_checked_window',return_value=[]), contextlib.redirect_stdout(io.StringIO()):
                result=recent.main(date(2026,9,30),conn=conn,client=Client(),state_path=state,identity_dir=identity)
            self.assertEqual(result['status'],'COMPLETE')
            self.assertEqual(json.loads(state.read_text(encoding='utf-8'))['last_complete'],'2026-09-30')
            conn.close()

    def test_split_window_difference_is_a_failure(self):
        with patch('src.ingestion.nse_market_data.announcements_bulk.fetch_window',side_effect=[[raw()],[],[]]):
            with self.assertRaises(AnnouncementFetchError):
                fetch_checked_window(None,date(2026,9,10),date(2026,9,16))

    def test_request_cap_includes_failed_attempts_and_disables_redirects(self):
        class Session:
            headers={}
            calls=[]
            def get(self,url,**kw):
                self.calls.append(kw)
                raise TimeoutError('fixture')
            def close(self):
                pass
        with tempfile.TemporaryDirectory() as td:
            session=Session(); client=CaptureSession(Path(td)/'capture',{'backfill':1},session=session)
            with self.assertRaises(TimeoutError):
                client.get('one','https://example.test')
            with self.assertRaises(RequestBudgetExceeded):
                client.get('two','https://example.test')
            self.assertEqual(len(session.calls),1)
            self.assertFalse(session.calls[0]['allow_redirects'])
            client.close()
