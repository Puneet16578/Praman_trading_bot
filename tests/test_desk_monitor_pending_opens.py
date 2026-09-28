"""Fix 2c (post-STOP-3 review): `desk monitor` completes a paper entry a prior `desk paper open` left
PENDING, once the target session's real data has been ingested -- no manual re-run required. NOT a
new autonomous decision: the human already approved opening this exact decision (the original
`paper open` call recorded a PAPER_OPEN_PENDING journal event); this only finishes a fill blocked
purely by Praman's own ingestion lag.

Real AXISBANK data throughout: the scratch Praman store is seeded with real rows ONLY THROUGH the
decision's own as_of_date (2021-10-27), via copy_symbol_rows's new `through_event_date` filter -- so
the very next real trading day genuinely does not exist in the store yet, exactly like a real
same-day evening `paper open` before the next session has been ingested. "Ingesting" that next day is
then a real write_fact of that date's own REAL row (fetched from production), not a fabricated one.
"""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_fact

from desk.gates.engine import run_assessment
from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.store import ProductionStoreMissingError, get_live_connection, max_recorded_at
from desk.monitor import complete_pending_paper_opens
from desk.paper.open import PendingOpen, open_approved_decision

from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_PRAMAN_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_pending_opens_praman.sqlite"
SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_pending_opens_desk.sqlite"


def _utc(date_str: str, hour: int = 12) -> datetime:
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, hour, tzinfo=timezone.utc)


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class MonitorCompletesPendingOpenTest(unittest.TestCase):
    def setUp(self):
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()
        self.d = "2021-10-27"
        prod = get_live_connection()
        self.d_plus_1_row = dict(prod.execute(
            "SELECT * FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date LIMIT 1",
            (self.d,),
        ).fetchone())
        self.d_plus_1 = self.d_plus_1_row["event_date"]
        self.d_plus_1_row.pop("row_id", None)
        self.d_plus_1_row.pop("recorded_at", None)

        self.scratch_praman = get_connection(str(SCRATCH_PRAMAN_DB))
        init_db(self.scratch_praman)
        # Only through `self.d` -- self.d_plus_1 deliberately does NOT exist in this store yet.
        copy_symbol_rows(prod, self.scratch_praman, "AXISBANK", through_event_date=self.d)
        prod.close()

        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)
        self.rulebook = make_test_rulebook()
        self.costs = make_test_costs()

    def tearDown(self):
        self.scratch_praman.close()
        self.desk_conn.close()
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()

    def test_open_on_d_ingest_d_plus_1_monitor_fills_at_d_plus_1_open(self):
        thesis = dict(COMPLETE_AXISBANK_THESIS)
        result = run_assessment(self.scratch_praman, self.desk_conn, symbol="AXISBANK", as_of_date=self.d,
                                 sector="Financials", thesis=thesis, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "ELIGIBLE", f"gates: {result.gate_results}")

        thesis_id = jstore.record_thesis(self.desk_conn, symbol="AXISBANK", evidence_cutoff=self.d, **{
            k: v for k, v in thesis.items() if k != "thesis_id"
        })
        decision_id = jstore.record_decision(
            self.desk_conn, symbol="AXISBANK", as_of_date=self.d, thesis_id=thesis_id,
            evidence_bundle_hash=result.evidence_bundle.content_hash(), gate_results=result.gate_results_json(),
            state=result.state, rulebook_version="test", rulebook_hash="rb", cost_config_version="test",
            cost_config_hash="cc", code_commit="deadbeef", praman_watermark=max_recorded_at(self.scratch_praman),
            desk_watermark_value=jstore.desk_watermark(self.desk_conn), as_of_is_live=True,
            position_size=result.position_size,
            stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
        )

        # Step 1: "open on D" -- self.d_plus_1 isn't in the store yet, so this must come back PENDING.
        open_result = open_approved_decision(self.scratch_praman, self.desk_conn, decision_id,
                                              costs=self.costs, cost_config_hash="test-cost-hash", now=_utc(self.d))
        self.assertIsInstance(open_result, PendingOpen)
        self.assertEqual(open_result.not_before_date, self.d)

        # `desk paper open` would log exactly this journal event on a PENDING result -- reproduced
        # directly here since this test exercises desk/monitor.py, not desk/cli.py.
        jstore.record_journal_event(self.desk_conn, event_type="PAPER_OPEN_PENDING", decision_id=decision_id,
                                     detail={"not_before_date": open_result.not_before_date})

        # A monitor run BEFORE ingestion must find it still pending -- no fill, no error, no noise.
        still_pending = complete_pending_paper_opens(self.scratch_praman, self.desk_conn)
        self.assertEqual(still_pending, [])
        self.assertEqual(jstore.open_trade_ids(self.desk_conn), [])

        # Step 2: "ingest D+1" -- a real write_fact of D+1's own REAL row (fetched from production).
        write_fact(self.scratch_praman, "bhavcopy", self.d_plus_1_row)

        # Step 3: "monitor fills at D+1's open" -- no `now` re-derivation, no re-approval.
        completed = complete_pending_paper_opens(self.scratch_praman, self.desk_conn)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["status"], "FILLED")
        self.assertEqual(completed[0]["decision_id"], decision_id)
        self.assertEqual(completed[0]["event_date"], self.d_plus_1)

        trade_id = f"AXISBANK:{thesis_id}"
        self.assertEqual(jstore.open_trade_ids(self.desk_conn), [trade_id])
        opened = jstore.latest_trade_event(self.desk_conn, trade_id)
        self.assertEqual(opened["event_type"], "OPEN")
        self.assertEqual(opened["event_date"], self.d_plus_1)

        # Resolved -- a second monitor pass must not try (or refuse) it again.
        self.assertEqual(jstore.pending_paper_opens(self.desk_conn), [])
        self.assertEqual(complete_pending_paper_opens(self.scratch_praman, self.desk_conn), [])


if __name__ == "__main__":
    unittest.main()
