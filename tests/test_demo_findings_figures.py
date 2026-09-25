"""Constraint on the Findings page: every hand-transcribed figure in demo/lib/findings.py gets a
test asserting it equals its committed source, re-parsed independently here -- the P8-009 lesson
(docs/DEFECT_REGISTER.md): two hand-mirrored copies of the same fact silently drift apart if
nothing ever checks them against each other again.
"""
from __future__ import annotations
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from demo.lib import findings

def _flatten(text: str) -> str:
    """Collapses whitespace (including line-wraps inside a markdown paragraph) to single spaces --
    the checks below assert a phrase appears in the prose, not that it happens to fall on one
    physical line of the committed file."""
    return re.sub(r"\s+", " ", text)


RESULTS_TEXT = _flatten(findings.RESULTS_PATH.read_text(encoding="utf-8"))
AMENDMENT5_TEXT = _flatten(findings.AMENDMENT5_PATH.read_text(encoding="utf-8"))


class ParsedAucTableTest(unittest.TestCase):
    def test_parses_exactly_seven_rows(self):
        rows = findings.parse_final_auc_table()
        self.assertEqual(len(rows), 7)

    def test_zscore_row_matches_committed_values(self):
        rows = {r["feature"]: r for r in findings.parse_final_auc_table()}
        z = rows["zscore_60d"]
        self.assertEqual(z["train_auc"], 0.5285)
        self.assertEqual(z["holdout_auc"], 0.5250)
        self.assertEqual(z["holdout_ci"], (0.5104, 0.5397))


class RetractionFiguresMatchSourceTest(unittest.TestCase):
    def test_classifier_top_tier_precision_raw(self):
        self.assertIn("90.6%", RESULTS_TEXT)
        self.assertEqual(findings.RETRACTION["classifier_top_tier_precision_raw"], 90.6)

    def test_classifier_top_tier_precision_clean_and_n(self):
        self.assertRegex(
            RESULTS_TEXT,
            re.escape("28.6% (n=7, actually *below* base rate"),
        )
        self.assertEqual(findings.RETRACTION["classifier_top_tier_precision_clean"], 28.6)
        self.assertEqual(findings.RETRACTION["classifier_top_tier_n_clean"], 7)

    def test_disclosure_alone_figures(self):
        self.assertIn("78.7% to 51.1%", RESULTS_TEXT)
        self.assertEqual(findings.RETRACTION["disclosure_alone_precision_raw"], 78.7)
        self.assertEqual(findings.RETRACTION["disclosure_alone_precision_clean"], 51.1)


class DecompositionFiguresMatchSourceTest(unittest.TestCase):
    def test_raw_and_drift_corrected_lift(self):
        self.assertIn("+16.4pp under the raw label", RESULTS_TEXT)
        self.assertIn("+15.9pp once", RESULTS_TEXT)
        self.assertEqual(findings.DECOMPOSITION["raw_lift_pp"], 16.4)
        self.assertEqual(findings.DECOMPOSITION["drift_corrected_lift_pp"], 15.9)

    def test_decoupled_lift(self):
        self.assertIn("−22.5pp / +6.7pp", RESULTS_TEXT)  # U+2212 MINUS SIGN, not a hyphen -- matches RESULTS.md's own typography
        self.assertEqual(findings.DECOMPOSITION["decoupled_lift_pp_primary"], -22.5)
        self.assertEqual(findings.DECOMPOSITION["decoupled_lift_pp_secondary"], 6.7)


class FrozenPreregistrationFiguresMatchSourceTest(unittest.TestCase):
    def test_missing_rates_and_threshold(self):
        self.assertIn("1.310%", AMENDMENT5_TEXT)
        self.assertIn("0.897%", AMENDMENT5_TEXT)
        self.assertIn("4.3%", AMENDMENT5_TEXT)
        self.assertEqual(findings.FROZEN_PREREGISTRATION["train_missing_rate_pct"], 1.310)
        self.assertEqual(findings.FROZEN_PREREGISTRATION["holdout_missing_rate_pct"], 0.897)
        self.assertEqual(findings.FROZEN_PREREGISTRATION["missing_data_threshold_pct"], 4.3)

    def test_pinned_commit(self):
        self.assertIn(findings.FROZEN_PREREGISTRATION["pinned_commit"], AMENDMENT5_TEXT)


if __name__ == "__main__":
    unittest.main()
