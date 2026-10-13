"""P8-058: the manual book's open risk is the stress loss recorded when each trade was opened.

The rulebook caps open risk on STRESS loss (`risk.max_open_risk_pct`); G6 and sizing used to sum
entry-to-stop risk for open manual trades, which understates a 20%-band stock about fourfold."""
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

import yaml

from desk.circuit_bands import CircuitBand
from desk.gates.checks import g6_risk
from desk.gates.engine import OpenRiskUnknown, _open_risk_used_inr
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.rulebook import DeskRulebook
from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.risk.officer import compute_stress_loss, planned_loss_inr
from src.bitemporal.connection import get_connection, init_db
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs

ROOT = Path(__file__).resolve().parents[1]
try:
    get_live_connection().close()
    _PRODUCTION = True
except ProductionStoreMissingError:
    _PRODUCTION = False


def rulebook():
    return DeskRulebook.model_validate(yaml.safe_load((ROOT / 'rulebook/desk_rulebook_v3.yaml').read_text(encoding='utf-8')))


class ManualOpenRiskTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        self.costs, self.rb = make_test_costs(), rulebook()
        d, self.days = date(2026, 9, 1), []
        while len(self.days) < 30:                       # flat history: no overnight gap
            if d.weekday() < 5:
                day = d.isoformat()
                self.days.append(day)
                self.praman.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                                    'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                                    "('BAND20',?,?,100,101,99,100,100,100000,'EQ','fixture',?)", (day, day, day))
            d += timedelta(days=1)
        self.praman.commit()

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def open_trade(self, stress_loss_inr, *, link=True):
        thesis_id = jstore.record_thesis(
            self.desk, symbol='BAND20', evidence_cutoff=self.days[-1], hypotheses=[dict(statement='s', test='t', monitor='m')],
            drivers=['d'], horizon='2026-12-31', invalidation_conditions=['i'], exit_price='p',
            exit_time='exit at the next session open after the horizon', exit_evidence='e', exit_risk='r',
            exit_portfolio='f', planned_entry=100.0, planned_stop=90.0, planned_target=130.0, sector='Test')
        decision_id = jstore.record_decision(
            self.desk, symbol='BAND20', as_of_date=self.days[-1], thesis_id=thesis_id, evidence_bundle_hash='h',
            gate_results={}, state='ELIGIBLE', rulebook_version='v3', rulebook_hash='r', cost_config_version='c',
            cost_config_hash='k', code_commit='c', praman_watermark='w', desk_watermark_value='d', as_of_is_live=True,
            isin_map_built_at='x', position_size=50, stress_loss_inr=stress_loss_inr)
        trade_id = f'BAND20:{thesis_id}'
        jstore.open_paper_trade(self.desk, trade_id=trade_id, decision_id=decision_id if link else None,
                                event_date=self.days[-1], price=100.0, quantity=50, stop=90.0, target=130.0,
                                buy_cost_inr=1.0, cost_config_hash='k')
        return trade_id

    def band_stress(self):
        """The rulebook's stress loss for 50 shares, entry 100, stop 90, on a fixed 20% band."""
        return compute_stress_loss(self.praman, 'BAND20', self.days[-1], 100.0, 90.0, 50, self.costs, self.rb,
                                   circuit_band=CircuitBand(kind='FIXED', percent=20.0)).stress_loss_inr

    def test_open_risk_is_the_recorded_stress_loss_not_entry_to_stop(self):
        stress = self.band_stress()
        entry_to_stop = abs(100.0 - 90.0) * 50                # the old measure: Rs 500
        self.assertAlmostEqual(stress, 100.0 * 50 * 0.20 * self.rb.risk.circuit_lock_days)   # Rs 2,000, locked circuit
        self.assertAlmostEqual(stress / entry_to_stop, 4.0)
        self.open_trade(stress)
        self.assertAlmostEqual(_open_risk_used_inr(self.desk), stress)

    def test_g6_counts_the_open_trade_at_its_stress_loss(self):
        self.open_trade(self.band_stress())
        budget = self.rb.risk.capital_allocated_inr * self.rb.risk.max_open_risk_pct / 100    # Rs 25,000
        candidate = budget - 1000.0                          # fits beside Rs 500, not beside Rs 2,000
        planned = planned_loss_inr(100.0, 99.0, 10, self.costs)
        result = g6_risk(planned_loss_inr=planned, stress_loss_inr=candidate, open_risk_used_inr=_open_risk_used_inr(self.desk),
                         capital_at_stock_inr=0.0, capital_at_sector_inr=0.0, rulebook=self.rb)
        self.assertEqual(result.result, 'FAIL')
        self.assertIn('open risk already used (Rs 2,000)', ' '.join(result.reasons))
        old = g6_risk(planned_loss_inr=planned, stress_loss_inr=candidate, open_risk_used_inr=500.0,
                      capital_at_stock_inr=0.0, capital_at_sector_inr=0.0, rulebook=self.rb)
        self.assertEqual(old.result, 'PASS')                 # what the entry-to-stop measure let through

    def test_a_trade_without_a_recorded_stress_loss_makes_open_risk_unknown(self):
        trade_id = self.open_trade(2000.0, link=False)
        with self.assertRaisesRegex(OpenRiskUnknown, trade_id):
            _open_risk_used_inr(self.desk)
        from desk.brief import open_risk_lines
        lines = open_risk_lines(self.desk, self.rb, None)
        self.assertEqual(lines[0], 'Open risk by book (stress loss, the rulebook measure):')
        self.assertTrue(any(line.startswith('  Manual (strategy_id=manual): UNKNOWN (No recorded stress loss') for line in lines))

    def test_closed_trades_do_not_count_and_the_brief_shows_the_stress_loss(self):
        trade_id = self.open_trade(self.band_stress())
        from desk.brief import open_risk_lines
        self.assertIn('  Manual (strategy_id=manual): Rs 2,000.00 of Rs 25,000.00; open trades',
                      '\n'.join(open_risk_lines(self.desk, self.rb, None)))
        jstore.close_paper_trade(self.desk, trade_id=trade_id, event_date=self.days[-1], price=95.0, reason='manual',
                                 sell_cost_inr=1.0, cost_config_hash='k')
        self.assertEqual(_open_risk_used_inr(self.desk), 0.0)


