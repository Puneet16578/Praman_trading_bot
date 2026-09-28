"""Integrity fixes (a) and (b) from STOP 2 review:
(a) a paper fill occurs at the first session open AFTER `paper open`'s own recorded_at, never at a
    session whose own calendar day has already happened by wall-clock time even if the store hasn't
    ingested it yet; `paper open` refuses a stale decision (the store has moved past its as_of_date
    since assessment) and refuses a decision made with an explicit historical --as-of.
(b) `paper open` executes the APPROVED decision exactly as persisted (position_size from the
    decision record, stop/target from the linked thesis) -- it never calls run_assessment again.
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
from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.paper.open import PaperOpenRefused, PendingOpen, open_approved_decision

from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_PRAMAN_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_hindsight_praman.sqlite"
SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_hindsight_desk.sqlite"


def _utc(date_str: str, hour: int = 12) -> datetime:
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, hour, tzinfo=timezone.utc)


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class PaperOpenHindsightTest(unittest.TestCase):
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
        self.rulebook = make_test_rulebook()
        self.costs = make_test_costs()

        # Real AXISBANK trading calendar has more sessions after 2021-10-27 in the copied data --
        # confirm the two we need for the D+1/D+2 test exist, and note them.
        hist_days = self._trading_days_after("2021-10-27", n=3)
        self.d, self.d_plus_1, self.d_plus_2 = "2021-10-27", hist_days[0], hist_days[1]

    def _trading_days_after(self, after: str, n: int) -> list[str]:
        rows = self.scratch_praman.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date LIMIT ?",
            (after, n),
        ).fetchall()
        return [r["event_date"] for r in rows]

    def tearDown(self):
        self.scratch_praman.close()
        self.desk_conn.close()
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()

    def _make_eligible_decision(self, as_of_date: str, as_of_is_live: bool = True) -> int:
        thesis = dict(COMPLETE_AXISBANK_THESIS)
        result = run_assessment(self.scratch_praman, self.desk_conn, symbol="AXISBANK", as_of_date=as_of_date,
                                 sector="Financials", thesis=thesis, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "ELIGIBLE", f"gates: {result.gate_results}")
        thesis_id = jstore.record_thesis(self.desk_conn, symbol="AXISBANK", evidence_cutoff=as_of_date, **{
            k: v for k, v in thesis.items() if k != "thesis_id"
        })
        from desk.lib.store import max_recorded_at
        return jstore.record_decision(
            self.desk_conn, symbol="AXISBANK", as_of_date=as_of_date, thesis_id=thesis_id,
            isin_map_built_at=result.isin_map_built_at,
            evidence_bundle_hash=result.evidence_bundle.content_hash(), gate_results=result.gate_results_json(),
            state=result.state, rulebook_version="test", rulebook_hash="rb", cost_config_version="test",
            cost_config_hash="cc", code_commit="deadbeef", praman_watermark=max_recorded_at(self.scratch_praman),
            desk_watermark_value=jstore.desk_watermark(self.desk_conn), as_of_is_live=as_of_is_live,
            position_size=result.position_size,
            stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
        )

    def _open(self, decision_id: int, now: datetime):
        return open_approved_decision(self.scratch_praman, self.desk_conn, decision_id,
                                       costs=self.costs, cost_config_hash="test-cost-hash", now=now)

    def test_decision_opened_during_d_plus_1_fills_at_d_plus_2(self):
        """`now` falls on D+1's own calendar date -- D+1's own session has already "happened" by
        wall-clock time (even though the store, in this test, DOES already have its data, since we
        copied real history) -- the fill must skip to D+2, never D+1."""
        decision_id = self._make_eligible_decision(self.d)
        result = self._open(decision_id, now=_utc(self.d_plus_1))
        self.assertFalse(isinstance(result, PendingOpen), f"Expected a fill, got PENDING: {result}")
        self.assertEqual(result.event_date, self.d_plus_2)
        self.assertNotEqual(result.event_date, self.d_plus_1)

    def test_decision_opened_same_day_fills_at_d_plus_1(self):
        """Contrast case: opened the SAME calendar day as the decision (normal case) -- fills at
        the very next session, D+1, no skip needed."""
        decision_id = self._make_eligible_decision(self.d)
        result = self._open(decision_id, now=_utc(self.d))
        self.assertFalse(isinstance(result, PendingOpen))
        self.assertEqual(result.event_date, self.d_plus_1)

    def test_open_records_raw_price_and_a_separate_buy_side_cost(self):
        """Post-STOP-3-plus consistency fix: the recorded price is the store's raw price, never
        cost-adjusted -- the round-trip BUY-side cost lives in its own field, computed from the
        SAME active cost config whose hash is recorded alongside it."""
        from desk.risk.officer import round_trip_cost_inr

        decision_id = self._make_eligible_decision(self.d)
        result = self._open(decision_id, now=_utc(self.d))
        original_decision = jstore.get_decision(self.desk_conn, decision_id)
        trade_id = f"AXISBANK:{original_decision['thesis_id']}"
        latest = jstore.latest_trade_event(self.desk_conn, trade_id)

        self.assertEqual(latest["price"], result.price)  # raw -- identical to the Fill's own price
        expected_buy_cost = round_trip_cost_inr(result.price, latest["quantity"], self.costs, "buy")
        self.assertAlmostEqual(latest["buy_cost_inr"], expected_buy_cost, places=6)
        self.assertEqual(latest["cost_config_hash"], "test-cost-hash")
        self.assertIsNone(latest["sell_cost_inr"])

    def test_stale_decision_is_refused(self):
        """More than STALE_AFTER_DAYS calendar days have passed since the decision's as_of_date --
        refuse, don't silently open against outdated context."""
        from datetime import timedelta

        decision_id = self._make_eligible_decision(self.d)
        far_later = _utc(self.d) + timedelta(days=5)
        with self.assertRaises(PaperOpenRefused):
            self._open(decision_id, now=far_later)

    def test_explicit_historical_as_of_decision_is_refused(self):
        decision_id = self._make_eligible_decision(self.d, as_of_is_live=False)
        with self.assertRaises(PaperOpenRefused):
            self._open(decision_id, now=_utc(self.d))

    def test_open_uses_persisted_decision_never_reassesses(self):
        """Integrity fix (b): append rows to the store between assess and open (as if new
        disclosures/prices arrived), then confirm the opened trade's quantity/stop/target match the
        ORIGINAL decision record exactly, not a value a re-assessment against the changed store
        would produce."""
        decision_id = self._make_eligible_decision(self.d)
        original_decision = jstore.get_decision(self.desk_conn, decision_id)
        original_size = original_decision["position_size"]

        # Mutate the store after the decision (a later-recorded row for a date FAR from d/d+1/d+2,
        # so it cannot itself become the "latest available" and trip the staleness refusal).
        write_fact(self.scratch_praman, "bhavcopy", {
            "symbol": "AXISBANK", "event_date": "2010-01-04", "knowledge_date": "2010-01-04",
            "open_price": 100.0, "high_price": 101.0, "low_price": 99.0, "close_price": 100.5,
            "prev_close": 99.5, "traded_qty": 500000, "delivery_qty": 200000, "delivery_pct": 40.0,
            "series": "EQ", "source_file": "test",
        })

        result = self._open(decision_id, now=_utc(self.d))
        self.assertFalse(isinstance(result, PendingOpen))
        latest = jstore.latest_trade_event(self.desk_conn, f"AXISBANK:{original_decision['thesis_id']}")
        self.assertAlmostEqual(latest["quantity"], original_size)
        self.assertAlmostEqual(latest["stop"], COMPLETE_AXISBANK_THESIS["planned_stop"])
        self.assertAlmostEqual(latest["target"], COMPLETE_AXISBANK_THESIS["planned_target"])


if __name__ == "__main__":
    unittest.main()
