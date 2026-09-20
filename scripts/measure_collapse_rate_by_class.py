"""Phase 7b measurement, run before any report generation, per explicit instruction: does
Phase 7b's classification (GROUNDED/PARTIALLY_GROUNDED/UNEXPLAINED/UNEXPLAINED_ISOLATED) separate
on real outcomes (collapsed_30d/60d/90d, Phase 6's own ground-truth label), and does that survive
stratifying by market-cap band the way Phase 6's own Simpson's-paradox finding says a pooled
comparison alone cannot be trusted to show (docs/phase6_signals.md: micro collapses at a
structurally different base rate than mega, so a pooled difference between classes could just be
composition -- UNEXPLAINED_ISOLATED being micro-skewed, say -- not a real difference in outcome).

collapsed_30d/60d/90d are NOT persisted anywhere yet (Phase 6's compute_outcome_labels.py only
computed the fixed 90-session definition) -- computed fresh here, once, using the identical
direction-aware "crossed back through the pre-move base" definition, just evaluated at three
horizons from a single forward scan instead of one.

Per instruction: thresholds are NOT tuned here or anywhere else to produce separation. This script
reports what the already-approved classification gives -- if classes don't separate within bands,
that is stated as plainly as if they did, and is consistent with Phase 6's 0.611-0.70 ceiling
finding, not a contradiction of it.
"""
from __future__ import annotations
import bisect
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, build_symbol_history

PRE_MOVE_LOOKBACK = 20
HORIZONS = (30, 60, 90)

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLASSIFICATIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_classifications.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "collapse_rate_by_class.csv"

def g(hist, event_date: str, as_of: str) -> float | None:
    row = hist.price_row_as_of(event_date, as_of)
    if row is None:
        return None
    return row["close_price"] * hist.cum_factor_up_to(event_date)

def compute_multi_horizon_collapse(hist, event_date: str, direction: int) -> dict[int, bool | None]:
    """Returns {30: bool|None, 60: bool|None, 90: bool|None} -- collapsed_Nd is None (excluded,
    not defaulted) if the pre-move base doesn't exist, fewer than N forward sessions exist yet, or
    a structural break falls in (pre-move-base date, event_date+N]. Each horizon's coverage is
    independent -- a recent event can have a usable collapsed_30d with no usable collapsed_90d yet."""
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {h: None for h in HORIZONS}

    pre_idx = idx - PRE_MOVE_LOOKBACK
    if pre_idx < 0:
        return {h: None for h in HORIZONS}
    pre_date = days[pre_idx]
    base = g(hist, pre_date, FAR_FUTURE_AS_OF)
    if base is None or base == 0:
        return {h: None for h in HORIZONS}

    max_h = max(HORIZONS)
    scan_end = min(idx + max_h, len(days) - 1)
    first_collapse_k: int | None = None
    for k in range(idx + 1, scan_end + 1):
        gk = g(hist, days[k], FAR_FUTURE_AS_OF)
        if gk is None:
            continue
        if (direction > 0 and gk < base) or (direction < 0 and gk > base):
            first_collapse_k = k
            break

    out: dict[int, bool | None] = {}
    for h in HORIZONS:
        collapse_idx = idx + h
        if collapse_idx >= len(days):
            out[h] = None
            continue
        if hist.structural_break_in_window(pre_date, days[collapse_idx]):
            out[h] = None
            continue
        out[h] = first_collapse_k is not None and first_collapse_k <= collapse_idx
    return out

def load_direction() -> dict[tuple[str, str], int]:
    directions = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            directions[(row["symbol"], row["event_date"])] = 1 if float(row["return_1d"]) > 0 else -1
    return directions

def load_classifications() -> list[dict]:
    with open(CLASSIFICATIONS_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    classifications = load_classifications()
    print(f"Loaded {len(classifications)} classified events")
    directions = load_direction()

    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for c in classifications:
        by_symbol[c["symbol"]].append(c)

    out_rows = []
    t0 = time.time()
    n_symbols = 0
    for symbol, events in by_symbol.items():
        n_symbols += 1
        hist = build_symbol_history(conn, symbol)
        for e in events:
            direction = directions.get((symbol, e["event_date"]))
            if direction is None:
                continue
            collapse = compute_multi_horizon_collapse(hist, e["event_date"], direction)
            out_rows.append({
                "symbol": symbol, "event_date": e["event_date"],
                "classification": e["classification"], "cap_band": e["cap_band"],
                "collapsed_30d": collapse[30], "collapsed_60d": collapse[60], "collapsed_90d": collapse[90],
            })
        if n_symbols % 500 == 0:
            print(f"  ...{n_symbols}/{len(by_symbol)} symbols, {time.time() - t0:.0f}s elapsed")

    print(f"Done in {time.time() - t0:.0f}s")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Persisted {len(out_rows)} rows to {OUTPUT_PATH}")

    print("\n=== POOLED collapse rate by class (composition NOT controlled -- see stratified table below) ===")
    for horizon in HORIZONS:
        field = f"collapsed_{horizon}d"
        print(f"\n-- {horizon}-session horizon --")
        by_class: dict[str, list[bool]] = defaultdict(list)
        for r in out_rows:
            v = r[field]
            if v in ("", None):
                continue
            by_class[r["classification"]].append(v is True)
        for cls in sorted(by_class):
            vals = by_class[cls]
            n = len(vals)
            rate = 100 * sum(vals) / n if n else float("nan")
            print(f"  {cls:32s} n={n:6d}  collapse_rate={rate:5.1f}%")

    print("\n=== STRATIFIED BY MARKET-CAP BAND (n per cell shown -- thin cells are not equal evidence) ===")
    for horizon in HORIZONS:
        field = f"collapsed_{horizon}d"
        print(f"\n-- {horizon}-session horizon --")
        by_cell: dict[tuple[str, str], list[bool]] = defaultdict(list)
        for r in out_rows:
            v = r[field]
            if v in ("", None):
                continue
            by_cell[(r["cap_band"], r["classification"])].append(v is True)
        bands = sorted({k[0] for k in by_cell})
        classes = sorted({k[1] for k in by_cell})
        for band in bands:
            print(f"  [{band}]")
            for cls in classes:
                vals = by_cell.get((band, cls), [])
                n = len(vals)
                if n == 0:
                    print(f"    {cls:32s} n=0")
                    continue
                rate = 100 * sum(vals) / n
                print(f"    {cls:32s} n={n:6d}  collapse_rate={rate:5.1f}%")

    conn.close()

if __name__ == "__main__":
    main()
