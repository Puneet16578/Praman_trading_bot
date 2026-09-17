"""Phase 2: NSE bhavcopy ingestion tests. Network-free -- every test injects a fixture `fetch_fn`
or constructs a `FetchResult` directly from fixture text; nothing here calls NSE. The real network
path (`fetch_bhavcopy`) was verified manually against a live response (see CLAUDE.md / this
session's transcript) and is exercised for real by `scripts/ingest_bhavcopy_sample.py`, not by this
suite.
"""
from __future__ import annotations
from datetime import date
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import latest_as_of, read_as_of
from src.ingestion.nse_market_data.bhavcopy import (
    BhavcopyFetchError, DateIngestionOutcome, FetchResult, GAP, INGESTED, NOT_A_TRADING_DAY,
    classify_against_observed_trading_calendar, ingest_bhavcopy_date, ingest_bhavcopy_dates,
    last_modified_to_ist_date, parse_bhavcopy_rows, validate_csv_content,
)

HTML_ERROR_PAGE = "<!DOCTYPE html>\n<html><body>Not found</body></html>\n"

VALID_CSV = (
    "SYMBOL, SERIES, DATE1, PREV_CLOSE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, LAST_PRICE, "
    "CLOSE_PRICE, AVG_PRICE, TTL_TRD_QNTY, TURNOVER_LACS, NO_OF_TRADES, DELIV_QTY, DELIV_PER\n"
    "FIXTURECO, EQ, 01-Oct-2019, 100.00, 101.00, 105.00, 99.00, 104.00, 104.00, 104.50, 10000, 10.45, 500, 4000, 40.00\n"
    "FIXTURECO, BE, 01-Oct-2019, 50.00, 51.00, 55.00, 49.00, 54.00, 54.00, 54.50, 2000, 1.09, 50, 800, 40.00\n"
    "ILLIQUIDCO, EQ, 01-Oct-2019, 20.00, 20.00, 20.00, 20.00, 20.00, 20.00, 20.00, 100, 0.02, 2, , \n"
    "1018GS2029, GS, 01-Oct-2019, 104.96, 104.98, 104.99, 104.97, 104.97, 104.97, 104.98, 5694, 5.98, 19, -, -\n"
)

MISSING_COLUMNS_CSV = "SYMBOL, SERIES, DATE1\nFIXTURECO, EQ, 01-Oct-2019\n"

def make_fetch_result(raw_text=VALID_CSV, knowledge_date="2019-10-02", trade_date=date(2019, 10, 1)):
    return FetchResult(trade_date=trade_date, raw_text=raw_text, knowledge_date=knowledge_date,
                        source_file="sec_bhavdata_full_01Oct2019bhav.csv")

class ContentValidationTest(unittest.TestCase):
    """P2-001's specific mitigation in this module: never trust 'no exception' as 'valid data'."""

    def test_html_error_page_rejected(self):
        with self.assertRaises(BhavcopyFetchError):
            validate_csv_content(HTML_ERROR_PAGE, date(2018, 1, 2))

    def test_empty_response_rejected(self):
        with self.assertRaises(BhavcopyFetchError):
            validate_csv_content("", date(2018, 1, 2))

    def test_schema_missing_expected_columns_rejected(self):
        with self.assertRaises(BhavcopyFetchError):
            validate_csv_content(MISSING_COLUMNS_CSV, date(2019, 10, 1))

    def test_valid_csv_accepted(self):
        validate_csv_content(VALID_CSV, date(2019, 10, 1))  # must not raise

class LastModifiedConversionTest(unittest.TestCase):
    def test_same_calendar_date_in_gmt_and_ist(self):
        # 18:25 GMT + 5:30 = 23:55 IST -- still the same calendar day
        self.assertEqual(last_modified_to_ist_date("Mon, 07 Sep 2026 18:25:37 GMT"), "2026-09-07")

    def test_crosses_midnight_into_next_ist_calendar_day(self):
        # 19:00 GMT + 5:30 = 00:30 IST -- the NEXT calendar day in IST
        self.assertEqual(last_modified_to_ist_date("Mon, 07 Sep 2026 19:00:00 GMT"), "2026-09-08")

