"""SEBI enforcement-order ingestion (Phase 7a) -- "Orders of AO" (Adjudicating Officer, smid=6),
the category that actually carries market-manipulation/fraud/insider-trading adjudications against
named entities, confirmed by direct inspection of the real page (not assumed from the category
label alone): real titles sampled include "...market manipulation using social media in the scrip
of Moksh Ornaments Limited", "...front running activities by...", "...insider trading activity of
an entity in the scrip of Jindal Steel and Power Limited".

Confirmed empirically before writing this module:
- The listing at https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=6
  is plain server-rendered HTML (a `requests.get()`, no JS execution needed) despite the visible
  UI using JS-driven pagination controls.
- `fromDate`/`toDate` (DD-MM-YYYY) ARE honored server-side as real GET query params, confirmed by
  the page's own "X to Y of Z records" count changing correctly (12,002 unfiltered; 71 for
  Jan 2020; 7 for the first week of Jan 2020).
- The JS-only pagination (`searchFormNewsList('n', N)`) could NOT be replicated via a `nextValue`
  GET param (tested directly -- returns page 1 regardless). Rather than reverse-engineer the
  POST/session-state pagination mechanism, this module sidesteps it: it walks the date range in
  7-day windows, chosen because a real sampled week (7 orders) sits comfortably under the 25-per-
  page cap for ordinary periods. `ingest_week()` asserts the parsed row count matches the page's
  own reported count and raises rather than silently under-ingesting a week that exceeds one page
  -- CLAUDE.md's "a summary is not trustworthy on its own" rule applies here as much as anywhere.
- Each detail page (e.g. .../adjudication-order-in-the-matter-of-global-securities-limited_45572.html)
  embeds the real PDF via `<iframe src='../../../web/?file=/sebi_data/attachdocs/...pdf'>` -- this
  module resolves that to the real, direct, absolute PDF URL, confirmed against one real order.

Deliberately NOT done in this pass, named rather than silently absent:
- PDF text extraction (pdfplumber) for a confirmed `event_date`/period and a clean entity/symbol
  match. `event_date` is stored equal to `knowledge_date` (the listing date) as an explicit,
  honest placeholder -- `needs_review=1` (the schema's own designed escape hatch, not a workaround
  invented here) means no caller may treat it as a confirmed period without that review.
- `symbol` is left NULL (the schema already allows this) rather than fuzzy-matched from the free-
  text title -- a wrong automated match is worse than an honest absence for a label source this
  project's whole classifier depends on.
"""
from __future__ import annotations
import re
from datetime import date, datetime, timedelta, timezone

import requests

from ...bitemporal.store import write_facts

LISTING_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do"
AO_ORDERS_SMID = "6"
ROW_RE = re.compile(
    r"<td>([A-Za-z]{3} \d{2}, \d{4})</td>\s*<td><a href=\"([^\"]+)\"\s+target=\"_blank\"\s+title=\"([^\"]+)\"",
)
COUNT_RE = re.compile(r"(\d+) to (\d+) of (\d+) records")

def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"})
    return session

def fetch_week_listing(session: requests.Session, from_date: date, to_date: date, timeout: float = 25.0) -> str:
    r = session.get(LISTING_URL, params={
        "doListing": "yes", "sid": "2", "ssid": "9", "smid": AO_ORDERS_SMID,
        "fromDate": from_date.strftime("%d-%m-%Y"), "toDate": to_date.strftime("%d-%m-%Y"),
    }, timeout=timeout)
    r.raise_for_status()
    return r.text

class ListingCountMismatchError(ValueError):
    """Raised when the page's own reported record count doesn't match what was actually parsed,
    or exceeds the one-page cap this module relies on -- never silently under-ingested."""

def parse_week_listing(html: str) -> list[dict]:
    """Pure function: no I/O. Returns [{event_date_listed, title, detail_url}, ...]. Raises
    ListingCountMismatchError if the page's own "X to Y of Z records" count disagrees with the
    number of rows actually parsed, or if Z exceeds what one page (up to 25) can hold -- a week
    that dense needs to be split into a narrower window, not silently truncated to 25.
    """
    count_match = COUNT_RE.search(html)
    if count_match is None:
        return []  # a genuinely empty week has no count string at all -- zero real rows, not an error
    _start, end, total = (int(g) for g in count_match.groups())
    if total > 25:
        raise ListingCountMismatchError(f"{total} records in this window exceeds the one-page (25) assumption this module relies on -- narrow the window.")

    rows = []
    for date_str, href, title in ROW_RE.findall(html):
        event_date = datetime.strptime(date_str, "%b %d, %Y").date().isoformat()
        rows.append({"event_date_listed": event_date, "title": title, "detail_url": href})

    if len(rows) != total:
        raise ListingCountMismatchError(f"Page reports {total} records but {len(rows)} were parsed from the row markup -- the row regex or page structure has likely changed.")
    return rows

