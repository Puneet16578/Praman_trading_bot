"""NSE full-bhavcopy ingestion.

Fetches NSE's combined price+delivery bhavcopy via jugaad-data's `NSEArchives` directly, not the
high-level `full_bhavcopy_save`/`full_bhavcopy_raw` convenience wrappers -- those discard the HTTP
response entirely, and this module needs the response's own `Last-Modified` header. NSE's bhavcopy
CSV carries no self-declared publication timestamp of its own; the file's `Last-Modified` (verified
empirically against a real response -- see CLAUDE.md's data-sourcing section) is the most
source-derived signal available for knowledge_date, converted to IST (NSE's own timezone) since a
GMT time in the evening can already be past midnight IST.

P2-001 (docs/DEFECT_REGISTER.md): `jugaad_data` itself does not validate its response -- it will
return normally even when NSE served an HTML error page. This module inspects raw content directly
and never treats "no exception raised" as "this is valid data." The store (`src/bitemporal/store.py`)
independently re-validates row shape regardless of what this module already checked -- this module's
own validation exists for a clean, specific error message, not as the only line of defense.

No `sqlite3.connect` call exists anywhere in this module or elsewhere in `src/ingestion/` --
`tests/test_no_update_on_fact_tables.py::IngestionNeverOpensConnectionDirectlyTest` enforces this
structurally. Every write goes through `src.bitemporal.store.write_facts`.
"""
from __future__ import annotations
import io
import sqlite3
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable

import pandas as pd
from jugaad_data.nse import NSEArchives

from ...bitemporal.store import write_facts

IST = timezone(timedelta(hours=5, minutes=30))

_EXPECTED_COLUMNS = {"SYMBOL", "SERIES", "DATE1", "PREV_CLOSE", "OPEN_PRICE", "HIGH_PRICE",
                     "LOW_PRICE", "CLOSE_PRICE", "TTL_TRD_QNTY", "DELIV_QTY", "DELIV_PER"}

class BhavcopyFetchError(Exception):
    """Raised when NSE returns something that is not a valid full-bhavcopy CSV for the requested
    date -- an HTML error page (P2-001), an unexpected schema, or a missing Last-Modified header.
    A non-exception return from the underlying library is never treated as success on its own.
    """

@dataclass(frozen=True)
class FetchResult:
    trade_date: date
    raw_text: str
    knowledge_date: str  # ISO date -- the IST calendar date of the response's Last-Modified header
    source_file: str

def _source_filename(trade_date: date) -> str:
    return f"sec_bhavdata_full_{trade_date.strftime('%d%b%Y')}bhav.csv"

def validate_csv_content(raw_text: str, trade_date: date) -> None:
    stripped = raw_text.lstrip()
    if stripped.startswith("<!DOCTYPE") or stripped.startswith("<html"):
        raise BhavcopyFetchError(f"NSE returned an HTML error page for {trade_date.isoformat()} instead of bhavcopy data (P2-001).")
    if not stripped:
        raise BhavcopyFetchError(f"NSE returned an empty response for {trade_date.isoformat()}.")
    header_line = raw_text.split("\n", 1)[0]
    header_cols = {c.strip() for c in header_line.split(",")}
    missing = _EXPECTED_COLUMNS - header_cols
    if missing:
        raise BhavcopyFetchError(f"Bhavcopy for {trade_date.isoformat()} is missing expected column(s) {sorted(missing)} -- unexpected schema, refusing to ingest.")

