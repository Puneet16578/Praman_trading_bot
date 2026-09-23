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
from src.bitemporal.store import write_fact
from src.ingestion.nse_market_data.corporate_actions import (
    BONUS, CAPITAL_REDUCTION, CAPITAL_REDUCTION_EXCLUSION, CONFIRMED, DEMERGER, DEMERGER_EXCLUSION,
    EX_DATE_FALLBACK, MATCHED_UNCONFIRMED, QUARANTINE, RATIO_CONFLICT, RATIO_CONFLICT_EXCLUSION,
    RIGHTS, RIGHTS_EXCLUSION, SPLIT, announcement_cache_key,
    build_isin_candidates_for_actions, build_rows_and_report, classify_bonus_split,
    collapse_clusters, find_announcement, ingest_corporate_actions, is_capital_reduction_subject,
    is_deferred_text, is_demerger_subject, is_rights_subject, parse_announcement_ratio,
    parse_subject_ratio, resolve_isin_symbol,
)

def make_bhavcopy_row(symbol: str, event_date: str) -> dict:
    return {
        "symbol": symbol, "event_date": event_date, "knowledge_date": event_date,
        "open_price": 100.0, "high_price": 100.0, "low_price": 100.0, "close_price": 100.0,
        "prev_close": 100.0, "traded_qty": 1000, "delivery_qty": 500, "delivery_pct": 50.0,
        "series": "EQ", "source_file": "fixture.csv",
    }

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

    def test_hyphen_attached_bonus_real_ajantpharm_subject(self):
        """P8-007 corrections: the real, live NSE subject for AJANTPHARM's 2022-06-22 bonus is
        'Bonus- 1:2' -- a hyphen attached directly to "Bonus", not the plain 'Bonus 1:2' form the
        original regex required. Confirmed missing before this fix (docs/phase10_p8007_scoping.md
        §1); this is the regression test."""
        result = parse_subject_ratio("Bonus- 1:2")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], BONUS)
        self.assertEqual((result["numerator"], result["denominator"]), (1.0, 2.0))

    def test_bonus_hyphen_no_space_variant(self):
        result = parse_subject_ratio("Bonus-1:2")
        self.assertIsNotNone(result)
        self.assertEqual((result["numerator"], result["denominator"]), (1.0, 2.0))

    def test_bonus_plain_space_form_still_matches(self):
        """The widened separator must not stop matching the original, most common real form."""
        result = parse_subject_ratio("Bonus 1:2")
        self.assertIsNotNone(result)
        self.assertEqual((result["numerator"], result["denominator"]), (1.0, 2.0))

    def test_rights_subject_detected(self):
        """P8-007 corrections: confirmed real case, M&MFIN 2020-07-22."""
        self.assertTrue(is_rights_subject("Rights 1:1 @ Premium Rs 48/-"))
        self.assertFalse(is_rights_subject("Bonus 1:1"))
        self.assertFalse(is_rights_subject("Interim Dividend - Rs 7.10 Per Share"))

    def test_demerger_detected(self):
        self.assertTrue(is_demerger_subject("Demerger"))
        self.assertFalse(is_demerger_subject("Bonus 1:1"))

    def test_hyphenated_demerger_variant_detected(self):
        """Real gap found by audit (docs/phase5_event_catalogue.md Sec.4e): TTML's real subject
        is ' De-Merger', which the bare 'demerger' substring check misses."""
        self.assertTrue(is_demerger_subject(" De-Merger"))
        self.assertTrue(is_demerger_subject("De Merger"))

    def test_scheme_of_arrangement_not_generally_treated_as_demerger(self):
        """Deliberately NOT a general pattern: it also matches real, ratio-bearing, non-demerger
        rows in this store (e.g. RADIOCITY's 'Scheme Of Arrangement - Bonus Ncrps 1:10')."""
        self.assertFalse(is_demerger_subject("Scheme Of Arrangement - Bonus Ncrps 1:10"))
        self.assertFalse(is_demerger_subject(" Scheme Of Arrangement"))

    def test_known_demerger_exception_requires_exact_symbol_and_date(self):
        """IIFL's 2019-05-30 'Scheme Of Arrangement' is a confirmed real demerger with no safe
        general pattern -- handled by exact (symbol, ex_date) enumeration, not a text match."""
        self.assertTrue(is_demerger_subject(" Scheme Of Arrangement", symbol="IIFL", ex_date="2019-05-30"))
        self.assertTrue(is_demerger_subject(" Composite Scheme Of Arrangement", symbol="BSOFT", ex_date="2019-01-24"))
        # same subject, different symbol or date -- must NOT match; this is an enumerated
        # exception, not a license to treat every "scheme of arrangement" as a demerger.
        self.assertFalse(is_demerger_subject(" Scheme Of Arrangement", symbol="IIFL", ex_date="2020-01-01"))
        self.assertFalse(is_demerger_subject(" Scheme Of Arrangement", symbol="OTHERCO", ex_date="2019-05-30"))

    def test_reduction_of_capital_not_treated_as_demerger(self):
        """A capital reduction is a distinct, accurately-labeled action type -- never classified
        as DEMERGER even though both share the same exclusion treatment (see
        is_capital_reduction_subject and docs/phase5_event_catalogue.md Sec.4j)."""
        self.assertFalse(is_demerger_subject("Capital Reduction Pursuant To Nclt Order"))
        self.assertFalse(is_demerger_subject("Reduction Of Capital"))

    def test_capital_reduction_subject_detected(self):
        self.assertTrue(is_capital_reduction_subject("Capital Reduction Pursuant To Nclt Order"))
        self.assertTrue(is_capital_reduction_subject("Reduction Of Capital"))
        self.assertFalse(is_capital_reduction_subject("Bonus 1:1"))
        self.assertFalse(is_capital_reduction_subject("Demerger"))

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

    def test_capital_reduction_becomes_exclusion_marker_accurately_labeled(self):
        """Same exclusion treatment as a demerger (no ratio, excluded not adjusted), but a
        distinct, accurate action_type -- never written as DEMERGER."""
        actions = [{"symbol": "MAXIND", "series": "EQ", "exDate": "26-Jul-2022",
                    "subject": "Capital Reduction Pursuant To Nclt Order"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_type"], CAPITAL_REDUCTION)
        self.assertNotEqual(rows[0]["action_type"], DEMERGER)
        self.assertEqual(rows[0]["confidence_tier"], CAPITAL_REDUCTION_EXCLUSION)
        self.assertIsNone(rows[0]["ratio_numerator"])
        self.assertIsNone(rows[0]["ratio_denominator"])
        self.assertEqual(report.tier_counts[CAPITAL_REDUCTION_EXCLUSION], 1)

    def test_unhandled_action_type_counted_not_written(self):
        actions = [{"symbol": "MAZDOCK", "series": "EQ", "exDate": "06-Jan-2022", "subject": "Interim Dividend - Rs 7.10 Per Share"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(rows, [])
        self.assertEqual(report.unhandled_action_types, 1)

    def test_rights_becomes_exclusion_marker_no_ratio(self):
        """P8-007 corrections: confirmed real case, M&MFIN 2020-07-22, 'Rights 1:1 @ Premium Rs
        48/-' -- previously silently counted as unhandled (indistinguishable from a dividend);
        now written as its own accurately-labeled structural-break exclusion marker."""
        actions = [{"symbol": "M&MFIN", "series": "EQ", "exDate": "22-Jul-2020",
                    "subject": "Rights 1:1 @ Premium Rs 48/-"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_type"], RIGHTS)
        self.assertEqual(rows[0]["confidence_tier"], RIGHTS_EXCLUSION)
        self.assertIsNone(rows[0]["ratio_numerator"])
        self.assertIsNone(rows[0]["ratio_denominator"])
        self.assertEqual(report.unhandled_action_types, 0)  # no longer falls into the generic bucket
        self.assertEqual(report.tier_counts[RIGHTS_EXCLUSION], 1)

    def test_quarantine_becomes_ratio_conflict_exclusion_marker_still_logged(self):
        """P8-007 corrections: a QUARANTINE-tier bonus/split (subject and announcement ratios
        disagree) used to be dropped entirely -- confirmed real case, UNIVASTU 2025-10-13, 'Bonus
        2:1' vs. the announcement's own garbled auto-parsed ratio (docs/phase10_p8007_scoping.md
        §1, same auto-text-quality failure mode already documented for AURIGROW). A real
        corporate action DID happen; it is now written as a structural-break exclusion marker
        (no ratio trusted) instead of silently vanishing, and still logged in `quarantined` for
        review, unchanged."""
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:1"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 10...")]}
        rows, report = build_rows_and_report(actions, announcements, "test.json")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_type"], RATIO_CONFLICT)
        self.assertEqual(rows[0]["confidence_tier"], RATIO_CONFLICT_EXCLUSION)
        self.assertIsNone(rows[0]["ratio_numerator"])
        self.assertIsNone(rows[0]["ratio_denominator"])
        self.assertEqual(len(report.quarantined), 1)
        self.assertEqual(report.quarantined[0]["symbol"], symbol)
        self.assertEqual(report.tier_counts[RATIO_CONFLICT_EXCLUSION], 1)
        self.assertNotIn(QUARANTINE, report.tier_counts)  # the raw QUARANTINE tier no longer
                                                            # appears in tier_counts -- it's
                                                            # renamed/rewritten to the exclusion
                                                            # tier at the point of writing

    def test_non_eq_series_skipped(self):
        actions = [{"symbol": "717GS2028", "series": "GS", "exDate": "06-Jan-2022", "subject": "Interest Payment"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(rows, [])
        self.assertEqual(report.unhandled_action_types, 0)  # never even considered -- filtered before the parser

    def test_isin_resolution_rewrites_symbol_to_the_one_actually_trading_on_ex_date(self):
        """P8-010 fix: real case, HEG renamed to HEGAM around its 2026-09-07 demerger. NSE's live
        feed reports HEGAM even for HEG's own pre-rename 2024-10-18 split -- resolved back to HEG
        (the symbol this project's own bhavcopy needs it filed under) via isin_candidates."""
        isin_candidates = {
            "INE545A01024": {"HEG": ("2019-10-01", "2026-09-21"), "HEGAM": ("2026-09-22", "2026-09-22")},
        }
        actions = [{"symbol": "HEGAM", "series": "EQ", "exDate": "18-Oct-2024", "subject": "Demerger",
                    "isin": "INE545A01024"}]
        rows, report = build_rows_and_report(actions, {}, "test.json", isin_candidates=isin_candidates)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "HEG")

    def test_no_isin_candidates_leaves_symbol_unchanged(self):
        """Default (isin_candidates=None) behavior is unchanged from before P8-010 -- backward
        compatible with every existing fixture that never passes this parameter."""
        actions = [{"symbol": "HEGAM", "series": "EQ", "exDate": "18-Oct-2024", "subject": "Demerger",
                    "isin": "INE545A01024"}]
        rows, report = build_rows_and_report(actions, {}, "test.json")
        self.assertEqual(rows[0]["symbol"], "HEGAM")

class ResolveIsinSymbolTest(unittest.TestCase):
    def test_picks_candidate_whose_window_covers_ex_date(self):
        candidates = {"HEG": ("2019-10-01", "2026-09-21"), "HEGAM": ("2026-09-22", "2026-09-22")}
        self.assertEqual(resolve_isin_symbol("HEGAM", date(2024, 10, 18), candidates), "HEG")

    def test_raw_symbol_kept_when_its_own_window_matches(self):
        candidates = {"HEG": ("2019-10-01", "2026-09-21"), "HEGAM": ("2026-09-22", "2026-09-22")}
        self.assertEqual(resolve_isin_symbol("HEGAM", date(2026, 9, 22), candidates), "HEGAM")

    def test_falls_back_to_raw_symbol_when_no_window_covers(self):
        candidates = {"HEG": ("2019-10-01", "2026-09-21")}
        self.assertEqual(resolve_isin_symbol("HEGAM", date(2030, 1, 1), candidates), "HEGAM")

    def test_empty_candidates_is_a_no_op(self):
        self.assertEqual(resolve_isin_symbol("ANY", date(2024, 1, 1), {}), "ANY")

class BuildIsinCandidatesForActionsTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEG", "2020-01-01"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEG", "2026-09-21"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEGAM", "2026-09-22"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("RELIANCE", "2020-01-01"))

    def test_multi_symbol_isin_present_in_actions_gets_date_ranges(self):
        isin_map = {"HEG": "INE545A01024", "HEGAM": "INE545A01024", "RELIANCE": "INE002A01018"}
        actions = [{"symbol": "HEGAM", "isin": "INE545A01024", "exDate": "18-Oct-2024"}]
        candidates = build_isin_candidates_for_actions(self.conn, actions, isin_map)
        self.assertEqual(candidates, {
            "INE545A01024": {"HEG": ("2020-01-01", "2026-09-21"), "HEGAM": ("2026-09-22", "2026-09-22")},
        })

    def test_single_symbol_isin_not_included(self):
        isin_map = {"HEG": "INE545A01024", "HEGAM": "INE545A01024", "RELIANCE": "INE002A01018"}
        actions = [{"symbol": "RELIANCE", "isin": "INE002A01018", "exDate": "01-Jan-2020"}]
        candidates = build_isin_candidates_for_actions(self.conn, actions, isin_map)
        self.assertEqual(candidates, {})

    def test_no_actions_with_isin_returns_empty(self):
        isin_map = {"HEG": "INE545A01024", "HEGAM": "INE545A01024"}
        candidates = build_isin_candidates_for_actions(self.conn, [{"symbol": "HEG"}], isin_map)
        self.assertEqual(candidates, {})

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

    def test_quarantined_row_written_as_ratio_conflict_exclusion_not_a_trusted_ratio(self):
        """P8-007 corrections: a QUARANTINE-tier disagreement now reaches the store as a
        RATIO_CONFLICT exclusion marker (no ratio) rather than never reaching it at all -- see
        BuildRowsAndReportTest.test_quarantine_becomes_ratio_conflict_exclusion_marker_still_logged
        for the unit-level version of this same behavior change."""
        symbol, ex_date_str = "TESTCO", "01-Mar-2021"
        key = announcement_cache_key(symbol, date(2021, 3, 1))
        actions = [{"symbol": symbol, "series": "EQ", "exDate": ex_date_str, "subject": "Bonus 1:1"}]
        announcements = {key: [ann("2021-01-20 10:00:00", "Bonus", "...bonus at the ratio of 1 : 10...")]}
        report, write_result = ingest_corporate_actions(self.conn, actions, announcements, "test.json")
        self.assertEqual(write_result.inserted, 1)
        stored = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol=symbol)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["action_type"], RATIO_CONFLICT)
        self.assertEqual(stored[0]["confidence_tier"], RATIO_CONFLICT_EXCLUSION)
        self.assertIsNone(stored[0]["ratio_numerator"])
        self.assertEqual(len(report.quarantined), 1)

    def test_isin_map_resolves_symbol_end_to_end(self):
        """P8-010 fix, full path: HEGAM-labeled action with an ex_date inside HEG's own bhavcopy
        window is written under HEG, not HEGAM, when isin_map is supplied."""
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEG", "2020-01-01"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEG", "2026-09-21"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEGAM", "2026-09-22"))
        isin_map = {"HEG": "INE545A01024", "HEGAM": "INE545A01024"}
        actions = [{"symbol": "HEGAM", "series": "EQ", "exDate": "18-Oct-2024", "subject": "Demerger",
                    "isin": "INE545A01024"}]
        report, write_result = ingest_corporate_actions(self.conn, actions, {}, "test.json", isin_map=isin_map)
        self.assertEqual(write_result.inserted, 1)
        heg_rows = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="HEG")
        hegam_rows = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="HEGAM")
        self.assertEqual(len(heg_rows), 1)
        self.assertEqual(len(hegam_rows), 0)

    def test_no_isin_map_keeps_prior_behavior(self):
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row("HEG", "2020-01-01"))
        actions = [{"symbol": "HEGAM", "series": "EQ", "exDate": "18-Oct-2024", "subject": "Demerger",
                    "isin": "INE545A01024"}]
        report, write_result = ingest_corporate_actions(self.conn, actions, {}, "test.json")
        self.assertEqual(write_result.inserted, 1)
        hegam_rows = read_as_of(self.conn, "corporate_actions", "2099-01-01", symbol="HEGAM")
        self.assertEqual(len(hegam_rows), 1)

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
