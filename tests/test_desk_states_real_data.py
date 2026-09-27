"""Acceptance test 4: one test per decision state, on real data. Every example below was verified
directly against the real store before being written into this test (not assumed):
  - CAPTRUST/2026-08-05: real ASM_LT stage I as of this date -> VETO (G4). (A real BE-series stock
    was tried first, e.g. ZEELEARN/2026-08-31, and found to fail G2 (INSUFFICIENT) instead, because
    Praman's own get_disclosure_window() builds its own internal, EQ-only symbol history regardless
    of what this bundle's own extend_with_series does -- a real, pinned-code limitation, not a bug
    in the Desk, worth naming rather than silently switching examples without explanation.)
  - RELIANCE/2023-07-21: the real trading day immediately after the 2023-07-20 Jio Financial
    demerger -- the demerger is still inside G3's 60-session trailing window (confirmed:
    corporate_actions evidence cites break=True), while price/volume/delivery are themselves
    normally computable on THIS date (unlike 2023-07-20 itself, where return_1d is None) -> G1/G2
    PASS, G3 FAILs -> RESEARCH_REQUIRED.
  - AXISBANK/2021-10-27 with a complete thesis -> ELIGIBLE (all 8 gates PASS, real position size
    and stress loss computed).
  - The same event with an incomplete thesis -> WATCH (G8 fails, nothing else does).
  - A symbol/date with no bhavcopy at all -> INSUFFICIENT (G1 fails).
  - A thesis whose horizon has already lapsed with no trade ever opened -> EXPIRED.
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.connection import get_desk_connection
from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.gates.engine import run_assessment

from tests.desk_fixtures import COMPLETE_AXISBANK_THESIS, make_test_costs, make_test_rulebook

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_states_real_data.sqlite"


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class DecisionStateRealDataTest(unittest.TestCase):
    def setUp(self):
        if SCRATCH_DESK_DB.exists():
            SCRATCH_DESK_DB.unlink()
        self.praman_conn = get_live_connection()
        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)
        self.rulebook = make_test_rulebook()
        self.costs = make_test_costs()

    def tearDown(self):
        self.praman_conn.close()
        self.desk_conn.close()
        if SCRATCH_DESK_DB.exists():
            SCRATCH_DESK_DB.unlink()

    def test_asm_flagged_stock_is_vetoed(self):
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="CAPTRUST", as_of_date="2026-08-05",
                                 sector="Test", thesis=None, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "VETO")
        self.assertEqual(result.gate_results["G1"].result, "PASS")
        self.assertEqual(result.gate_results["G2"].result, "PASS")
        self.assertEqual(result.gate_results["G4"].result, "FAIL")
        self.assertIn("ASM", result.gate_results["G4"].reasons[0])

    def test_reliance_day_after_demerger_is_research_required(self):
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="RELIANCE", as_of_date="2023-07-21",
                                 sector="Energy", thesis=None, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "RESEARCH_REQUIRED")
        self.assertEqual(result.gate_results["G1"].result, "PASS")
        self.assertEqual(result.gate_results["G2"].result, "PASS")
        self.assertEqual(result.gate_results["G3"].result, "FAIL")
        self.assertIn("DEMERGER", result.gate_results["G3"].reasons[0])

    def test_clean_liquid_large_cap_with_complete_thesis_is_eligible(self):
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="AXISBANK", as_of_date="2021-10-27",
                                 sector="Financials", thesis=dict(COMPLETE_AXISBANK_THESIS),
                                 rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "ELIGIBLE")
        for gate, r in result.gate_results.items():
            self.assertEqual(r.result, "PASS", f"{gate} unexpectedly {r.result}: {r.reasons}")
        self.assertIsNotNone(result.position_size)
        self.assertGreater(result.position_size, 0)
        self.assertIsNotNone(result.stress_loss)

    def test_same_event_with_incomplete_thesis_is_watch(self):
        incomplete = dict(COMPLETE_AXISBANK_THESIS)
        del incomplete["invalidation_conditions"]  # required by G8
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="AXISBANK", as_of_date="2021-10-27",
                                 sector="Financials", thesis=incomplete, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "WATCH")
        self.assertEqual(result.gate_results["G8"].result, "FAIL")
        for gate in ("G1", "G2", "G3", "G4", "G5", "G6", "G7"):
            self.assertEqual(result.gate_results[gate].result, "PASS", f"{gate}: {result.gate_results[gate].reasons}")

    def test_symbol_with_no_bhavcopy_at_all_is_insufficient(self):
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="THISSYMBOLDOESNOTEXIST",
                                 as_of_date="2026-01-05", sector=None, thesis=None,
                                 rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "INSUFFICIENT")
        self.assertEqual(result.gate_results["G1"].result, "FAIL")


class AllGatesRunEveryTimeTest(DecisionStateRealDataTest):
    """Instruction 4: no short-circuit -- every gate is recorded on every assessment, even when an
    earlier one in priority order already determines the final state."""

    def test_insufficient_case_still_records_all_eight_gates(self):
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="THISSYMBOLDOESNOTEXIST",
                                 as_of_date="2026-01-05", sector=None, thesis=None,
                                 rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "INSUFFICIENT")
        self.assertEqual(set(result.gate_results.keys()), {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"})

    def test_veto_case_still_records_g1_through_g3_and_g7_g8(self):
        """CAPTRUST is VETOed by G4 -- confirms G1-G3 and G7-G8 are ALSO recorded, not skipped just
        because G4 already determines VETO. G5/G6 are UNKNOWN here (no thesis), which is itself a
        recorded result, not an absence."""
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="CAPTRUST", as_of_date="2026-08-05",
                                 sector="Test", thesis=None, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "VETO")
        self.assertEqual(set(result.gate_results.keys()), {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"})
        self.assertEqual(result.gate_results["G1"].result, "PASS")
        self.assertEqual(result.gate_results["G3"].result, "PASS")
        self.assertEqual(result.gate_results["G8"].result, "FAIL")  # no thesis supplied -- still evaluated and recorded

    def test_lapsed_thesis_horizon_with_no_trade_is_expired(self):
        lapsed = dict(COMPLETE_AXISBANK_THESIS)
        lapsed["horizon"] = "2021-10-28"  # the very next day -- as_of_date below is well past it
        lapsed["thesis_id"] = 999999  # no trade_id in paper_trade_events references this
        result = run_assessment(self.praman_conn, self.desk_conn, symbol="AXISBANK", as_of_date="2021-11-15",
                                 sector="Financials", thesis=lapsed, rulebook=self.rulebook, costs=self.costs)
        self.assertEqual(result.state, "EXPIRED")


if __name__ == "__main__":
    unittest.main()
