"""Corporate-action knowledge-date-ordering guard test against REAL data -- owed since Phase 2
(bhavcopy's real-data guard tests existed; corporate_actions had none, because no real corporate-
action data existed until this session). Skipped, not faked, if the real sample DB is absent.

Honest scope: every real CONFIRMED/MATCHED_UNCONFIRMED row in this project's ingested sample has
knowledge_date BEFORE event_date (median 44 days, per the measured distribution) -- board
announcements precede ex-dates as a matter of regulatory process. The INVERSE ordering (knowledge_date
AFTER event_date -- a late/retroactively-announced action) has no real example in this dataset;
that specific case remains fixture-verified only
(tests/test_bitemporal_core.py::CorporateActionKnowledgeDateOrderingTest). What this file verifies
against real data is the same underlying mechanism -- the guard blocks on knowledge_date regardless
of event_date -- using the ordering that actually occurs in practice.
"""
from __future__ import annotations
import unittest
from pathlib import Path

from src.bitemporal.connection import get_connection
from src.bitemporal.guard import read_as_of
from src.config.settings import get_settings

_settings = get_settings()
_DB_EXISTS = Path(_settings.database_path).exists()

@unittest.skipUnless(_DB_EXISTS, f"Real ingested DB not found at {_settings.database_path} -- run scripts/ingest_corporate_actions_sample.py first.")
class RealCorporateActionGuardTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(_settings.database_path)

    def tearDown(self):
        self.conn.close()

    def test_bajfinance_actions_invisible_before_real_announcement_knowledge_date(self):
        """Real BAJFINANCE bonus 4:1 + split 2:1: announced 2025-04-29, ex-date 2025-06-16. An
        as-of query between the two real dates must not see them, even though 2025-04-29 has
        already passed relative to that as-of -- the guard must block on the row's OWN
        knowledge_date field, not on "did this generally happen a while ago"."""
        before = read_as_of(self.conn, "corporate_actions", "2025-03-01", symbol="BAJFINANCE")
        self.assertEqual(len(before), 0, "Must be invisible before the real announcement date.")

        after = read_as_of(self.conn, "corporate_actions", "2025-05-01", symbol="BAJFINANCE")
        self.assertEqual(len(after), 2, "Must be visible on/after the real announcement date (2025-04-29).")
        self.assertEqual({row["action_type"] for row in after}, {"BONUS", "SPLIT"})

    def test_quarantined_aurigrow_disagreement_never_reached_the_store(self):
        """AURIGROW's quarantined 2022-01-20 bonus (subject '1:1' vs announcement's erroneous
        '11104000:111040000', resolved against the real filed PDF -- see docs/phase3_corporate_actions.md)
        must not be queryable at any as-of, confirming QUARANTINE really means never written."""
        rows = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="AURIGROW", event_date="2022-01-20")
        self.assertEqual(len(rows), 0)

    def test_no_real_row_has_knowledge_date_after_event_date(self):
        """Documents the honest scope note above: in this real dataset, every writable row's
        knowledge_date precedes or equals its event_date. The inverse ordering is fixture-only."""
        all_rows = read_as_of(self.conn, "corporate_actions", "2099-01-01")
        inverted = [r for r in all_rows if r["knowledge_date"] > r["event_date"]]
        self.assertEqual(inverted, [], "If this ever fails, a real late-announced action exists -- update the scope note above, don't just widen the assertion.")

if __name__ == "__main__":
    unittest.main()
