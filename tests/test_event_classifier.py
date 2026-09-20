"""Fixture tests for src/classification/event_classifier.py -- the production application of the
Phase 7b rules approved in docs/phase7b_classification_design.md. These tests exercise every row
of the approved rule table directly; the real class-distribution validation lives in
scripts/design_classification_rules.py's own output (recorded in the design doc), not here."""
from __future__ import annotations
import unittest

from src.classification.event_classifier import (
    GROUNDED, PARTIALLY_GROUNDED, UNEXPLAINED, UNEXPLAINED_ISOLATED, UNEXPLAINED_UNKNOWN_COVERAGE,
    ClassificationThresholds, classify_event, momentum_is_high, sessions_to_subsequent_flag,
)
from src.signals.surveillance_state import SurveillanceTimeline

THRESHOLDS = ClassificationThresholds(
    band_median_abs_return_20d={"Micro": 0.10, "Large": 0.12},
    isolated_comovement_threshold=36,
)

class ClassifyEventTest(unittest.TestCase):
    def test_no_coverage_overrides_everything(self):
        cls, is_isolated = classify_event(
            disclosure_tier="SUBSTANTIVE", has_coverage=False, momentum_high=True,
            same_date_event_count=1, thresholds=THRESHOLDS,
        )
        self.assertEqual(cls, UNEXPLAINED_UNKNOWN_COVERAGE)
        self.assertIsNone(is_isolated)

    def test_substantive_is_grounded_regardless_of_momentum_or_isolation(self):
        cls, _ = classify_event(disclosure_tier="SUBSTANTIVE", has_coverage=True, momentum_high=False,
                                 same_date_event_count=1, thresholds=THRESHOLDS)
        self.assertEqual(cls, GROUNDED)

    def test_routine_only_high_momentum_is_partially_grounded(self):
        cls, _ = classify_event(disclosure_tier="ROUTINE_ONLY", has_coverage=True, momentum_high=True,
                                 same_date_event_count=1000, thresholds=THRESHOLDS)
        self.assertEqual(cls, PARTIALLY_GROUNDED)

    def test_routine_only_low_momentum_is_unexplained(self):
        cls, _ = classify_event(disclosure_tier="ROUTINE_ONLY", has_coverage=True, momentum_high=False,
                                 same_date_event_count=1000, thresholds=THRESHOLDS)
        self.assertEqual(cls, UNEXPLAINED)

    def test_routine_only_missing_momentum_defaults_to_unexplained_not_grounded(self):
        cls, _ = classify_event(disclosure_tier="ROUTINE_ONLY", has_coverage=True, momentum_high=None,
                                 same_date_event_count=1000, thresholds=THRESHOLDS)
        self.assertEqual(cls, UNEXPLAINED)

    def test_none_isolated_is_unexplained_isolated_regardless_of_momentum(self):
        cls, is_isolated = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=True,
                                           same_date_event_count=5, thresholds=THRESHOLDS)
        self.assertEqual(cls, UNEXPLAINED_ISOLATED)
        self.assertTrue(is_isolated)

    def test_none_not_isolated_high_momentum_is_partially_grounded(self):
        cls, is_isolated = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=True,
                                           same_date_event_count=100, thresholds=THRESHOLDS)
        self.assertEqual(cls, PARTIALLY_GROUNDED)
        self.assertFalse(is_isolated)

    def test_none_not_isolated_low_momentum_is_unexplained(self):
        cls, is_isolated = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=False,
                                           same_date_event_count=100, thresholds=THRESHOLDS)
        self.assertEqual(cls, UNEXPLAINED)
        self.assertFalse(is_isolated)

    def test_none_missing_comovement_count_is_not_isolated_by_default(self):
        """A missing same_date_event_count must never silently qualify as 'isolated' -- the
        conservative default (can't confirm isolation -> don't claim it)."""
        cls, is_isolated = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=True,
                                           same_date_event_count=None, thresholds=THRESHOLDS)
        self.assertFalse(is_isolated)
        self.assertEqual(cls, PARTIALLY_GROUNDED)

    def test_isolated_boundary_is_strictly_below_threshold(self):
        cls_at, _ = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=False,
                                    same_date_event_count=36, thresholds=THRESHOLDS)
        cls_below, _ = classify_event(disclosure_tier="NONE", has_coverage=True, momentum_high=False,
                                       same_date_event_count=35, thresholds=THRESHOLDS)
        self.assertEqual(cls_at, UNEXPLAINED)  # 36 is NOT < 36
        self.assertEqual(cls_below, UNEXPLAINED_ISOLATED)

