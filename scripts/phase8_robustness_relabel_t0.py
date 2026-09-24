"""Phase 8 robustness check 1(c)/(3)/(4): a NEW outcome label anchored at the event-day close
(not event_date-20, which check 1(b) confirmed collapsed_90d shares with return_20d_context_only,
numerically verified in docs/phase8_robustness_checks.md) and market-relative (dividing by the
equal-weighted EQ index), removing the mechanical coupling that check identified.

Pre-registered in docs/phase8_robustness_checks.md BEFORE this script was run:
  PRIMARY:   signed 90-session market-relative forward return from close(event_date) < 0
  SECONDARY: the same return < -0.10
"signed" = multiplied by the event's own initial direction (return_1d sign), the same
direction-aware convention collapsed_90d/collapsed_relative already use.

Amendment 4 prep round 4 (docs/phase10_amendment4_prep4.md): the "90-session" horizon itself is
REDEFINED here, superseding the own-session definition rounds 1-3 used. The own-session definition
(the symbol's own 90th real EQ/BE/BZ-extended trading day) was found, by direct diagnosis, to
create a real selection problem: missingness under it is NOT random -- it is highest for the
smallest, least liquid names (TRAIN, buffer>=30: Micro 2.09% vs. Mega 1.20% missing, a clean
monotonic gradient by cap_band -- scripts/phase10_amendment4_selection_problem.py), because a
thinly-traded stock takes longer in CALENDAR time to accumulate 90 REAL sessions, and no fixed
buffer can bound that tail (round 3's own decay-curve measurement found no plateau within 120
sessions). The label now uses a GLOBAL 90-session horizon instead: the return from close(event_date)
to the LAST AVAILABLE close (across EQ, extended through BE/BZ per P8-012) ON OR BEFORE the 90th
GLOBAL trading session after event_date -- with a STALENESS CAP (10 global sessions): if the last
available close is more than 10 sessions stale relative to that global target date, the outcome is
MISSING (a genuine, uncensored gap -- likely suspension/delisting -- not silently extrapolated
across). The market index is evaluated at the SAME date as whichever close is actually used (the
existing `relative_g` convention, unchanged) -- comparing a stock's own last real observation to
the market AS OF THAT SAME DATE, never to a later index level the stock itself never had a chance
to keep pace with.

Also computes, for every 2026 hold-out event with no computable 90-session outcome, whether that
is because the GLOBAL calendar (market_index.csv's own dates) also lacks 90 sessions after
event_date (genuine "too close to data's own end") or because the staleness cap was exceeded
(heuristic flag for delisting/suspension inside the window). Stated as a heuristic, not a confirmed
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
STALENESS_CAP_SESSIONS = 10  # Amendment 4 prep round 4: beyond this many GLOBAL sessions of
                              # staleness relative to the target date, the outcome is MISSING
                              # (genuine suspension/delisting), not extrapolated across the gap

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
    """Amendment 4 prep round 4: GLOBAL 90-session horizon with a staleness cap, superseding the
    own-session definition (see module docstring). `target_date` is the 90th GLOBAL trading
    session after event_date; the outcome uses the symbol's own LAST AVAILABLE close on or before
    `target_date` (across EQ/BE/BZ, via hist's own extend_with_series), evaluating the market
    index at that SAME observed date (relative_g's existing convention) -- never comparing a
    stale price to a later index level the symbol had no chance to keep pace with. If that last
    available close is more than STALENESS_CAP_SESSIONS global sessions before target_date, the
    outcome is MISSING, not extrapolated across the gap."""
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "event_date not in symbol's trading calendar", "survivorship_flag": ""}

    g_idx = bisect.bisect_left(global_dates, event_date)
    if g_idx >= len(global_dates) or global_dates[g_idx] != event_date:
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "event_date not in global trading calendar", "survivorship_flag": ""}

    target_idx = g_idx + HORIZON
    if target_idx >= len(global_dates):
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "insufficient forward history (global calendar)",
                "survivorship_flag": "data_cutoff_proximity"}
    target_date = global_dates[target_idx]

    last_idx = bisect.bisect_right(days, target_date) - 1
    if last_idx < idx:
        # No trading day at all for this symbol between event_date and target_date (should only
        # happen if event_date is itself the symbol's last-ever row) -- treat as maximally stale,
        # not as "no data."
        last_idx = idx
    last_date = days[last_idx]

    last_g_idx = bisect.bisect_left(global_dates, last_date)
    staleness_sessions = target_idx - last_g_idx
    if staleness_sessions > STALENESS_CAP_SESSIONS:
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": f"stale beyond {STALENESS_CAP_SESSIONS}-session cap "
                                    f"({staleness_sessions} sessions stale)",
                "survivorship_flag": "possible_delisting_or_suspension"}

    if hist.structural_break_in_window(event_date, last_date):
        return {"signed_return_90d": None, "collapsed_t0_primary": None, "collapsed_t0_secondary": None,
                "excluded_reason": "structural break inside the label window", "survivorship_flag": ""}

    base = relative_g(hist, event_date, market_index)
    end = relative_g(hist, last_date, market_index)
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

    # Amendment 4 prep round 2, item 1(b)/2 fix (P8-012): extend through BE/BZ (trade-for-trade
    # settlement), labels only -- the event catalogue itself stays EQ-only. See
    # compute_outcome_labels.py's identical wiring for the full rationale.
    out_rows = []
    survivorship_rows = []
    t0 = time.time()
    for i, (symbol, symbol_events) in enumerate(by_symbol.items()):
        hist = build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]),
                                     extend_with_series=("BE", "BZ"))
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
