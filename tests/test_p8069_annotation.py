"""P8-069 note: 13 October's records are annotated, never edited or re-decided, and shown."""
import io
import json
import contextlib
import unittest

from desk.annotations import annotate_day_incomplete_disclosures, burn_in_incomplete_days
from desk.brief import build_brief, burn_in_incomplete_line
from scripts import desk_annotate_p8069 as script
from tests.test_strategy0_engine import DAYS, EngineFixture, opportunity, plan, rulebook


class P8069AnnotationTest(EngineFixture):
    def test_the_days_records_get_an_appended_note_shown_in_the_brief_and_status(self):
        day = DAYS[0]
        self.store.market(day)
        for symbol in ('AAA', 'BBB'):
            opportunity(self.desk, symbol, day, plan(), state='SCREEN_FAIL')
        self.run_day(day)
        before = [tuple(r) for r in self.desk.execute('SELECT * FROM strategy_runs')]
        self.assertEqual(burn_in_incomplete_line(self.desk), 'Strategy 0 burn-in dates decided on incomplete disclosure data: 0')
        counts = annotate_day_incomplete_disclosures(self.desk, day=day, defect='P8-069', reason='r', evidence=dict(e=1))
        self.assertEqual((counts['opportunity_log'], counts['strategy_runs']),
                         (dict(dated=2, newly_annotated=2), dict(dated=1, newly_annotated=1)))
        again = annotate_day_incomplete_disclosures(self.desk, day=day, defect='P8-069', reason='r', evidence=dict(e=1))
        self.assertEqual((again['opportunity_log']['newly_annotated'], again['strategy_runs']['newly_annotated']), (0, 0))
        self.assertEqual([tuple(r) for r in self.desk.execute('SELECT * FROM strategy_runs')], before)   # not re-decided
        self.assertEqual(burn_in_incomplete_days(self.desk), [dict(run_date=day, defect='P8-069')])
        line = f'Strategy 0 burn-in dates decided on incomplete disclosure data: 1: {day} (P8-069; 2 screen results annotated)'
        self.assertEqual(burn_in_incomplete_line(self.desk), line)
        self.assertIn(line, build_brief(self.store.conn, self.desk, day, rulebook=rulebook(), health_lines=[]))
        detail = json.loads(self.desk.execute('SELECT detail FROM record_annotations LIMIT 1').fetchone()[0])
        self.assertEqual((detail['defect'], detail['record_date']), ('P8-069', day))

    def test_the_one_time_script_targets_13_october_only(self):
        self.assertEqual(script.DAY, '2026-10-13')
        with contextlib.redirect_stdout(io.StringIO()):
            counts = script.main(self.desk)                 # an empty Desk: nothing dated 13 Oct, nothing written
        self.assertTrue(all(c['newly_annotated'] == 0 for c in counts.values()))


if __name__ == '__main__':
    unittest.main()
