"""Manual paper limit entry (user-approved convention, 2026-10-04) and the decision share basis (P8-044)."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.paper.close import PaperCloseRefused, close_approved_trade
from desk.paper.execution import check_stop_on_session
from desk.paper.open import NoFill, PaperOpenRefused, PendingOpen, open_approved_decision
from desk.risk.officer import realized_pnl_inr
from src.bitemporal.connection import get_connection, init_db
from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, make_test_costs


def weekdays(start, n):
    days, d = [], date.fromisoformat(start)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


DAYS = weekdays('2026-08-03', 40)
D = DAYS[24]          # decision date: 24 prior sessions give ATR20 = 4 exactly
F, F2, F3 = DAYS[25], DAYS[26], DAYS[27]


class PaperLimitEntryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')
        self.costs = make_test_costs()
        for day in DAYS[:25]:
            self.bar(day, 100, 102, 98, 100)          # true range 4 every session -> ATR20 = 4

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def bar(self, day, o, h, l, c, symbol='LIMITCO'):
        self.praman.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price,'
                            'prev_close,traded_qty,series,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                            (symbol, day, day, o, h, l, c, c, 100000, 'EQ', 'fixture', day))
        self.praman.commit()

    def action(self, kind, ex_date, num=None, den=None, known=None, symbol='LIMITCO'):
        self.praman.execute('INSERT INTO corporate_actions (symbol,action_type,event_date,knowledge_date,ratio_numerator,'
                            'ratio_denominator,confidence_tier,details,source_file,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                            (symbol, kind, ex_date, known or ex_date, num, den, 'HIGH', 'fixture', 'fixture', ex_date))
        self.praman.commit()

    def decision(self, entry=100.0, stop=92.0, qty=50):
        thesis = dict(COMPLETE_AXISBANK_THESIS, planned_entry=entry, planned_stop=stop, planned_target=120.0)
        thesis_id = jstore.record_thesis(self.desk, symbol='LIMITCO', evidence_cutoff=D,
                                         **{k: v for k, v in thesis.items() if k != 'thesis_id'})
        return jstore.record_decision(
            self.desk, symbol='LIMITCO', as_of_date=D, thesis_id=thesis_id, evidence_bundle_hash='h', gate_results={},
            state='ELIGIBLE', rulebook_version='v3', rulebook_hash='r', cost_config_version='v1', cost_config_hash='c',
            code_commit='c', praman_watermark='w', desk_watermark_value='d', as_of_is_live=True,
            isin_map_built_at='2026-09-01T00:00:00+00:00', position_size=qty, stress_loss_inr=1000.0)

    def open(self, decision_id):
        now = datetime.fromisoformat(D + 'T12:00:00+00:00')
        return open_approved_decision(self.praman, self.desk, decision_id, costs=self.costs, cost_config_hash='h', now=now)

    def opened(self, decision_id):
        thesis_id = jstore.get_decision(self.desk, decision_id)['thesis_id']
        return jstore.latest_trade_event(self.desk, f'LIMITCO:{thesis_id}')

    def test_open_at_or_below_limit_fills_at_the_open(self):
        self.bar(F, 101.5, 103, 100, 102)
        decision_id = self.decision()
        result = self.open(decision_id)                           # limit 100 + 0.5 x 4 = 102
        self.assertEqual((result.event_date, result.price), (F, 101.5))
        self.assertEqual(self.opened(decision_id)['reason'], 'entry: FILL_OPEN (limit 102.00)')

    def test_open_above_limit_fills_at_limit_when_low_reaches_it(self):
        self.bar(F, 105, 106, 101, 104)
        decision_id = self.decision()
        result = self.open(decision_id)
        self.assertEqual(result.price, 102.0)
        self.assertEqual(self.opened(decision_id)['quantity'], 50)            # quantity unchanged

    def test_untouched_limit_is_a_terminal_no_fill(self):
        self.bar(F, 105, 107, 103, 106)
        decision_id = self.decision()
        result = self.open(decision_id)
        self.assertIsInstance(result, NoFill)
        self.assertEqual((result.session, result.limit, result.status), (F, 102.0, 'NO_FILL'))
        self.assertIsNone(self.opened(decision_id))
        row = self.desk.execute("SELECT detail FROM journal_events WHERE event_type='PAPER_OPEN_NO_FILL'").fetchone()
        self.assertEqual(json.loads(row[0])['low'], 103)

    def test_pending_open_resolves_to_no_fill_and_is_never_retried(self):
        from desk.monitor import complete_pending_paper_opens
        decision_id = self.decision()
        result = self.open(decision_id)
        self.assertIsInstance(result, PendingOpen)                            # F not ingested yet
        jstore.record_journal_event(self.desk, event_type='PAPER_OPEN_PENDING', decision_id=decision_id,
                                    detail={'not_before_date': result.not_before_date})
        self.bar(F, 105, 107, 103, 106)

        class Loaded:
            costs, sha256 = self.costs, 'h'
        done = complete_pending_paper_opens(self.praman, self.desk, Loaded)
        self.assertEqual([(d['status'], d['event_date']) for d in done], [('NO_FILL', F)])
        self.assertEqual(jstore.pending_paper_opens(self.desk), [])
        self.assertEqual(complete_pending_paper_opens(self.praman, self.desk, Loaded), [])

    def test_unusable_session_prices_are_a_terminal_unknown(self):
        self.bar(F, 105, 106, 0, 104)                                        # open above limit, unusable low
        result = self.open(self.decision())
        self.assertIsInstance(result, NoFill)
        self.assertEqual(result.status, 'UNKNOWN')

    def test_old_split_no_longer_scales_the_fill_p8044(self):
        # A 10:1 split in 2022 left the history-wide cumulative factor at 10. The old fill
        # multiplied the raw open by it (1015 instead of 101.5); stop and quantity are raw.
        for day in ('2022-07-01', '2022-07-29'):
            self.bar(day, 1000 if day < '2022-07-28' else 100, 1000, 100, 100)
        self.action('SPLIT', '2022-07-28', 10, 1, known='2022-07-01')
        self.bar(F, 101.5, 103, 100, 102)
        result = self.open(self.decision())
        self.assertEqual(result.price, 101.5)

    def test_split_between_decision_and_fill_is_priced_on_the_decision_basis(self):
        self.action('SPLIT', F, 10, 1, known=D)
        self.bar(F, 10.15, 10.3, 10.0, 10.2)                                # raw, post-split
        decision_id = self.decision()
        result = self.open(decision_id)
        self.assertAlmostEqual(result.price, 101.5)                          # 10.15 x 10, decision basis
        self.assertEqual(self.opened(decision_id)['quantity'], 50)            # decision-basis shares

    def test_demerger_before_fill_refuses(self):
        self.action('DEMERGER', F, known=D)
        self.bar(F, 60, 61, 59, 60)
        with self.assertRaises(PaperOpenRefused):
            self.open(self.decision())

    def test_stop_and_exit_after_a_split_during_the_position(self):
        self.bar(F, 101.5, 103, 100, 102)
        decision_id = self.decision()
        self.open(decision_id)
        self.action('SPLIT', F2, 10, 1, known=F)
        self.bar(F2, 10.0, 10.2, 9.7, 10.0)                                  # 100 / 97 on the decision basis
        self.assertIsNone(check_stop_on_session(self.praman, 'LIMITCO', F2, 92.0, F2, basis_date=D))
        self.assertEqual(check_stop_on_session(self.praman, 'LIMITCO', F2, 92.0, F2).kind, 'stop_gap')  # raw: false stop
        self.bar(F3, 9.5, 9.6, 9.0, 9.2)
        hit = check_stop_on_session(self.praman, 'LIMITCO', F3, 92.0, F3, basis_date=D)
        self.assertEqual((hit.kind, hit.price), ('stop_touch', 92.0))
        thesis_id = jstore.get_decision(self.desk, decision_id)['thesis_id']
        now = datetime.fromisoformat(F2 + 'T12:00:00+00:00')
        close = close_approved_trade(self.praman, self.desk, f'LIMITCO:{thesis_id}', reason='manual', costs=self.costs,
                                     cost_config_hash='h', now=now)
        self.assertAlmostEqual(close.price, 95.0)                              # 9.5 x 10, decision basis
        opened = self.desk.execute("SELECT * FROM paper_trade_events WHERE event_type='OPEN'").fetchone()
        closed = self.desk.execute("SELECT * FROM paper_trade_events WHERE event_type='CLOSE'").fetchone()
        pnl = realized_pnl_inr(opened['price'], closed['price'], opened['quantity'], opened['buy_cost_inr'], closed['sell_cost_inr'])
        self.assertAlmostEqual(pnl, (95.0 - 101.5) * 50 - opened['buy_cost_inr'] - closed['sell_cost_inr'])

    def test_demerger_during_position_refuses_automatic_exit_pricing(self):
        self.bar(F, 101.5, 103, 100, 102)
        decision_id = self.decision()
        self.open(decision_id)
        self.action('DEMERGER', F2, known=F)
        self.bar(F3, 60, 61, 59, 60)
        thesis_id = jstore.get_decision(self.desk, decision_id)['thesis_id']
        with self.assertRaises(PaperCloseRefused):
            close_approved_trade(self.praman, self.desk, f'LIMITCO:{thesis_id}', reason='manual', costs=self.costs,
                                 cost_config_hash='h', now=datetime.fromisoformat(F2 + 'T12:00:00+00:00'))


if __name__ == '__main__':
    unittest.main()
