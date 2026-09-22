"""Phase 10 pre-registration: compute TRAIN-only (2019-2025) threshold values for the redesign
spec in docs/phase10_preregistration.md, BEFORE that document is written and committed. Computed
from data already in hand (2019-2025), never from 2026 -- consistent with
scripts/phase8_freeze_thresholds.py's own discipline.

Features and split methodology, per the pre-registration:
  - delivery_pct_percentile_60d: pooled TRAIN median (uniform across bands per
    docs/phase8b_clean_label_features.md item 3 -- a single pooled cutoff is defensible).
  - volume_ratio: per-band (5-way) TRAIN median, since item 3 found this feature real only in
    Small/Large/Mega and at chance in Micro/Mid -- computed for every band regardless, so the doc
    can state plainly which bands the interaction actually uses.
  - same_date_event_count: pooled TRAIN median (item 3 found this fairly uniform across bands,
    unlike volume_ratio -- a pooled cutoff matches how the evidence looked).
"""
from __future__ import annotations
import csv
import statistics
from pathlib import Path

TRAIN_CUTOFF = "2026-01-01"
ROOT = Path(__file__).resolve().parents[1]

CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLUSTERING_PATH = ROOT / "data" / "processed" / "clustering.csv"
TRAIN_CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"


def load_cap_bands() -> dict[tuple[str, str], str]:
    out = {}
    with open(TRAIN_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            out[(row["symbol"], row["event_date"])] = row["cap_band"]
    return out


def main() -> None:
    bands = load_cap_bands()
    print(f"TRAIN cap_band lookups: {len(bands)}")

    delivery_vals = []
    volume_by_band: dict[str, list[float]] = {b: [] for b in ("Micro", "Small", "Mid", "Large", "Mega")}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            key = (row["symbol"], row["event_date"])
            d = row["delivery_pct_percentile_60d"]
            if d not in ("", "None"):
                delivery_vals.append(float(d))
            v = row["volume_ratio"]
            band = bands.get(key)
            if v not in ("", "None") and band is not None:
                volume_by_band[band].append(float(v))

    same_date_vals = []
    with open(CLUSTERING_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["same_date_event_count"]
            if v not in ("", "None"):
                same_date_vals.append(float(v))

    print(f"\ndelivery_pct_percentile_60d: n={len(delivery_vals)}  "
          f"TRAIN median = {statistics.median(delivery_vals):.4f}")

    print(f"\nvolume_ratio TRAIN median by band:")
    for band in ("Micro", "Small", "Mid", "Large", "Mega"):
        vals = volume_by_band[band]
        print(f"  {band:8s} n={len(vals):6d}  median = {statistics.median(vals):.4f}")

    print(f"\nsame_date_event_count: n={len(same_date_vals)}  "
          f"TRAIN median = {statistics.median(same_date_vals):.4f}")


if __name__ == "__main__":
    main()
