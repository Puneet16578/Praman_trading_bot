"""Query-time adjustment factor / adjusted close. BAJFINANCE 2025 (bonus 4:1 AND split 2:1 on the
same ex-date) is the permanent compounding fixture -- it must produce 10x, not 4x or 2x, and is
exactly the case that would silently under-compound if the two actions were applied independently
instead of multiplicatively.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_fact
from src.ingestion.nse_market_data.corporate_actions import (
    BONUS, CONFIRMED, DEMERGER, DEMERGER_EXCLUSION, RATIO_CONFLICT, RATIO_CONFLICT_EXCLUSION,
    RIGHTS, RIGHTS_EXCLUSION, SPLIT,
)
from src.signals.price_adjustment import UnadjustableWindowError, adjusted_close, compute_adjustment_factor, factor_for_action

def make_bhavcopy(symbol, event_date, knowledge_date, close_price):
    return {
        "symbol": symbol, "event_date": event_date, "knowledge_date": knowledge_date,
        "open_price": close_price, "high_price": close_price, "low_price": close_price,
        "close_price": close_price, "prev_close": close_price, "traded_qty": 1000,
        "delivery_qty": 500, "delivery_pct": 50.0, "series": "EQ",
        "source_file": "fixture.csv",
    }

def make_action(symbol, action_type, event_date, knowledge_date, num, denom, tier=CONFIRMED):
    return {
        "symbol": symbol, "action_type": action_type, "event_date": event_date, "knowledge_date": knowledge_date,
        "ratio_numerator": num, "ratio_denominator": denom, "confidence_tier": tier,
        "details": "fixture", "source_file": "fixture.json",
    }

class FactorForActionTest(unittest.TestCase):
    def test_bonus_4_1(self):
        self.assertEqual(factor_for_action(BONUS, 4.0, 1.0), 5.0)

    def test_split_2_1(self):
        self.assertEqual(factor_for_action(SPLIT, 2.0, 1.0), 2.0)

    def test_unadjustable_type_rejected(self):
        with self.assertRaises(ValueError):
            factor_for_action(DEMERGER, 1.0, 1.0)

class BajfinanceCompoundingFixtureTest(unittest.TestCase):
    """The permanent fixture: real BAJFINANCE 2025 bonus 4:1 + split 2:1, same ex-date
    (2025-06-16), announced 2025-04-29. Must compound to 10x -- verified by hand against the
    real board-meeting announcement text this session (see docs/phase3_corporate_actions.md)."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        # A raw close shortly before the actions -- real BAJFINANCE traded around this level pre-action.
        write_fact(self.conn, "bhavcopy", make_bhavcopy("BAJFINANCE", "2025-06-13", "2025-06-13", 8800.0))
        write_fact(self.conn, "corporate_actions", make_action("BAJFINANCE", BONUS, "2025-06-16", "2025-04-29", 4.0, 1.0))
        write_fact(self.conn, "corporate_actions", make_action("BAJFINANCE", SPLIT, "2025-06-16", "2025-04-29", 2.0, 1.0))

    def test_before_ex_date_factor_is_one_no_adjustment_needed(self):
        as_of = "2025-06-15"  # before the ex-date -- window can't span it
        factor = compute_adjustment_factor(self.conn, "BAJFINANCE", "2025-06-13", as_of)
        self.assertEqual(factor, 1.0)

    def test_after_ex_date_factor_compounds_to_ten_not_four_or_two(self):
        as_of = "2025-06-20"  # at/after the ex-date -- both actions visible and known
        factor = compute_adjustment_factor(self.conn, "BAJFINANCE", "2025-06-13", as_of)
        self.assertEqual(factor, 10.0, "Bonus (5x) and split (2x) must compound multiplicatively to 10x.")

    def test_adjusted_close_before_and_after(self):
        before = adjusted_close(self.conn, "BAJFINANCE", "2025-06-13", "2025-06-15")
        after = adjusted_close(self.conn, "BAJFINANCE", "2025-06-13", "2025-06-20")
        self.assertEqual(before, 8800.0)
        self.assertEqual(after, 880.0)  # 8800 / 10 -- the real, publicly observable post-action price level

