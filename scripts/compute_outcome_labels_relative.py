"""Phase 6 pre-flight, part 4: benchmark-relative collapsed/held label, built because Check 1
(docs/phase6_signals.md) found the raw collapsed_90d label swings 50.6%-74.1% by year -- it was
tracking market drift, not move authenticity. Uses the equal-weighted EQ market-index proxy from
scripts/build_market_index.py (no real index/NIFTY series is ingested; this is the "serviceable
proxy" per instruction, stated explicitly here and in the phase doc, not left implicit).

Same direction-aware collapse definition as compute_outcome_labels.py, but every price is first
divided by the market index level for that day before comparing -- so "collapsed" now means "the
stock's move reversed relative to the market," not "the stock's raw price fell," which is exactly
the distinction Check 1 showed the raw label was blind to.
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
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, build_symbol_history

PRE_MOVE_LOOKBACK = 20
COLLAPSE_HORIZON = 90

INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "market_index.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "outcome_labels_relative.csv"

def load_market_index() -> dict[str, float]:
    idx = {}
    with open(INDEX_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            idx[row["date"]] = float(row["index_level"])
    return idx

def relative_g(hist, event_date: str, market_index: dict[str, float]) -> float | None:
    row = hist.price_row_as_of(event_date, FAR_FUTURE_AS_OF)
    if row is None:
        return None
    idx_level = market_index.get(event_date)
    if idx_level is None or idx_level == 0:
        return None
    return (row["close_price"] * hist.cum_factor_up_to(event_date)) / idx_level

def compute_relative_outcome(hist, event_date: str, direction: int, market_index: dict[str, float]) -> dict:
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {"collapsed_relative": None, "excluded_reason": "event_date not in symbol's trading calendar"}

    pre_idx = idx - PRE_MOVE_LOOKBACK
    collapse_idx = idx + COLLAPSE_HORIZON
    if pre_idx < 0:
        return {"collapsed_relative": None, "excluded_reason": "insufficient pre-move history"}
    if collapse_idx >= len(days):
        return {"collapsed_relative": None, "excluded_reason": "insufficient forward history"}

    pre_date = days[pre_idx]
    last_date = days[collapse_idx]
    if hist.structural_break_in_window(pre_date, last_date):
        return {"collapsed_relative": None, "excluded_reason": "structural break inside the label window"}

    base = relative_g(hist, pre_date, market_index)
    if base is None or base == 0:
        return {"collapsed_relative": None, "excluded_reason": "no usable pre-move base (market index gap)"}

    collapsed = False
    for k in range(idx + 1, collapse_idx + 1):
        rk = relative_g(hist, days[k], market_index)
        if rk is None:
            continue
        if direction > 0 and rk < base:
            collapsed = True
            break
        if direction < 0 and rk > base:
            collapsed = True
            break
    return {"collapsed_relative": collapsed, "excluded_reason": None}

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    market_index = load_market_index()
    print(f"Loaded market index: {len(market_index)} dates")

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
        for e in symbol_events:
            direction = 1 if float(e["return_1d"]) > 0 else -1
            outcome = compute_relative_outcome(hist, e["event_date"], direction, market_index)
            out_rows.append({
                "symbol": symbol, "event_date": e["event_date"], "direction": direction,
                "delivery_pct": e["delivery_pct"], "delivery_pct_percentile_60d": e["delivery_pct_percentile_60d"],
                "zscore_60d": e["zscore_60d"], "volume_ratio": e["volume_ratio"],
                "cap_band": e["cap_band"], "asm_stage": e["asm_stage"], "gsm_stage": e["gsm_stage"],
                "collapsed_relative": outcome["collapsed_relative"],
                "excluded_reason": outcome["excluded_reason"],
            })
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(by_symbol)} symbols, {time.time() - t0:.0f}s elapsed")

    print(f"Done in {time.time() - t0:.0f}s")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Persisted {len(out_rows)} rows to {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
