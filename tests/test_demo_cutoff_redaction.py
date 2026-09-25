"""Constraint 2 (forward-window cutoff), redaction layer -- pure logic, no real data needed."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo.lib.cutoff import DEMO_DATA_CUTOFF, REDACTED, redact_post_cutoff


class RedactPostCutoffTest(unittest.TestCase):
    def test_date_on_cutoff_passes_through(self):
        self.assertEqual(redact_post_cutoff(DEMO_DATA_CUTOFF), DEMO_DATA_CUTOFF)

    def test_date_before_cutoff_passes_through(self):
        self.assertEqual(redact_post_cutoff("2026-01-01"), "2026-01-01")

    def test_date_after_cutoff_is_redacted(self):
        self.assertEqual(redact_post_cutoff("2026-09-16"), REDACTED)

    def test_non_date_string_is_never_touched(self):
        self.assertEqual(redact_post_cutoff("GROUNDED"), "GROUNDED")
        self.assertEqual(redact_post_cutoff("first flagged 40 session(s) after event_date"),
                          "first flagged 40 session(s) after event_date")

    def test_nested_dict_is_walked(self):
        value = {"a": "2026-09-20", "b": {"c": ["2026-01-01", "2026-12-31"]}}
        result = redact_post_cutoff(value)
        self.assertEqual(result["a"], REDACTED)
        self.assertEqual(result["b"]["c"][0], "2026-01-01")
        self.assertEqual(result["b"]["c"][1], REDACTED)

    def test_numbers_and_none_pass_through(self):
        self.assertEqual(redact_post_cutoff(42), 42)
        self.assertIsNone(redact_post_cutoff(None))

    def test_known_blind_spot_documented_not_fixed_here(self):
        """A derived value with no date in it (a session count implying a post-cutoff flag) is NOT
        caught by this pattern filter -- this is exactly why the structural cutoff (the demo store
        itself has no post-cutoff rows) is the primary control, not this function. See
        tests/test_demo_store_structural_cutoff.py for the real leak test."""
        self.assertEqual(redact_post_cutoff("first flagged 40 session(s) after event_date"),
                          "first flagged 40 session(s) after event_date")


if __name__ == "__main__":
    unittest.main()
