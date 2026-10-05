"""Fixture tests for MultiAgentOrchestrator -- the full Supervisor -> specialists -> Adversary ->
Synthesis pipeline, against a small in-memory store built by hand (not the real database; see
tests/test_orchestrator_real_data_guard.py for that). Covers the two acceptance criteria that are
meaningless to check against real data alone: (1) the pipeline runs and produces a complete,
banned-term-clean report with NO LLM provider anywhere in the path, and (2) running the identical
event twice produces byte-identical report structure (determinism)."""
from __future__ import annotations
import unittest

from src.agent.banned_terms import lint_text
from src.agent.budgets import BudgetConfig
from src.agent.orchestrator import MultiAgentOrchestrator
from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_facts

SYMBOL = "FIXCO"

def _seed_bhavcopy(conn, n_days: int = 90):
    rows = []
    import datetime
    d = datetime.date(2024, 1, 2)
    price = 100.0
    for i in range(n_days):
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        event_date = d.isoformat()
        close = price + (i % 7) * 0.5
        rows.append({
            "symbol": SYMBOL, "event_date": event_date, "knowledge_date": event_date,
            "open_price": close - 1, "high_price": close + 1, "low_price": close - 2,
            "close_price": close, "prev_close": close - 0.5,
            "traded_qty": 100000 + (i * 137 % 5000), "delivery_qty": 40000, "delivery_pct": 40.0,
            "series": "EQ", "source_file": "fixture",
        })
        d += datetime.timedelta(days=1)
    write_facts(conn, "bhavcopy", rows)
    return [r["event_date"] for r in rows]

def _seed_announcement(conn, event_date: str, category: str = "Outcome of Board Meeting"):
    write_facts(conn, "corporate_announcements", [{
        "symbol": SYMBOL, "event_date": event_date, "knowledge_date": event_date,
        "seq_id": f"SEQ-{event_date}", "category": category, "description": "fixture announcement",
        "sort_timestamp": f"{event_date} 09:00:00", "source_file": "fixture",
        "isin": None, "reported_symbol": SYMBOL, "identity_date": None,
        "identity_status": "LEGACY_UNVERIFIED", "raw_json": None,
    }])

class OrchestratorFixtureTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        self.days = _seed_bhavcopy(self.conn)
        self.event_date = self.days[70]  # well past the 60-session trailing window
        self.orchestrator = MultiAgentOrchestrator()

    def test_report_has_all_five_agents_and_no_llm_provider_anywhere(self):
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        for role in ("MARKET_MICROSTRUCTURE", "DISCLOSURE", "SURVEILLANCE", "ADVERSARY", "SYNTHESIS"):
            self.assertIn(role, report.agents_used)
        self.assertIn(report.classification, (
            "GROUNDED", "PARTIALLY_GROUNDED", "UNEXPLAINED", "UNEXPLAINED_ISOLATED", "UNEXPLAINED_UNKNOWN_COVERAGE",
        ))

    def test_every_accepted_claim_states_which_verification_it_received(self):
        _seed_announcement(self.conn, self.days[65])
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertTrue(report.accepted_claims)
        for claim in report.accepted_claims:
            self.assertIn("verification", claim)
            self.assertIn("transcription", claim["verification"])
            self.assertIn("derivation", claim["verification"])
            self.assertIn(claim["verification"]["transcription"], ("PASS", "NOT_APPLICABLE"))
            self.assertIn(claim["verification"]["derivation"], ("PASS", "NOT_APPLICABLE", "NOT_SAMPLED"))

    def test_discriminative_power_note_present_on_every_report(self):
        # The original 0.611-0.70 ceiling this note used to cite is WITHDRAWN (P8-001,
        # docs/DEFECT_REGISTER.md) -- asserting the corrected citation is present and the
        # withdrawn number is absent, so a future accidental revert is caught.
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertIn("P8-001", report.discriminative_power_note)
        self.assertNotIn("0.611", report.discriminative_power_note)

    def test_report_is_banned_term_clean(self):
        _seed_announcement(self.conn, self.days[65])
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        for claim in report.accepted_claims:
            violations = lint_text(claim["text"])
            self.assertEqual(violations, [], f"Banned-term violation in report output: {claim}")
        self.assertEqual(lint_text(report.provenance_note), [])

    def test_no_coverage_produces_unknown_coverage_gap(self):
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertEqual(report.disclosure_tier, "UNKNOWN_COVERAGE")
        self.assertEqual(report.classification, "UNEXPLAINED_UNKNOWN_COVERAGE")
        self.assertTrue(any("no cached announcement data" in g.lower() for g in report.gaps))

    def test_substantive_disclosure_yields_grounded(self):
        _seed_announcement(self.conn, self.days[65], category="Outcome of Board Meeting")
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertEqual(report.disclosure_tier, "SUBSTANTIVE")
        self.assertEqual(report.classification, "GROUNDED")

    def test_no_claims_rejected_on_clean_fixture_data(self):
        _seed_announcement(self.conn, self.days[65])
        report = self.orchestrator.run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertEqual(report.rejected_claims, [])
        # NOT_APPLICABLE (no derivation implemented for this claim type) and NOT_SAMPLED (outside
        # the seeded ~20% sample) are legitimate non-failure verdicts, not rejections -- only FAIL
        # indicates a real problem.
        self.assertFalse(any(f["verdict"] == "FAIL" for f in report.adversary_findings))

