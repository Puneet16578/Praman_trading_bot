"""Phase 7a: for every catalogued event, does corporate_announcements have at least one
announcement (any category) in the 10 real trading sessions strictly before event_date? Reports
coverage: events with >=1 announcement in that window, events with none, and any event whose
symbol has no announcement data cached at all (a fetch gap, distinct from a real "no disclosure"
absence -- CLAUDE.md's "report missing data explicitly, never a neutral-looking zero" rule applies
here as much as to any signal).

10 real trading sessions, not 10 calendar days: matches this project's own windowing convention
elsewhere (TRAILING_WINDOW, CUMULATIVE_WINDOW in event_catalogue.py) rather than a bare calendar
count, since a 10-calendar-day window spans a different number of real trading opportunities
depending on where weekends/holidays fall.
"""
from __future__ import annotations
import bisect
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.disclosure_classification import classify_disclosure_window
from src.signals.event_catalogue import build_symbol_history

DISCLOSURE_WINDOW_SESSIONS = 10
INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    # deliberately NOT setting conn.row_factory = None here: build_symbol_history() below shares
    # this same connection and its internal read_as_of() calls require the default sqlite3.Row
    # factory (dict(row) conversion) -- this script's own raw queries use positional r[0] access,
    # which sqlite3.Row supports natively, so no row_factory override is needed at all.

    with open(INPUT_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Loaded {len(events)} catalogued events")

    fetched_symbols = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM corporate_announcements").fetchall()}
    print(f"{len(fetched_symbols)} symbols have announcement data cached")

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        by_symbol.setdefault(e["symbol"], []).append(e)

    has_disclosure = 0
    no_disclosure = 0
    fetch_gap = 0
    insufficient_history = 0
    substantive = 0
    routine_only = 0
    none_found = 0
    t0 = time.time()
    for i, (symbol, symbol_events) in enumerate(by_symbol.items()):
        if symbol not in fetched_symbols:
            fetch_gap += len(symbol_events)
            continue

        ann_rows = conn.execute(
            "SELECT event_date, category FROM corporate_announcements WHERE symbol=? ORDER BY event_date", (symbol,)).fetchall()
        ann_dates = sorted(r[0] for r in ann_rows)
        rows_by_date: dict[str, list[dict]] = {}
        for event_date_, category in ann_rows:
            rows_by_date.setdefault(event_date_, []).append({"category": category})

        hist = build_symbol_history(conn, symbol)
        days = hist.trading_days
        for e in symbol_events:
            event_date = e["event_date"]
            idx = bisect.bisect_left(days, event_date)
            if idx < DISCLOSURE_WINDOW_SESSIONS:
                insufficient_history += 1
                continue
            window_start = days[idx - DISCLOSURE_WINDOW_SESSIONS]
            lo = bisect.bisect_left(ann_dates, window_start)
            hi = bisect.bisect_left(ann_dates, event_date)
            window_dates = ann_dates[lo:hi]
            if window_dates:
                has_disclosure += 1
            else:
                no_disclosure += 1

            window_rows: list[dict] = []
            for d in window_dates:
                window_rows.extend(rows_by_date.get(d, []))
            tier = classify_disclosure_window(window_rows)
            if tier == "SUBSTANTIVE":
                substantive += 1
            elif tier == "ROUTINE_ONLY":
                routine_only += 1
            else:
                none_found += 1
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(by_symbol)} symbols, {time.time() - t0:.0f}s elapsed")

    total = has_disclosure + no_disclosure + fetch_gap + insufficient_history
    print(f"\nDone in {time.time() - t0:.0f}s")
    print(f"Total events: {total}")
    print(f"  >=1 announcement in the {DISCLOSURE_WINDOW_SESSIONS}-session window: {has_disclosure} ({100*has_disclosure/total:.1f}%)")
    known = substantive + routine_only + none_found
    print(f"\nThree-way split (substantive/routine-only/none), fetch-gap and insufficient-history events excluded from the denominator ({known} events):")
    print(f"  SUBSTANTIVE disclosure present: {substantive} ({100*substantive/known:.1f}%)")
    print(f"  ROUTINE disclosure only (or ambiguous-only): {routine_only} ({100*routine_only/known:.1f}%)")
    print(f"  NO disclosure at all in the window: {none_found} ({100*none_found/known:.1f}%)")
    print(f"  0 announcements in the window (real absence): {no_disclosure} ({100*no_disclosure/total:.1f}%)")
    print(f"  fetch gap -- symbol has no announcement data cached at all: {fetch_gap} ({100*fetch_gap/total:.1f}%)")
    print(f"  insufficient trading history for a full {DISCLOSURE_WINDOW_SESSIONS}-session window: {insufficient_history} ({100*insufficient_history/total:.1f}%)")
    conn.close()

if __name__ == "__main__":
    main()
