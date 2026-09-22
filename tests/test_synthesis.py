"""Direct unit tests for SynthesisAgent.render() -- specifically the classification_notes field
(src/classification/event_classifier.py: INDISTINGUISHABLE_PAIR_NOTE, GROUNDED_LIMITATION_NOTE),
which must appear at the point of classification, not a footnote. A list, not a single optional
string, because more than one note can apply to the same class: GROUNDED carries both the
indistinguishability note (it shares a collapse-rate profile with UNEXPLAINED_ISOLATED) and its
own proportionality limitation (disclosure presence says nothing about whether the disclosure's
materiality matches the move's size). Exercised directly against SynthesisAgent rather than
through the full orchestrator/store fixture, since forcing UNEXPLAINED_ISOLATED requires a
specific same_date_event_count that a synthetic (non-catalogued) symbol cannot supply through the
real reference-data lookup.
"""
from __future__ import annotations
import unittest

from src.agent.banned_terms import lint_text
from src.agent.models import EvidenceClaim
from src.agent.synthesis import SynthesisAgent
from src.classification.event_classifier import (
    BASELINE_COMPARISON_NOTE, ClassificationThresholds, DISCRIMINATIVE_POWER_NOTE,
    GROUNDED_LIMITATION_NOTE, INDISTINGUISHABLE_PAIR_NOTE,
)

THRESHOLDS = ClassificationThresholds(
    band_median_abs_return_20d={"Micro": 0.10, "Large": 0.12},
    isolated_comovement_threshold=36,
)

def _return_20d_claim(value: float) -> EvidenceClaim:
    return EvidenceClaim(claim_id="X:2024-01-01:return_20d", agent_role="MARKET_MICROSTRUCTURE",
                          text=f"20d return {value}", cited_value=value, source="test")

def _tier_claim(tier: str) -> EvidenceClaim:
    return EvidenceClaim(claim_id="X:2024-01-01:disclosure_tier", agent_role="DISCLOSURE",
                          text=f"tier {tier}", cited_value=tier, source="test")

class ClassificationNoteTest(unittest.TestCase):
    def setUp(self):
        self.synth = SynthesisAgent()

    def _render(self, *, tier: str, same_date_event_count: int, return_20d: float = 0.20):
        return self.synth.render(
            symbol="X", event_date="2024-01-01",
            microstructure_claims=[_return_20d_claim(return_20d)],
            disclosure_claims=[_tier_claim(tier)], surveillance_claims=[], rejected=[],
            catalogue_reference={"cap_band": "Micro", "same_date_event_count": same_date_event_count, "source": "test"},
            thresholds=THRESHOLDS, agents_used=[], tool_calls_used=0,
        )

    def test_grounded_carries_both_the_indistinguishability_and_proportionality_notes(self):
        report = self._render(tier="SUBSTANTIVE", same_date_event_count=1000)
        self.assertEqual(report.classification, "GROUNDED")
        self.assertIn(INDISTINGUISHABLE_PAIR_NOTE, report.classification_notes)
        self.assertIn(GROUNDED_LIMITATION_NOTE, report.classification_notes)
        self.assertEqual(len(report.classification_notes), 2)

    def test_unexplained_isolated_carries_only_the_indistinguishability_note(self):
        report = self._render(tier="NONE", same_date_event_count=1)  # well below threshold=36
        self.assertEqual(report.classification, "UNEXPLAINED_ISOLATED")
        self.assertEqual(report.classification_notes, [INDISTINGUISHABLE_PAIR_NOTE])

    def test_partially_grounded_has_no_notes(self):
        report = self._render(tier="NONE", same_date_event_count=1000, return_20d=0.50)  # not isolated, high momentum
        self.assertEqual(report.classification, "PARTIALLY_GROUNDED")
        self.assertEqual(report.classification_notes, [])

    def test_plain_unexplained_has_no_notes(self):
        report = self._render(tier="NONE", same_date_event_count=1000, return_20d=0.01)  # not isolated, low momentum
        self.assertEqual(report.classification, "UNEXPLAINED")
        self.assertEqual(report.classification_notes, [])

    def test_unknown_coverage_has_no_notes(self):
        report = self.synth.render(
            symbol="X", event_date="2024-01-01", microstructure_claims=[],
            disclosure_claims=[EvidenceClaim(claim_id="X:2024-01-01:no_coverage", agent_role="DISCLOSURE",
                                              text="no coverage", cited_value=False, source="test")],
            surveillance_claims=[], rejected=[], catalogue_reference=None,
            thresholds=THRESHOLDS, agents_used=[], tool_calls_used=0,
        )
        self.assertEqual(report.classification, "UNEXPLAINED_UNKNOWN_COVERAGE")
        self.assertEqual(report.classification_notes, [])

    def test_notes_are_banned_term_clean(self):
        self.assertEqual(lint_text(INDISTINGUISHABLE_PAIR_NOTE), [])
        self.assertEqual(lint_text(GROUNDED_LIMITATION_NOTE), [])

    def test_discriminative_power_note_is_attached_unconditionally(self):
        """Unlike classification_notes (class-specific), the P8-001-corrected discriminative-power
        statement must appear on EVERY report, next to the classification, regardless of class.
        The original 0.611-0.70 ceiling this note used to cite is WITHDRAWN (P8-001) -- asserting
        its absence here, not its presence, so a future accidental revert is caught."""
        for tier, count, r20 in [("SUBSTANTIVE", 1000, 0.20), ("NONE", 1000, 0.01), ("ROUTINE", 1000, 0.50)]:
            with self.subTest(tier=tier):
                report = self._render(tier=tier if tier != "ROUTINE" else "ROUTINE_ONLY", same_date_event_count=count, return_20d=r20)
                self.assertEqual(report.discriminative_power_note, DISCRIMINATIVE_POWER_NOTE)
                self.assertIn("P8-001", report.discriminative_power_note)
                self.assertNotIn("0.611", report.discriminative_power_note)
                self.assertEqual(lint_text(report.discriminative_power_note), [])

    def test_baseline_comparison_note_is_attached_unconditionally(self):
        report = self._render(tier="SUBSTANTIVE", same_date_event_count=1000)
        self.assertEqual(report.baseline_comparison_note, BASELINE_COMPARISON_NOTE)
        self.assertEqual(lint_text(report.baseline_comparison_note), [])

if __name__ == "__main__":
    unittest.main()
