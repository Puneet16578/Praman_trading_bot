"""P8-054: `desk monitor` finds mechanical exits on every session since entry, in date order.

Before: the stop was checked on the run date's session only, so a stop hit on an evening nobody ran
the monitor was missed (or filled on a later day at a later price). Synthetic store, temp files only.
"""
from pathlib import Path
import tempfile
import unittest

from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.monitor import first_mechanical_exit, run_monitor
from src.bitemporal.connection import get_connection, init_db

DAYS = ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-09', '2026-11-10']
FLAT = (100.0, 101.0, 99.0, 100.0)      # open, high, low, close: never near the 92 stop


class MonitorCatchUpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.praman = get_connection(str(Path(self.temp.name) / 'praman.db'))
        init_db(self.praman)
        self.desk = get_desk_connection(Path(self.temp.name) / 'desk.sqlite')

    def tearDown(self):
        self.praman.close()
        self.desk.close()
        self.temp.cleanup()

    def bars(self, **override):
        """One MANU bar per day, each known on its own date; `d2=(o, h, l, c)` overrides DAYS[2]."""
        for i, day in enumerate(DAYS):
            o, h, l, c = override.get(f'd{i}', FLAT)
            self.praman.execute('INSERT INTO bhavcopy (symbol,event_date,knowledge_date,open_price,high_price,low_price,'
                                'close_price,prev_close,traded_qty,series,source_file,recorded_at) VALUES '
                                "('MANU',?,?,?,?,?,?,?,1000,'EQ','fixture',?)", (day, day, o, h, l, c, c, day))
        self.praman.commit()

    def trade(self, *, horizon='2026-12-31', link=True):
        """Decision on DAYS[0], entry filled on DAYS[1] at 100, stop 92, target 120."""
        thesis_id = jstore.record_thesis(
            self.desk, symbol='MANU', evidence_cutoff=DAYS[0], hypotheses=[dict(statement='s', test='t', monitor='m')],
            drivers=['d'], horizon=horizon, invalidation_conditions=['i'], exit_price='stop or target',
            exit_time='exit at the next session open after the horizon', exit_evidence='e', exit_risk='r',
            exit_portfolio='p', planned_entry=100.0, planned_stop=92.0, planned_target=120.0, sector='Test')
        decision_id = jstore.record_decision(
            self.desk, symbol='MANU', as_of_date=DAYS[0], thesis_id=thesis_id, evidence_bundle_hash='h', gate_results={},
            state='ELIGIBLE', rulebook_version='v', rulebook_hash='r', cost_config_version='c', cost_config_hash='k',
            code_commit='c', praman_watermark='w', desk_watermark_value='d', as_of_is_live=True, isin_map_built_at='x',
            position_size=10, stress_loss_inr=100.0)
        trade_id = f'MANU:{thesis_id}'
        jstore.open_paper_trade(self.desk, trade_id=trade_id, decision_id=decision_id if link else None,
                                event_date=DAYS[1], price=100.0, quantity=10, stop=92.0, target=120.0,
                                buy_cost_inr=1.0, cost_config_hash='k')
        return trade_id

    def close_event(self, trade_id):
        row = self.desk.execute("SELECT event_date, price, reason FROM paper_trade_events WHERE trade_id=? AND event_type='CLOSE'",
                                (trade_id,)).fetchone()
        return tuple(row) if row else None

    def test_stop_touched_on_a_missed_evening_is_found_and_filled_that_day(self):
        self.bars(d2=(96.0, 97.0, 90.0, 95.0), d3=(97.0, 98.0, 96.0, 97.0))   # touch on d2, recovered by d3
        trade_id = self.trade()
        report = run_monitor(self.praman, self.desk, DAYS[3])                  # nobody ran it on d2
        self.assertEqual(report['exits_triggered'], [dict(trade_id=trade_id, reason='stop_touch', price=92.0,
                                                          event_date=DAYS[2], trigger='price')])
        self.assertEqual(self.close_event(trade_id), (DAYS[2], 92.0, 'stop (stop_touch)'))
        self.assertEqual(jstore.open_trade_ids(self.desk), [])

    def test_gap_on_a_missed_evening_fills_at_that_open_not_a_later_one(self):
        self.bars(d2=(88.0, 89.0, 85.0, 86.0), d3=(80.0, 81.0, 79.0, 80.0))
        trade_id = self.trade()
        run_monitor(self.praman, self.desk, DAYS[4])
        self.assertEqual(self.close_event(trade_id), (DAYS[2], 88.0, 'stop (stop_gap)'))

    def test_missed_horizon_orders_on_recovery_and_fills_after_it(self):
        from desk.brief import manual_monitor_lines
        self.bars(d4=(103.0, 104.0, 102.0, 103.0), d6=(106.0, 107.0, 105.0, 106.0))
        trade_id = self.trade(horizon=DAYS[3])
        report = run_monitor(self.praman, self.desk, DAYS[5])
        self.assertIsNone(self.close_event(trade_id))
        self.assertEqual(report['time_exits_pending'], [dict(trade_id=trade_id, not_before_date=DAYS[5],
                         horizon=DAYS[3], ordered_late_by_sessions=2)])
        self.assertIn('2 session(s) late', '\n'.join(manual_monitor_lines(self.desk, DAYS[5])))
        run_monitor(self.praman, self.desk, DAYS[5])
        self.assertEqual(self.desk.execute("SELECT COUNT(*) FROM journal_events WHERE event_type='TIME_EXIT_ORDERED'").fetchone()[0], 1)
        run_monitor(self.praman, self.desk, DAYS[6])
        self.assertEqual(self.close_event(trade_id)[:2], (DAYS[6], 106.0))

    def test_order_on_horizon_fills_next_open_despite_missed_later_runs(self):
        self.bars(d4=(103.0, 104.0, 102.0, 103.0))
        trade_id = self.trade(horizon=DAYS[3])
        report = run_monitor(self.praman, self.desk, DAYS[3])
        self.assertEqual(report['time_exits_pending'][0]['ordered_late_by_sessions'], 0)
        self.assertIsNone(self.close_event(trade_id))
        run_monitor(self.praman, self.desk, DAYS[6])
        self.assertEqual(self.close_event(trade_id)[:2], (DAYS[4], 103.0))

    def test_on_the_time_exit_session_only_the_open_counts(self):
        self.bars(d4=(100.0, 101.0, 85.0, 90.0))
        trade_id = self.trade(horizon=DAYS[3])
        run_monitor(self.praman, self.desk, DAYS[3])
        run_monitor(self.praman, self.desk, DAYS[5])
        self.assertEqual(self.close_event(trade_id)[:2], (DAYS[4], 100.0))

    def test_time_exit_session_opening_through_the_stop_is_a_stop_gap(self):
        self.bars(d4=(90.0, 91.0, 89.0, 90.0))
        trade_id = self.trade(horizon=DAYS[3])
        run_monitor(self.praman, self.desk, DAYS[3])
        fill, trigger = first_mechanical_exit(self.praman, self.desk, trade_id, DAYS[5])
        self.assertEqual((fill.event_date, fill.price, fill.kind, trigger), (DAYS[4], 90.0, 'stop_gap', 'price'))

    def test_overdue_horizon_does_not_backdate_to_entry_or_next_open(self):
        self.bars(d2=(104.0, 105.0, 103.0, 104.0))
        trade_id = self.trade(horizon=DAYS[0])
        self.assertIsNone(first_mechanical_exit(self.praman, self.desk, trade_id, DAYS[3]))
        run_monitor(self.praman, self.desk, DAYS[3])
        self.assertIsNone(self.close_event(trade_id))
        run_monitor(self.praman, self.desk, DAYS[4])
        self.assertEqual(self.close_event(trade_id)[:2], (DAYS[4], 100.0))

    def test_standing_stop_on_missed_horizon_precedes_new_time_order(self):
        self.bars(d4=(95.0, 96.0, 91.0, 93.0))
        trade_id = self.trade(horizon=DAYS[3])
        report = run_monitor(self.praman, self.desk, DAYS[5])
        self.assertEqual(self.close_event(trade_id)[:2], (DAYS[4], 92.0))
        self.assertNotIn('time_exits_pending', report)

    def test_trade_without_a_linked_thesis_has_no_time_exit_but_keeps_its_stop(self):
        self.bars(d5=(95.0, 96.0, 91.0, 92.0))
        trade_id = self.trade(horizon=DAYS[1], link=False)
        self.assertIsNone(first_mechanical_exit(self.praman, self.desk, trade_id, DAYS[4]))
        run_monitor(self.praman, self.desk, DAYS[6])
        self.assertEqual(self.close_event(trade_id), (DAYS[5], 92.0, 'stop (stop_touch)'))

    def test_each_session_uses_the_stop_in_force_on_that_date(self):
        self.bars(d2=(95.0, 96.0, 91.0, 93.0))                                # 91 touches the original 92 stop
        trade_id = self.trade()
        jstore.adjust_paper_trade(self.desk, trade_id=trade_id, event_date=DAYS[3], price=100.0, quantity=10,
                                  stop=85.0, target=120.0, reason='manual stop widen')
        run_monitor(self.praman, self.desk, DAYS[4])
        self.assertEqual(self.close_event(trade_id), (DAYS[2], 92.0, 'stop (stop_touch)'))


if __name__ == '__main__':
    unittest.main()
