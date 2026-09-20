"""Real-data guard: runs MultiAgentOrchestrator against the actual populated database (not a
fixture) for one real catalogued event per classification, using the exact (symbol, event_date)
pairs scripts/build_event_classifications.py itself classified into each class. Two things this
confirms that a fixture test cannot: (1) the live, per-event pipeline agrees with the batch
classifier's output for the same real event -- both apply the same rules, so a mismatch would mean
a real bug in the live path, not a design disagreement; (2) real evidence, gathered from the real
store, never trips the Adversary's checks -- if it did, either a real data-consistency bug exists
or a specialist agent's claim-construction logic has drifted from what its own tool actually
returns.

Skipped automatically if the real database or the classification artifact isn't present (e.g. a
fresh checkout before the backfill scripts have been run) -- this is a guard against a real,
already-ingested dataset, not something that should fail CI in an environment without one.
"""
from __future__ import annotations
import unittest
from pathlib import Path

from src.agent.banned_terms import lint_text
from src.agent.orchestrator import MultiAgentOrchestrator
from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

REAL_EVENTS_BY_CLASS = {
    "GROUNDED": ("20MICRONS", "2020-03-12"),
    "UNEXPLAINED_ISOLATED": ("20MICRONS", "2020-12-18"),
    "UNEXPLAINED": ("20MICRONS", "2023-03-31"),
    "PARTIALLY_GROUNDED": ("20MICRONS", "2020-01-24"),
    "UNEXPLAINED_UNKNOWN_COVERAGE": ("AARVEEDEN", "2020-04-09"),
}

_settings = get_settings()
_db_present = Path(_settings.database_path).exists()

@unittest.skipUnless(_db_present, "real database not present in this environment")
class OrchestratorRealDataGuardTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(_settings.database_path)
        init_db(self.conn)
        self.orchestrator = MultiAgentOrchestrator()

    def test_live_classification_matches_batch_classification_for_every_class(self):
        for expected_class, (symbol, event_date) in REAL_EVENTS_BY_CLASS.items():
            with self.subTest(expected_class=expected_class, symbol=symbol, event_date=event_date):
                report = self.orchestrator.run_for_event(self.conn, symbol, event_date)
                self.assertEqual(report.classification, expected_class,
                    f"Live pipeline classified {symbol}/{event_date} as {report.classification}, "
                    f"batch classifier (data/processed/event_classifications.csv) says {expected_class}.")

    def test_real_evidence_never_trips_the_adversary(self):
        for expected_class, (symbol, event_date) in REAL_EVENTS_BY_CLASS.items():
            with self.subTest(expected_class=expected_class, symbol=symbol, event_date=event_date):
                report = self.orchestrator.run_for_event(self.conn, symbol, event_date)
                self.assertEqual(report.rejected_claims, [],
                    f"Real evidence for {symbol}/{event_date} was rejected by the Adversary: {report.rejected_claims}")

    def test_real_reports_are_banned_term_clean(self):
        for symbol, event_date in REAL_EVENTS_BY_CLASS.values():
            report = self.orchestrator.run_for_event(self.conn, symbol, event_date)
            for claim in report.accepted_claims:
                self.assertEqual(lint_text(claim["text"]), [], f"Banned-term violation: {claim}")
            for gap in report.gaps:
                self.assertEqual(lint_text(gap), [], f"Banned-term violation in a gap note: {gap}")

if __name__ == "__main__":
    unittest.main()