class BitemporalSafetyTest(unittest.TestCase):
    """Section 7: an action whose knowledge_date has not yet arrived as of the query's `as_of`
    must not affect the factor, even though its event_date (ex_date) has already passed in
    calendar time -- this is the look-ahead-bias guarantee the whole project rests on."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy("TESTCO", "2025-01-01", "2025-01-01", 100.0))
        # event_date (ex_date) already passed by 2025-02-01, but knowledge_date is LATER (a late-filed/
        # retroactively-announced action) -- as_of=2025-02-01 must not see it.
        write_fact(self.conn, "corporate_actions", make_action("TESTCO", BONUS, "2025-01-15", "2025-03-01", 1.0, 1.0))

    def test_action_invisible_before_its_own_knowledge_date(self):
        factor = compute_adjustment_factor(self.conn, "TESTCO", "2025-01-01", "2025-02-01")
        self.assertEqual(factor, 1.0, "An action not yet knowledge-dated as of the query must not affect adjustment.")

    def test_action_visible_after_its_own_knowledge_date(self):
        factor = compute_adjustment_factor(self.conn, "TESTCO", "2025-01-01", "2025-03-01")
        self.assertEqual(factor, 2.0)

class DemergerUnadjustableTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy("RELIANCE", "2023-06-01", "2023-06-01", 2500.0))
        write_fact(self.conn, "corporate_actions", {
            "symbol": "RELIANCE", "action_type": DEMERGER, "event_date": "2023-07-20", "knowledge_date": "2023-07-20",
            "ratio_numerator": None, "ratio_denominator": None, "confidence_tier": DEMERGER_EXCLUSION,
            "details": "Demerger", "source_file": "fixture.json",
        })

    def test_demerger_in_range_raises_not_silently_ignored(self):
        with self.assertRaises(UnadjustableWindowError):
            compute_adjustment_factor(self.conn, "RELIANCE", "2023-06-01", "2023-08-01")

    def test_demerger_outside_range_does_not_raise(self):
        factor = compute_adjustment_factor(self.conn, "RELIANCE", "2023-06-01", "2023-07-01")
        self.assertEqual(factor, 1.0)

class RightsAndRatioConflictUnadjustableTest(unittest.TestCase):
    """P8-007 corrections: RIGHTS and RATIO_CONFLICT are written as no-ratio exclusion markers,
    the identical shape DEMERGER already uses (DemergerUnadjustableTest above) -- this is the
    per-pair-verified compute_adjustment_factor/adjusted_close path's own coverage of that same
    exclusion, which UNADJUSTABLE_ACTION_TYPES must independently list (see that constant's
    docstring: deliberately mirrored, not shared, with event_catalogue.py's
    STRUCTURAL_BREAK_ACTION_TYPES)."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy("MMFIN", "2020-06-01", "2020-06-01", 100.0))
        write_fact(self.conn, "corporate_actions", {
            "symbol": "MMFIN", "action_type": RIGHTS, "event_date": "2020-07-22", "knowledge_date": "2020-07-22",
            "ratio_numerator": None, "ratio_denominator": None, "confidence_tier": RIGHTS_EXCLUSION,
            "details": "Rights 1:1 @ Premium Rs 48/-", "source_file": "fixture.json",
        })
        write_fact(self.conn, "bhavcopy", make_bhavcopy("UNIVASTU", "2025-09-01", "2025-09-01", 100.0))
        write_fact(self.conn, "corporate_actions", {
            "symbol": "UNIVASTU", "action_type": RATIO_CONFLICT, "event_date": "2025-10-13", "knowledge_date": "2025-10-13",
            "ratio_numerator": None, "ratio_denominator": None, "confidence_tier": RATIO_CONFLICT_EXCLUSION,
            "details": "subject=2:1 announcement=25357180:11995590", "source_file": "fixture.json",
        })

    def test_rights_in_range_raises_not_silently_ignored(self):
        with self.assertRaises(UnadjustableWindowError):
            compute_adjustment_factor(self.conn, "MMFIN", "2020-06-01", "2020-08-01")

    def test_ratio_conflict_in_range_raises_not_silently_ignored(self):
        with self.assertRaises(UnadjustableWindowError):
            compute_adjustment_factor(self.conn, "UNIVASTU", "2025-09-01", "2025-11-01")

    def test_rights_outside_range_does_not_raise(self):
        factor = compute_adjustment_factor(self.conn, "MMFIN", "2020-06-01", "2020-07-01")
        self.assertEqual(factor, 1.0)

if __name__ == "__main__":
    unittest.main()
