"""Phase 3 (Session A): corporate-actions tiering, matching, and ingestion. Fixture data only,
network-free -- reproduces the real failure/success patterns found during source evaluation
(KITEX same-session correction, UEL cross-action window contamination, AURIGROW subject-vs-
announcement disagreement) as small, explicit fixtures rather than depending on cached network
data.
"""
from __future__ import annotations
from datetime import date
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.ingestion.nse_market_data.corporate_actions import (
    BONUS, CONFIRMED, DEMERGER, DEMERGER_EXCLUSION, EX_DATE_FALLBACK, MATCHED_UNCONFIRMED,
    QUARANTINE, SPLIT, announcement_cache_key, build_rows_and_report, classify_bonus_split,
    collapse_clusters, find_announcement, ingest_corporate_actions, is_deferred_text,
    is_demerger_subject, parse_announcement_ratio, parse_subject_ratio,
)

def ann(sort_date: str, desc: str, text: str) -> dict:
    return {"sort_date": sort_date, "desc": desc, "attchmntText": text}

class ParseSubjectRatioTest(unittest.TestCase):
    def test_bonus(self):
        result = parse_subject_ratio("Bonus 1:3")
        self.assertEqual(result["type"], BONUS)
        self.assertEqual((result["numerator"], result["denominator"]), (1.0, 3.0))
        self.assertAlmostEqual(result["factor"], 4 / 3)

    def test_split(self):
        result = parse_subject_ratio("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share")
        self.assertEqual(result["type"], SPLIT)
        self.assertEqual((result["numerator"], result["denominator"]), (10.0, 2.0))
        self.assertEqual(result["factor"], 5.0)

    def test_dividend_unhandled(self):
        self.assertIsNone(parse_subject_ratio("Interim Dividend - Rs 7.10 Per Share"))

    def test_demerger_detected(self):
        self.assertTrue(is_demerger_subject("Demerger"))
        self.assertFalse(is_demerger_subject("Bonus 1:1"))

class ParseAnnouncementRatioTest(unittest.TestCase):
    def test_bonus_colon_form(self):
        result = parse_announcement_ratio("...bonus at the ratio of 4 : 1, i.e 4 Equity Shares...", BONUS)
        self.assertAlmostEqual(result["factor"], 5.0)

    def test_split_optional_currency_prefix(self):
        # the dominant v1 gap: no "Rs."/"Re." before the number
        text = "...has considered and approved subdivision of 100 equity shares of 10 each into 500 equity shares of 2 each."
        result = parse_announcement_ratio(text, SPLIT)
        self.assertEqual(result["factor"], 5.0)

    def test_split_face_value_only_fallback(self):
        text = "...sub-division (split) of 1 existing equity share having face value of Rs. 5/- each into 5 equity shares having face value of Re. 1/- each..."
        result = parse_announcement_ratio(text, SPLIT)
        self.assertEqual(result["factor"], 5.0)

    def test_bonus_ration_typo_tolerance(self):
        text = "...has recommended the issue of Bonus shares...in the ration of 1:1 i.e. 1 bonus equity share..."
        result = parse_announcement_ratio(text, BONUS)
        self.assertEqual(result["factor"], 2.0)

    def test_generic_no_detail_returns_none(self):
        self.assertIsNone(parse_announcement_ratio("Kuantum Papers Limited has informed the Exchange about Stock split", SPLIT))

    def test_internal_mismatch_rejected(self):
        text = "...subdivision of 1 equity shares of Rs. 10 each into 964157160 equity shares of Re. 1 each."
        result = parse_announcement_ratio(text, SPLIT)
        self.assertIsNone(result["factor"])
        self.assertIn("INTERNAL_MISMATCH", result["raw"])

