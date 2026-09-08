"""Real-data ingestion sample + coverage report for Phase 2 verification.

Ingests a real, non-trivial sample of NSE bhavcopy: the earliest available date (2019-10-01, per
CLAUDE.md's hard constraint -- NOT 2019-09-30, see P2-003), one reference date per calendar year
through 2025, and a recent contiguous window (to exercise real weekday/weekend/holiday behavior
and idempotent re-ingestion). Writes to a real file-based SQLite DB (not :memory:) so the guard
can be re-tested against real rows afterward and so a second run of this script itself
demonstrates real-data idempotency.

Reporting is against the OBSERVED TRADING CALENDAR (P2-005), not the raw calendar sweep: a weekend
(hard HTTP error) and a holiday (small fallback to a different date) are both reported as
NOT_A_TRADING_DAY, not conflated as "gap" vs "ingested" depending on which artifact NSE happened
to serve. GAP is reserved for a date some other outcome confirms is a real trading day, but whose
own direct fetch failed to retrieve it -- see `classify_against_observed_trading_calendar`.
"""
from __future__ import annotations
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.config.settings import get_settings
from src.ingestion.nse_market_data.bhavcopy import (
    GAP, INGESTED, NOT_A_TRADING_DAY, classify_against_observed_trading_calendar, ingest_bhavcopy_dates,
)

REFERENCE_DATES = [
    date(2019, 10, 1),   # earliest available date (CLAUDE.md hard constraint; NOT 2019-09-30, see P2-003)
    date(2020, 3, 2),
    date(2021, 3, 1),
    date(2022, 3, 1),
    date(2023, 3, 1),
    date(2024, 3, 1),
    date(2025, 3, 3),
]

def recent_window(end: date, days: int = 10) -> list[date]:
    return [end - timedelta(days=i) for i in range(days)][::-1]

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    today = date(2026, 9, 7)  # most recent date confirmed real during pre-flight verification
    all_dates = REFERENCE_DATES + recent_window(today, days=10)

    print(f"Requesting {len(all_dates)} calendar dates into {settings.database_path} ...")
    outcomes = ingest_bhavcopy_dates(conn, all_dates, delay_seconds=settings.nse_request_delay_seconds)
    classification = classify_against_observed_trading_calendar(outcomes)

    trading_day_outcomes = {d: c for d, c in classification.items() if c != NOT_A_TRADING_DAY}
    ingested_days = [d for d, c in classification.items() if c == INGESTED]
    gap_days = [d for d, c in classification.items() if c == GAP]
    not_trading_days = [d for d, c in classification.items() if c == NOT_A_TRADING_DAY]

    print(f"\nRequested calendar dates: {len(all_dates)}")
    print(f"Observed trading calendar (dates confirmed to be real trading days): {len(trading_day_outcomes)}")
    print(f"  Ingested: {len(ingested_days)}")
    print(f"  GAP (confirmed trading day, ingestion failed -- real anomaly): {len(gap_days)}")
    print(f"Not a trading day (weekend/holiday, excluded from the trading-day denominator): {len(not_trading_days)} -> {not_trading_days}")

    by_date = {o.trade_date.isoformat(): o for o in outcomes}
    print(f"\nTotal rows inserted: {sum(o.rows_inserted for o in outcomes)}")
    print(f"Total rows skipped as duplicate: {sum(o.rows_skipped_duplicate for o in outcomes)}")
    print(f"Total rows skipped as invalid (missing symbol/series, P2-004): {sum(o.rows_skipped_invalid for o in outcomes)}")
    print("\nPer-date outcome (requested date -> actual event_date, if different):")
    for req_date, cls in sorted(classification.items()):
        o = by_date[req_date]
        if cls == INGESTED:
            print(f"  {req_date}  INGESTED           rows_inserted={o.rows_inserted}  rows_skipped_duplicate={o.rows_skipped_duplicate}")
        elif cls == GAP:
            print(f"  {req_date}  GAP (real anomaly) reason={o.reason}  actual_event_date={o.actual_event_date}")
        else:
            note = f"actual_event_date={o.actual_event_date}" if o.actual_event_date else (o.reason or "no data")
            print(f"  {req_date}  not_a_trading_day  {note}")

    all_rows = read_as_of(conn, "bhavcopy", "2099-01-01")
    symbols = {r["symbol"] for r in all_rows}
    event_dates = sorted({r["event_date"] for r in all_rows})
    print(f"\nDistinct symbols across all ingested dates: {len(symbols)}")
    print(f"Distinct event_dates with data: {len(event_dates)} -> {event_dates}")

    earliest_date, latest_date = event_dates[0], event_dates[-1]
    early_symbols = {r["symbol"] for r in all_rows if r["event_date"] == earliest_date}
    recent_symbols = {r["symbol"] for r in all_rows if r["event_date"] == latest_date}
    not_seen_recently = early_symbols - recent_symbols
    new_since = recent_symbols - early_symbols
    print(f"\nSurvivorship spot-check ONLY (earliest={earliest_date} vs. latest={latest_date}, "
          f"{len(early_symbols)} vs. {len(recent_symbols)} symbols) -- see phase doc for why this "
          f"is a lower bound, not a delisted-company count:")
    print(f"  Present {earliest_date} but absent {latest_date}: {len(not_seen_recently)}")
    print(f"  Present {latest_date} but absent {earliest_date} (new listings since): {len(new_since)}")
    if not_seen_recently:
        print(f"  Sample: {sorted(not_seen_recently)[:20]}")

    conn.close()

if __name__ == "__main__":
    main()