class MomentumIsHighTest(unittest.TestCase):
    def test_missing_return_is_none(self):
        self.assertIsNone(momentum_is_high(None, "Micro", THRESHOLDS))

    def test_missing_band_median_is_none(self):
        self.assertIsNone(momentum_is_high(0.5, "Mega", THRESHOLDS))

    def test_at_or_above_median_is_high(self):
        self.assertTrue(momentum_is_high(0.10, "Micro", THRESHOLDS))
        self.assertTrue(momentum_is_high(0.20, "Micro", THRESHOLDS))

    def test_below_median_is_low(self):
        self.assertFalse(momentum_is_high(0.05, "Micro", THRESHOLDS))

class SessionsToSubsequentFlagTest(unittest.TestCase):
    def setUp(self):
        self.days = [f"2024-01-{d:02d}" for d in range(1, 29)]  # 28 fake trading sessions

    def test_already_flagged_by_asm(self):
        timeline = SurveillanceTimeline(entries=[])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-10", trading_days=self.days,
            asm_stage_as_of="I", gsm_stage_as_of=None,
        )
        self.assertIsNone(gap)
        self.assertIn("already under surveillance", note)

    def test_already_flagged_by_gsm(self):
        timeline = SurveillanceTimeline(entries=[])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-10", trading_days=self.days,
            asm_stage_as_of=None, gsm_stage_as_of="II",
        )
        self.assertIsNone(gap)
        self.assertIn("already under surveillance", note)

    def test_no_subsequent_flag(self):
        timeline = SurveillanceTimeline(entries=[])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-10", trading_days=self.days,
            asm_stage_as_of=None, gsm_stage_as_of=None,
        )
        self.assertIsNone(gap)
        self.assertIn("no subsequent flag", note)

    def test_subsequent_flag_gap_computed_in_real_sessions(self):
        timeline = SurveillanceTimeline(entries=[
            {"event_date": "2024-01-15", "mechanism": "ASM_ST", "to_stage": "I"},
        ])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-10", trading_days=self.days,
            asm_stage_as_of=None, gsm_stage_as_of=None,
        )
        self.assertEqual(gap, 5)  # index of the 15th minus index of the 10th
        self.assertIn("first flagged 5 session(s)", note)
        self.assertIn("ASM_ST", note)

    def test_earliest_of_multiple_future_entries_is_used(self):
        timeline = SurveillanceTimeline(entries=[
            {"event_date": "2024-01-20", "mechanism": "GSM", "to_stage": "III"},
            {"event_date": "2024-01-12", "mechanism": "ASM_ST", "to_stage": "I"},
        ])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-10", trading_days=self.days,
            asm_stage_as_of=None, gsm_stage_as_of=None,
        )
        self.assertEqual(gap, 2)
        self.assertIn("ASM_ST", note)

    def test_event_date_not_in_trading_calendar_falls_back_gracefully(self):
        """self.days only covers 2024-01-01..28 -- an event_date outside that range (a fixture
        gap, not something that happens for real catalogued events) must degrade to an explicit
        note rather than raise or silently report a wrong gap."""
        timeline = SurveillanceTimeline(entries=[
            {"event_date": "2024-02-05", "mechanism": "ASM_ST", "to_stage": "I"},
        ])
        gap, note = sessions_to_subsequent_flag(
            timeline=timeline, event_date="2024-01-31", trading_days=self.days,
            asm_stage_as_of=None, gsm_stage_as_of=None,
        )
        self.assertIsNone(gap)
        self.assertIn("session gap not computable", note)

if __name__ == "__main__":
    unittest.main()
