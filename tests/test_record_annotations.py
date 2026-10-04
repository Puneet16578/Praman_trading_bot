"""P8-021 addition: append-only annotation of records made during the announcement lapse."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from desk.annotations import LAPSE_FROM, annotate_incomplete_disclosures, annotated_ids
from desk.lib.connection import get_desk_connection
from desk.lib.schema import INCOMPLETE_DISCLOSURE


class AnnotationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.conn = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        for symbol, event_date, recorded in [('OLD', '2026-09-10', '2026-09-12T10:00:00+00:00'),
                                             ('EARLY', '2026-09-17', '2026-10-01T08:00:00+00:00'),
                                             ('LATE', '2026-09-30', '2026-10-02T08:00:00+00:00'),
                                             ('AFTERFIX', '2026-10-05', '2026-10-05T13:00:00+00:00')]:
            self.conn.execute('INSERT INTO opportunity_log(symbol,event_date,knowledge_date,recorded_at,inputs,evidence_bundle_hash,'
                              'gate_results,state,reasons,content_hash,code_commit,praman_watermark,desk_watermark,rulebook_hash,'
                              "cost_config_hash) VALUES(?,?,?,?,'{}','h','{}','SCREEN_PASS','[]',?,'c','w','d','r','k')",
                              (symbol, event_date, event_date, recorded, symbol))
        self.conn.execute("INSERT INTO decisions (symbol, as_of_date, evidence_bundle_hash, gate_results, state, rulebook_version, "
                          "rulebook_hash, cost_config_version, cost_config_hash, code_commit, praman_watermark, desk_watermark, "
                          "as_of_is_live, recorded_at) VALUES ('D1','2026-09-29','h','{}','WATCH','v3','r','v1','c','s','w','d',1,"
                          "'2026-09-29T15:00:00+00:00')")
        self.conn.commit()
        self.until = '2026-10-04T15:30:00+00:00'

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def ids(self, *symbols):
        return {r[0] for r in self.conn.execute(
            f"SELECT opportunity_id FROM opportunity_log WHERE symbol IN ({','.join('?' * len(symbols))})", symbols)}

    def test_annotates_only_records_made_during_the_lapse(self):
        counts = annotate_incomplete_disclosures(self.conn, until=self.until)
        self.assertEqual(counts['opportunity_log'], dict(in_window=2, newly_annotated=2))
        self.assertEqual(counts['decisions'], dict(in_window=1, newly_annotated=1))
        self.assertEqual(annotated_ids(self.conn, 'opportunity_log'), self.ids('EARLY', 'LATE'))
        detail = {r['target_id']: json.loads(r['detail']) for r in self.conn.execute(
            "SELECT target_id, detail FROM record_annotations WHERE target_table='opportunity_log'")}
        early, late = detail[min(self.ids('EARLY'))], detail[min(self.ids('LATE'))]
        self.assertFalse(early['window_extends_past_coverage'])     # window needed only through 2026-09-16
        self.assertTrue(late['window_extends_past_coverage'])
        self.assertEqual(late['lapse_from'], LAPSE_FROM)

    def test_idempotent_and_never_edits_the_record(self):
        before = [tuple(r) for r in self.conn.execute('SELECT * FROM opportunity_log ORDER BY opportunity_id')]
        annotate_incomplete_disclosures(self.conn, until=self.until)
        again = annotate_incomplete_disclosures(self.conn, until=self.until)
        self.assertEqual(again['opportunity_log']['newly_annotated'], 0)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM record_annotations').fetchone()[0], 3)
        self.assertEqual([tuple(r) for r in self.conn.execute('SELECT * FROM opportunity_log ORDER BY opportunity_id')], before)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM record_annotations')
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE record_annotations SET annotation='X'")

    def test_research_queries_can_filter_on_the_annotation(self):
        annotate_incomplete_disclosures(self.conn, until=self.until)
        clean = {r[0] for r in self.conn.execute(
            'SELECT symbol FROM opportunity_log_annotated WHERE incomplete_disclosure_evidence = 0')}
        flagged = {r[0] for r in self.conn.execute(
            'SELECT symbol FROM opportunity_log_annotated WHERE incomplete_disclosure_evidence = 1')}
        self.assertEqual((clean, flagged), ({'OLD', 'AFTERFIX'}, {'EARLY', 'LATE'}))
        self.assertEqual([r[0] for r in self.conn.execute(
            'SELECT incomplete_disclosure_evidence FROM decisions_annotated')], [1])
        self.assertEqual(INCOMPLETE_DISCLOSURE, 'INCOMPLETE_DISCLOSURE_EVIDENCE')


if __name__ == '__main__':
    unittest.main()
