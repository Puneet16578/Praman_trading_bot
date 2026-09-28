"""Insert-time hardening on paper_trade_events (post-STOP-3-plus review), enforced by the database
itself, not just trusted to every caller: an OPEN row with no buy_cost_inr/cost_config_hash, a CLOSE
row with no sell_cost_inr/cost_config_hash, or ANY row with a non-integer quantity, is rejected
outright by a BEFORE INSERT trigger (desk/lib/schema.py). No behaviour change for any currently-
exercised code path -- every real call site already always supplies these; this only turns "should
never happen" into "cannot happen." Pure desk-schema tests -- no Praman production store needed.
"""
from __future__ import annotations
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection


class PaperTradeEventsInsertGuardsTest(unittest.TestCase):
    def setUp(self):
        self.db_path = Path(tempfile.mkdtemp(prefix="praman_desk_test_guards_")) / "desk.sqlite"
        self.conn = get_desk_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.db_path.parent, ignore_errors=True)

    # --- OPEN requires buy_cost_inr and cost_config_hash ------------------------------------------

    def test_open_without_buy_cost_inr_is_rejected(self):
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.open_paper_trade(self.conn, trade_id="AXISBANK:1", decision_id=1, event_date="2021-10-28",
                                     price=750.0, quantity=66.0, stop=700.0, target=820.0,
                                     buy_cost_inr=None, cost_config_hash="somehash")

    def test_open_without_cost_config_hash_is_rejected(self):
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.open_paper_trade(self.conn, trade_id="AXISBANK:1", decision_id=1, event_date="2021-10-28",
                                     price=750.0, quantity=66.0, stop=700.0, target=820.0,
                                     buy_cost_inr=59.37, cost_config_hash=None)

    def test_open_with_both_cost_fields_present_succeeds(self):
        jstore.open_paper_trade(self.conn, trade_id="AXISBANK:1", decision_id=1, event_date="2021-10-28",
                                 price=750.0, quantity=66.0, stop=700.0, target=820.0,
                                 buy_cost_inr=59.37, cost_config_hash="somehash")
        latest = jstore.latest_trade_event(self.conn, "AXISBANK:1")
        self.assertEqual(latest["buy_cost_inr"], 59.37)
        self.assertEqual(latest["cost_config_hash"], "somehash")

    # --- CLOSE requires sell_cost_inr and cost_config_hash -----------------------------------------

    def _open_a_position(self, trade_id: str = "AXISBANK:2"):
        jstore.open_paper_trade(self.conn, trade_id=trade_id, decision_id=1, event_date="2021-10-28",
                                 price=750.0, quantity=66.0, stop=700.0, target=820.0,
                                 buy_cost_inr=59.37, cost_config_hash="somehash")

    def test_close_without_sell_cost_inr_is_rejected(self):
        self._open_a_position()
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.close_paper_trade(self.conn, trade_id="AXISBANK:2", event_date="2021-10-29",
                                      price=760.0, reason="test", sell_cost_inr=None, cost_config_hash="somehash")

    def test_close_without_cost_config_hash_is_rejected(self):
        self._open_a_position()
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.close_paper_trade(self.conn, trade_id="AXISBANK:2", event_date="2021-10-29",
                                      price=760.0, reason="test", sell_cost_inr=67.21, cost_config_hash=None)

    def test_close_with_both_cost_fields_present_succeeds(self):
        self._open_a_position()
        jstore.close_paper_trade(self.conn, trade_id="AXISBANK:2", event_date="2021-10-29",
                                  price=760.0, reason="test", sell_cost_inr=67.21, cost_config_hash="somehash")
        latest = jstore.latest_trade_event(self.conn, "AXISBANK:2")
        self.assertEqual(latest["event_type"], "CLOSE")
        self.assertEqual(latest["sell_cost_inr"], 67.21)
        self.assertEqual(latest["cost_config_hash"], "somehash")

    # --- ANY row requires an integer quantity ------------------------------------------------------

    def test_open_with_a_fractional_quantity_is_rejected(self):
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.open_paper_trade(self.conn, trade_id="AXISBANK:3", decision_id=1, event_date="2021-10-28",
                                     price=750.0, quantity=66.5, stop=700.0, target=820.0,
                                     buy_cost_inr=59.37, cost_config_hash="somehash")

    def test_open_with_a_whole_number_quantity_stored_as_float_succeeds(self):
        """66.0 must NOT be rejected -- it's a whole number, just stored in a REAL column."""
        jstore.open_paper_trade(self.conn, trade_id="AXISBANK:4", decision_id=1, event_date="2021-10-28",
                                 price=750.0, quantity=66.0, stop=700.0, target=820.0,
                                 buy_cost_inr=59.37, cost_config_hash="somehash")
        self.assertEqual(jstore.latest_trade_event(self.conn, "AXISBANK:4")["quantity"], 66.0)

    def test_adjust_with_a_fractional_quantity_is_rejected(self):
        """The integer-quantity guard applies to every event type, not just OPEN -- an ADJUST row
        (e.g. from a corporate-action factor that doesn't divide evenly into a whole share) is
        rejected exactly the same way."""
        self._open_a_position(trade_id="AXISBANK:5")
        with self.assertRaises(sqlite3.DatabaseError):
            jstore.adjust_paper_trade(self.conn, trade_id="AXISBANK:5", event_date="2021-10-29",
                                       price=500.0, quantity=92.4, stop=466.67, target=546.67,
                                       reason="corporate action: 7:5 split")

    def test_close_quantity_is_always_zero_a_whole_number_and_never_rejected(self):
        """CLOSE always inserts quantity=0.0 (desk/journal/store.py) -- confirms the new integer
        guard doesn't interfere with that existing, always-whole-number contract."""
        self._open_a_position(trade_id="AXISBANK:6")
        jstore.close_paper_trade(self.conn, trade_id="AXISBANK:6", event_date="2021-10-29",
                                  price=760.0, reason="test", sell_cost_inr=67.21, cost_config_hash="somehash")
        self.assertEqual(jstore.latest_trade_event(self.conn, "AXISBANK:6")["quantity"], 0.0)


if __name__ == "__main__":
    unittest.main()