class DeferredLanguageTest(unittest.TestCase):
    def test_deferred_rejected(self):
        self.assertTrue(is_deferred_text("The Board of Directors has deferred the proposal pertaining to issue of Bonus Shares."))

    def test_scheduled_to_consider_rejected(self):
        self.assertTrue(is_deferred_text("...the Board of Directors...shall inter-alia, also consider the proposal for declaration of Bonus Issue..."))

    def test_approved_text_not_flagged(self):
        self.assertFalse(is_deferred_text("...has considered and approved bonus at the ratio of 1 : 3..."))

class ClusterCollapseTest(unittest.TestCase):
    def test_kitex_same_session_typo_correction(self):
        """Real case: a typo'd ratio corrected 38 seconds later, same board meeting."""
        matches = [
            ann("2024-11-22 11:21:41", "Bonus", "...bonus at the ratio of 2 : 2..."),
            ann("2024-11-22 11:59:59", "Bonus", "...bonus at the ratio of 2 : 1..."),
        ]
        collapsed = collapse_clusters(matches)
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(collapsed[0]["sort_date"], "2024-11-22 11:59:59")

    def test_bepl_gap_outside_one_hour_not_collapsed(self):
        """Real case: two announcements 1h51m apart are NOT the same correction cluster."""
        matches = [
            ann("2023-05-21 18:59:27", "Bonus", "ratio of 1 : 2"),
            ann("2023-05-21 20:50:20", "Bonus", "ratio of 2:1"),
        ]
        collapsed = collapse_clusters(matches)
        self.assertEqual(len(collapsed), 2)

class FindAnnouncementTest(unittest.TestCase):
    def test_uel_cross_action_window_contamination_avoided(self):
        """Real case: two separate bonus rounds four months apart. The one relevant to THIS
        ex-date (Oct 10) must be picked, not the earlier, unrelated round (for a different,
        earlier ex-date in May)."""
        announcements = [
            ann("2025-04-19 17:27:24", "Bonus", "...bonus at the ratio of 17 : 25..."),
            ann("2025-08-26 12:17:43", "Bonus", "...bonus at the ratio of 2 : 1..."),
        ]
        match, gap_days = find_announcement(announcements, date(2025, 10, 10), BONUS)
        self.assertEqual(match["sort_date"], "2025-08-26 12:17:43")
        self.assertEqual(gap_days, (date(2025, 10, 10) - date(2025, 8, 26)).days)

    def test_deferred_candidate_skipped_in_favor_of_real_approval(self):
        announcements = [
            ann("2021-04-23 10:00:00", "Bonus", "...shall inter-alia, also consider the proposal for declaration of Bonus Issue..."),
            ann("2021-05-03 11:43:42", "Bonus", "...Recommended the Bonus Issue...in the proportion of 1 (One) Equity Share...for every 2 (Two)..."),
        ]
        match, gap_days = find_announcement(announcements, date(2021, 6, 10), BONUS)
        self.assertEqual(match["sort_date"], "2021-05-03 11:43:42")

    def test_no_match_returns_none(self):
        match, gap_days = find_announcement([], date(2021, 6, 10), BONUS)
        self.assertIsNone(match)
        self.assertIsNone(gap_days)

