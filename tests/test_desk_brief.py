"""Daily decision desk brief (session item B5)."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desk.brief import build_brief, write_brief
from tests.test_strategy0_engine import DAYS, EngineFixture, ROOT, expected_order, opportunity, plan, rulebook


class BriefTest(EngineFixture):
    def brief(self, day):
        return build_brief(self.store.conn, self.desk, day, rulebook=rulebook(), health_lines=['Ingestion health: fixture'])

    def test_candidates_shown_with_unknown_model_fields(self):
        self.store.market(DAYS[0], symbols=('ZZZ', 'AAA', 'BBB', 'CCC'))
        for s in ('AAA', 'BBB', 'CCC'):
            opportunity(self.desk, s, DAYS[0], plan())
        opportunity(self.desk, 'DDD', DAYS[0], plan(), state='SCREEN_FAIL')
        self.run_day(DAYS[0])
        text = self.brief(DAYS[0])
        seed, (first, second, last) = expected_order(('AAA', 'BBB', 'CCC'), DAYS[0])
        for expected in ('PRAMAN - DAILY DECISION DESK', 'Universe scanned: 4', 'Candidates: 4',
                         'Passed evidence/data checks: 3', 'High-confidence model candidates: UNKNOWN',
                         'Passed risk/portfolio/execution checks: 2', 'Rejected by reason: OPEN_RISK_BUDGET 1',
                         f'Strategy 0 version 3; candidate order SEEDED_RANDOM, seed {seed[:16]}',
                         f'Candidate {first}', f'Candidate {second}', 'Calibrated P(profitable): UNKNOWN (T4)',
                         'Expected value: UNKNOWN (T4)', 'Execution: limit order at 102.00', 'Final state: WATCH',
                         'Kill switches:', 'Rs 24,480.00 of Rs 25,000.00', 'Manual (strategy_id=manual)',
                         'SEALED until 2027-06-01', 'Data health:'):
            self.assertIn(expected, text)
        self.assertNotIn(f'Candidate {last}', text)
        self.assertNotIn('NO TRADE', text)

    def test_no_trade_is_a_normal_outcome(self):
        self.store.market(DAYS[0])
        self.run_day(DAYS[0])
        text = self.brief(DAYS[0])
        self.assertIn('NO TRADE - no candidate passed every check today. This is a normal outcome.', text)
        self.assertIn('Rejected by reason: none', text)

    def test_unrun_date_says_so(self):
        self.store.market(DAYS[0])
        self.assertIn('Strategy 0 has not run for this date', self.brief(DAYS[0]))

    def test_sealed_outcomes_never_displayed(self):
        self.store.market(DAYS[0])
        opportunity(self.desk, 'AAA', DAYS[0], plan())
        self.run_day(DAYS[0])
        self.store.market(DAYS[1])
        self.store.bar('AAA', DAYS[1], 101, 104, 100, 103)
        self.run_day(DAYS[1])
        self.store.market(DAYS[2])
        self.store.bar('AAA', DAYS[2], 87.65, 88, 87, 87.5)        # gap through the stop
        self.run_day(DAYS[2])
        self.assertEqual(len(self.events('EXIT_FILLED')), 1)
        text = self.brief(DAYS[2])
        for forbidden in ('87.65', 'pnl', 'P&L:', 'profit of', 'loss of', 'STOP', 'stop_gap'):
            self.assertNotIn(forbidden, text)

    def test_write_brief_names_file_by_date(self):
        self.store.market(DAYS[0])
        self.run_day(DAYS[0])
        with tempfile.TemporaryDirectory() as out, \
             patch('desk.lib.store.get_live_connection', return_value=self.store.conn), \
             patch('desk.lib.connection.get_desk_connection', return_value=self.desk), \
             patch('desk.lib.rulebook.load_active_rulebook', return_value=type('L', (), dict(rulebook=rulebook()))), \
             patch('desk.brief.health_lines', return_value=[]):
            path, text = write_brief(DAYS[0], out_dir=Path(out))
            self.assertEqual(path.name, f'brief_{DAYS[0]}.txt')
            self.assertEqual(path.read_text(encoding='utf-8'), text)
        # write_brief closed the fixture connections; reopen for tearDown.
        from desk.lib.connection import get_desk_connection
        self.desk = get_desk_connection(Path(self.temp.name)/'desk.sqlite')
        self.store.conn = __import__('sqlite3').connect(':memory:')


class BriefNightlyTest(unittest.TestCase):
    def test_brief_follows_auto_paper_in_nightly_run(self):
        sys.path.insert(0, str(ROOT/'scripts'))
        import weekly_ingest
        labels = [label for label, _ in weekly_ingest.STEPS]
        self.assertEqual(labels.index('brief'), labels.index('auto_paper') + 1)
        self.assertLess(labels.index('brief'), labels.index('backups'))
        with patch('desk.brief.write_brief', return_value=(Path('logs/brief_2026-10-05.txt'), '')) as called, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            weekly_ingest.step_brief()
        called.assert_called_once_with()
        self.assertIn('brief_2026-10-05.txt', out.getvalue())


if __name__ == '__main__':
    unittest.main()
