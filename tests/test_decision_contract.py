"""Blueprint decision contract (session item B3)."""
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desk import decision_contract as dc
from desk.gates.checks import GateResult
from desk.gates.engine import AssessmentResult
from desk.lib.connection import get_desk_connection


def contract(**overrides):
    args = dict(symbol='X', desk_state='SCREEN_PASS', hard_veto=False, horizon=dc.known('10d', 'fixed'),
                evidence_completeness=dc.known('G2 PASS', 'gate'), liquidity_state=dc.known('PASS', 'G5'),
                portfolio_incremental_risk=dc.known(1000.0, 'stress'), invalidations=['stop'],
                rejection_reasons=[], model_version='NONE', rulebook_version='v3', data_as_of='w', commit_hash='c')
    args.update(overrides)
    return dc.build_contract(**args)


class DecisionContractTest(unittest.TestCase):
    def test_every_blueprint_field_present(self):
        value = contract()
        for name in dc.FIELDS:
            self.assertIn(name, value)

    def test_later_phase_fields_are_unknown_with_reason_and_no_number(self):
        value = contract()
        for name in ('calibrated_probability', 'probability_interval', 'uncertainty_score', 'expected_value',
                     'historical_analogue_count', 'market_regime', 'sector_regime',
                     'expected_net_return_after_costs', 'maximum_adverse_excursion_estimate'):
            entry = value[name]
            self.assertEqual(entry['status'], 'UNKNOWN', name)
            self.assertNotIn('value', entry)
            self.assertTrue(entry['reason'])
            self.assertRegex(entry['supplied_by'], r'^T\d+$')

    def test_placeholder_numbers_are_rejected(self):
        value = contract()
        value['calibrated_probability'] = dict(status='UNKNOWN', reason='x', supplied_by='T4', value=0.5)
        with self.assertRaises(ValueError):
            dc.validate_contract(value)
        value = contract()
        value['portfolio_incremental_risk'] = dc.known(float('nan'), 'x')
        with self.assertRaises(ValueError):
            dc.validate_contract(value)
        value = contract()
        value['state'] = dc.known('ELIGIBLE', 'x')
        with self.assertRaises(ValueError):
            dc.validate_contract(value)

    def test_model_estimates_need_a_permitted_source(self):
        value = contract()
        value['calibrated_probability'] = dc.unvalidated(0.62, source='statistical_model', model_version='lr-v1',
                                                         definition='P(target before stop)')
        dc.validate_contract(value)
        self.assertEqual(value['calibrated_probability']['label'], dc.UNVALIDATED_LABEL)
        for bad in (dict(source='llm', model_version='x'), dict(source=None), dict(source='statistical_model')):
            value = contract()
            value['expected_value'] = dc.unvalidated(0.1, definition='EV in R', **(dict(model_version=None) | bad))
            with self.assertRaises(ValueError, msg=bad):
                dc.validate_contract(value)
        value = contract()
        value['expected_value'] = dc.unvalidated(0.1, source='user', definition='User EV estimate')
        dc.validate_contract(value)

    def test_unvalidated_estimates_never_make_a_candidate_eligible(self):
        value = contract()
        for name in ('calibrated_probability', 'expected_value'):
            value[name] = dc.unvalidated(0.7, source='statistical_model', model_version='m', definition='d')
        value['state'] = dc.known('ELIGIBLE', 'x')
        with self.assertRaises(ValueError):
            dc.validate_contract(value)
        # KNOWN requires a passed validation reference; without one it must stay UNVALIDATED.
        value['calibrated_probability'] = dict(dc.known(0.7, 'd'), source='statistical_model', model_version='m')
        with self.assertRaises(ValueError):
            dc.validate_contract(value)
        # A non-model field can never be UNVALIDATED, and the display-only label cannot be dropped.
        value = contract()
        value['liquidity_state'] = dc.unvalidated('PASS', source='user', definition='d')
        with self.assertRaises(ValueError):
            dc.validate_contract(value)
        value = contract()
        value['expected_value'] = dict(dc.unvalidated(0.1, source='user', definition='d'), display_only=False)
        with self.assertRaises(ValueError):
            dc.validate_contract(value)

    def test_blueprint_state_rule(self):
        self.assertEqual(contract(hard_veto=True)['state']['value'], 'VETO')
        self.assertEqual(contract(desk_state='SCREEN_FAIL')['state']['value'], 'NO_TRADE')
        self.assertEqual(contract(desk_state='INSUFFICIENT')['state']['value'], 'NO_TRADE')
        for state in ('SCREEN_PASS', 'ELIGIBLE', 'WATCH', 'RESEARCH_REQUIRED'):
            value = contract(desk_state=state)
            self.assertEqual(value['state']['value'], 'WATCH')
            self.assertEqual(value['desk_state']['value'], state)

    def test_contract_is_appended_and_linked_once(self):
        with tempfile.TemporaryDirectory() as temp:
            conn = get_desk_connection(Path(temp)/'desk.sqlite')
            try:
                with self.assertRaises(ValueError):
                    dc.record_contract(conn, contract())
                conn.execute("INSERT INTO decisions (symbol, as_of_date, evidence_bundle_hash, gate_results, state, "
                             "rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit, "
                             "praman_watermark, desk_watermark, as_of_is_live, recorded_at) VALUES "
                             "('X','2026-01-01','h','{}','WATCH','v3','r','v1','c','s','w','d',1,'t')")
                dc.record_contract(conn, contract(), decision_id=1)
                row = conn.execute('SELECT * FROM decision_contracts').fetchone()
                self.assertEqual(json.loads(row['contract'])['symbol']['value'], 'X')
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute('UPDATE decision_contracts SET contract=?', ('{}',))
            finally:
                conn.close()

    def test_assess_records_contract_without_changing_decision(self):
        from desk.cli import cmd_assess
        from desk.volatility_context import unavailable
        gates = {f'G{i}': GateResult(f'G{i}', 'PASS') for i in range(1, 9)}
        gates['G5'] = GateResult('G5', 'FAIL', ('Order too large.',))
        result = AssessmentResult('VETO', gates, None)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'desk.sqlite'
            with patch('desk.cli.get_live_connection', return_value=Mock()), \
                 patch('desk.cli.get_desk_connection', return_value=get_desk_connection(path)), \
                 patch('desk.cli.run_assessment', return_value=result), \
                 patch('desk.cli.max_recorded_at', return_value='2020-01-02T00:00:00+00:00'), \
                 patch('desk.cli.assessment_context', return_value=unavailable('2020-01-02', 'fixture')), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                cmd_assess(SimpleNamespace(symbol='EXAMPLE', as_of='2020-01-02', thesis=None))
            self.assertIn('blueprint state VETO', out.getvalue())
            conn = get_desk_connection(path)
            try:
                decision = conn.execute('SELECT * FROM decisions').fetchone()
                stored = json.loads(conn.execute('SELECT contract FROM decision_contracts WHERE decision_id=?',
                                                 (decision['decision_id'],)).fetchone()[0])
                self.assertEqual(decision['state'], 'VETO')
                self.assertEqual(stored['state']['value'], 'VETO')
                self.assertEqual(stored['liquidity_state']['value']['result'], 'FAIL')
                self.assertIn('G5: Order too large.', stored['rejection_reasons']['value'])
                self.assertEqual(stored['calibrated_probability']['status'], 'UNKNOWN')
            finally:
                conn.close()


if __name__ == '__main__':
    unittest.main()
