"""Amendment 4 prep round 4, item 1: confirm the selection problem on the OLD (own-session)
outcome definition before adopting the new one -- missing-outcome rate by cap_band,
volume_ratio_high, and delivery_low, TRAIN events with buffer>=30 sessions (comfortably past any
boundary-proximity effect, per round 3's own finding that the artifact clearly operates within
that range even though its full decay curve could not be cleanly measured).

Uses data/processed/phase8_relabel_t0_relative_OLD_own_session.csv (a preserved copy of the
own-session-definition label, taken before this round's redefinition) rather than the live
phase8_relabel_t0_relative.csv, which this round replaces.
"""
from __future__ import annotations
import bisect
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
OLD_LABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative_OLD_own_session.csv"
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"

TRAIN_CUTOFF = "2026-01-01"
HORIZON = 90
BUFFER_MIN = 30

DELIVERY_THRESHOLD = 13.3333
VOLUME_RATIO_BAND_MEDIAN = {
    "Micro": 5.0926, "Small": 6.8397, "Mid": 7.6364, "Large": 8.6042, "Mega": 7.4616,
}


def main() -> None:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        global_days = [r["date"] for r in csv.DictReader(f)]

    cap_band = {}
    with open(CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cap_band[(row["symbol"], row["event_date"])] = row["cap_band"]

    features = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["symbol"], row["event_date"])
            features[key] = {
                "delivery_pct_percentile_60d": row["delivery_pct_percentile_60d"],
                "volume_ratio": row["volume_ratio"],
            }

    with open(OLD_LABEL_PATH, encoding="utf-8") as f:
        labels = list(csv.DictReader(f))

    # Restrict to TRAIN, buffer>=30 (fully elapsed with real margin, per round 3's own finding
    # that boundary effects operate within roughly this range).
    eligible = []
    for r in labels:
        ed = r["event_date"]
        if ed >= TRAIN_CUTOFF:
            continue
        idx = bisect.bisect_left(global_days, ed)
        if not (idx < len(global_days) and global_days[idx] == ed):
            continue
        t90 = idx + HORIZON
        if t90 >= len(global_days):
            continue
        buffer = (len(global_days) - 1) - t90
        if buffer < BUFFER_MIN:
            continue
        eligible.append(r)

    print(f"TRAIN events, buffer>={BUFFER_MIN}: {len(eligible)}")

    def bucket(rows, keyfn):
        agg = defaultdict(lambda: [0, 0])  # [n, missing]
        for r in rows:
            key = keyfn(r)
            if key is None:
                continue
            agg[key][0] += 1
            if r["signed_return_90d"] in ("", "None"):
                agg[key][1] += 1
        return agg

    print("\n=== By cap_band ===")
    agg = bucket(eligible, lambda r: cap_band.get((r["symbol"], r["event_date"])))
    for band in ("Micro", "Small", "Mid", "Large", "Mega"):
        n, missing = agg.get(band, [0, 0])
        rate = 100 * missing / n if n else float("nan")
        print(f"  {band:8s} n={n:6d}  missing={missing:5d}  rate={rate:.3f}%")

    print("\n=== By volume_ratio_high (>= own band median) ===")
    def vol_high_key(r):
        band = cap_band.get((r["symbol"], r["event_date"]))
        f = features.get((r["symbol"], r["event_date"]))
        if band is None or f is None or f["volume_ratio"] in ("", "None"):
            return None
        return "HIGH" if float(f["volume_ratio"]) >= VOLUME_RATIO_BAND_MEDIAN.get(band, float("inf")) else "LOW"
    agg = bucket(eligible, vol_high_key)
    for k in ("LOW", "HIGH"):
        n, missing = agg.get(k, [0, 0])
        rate = 100 * missing / n if n else float("nan")
        print(f"  {k:8s} n={n:6d}  missing={missing:5d}  rate={rate:.3f}%")

    print("\n=== By delivery_low (< 13.3333 pooled threshold) ===")
    def delivery_low_key(r):
        f = features.get((r["symbol"], r["event_date"]))
        if f is None or f["delivery_pct_percentile_60d"] in ("", "None"):
            return None
        return "LOW" if float(f["delivery_pct_percentile_60d"]) < DELIVERY_THRESHOLD else "HIGH/NORMAL"
    agg = bucket(eligible, delivery_low_key)
    for k in ("HIGH/NORMAL", "LOW"):
        n, missing = agg.get(k, [0, 0])
        rate = 100 * missing / n if n else float("nan")
        print(f"  {k:12s} n={n:6d}  missing={missing:5d}  rate={rate:.3f}%")


if __name__ == "__main__":
    main()
