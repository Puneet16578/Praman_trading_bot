"""Phase 7a: SEBI "Orders of AO" listing/detail parsing. Fixtures are real HTML shapes captured
directly from the live site before this module was written (see orders.py's module docstring for
what was confirmed and how) -- network-free.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from datetime import date

from src.ingestion.sebi_orders.orders import (
    ListingCountMismatchError, build_order_row, extract_entity_name,
    ingest_range, order_id_from_detail_url, parse_week_listing, resolve_pdf_url,
)

# Real HTML shape, captured 2026-09-18 for the week of 2020-01-01 to 2020-01-07 (7 real records).
REAL_LISTING_HTML = """
<div class="pagination_inner"><p>1 to 1 of 1 records</p></div>
<table>
<thead>
<tr role='row'>
<th style='width:18%'>Date</th>
<th>Title</th>
</tr>
</thead>
<tbody>
<tr role='row' class='odd'>
<td>Jan 07, 2020</td>
<td><a href="https://www.sebi.gov.in/enforcement/orders/jan-2020/adjudication-order-in-the-matter-of-global-securities-limited_45572.html"  target="_blank" title="Adjudication Order in the matter of Global Securities Limited" class="points"> Adjudication Order in the matter of Global Securities Limited</a>
</tr>
</tbody>
</table>
"""

REAL_TWO_ROW_HTML = """
<div class="pagination_inner"><p>1 to 2 of 2 records</p></div>
<tbody>
<tr role='row' class='odd'>
<td>Jan 07, 2020</td>
<td><a href="https://www.sebi.gov.in/enforcement/orders/jan-2020/adjudication-order-in-the-matter-of-global-securities-limited_45572.html"  target="_blank" title="Adjudication Order in the matter of Global Securities Limited" class="points"> Adjudication Order in the matter of Global Securities Limited</a>
</tr>
<tr role='row' class='even'>
<td>Jan 03, 2020</td>
<td><a href="https://www.sebi.gov.in/enforcement/orders/jan-2020/adjudication-order-in-respect-of-a-b-in-the-matter-of-trading-in-illiquid-stock-options_45510.html"  target="_blank" title="Adjudication Order in respect of  A B in the matter of Trading in Illiquid Stock Options" class="points"> Adjudication Order in respect of A B in the matter of Trading in Illiquid Stock Options</a>
</tr>
</tbody>
"""

REAL_DETAIL_PAGE_HTML = """
<div class='date_value'><h5>Jan 07, 2020</h5></div>
<div class='cover'>
<iframe src='../../../web/?file=/sebi_data/attachdocs/jan-2020/1578379222139.pdf' width='100%' title="Adjudication Order in the matter of Global Securities Limited">
</iframe>
</div>
"""

class ParseWeekListingTest(unittest.TestCase):
    def test_single_real_row_parsed(self):
        rows = parse_week_listing(REAL_LISTING_HTML)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_date_listed"], "2020-01-07")
        self.assertEqual(rows[0]["title"], "Adjudication Order in the matter of Global Securities Limited")
        self.assertTrue(rows[0]["detail_url"].endswith("_45572.html"))

    def test_two_real_rows_parsed(self):
        rows = parse_week_listing(REAL_TWO_ROW_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["event_date_listed"] for r in rows], ["2020-01-07", "2020-01-03"])

    def test_no_count_string_returns_empty_not_error(self):
        self.assertEqual(parse_week_listing("<html><body>no results</body></html>"), [])

    def test_count_exceeding_one_page_raises(self):
        html = '<div class="pagination_inner"><p>1 to 25 of 40 records</p></div>'
        with self.assertRaises(ListingCountMismatchError):
            parse_week_listing(html)

    def test_count_mismatch_with_parsed_rows_raises(self):
        """Page claims 2 records but the row markup only yields 1 -- must raise, not silently
        under-ingest (CLAUDE.md's 'a summary is not trustworthy on its own' rule)."""
        html = REAL_LISTING_HTML.replace("1 to 1 of 1 records", "1 to 2 of 2 records")
        with self.assertRaises(ListingCountMismatchError):
            parse_week_listing(html)

class ExtractEntityNameTest(unittest.TestCase):
    def test_in_the_matter_of_form(self):
        self.assertEqual(extract_entity_name("Adjudication Order in the matter of Global Securities Limited"), "Global Securities Limited")

    def test_in_respect_of_and_in_the_matter_of_form_prefers_trailing_clause(self):
        title = "Adjudication Order in respect of  A B in the matter of Trading in Illiquid Stock Options"
        self.assertEqual(extract_entity_name(title), "Trading in Illiquid Stock Options")

    def test_no_pattern_falls_back_to_whole_title_not_fabricated(self):
        self.assertEqual(extract_entity_name("Some unusual title shape"), "Some unusual title shape")

class OrderIdFromDetailUrlTest(unittest.TestCase):
    def test_extracts_trailing_numeric_id(self):
        self.assertEqual(order_id_from_detail_url("https://www.sebi.gov.in/enforcement/orders/jan-2020/x_45572.html"), "45572")

    def test_no_match_returns_none(self):
        self.assertIsNone(order_id_from_detail_url("https://www.sebi.gov.in/enforcement/orders/jan-2020/x.html"))

class ResolvePdfUrlTest(unittest.TestCase):
    def test_extracts_and_resolves_real_iframe_pattern(self):
        # resolve_pdf_url does its own HTTP GET; test the regex/resolution logic directly via a
        # minimal fake session rather than hitting the network from a fixture test.
        class FakeResponse:
            status_code = 200
            text = REAL_DETAIL_PAGE_HTML
        class FakeSession:
            def get(self, url, timeout=25.0):
                return FakeResponse()
        result = resolve_pdf_url(FakeSession(), "https://www.sebi.gov.in/enforcement/orders/jan-2020/x_45572.html")
        self.assertEqual(result, "https://www.sebi.gov.in/web/?file=/sebi_data/attachdocs/jan-2020/1578379222139.pdf")

    def test_non_200_returns_none(self):
        class FakeResponse:
            status_code = 404
            text = ""
        class FakeSession:
            def get(self, url, timeout=25.0):
                return FakeResponse()
        self.assertIsNone(resolve_pdf_url(FakeSession(), "https://example.com/x.html"))

class BuildOrderRowTest(unittest.TestCase):
    def test_real_shaped_row_built_correctly(self):
        listing_row = {"event_date_listed": "2020-01-07", "title": "Adjudication Order in the matter of Global Securities Limited",
                        "detail_url": "https://www.sebi.gov.in/enforcement/orders/jan-2020/x_45572.html"}
        row = build_order_row(listing_row, "https://www.sebi.gov.in/web/?file=/sebi_data/attachdocs/jan-2020/1578379222139.pdf", "2020-01-07")
        self.assertIsNotNone(row)
        self.assertEqual(row["order_id"], "45572")
        self.assertEqual(row["entity_name"], "Global Securities Limited")
        self.assertIsNone(row["symbol"])
        self.assertEqual(row["event_date"], "2020-01-07")
        self.assertEqual(row["knowledge_date"], "2020-01-07")
        self.assertTrue(row["needs_review"])
        self.assertEqual(row["pdf_url"], "https://www.sebi.gov.in/web/?file=/sebi_data/attachdocs/jan-2020/1578379222139.pdf")

    def test_missing_pdf_url_skips_row_not_fabricated(self):
        listing_row = {"event_date_listed": "2020-01-07", "title": "X", "detail_url": "https://example.com/x_1.html"}
        self.assertIsNone(build_order_row(listing_row, None, "2020-01-07"))

    def test_missing_order_id_skips_row_not_fabricated(self):
        listing_row = {"event_date_listed": "2020-01-07", "title": "X", "detail_url": "https://example.com/no-id-here.html"}
        self.assertIsNone(build_order_row(listing_row, "https://example.com/x.pdf", "2020-01-07"))

class IngestRangeBisectionTest(unittest.TestCase):
    """Confirmed necessary by real data, not speculative: 2020-01-29..31 (3 days) held 36 real
    records, over the one-page cap a fixed 7-day window assumption doesn't protect against."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_overflowing_window_recovers_via_bisection(self):
        overflow_html = '<div class="pagination_inner"><p>1 to 25 of 36 records</p></div>'

        class FakeSession:
            def get(self, url, params=None, timeout=25.0):
                class R:
                    status_code = 200
                    def raise_for_status(self):
                        pass
                if params is not None and params.get("doListing") == "yes":
                    is_full_span = params["fromDate"] == "29-01-2020" and params["toDate"] == "31-01-2020"
                    R.text = overflow_html if is_full_span else REAL_LISTING_HTML
                else:
                    R.text = REAL_DETAIL_PAGE_HTML
                return R()

        listed, written, inserted, skipped, failed = ingest_range(self.conn, FakeSession(), date(2020, 1, 29), date(2020, 1, 31))
        self.assertEqual(failed, [])
        self.assertGreater(written, 0)

    def test_single_day_still_overflowing_reported_as_failed_not_silently_dropped(self):
        overflow_html = '<div class="pagination_inner"><p>1 to 25 of 30 records</p></div>'

        class FakeSession:
            def get(self, url, params=None, timeout=25.0):
                class R:
                    status_code = 200
                    text = overflow_html
                    def raise_for_status(self):
                        pass
                return R()

        listed, written, inserted, skipped, failed = ingest_range(self.conn, FakeSession(), date(2020, 1, 15), date(2020, 1, 15))
        self.assertEqual(failed, [(date(2020, 1, 15), date(2020, 1, 15))])
        self.assertEqual(written, 0)

class WriteThroughStoreTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_built_row_writes_and_reads_back(self):
        from src.bitemporal.store import write_facts
        listing_row = {"event_date_listed": "2020-01-07", "title": "Adjudication Order in the matter of Global Securities Limited",
                        "detail_url": "https://www.sebi.gov.in/enforcement/orders/jan-2020/x_45572.html"}
        row = build_order_row(listing_row, "https://www.sebi.gov.in/web/?file=/sebi_data/attachdocs/jan-2020/1578379222139.pdf", "2020-01-07")
        result = write_facts(self.conn, "sebi_orders", [row])
        self.assertEqual(result.inserted, 1)
        rows = read_as_of(self.conn, "sebi_orders", "2099-01-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["order_id"], "45572")
        self.assertTrue(rows[0]["needs_review"])

if __name__ == "__main__":
    unittest.main()
