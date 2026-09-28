"""Acceptance test 7: record a decision, append later-recorded rows to a COPY of the store, replay,
and get an identical record.

Builds a small scratch Praman-schema store (via Praman's own get_connection/init_db/write_facts --
real functions, not a reimplementation) seeded with AXISBANK's REAL historical rows copied from
production, so build_symbol_history/get_disclosure_window/etc. all see real, working data. Runs one
assessment against it (capturing the watermark), appends a new row afterward (which naturally gets
a LATER recorded_at, since the store's own _now() stamps wall-clock time), then replays the original
decision and confirms the appended row is invisible to the replay -- the TEMP-VIEW-shadowing
approach (desk/lib/store.py) applied to this scratch copy, exactly as it would be to production.
"""
from __future__ import annotations
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db

from desk.evidence.bundle import assemble_evidence_bundle
from desk.gates.engine import run_assessment
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.store import ProductionStoreMissingError, get_live_connection, max_recorded_at

from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_PRAMAN_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_replay_praman.sqlite"
SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_replay_desk.sqlite"


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class ReplayMatchesOriginalDecisionTest(unittest.TestCase):
    def setUp(self):
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()
        prod = get_live_connection()
        self.scratch_praman = get_connection(str(SCRATCH_PRAMAN_DB))
        init_db(self.scratch_praman)
        copy_symbol_rows(prod, self.scratch_praman, "AXISBANK")
        prod.close()
        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)

    def tearDown(self):
        self.scratch_praman.close()
        self.desk_conn.close()
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()

    def test_replay_after_appending_later_rows_matches_the_original_decision(self):
        rulebook = make_test_rulebook()
        costs = make_test_costs()
        thesis = dict(COMPLETE_AXISBANK_THESIS)

        result = run_assessment(self.scratch_praman, self.desk_conn, symbol="AXISBANK", as_of_date="2021-10-27",
                                 sector="Financials", thesis=thesis, rulebook=rulebook, costs=costs)
        self.assertEqual(result.state, "ELIGIBLE")

        praman_watermark = max_recorded_at(self.scratch_praman)
        thesis_id = jstore.record_thesis(self.desk_conn, symbol="AXISBANK", evidence_cutoff="2021-10-27", **{
            k: v for k, v in thesis.items() if k not in ("thesis_id",)
        })
        decision_id = jstore.record_decision(
            self.desk_conn, symbol="AXISBANK", as_of_date="2021-10-27", thesis_id=thesis_id,
            isin_map_built_at=result.isin_map_built_at,
            evidence_bundle_hash=result.evidence_bundle.content_hash(), gate_results=result.gate_results_json(),
            state=result.state, rulebook_version="test", rulebook_hash="test-rb-hash",
            cost_config_version="test", cost_config_hash="test-cost-hash",
            code_commit=_git_head(), praman_watermark=praman_watermark,
            desk_watermark_value=jstore.desk_watermark(self.desk_conn),
            as_of_is_live=result.as_of_is_live, position_size=result.position_size,
            stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
        )

        # Append a row that arrives AFTER the decision -- a new bhavcopy row for the SAME symbol on
        # a date guaranteed not to collide with any real copied row, which naturally gets a later
        # recorded_at (the store's own _now()).
        from src.bitemporal.store import write_fact
        write_fact(self.scratch_praman, "bhavcopy", {
            "symbol": "AXISBANK", "event_date": "2099-01-01", "knowledge_date": "2099-01-01",
            "open_price": 750.0, "high_price": 760.0, "low_price": 745.0, "close_price": 755.0,
            "prev_close": 748.0, "traded_qty": 1000000, "delivery_qty": 400000, "delivery_pct": 40.0,
            "series": "EQ", "source_file": "test",
        })

        from desk.replay import replay_decision
        self.assertEqual(jstore.get_decision(self.desk_conn, decision_id)["isin_map_built_at"],
                         result.isin_map_built_at)
        with patch("shared.isin_map_metadata.read_metadata",
                   side_effect=AssertionError("Replay must never read the current companion")):
            replayed = replay_decision(decision_id, desk_db_path=SCRATCH_DESK_DB,
                                        rulebook_override=rulebook, costs_override=costs)

        self.assertTrue(replayed.matched, f"Replay diverged: {replayed.diff}")
        self.assertEqual(replayed.replayed_state, "ELIGIBLE")
        self.assertEqual(replayed.original_state, replayed.replayed_state)


def _git_head() -> str:
    import subprocess
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
                           capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    unittest.main()
