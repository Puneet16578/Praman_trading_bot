"""Phase 6: close-to-close price variation, on NSE's own published ASM criteria list (long-term
ASM: 60- and 365-trading-day close-to-close variation, beta-adjusted against Nifty 50 --
docs/phase6_signals.md Part B) and never built despite being directly computable from bhavcopy
alone. 60-trading-day window chosen to match this project's existing TRAILING_WINDOW (the z-score
reference period) rather than NSE's 365-day option, for consistency with everything else already
computed per event.

Genuinely as-of correct, unlike the outcome labels: computed with as_of=event_date (what was
knowable the day of the event), not FAR_FUTURE_AS_OF -- this is a live-computable feature, not a
retrospective label.
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
from src.signals.event_catalogue import _return, build_symbol_history

LOOKBACK = 60
INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "close_to_close_60d.csv"

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    with open(INPUT_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Loaded {len(events)} catalogued events")

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        by_symbol.setdefault(e["symbol"], []).append(e)

    out_rows = []
    t0 = time.time()
    for i, (symbol, symbol_events) in enumerate(by_symbol.items()):
        hist = build_symbol_history(conn, symbol)
        days = hist.trading_days
        for e in symbol_events:
            idx = bisect.bisect_left(days, e["event_date"])
            if idx >= len(days) or days[idx] != e["event_date"]:
                ctc = None
            elif idx - LOOKBACK < 0:
                ctc = None
            else:
                start = days[idx - LOOKBACK]
                ctc = _return(hist, start, e["event_date"], as_of=e["event_date"])
            out_rows.append({"symbol": symbol, "event_date": e["event_date"], "close_to_close_60d": ctc})
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(by_symbol)} symbols, {time.time() - t0:.0f}s elapsed")

    print(f"Done in {time.time() - t0:.0f}s")
    n_none = sum(1 for r in out_rows if r["close_to_close_60d"] is None)
    print(f"None (insufficient history or structural break in window): {n_none} / {len(out_rows)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "event_date", "close_to_close_60d"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Persisted {len(out_rows)} rows to {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
