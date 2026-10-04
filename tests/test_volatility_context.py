import json
from pathlib import Path
import tempfile
import unittest
from desk.evidence.types import Fact, Unknown
from desk.volatility_context import BOUNDARIES, context_from_values, atr20_and_close
from scripts.desk_volatility_reference import build_reference


class VolatilityContextTest(unittest.TestCase):
    def test_ties_source_type_and_retrospective_date(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'reference.json'
            source.write_text(json.dumps(dict(assessment_context=dict(boundaries_pct=list(BOUNDARIES),
                known_on='2026-10-04',quintiles=[dict(quintile=q,rate=dict(estimate=.1*q,interval95=[.05,.6],
                n_events=100,date_clusters=30,usable_replicates=2000)) for q in range(1,6)]))),encoding='utf-8')
            for i,boundary in enumerate(BOUNDARIES,2):
                result=context_from_values(boundary,100,'2020-01-02',source=source)
                self.assertEqual(result.quintile,i)
                self.assertIsInstance(result.historical_rate,Fact)
                record=result.to_record()
                self.assertEqual(record['historical_rate']['type'],'FACT')
                self.assertEqual(record['reference_known_on'],'2026-10-04')
                self.assertTrue(record['informational_only'])
                self.assertIn('shadow_replay_followup_results',result.display())
                json.dumps(record,allow_nan=False)

    def test_retrospective_label_depends_on_publication_date(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'reference.json'
            source.write_text(json.dumps(dict(assessment_context=dict(boundaries_pct=list(BOUNDARIES),
                known_on='2026-10-04',quintiles=[dict(quintile=q,rate=dict(estimate=.1,interval95=[.05,.2],
                n_events=100,date_clusters=30,usable_replicates=2000)) for q in range(1,6)]))),encoding='utf-8')
            past=context_from_values(4,100,'2021-10-27',source=source)
            current=context_from_values(4,100,'2026-10-05',source=source)
            self.assertTrue(past.to_record()['retrospective'])
            self.assertIn('RETROSPECTIVE',past.display())
            self.assertFalse(current.to_record()['retrospective'])
            self.assertNotIn('RETROSPECTIVE',current.display())
        self.assertFalse(context_from_values(4,100,'2021-10-27',source=Path('absent_reference_038.json')).retrospective)

    def test_missing_reference_preserves_measured_volatility(self):
        result=context_from_values(5,100,'2020-01-02',source=Path('absent_reference_038.json'))
        self.assertEqual(result.quintile,4)
        self.assertEqual(result.atr20_pct,5)
        self.assertIsInstance(result.historical_rate,Unknown)
        self.assertIsNone(context_from_values(None,100,'2020-01-02').quintile)

    def test_pooled_reference_uses_both_states_and_missingness(self):
        rows=[dict(event_date='2020-01-02',state=state,plan=dict(atr20=2,decision_price=100),adverse20=outcome)
              for state,outcome in [('SCREEN_PASS',False),('SCREEN_FAIL',True),('SCREEN_FAIL',None)]]
        result=build_reference(rows,replicates=20)['quintiles'][0]
        self.assertEqual(result['candidates'],3)
        self.assertEqual(result['missing_outcomes'],1)
        self.assertEqual(result['rate']['estimate'],.5)

    def test_real_atr_agrees_with_screening_plan(self):
        from desk.lib.store import get_live_connection
        from desk.screening_plan import decision_plan
        conn=get_live_connection()
        try:
            atr,close=atr20_and_close(conn,'AXISBANK','2021-10-27')
            plan=decision_plan(conn,'AXISBANK','2021-10-27')
            self.assertEqual(atr,plan['atr20'])
            self.assertEqual(close,plan['decision_price'])
        finally:
            conn.close()

    def test_context_is_append_only_and_linked_separately(self):
        from desk.lib.connection import get_desk_connection
        from desk.volatility_context import record_context
        with tempfile.TemporaryDirectory() as temp:
            conn=get_desk_connection(Path(temp)/'desk.sqlite')
            try:
                value=context_from_values(5,100,'2020-01-02',source=Path(temp)/'missing.json')
                record_context(conn,value,symbol='EXAMPLE',decision_id=1)
                record_context(conn,value,symbol='EXAMPLE',opportunity_id=2)
                records=conn.execute("SELECT * FROM journal_events WHERE event_type='VOLATILITY_CONTEXT'").fetchall()
                self.assertEqual(len(records),2)
                self.assertEqual(records[0]['decision_id'],1)
                detail=json.loads(records[1]['detail'])
                self.assertEqual(detail['opportunity_id'],2)
                self.assertEqual(detail['context']['decision_as_of'],'2020-01-02')
                self.assertTrue(detail['context']['informational_only'])
            finally:
                conn.close()
