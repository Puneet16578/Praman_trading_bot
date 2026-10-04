"""CLI and scan persist information separately from decision inputs."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desk.gates.engine import AssessmentResult
from desk.lib.connection import get_desk_connection
from desk.volatility_context import BOUNDARIES, context_from_values


class ContextWiringTest(unittest.TestCase):
    def reference(self,folder):
        path=Path(folder)/'reference.json'
        path.write_text(json.dumps(dict(assessment_context=dict(boundaries_pct=list(BOUNDARIES),
            known_on='2026-10-04',quintiles=[dict(quintile=q,rate=dict(estimate=.1,interval95=[.08,.12],
            n_events=100,date_clusters=30,usable_replicates=2000)) for q in range(1,6)]))),encoding='utf-8')
        return context_from_values(5,100,'2020-01-02',source=path)

    def test_assess_prints_fact_and_records_linked_context(self):
        from desk.cli import cmd_assess
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'desk.sqlite'
            conn=get_desk_connection(path)
            result=AssessmentResult('WATCH',{},None)
            output=io.StringIO()
            with patch('desk.cli.get_live_connection',return_value=Mock()), \
                 patch('desk.cli.get_desk_connection',return_value=conn), \
                 patch('desk.cli.run_assessment',return_value=result), \
                 patch('desk.cli.max_recorded_at',return_value='2020-01-02T00:00:00+00:00'), \
                 patch('desk.cli.assessment_context',return_value=self.reference(temp)), \
                 contextlib.redirect_stdout(output):
                cmd_assess(SimpleNamespace(symbol='EXAMPLE',as_of='2020-01-02',thesis=None))
            self.assertIn('FACT: 2019-2025 pooled adverse20 rate',output.getvalue())
            self.assertIn('95% CI',output.getvalue())
            check=get_desk_connection(path)
            try:
                decision=check.execute('SELECT * FROM decisions').fetchone()
                record=check.execute("SELECT * FROM journal_events WHERE event_type='VOLATILITY_CONTEXT'").fetchone()
                self.assertEqual(decision['state'],'WATCH')
                self.assertEqual(json.loads(decision['gate_results']),{})
                self.assertEqual(record['decision_id'],decision['decision_id'])
                self.assertEqual(json.loads(record['detail'])['context']['historical_rate']['type'],'FACT')
            finally:
                check.close()

    def test_scan_records_context_without_changing_plan_or_gates(self):
        from desk.scan import run_scan_range
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'desk.sqlite'
            plan=dict(decision_price=100,atr20=5,quantity=1)
            assessment=AssessmentResult('SCREEN_PASS',{},SimpleNamespace(content_hash=lambda:'fixture'))
            with patch('desk.scan.get_live_connection',return_value=Mock()), \
                 patch('desk.scan.max_recorded_at',return_value='2020-01-02T00:00:00+00:00'), \
                 patch('desk.scan.catalogue_events',return_value=[SimpleNamespace(symbol='EXAMPLE',event_date='2020-01-02')]), \
                 patch('desk.scan.screen_event',return_value=(plan,assessment)), \
                 patch('desk.scan.execution_observation',return_value=None), \
                 patch('desk.scan.assessment_context',return_value=self.reference(temp)):
                self.assertEqual(run_scan_range(['2020-01-02'],desk_db_path=path),1)
                self.assertEqual(run_scan_range(['2020-01-02'],desk_db_path=path),0)
            conn=get_desk_connection(path)
            try:
                opportunity=conn.execute('SELECT * FROM opportunity_log').fetchone()
                records=conn.execute("SELECT * FROM journal_events WHERE event_type='VOLATILITY_CONTEXT'").fetchall()
                self.assertEqual(len(records),1)
                detail=json.loads(records[0]['detail'])
                self.assertEqual(detail['opportunity_id'],opportunity['opportunity_id'])
                self.assertEqual(detail['context']['historical_rate']['type'],'FACT')
                self.assertEqual(json.loads(opportunity['inputs'])['plan'],plan)
                self.assertEqual(json.loads(opportunity['gate_results']),{})
            finally:
                conn.close()
