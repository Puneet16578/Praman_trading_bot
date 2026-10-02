import copy
import unittest
from unittest.mock import patch

from desk.lib.connection import get_desk_connection
from desk.journal import store
from desk.process_quality import audit_trade_process
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS


class ProcessQualityTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_desk_connection(':memory:')
        self.addCleanup(self.conn.close)
        self.trade = 'AXISBANK:1'

    def entry(self, *, incomplete=False, override=None, late_thesis=False, stress_loss=None):
        thesis = copy.deepcopy(COMPLETE_AXISBANK_THESIS)
        if incomplete:
            thesis['hypotheses'] = []
        with patch('desk.journal.store._now', return_value='2021-10-29T00:00:00+00:00' if late_thesis else '2021-10-26T00:00:00+00:00'):
            thesis_id = store.record_thesis(self.conn, symbol='AXISBANK', evidence_cutoff='2021-10-26', **thesis)
        with patch('desk.journal.store._now', return_value='2021-10-26T01:00:00+00:00'):
            decision = store.record_decision(self.conn, symbol='AXISBANK', as_of_date='2021-10-26', thesis_id=thesis_id,
                evidence_bundle_hash='e', gate_results={}, state='ELIGIBLE', rulebook_version='test', rulebook_hash='r',
                cost_config_version='test', cost_config_hash='c', code_commit='code', praman_watermark='p',
                desk_watermark_value='d', as_of_is_live=True, isin_map_built_at='', override_reason=override,
                stress_loss_inr=stress_loss)
        with patch('desk.journal.store._now', return_value='2021-10-27T00:00:00+00:00'):
            store.open_paper_trade(self.conn, trade_id=self.trade, decision_id=decision, event_date='2021-10-27',
                                   price=750, quantity=10, stop=700, target=820, buy_cost_inr=1, cost_config_hash='c')

    def exit(self, *, recorded=True, manual=False):
        reason = 'Taking cash for a planned expense' if manual else 'stop (stop_intraday)'
        if recorded:
            self.journal('MANUAL_CLOSE_REQUEST' if manual else 'EXIT_TRIGGER',
                         {'trigger':'price', 'event_date':'2021-10-28'}, reason)
        with patch('desk.journal.store._now', return_value='2021-10-28T02:00:00+00:00'):
            store.close_paper_trade(self.conn, trade_id=self.trade, event_date='2021-10-28', price=700,
                                    reason=reason, sell_cost_inr=1, cost_config_hash='c')

    def journal(self, kind, detail=None, reason=None):
        with patch('desk.journal.store._now', return_value='2021-10-28T01:00:00+00:00'):
            store.record_journal_event(self.conn, event_type=kind, trade_id=self.trade,
                                       detail=detail or {}, reason=reason)

    def test_complete_entry_and_recorded_trigger_is_good_even_when_losing(self):
        self.entry(); self.exit()
        self.assertTrue(audit_trade_process(self.conn, self.trade)['good'])

    def test_reasoned_manual_request_is_good_without_matching_a_trigger_prefix(self):
        self.entry(); self.exit(manual=True)
        self.assertTrue(audit_trade_process(self.conn, self.trade)['good'])

    def test_matching_exit_reason_alone_is_insufficient(self):
        self.entry(); self.exit(recorded=False)
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])

    def test_incomplete_thesis_at_entry_fails(self):
        self.entry(incomplete=True); self.exit()
        self.assertFalse(audit_trade_process(self.conn, self.trade)['thesis_complete_at_entry'])

    def test_later_complete_thesis_cannot_repair_entry_retroactively(self):
        self.entry(late_thesis=True); self.exit()
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])

    def test_decision_g7_override_fails(self):
        self.entry(override='Exceptional case'); self.exit()
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])

    def test_journal_g7_override_fails(self):
        self.entry(); self.journal('G7_OVERRIDE', reason='Exceptional case'); self.exit()
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])

    def test_unlogged_violation_fails_despite_valid_exit(self):
        self.entry(); self.journal('UNLOGGED_RULE_VIOLATION'); self.exit()
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])

    def test_unlogged_stop_widening_is_detected_from_trade_history(self):
        self.entry()
        with patch('desk.journal.store._now', return_value='2021-10-27T01:00:00+00:00'):
            store.adjust_paper_trade(self.conn, trade_id=self.trade, event_date='2021-10-27', price=750,
                                     quantity=10, stop=600, target=820, reason='manual stop widen')
        self.exit()
        self.assertEqual(audit_trade_process(self.conn, self.trade)['unlogged_violations'], 1)

    def test_late_exit_record_does_not_retroactively_validate_process(self):
        self.entry(); self.exit(recorded=False)
        with patch('desk.journal.store._now', return_value='2021-10-29T00:00:00+00:00'):
            store.record_journal_event(self.conn, event_type='EXIT_TRIGGER', trade_id=self.trade,
                                      detail={'trigger':'price','event_date':'2021-10-28'}, reason='stop (stop_intraday)')
        self.assertFalse(audit_trade_process(self.conn, self.trade)['good'])
