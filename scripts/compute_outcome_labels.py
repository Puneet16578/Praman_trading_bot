"""Phase 6 pre-flight, part 2: outcome labels -- whether a catalogued move actually held or
reversed, independent of ASM/GSM status (Part 1 found ASM/GSM is an exchange-attention proxy, not
a manipulation proxy -- docs/phase6_signals.md). This is the ground truth Part 2 re-tests delivery
divergence against.

Deliberately retrospective, unlike every signal this project builds: an outcome label is allowed
to use knowledge from AFTER the event (that is what makes it useful as ground truth). Still
corporate-action-adjusted and structural-break-excluded via the same machinery as Phase 5
(FAR_FUTURE_AS_OF is the correct as_of for "what actually happened," not a Section 7 violation --
this is labeling, not a live signal).

For each catalogued event with direction sign(return_1d):
  - forward_return_Nd (N=30,60,90): adjusted return from event_date to the Nth real trading
    session after it, or None if a structural break falls in between or fewer than N future
    sessions exist yet.
  - collapsed: did any closing day in (event_date, event_date+90] cross back through the
    pre-move base (close 20 real trading sessions before event_date), in the direction opposite
    the event's own move -- an up-move that later closes below its pre-move base, or a down-move
    that later closes above it. None (excluded, not defaulted) if the pre-move base doesn't exist
    (event within the first 20 sessions of the symbol's history), fewer than 90 forward sessions
    exist yet, or a structural break falls anywhere in (pre-move-base date, event_date+90].
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
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, _return, build_symbol_history

ISIN_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"

PRE_MOVE_LOOKBACK = 20
HORIZONS = (30, 60, 90)
COLLAPSE_HORIZON = 90

INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "outcome_labels.csv"

def g(hist, event_date: str, as_of: str) -> float | None:
    row = hist.price_row_as_of(event_date, as_of)
    if row is None:
        return None
    return row["close_price"] * hist.cum_factor_up_to(event_date)

def compute_outcome(hist, event_date: str, direction: int) -> dict:
    """Returns a dict with forward_return_30d/60d/90d and collapsed, each None if not computable,
    plus a human-readable `excluded_reason` set whenever anything was excluded."""
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {"forward_return_30d": None, "forward_return_60d": None, "forward_return_90d": None,
                "collapsed": None, "excluded_reason": "event_date not in symbol's trading calendar"}

    out: dict = {"excluded_reason": None}
    for h in HORIZONS:
        fwd_idx = idx + h
        if fwd_idx >= len(days):
            out[f"forward_return_{h}d"] = None
            continue
        out[f"forward_return_{h}d"] = _return(hist, event_date, days[fwd_idx], as_of=FAR_FUTURE_AS_OF)

    pre_idx = idx - PRE_MOVE_LOOKBACK
    collapse_idx = idx + COLLAPSE_HORIZON
    if pre_idx < 0:
        out["collapsed"] = None
        out["excluded_reason"] = "insufficient pre-move history (event within first 20 sessions)"
        return out
    if collapse_idx >= len(days):
        out["collapsed"] = None
        out["excluded_reason"] = "insufficient forward history (fewer than 90 sessions since event)"
        return out

    pre_date = days[pre_idx]
    last_date = days[collapse_idx]
    if hist.structural_break_in_window(pre_date, last_date):
        out["collapsed"] = None
        out["excluded_reason"] = "structural break (demerger/capital reduction) inside the label window"
        return out

    base = g(hist, pre_date, FAR_FUTURE_AS_OF)
    if base is None or base == 0:
        out["collapsed"] = None
        out["excluded_reason"] = "no usable pre-move base price"
        return out

    collapsed = False
    for k in range(idx + 1, collapse_idx + 1):
        gk = g(hist, days[k], FAR_FUTURE_AS_OF)
        if gk is None:
            continue
        if direction > 0 and gk < base:
            collapsed = True
            break
        if direction < 0 and gk > base:
            collapsed = True
            break
    out["collapsed"] = collapsed
    return out

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    with open(INPUT_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Loaded {len(events)} catalogued events from {INPUT_PATH.name}")

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        by_symbol.setdefault(e["symbol"], []).append(e)
    print(f"Across {len(by_symbol)} symbols")

    # Amendment 4 prep item 5: stitch a renamed security's symbols so a 90-session forward window
    # that crosses a rename (P8-010) doesn't starve for real trading days it should be able to see.
    # Missing map file falls back to no stitching (P8-006's lesson -- not a hard dependency).
    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}
    if not symbol_groups:
        print("No ISIN map found -- computing per-symbol, unstitched (run scripts/build_isin_map.py to enable stitching)")

    out_rows = []
    t0 = time.time()
    for i, (symbol, symbol_events) in enumerate(by_symbol.items()):
        hist = build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]))
        for e in symbol_events:
            direction = 1 if float(e["return_1d"]) > 0 else -1
            outcome = compute_outcome(hist, e["event_date"], direction)
            out_rows.append({
                "symbol": symbol, "event_date": e["event_date"], "direction": direction,
                "delivery_pct": e["delivery_pct"], "delivery_pct_percentile_60d": e["delivery_pct_percentile_60d"],
                "zscore_60d": e["zscore_60d"], "volume_ratio": e["volume_ratio"],
                "asm_stage": e["asm_stage"], "gsm_stage": e["gsm_stage"],
                "forward_return_30d": outcome["forward_return_30d"],
                "forward_return_60d": outcome["forward_return_60d"],
                "forward_return_90d": outcome["forward_return_90d"],
                "collapsed": outcome["collapsed"],
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
