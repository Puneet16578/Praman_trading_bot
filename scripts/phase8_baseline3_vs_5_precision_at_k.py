"""Phase 8 follow-up: precision@k for baseline 3 (disclosure tier alone) vs. baseline 5 (full
agent system) at k = 10, 20, 50, 100, both ranked by the SAME categorical TRAIN-period score with
volume_ratio as the tie-break (ascending -- LOW volume_ratio ranks first, matching the
empirically-correct direction already established in
scripts/phase8_precision_at_k_alternative_orderings.py: TRAIN rank-sum AUC for volume_ratio in the
naive "high predicts collapse" direction is 0.4005, so LOW volume_ratio is what actually predicts
collapse on this data). This resolves the "255 tied at the max score" coarseness a pure categorical
ranking has, without changing what each baseline's PRIMARY score means.

Decision rule (specified in advance, applied mechanically below, not adjusted after seeing the
result): if baseline 5 beats baseline 3 at k=20 AND k=50 by more than the CI width, the
narrow-claim branch is taken (isolation adds ranking power disclosure tier cannot express, AUC/
Brier ties). Otherwise, the architecture-adds-nothing-to-classification branch is taken.
"""
from __future__ import annotations
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PRIMARY_HORIZON = 90
K_VALUES = (10, 20, 50, 100)

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
TRAIN_COLLAPSE_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
PROD_CLASSIFICATIONS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
HOLDOUT_OUTCOMES_PATH = ROOT / "data" / "processed" / "phase8_2026_outcomes.csv"

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))

def load_train_rate_table(key_field: str) -> dict[tuple[str, str], float]:
    outcomes: dict[tuple[str, str], bool] = {}
    with open(TRAIN_COLLAPSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            v = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if v == "":
                continue
            outcomes[(row["symbol"], row["event_date"])] = v == "True"
    cells: dict[tuple[str, str], list[bool]] = {}
    with open(PROD_CLASSIFICATIONS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            key = (row["symbol"], row["event_date"])
            if key not in outcomes:
                continue
            cells.setdefault((row[key_field], row["cap_band"]), []).append(outcomes[key])
    return {cell: sum(v) / len(v) for cell, v in cells.items() if v}

def load_holdout() -> list[dict]:
    class_by_key: dict[tuple[str, str], dict] = {}
    with open(HOLDOUT_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            class_by_key[(row["symbol"], row["event_date"])] = row

    vr_by_key: dict[tuple[str, str], float] = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] < "2026-01-01":
                continue
            v = row["volume_ratio"]
            if v not in ("", "None"):
                vr_by_key[(row["symbol"], row["event_date"])] = float(v)

    out = []
    with open(HOLDOUT_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            actual_str = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if actual_str == "":
                continue
            key = (row["symbol"], row["event_date"])
            cls_row = class_by_key.get(key)
            vr = vr_by_key.get(key)
            if cls_row is None or vr is None:
                continue
            out.append({
                "symbol": row["symbol"], "event_date": row["event_date"],
                "classification": row["classification"], "cap_band": row["cap_band"],
                "disclosure_tier": cls_row["disclosure_tier"], "volume_ratio": vr,
                "actual": actual_str == "True",
            })
    return out

def precision_at_k(ranked: list[dict], k: int) -> tuple[int, int, float, float, float]:
    top = ranked[:k]
    hits = sum(1 for x in top if x["actual"])
    n = len(top)
    p, lo, hi = wilson_ci(hits, n)
    return hits, n, p, lo, hi

def main() -> None:
    disclosure_scores = load_train_rate_table("disclosure_tier")
    classification_scores = load_train_rate_table("classification")
    holdout = load_holdout()
    print(f"{len(holdout)} hold-out events with disclosure_tier, classification, volume_ratio, and a known {PRIMARY_HORIZON}d outcome")

    base_rate = sum(1 for e in holdout if e["actual"]) / len(holdout)
    print(f"Base rate: {100*base_rate:.1f}% (n={len(holdout)})")

    # Primary sort: descending categorical TRAIN score. Tie-break: ASCENDING volume_ratio (low
    # volume_ratio ranks first within a tie -- the empirically correct direction).
    b3_ranked = sorted(
        holdout,
        key=lambda e: (-disclosure_scores.get((e["disclosure_tier"], e["cap_band"]), 0.5), e["volume_ratio"]),
    )
    b5_ranked = sorted(
        holdout,
        key=lambda e: (-classification_scores.get((e["classification"], e["cap_band"]), 0.5), e["volume_ratio"]),
    )

    print(f"\n{'='*100}\nPrecision@k: Baseline 3 (disclosure tier alone) vs Baseline 5 (full system), volume_ratio tie-break\n{'='*100}")
    print(f"{'k':>5s} | {'Baseline 3':^32s} | {'Baseline 5':^32s} | {'Gap':>8s}  CI-width-exceeded?")
    print(f"{'':>5s} | {'hits/n = rate [CI]':^32s} | {'hits/n = rate [CI]':^32s} |")
    decision_data = {}
    for k in K_VALUES:
        h3, n3, p3, lo3, hi3 = precision_at_k(b3_ranked, k)
        h5, n5, p5, lo5, hi5 = precision_at_k(b5_ranked, k)
        gap = p5 - p3
        exceeds = lo5 > hi3  # baseline 5's CI lower bound clears baseline 3's CI upper bound
        decision_data[k] = (h3, n3, p3, lo3, hi3, h5, n5, p5, lo5, hi5, exceeds)
        b3_str = f"{h3}/{n3} = {100*p3:.1f}% [{100*lo3:.1f},{100*hi3:.1f}]"
        b5_str = f"{h5}/{n5} = {100*p5:.1f}% [{100*lo5:.1f},{100*hi5:.1f}]"
        print(f"{k:5d} | {b3_str:^32s} | {b5_str:^32s} | {100*gap:+7.1f}pp  {'YES' if exceeds else 'no'}")

    print(f"\n{'='*100}\nDECISION RULE\n{'='*100}")
    exceeds_20 = decision_data[20][-1]
    exceeds_50 = decision_data[50][-1]
    print(f"Baseline 5 CI clears baseline 3 CI at k=20: {exceeds_20}")
    print(f"Baseline 5 CI clears baseline 3 CI at k=50: {exceeds_50}")
    if exceeds_20 and exceeds_50:
        print("\n=> NARROW-CLAIM BRANCH: baseline 5 beats baseline 3 at both k=20 and k=50 by more")
        print("   than the CI width. State the narrow claim: isolation dimension adds ranking power")
        print("   disclosure tier structurally cannot express, while AUC/Brier tie.")
    else:
        print("\n=> NULL BRANCH: baseline 5 does NOT clear baseline 3's CI at both k=20 and k=50.")
        print("   State that the architecture adds nothing measurable to classification/ranking at")
        print("   these k -- its value is verification and reporting, not ranking power.")

if __name__ == "__main__":
    main()
