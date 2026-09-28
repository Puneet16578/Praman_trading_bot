"""Manual-close hindsight fix (post-STOP-3-plus review): `desk paper close` used to take --price and
--event-date directly from the human -- the exact same hindsight loophole already closed for entries
(any exit price could be recorded on any past date). Now, mirroring desk/paper/open.py exactly:
(a) there is no price/event_date parameter anywhere -- the CLI parser itself rejects both flags;
(b) the fill occurs at the first session open AFTER the close command's own recorded_at, net of the
    real round-trip sell-side cost from the active cost config;
(c) if that session's data isn't in the store yet, the close is PENDING with its fill date frozen,
    and `desk monitor` completes it automatically later, at that SAME frozen date.
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
from desk.monitor import complete_pending_paper_closes
from desk.paper.close import PaperCloseRefused, PendingClose, close_approved_trade
from desk.risk.officer import round_trip_cost_inr

from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, copy_symbol_rows, make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_PRAMAN_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_close_hindsight_praman.sqlite"
SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_close_hindsight_desk.sqlite"


def _utc(date_str: str, hour: int = 12) -> datetime:
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, hour, tzinfo=timezone.utc)


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class PaperCloseHindsightTest(unittest.TestCase):
    def setUp(self):
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()
        prod = get_live_connection()
        self.scratch_praman = get_connection(str(SCRATCH_PRAMAN_DB))
        self.addCleanup(self.scratch_praman.close)
        init_db(self.scratch_praman)
        copy_symbol_rows(prod, self.scratch_praman, "AXISBANK")
        prod.close()
        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)
        self.addCleanup(self.desk_conn.close)
        self.costs = make_test_costs()

        hist_days = self._trading_days_after("2021-10-27", n=3)
        self.d, self.d_plus_1, self.d_plus_2 = "2021-10-27", hist_days[0], hist_days[1]

        # Seed an already-OPEN position directly -- what desk paper open produced is not what this
        # file is testing; only the CLOSE side is.
        rulebook = make_test_rulebook()
        thesis = dict(COMPLETE_AXISBANK_THESIS)
        result = run_assessment(self.scratch_praman, self.desk_conn, symbol="AXISBANK", as_of_date=self.d,
                                 sector="Financials", thesis=thesis, rulebook=rulebook, costs=self.costs)
        self.assertEqual(result.state, "ELIGIBLE")
        self.thesis_id = jstore.record_thesis(self.desk_conn, symbol="AXISBANK", evidence_cutoff=self.d, **{
            k: v for k, v in thesis.items() if k != "thesis_id"
        })
        decision_id = jstore.record_decision(
            self.desk_conn, symbol="AXISBANK", as_of_date=self.d, thesis_id=self.thesis_id,
            evidence_bundle_hash=result.evidence_bundle.content_hash(), gate_results=result.gate_results_json(),
            state=result.state, rulebook_version="test", rulebook_hash="rb", cost_config_version="test",
            cost_config_hash="cc", code_commit="deadbeef", praman_watermark=max_recorded_at(self.scratch_praman),
            desk_watermark_value=jstore.desk_watermark(self.desk_conn), as_of_is_live=True,
            position_size=result.position_size,
            stress_loss_inr=result.stress_loss.stress_loss_inr if result.stress_loss else None,
        )
        self.quantity = result.position_size
        self.trade_id = f"AXISBANK:{self.thesis_id}"
        jstore.open_paper_trade(self.desk_conn, trade_id=self.trade_id, decision_id=decision_id,
                                 event_date=self.d_plus_1, price=750.0, quantity=self.quantity,
                                 stop=700.0, target=820.0,
                                 buy_cost_inr=round_trip_cost_inr(750.0, self.quantity, self.costs, "buy"),
                                 cost_config_hash="test-cost-hash")

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

    def _close(self, trade_id, reason, now):
        return close_approved_trade(self.scratch_praman, self.desk_conn, trade_id, reason=reason,
                                     costs=self.costs, cost_config_hash="test-cost-hash", now=now)

    def test_close_issued_same_day_fills_at_d_plus_1_no_skip(self):
        result = self._close(self.trade_id, "test exit", now=_utc(self.d))
        self.assertFalse(isinstance(result, PendingClose), f"Expected a fill, got PENDING: {result}")
        self.assertEqual(result.event_date, self.d_plus_1)

    def test_close_issued_after_d_plus_1_open_fills_at_d_plus_2_open(self):
        """`now` falls on D+1's own calendar date -- D+1's own session has already "happened" by
        wall-clock time -- the fill must skip to D+2, never D+1, exactly like the entry-side fix."""
        result = self._close(self.trade_id, "test exit", now=_utc(self.d_plus_1))
        self.assertFalse(isinstance(result, PendingClose), f"Expected a fill, got PENDING: {result}")
        self.assertEqual(result.event_date, self.d_plus_2)
        self.assertNotEqual(result.event_date, self.d_plus_1)

    def test_close_records_raw_price_and_a_separate_sell_side_cost(self):
        """Post-STOP-3-plus consistency fix: the recorded price is the store's raw price, NOT net
        of cost -- the round-trip SELL-side cost (including the DP charge) lives in its own field,
        computed from the SAME active cost config whose hash is recorded alongside it."""
        result = self._close(self.trade_id, "test exit", now=_utc(self.d))
        from src.signals.event_catalogue import build_symbol_history
        hist = build_symbol_history(self.scratch_praman, "AXISBANK")
        row = hist.price_row_as_of(self.d_plus_1, self.d_plus_1)
        gross_price = row["open_price"] * hist.cum_factor_up_to(self.d_plus_1)
        expected_cost = round_trip_cost_inr(gross_price, self.quantity, self.costs, "sell")

        self.assertAlmostEqual(result.price, gross_price, places=6)  # raw -- NOT net of cost anymore

        latest = jstore.latest_trade_event(self.desk_conn, self.trade_id)
        self.assertEqual(latest["price"], result.price)
        self.assertAlmostEqual(latest["sell_cost_inr"], expected_cost, places=6)
        self.assertEqual(latest["cost_config_hash"], "test-cost-hash")
        self.assertIsNone(latest["buy_cost_inr"])

    def test_reason_is_mandatory(self):
        with self.assertRaises(PaperCloseRefused):
            self._close(self.trade_id, "", now=_utc(self.d))

    def test_closing_an_already_closed_trade_is_refused(self):
        self._close(self.trade_id, "first close", now=_utc(self.d))
        with self.assertRaises(PaperCloseRefused):
            self._close(self.trade_id, "second close attempt", now=_utc(self.d))

    def test_closing_an_unknown_trade_id_is_refused(self):
        with self.assertRaises(PaperCloseRefused):
            self._close("NOSUCHTRADE:999", "test", now=_utc(self.d))


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class MonitorCompletesPendingCloseTest(unittest.TestCase):
    def setUp(self):
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()
        self.d = "2021-10-27"
        prod = get_live_connection()
        self.d_plus_1 = prod.execute(
            "SELECT event_date FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date LIMIT 1",
            (self.d,),
        ).fetchone()["event_date"]
        self.d_plus_2_row = dict(prod.execute(
            "SELECT * FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date LIMIT 1",
            (self.d_plus_1,),
        ).fetchone())
        self.d_plus_2 = self.d_plus_2_row["event_date"]
        self.d_plus_2_row.pop("row_id", None)
        self.d_plus_2_row.pop("recorded_at", None)

        self.scratch_praman = get_connection(str(SCRATCH_PRAMAN_DB))
        self.addCleanup(self.scratch_praman.close)
        init_db(self.scratch_praman)
        # Only through D+1 -- D+2 deliberately does not exist in this store yet.
        copy_symbol_rows(prod, self.scratch_praman, "AXISBANK", through_event_date=self.d_plus_1)
        prod.close()

        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)
        self.addCleanup(self.desk_conn.close)
        self.costs = make_test_costs()
        self.trade_id = "AXISBANK:1"
        jstore.open_paper_trade(self.desk_conn, trade_id=self.trade_id, decision_id=None,
                                 event_date=self.d_plus_1, price=750.0, quantity=66.0,
                                 stop=700.0, target=820.0,
                                 buy_cost_inr=round_trip_cost_inr(750.0, 66.0, self.costs, "buy"),
                                 cost_config_hash="test-cost-hash")

    def tearDown(self):
        self.scratch_praman.close()
        self.desk_conn.close()
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()

    def test_pending_close_is_completed_by_the_monitor_once_ingested(self):
        # Issued on D+1 -- the target session (first strictly after D+1) isn't in the store yet.
        result = close_approved_trade(self.scratch_praman, self.desk_conn, self.trade_id,
                                       reason="evidence invalidated", costs=self.costs,
                                       cost_config_hash="test-cost-hash", now=_utc(self.d_plus_1))
        self.assertIsInstance(result, PendingClose)
        self.assertEqual(result.not_before_date, self.d_plus_1)

        # What `desk paper close` would log on PENDING -- reproduced directly since this test
        # exercises desk/monitor.py, not desk/cli.py.
        jstore.record_journal_event(self.desk_conn, event_type="PAPER_CLOSE_PENDING", trade_id=self.trade_id,
                                     detail={"not_before_date": result.not_before_date, "reason": result.reason})

        still_pending = complete_pending_paper_closes(self.scratch_praman, self.desk_conn)
        self.assertEqual(still_pending, [])
        self.assertEqual(jstore.latest_trade_event(self.desk_conn, self.trade_id)["event_type"], "OPEN")

        # "Ingest" D+2 -- a real write_fact of its own real row.
        write_fact(self.scratch_praman, "bhavcopy", self.d_plus_2_row)

        completed = complete_pending_paper_closes(self.scratch_praman, self.desk_conn)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["status"], "FILLED")
        self.assertEqual(completed[0]["event_date"], self.d_plus_2)

        latest = jstore.latest_trade_event(self.desk_conn, self.trade_id)
        self.assertEqual(latest["event_type"], "CLOSE")
        self.assertEqual(latest["event_date"], self.d_plus_2)

        # Resolved -- a second monitor pass must not try it again.
        self.assertEqual(jstore.pending_paper_closes(self.desk_conn), [])
        self.assertEqual(complete_pending_paper_closes(self.scratch_praman, self.desk_conn), [])


class PaperCloseCliRejectsPriceAndDateTest(unittest.TestCase):
    """No store access needed -- argparse itself refuses an unrecognized flag before any command
    function runs, so this runs unconditionally."""

    def test_price_flag_is_rejected(self):
        from desk.cli import main
        with self.assertRaises(SystemExit):
            main(["paper", "close", "AXISBANK:1", "--price", "750", "--reason", "x"])

    def test_event_date_flag_is_rejected(self):
        from desk.cli import main
        with self.assertRaises(SystemExit):
            main(["paper", "close", "AXISBANK:1", "--event-date", "2021-10-27", "--reason", "x"])

    def test_reason_is_still_required_by_the_parser(self):
        from desk.cli import main
        with self.assertRaises(SystemExit):
            main(["paper", "close", "AXISBANK:1"])


if __name__ == "__main__":
    unittest.main()