class OrchestratorBudgetIsolationTest(unittest.TestCase):
    """Regression test for a real bug found via the real-data guard test
    (tests/test_orchestrator_real_data_guard.py): a shared BudgetTracker across multiple
    run_for_event() calls on one orchestrator instance silently starved later reports' tool
    calls, causing the Disclosure agent to error out and the report to misclassify (a real event
    with a substantive disclosure was reported as if it had none). Fixed by allocating a fresh
    budget per call -- see orchestrator.py's class docstring."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        self.days = _seed_bhavcopy(self.conn)
        _seed_announcement(self.conn, self.days[65])

    def test_many_reports_from_one_orchestrator_each_get_a_full_budget(self):
        orchestrator = MultiAgentOrchestrator()
        results = [orchestrator.run_for_event(self.conn, SYMBOL, self.days[70]) for _ in range(5)]
        for report in results:
            self.assertEqual(report.classification, "GROUNDED")
            self.assertEqual(report.rejected_claims, [])
            # FIXCO is a synthetic fixture symbol, not in the real catalogue -- this gap is
            # expected (cap-band/co-movement reference data genuinely doesn't exist for it), and
            # must appear identically on every one of the 5 calls, not degrade after the first.
            self.assertEqual(report.gaps, ["This event is not in this project's catalogue -- cap-band and co-movement context are unavailable."])

    def test_a_genuinely_exhausted_single_report_budget_surfaces_as_unknown_coverage_not_silent_misclassification(self):
        """With only 1 total tool call allowed, Market Microstructure succeeds and Disclosure/
        Surveillance are denied -- the report must say so explicitly (UNKNOWN_COVERAGE + a gap
        naming the failure), never silently fall through to a NONE-disclosure classification."""
        orchestrator = MultiAgentOrchestrator(budget_config=BudgetConfig(max_total_tool_calls=1, max_agent_tool_calls=1))
        report = orchestrator.run_for_event(self.conn, SYMBOL, self.days[70])
        self.assertEqual(report.disclosure_tier, "UNKNOWN_COVERAGE")
        self.assertEqual(report.classification, "UNEXPLAINED_UNKNOWN_COVERAGE")
        self.assertTrue(any("DISCLOSURE agent could not complete" in g for g in report.gaps), report.gaps)

class OrchestratorDeterminismTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        self.days = _seed_bhavcopy(self.conn)
        self.event_date = self.days[70]
        _seed_announcement(self.conn, self.days[65])

    def test_two_runs_of_the_same_event_are_byte_identical(self):
        r1 = MultiAgentOrchestrator().run_for_event(self.conn, SYMBOL, self.event_date)
        r2 = MultiAgentOrchestrator().run_for_event(self.conn, SYMBOL, self.event_date)
        self.assertEqual(r1.to_dict(), r2.to_dict())

if __name__ == "__main__":
    unittest.main()