def last_modified_to_ist_date(last_modified_http_date: str) -> str:
    dt_gmt = datetime.strptime(last_modified_http_date, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    return dt_gmt.astimezone(IST).date().isoformat()

def fetch_bhavcopy(trade_date: date, timeout: float = 30.0) -> FetchResult:
    """Real network call. Not exercised by the unit test suite -- see `ingest_bhavcopy_date`'s
    `fetch_fn` parameter for how tests inject a fixture instead."""
    archives = NSEArchives()
    archives.timeout = timeout
    try:
        raw_text = archives.full_bhavcopy_raw(trade_date)
    except Exception as exc:
        raise BhavcopyFetchError(f"Fetch failed for {trade_date.isoformat()}: {type(exc).__name__}: {exc}") from exc

    validate_csv_content(raw_text, trade_date)

    response = archives.r  # underlying requests.Response; full_bhavcopy_raw() discards it otherwise
    last_modified = response.headers.get("Last-Modified") if response is not None else None
    if not last_modified:
        raise BhavcopyFetchError(f"NSE response for {trade_date.isoformat()} carries no Last-Modified header; refusing to guess knowledge_date.")

    return FetchResult(trade_date=trade_date, raw_text=raw_text,
                        knowledge_date=last_modified_to_ist_date(last_modified),
                        source_file=_source_filename(trade_date))

@dataclass(frozen=True)
class ParsedBhavcopy:
    rows: list[dict]
    skipped_invalid: int  # rows with a genuinely missing SYMBOL/SERIES (P2-004) -- can't form a business key

def parse_bhavcopy_rows(fetch_result: FetchResult) -> ParsedBhavcopy:
    """Every value is coerced to a native Python type here (str/int/float), not left as a numpy/
    pandas scalar -- store.py independently coerces too (P2-002), but doing it at the source keeps
    this module's own output self-describing and testable without depending on that guarantee.

    P2-004: NSE's own file occasionally has a genuinely blank SERIES (observed: 30 of 43,942 rows
    in the 2019-10-01 file, all NCD/bond-like instruments -- DHFL, HUDCO, IBULHSGFIN, IRFC). A
    naive `str(nan_value)` produces the literal text "nan", which is a valid-looking but semantically
    wrong, non-null string -- it would silently pass the store's type check and corrupt the
    business key. Rows missing SYMBOL or SERIES are skipped, not force-labeled, and counted so
    ingestion can report them rather than losing them silently.
    """
    # NSE uses '-' as its own "not applicable" sentinel for delivery fields on non-equity series
    # (e.g. debt/government-securities instruments carry no delivery concept at all) -- treated as
    # null exactly like a blank field, on top of pandas' own default NA sentinels.
    df = pd.read_csv(io.StringIO(fetch_result.raw_text), skipinitialspace=True, na_values=["-"])
    df.columns = [c.strip() for c in df.columns]
    df["EVENT_DATE"] = pd.to_datetime(df["DATE1"].astype(str).str.strip(), format="%d-%b-%Y").dt.strftime("%Y-%m-%d")

    rows = []
    skipped_invalid = 0
    for record in df.to_dict(orient="records"):
        if pd.isna(record.get("SYMBOL")) or pd.isna(record.get("SERIES")):
            skipped_invalid += 1
            continue
        delivery_qty = record.get("DELIV_QTY")
        delivery_pct = record.get("DELIV_PER")
        rows.append({
            "symbol": str(record["SYMBOL"]).strip(),
            "event_date": record["EVENT_DATE"],
            "knowledge_date": fetch_result.knowledge_date,
            "open_price": float(record["OPEN_PRICE"]),
            "high_price": float(record["HIGH_PRICE"]),
            "low_price": float(record["LOW_PRICE"]),
            "close_price": float(record["CLOSE_PRICE"]),
            "prev_close": float(record["PREV_CLOSE"]),
            "traded_qty": int(record["TTL_TRD_QNTY"]),
            "delivery_qty": None if pd.isna(delivery_qty) else int(delivery_qty),
            "delivery_pct": None if pd.isna(delivery_pct) else float(delivery_pct),
            "series": str(record["SERIES"]).strip(),
            "source_file": fetch_result.source_file,
        })
    return ParsedBhavcopy(rows=rows, skipped_invalid=skipped_invalid)

# P2-003: NSE's archive can return HTTP 200 with well-formed CSV for a DIFFERENT date than
# requested. A closed-market date (weekend/holiday) sanely falls back to the nearest prior trading
# day, observed within a few calendar days -- 2019-09-30 itself returned a file 95 days stale, not
# a fallback. 7 days comfortably covers even a multi-day festival closure without accepting a
# genuinely anomalous archive entry.
MAX_FALLBACK_DAYS = 7

@dataclass
class DateIngestionOutcome:
    trade_date: date
    status: str  # "ingested" or "gap"
    reason: str = ""
    actual_event_date: str = ""  # the response's own date, which may differ from trade_date (P2-003)
    rows_inserted: int = 0
    rows_skipped_duplicate: int = 0
    rows_skipped_invalid: int = 0  # missing SYMBOL/SERIES, can't form a business key (P2-004)

def ingest_bhavcopy_date(conn: sqlite3.Connection, trade_date: date,
                          fetch_fn: Callable[[date], FetchResult] = fetch_bhavcopy) -> DateIngestionOutcome:
    """`fetch_fn` defaults to the real network fetch; tests inject a fixture-returning callable
    instead so the unit suite never depends on NSE being reachable."""
    try:
        fetch_result = fetch_fn(trade_date)
    except BhavcopyFetchError as exc:
        return DateIngestionOutcome(trade_date=trade_date, status="gap", reason=str(exc))

    parsed = parse_bhavcopy_rows(fetch_result)
    if not parsed.rows:
        return DateIngestionOutcome(trade_date=trade_date, status="gap", rows_skipped_invalid=parsed.skipped_invalid,
                                     reason="Parsed zero valid rows from an otherwise valid response.")

    actual_event_dates = {r["event_date"] for r in parsed.rows}
    if len(actual_event_dates) != 1:
        return DateIngestionOutcome(trade_date=trade_date, status="gap",
                                     reason=f"Response mixes {len(actual_event_dates)} distinct event_dates in one file -- untrustworthy, refusing to ingest.")

    actual_event_date = date.fromisoformat(next(iter(actual_event_dates)))
    day_gap = (trade_date - actual_event_date).days
    if day_gap < 0 or day_gap > MAX_FALLBACK_DAYS:
        return DateIngestionOutcome(
            trade_date=trade_date, status="gap", actual_event_date=actual_event_date.isoformat(),
            reason=(f"Requested {trade_date.isoformat()} but NSE's archive returned data dated "
                     f"{actual_event_date.isoformat()} ({day_gap} day(s) off) -- beyond the "
                     f"{MAX_FALLBACK_DAYS}-day holiday/weekend fallback window, treated as an "
                     "anomalous/misrouted archive entry (P2-003), not ingested."))

    result = write_facts(conn, "bhavcopy", parsed.rows)
    return DateIngestionOutcome(trade_date=trade_date, status="ingested", actual_event_date=actual_event_date.isoformat(),
                                 rows_inserted=result.inserted, rows_skipped_duplicate=result.skipped_duplicate,
                                 rows_skipped_invalid=parsed.skipped_invalid)

def ingest_bhavcopy_dates(conn: sqlite3.Connection, trade_dates: list[date], delay_seconds: float = 1.0,
                           fetch_fn: Callable[[date], FetchResult] = fetch_bhavcopy) -> list[DateIngestionOutcome]:
    """Ingests each date in sequence with a politeness delay between real network calls (no delay
    is applied when `fetch_fn` is a test fixture, since there's no real request to throttle)."""
    outcomes = []
    for i, trade_date in enumerate(trade_dates):
        if i > 0 and fetch_fn is fetch_bhavcopy:
            time.sleep(delay_seconds)
        outcomes.append(ingest_bhavcopy_date(conn, trade_date, fetch_fn=fetch_fn))
    return outcomes

# P2-005: reporting a "gap" for every requested date whose own direct fetch didn't match conflates
# two entirely different situations -- a weekend/holiday (NSE never had a trading day there, not a
# problem) and a genuine trading day that ingestion failed to retrieve (a real anomaly worth
# investigating). Both previously showed up as "GAP" (weekends, via an HTML error) or "ingested"
# (holidays and Sundays, via a small fallback) depending on which specific artifact NSE happened to
# serve -- neither label was actually correct for a non-trading day. This function derives which
# requested dates are genuine trading days FROM THE OBSERVED EVIDENCE ITSELF (every outcome's own
# actual_event_date, whether obtained directly or via someone else's fallback) rather than from an
# external holiday calendar, and reclassifies accordingly. No new network calls.
INGESTED = "ingested"
NOT_A_TRADING_DAY = "not_a_trading_day"
GAP = "gap"

def classify_against_observed_trading_calendar(outcomes: list[DateIngestionOutcome]) -> dict[str, str]:
    """Returns {requested_date_iso: classification}, classification in
    {INGESTED, GAP, NOT_A_TRADING_DAY}.

    - INGESTED: the date's own direct fetch matched itself exactly -- a confirmed real trading day
      with data.
    - GAP: some OTHER outcome in this batch confirms the date is a real trading day (its own
      actual_event_date), but this date's own direct fetch did not retrieve it -- a genuine
      anomaly worth investigating.
    - NOT_A_TRADING_DAY: nothing in this batch's evidence suggests the date was ever a real
      trading day (the ordinary, expected case for weekends and holidays alike).
    """
    observed_trading_calendar = {o.actual_event_date for o in outcomes if o.actual_event_date}

    classification = {}
    for o in outcomes:
        requested = o.trade_date.isoformat()
        if o.actual_event_date == requested:
            classification[requested] = INGESTED
        elif requested in observed_trading_calendar:
            classification[requested] = GAP
        else:
            classification[requested] = NOT_A_TRADING_DAY
    return classification
