"""P8-007 scoping, item 4: quantify contamination and re-run Phase 8b's feature AUC table
excluding contaminated events, as a sensitivity check only (measurement, no fix applied).

An event D (symbol, event_date) is CONTAMINATED if any of the 96 split/bonus shape-matched dates
for the SAME symbol falls inside D's own 60-session trailing window OR 90-session forward window
-- i.e. the shape-matched date S is within [D-60 sessions, D+90 sessions] on that symbol's own
trading calendar (session-based distance, not calendar days, matching this project's convention).
"""
from __future__ import annotations
import bisect
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.event_catalogue import build_symbol_history

TRAIN_CUTOFF = "2026-01-01"
TOLERANCE_PP = 2.0
TARGET_SHAPES_PCT = [-33.3, -50.0, -66.7, -75.0, -80.0, -83.3, -90.0]
ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"


def matches_target_shape(pct: float) -> float | None:
    for shape in TARGET_SHAPES_PCT:
        if abs(pct - shape) <= TOLERANCE_PP:
            return shape
    return None


def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = list(csv.DictReader(f))

    by_symbol: dict[str, list[dict]] = {}
    for r in catalogue:
        by_symbol.setdefault(r["symbol"], []).append(r)

    shape_dates_by_symbol: dict[str, list[str]] = {}
    for r in catalogue:
        r1 = r["return_1d"]
        if r1 in ("", "None"):
            continue
        pct = float(r1) * 100
        if matches_target_shape(pct) is not None:
            shape_dates_by_symbol.setdefault(r["symbol"], []).append(r["event_date"])

    print(f"{sum(len(v) for v in shape_dates_by_symbol.values())} shape-matched dates across "
          f"{len(shape_dates_by_symbol)} symbols")

    contaminated: set[tuple[str, str]] = set()
    for symbol, shape_dates in shape_dates_by_symbol.items():
        hist = build_symbol_history(conn, symbol)
        days = hist.trading_days
        shape_indices = []
        for sd in shape_dates:
            idx = bisect.bisect_left(days, sd)
            if idx < len(days) and days[idx] == sd:
                shape_indices.append(idx)
        if not shape_indices:
            continue
        for e in by_symbol[symbol]:
            d_idx = bisect.bisect_left(days, e["event_date"])
            if d_idx >= len(days) or days[d_idx] != e["event_date"]:
                continue
            for s_idx in shape_indices:
                if (d_idx - 90) <= s_idx <= (d_idx + 60):
                    contaminated.add((symbol, e["event_date"]))
                    break

    conn.close()

    train_contam = {k for k in contaminated if k[1] < TRAIN_CUTOFF}
    holdout_contam = {k for k in contaminated if k[1] >= TRAIN_CUTOFF}
    print(f"\nTotal contaminated catalogue events: {len(contaminated)}")
    print(f"  TRAIN: {len(train_contam)} of 64,450 ({100*len(train_contam)/64450:.3f}%)")
    print(f"  HOLD-OUT: {len(holdout_contam)} of 10,850 ({100*len(holdout_contam)/10850:.3f}%)")

    out_path = ROOT / "data" / "raw" / "phase10_p8007_contaminated_events.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "event_date"])
        for k in sorted(contaminated):
            w.writerow(k)
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
