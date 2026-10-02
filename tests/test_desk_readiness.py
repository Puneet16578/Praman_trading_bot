from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml
from pydantic import ValidationError

from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import DeskRulebook
from desk.readiness import gate_progress, open_defects
from tests import test_desk_process_quality as process_fixtures

ROOT = Path(__file__).resolve().parents[1]


class ReadinessTest(unittest.TestCase):
    def setUp(self):
        self.raw = yaml.safe_load((ROOT/'rulebook/desk_rulebook_v2.yaml').read_text())
        self.rb = DeskRulebook.model_validate(self.raw)
        self.conn = get_desk_connection(':memory:')
        self.addCleanup(self.conn.close)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.defects = Path(temporary.name)/'defects.md'
        self.defects.write_text('# Defects\n',encoding='utf-8')

    def test_v2_has_two_required_gates_and_v1_remains_loadable(self):
        self.assertIsNone(self.rb.paper_to_live_criteria)
        self.assertEqual(self.rb.operational_gate.min_calendar_days,90)
        self.assertEqual(self.rb.operational_gate.min_closed_paper_trades,30)
        self.assertEqual(self.rb.edge_confidence_gate.min_logged_opportunities,1000)
        self.assertEqual(self.rb.edge_confidence_gate.min_distinct_market_regimes,2)
        self.assertEqual(self.rb.edge_confidence_gate.bootstrap_confidence_level,.95)
        self.assertEqual(self.rb.risk.circuit_lock_days,2)
        self.assertEqual(self.rb.screening.stop_multiple,2)
        self.assertIsNotNone(DeskRulebook.model_validate(yaml.safe_load((ROOT/'rulebook/desk_rulebook_v1.yaml').read_text())).paper_to_live_criteria)
        del self.raw['edge_confidence_gate']
        with self.assertRaises(ValidationError):
            DeskRulebook.model_validate(self.raw)

    def test_empty_history_never_qualifies_and_edge_is_not_evaluable(self):
        result=gate_progress(self.conn,self.rb,today=date(2026,10,2),defect_path=self.defects)
        self.assertEqual(result['operational_gate']['status'],'NOT_MET')
        self.assertEqual(result['operational_gate']['checks']['calendar_days']['value'],0)
        self.assertEqual(result['edge_confidence_gate']['status'],'NOT_EVALUABLE')
        self.assertFalse(result['edge_confidence_gate']['checks']['bootstrap_lower_bound']['passed'])

    def test_severity_reader_finds_open_high_and_unclassified(self):
        self.defects.write_text('| P1-001 | now | High | description | Open |\n\n## P1-002 - issue (open)\n\n**Status.** Open\n',encoding='utf-8')
        self.assertEqual(open_defects(self.defects),(['P1-001'],['P1-002']))

    def test_calendar_boundary_and_recorded_exit_requirements(self):
        # Use real journal writes, with one trade sufficient only in this fixture.
        self.rb.operational_gate.min_closed_paper_trades=1
        fixture=process_fixtures.ProcessQualityTest()
        fixture.conn=self.conn;fixture.trade='AXISBANK:1'
        fixture.entry();fixture.exit(recorded=False)
        for today,expected in ((date(2022,1,24),False),(date(2022,1,25),True)):
            result=gate_progress(self.conn,self.rb,today=today,defect_path=self.defects)['operational_gate']
            self.assertEqual(result['checks']['calendar_days']['passed'],expected)
            self.assertFalse(result['checks']['recorded_exits']['passed'])
            self.assertFalse(result['checks']['open_risk_budget_breaches']['passed'])
            self.assertEqual(result['unknown_risk_records'],1)

    def test_high_defect_blocks_even_if_other_gate_evidence_passes(self):
        self.defects.write_text('| P1-001 | now | Critical | description | Found, not fixed |\n',encoding='utf-8')
        result=gate_progress(self.conn,self.rb,today=date(2026,10,2),defect_path=self.defects)['operational_gate']
        self.assertFalse(result['checks']['open_high_severity_defects']['passed'])

    def test_thirty_trades_ninety_days_and_all_operational_constraints(self):
        fixture=process_fixtures.ProcessQualityTest()
        fixture.conn=self.conn
        for i in range(30):
            fixture.trade=f'AXISBANK:{i}'
            fixture.entry(stress_loss=500);fixture.exit()
            if i==28:
                before=gate_progress(self.conn,self.rb,today=date(2022,1,25),defect_path=self.defects)
                self.assertFalse(before['operational_gate']['checks']['closed_paper_trades']['passed'])
        result=gate_progress(self.conn,self.rb,today=date(2022,1,25),defect_path=self.defects)
        self.assertEqual(result['operational_gate']['status'],'PASS')
        self.assertEqual(result['edge_confidence_gate']['status'],'NOT_EVALUABLE')
        fixture.journal('UNLOGGED_RULE_VIOLATION')
        result=gate_progress(self.conn,self.rb,today=date(2022,1,25),defect_path=self.defects)
        self.assertEqual(result['operational_gate']['status'],'NOT_MET')
        self.assertEqual(result['operational_gate']['checks']['unlogged_rule_violations']['value'],1)

    def test_historical_open_risk_breach_blocks_after_positions_close(self):
        fixture=process_fixtures.ProcessQualityTest()
        fixture.conn=self.conn
        for i in range(2):
            fixture.trade=f'AXISBANK:{i}'
            fixture.entry(stress_loss=13000);fixture.exit()
        result=gate_progress(self.conn,self.rb,today=date(2022,1,25),defect_path=self.defects)
        self.assertEqual(result['operational_gate']['checks']['open_risk_budget_breaches']['value'],1)
        self.assertFalse(result['operational_gate']['checks']['open_risk_budget_breaches']['passed'])
