"""Phase 5: event catalogue tests. Fixture data only (synthetic, clearly not real NSE data) -- the
real-data cross-validation against actual compute_adjustment_factor()/adjusted_close() calls lives
in tests/test_event_catalogue_real_data_guard.py, per this project's rule that fixture tests prove
the plumbing, not the guard against real-world messiness.
"""
from __future__ import annotations
from datetime import date, timedelta
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_fact, write_facts
from src.ingestion.nse_market_data.corporate_actions import (
    BONUS, CAPITAL_REDUCTION, CAPITAL_REDUCTION_EXCLUSION, CONFIRMED, DEMERGER, DEMERGER_EXCLUSION,
    RATIO_CONFLICT, RATIO_CONFLICT_EXCLUSION, RIGHTS, RIGHTS_EXCLUSION, SPLIT,
)
from src.signals.event_catalogue import (
    LateAnnouncedActionError, TRAILING_WINDOW, build_symbol_history,
    compute_daily_stats, _assert_ordering_guarantee, _percentile_rank, _return,
)

def _dates(n: int, start: date = date(2021, 1, 1)) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]

def make_bhavcopy_row(symbol, event_date, close_price, traded_qty=10000, delivery_pct=40.0, knowledge_date=None, **overrides):
    row = {
        "symbol": symbol, "event_date": event_date, "knowledge_date": knowledge_date or event_date,
        "open_price": close_price, "high_price": close_price, "low_price": close_price, "close_price": close_price,
        "prev_close": close_price, "traded_qty": traded_qty, "delivery_qty": int(traded_qty * (delivery_pct or 0) / 100) if delivery_pct is not None else None,
        "delivery_pct": delivery_pct, "series": "EQ", "source_file": "fixture.csv",
    }
    row.update(overrides)
    return row

def make_action(symbol, action_type, event_date, knowledge_date, ratio_numerator=None, ratio_denominator=None, confidence_tier=CONFIRMED, details=None):
    return {
        "symbol": symbol, "action_type": action_type, "event_date": event_date, "knowledge_date": knowledge_date,
        "ratio_numerator": ratio_numerator, "ratio_denominator": ratio_denominator,
        "confidence_tier": confidence_tier, "details": details, "source_file": "fixture.csv",
    }

class OrderingGuardTest(unittest.TestCase):
    def test_passes_on_correctly_ordered_actions(self):
        actions = [make_action("ABC", BONUS, "2021-02-01", "2021-01-15", 1, 1)]
        _assert_ordering_guarantee(actions, "ABC")  # must not raise

    def test_raises_on_knowledge_date_after_event_date(self):
        actions = [make_action("ABC", BONUS, "2021-02-01", "2021-02-15", 1, 1)]  # knowledge AFTER event
        with self.assertRaises(LateAnnouncedActionError):
            _assert_ordering_guarantee(actions, "ABC")

class PercentileRankTest(unittest.TestCase):
    def test_middle_value(self):
        pop = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertEqual(_percentile_rank(3.0, pop), 50.0)

    def test_lowest_value(self):
        pop = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(_percentile_rank(1.0, pop), 100.0 * 0.5 / 3)

    def test_highest_value(self):
        pop = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(_percentile_rank(3.0, pop), 100.0 * 2.5 / 3)

class SymbolHistoryReturnTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_plain_return_no_actions(self):
        dates = _dates(5)
        rows = [make_bhavcopy_row("ABC", d, close_price=100.0 * (1 + 0.01 * i)) for i, d in enumerate(dates)]
        write_facts(self.conn, "bhavcopy", rows)
        from src.signals.event_catalogue import build_symbol_history
        hist = build_symbol_history(self.conn, "ABC")
        r = _return(hist, dates[0], dates[1], as_of=dates[1])
        self.assertAlmostEqual(r, 0.01)

    def test_bonus_and_split_same_day_cancels_to_zero_return_bajfinance_shape(self):
        """Mirrors the hand-verified real BAJFINANCE case: a 4:1 bonus (factor 5) plus a 2:1 split
        (factor 2) on the same ex-date, combined factor 10 -- a pure mechanical event with NO real
        price move must show return_1d == 0, not a ~90% 'crash'."""
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("BAJFINANCE", d0, close_price=8000.0),
            make_bhavcopy_row("BAJFINANCE", d1, close_price=800.0),  # exactly 1/10th -- pure mechanical
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("BAJFINANCE", BONUS, d1, d0, ratio_numerator=4, ratio_denominator=1),
            make_action("BAJFINANCE", SPLIT, d1, d0, ratio_numerator=2, ratio_denominator=1),
        ])
        hist = build_symbol_history(self.conn, "BAJFINANCE")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertAlmostEqual(r, 0.0, places=9)

    def test_real_price_move_survives_adjustment(self):
        """Same mechanical 10x adjustment, but WITH a genuine 5% real move underneath -- the
        adjusted return must show 5%, not 0% and not -90%."""
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("XYZ", d0, close_price=8000.0),
            make_bhavcopy_row("XYZ", d1, close_price=840.0),  # 800 (pure mechanical) * 1.05
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("XYZ", BONUS, d1, d0, ratio_numerator=4, ratio_denominator=1),
            make_action("XYZ", SPLIT, d1, d0, ratio_numerator=2, ratio_denominator=1),
        ])
        hist = build_symbol_history(self.conn, "XYZ")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertAlmostEqual(r, 0.05, places=9)

    def test_demerger_window_excluded_not_adjusted(self):
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("DEM", d0, close_price=1000.0),
            make_bhavcopy_row("DEM", d1, close_price=600.0),  # would look like a 40% crash
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("DEM", DEMERGER, d1, d1, confidence_tier=DEMERGER_EXCLUSION, details="Demerger of Whatever Ltd"),
        ])
        hist = build_symbol_history(self.conn, "DEM")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertIsNone(r, "A demerger-spanning window must be excluded, never computed on raw prices.")

    def test_capital_reduction_window_excluded_same_as_demerger(self):
        """A distinct, accurately-labeled action_type (not DEMERGER) -- but the same exclusion
        treatment, since a share-swap or NCLT-ordered capital reduction is the same kind of
        structural, no-disclosed-ratio price break (docs/phase5_event_catalogue.md Sec.4j)."""
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("CAPRED", d0, close_price=1000.0),
            make_bhavcopy_row("CAPRED", d1, close_price=600.0),
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("CAPRED", CAPITAL_REDUCTION, d1, d1, confidence_tier=CAPITAL_REDUCTION_EXCLUSION,
                        details="Capital Reduction Pursuant To Nclt Order"),
        ])
        hist = build_symbol_history(self.conn, "CAPRED")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertIsNone(r, "A capital-reduction-spanning window must be excluded, same as a demerger.")

    def test_rights_window_excluded_same_as_demerger(self):
        """P8-007 corrections: a Rights issue has a disclosed ratio, but this project does not
        attempt rights-issue price adjustment (a different mechanism than bonus/split -- see
        is_rights_subject) -- same exclusion treatment as a demerger, real case M&MFIN 2020-07-22."""
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("MMFIN", d0, close_price=1000.0),
            make_bhavcopy_row("MMFIN", d1, close_price=675.0),
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("MMFIN", RIGHTS, d1, d1, confidence_tier=RIGHTS_EXCLUSION,
                        details="Rights 1:1 @ Premium Rs 48/-"),
        ])
        hist = build_symbol_history(self.conn, "MMFIN")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertIsNone(r, "A rights-spanning window must be excluded, same as a demerger.")

    def test_ratio_conflict_window_excluded_same_as_demerger(self):
        """P8-007 corrections: a QUARANTINE-tier bonus/split disagreement (subject and announcement
        ratios don't agree) is written as a RATIO_CONFLICT exclusion marker -- real case UNIVASTU
        2025-10-13, no ratio trusted enough to adjust by, same exclusion treatment as a demerger."""
        d0, d1 = _dates(2)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("UNIVASTU", d0, close_price=1000.0),
            make_bhavcopy_row("UNIVASTU", d1, close_price=333.0),
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("UNIVASTU", RATIO_CONFLICT, d1, d1, confidence_tier=RATIO_CONFLICT_EXCLUSION,
                        details="subject=2:1 announcement=25357180:11995590"),
        ])
        hist = build_symbol_history(self.conn, "UNIVASTU")
        r = _return(hist, d0, d1, as_of=d1)
        self.assertIsNone(r, "A ratio-conflict-spanning window must be excluded, same as a demerger.")

    def test_demerger_outside_window_does_not_affect_an_unrelated_return(self):
        d0, d1, d2 = _dates(3)
        write_facts(self.conn, "bhavcopy", [
            make_bhavcopy_row("DEM2", d0, close_price=1000.0),
            make_bhavcopy_row("DEM2", d1, close_price=1010.0),
            make_bhavcopy_row("DEM2", d2, close_price=600.0),
        ])
        write_facts(self.conn, "corporate_actions", [
            make_action("DEM2", DEMERGER, d2, d2, confidence_tier=DEMERGER_EXCLUSION),
        ])
        hist = build_symbol_history(self.conn, "DEM2")
        r_before = _return(hist, d0, d1, as_of=d1)  # doesn't touch the demerger date at all
        self.assertAlmostEqual(r_before, 0.01)

    def test_republished_bhavcopy_correction_is_visible_only_after_its_own_knowledge_date(self):
        """The bitemporal consequence stated in the module docstring and phase doc: an as-of query
        before the correction's knowledge_date sees the ORIGINAL value; as-of on/after sees the
        corrected one. Both are 'correct' answers to different questions asked at different times."""
        d0, d1 = _dates(2)
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("COR", d1, close_price=100.0, knowledge_date=d1))
        corrected_kd = (date.fromisoformat(d1) + timedelta(days=3)).isoformat()
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("COR", d1, close_price=105.0, knowledge_date=corrected_kd))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("COR", d0, close_price=100.0, knowledge_date=d0))

        hist = build_symbol_history(self.conn, "COR")
        before_correction = hist.price_row_as_of(d1, as_of=d1)
        after_correction = hist.price_row_as_of(d1, as_of=corrected_kd)
        self.assertEqual(before_correction["close_price"], 100.0)
        self.assertEqual(after_correction["close_price"], 105.0)

class ComputeDailyStatsTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_needs_a_full_trailing_window_before_emitting_anything(self):
        dates = _dates(TRAILING_WINDOW)  # exactly TRAILING_WINDOW days -- one short of enough
        write_facts(self.conn, "bhavcopy", [make_bhavcopy_row("SHORT", d, 100.0) for d in dates])
        hist = build_symbol_history(self.conn, "SHORT")
        stats = compute_daily_stats(hist)
        self.assertEqual(stats, [], "Must not emit a stat without a full trailing window's worth of prior history.")

    def test_emits_once_window_plus_one_is_available(self):
        dates = _dates(TRAILING_WINDOW + 2)
        write_facts(self.conn, "bhavcopy", [make_bhavcopy_row("LONG", d, 100.0 + i) for i, d in enumerate(dates)])
        hist = build_symbol_history(self.conn, "LONG")
        stats = compute_daily_stats(hist)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0].event_date, dates[-1])

    def test_flat_series_gives_zero_zscore_and_no_volume_flag(self):
        dates = _dates(TRAILING_WINDOW + 2)
        write_facts(self.conn, "bhavcopy", [make_bhavcopy_row("FLAT", d, 100.0, traded_qty=5000) for d in dates])
        hist = build_symbol_history(self.conn, "FLAT")
        stat = compute_daily_stats(hist)[0]
        self.assertEqual(stat.return_1d, 0.0)
        self.assertIsNone(stat.zscore_60d)  # stdev is 0 -- explicitly None, never a divide-by-zero
        self.assertAlmostEqual(stat.volume_ratio, 1.0)

    def test_predicted_empty_a_pure_bonus_produces_no_unusual_move(self):
        """The predicted-empty sanity check pattern, exercised here as a unit test: a large bonus
        with NO real underlying price move must never register as an unusual return, however large
        the raw/unadjusted jump would have looked."""
        dates = _dates(TRAILING_WINDOW + 2)
        rows = [make_bhavcopy_row("PUREBONUS", d, 100.0) for d in dates[:-1]]
        rows.append(make_bhavcopy_row("PUREBONUS", dates[-1], 20.0))  # exactly 1/5th, a 4:1 bonus, no real move
        write_facts(self.conn, "bhavcopy", rows)
        write_facts(self.conn, "corporate_actions", [
            make_action("PUREBONUS", BONUS, dates[-1], dates[-2], ratio_numerator=4, ratio_denominator=1),
        ])
        hist = build_symbol_history(self.conn, "PUREBONUS")
        stat = compute_daily_stats(hist)[0]
        self.assertAlmostEqual(stat.return_1d, 0.0, places=9)
        self.assertIsNone(stat.zscore_60d)  # flat trailing distribution again (all prior returns are 0)

if __name__ == "__main__":
    unittest.main()
