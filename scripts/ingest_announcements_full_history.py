"""Phase 7a: full-history corporate-announcement backfill for every EQ symbol in the event
catalogue. Resumable by design: checks which symbols already have at least one cached row at
startup and fetches only the rest -- same pattern as scripts/ingest_bhavcopy_full_history.py's
`already_confirmed_trading_days`, adopted here for the same reason (a real, timed 10-symbol
sample projected to ~87 minutes for the full 2,958-symbol catalogue universe, over the
one-hour bar that triggers this).
"""
from __future__ import annotations
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.market_time import market_today
from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.announcements import _session_with_cookie, fetch_and_ingest_symbol

START_DATE = date(2019, 10, 1)

def already_fetched_symbols(conn) -> set[str]:
    conn.row_factory = None
    rows = conn.execute("SELECT DISTINCT symbol FROM corporate_announcements").fetchall()
    return {r[0] for r in rows}

def main(end_date: date | None = None) -> None:
    end_date = end_date or market_today()
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    catalogue_symbols = sorted({r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ'").fetchall()})
    print(f"{len(catalogue_symbols)} distinct EQ symbols in the store.")

    already_done = already_fetched_symbols(conn)
    remaining = [s for s in catalogue_symbols if s not in already_done]
    print(f"{len(already_done)} symbols already cached, {len(remaining)} remaining to fetch.")

    session = _session_with_cookie()
    t0 = time.time()
    total_raw = 0
    failed: list[str] = []
    for i, symbol in enumerate(remaining):
        try:
            result, raw_count = fetch_and_ingest_symbol(conn, session, symbol, START_DATE, end_date)
            total_raw += raw_count
        except Exception as exc:
            failed.append(symbol)
            # "WARN " lines make weekly_ingest report this step WARN, not OK (P8-021).
            print(f"WARN announcements backfill: FAILED {symbol}: {type(exc).__name__}: {exc}")
            continue
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            remaining_count = len(remaining) - (i + 1)
            eta_s = remaining_count / rate if rate > 0 else float("nan")
            print(f"  ...{i + 1}/{len(remaining)} symbols, {total_raw} rows, {elapsed:.0f}s elapsed, ETA {eta_s:.0f}s")

    elapsed = time.time() - t0
    print(f"\nDone: {len(remaining) - len(failed)}/{len(remaining)} symbols fetched, {total_raw} new rows, {elapsed:.0f}s")
    if failed:
        print(f"WARN announcements backfill: {len(failed)} symbols FAILED: {failed}")

    total_rows = conn.execute("SELECT COUNT(*) FROM corporate_announcements").fetchone()[0]
    total_symbols = len(already_fetched_symbols(conn))
    print(f"Store now holds {total_rows} announcement rows across {total_symbols} symbols.")
    conn.close()

if __name__ == "__main__":
    main()
