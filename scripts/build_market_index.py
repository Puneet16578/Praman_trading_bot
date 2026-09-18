"""Phase 6 pre-flight, part 3: an equal-weighted EQ market-index proxy, built because
docs/phase6_signals.md's Check 1 found the raw collapsed_90d outcome label swings 50.6% (2020) to
74.1% (2026) by year -- it is tracking market drift, not move authenticity. No real index (NIFTY)
is ingested, so per instruction this project builds the "serviceable proxy" explicitly: the
equal-weighted mean daily adjusted return across every EQ symbol with a valid return that day.

One index level per real trading day, corporate-action-adjusted (via the same _return()/
structural-break-excluded machinery as everything else), covering the full 2019-10-01 to
2026-09-15 history. index[first_day] = 1.0; index[day] = index[day-1] * (1 + mean_return[day]).
A symbol contributes to a day's mean only when its own _return() for that single day is
computable (not None) -- excluded (not zero-filled) otherwise, e.g. on that symbol's own
structural-break day.
"""
from __future__ import annotations
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, _return, build_symbol_history

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "market_index.csv"

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    symbols = [r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ' ORDER BY symbol").fetchall()]
    print(f"Building equal-weighted market index from {len(symbols)} EQ symbols...")

    returns_by_date: dict[str, list[float]] = defaultdict(list)
    t0 = time.time()
    for i, symbol in enumerate(symbols):
        hist = build_symbol_history(conn, symbol)
        days = hist.trading_days
        for k in range(1, len(days)):
            r = _return(hist, days[k - 1], days[k], as_of=FAR_FUTURE_AS_OF)
            if r is not None:
                returns_by_date[days[k]].append(r)
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(symbols)} symbols, {time.time() - t0:.0f}s elapsed")

    print(f"Done accumulating in {time.time() - t0:.0f}s. {len(returns_by_date)} distinct dates with returns.")

    dates = sorted(returns_by_date.keys())
    mean_return: dict[str, float] = {d: sum(returns_by_date[d]) / len(returns_by_date[d]) for d in dates}

    index: dict[str, float] = {}
    level = 1.0
    # The first date in the whole history has no "day-over-day return INTO it" recorded (nothing
    # before it) -- start the index at 1.0 one trading day earlier conceptually, then compound
    # every date's mean return in order.
    for d in dates:
        level *= (1.0 + mean_return[d])
        index[d] = level

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "n_symbols_contributing", "mean_return", "index_level"])
        for d in dates:
            writer.writerow([d, len(returns_by_date[d]), mean_return[d], index[d]])

    print(f"Persisted {len(dates)} index rows to {OUTPUT_PATH}")
    print(f"Index level range: {index[dates[0]]:.4f} ({dates[0]}) -> {index[dates[-1]]:.4f} ({dates[-1]})")
    conn.close()

if __name__ == "__main__":
    main()
