"""Acceptance test 3: epistemic enforcement -- a FACT without a source, an INFERENCE without a rule
or FACT, and a HYPOTHESIS without a test are each rejected. Plus the disclosure-UNKNOWN handling
requirement: a synthetic unseen category must produce Unknown, never a crash, never a silent
ROUTINE default.
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.models import EvidenceClaim
from desk.evidence.types import EpistemicTypeError, Fact, Hypothesis, Inference, Unknown
from desk.evidence.bundle import _is_unmapped, _disclosures


class FactRejectionTest(unittest.TestCase):
    def test_fact_without_source_is_rejected(self):
        claim = EvidenceClaim(claim_id="x", agent_role="DESK", text="t", cited_value=1, source="")
        with self.assertRaises(EpistemicTypeError):
            Fact(claim=claim)

    def test_fact_with_unverified_verify_closure_is_rejected(self):
        claim = EvidenceClaim(claim_id="x", agent_role="DESK", text="t", cited_value=1, source="s",
                               verify=lambda: 1)  # verification dict never populated -- never run through the Adversary
        with self.assertRaises(EpistemicTypeError):
            Fact(claim=claim)

    def test_fact_with_no_verify_closure_needs_no_verification(self):
        claim = EvidenceClaim(claim_id="x", agent_role="DESK", text="t", cited_value=1, source="s", verify=None)
        Fact(claim=claim)  # must not raise

    def test_fact_with_populated_verification_is_accepted(self):
        claim = EvidenceClaim(claim_id="x", agent_role="DESK", text="t", cited_value=1, source="s", verify=lambda: 1)
        claim.verification = {"transcription": "PASS"}
        Fact(claim=claim)  # must not raise


class InferenceRejectionTest(unittest.TestCase):
    def test_inference_without_fact_ids_is_rejected(self):
        with self.assertRaises(EpistemicTypeError):
            Inference(statement="s", fact_ids=(), rule_id="r1")

    def test_inference_without_rule_id_is_rejected(self):
        with self.assertRaises(EpistemicTypeError):
            Inference(statement="s", fact_ids=("f1",), rule_id="")

    def test_complete_inference_is_accepted(self):
        Inference(statement="s", fact_ids=("f1",), rule_id="r1")  # must not raise


class HypothesisRejectionTest(unittest.TestCase):
    def test_hypothesis_without_observable_test_is_rejected(self):
        with self.assertRaises(EpistemicTypeError):
            Hypothesis(statement="s", observable_test="")

    def test_complete_hypothesis_is_accepted(self):
        Hypothesis(statement="s", observable_test="check next quarter's results")  # must not raise


class UnknownRejectionTest(unittest.TestCase):
    def test_invalid_uncertainty_category_is_rejected(self):
        with self.assertRaises(EpistemicTypeError):
            Unknown(dimension="d", uncertainty_category="not_a_real_category", detail="x")

    def test_valid_uncertainty_category_is_accepted(self):
        Unknown(dimension="d", uncertainty_category="epistemic", detail="x")  # must not raise


class DisclosureUnmappedCategoryTest(unittest.TestCase):
    """The requirement: for the Desk, an unmapped category must become an UNKNOWN on the disclosure
    dimension -- INSUFFICIENT plus an alert naming the category -- never a crash and never a silent
    default. Verified against Praman's REAL classify_category_safe() behavior first (it does NOT
    raise -- it silently defaults to ROUTINE), then against the Desk's own detection layer, which
    must catch this before it ever reaches that safe default.
    """

    def test_praman_own_safe_classifier_silently_defaults_a_synthetic_unseen_category(self):
        from src.signals.disclosure_classification import classify_category_safe

        self.assertEqual(classify_category_safe("A Totally Synthetic Category Nobody Has Seen"), "ROUTINE")

    def test_desk_detects_the_same_synthetic_category_as_unmapped(self):
        self.assertTrue(_is_unmapped("A Totally Synthetic Category Nobody Has Seen"))
        self.assertFalse(_is_unmapped("Outcome of Board Meeting"))  # a real, mapped SUBSTANTIVE category

    def test_desk_disclosures_evidence_is_unknown_when_an_unmapped_category_is_present(self):
        from desk.lib.store import get_live_connection

        conn = get_live_connection()
        try:
            # Real disclosure_window rows for AXISBANK's real window, but with a synthetic category
            # spliced into one row to exercise the detection path deterministically without
            # depending on a real unmapped category actually existing in the live store today.
            import desk.evidence.bundle as bundle_module
            real_get_window = bundle_module.get_disclosure_window

            def fake_get_window(conn, symbol, event_date):
                result = real_get_window(conn, symbol, event_date)
                result["rows"] = list(result["rows"]) + [{
                    "event_date": event_date, "category": "A Totally Synthetic Category Nobody Has Seen",
                    "seq_id": "synthetic", "description": "",
                }]
                return result

            bundle_module.get_disclosure_window = fake_get_window
            try:
                evidence = _disclosures(conn, "AXISBANK", "2021-10-27")
            finally:
                bundle_module.get_disclosure_window = real_get_window

            self.assertIsInstance(evidence, Unknown)
            self.assertEqual(evidence.uncertainty_category, "epistemic")
            self.assertIn("A Totally Synthetic Category Nobody Has Seen", evidence.detail)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
