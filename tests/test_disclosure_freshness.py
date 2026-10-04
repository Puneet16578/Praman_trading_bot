"""P8-021 addition: missing announcements never read as "no disclosure"."""
import contextlib
from datetime import date, timedelta
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from desk.evidence.bundle import _disclosures
from desk.evidence.types import Fact, Unknown
from desk.lib.connection import get_desk_connection
from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.source_freshness import BACKFILL_COMPLETE_THROUGH, complete_through, record_refresh, required_through
from src.bitemporal.connection import get_connection, init_db
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs, make_test_rulebook

ROOT = Path(__file__).resolve().parents[1]
try:
    get_live_connection().close()
    _PRODUCTION = True
except ProductionStoreMissingError:
    _PRODUCTION = False


def day_before(d, n=1):
    return (date.fromisoformat(d) - timedelta(days=n)).isoformat()


class FreshnessRulesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desk_path = Path(self.temp.name) / 'desk.sqlite'
        self.desk = get_desk_connection(self.desk_path)

    def tearDown(self):
        self.desk.close()
        self.temp.cleanup()

    def test_required_date_is_the_day_before_the_decision(self):
        self.assertEqual(required_through('2026-10-05'), '2026-10-04')
        self.assertEqual(complete_through(self.desk, 'X'), BACKFILL_COMPLETE_THROUGH)
        self.assertEqual(complete_through(None, 'X'), BACKFILL_COMPLETE_THROUGH)

    def test_partial_refresh_keeps_failed_symbols_stale(self):
        record_refresh(self.desk, through_date='2026-10-05', status='PARTIAL', failed_symbols=['BAD'], summary={})
        self.assertEqual(complete_through(self.desk, 'GOOD'), '2026-10-05')
        self.assertEqual(complete_through(self.desk, 'BAD'), BACKFILL_COMPLETE_THROUGH)
        record_refresh(self.desk, through_date='2026-10-06', status='COMPLETE', failed_symbols=[], summary={})
        self.assertEqual(complete_through(self.desk, 'BAD'), '2026-10-06')
        with self.assertRaises(ValueError):
            record_refresh(self.desk, through_date='2026-10-07', status='NOT_DUE', failed_symbols=[], summary={})

    def test_replay_sees_only_the_freshness_known_at_the_decision(self):
        from desk.replay import get_desk_replay_connection
        record_refresh(self.desk, through_date='2026-10-05', status='COMPLETE', failed_symbols=[], summary={})
        watermark = self.desk.execute('SELECT recorded_at FROM source_freshness').fetchone()[0]
        record_refresh(self.desk, through_date='2026-10-09', status='COMPLETE', failed_symbols=[], summary={})
        replay = get_desk_replay_connection(self.desk_path, watermark)
        try:
            self.assertEqual(complete_through(replay, 'X'), '2026-10-05')
        finally:
            replay.close()
        self.assertEqual(complete_through(self.desk, 'X'), '2026-10-09')

    def test_nightly_step_records_the_watermark_only_after_a_refresh(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import weekly_ingest
        summary = dict(status='PARTIAL', end_date='2026-10-05', failed_symbols=['BAD'])
        with patch('ingest_announcements_recent.main', return_value=summary), \
             patch('desk.lib.connection.get_desk_connection', side_effect=lambda: get_desk_connection(self.desk_path)), \
             contextlib.redirect_stdout(io.StringIO()):
            weekly_ingest.step_announcements_recent()
        with patch('ingest_announcements_recent.main', return_value=dict(status='NOT_DUE')), \
             contextlib.redirect_stdout(io.StringIO()):
            weekly_ingest.step_announcements_recent()
        rows = self.desk.execute('SELECT through_date, status FROM source_freshness').fetchall()
        self.assertEqual([tuple(r) for r in rows], [('2026-10-05', 'PARTIAL')])
        self.assertEqual(complete_through(self.desk, 'BAD'), BACKFILL_COMPLETE_THROUGH)


class MissingCoverageTest(unittest.TestCase):
    """Synthetic store: an empty window is only evidence when the window was really checked."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.conn = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.conn)
        d = date(2026, 8, 3)
        self.days = []
        while len(self.days) < 15:
            if d.weekday() < 5:
                self.days.append(d.isoformat())
                self.conn.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                                  'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                                  "('NOANN',?,?,100,101,99,100,100,1000,'EQ','f',?)", (d.isoformat(),) * 3)
            d += timedelta(days=1)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_symbol_never_covered_is_unknown(self):
        ev = _disclosures(self.conn, 'NOANN', self.days[-1], '2026-12-31')
        self.assertIsInstance(ev, Unknown)
        self.assertIn('No announcement has ever been stored', ev.detail)

    def test_insufficient_history_is_unknown(self):
        ev = _disclosures(self.conn, 'NOANN', self.days[4], '2026-12-31')
        self.assertIsInstance(ev, Unknown)
        self.assertIn('insufficient_history', ev.detail)


@unittest.skipUnless(_PRODUCTION, 'Real Praman production store not found.')
class RealDataFreshnessTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        prod = get_live_connection()
        try:
            copy_symbol_rows(prod, self.praman, 'AXISBANK')
        finally:
            prod.close()
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        self.sessions = [r[0] for r in self.praman.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date",
            (day_before(BACKFILL_COMPLETE_THROUGH, -1),))]

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def test_stale_source_never_yields_a_disclosure_fact(self):
        self.assertGreater(len(self.sessions), 5)
        for as_of in self.sessions:
            for lag in (1, 2, 5, 10, 30):
                stale = day_before(as_of, 1 + lag)
                ev = _disclosures(self.praman, 'AXISBANK', as_of, stale)
                self.assertIsInstance(ev, Unknown, (as_of, stale))
                self.assertIn('complete only through', ev.detail)
            self.assertIsInstance(_disclosures(self.praman, 'AXISBANK', as_of, None), Unknown)   # baseline only
        fresh = _disclosures(self.praman, 'AXISBANK', self.sessions[-1], day_before(self.sessions[-1]))
        self.assertIsInstance(fresh, Fact)
        historical = _disclosures(self.praman, 'AXISBANK', '2021-10-27', None)                # inside the baseline
        self.assertIsInstance(historical, Fact)

    def test_stale_source_makes_the_assessment_insufficient(self):
        from desk.gates.engine import run_assessment
        as_of = self.sessions[-1]
        thesis = dict(COMPLETE_AXISBANK_THESIS, horizon='2027-03-31')
        stale = run_assessment(self.praman, self.desk, symbol='AXISBANK', as_of_date=as_of, sector='Financials',
                               thesis=thesis, rulebook=make_test_rulebook(), costs=make_test_costs())
        self.assertEqual(stale.state, 'INSUFFICIENT')
        self.assertEqual(stale.gate_results['G2'].result, 'FAIL')
        self.assertIn("'disclosures'", ' '.join(stale.gate_results['G2'].reasons))
        record_refresh(self.desk, through_date=as_of, status='COMPLETE', failed_symbols=[], summary={})
        fresh = run_assessment(self.praman, self.desk, symbol='AXISBANK', as_of_date=as_of, sector='Financials',
                               thesis=thesis, rulebook=make_test_rulebook(), costs=make_test_costs())
        self.assertEqual(fresh.gate_results['G2'].result, 'PASS')
        self.assertNotEqual(fresh.state, 'INSUFFICIENT')


if __name__ == '__main__':
    unittest.main()