def resolve_pdf_url(session: requests.Session, detail_url: str, timeout: float = 25.0) -> str | None:
    r = session.get(detail_url, timeout=timeout)
    if r.status_code != 200:
        return None
    m = re.search(r"<iframe src='([^']+\.pdf)'", r.text)
    if m is None:
        return None
    relative = m.group(1)
    # observed shape: '../../../web/?file=/sebi_data/attachdocs/jan-2020/NNNN.pdf' relative to the
    # detail page -- resolved against the fixed site root rather than a generic urljoin, since the
    # relative-dots count is a property of this specific page template, confirmed on one real page,
    # not assumed stable across templates.
    file_param = relative.split("file=", 1)[-1]
    return f"https://www.sebi.gov.in/web/?file={file_param}"

_ORDER_ID_RE = re.compile(r"_(\d+)\.html$")

def order_id_from_detail_url(detail_url: str) -> str | None:
    m = _ORDER_ID_RE.search(detail_url)
    return m.group(1) if m else None

_ENTITY_RE = re.compile(r"in (?:the matter of|respect of)\s+(.+?)(?:\s+in the matter of\s+(.+))?$", re.IGNORECASE)

def extract_entity_name(title: str) -> str:
    """Best-effort, deliberately crude: real titles are irregular free text ("Adjudication Order
    in the matter of X", "Adjudication Order in respect of Person Y in the matter of Z"). Returns
    the fuller, more specific trailing clause when both are present (matches the entity the order
    is actually about, e.g. "Global Securities Limited" not the generic "the matter of"); falls
    back to the whole title if no pattern matches, never raises, never fabricates a name that
    isn't a substring of the real title.
    """
    m = _ENTITY_RE.search(title)
    if not m:
        return title.strip()
    return (m.group(2) or m.group(1)).strip()

def build_order_row(listing_row: dict, pdf_url: str | None, knowledge_date: str) -> dict | None:
    """No `source_file` field: unlike bhavcopy/corporate_actions/surveillance_flags, the
    `sebi_orders` schema (Phase 1) has no such column -- `pdf_url` already IS the row's own
    source reference, so there is nothing a separate field would add. Confirmed against the real
    schema (src/bitemporal/schema.py) before writing this, not assumed from the sibling tables'
    shape.
    """
    order_id = order_id_from_detail_url(listing_row["detail_url"])
    if order_id is None or pdf_url is None:
        return None  # cannot build a row without both required NOT NULL fields -- skipped, not guessed
    return {
        "order_id": order_id, "entity_name": extract_entity_name(listing_row["title"]),
        "symbol": None, "event_date": knowledge_date, "knowledge_date": knowledge_date,
        "needs_review": True, "pdf_url": pdf_url, "raw_text_excerpt": None,
    }

def ingest_window(conn, session: requests.Session, from_date: date, to_date: date):
    """Fetches and ingests one window's real listing. Raises ListingCountMismatchError if the
    window holds more than one page (25) of records -- callers that want automatic recovery from
    that should use `ingest_range()` below, not this function directly.
    """
    html = fetch_week_listing(session, from_date, to_date)
    listing_rows = parse_week_listing(html)
    order_rows = []
    for listing_row in listing_rows:
        pdf_url = resolve_pdf_url(session, listing_row["detail_url"])
        row = build_order_row(listing_row, pdf_url, listing_row["event_date_listed"])
        if row is not None:
            order_rows.append(row)
    if not order_rows:
        from ...bitemporal.store import BulkWriteResult
        return BulkWriteResult(inserted=0, skipped_duplicate=0), len(listing_rows), len(order_rows)
    result = write_facts(conn, "sebi_orders", order_rows)
    return result, len(listing_rows), len(order_rows)

# Backward-compatible alias -- ingest_week was the original name before real data (Jan 2020,
# 29th-31st: 36 records in 3 days) showed a fixed 7-day window isn't always under the 25-per-page
# cap and this function needed to become window-size-agnostic, not week-specific.
ingest_week = ingest_window

def ingest_range(conn, session: requests.Session, start: date, end: date, _depth: int = 0):
    """Ingests [start, end] with automatic recovery from ListingCountMismatchError: on overflow,
    bisects the window in half and retries each half, recursively -- confirmed necessary, not
    speculative, by a real 3-day window (2020-01-29..31) holding 36 records. Gives up only when a
    single day itself exceeds 25 records (would need real pagination, not narrowing, to fix; rare
    enough in 7 years of data that this project handles it by exception rather than by solving
    the harder JS-pagination-replication problem for a handful of days).

    Returns (total_listed, total_written, total_inserted, total_skipped, failed_windows) --
    `failed_windows` is a list of (day, day) pairs that could not be ingested even at single-day
    granularity, reported rather than silently dropped.
    """
    try:
        result, n_listed, n_written = ingest_window(conn, session, start, end)
        return n_listed, n_written, result.inserted, result.skipped_duplicate, []
    except ListingCountMismatchError:
        if start == end:
            return 0, 0, 0, 0, [(start, end)]  # a single day over 25 records -- cannot narrow further
        mid = start + (end - start) // 2
        l1, w1, i1, s1, f1 = ingest_range(conn, session, start, mid, _depth + 1)
        l2, w2, i2, s2, f2 = ingest_range(conn, session, mid + timedelta(days=1), end, _depth + 1)
        return l1 + l2, w1 + w2, i1 + i2, s1 + s2, f1 + f2

def iterate_weeks(start: date, end: date):
    current = start
    while current <= end:
        week_end = min(current + timedelta(days=6), end)
        yield current, week_end
        current = week_end + timedelta(days=1)