class ClassifyBonusSplitTest(unittest.TestCase):
    def test_confirmed(self):
        subj = parse_subject_ratio("Bonus 1:3")
        announcements = [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 3...")]
        result = classify_bonus_split(subj, date(2021, 3, 1), announcements)  # gap = 40 days, in range
        self.assertEqual(result.tier, CONFIRMED)
        self.assertEqual(result.knowledge_date, "2021-01-20")

    def test_matched_unconfirmed_generic_text(self):
        subj = parse_subject_ratio("Bonus 1:3")
        announcements = [ann("2021-01-20 10:00:00", "Bonus", "Some Company has informed the Exchange about Bonus")]
        result = classify_bonus_split(subj, date(2021, 3, 1), announcements)
        self.assertEqual(result.tier, MATCHED_UNCONFIRMED)
        self.assertEqual(result.knowledge_date, "2021-01-20")

    def test_ex_date_fallback_no_announcement(self):
        subj = parse_subject_ratio("Bonus 1:3")
        result = classify_bonus_split(subj, date(2021, 3, 1), [])
        self.assertEqual(result.tier, EX_DATE_FALLBACK)
        self.assertEqual(result.knowledge_date, "2021-03-01")
        self.assertFalse(result.downgraded_for_gap)

    def test_ex_date_fallback_downgraded_for_gap_out_of_range(self):
        subj = parse_subject_ratio("Bonus 1:3")
        # gap = 10 days -- below the measured MIN_GAP_DAYS=28, doesn't look like a real board-to-ex-date sequence
        announcements = [ann("2021-02-19 10:00:00", "Bonus", "...bonus at the ratio of 1 : 3...")]
        result = classify_bonus_split(subj, date(2021, 3, 1), announcements)
        self.assertEqual(result.tier, EX_DATE_FALLBACK)
        self.assertTrue(result.downgraded_for_gap)
        self.assertEqual(result.knowledge_date, "2021-03-01")

    def test_quarantine_on_disagreement(self):
        subj = parse_subject_ratio("Bonus 1:1")
        announcements = [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 10...")]
        result = classify_bonus_split(subj, date(2021, 3, 1), announcements)
        self.assertEqual(result.tier, QUARANTINE)

class BuildRowsAndReportTest(unittest.TestCase):
    def test_demerger_becomes_exclusion_marker_no_ratio(self):
        actions = [{"symbol": "RELIANCE", "series": "EQ", "exDate": "20-Jul-2023", "subject": "Demerger"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_type"], DEMERGER)
        self.assertEqual(rows[0]["confidence_tier"], DEMERGER_EXCLUSION)
        self.assertIsNone(rows[0]["ratio_numerator"])
        self.assertIsNone(rows[0]["ratio_denominator"])
        self.assertEqual(rows[0]["knowledge_date"], "2023-07-20")
        self.assertEqual(report.tier_counts[DEMERGER_EXCLUSION], 1)

    def test_unhandled_action_type_counted_not_written(self):
        actions = [{"symbol": "MAZDOCK", "series": "EQ", "exDate": "06-Jan-2022", "subject": "Interim Dividend - Rs 7.10 Per Share"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(rows, [])
        self.assertEqual(report.unhandled_action_types, 1)

    def test_quarantine_row_not_in_output_but_logged(self):
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:1"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 10...")]}
        rows, report = build_rows_and_report(actions, announcements, "test.json")
        self.assertEqual(rows, [])
        self.assertEqual(len(report.quarantined), 1)
        self.assertEqual(report.quarantined[0]["symbol"], symbol)

    def test_non_eq_series_skipped(self):
        actions = [{"symbol": "717GS2028", "series": "GS", "exDate": "06-Jan-2022", "subject": "Interest Payment"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(rows, [])
        self.assertEqual(report.unhandled_action_types, 0)  # never even considered -- filtered before the parser

class IngestCorporateActionsTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_confirmed_row_written_and_queryable(self):
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:3"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 3...")]}
        report, write_result = ingest_corporate_actions(self.conn, actions, announcements, "test.json")
        self.assertEqual(report.tier_counts[CONFIRMED], 1)
        self.assertEqual(write_result.inserted, 1)
        rows = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol=symbol)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["confidence_tier"], CONFIRMED)

    def test_quarantined_row_never_reaches_the_store(self):
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:1"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 10...")]}
        report, write_result = ingest_corporate_actions(self.conn, actions, announcements, "test.json")
        self.assertEqual(write_result.inserted, 0)
        self.assertEqual(len(read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol=symbol)), 0)
        self.assertEqual(len(report.quarantined), 1)

    def test_reingesting_identical_data_is_idempotent(self):
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:3"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 3...")]}
        ingest_corporate_actions(self.conn, actions, announcements, "test.json")
        _, second = ingest_corporate_actions(self.conn, actions, announcements, "test.json")
        self.assertEqual(second.inserted, 0)
        self.assertEqual(second.skipped_duplicate, 1)

if __name__ == "__main__":
    unittest.main()
