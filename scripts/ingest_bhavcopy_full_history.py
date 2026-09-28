"""Full-history bhavcopy ingestion -- WP-1's actual scope (2019-10-01 through today), not the
Phase 2 verification sample (`scripts/ingest_bhavcopy_sample.py`, which deliberately covers only
8 reference dates + a 10-day window to exercise the pipeline's logic against real data cheaply).
A store with `surveillance_flags` and `corporate_actions` fully populated across 2019-2026 can
still have `bhavcopy` -- the table everything else in this project ultimately joins against for
prices -- covering only 15 sample dates. The full ASM/GSM sweep ran before anyone noticed bhavcopy
itself was never run at scale; a populated-looking store is not the same claim as a complete one,
and this project verifies completeness rather than inferring it from a sibling table's coverage.

Resumable: every weekday already present as its own `event_date` in the real store is skipped
before any network call, so an interrupted run (this project's ASM/GSM sweep needed two restarts)
can simply be re-invoked.

Weekday-only requests (Mon-Fri) trim the largest source of pure-fallback noise (a Saturday/Sunday
request would otherwise always re-fetch whatever the archive serves for the nearest prior trading
day, for no new information). Within one run, `already_confirmed` (see
`ingest_bhavcopy_date`'s docstring) additionally skips writing a second time when a later weekday
(a holiday) falls back to a day this run already confirmed and wrote -- structurally preventing
the duplicate-vintage pattern found in the sample data (3,506 rows, all one harmless artifact:
2026-09-04 requested by two SEPARATE real invocations of the sample script days apart, whose
Last-Modified header apparently drifted between those two real-world calls) regardless of whether
NSE's Last-Modified header is byte-stable across a single run's whole duration.
"""
from __future__ import annotations
from datetime import date, timedelta
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.market_time import market_today
from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.config.settings import get_settings
from src.ingestion.nse_market_data.bhavcopy import (
    GAP, INGESTED, NOT_A_TRADING_DAY, classify_against_observed_trading_calendar, ingest_bhavcopy_date,
)

START_DATE = date(2019, 10, 1)  # CLAUDE.md hard constraint (P2-003)

def weekdays_between(start: date, end: date) -> list[date]:
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:  # Mon=0 .. Fri=4
            days.append(d)
        d += timedelta(days=1)
    return days

def already_confirmed_trading_days(conn) -> set[str]:
    rows = read_as_of(conn, "bhavcopy", "2099-01-01")
    return {r["event_date"] for r in rows}

def main(end_date: date | None = None) -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    end = end_date or (market_today() - timedelta(days=1))
    candidates = weekdays_between(START_DATE, end)
    confirmed = already_confirmed_trading_days(conn)
    to_request = [d for d in candidates if d.isoformat() not in confirmed]

    print(f"Weekdays in range {START_DATE.isoformat()}..{end.isoformat()}: {len(candidates)}")
    print(f"Already confirmed in store (resumed, skipped): {len(candidates) - len(to_request)}")
    print(f"To request this run: {len(to_request)}")

    outcomes = []
    redundant_skips = 0
    for i, trade_date in enumerate(to_request):
        if i > 0:
            time.sleep(settings.nse_request_delay_seconds)
        before = len(confirmed)
        outcome = ingest_bhavcopy_date(conn, trade_date, already_confirmed=confirmed)
        if outcome.actual_event_date:
            if outcome.actual_event_date in confirmed and outcome.rows_inserted == 0 and outcome.status == "ingested":
                redundant_skips += 1
            confirmed.add(outcome.actual_event_date)
        outcomes.append(outcome)

        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1}/{len(to_request)} requested, {sum(o.rows_inserted for o in outcomes)} rows written so far, "
                  f"{redundant_skips} redundant-fallback skips, {sum(1 for o in outcomes if o.status == 'gap')} gaps")

    classification = classify_against_observed_trading_calendar(outcomes)
    ingested_days = [d for d, c in classification.items() if c == INGESTED]
    gap_days = [d for d, c in classification.items() if c == GAP]
    not_trading_days = [d for d, c in classification.items() if c == NOT_A_TRADING_DAY]

    print(f"\n=== THIS RUN'S REQUESTS ===")
    print(f"Requested: {len(to_request)}")
    print(f"Confirmed trading days (direct): {len(ingested_days)}")
    print(f"Redundant-fallback skips (holiday re-serving an already-confirmed day): {redundant_skips}")
    print(f"GAP (confirmed trading day, this request failed): {len(gap_days)}")
    for d in sorted(gap_days):
        o = next(o for o in outcomes if o.trade_date.isoformat() == d)
        print(f"  GAP {d}: {o.reason}")
    print(f"Not a trading day (weekend/holiday, no other outcome confirms it): {len(not_trading_days)}")
    print(f"New rows written: {sum(o.rows_inserted for o in outcomes)}")
    print(f"Rows skipped as duplicate: {sum(o.rows_skipped_duplicate for o in outcomes)}")
    print(f"Rows skipped as invalid (P2-004): {sum(o.rows_skipped_invalid for o in outcomes)}")

    all_rows = read_as_of(conn, "bhavcopy", "2099-01-01")
    print(f"\n=== STORE STATE (all-time) ===")
    print(f"Total rows: {len(all_rows)}")
    print(f"Distinct symbols: {len({r['symbol'] for r in all_rows})}")
    event_dates = sorted({r["event_date"] for r in all_rows})
    print(f"Distinct trading days: {len(event_dates)}")
    print(f"Date range: {event_dates[0]} .. {event_dates[-1]}")

    conn.close()

if __name__ == "__main__":
    main()
