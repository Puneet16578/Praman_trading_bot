"""Phase 7: substantive vs. routine disclosure classification. Coverage against the real store is
asserted directly (not just fixture-tested), since an uncategorized real category is exactly the
defect this module exists to prevent.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

from src.signals.disclosure_classification import (
    AMBIGUOUS_CATEGORIES, ROUTINE_CATEGORIES, SUBSTANTIVE_CATEGORIES,
    classify_category, classify_category_safe, classify_disclosure_window,
)

CATEGORY_COUNTS_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "announcement_category_counts.json"

class ClassifyCategoryTest(unittest.TestCase):
    def test_known_substantive_examples(self):
        for cat in ("Outcome of Board Meeting", "Financial Result Updates", "Bagging/Receiving of orders/contracts",
                    "Action(s) taken or orders passed", "Acquisition", "Credit Rating"):
            self.assertEqual(classify_category(cat), "SUBSTANTIVE", cat)

    def test_board_meeting_intimation_is_a_recorded_judgment_call_substantive(self):
        """Structurally the same shape as an investor-meet notice (ROUTINE) -- announces a
        meeting WILL occur, not what was decided. Classed SUBSTANTIVE anyway because SEBI LODR
        requires the intimation to state WHY the board is meeting; see the module's inline
        rationale. Recorded as its own test specifically so this judgment call is visible and
        breakable, not buried inside the general substantive-examples list."""
        self.assertEqual(classify_category("Board Meeting Intimation"), "SUBSTANTIVE")
        self.assertEqual(classify_category("Intimation of Board Meeting"), "SUBSTANTIVE")

    def test_known_routine_examples(self):
        for cat in ("Analysts/Institutional Investor Meet/Con. Call Updates", "Trading Window",
                    "Certificate under SEBI (Depositories and Participants) Regulations, 2018",
                    "Copy of Newspaper Publication", "Loss of Share Certificates", "Record Date"):
            self.assertEqual(classify_category(cat), "ROUTINE", cat)

    def test_known_ambiguous_examples(self):
        """Confirmed by direct content inspection (Phase 7a), not assumed: 'Updates' bundles both
        substantive (CRISIL/CARE rating letters, Reg 30 disclosures) and routine content."""
        for cat in ("Updates", "General Updates", "Press Release", "Investor Presentation"):
            self.assertEqual(classify_category(cat), "AMBIGUOUS", cat)

    def test_uncategorized_real_category_raises_not_silently_defaults(self):
        with self.assertRaises(ValueError):
            classify_category("Some category that has never been observed")

class ClassifyCategorySafeTest(unittest.TestCase):
    """Live-classification path: never raises, and an unmapped category can only ever degrade a
    report toward ROUTINE, never inflate it toward SUBSTANTIVE."""

    def test_known_categories_behave_identically_to_the_strict_function(self):
        self.assertEqual(classify_category_safe("Acquisition"), "SUBSTANTIVE")
        self.assertEqual(classify_category_safe("Trading Window"), "ROUTINE")
        self.assertEqual(classify_category_safe("Updates"), "AMBIGUOUS")

    def test_unmapped_category_defaults_to_routine_never_substantive(self):
        result = classify_category_safe("A brand new NSE category introduced after this mapping was built")
        self.assertEqual(result, "ROUTINE")
        self.assertNotEqual(result, "SUBSTANTIVE")

    def test_window_with_only_an_unmapped_category_cannot_be_classified_substantive(self):
        rows = [{"category": "A brand new NSE category introduced after this mapping was built"}]
        self.assertEqual(classify_disclosure_window(rows), "ROUTINE_ONLY")

class FullCoverageAgainstRealStoreTest(unittest.TestCase):
    """The real store (280 distinct categories, 1,021,591 rows, full backfill) must be entirely
    covered -- every real category classified explicitly, none silently defaulted."""

    def setUp(self):
        if not CATEGORY_COUNTS_PATH.exists():
            self.skipTest(f"{CATEGORY_COUNTS_PATH} not present -- real-data coverage check skipped")
        with open(CATEGORY_COUNTS_PATH, encoding="utf-8") as f:
            self.counts = dict(json.load(f))

    def test_every_real_category_is_classified(self):
        all_classified = SUBSTANTIVE_CATEGORIES | ROUTINE_CATEGORIES | AMBIGUOUS_CATEGORIES
        missing = set(self.counts) - all_classified
        self.assertEqual(missing, set(), f"{len(missing)} real categories are not covered by the mapping: {sorted(missing)}")

    def test_no_stale_mapped_categories_that_no_longer_exist(self):
        """Not a correctness requirement (a mapped-but-unobserved category is harmless), but a
        signal that the mapping may be stale relative to the real store -- flagged, not silently
        ignored, so a rename/typo in the mapping doesn't quietly stop covering the real category
        it was meant to."""
        all_classified = SUBSTANTIVE_CATEGORIES | ROUTINE_CATEGORIES | AMBIGUOUS_CATEGORIES
        extra = all_classified - set(self.counts)
        self.assertEqual(extra, set(), f"{len(extra)} mapped categories were not observed in the real store: {sorted(extra)}")

class ClassifyDisclosureWindowTest(unittest.TestCase):
    def test_empty_window_is_none(self):
        self.assertEqual(classify_disclosure_window([]), "NONE")

    def test_substantive_row_present_wins(self):
        rows = [{"category": "Trading Window"}, {"category": "Outcome of Board Meeting"}]
        self.assertEqual(classify_disclosure_window(rows), "SUBSTANTIVE")

    def test_routine_only(self):
        rows = [{"category": "Trading Window"}, {"category": "Record Date"}]
        self.assertEqual(classify_disclosure_window(rows), "ROUTINE_ONLY")

    def test_ambiguous_only_conservatively_treated_as_routine_only(self):
        """An investor-meet-shaped 'Updates' row alone cannot be treated as grounds for calling a
        move explained -- CLAUDE.md invariant 12's never-overclaim rule."""
        rows = [{"category": "Updates"}]
        self.assertEqual(classify_disclosure_window(rows), "ROUTINE_ONLY")

    def test_mix_of_ambiguous_and_routine_stays_routine_only(self):
        rows = [{"category": "Updates"}, {"category": "Trading Window"}]
        self.assertEqual(classify_disclosure_window(rows), "ROUTINE_ONLY")

    def test_ambiguous_plus_substantive_is_substantive(self):
        rows = [{"category": "Updates"}, {"category": "Acquisition"}]
        self.assertEqual(classify_disclosure_window(rows), "SUBSTANTIVE")

if __name__ == "__main__":
    unittest.main()
