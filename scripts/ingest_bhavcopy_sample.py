"""Real-data ingestion sample + coverage report for Phase 2 verification.

Ingests a real, non-trivial sample of NSE bhavcopy: the earliest available date (2019-09-30, per
CLAUDE.md's hard constraint), one reference date per calendar year through 2025, and a recent
contiguous window (to exercise real weekday/weekend/holiday gaps and idempotent re-ingestion).
Writes to a real file-based SQLite DB (not :memory:) so the guard can be re-tested against real
rows afterward and so a second run of this script itself demonstrates real-data idempotency.
"""
from __future__ import annotations
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.config.settings import get_settings
from src.ingestion.nse_market_data.bhavcopy import ingest_bhavcopy_dates

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

    print(f"Ingesting {len(all_dates)} calendar dates into {settings.database_path} ...")
    outcomes = ingest_bhavcopy_dates(conn, all_dates, delay_seconds=settings.nse_request_delay_seconds)

    ingested = [o for o in outcomes if o.status == "ingested"]
    gaps = [o for o in outcomes if o.status == "gap"]

    print(f"\nIngested: {len(ingested)} date(s), Gaps: {len(gaps)} date(s)")
    print(f"Total rows inserted: {sum(o.rows_inserted for o in ingested)}")
    print(f"Total rows skipped as duplicate: {sum(o.rows_skipped_duplicate for o in ingested)}")
    print(f"Total rows skipped as invalid (missing symbol/series, P2-004): {sum(o.rows_skipped_invalid for o in ingested)}")
    print("\nPer-date outcome (requested date -> actual event_date, if different):")
    for o in outcomes:
        if o.status == "ingested":
            note = "" if o.actual_event_date == o.trade_date.isoformat() else f"  [actual_event_date={o.actual_event_date}]"
            print(f"  {o.trade_date}  ingested  rows_inserted={o.rows_inserted}  rows_skipped_duplicate={o.rows_skipped_duplicate}{note}")
        else:
            print(f"  {o.trade_date}  GAP       reason={o.reason}")

    all_rows = read_as_of(conn, "bhavcopy", "2099-01-01")
    symbols = {r["symbol"] for r in all_rows}
    event_dates = sorted({r["event_date"] for r in all_rows})
    print(f"\nDistinct symbols across all ingested dates: {len(symbols)}")
    print(f"Distinct event_dates with data: {len(event_dates)} -> {event_dates}")

    earliest_date, latest_date = event_dates[0], event_dates[-1]
    early_symbols = {r["symbol"] for r in all_rows if r["event_date"] == earliest_date}
    recent_symbols = {r["symbol"] for r in all_rows if r["event_date"] == latest_date}
    not_currently_listed = early_symbols - recent_symbols
    new_since = recent_symbols - early_symbols
    print(f"\nUniverse check (earliest={earliest_date} vs. latest={latest_date}, {len(early_symbols)} vs. {len(recent_symbols)} symbols):")
    print(f"  Present {earliest_date} but absent {latest_date} (proxy for delisted/suspended/renamed): {len(not_currently_listed)}")
    print(f"  Present {latest_date} but absent {earliest_date} (new listings since): {len(new_since)}")
    if not_currently_listed:
        print(f"  Sample: {sorted(not_currently_listed)[:20]}")

    conn.close()

if __name__ == "__main__":
    main()
