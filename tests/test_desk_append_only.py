"""Acceptance test 1: UPDATE and DELETE on every desk table abort."""
from __future__ import annotations
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.connection import get_desk_connection
from desk.lib.schema import DESK_TABLES

SCRATCH_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_append_only.sqlite"

_SAMPLE_INSERT = {
    "circuit_bands": (
        "INSERT INTO circuit_bands (symbol,series,security_name,event_date,knowledge_date,recorded_at,"
        "band_kind,band_pct,remarks,source_url,source_sha256,published_at) VALUES "
        "('X','EQ','Fixture','2026-01-01','2026-01-01','2026-01-01T18:00:00+00:00',"
        "'FIXED',5,'-','fixture','hash','2026-01-01T17:30:00+05:30')"
    ),
    "decisions": (
        "INSERT INTO decisions (symbol, as_of_date, evidence_bundle_hash, gate_results, state, "
        "rulebook_version, rulebook_hash, cost_config_version, cost_config_hash, code_commit, "
        "praman_watermark, desk_watermark, as_of_is_live, recorded_at) VALUES "
        "('X','2026-01-01','h','{}','WATCH','v1','rh','v1','ch','sha','2026-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00',1,'2026-01-01T00:00:00+00:00')"
    ),
    "theses": (
        "INSERT INTO theses (symbol, evidence_cutoff, hypotheses, drivers, horizon, "
        "invalidation_conditions, planned_entry, planned_stop, planned_target, sector, paper_or_live, recorded_at) "
        "VALUES ('X','2026-01-01','[]','[]','2026-02-01','[]',100,90,120,'Financials','PAPER','2026-01-01T00:00:00+00:00')"
    ),
    "paper_trade_events": (
        "INSERT INTO paper_trade_events (trade_id, event_type, event_date, price, quantity, stop, target, reason, recorded_at, buy_cost_inr, cost_config_hash) "
        "VALUES ('X:1','OPEN','2026-01-01',100,10,90,120,'entry','2026-01-01T00:00:00+00:00',1.0,'test-costs')"
    ),
    "journal_events": (
        "INSERT INTO journal_events (event_type, detail, recorded_at) VALUES ('TEST','{}','2026-01-01T00:00:00+00:00')"
    ),
    "opportunities": (
        "INSERT INTO opportunities (symbol, as_of_date, inputs, state, recorded_at) "
        "VALUES ('X','2026-01-01','{}','WATCH','2026-01-01T00:00:00+00:00')"
    ),
    "monitor_runs": (
        "INSERT INTO monitor_runs (run_date, report, recorded_at) VALUES ('2026-01-01','{}','2026-01-01T00:00:00+00:00')"
    ),
}


class AppendOnlyTest(unittest.TestCase):
    def setUp(self):
        if SCRATCH_DB.exists():
            SCRATCH_DB.unlink()
        self.conn = get_desk_connection(SCRATCH_DB)

    def tearDown(self):
        self.conn.close()
        if SCRATCH_DB.exists():
            SCRATCH_DB.unlink()

    def _insert_one_row(self, table: str) -> None:
        """A row-level BEFORE UPDATE/DELETE trigger only fires per row it would touch -- an UPDATE/
        DELETE against a table with zero matching rows is a genuine no-op that never fires the
        trigger at all (nothing to abort), which is correct, not a gap: append-only integrity is
        about protecting an EXISTING row, not about every UPDATE/DELETE statement raising
        regardless of whether anything would be touched. So every table gets one real row first."""
        self.conn.execute(_SAMPLE_INSERT[table])

    def test_update_aborts_on_every_table(self):
        for table in DESK_TABLES:
            with self.subTest(table=table):
                self._insert_one_row(table)
                with self.assertRaises(sqlite3.DatabaseError, msg=f"UPDATE on {table} did not abort"):
                    self.conn.execute(f"UPDATE {table} SET recorded_at = recorded_at")

    def test_delete_aborts_on_every_table(self):
        for table in DESK_TABLES:
            with self.subTest(table=table):
                self._insert_one_row(table)
                with self.assertRaises(sqlite3.DatabaseError, msg=f"DELETE on {table} did not abort"):
                    self.conn.execute(f"DELETE FROM {table}")

    def test_insert_still_works(self):
        """The triggers must abort UPDATE/DELETE specifically -- not make the tables unusable."""
        self.conn.execute(
            "INSERT INTO journal_events (event_type, detail, recorded_at) VALUES ('TEST', '{}', '2026-01-01T00:00:00+00:00')"
        )
        row = self.conn.execute("SELECT COUNT(*) AS n FROM journal_events").fetchone()
        self.assertEqual(row["n"], 1)


if __name__ == "__main__":
    unittest.main()