@unittest.skipUnless(_PRODUCTION, 'Real Praman production store not found.')
class AssessmentWithUnknownOpenRiskTest(unittest.TestCase):
    def test_unknown_open_risk_makes_g5_and_g6_unknown(self):
        from desk.gates.engine import run_assessment
        with tempfile.TemporaryDirectory() as temp:
            praman = get_connection(str(Path(temp) / 'praman.db'))
            init_db(praman)
            prod = get_live_connection()
            try:
                copy_symbol_rows(prod, praman, 'AXISBANK')
            finally:
                prod.close()
            desk = get_desk_connection(Path(temp) / 'desk.sqlite')
            try:
                as_of = praman.execute("SELECT MAX(event_date) FROM bhavcopy WHERE symbol='AXISBANK'").fetchone()[0]
                jstore.open_paper_trade(desk, trade_id='OTHER:1', decision_id=None, event_date=as_of, price=100.0,
                                        quantity=10, stop=90.0, target=120.0, buy_cost_inr=1.0, cost_config_hash='k')
                result = run_assessment(praman, desk, symbol='AXISBANK', as_of_date=as_of, sector='Financials',
                                        thesis=dict(COMPLETE_AXISBANK_THESIS, horizon='2027-03-31'), rulebook=rulebook(),
                                        costs=make_test_costs())
                for gate in ('G5', 'G6'):
                    self.assertEqual(result.gate_results[gate].result, 'UNKNOWN')
                    self.assertIn('No recorded stress loss for open manual trade(s) OTHER:1',
                                  ' '.join(result.gate_results[gate].reasons))
                self.assertNotEqual(result.state, 'ELIGIBLE')
            finally:
                desk.close()
                praman.close()


if __name__ == '__main__':
    unittest.main()