class ParseBhavcopyRowsTest(unittest.TestCase):
    def test_parses_expected_row_count_and_fields(self):
        parsed = parse_bhavcopy_rows(make_fetch_result())
        self.assertEqual(len(parsed.rows), 4)
        self.assertEqual(parsed.skipped_invalid, 0)
        fixtureco_eq = next(r for r in parsed.rows if r["symbol"] == "FIXTURECO" and r["series"] == "EQ")
        self.assertEqual(fixtureco_eq["event_date"], "2019-10-01")
        self.assertEqual(fixtureco_eq["knowledge_date"], "2019-10-02")
        self.assertEqual(fixtureco_eq["close_price"], 104.0)
        self.assertEqual(fixtureco_eq["delivery_qty"], 4000)
        self.assertEqual(fixtureco_eq["delivery_pct"], 40.0)
        self.assertIsInstance(fixtureco_eq["traded_qty"], int)
        self.assertIsInstance(fixtureco_eq["close_price"], float)

    def test_same_symbol_multiple_series_same_date_are_distinct_rows(self):
        parsed = parse_bhavcopy_rows(make_fetch_result())
        fixtureco_rows = [r for r in parsed.rows if r["symbol"] == "FIXTURECO"]
        self.assertEqual({r["series"] for r in fixtureco_rows}, {"EQ", "BE"})
        self.assertEqual(len(fixtureco_rows), 2)

    def test_blank_delivery_fields_parsed_as_none_not_error(self):
        parsed = parse_bhavcopy_rows(make_fetch_result())
        illiquid = next(r for r in parsed.rows if r["symbol"] == "ILLIQUIDCO")
        self.assertIsNone(illiquid["delivery_qty"])
        self.assertIsNone(illiquid["delivery_pct"])

    def test_dash_sentinel_delivery_fields_parsed_as_none_not_error(self):
        parsed = parse_bhavcopy_rows(make_fetch_result())
        gsec = next(r for r in parsed.rows if r["symbol"] == "1018GS2029")
        self.assertIsNone(gsec["delivery_qty"])
        self.assertIsNone(gsec["delivery_pct"])

    def test_row_with_missing_series_is_skipped_not_labeled_literal_nan(self):
        # P2-004: a real NSE file can have a genuinely blank SERIES for some rows (observed:
        # bond/NCD-like instruments on 2019-10-01). Must be skipped and counted, never turned
        # into the literal string "nan".
        csv_with_blank_series = VALID_CSV + (
            "BONDCO, , 01-Oct-2019, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 10, 0.01, 1, -, -\n"
        )
        parsed = parse_bhavcopy_rows(make_fetch_result(raw_text=csv_with_blank_series))
        self.assertEqual(parsed.skipped_invalid, 1)
        self.assertNotIn("nan", {r["series"] for r in parsed.rows})
        self.assertFalse(any(r["symbol"] == "BONDCO" for r in parsed.rows))

class IngestBhavcopyDateTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_valid_fetch_writes_rows_and_reports_ingested(self):
        outcome = ingest_bhavcopy_date(self.conn, date(2019, 10, 1), fetch_fn=lambda d: make_fetch_result())
        self.assertEqual(outcome.status, "ingested")
        self.assertEqual(outcome.rows_inserted, 4)
        self.assertEqual(outcome.rows_skipped_duplicate, 0)

    def test_fetch_error_reported_as_gap_not_raised(self):
        def failing_fetch(d):
            raise BhavcopyFetchError("simulated NSE error page")
        outcome = ingest_bhavcopy_date(self.conn, date(2019, 9, 27), fetch_fn=failing_fetch)
        self.assertEqual(outcome.status, "gap")
        self.assertIn("simulated NSE error page", outcome.reason)

    def test_reingesting_same_data_is_idempotent(self):
        fetch_fn = lambda d: make_fetch_result()
        first = ingest_bhavcopy_date(self.conn, date(2019, 10, 1), fetch_fn=fetch_fn)
        second = ingest_bhavcopy_date(self.conn, date(2019, 10, 1), fetch_fn=fetch_fn)
        self.assertEqual(first.rows_inserted, 4)
        self.assertEqual(second.rows_inserted, 0)
        self.assertEqual(second.rows_skipped_duplicate, 4)
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2099-01-01")), 4)  # no new rows

    def test_already_confirmed_date_skips_the_write_entirely(self):
        """Full-history run support: a weekday that turns out to be a holiday falls back to a day
        this run already confirmed and wrote -- the write must be skipped BEFORE it ever reaches
        write_facts (not merely deduplicated by it), so this never depends on NSE's Last-Modified
        header staying byte-stable across the whole run (scripts/ingest_bhavcopy_full_history.py)."""
        fetch_fn = lambda d: make_fetch_result()
        outcome = ingest_bhavcopy_date(self.conn, date(2019, 10, 1), fetch_fn=fetch_fn,
                                        already_confirmed={"2019-10-01"})
        self.assertEqual(outcome.status, "ingested")
        self.assertEqual(outcome.rows_inserted, 0)
        self.assertEqual(outcome.rows_skipped_duplicate, 0)  # never called write_facts at all
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2099-01-01")), 0)

    def test_already_confirmed_does_not_affect_a_genuinely_new_date(self):
        fetch_fn = lambda d: make_fetch_result()
        outcome = ingest_bhavcopy_date(self.conn, date(2019, 10, 1), fetch_fn=fetch_fn,
                                        already_confirmed={"2020-01-01"})  # unrelated date
        self.assertEqual(outcome.rows_inserted, 4)

    def test_corrected_republished_file_produces_new_row_with_later_knowledge_date(self):
        original = ingest_bhavcopy_date(self.conn, date(2019, 10, 1),
                                         fetch_fn=lambda d: make_fetch_result(knowledge_date="2019-10-02"))
        corrected_csv = VALID_CSV.replace("104.00, 104.00, 104.50", "106.00, 106.00, 105.50")
        corrected = ingest_bhavcopy_date(self.conn, date(2019, 10, 1),
                                          fetch_fn=lambda d: make_fetch_result(raw_text=corrected_csv, knowledge_date="2019-10-05"))
        self.assertEqual(original.rows_inserted, 4)
        self.assertEqual(corrected.rows_inserted, 4)  # new knowledge_date -> new rows, not skipped
        self.assertEqual(corrected.rows_skipped_duplicate, 0)

        latest = latest_as_of(self.conn, "bhavcopy", "2099-01-01", symbol="FIXTURECO", series="EQ")
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["close_price"], 106.0)  # corrected value wins as-of after the correction

        before_correction = latest_as_of(self.conn, "bhavcopy", "2019-10-03", symbol="FIXTURECO", series="EQ")
        self.assertEqual(before_correction[0]["close_price"], 104.0)  # original value still visible before the correction's knowledge_date

