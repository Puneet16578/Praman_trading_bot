"""Phase 7b classification-rule design check, round 2 (NOT the production classifier -- this
computes the real class distribution the proposed rules would produce, so the thresholds can be
shown and argued about before any agent/tool code is written).

SIGNATURE_PRESENT renamed to UNEXPLAINED_ISOLATED and redefined to exactly two conditions, per
instruction: disclosure tier NONE, and same_date_event_count below the real bottom-quartile
threshold (36, p25 across all 75,300 catalogued events -- "isolated" relative to this catalogue's
own real co-movement distribution, not an arbitrary round number). Volume_ratio, delivery, and
market-cap band are NOT part of this or any other class definition -- they are reported on every
event as separate fields (Phase 7b requirement 2), not folded into a conjunction a reader cannot
unpick. Co-movement is used here descriptively ("this move happened alongside few others that
day"), not predictively -- Phase 6 found it carries no predictive power for whether a move holds,
which is exactly why the new name describes what was OBSERVED (isolated in time) rather than
implying a verdict the way "SIGNATURE_PRESENT" did.

Design choice, stated so it can be corrected: within the NONE-disclosure tier, co-movement is
checked FIRST (a NONE-disclosure event with low co-movement is UNEXPLAINED_ISOLATED regardless of
its own momentum); a NONE-disclosure event that is NOT isolated (co-movement at or above the
threshold) falls back to the original momentum-based split (HIGH momentum -> PARTIALLY_GROUNDED,
per the still-open judgment call from round 1; LOW momentum -> plain UNEXPLAINED). The
ROUTINE_ONLY branch is untouched from round 1.
"""
from __future__ import annotations
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.disclosure_classification import classify_disclosure_window

DISCLOSURE_WINDOW_SESSIONS = 10

ISOLATED_COMOVEMENT_THRESHOLD = 36  # real p25 of same_date_event_count across all 75,300 events

def load_catalogue():
    with open("data/processed/event_catalogue_loose_zscore_only.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_comovement_counts():
    counts = {}
    with open("data/processed/clustering.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            counts[(row["symbol"], row["event_date"])] = int(row["same_date_event_count"])
    return counts

def compute_quintile_bands(rows):
    turnover_by_year = defaultdict(list)
    for r in rows:
        t = float(r["close_price_raw"]) * float(r["traded_qty"])
        turnover_by_year[r["event_date"][:4]].append(t)
    cuts = {}
    for year, vals in turnover_by_year.items():
        vals = sorted(vals)
        n = len(vals)
        cuts[year] = [vals[int(n * p)] for p in (0.2, 0.4, 0.6, 0.8)]
    names = ["Micro", "Small", "Mid", "Large", "Mega"]
    bands = {}
    for r in rows:
        t = float(r["close_price_raw"]) * float(r["traded_qty"])
        c = cuts[r["event_date"][:4]]
        idx = sum(1 for x in c if t > x)
        bands[(r["symbol"], r["event_date"])] = names[idx]
    return bands

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    rows = load_catalogue()
    print(f"Loaded {len(rows)} catalogued events")
    bands = compute_quintile_bands(rows)
    comovement = load_comovement_counts()
    print(f"Loaded co-movement counts for {len(comovement)} events; isolated threshold = same_date_event_count < {ISOLATED_COMOVEMENT_THRESHOLD}")

    # per-band median abs(return_20d), real, computed once
    r20_by_band = defaultdict(list)
    for r in rows:
        v = r["return_20d_context_only"]
        if v in ("", "None"):
            continue
        band = bands[(r["symbol"], r["event_date"])]
        r20_by_band[band].append(abs(float(v)))
    band_median = {b: float(np.median(vals)) for b, vals in r20_by_band.items()}
    print("Per-band median abs(return_20d), the momentum-persistence threshold:")
    for b, m in sorted(band_median.items()):
        print(f"  {b}: {m:.4f} (n={len(r20_by_band[b])})")

    fetched_symbols = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM corporate_announcements").fetchall()}

    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_symbol[r["symbol"]].append(r)

    import bisect
    from src.signals.event_catalogue import build_symbol_history

    class_counts = defaultdict(int)
    disclosure_x_momentum = defaultdict(int)
    unknown_coverage = 0
    no_r20 = 0
    t_symbols = 0
    for symbol, symbol_events in by_symbol.items():
        t_symbols += 1
        if symbol not in fetched_symbols:
            for e in symbol_events:
                unknown_coverage += 1
                class_counts["UNEXPLAINED_UNKNOWN_COVERAGE"] += 1
            continue

        ann_rows = conn.execute(
            "SELECT event_date, category FROM corporate_announcements WHERE symbol=? ORDER BY event_date", (symbol,)).fetchall()
        ann_dates = sorted(r[0] for r in ann_rows)
        rows_by_date: dict[str, list[dict]] = defaultdict(list)
        for event_date_, category in ann_rows:
            rows_by_date[event_date_].append({"category": category})

        hist = build_symbol_history(conn, symbol)
        days = hist.trading_days

        for e in symbol_events:
            event_date = e["event_date"]
            band = bands[(symbol, event_date)]
            r20_str = e["return_20d_context_only"]
            if r20_str in ("", "None"):
                no_r20 += 1
                continue
            momentum_high = abs(float(r20_str)) >= band_median.get(band, 0.0)

            idx = bisect.bisect_left(days, event_date)
            if idx < DISCLOSURE_WINDOW_SESSIONS:
                continue
            window_start = days[idx - DISCLOSURE_WINDOW_SESSIONS]
            lo = bisect.bisect_left(ann_dates, window_start)
            hi = bisect.bisect_left(ann_dates, event_date)
            window_dates = ann_dates[lo:hi]
            window_rows = []
            for d in window_dates:
                window_rows.extend(rows_by_date.get(d, []))
            tier = classify_disclosure_window(window_rows)  # SUBSTANTIVE / ROUTINE_ONLY / NONE

            disclosure_x_momentum[(tier, "HIGH" if momentum_high else "LOW")] += 1
            is_isolated = comovement.get((symbol, event_date), 10**9) < ISOLATED_COMOVEMENT_THRESHOLD

            if tier == "SUBSTANTIVE":
                cls = "GROUNDED"
            elif tier == "ROUTINE_ONLY":
                cls = "PARTIALLY_GROUNDED" if momentum_high else "UNEXPLAINED"
            else:  # NONE
                if is_isolated:
                    cls = "UNEXPLAINED_ISOLATED"
                else:
                    cls = "PARTIALLY_GROUNDED" if momentum_high else "UNEXPLAINED"
            class_counts[cls] += 1

    print(f"\n{t_symbols} symbols processed. {no_r20} events skipped (no return_20d). {unknown_coverage} events have unknown disclosure coverage.")

    print("\nRaw (disclosure tier x momentum) cell counts:")
    for key, n in sorted(disclosure_x_momentum.items()):
        print(f"  {key}: {n}")

    total = sum(class_counts.values())
    print(f"\nFinal class distribution ({total} events, including {unknown_coverage} unknown-coverage events folded in separately):")
    for cls, n in sorted(class_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cls}: {n} ({100*n/total:.1f}%)")

    conn.close()

if __name__ == "__main__":
    main()
