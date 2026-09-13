"""EX_DATE_FALLBACK's knowledge_date is a safe stand-in for price adjustment (an ex-date always
follows its announcement) but is NOT a real announcement date. A timing-sensitive signal must
never see these rows -- this asserts the dedicated accessor enforces that structurally, and that
the raw guard call (deliberately) does not, which is exactly why the dedicated accessor exists.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import latest_as_of
from src.bitemporal.store import write_fact
from src.ingestion.nse_market_data.corporate_actions import BONUS, CONFIRMED, EX_DATE_FALLBACK
from src.signals.corporate_action_timing import timing_reliable_corporate_actions

def make_action(symbol, event_date, knowledge_date, tier):
    return {
        "symbol": symbol, "action_type": BONUS, "event_date": event_date, "knowledge_date": knowledge_date,
        "ratio_numerator": 1.0, "ratio_denominator": 1.0, "confidence_tier": tier,
        "details": "fixture", "source_file": "fixture.json",
    }

class TimingReliableCorporateActionsTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "corporate_actions", make_action("TESTCO", "2025-03-01", "2025-01-20", CONFIRMED))
        write_fact(self.conn, "corporate_actions", make_action("OTHERCO", "2025-04-01", "2025-04-01", EX_DATE_FALLBACK))

    def test_dedicated_accessor_excludes_ex_date_fallback(self):
        confirmed_rows = timing_reliable_corporate_actions(self.conn, "TESTCO", "2099-01-01")
        fallback_rows = timing_reliable_corporate_actions(self.conn, "OTHERCO", "2099-01-01")
        self.assertEqual(len(confirmed_rows), 1)
        self.assertEqual(confirmed_rows[0]["confidence_tier"], CONFIRMED)
        self.assertEqual(fallback_rows, [], "A timing-based signal must never see an EX_DATE_FALLBACK row.")

    def test_raw_guard_call_does_not_filter_by_tier(self):
        # Demonstrates why the dedicated accessor is necessary: the raw guard alone returns both.
        raw_rows = latest_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="OTHERCO")
        self.assertEqual(len(raw_rows), 1)
        self.assertEqual(raw_rows[0]["confidence_tier"], EX_DATE_FALLBACK)

if __name__ == "__main__":
    unittest.main()
