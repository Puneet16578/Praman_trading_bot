"""Guard re-test against REAL ingested data (your instruction: fixture testing proves the
plumbing, not the guard against real-world messiness).

Requires `data/processed/praman.db` to already contain the real sample from
`scripts/ingest_bhavcopy_sample.py` -- skipped entirely (not faked, not fixture-substituted) if
that file doesn't exist, so this never silently passes against fixture data pretending to be real.

Honest scope, stated per CLAUDE.md's verification-honesty rule:
- Mid-series delisting: verified below, against a real symbol (ALBK -- Allahabad Bank, merged
  into Indian Bank in 2020) that is genuinely present in the earliest sample date and genuinely
  absent from the latest.
- Multiple series, same real date: verified below (DHFL alone has 9+ distinct NCD series on
  2019-10-01).
- Republished/corrected bhavcopy, real instance: NOT achieved. No naturally-occurring NSE
  correction was identified or available to this session (that would require either prior
  knowledge of a specific historical correction date, or waiting for one to occur during ongoing
  operation and re-fetching to detect it). The mechanism itself is proven in
  `test_nse_ingestion.py::test_corrected_republished_file_produces_new_row_with_later_knowledge_date`
  using a deliberately-modified copy of a real fetched file -- labeled honestly as an engineered
  second vintage, not a found one. DOCUMENTED, NOT VERIFIED against a genuine real correction.
- Corporate action with knowledge_date after event_date, real instance: BLOCKED. jugaad-data has
  no corporate-actions endpoint (discovered during this phase); no corporate_actions rows have
  been ingested yet. DOCUMENTED, NOT VERIFIED -- owed once corporate-actions ingestion exists.
"""
from __future__ import annotations
import unittest
from pathlib import Path

from src.bitemporal.connection import get_connection
from src.bitemporal.guard import latest_as_of, read_as_of
from src.config.settings import get_settings

_settings = get_settings()
_DB_EXISTS = Path(_settings.database_path).exists()

@unittest.skipUnless(_DB_EXISTS, f"Real ingested DB not found at {_settings.database_path} -- run scripts/ingest_bhavcopy_sample.py first.")
class RealDataGuardTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(_settings.database_path)

    def tearDown(self):
        self.conn.close()

    def test_mid_series_delisting_albk(self):
        """ALBK (Allahabad Bank) merged into Indian Bank in 2020 -- present in the 2019-10-01
        sample, absent from every later one. The guard must return its historical rows for any
        as-of after its own data ends, and must NOT return rows for a recent event_date."""
        all_time = read_as_of(self.conn, "bhavcopy", "2099-01-01", symbol="ALBK")
        self.assertGreater(len(all_time), 0, "ALBK must have real historical rows in the sample.")

        recent = read_as_of(self.conn, "bhavcopy", "2099-01-01", symbol="ALBK", event_date="2026-09-07")
        self.assertEqual(len(recent), 0, "ALBK must have no data on a recent trading date -- it stopped existing under this symbol.")

        before_it_stopped = latest_as_of(self.conn, "bhavcopy", "2020-06-01", symbol="ALBK")
        self.assertGreater(len(before_it_stopped), 0, "Historical ALBK data must remain queryable for an as-of within its trading history.")

    def test_multiple_series_same_real_date(self):
        """DHFL had many NCD/bond series trading under the same symbol on 2019-10-01 -- the
        business key (symbol, event_date, series) must keep these as distinct rows, not collide."""
        rows = read_as_of(self.conn, "bhavcopy", "2099-01-01", symbol="DHFL", event_date="2019-10-01")
        series_seen = {r["series"] for r in rows}
        self.assertGreater(len(series_seen), 1, f"Expected multiple distinct series for DHFL on 2019-10-01, got: {series_seen}")
        self.assertNotIn("nan", series_seen, "P2-004 regression: a blank SERIES must never appear as the literal string 'nan'.")

    def test_no_symbol_series_pair_has_duplicate_rows_for_one_knowledge_vintage(self):
        """Sanity check on the business key itself, against the full real dataset: no
        (symbol, event_date, series) should ever have more than one row at a single knowledge_date
        (that would mean the UNIQUE constraint was somehow bypassed)."""
        from collections import Counter
        all_rows = read_as_of(self.conn, "bhavcopy", "2099-01-01")
        keys = Counter((r["symbol"], r["event_date"], r["series"], r["knowledge_date"]) for r in all_rows)
        dupes = {k: c for k, c in keys.items() if c > 1}
        self.assertEqual(dupes, {}, f"Found duplicate (business key, knowledge_date) rows: {dupes}")

if __name__ == "__main__":
    unittest.main()