class DateMismatchTest(unittest.TestCase):
    """P2-003: NSE's archive can return well-formed CSV for a DIFFERENT date than requested. A
    small (holiday/weekend fallback) gap is accepted and labeled; a large one is rejected as a
    gap and never written."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_small_fallback_gap_is_accepted_and_labeled(self):
        # requested Oct 2 (a Wednesday, simulating a holiday); response is actually dated Oct 1 -- a sane 1-day fallback
        fallback_csv = VALID_CSV.replace("01-Oct-2019", "01-Oct-2019")  # already Oct 1 content
        outcome = ingest_bhavcopy_date(
            self.conn, date(2019, 10, 2),
            fetch_fn=lambda d: make_fetch_result(raw_text=fallback_csv, trade_date=d, knowledge_date="2019-10-02"))
        self.assertEqual(outcome.status, "ingested")
        self.assertEqual(outcome.actual_event_date, "2019-10-01")
        self.assertEqual(outcome.rows_inserted, 4)

    def test_large_mismatch_rejected_as_gap_and_not_written(self):
        # requested 2019-09-30 but the fixture content (like the real anomaly) is dated 2019-06-27
        stale_csv = VALID_CSV.replace("01-Oct-2019", "27-Jun-2019")
        outcome = ingest_bhavcopy_date(
            self.conn, date(2019, 9, 30),
            fetch_fn=lambda d: make_fetch_result(raw_text=stale_csv, trade_date=d, knowledge_date="2019-10-01"))
        self.assertEqual(outcome.status, "gap")
        self.assertIn("anomalous", outcome.reason)
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2099-01-01")), 0)  # nothing written

    def test_response_mixing_multiple_event_dates_rejected(self):
        mixed_csv = VALID_CSV + "OTHERCO, EQ, 02-Oct-2019, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 10, 0.01, 1, 5, 50.0\n"
        outcome = ingest_bhavcopy_date(
            self.conn, date(2019, 10, 1),
            fetch_fn=lambda d: make_fetch_result(raw_text=mixed_csv, trade_date=d))
        self.assertEqual(outcome.status, "gap")
        self.assertIn("distinct event_dates", outcome.reason)

class TradingCalendarClassificationTest(unittest.TestCase):
    """P2-005: a weekend (hard HTML error, no actual_event_date at all) and a holiday (small
    fallback to a different actual_event_date) both mean 'not a trading day' -- neither should be
    reported as a GAP (that label must mean 'a confirmed trading day we failed to retrieve').
    """

    def test_weekend_hard_error_is_not_a_trading_day_not_a_gap(self):
        outcomes = [DateIngestionOutcome(trade_date=date(2026, 8, 29), status="gap", reason="HTML error page")]
        result = classify_against_observed_trading_calendar(outcomes)
        self.assertEqual(result["2026-08-29"], NOT_A_TRADING_DAY)

    def test_holiday_fallback_is_not_a_trading_day_not_ingested(self):
        # requested Sunday 2026-08-30, archive fell back to Friday 2026-08-28
        outcomes = [DateIngestionOutcome(trade_date=date(2026, 8, 30), status="ingested",
                                          actual_event_date="2026-08-28", rows_inserted=100)]
        result = classify_against_observed_trading_calendar(outcomes)
        self.assertEqual(result["2026-08-30"], NOT_A_TRADING_DAY)

    def test_genuine_trading_day_direct_match_is_ingested(self):
        outcomes = [DateIngestionOutcome(trade_date=date(2026, 8, 31), status="ingested",
                                          actual_event_date="2026-08-31", rows_inserted=3000)]
        result = classify_against_observed_trading_calendar(outcomes)
        self.assertEqual(result["2026-08-31"], INGESTED)

    def test_date_confirmed_real_by_a_neighbors_fallback_but_own_fetch_failed_is_a_real_gap(self):
        outcomes = [
            # 2026-08-31's own direct request failed outright
            DateIngestionOutcome(trade_date=date(2026, 8, 31), status="gap", reason="simulated outage"),
            # but 2026-09-01's fallback independently confirms 2026-08-31 IS a real trading day
            DateIngestionOutcome(trade_date=date(2026, 9, 1), status="ingested", actual_event_date="2026-08-31"),
        ]
        result = classify_against_observed_trading_calendar(outcomes)
        self.assertEqual(result["2026-08-31"], GAP)
        self.assertEqual(result["2026-09-01"], NOT_A_TRADING_DAY)  # 2026-09-01 itself was never confirmed as its own trading day

    def test_full_window_reclassification_matches_expected_real_pattern(self):
        # Reproduces the exact Aug29-Sep7 2026 pattern this project observed against real NSE data.
        outcomes = [
            DateIngestionOutcome(trade_date=date(2026, 8, 29), status="gap", reason="HTML error page"),
            DateIngestionOutcome(trade_date=date(2026, 8, 30), status="ingested", actual_event_date="2026-08-28"),
            DateIngestionOutcome(trade_date=date(2026, 8, 31), status="ingested", actual_event_date="2026-08-31"),
            DateIngestionOutcome(trade_date=date(2026, 9, 1), status="ingested", actual_event_date="2026-09-01"),
            DateIngestionOutcome(trade_date=date(2026, 9, 5), status="gap", reason="HTML error page"),
            DateIngestionOutcome(trade_date=date(2026, 9, 6), status="ingested", actual_event_date="2026-09-04"),
            DateIngestionOutcome(trade_date=date(2026, 9, 7), status="ingested", actual_event_date="2026-09-07"),
        ]
        result = classify_against_observed_trading_calendar(outcomes)
        trading_days = {d: c for d, c in result.items() if c != NOT_A_TRADING_DAY}
        self.assertEqual(trading_days, {"2026-08-31": INGESTED, "2026-09-01": INGESTED, "2026-09-07": INGESTED})
        self.assertEqual(sum(1 for c in result.values() if c == GAP), 0)  # no genuine anomalies in this window

class IngestBhavcopyDatesTest(unittest.TestCase):
    def test_reports_one_outcome_per_date_including_gaps(self):
        conn = get_connection(":memory:")
        init_db(conn)

        def fetch_fn(d):
            if d == date(2019, 9, 27):
                raise BhavcopyFetchError("no data before 2019-10-01")
            # VALID_CSV's own event_date is 2019-10-01 -- only matches when requested d is that date
            return make_fetch_result(trade_date=d, knowledge_date="2019-10-02")

        outcomes = ingest_bhavcopy_dates(conn, [date(2019, 9, 27), date(2019, 10, 1)], fetch_fn=fetch_fn)
        self.assertEqual([o.status for o in outcomes], ["gap", "ingested"])

if __name__ == "__main__":
    unittest.main()
