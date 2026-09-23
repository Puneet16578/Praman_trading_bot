"""Phase 8 robustness check 1(c)/(3)/(4): a NEW outcome label anchored at the event-day close
(not event_date-20, which check 1(b) confirmed collapsed_90d shares with return_20d_context_only,
numerically verified in docs/phase8_robustness_checks.md) and market-relative (dividing by the
equal-weighted EQ index), removing the mechanical coupling that check identified.

Pre-registered in docs/phase8_robustness_checks.md BEFORE this script was run:
  PRIMARY:   signed 90-session market-relative forward return from close(event_date) < 0
  SECONDARY: the same return < -0.10
"signed" = multiplied by the event's own initial direction (return_1d sign), the same
direction-aware convention collapsed_90d/collapsed_relative already use. This is an ENDPOINT
return (t to t+90), not the path-dependent "crossed back at any point" scan those two labels use --
a real methodological difference, stated in the pre-registration rather than discovered later.

Also computes, for every 2026 hold-out event with no computable 90-session outcome, whether that
is because the GLOBAL calendar (market_index.csv's own dates) also lacks 90 sessions after
event_date (genuine "too close to data's own end") or because the global calendar has enough
sessions but THIS SYMBOL's own trading history ends first (heuristic flag for delisting/suspension
inside the window -- addition 4 of the robustness review). Stated as a heuristic, not a confirmed
delisting determination -- this project has no direct delisting-event feed.
"""
from __future__ import annotations
import bisect
import csv
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, build_symbol_history

HORIZON = 90
TRAIN_CUTOFF = "2026-01-01"
SECONDARY_THRESHOLD = -0.10

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
SURVIVORSHIP_PATH = ROOT / "data" / "processed" / "phase8_survivorship_check.csv"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"


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


def compute_t0_relative(hist, event_date: str, direction: int, market_index: dict[str, float],
                          global_dates: list[str]) -> dict:
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "event_date not in symbol's trading calendar", "survivorship_flag": ""}

    end_idx = idx + HORIZON
    if end_idx >= len(days):
        g_idx = bisect.bisect_left(global_dates, event_date)
        global_has_horizon = (g_idx + HORIZON) < len(global_dates)
        flag = "possible_delisting_or_suspension" if global_has_horizon else "data_cutoff_proximity"
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "insufficient forward history", "survivorship_flag": flag}

    end_date = days[end_idx]
    if hist.structural_break_in_window(event_date, end_date):
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "structural break inside the label window", "survivorship_flag": ""}

    base = relative_g(hist, event_date, market_index)
    end = relative_g(hist, end_date, market_index)
    if base is None or base == 0 or end is None:
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "no usable relative price (market index gap)", "survivorship_flag": ""}

    raw_relative_return = end / base - 1.0
    signed = direction * raw_relative_return
    return {"signed_return_90d": signed, "collapsed_t0_primary": signed < 0.0,
            "collapsed_t0_secondary": signed < SECONDARY_THRESHOLD, "excluded_reason": None,
            "survivorship_flag": ""}


def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    market_index = load_market_index()
    global_dates = sorted(market_index.keys())
    print(f"Loaded market index: {len(global_dates)} dates, {global_dates[0]} -> {global_dates[-1]}")

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Loaded {len(events)} catalogued events")

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        by_symbol.setdefault(e["symbol"], []).append(e)

    # Amendment 4 prep item 5: stitch a renamed security's symbols (P8-010) so this label's
    # 90-session forward window doesn't starve for real trading days just because this project's
    # own tables are keyed by symbol string. Missing map file falls back to no stitching
    # (P8-006's lesson -- not a hard dependency).
    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}

    out_rows = []
    survivorship_rows = []
    t0 = time.time()
    for i, (symbol, symbol_events) in enumerate(by_symbol.items()):
        hist = build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]))
        for e in symbol_events:
            direction = 1 if float(e["return_1d"]) > 0 else -1
            result = compute_t0_relative(hist, e["event_date"], direction, market_index, global_dates)
            out_rows.append({
                "symbol": symbol, "event_date": e["event_date"], "direction": direction,
                "cap_band": e["cap_band"],
                "signed_return_90d": result["signed_return_90d"],
                "collapsed_t0_primary": result["collapsed_t0_primary"],
                "collapsed_t0_secondary": result["collapsed_t0_secondary"],
                "excluded_reason": result["excluded_reason"],
            })
            if result["survivorship_flag"] and e["event_date"] >= TRAIN_CUTOFF:
                survivorship_rows.append({
                    "symbol": symbol, "event_date": e["event_date"], "flag": result["survivorship_flag"],
                    "symbol_last_trading_day": hist.trading_days[-1] if hist.trading_days else "",
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

    with open(SURVIVORSHIP_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "event_date", "flag", "symbol_last_trading_day"])
        writer.writeheader()
        writer.writerows(survivorship_rows)
    print(f"Persisted {len(survivorship_rows)} 2026 hold-out survivorship-flagged rows to {SURVIVORSHIP_PATH}")

    counts = Counter(r["flag"] for r in survivorship_rows)
    print(f"Survivorship breakdown (2026 hold-out events lacking a 90d outcome, of any label): {dict(counts)}")

    excl_counts = Counter(r["excluded_reason"] for r in out_rows if r["event_date"] >= TRAIN_CUTOFF)
    print(f"2026 hold-out exclusion-reason breakdown (new t0-relative label): {dict(excl_counts)}")

    conn.close()


if __name__ == "__main__":
    main()
