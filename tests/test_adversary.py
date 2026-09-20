"""The Adversary's core requirement, tested directly: deliberately fabricated claims must be
caught and must never reach the accepted set. Each test constructs an EvidenceClaim whose
cited_value/text has been tampered with relative to what independent verification would find, and
asserts the Adversary rejects it -- not merely flags it as a warning."""
from __future__ import annotations
import unittest

from src.agent.adversary import AdversaryAgent
from src.agent.models import EvidenceClaim

class AdversaryFabricatedClaimTest(unittest.TestCase):
    def setUp(self):
        self.adversary = AdversaryAgent()

    def test_fabricated_numeric_value_is_rejected(self):
        """A claim citing a volume_ratio that does not match what fresh recomputation gives --
        the exact shape of a hallucinated or tampered number."""
        claim = EvidenceClaim(
            claim_id="FAKE:2024-01-01:volume_ratio", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 47.00x the trailing 60-session median traded quantity.",
            cited_value=47.00, source="bhavcopy, trailing 60-session median traded_qty",
            verify=lambda: 3.2,  # what independent recomputation actually finds
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "transcription")
        self.assertEqual(fail.verdict, "FAIL")
        self.assertIn("47.0", fail.detail)
        self.assertIn("3.2", fail.detail)

    def test_fabricated_record_existence_claim_is_rejected(self):
        """A claim asserting a specific announcement record exists when independent lookup finds
        it does not -- the record-existence check."""
        claim = EvidenceClaim(
            claim_id="FAKE:2024-01-01:announcement:99999", agent_role="DISCLOSURE",
            text="A 'Outcome of Board Meeting' announcement (seq_id 99999) was disclosed on 2024-01-01, before this event.",
            cited_value=True, source="corporate_announcements",
            verify=lambda: False,  # independent lookup: this seq_id was never found
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "transcription")
        self.assertEqual(fail.verdict, "FAIL")

    def test_conclusion_language_claim_is_rejected_even_with_correct_numbers(self):
        """A claim whose NUMBERS are all correct but whose text states a banned verdict must
        still be rejected -- correctness of the cited value does not excuse invariant 12."""
        claim = EvidenceClaim(
            claim_id="FAKE:2024-01-01:verdict", agent_role="MARKET_MICROSTRUCTURE",
            text="Delivery 11% on 14x average volume with no disclosure -- this is manipulation.",
            cited_value=11.0, source="bhavcopy delivery_pct, event day",
            verify=lambda: 11.0,  # the number itself is correct
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "conclusion_language")
        self.assertEqual(fail.verdict, "FAIL")

    def test_cherry_picked_window_claim_is_rejected(self):
        """A disclosure-tier claim that used a non-canonical window (e.g. narrowed to hide a
        substantive disclosure just outside it) must be caught by the window check."""
        claim = EvidenceClaim(
            claim_id="FAKE:2024-01-01:disclosure_tier", agent_role="DISCLOSURE",
            text="Disclosure tier for the 3-session pre-event window: NONE.",
            cited_value="NONE", source="disclosure_classification.classify_disclosure_window",
            verify=lambda: "NONE", window_description="3 sessions", canonical_window="10 sessions",
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "window")
        self.assertEqual(fail.verdict, "FAIL")

    def test_verification_that_raises_is_treated_as_failure_not_silently_passed(self):
        """A claim whose verify() closure raises (e.g. the underlying record vanished, a real
        error) must fail closed, not be silently accepted because verification 'didn't run.'"""
        def broken():
            raise RuntimeError("store lookup failed")
        claim = EvidenceClaim(
            claim_id="FAKE:2024-01-01:broken", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 3.20x the trailing 60-session median traded quantity.",
            cited_value=3.2, source="bhavcopy", verify=broken,
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "transcription")
        self.assertEqual(fail.verdict, "FAIL")
        self.assertIn("store lookup failed", fail.detail)

    def test_genuine_valid_claim_is_accepted(self):
        """Negative control for the above: a claim that is correct on every axis must survive --
        the Adversary must not be so aggressive it rejects good evidence."""
        claim = EvidenceClaim(
            claim_id="REAL:2024-01-01:volume_ratio", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 3.20x the trailing 60-session median traded quantity.",
            cited_value=3.2, source="bhavcopy, trailing 60-session median traded_qty",
            verify=lambda: 3.2,
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(len(accepted), 1)
        # NOT_APPLICABLE (e.g. derivation, since this claim has no derivation_verify) is a valid
        # non-failure verdict, not a reason to reject -- only FAIL should ever appear here.
        self.assertFalse(any(f.verdict == "FAIL" for f in findings))
        self.assertEqual(accepted[0].verification["transcription"], "PASS")
        self.assertEqual(accepted[0].verification["derivation"], "NOT_APPLICABLE")

    def test_mixed_batch_only_the_fabricated_claim_is_dropped(self):
        good = EvidenceClaim(
            claim_id="REAL:2024-01-01:zscore", agent_role="MARKET_MICROSTRUCTURE",
            text="The event-day return had a z-score of 3.14 against its trailing 60-session return distribution.",
            cited_value=3.14, source="bhavcopy", verify=lambda: 3.14,
        )
        fabricated = EvidenceClaim(
            claim_id="FAKE:2024-01-01:zscore", agent_role="MARKET_MICROSTRUCTURE",
            text="The event-day return had a z-score of 99.00 against its trailing 60-session return distribution.",
            cited_value=99.0, source="bhavcopy", verify=lambda: 3.14,
        )
        accepted, findings = self.adversary.verify([good, fabricated])
        self.assertEqual([c.claim_id for c in accepted], [good.claim_id])

class AdversaryDerivationTierTest(unittest.TestCase):
    """Tier 2: a SEPARATE, independently-implemented recomputation, distinct from transcription
    (which re-runs the SAME function the claim's value came from and therefore cannot see a bug
    inside that shared function). "TESTBUG:..." and "TESTNOTSAMPLED:..." are real claim_ids
    confirmed (src/agent/derivation_check.py:is_sampled_for_derivation) to fall on either side of
    the deterministic ~20% seeded sample -- picked directly, not mocked, so this test exercises
    the real sampling function, not a stand-in for it."""
    def setUp(self):
        self.adversary = AdversaryAgent()

    def test_derivation_catches_a_systematic_bug_transcription_alone_would_miss(self):
        """The core scenario the two-tier design exists for: the SHARED derivation function has a
        bug, so `verify` (which re-runs that same function) returns the identical wrong number and
        transcription PASSES -- but the independent, separately-implemented `derivation_verify`
        computes the correct value from raw bhavcopy rows and disagrees. The claim must still be
        rejected overall."""
        claim = EvidenceClaim(
            claim_id="TESTBUG:2024-01-01:volume_ratio", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 9.00x the trailing 60-session median traded quantity.",
            cited_value=9.0, source="bhavcopy, trailing 60-session median traded_qty",
            verify=lambda: 9.0,             # the SAME (buggy) shared function -- agrees, transcription PASSES
            derivation_verify=lambda: 3.2,  # independent recomputation from raw bhavcopy -- disagrees
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        transcription = next(f for f in findings if f.check == "transcription")
        derivation = next(f for f in findings if f.check == "derivation")
        self.assertEqual(transcription.verdict, "PASS")   # transcription alone would have let this through
        self.assertEqual(derivation.verdict, "FAIL")       # derivation is what actually catches it
        self.assertIn("9.0", derivation.detail)
        self.assertIn("3.2", derivation.detail)

    def test_derivation_not_applicable_when_no_second_implementation_exists(self):
        """zscore_60d/return_20d-shaped claims have no derivation_verify yet (module docstring's
        stated scope limit) -- must report NOT_APPLICABLE, never silently PASS."""
        claim = EvidenceClaim(
            claim_id="REAL:2024-01-01:zscore", agent_role="MARKET_MICROSTRUCTURE",
            text="The event-day return had a z-score of 3.14 against its trailing 60-session return distribution.",
            cited_value=3.14, source="bhavcopy", verify=lambda: 3.14,
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].verification["derivation"], "NOT_APPLICABLE")

    def test_derivation_not_sampled_is_recorded_not_silently_passed(self):
        """A derivation-eligible claim outside the seeded sample must be marked NOT_SAMPLED, not
        PASS -- a reader must be able to tell 'checked and agreed' from 'not checked this time.'"""
        claim = EvidenceClaim(
            claim_id="TESTNOTSAMPLED:2024-01-01:volume_ratio", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 3.20x the trailing 60-session median traded quantity.",
            cited_value=3.2, source="bhavcopy", verify=lambda: 3.2,
            derivation_verify=lambda: 3.2,
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].verification["derivation"], "NOT_SAMPLED")

    def test_derivation_sample_selection_is_deterministic(self):
        from src.agent.derivation_check import is_sampled_for_derivation
        claim_id = "TESTBUG:2024-01-01:volume_ratio"
        self.assertTrue(is_sampled_for_derivation(claim_id))
        self.assertEqual(is_sampled_for_derivation(claim_id), is_sampled_for_derivation(claim_id))

    def test_derivation_that_raises_fails_closed(self):
        def broken():
            raise RuntimeError("independent query failed")
        claim = EvidenceClaim(
            claim_id="TESTBUG:2024-01-01:volume_ratio", agent_role="MARKET_MICROSTRUCTURE",
            text="Traded quantity was 3.20x the trailing 60-session median traded quantity.",
            cited_value=3.2, source="bhavcopy", verify=lambda: 3.2, derivation_verify=broken,
        )
        accepted, findings = self.adversary.verify([claim])
        self.assertEqual(accepted, [])
        fail = next(f for f in findings if f.check == "derivation")
        self.assertEqual(fail.verdict, "FAIL")
        self.assertIn("independent query failed", fail.detail)

if __name__ == "__main__":
    unittest.main()
