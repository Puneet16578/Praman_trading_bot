"""Phase 8 discipline: freeze classification thresholds on 2019-2025 data only, before touching
2026 at all. Distinct from data/processed/classification_thresholds.json (the PRODUCTION
thresholds, fit on the full available history through today -- entirely appropriate for a live
system that legitimately uses all data available at the time it runs). This script's output is
an EVALUATION-ONLY artifact: what the thresholds would have been had they been frozen at the end
of 2025, so Phase 8's test on 2026 is a genuine walk-forward hold-out, not a backtest against
thresholds that already saw the answer.

Two quantities need re-deriving on train-only data (the two genuinely period-pooled thresholds);
everything else in the classifier is already correctly scoped and needs no change:
- band_median_abs_return_20d: currently pooled across ALL years in the production thresholds.
- isolated_comovement_threshold: currently the p25 of same_date_event_count across ALL events.

Cap_band and same_date_event_count themselves are NOT re-derived here -- cap_band is already
computed per-calendar-year (a 2026 event's band uses only 2026 turnover data, the same way a live
system would), and same_date_event_count is an inherently same-day cross-sectional count (no
future information involved). Only the POOLED CUTOFF NUMBERS derived from looking across the
whole period needed freezing.
"""
from __future__ import annotations
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TRAIN_CUTOFF = "2026-01-01"  # events with event_date < this are TRAIN; >= this are the frozen 2026 hold-out

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLUSTERING_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "clustering.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase8_frozen_thresholds.json"

def load_catalogue() -> list[dict]:
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_comovement_counts() -> dict[tuple[str, str], int]:
    counts = {}
    with open(CLUSTERING_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            counts[(row["symbol"], row["event_date"])] = int(row["same_date_event_count"])
    return counts

def compute_quintile_bands(rows: list[dict]) -> dict[tuple[str, str], str]:
    """Unchanged from build_event_classifications.py -- per-YEAR quintiles, so this needs no
    train/test split of its own; included here only so band assignment is available to compute
    the train-only momentum medians below."""
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
    rows = load_catalogue()
    print(f"Loaded {len(rows)} catalogued events")
    train_rows = [r for r in rows if r["event_date"] < TRAIN_CUTOFF]
    holdout_rows = [r for r in rows if r["event_date"] >= TRAIN_CUTOFF]
    print(f"TRAIN (event_date < {TRAIN_CUTOFF}): {len(train_rows)} events")
    print(f"HOLD-OUT (event_date >= {TRAIN_CUTOFF}): {len(holdout_rows)} events -- not used below")

    bands = compute_quintile_bands(rows)  # per-year, so computing over all rows is fine/necessary
    # for band lookups later; TRAIN-ONLY restriction is applied to the MEDIAN computation itself.

    r20_by_band = defaultdict(list)
    for r in train_rows:
        v = r["return_20d_context_only"]
        if v in ("", "None"):
            continue
        band = bands[(r["symbol"], r["event_date"])]
        r20_by_band[band].append(abs(float(v)))
    band_medians = {b: float(np.median(vals)) for b, vals in r20_by_band.items()}
    print("\nTRAIN-ONLY per-band median abs(return_20d):")
    for b, m in sorted(band_medians.items()):
        print(f"  {b}: {m:.4f} (n={len(r20_by_band[b])})")

    comovement = load_comovement_counts()
    train_counts = [comovement[(r["symbol"], r["event_date"])] for r in train_rows
                     if (r["symbol"], r["event_date"]) in comovement]
    isolated_threshold = int(np.percentile(train_counts, 25))
    print(f"\nTRAIN-ONLY isolated_comovement_threshold (p25 of same_date_event_count, n={len(train_counts)}): {isolated_threshold}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "train_cutoff": TRAIN_CUTOFF,
            "train_event_count": len(train_rows),
            "holdout_event_count": len(holdout_rows),
            "band_median_abs_return_20d": band_medians,
            "isolated_comovement_threshold": isolated_threshold,
        }, f, indent=2)
    print(f"\nPersisted frozen (train-only) thresholds to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
