"""Phase 8b, item 3: re-run Phase 6's feature-vs-outcome AUC analysis under relative_t0_primary
(the label docs/phase8_robustness_checks.md Check 1 built to remove the collapsed_90d/return_20d
anchor coupling), for every feature Phase 6 originally tested against the coupled raw label:
volume_ratio, zscore_60d, return_20d_context_only, close_to_close_60d,
delivery_pct_percentile_60d, same_date_event_count, and ASM/GSM-labelled status.

Every Phase 6 feature conclusion (the momentum axis' design, "volume_ratio does not survive
stratification," "return_20d_context_only is the strongest predictor found") used the coupled raw
label -- this re-derives all of them under the clean label, TRAIN (2019-2025, the same population
Phase 6 measured) AND HOLD-OUT (2026, a genuine walk-forward check Phase 6 itself never had),
pooled and stratified by cap_band. Stratify before believing anything, per instruction.

AUC confidence intervals use the Hanley-McNeil (1982) normal approximation (closed-form, standard
for this purpose), not a bootstrap -- named explicitly since this project always names its methods:
  SE(AUC) = sqrt[ (AUC(1-AUC) + (n1-1)(Q1-AUC^2) + (n0-1)(Q0-AUC^2)) / (n1*n0) ]
  Q1 = AUC/(2-AUC), Q0 = 2*AUC^2/(1+AUC)
"""
from __future__ import annotations
import csv
import math
from collections import defaultdict
from pathlib import Path

TRAIN_CUTOFF = "2026-01-01"
ROOT = Path(__file__).resolve().parents[1]

CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLOSE_TO_CLOSE_PATH = ROOT / "data" / "processed" / "close_to_close_60d.csv"
CLUSTERING_PATH = ROOT / "data" / "processed" / "clustering.csv"
RELABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
# The catalogue's OWN cap_band column is the older 3-way Small/Mid/Large split -- the 5-way
# Micro/Small/Mid/Large/Mega quintile band phase8's own classification scripts use (and this
# script needs, to match Check 1's own banding) lives only in these two classification files,
# recomputed per-year by compute_quintile_bands() in scripts/phase8_classify_holdout.py /
# scripts/build_event_classifications.py -- NOT in event_catalogue_loose_zscore_only.csv.
TRAIN_CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"

# feature_name -> (value_fn(row) -> float|None, use_abs)
FEATURES = ["zscore_60d", "volume_ratio", "delivery_pct_percentile_60d",
            "return_20d_context_only", "close_to_close_60d", "same_date_event_count", "asm_gsm_labelled"]
USE_ABS = {"zscore_60d": True, "volume_ratio": True, "delivery_pct_percentile_60d": False,
           "return_20d_context_only": True, "close_to_close_60d": True,
           "same_date_event_count": False, "asm_gsm_labelled": False}


def rank_auc(scores: list[float], labels: list[bool]) -> tuple[float, int, int]:
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan"), n_pos, n_neg
    rank_sum_pos = 0.0
    i = 0
    rank = 1
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (rank + (rank + (j - i) - 1)) / 2.0
        for k in range(i, j):
            if pairs[k][1]:
                rank_sum_pos += avg_rank
        rank += (j - i)
        i = j
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return auc, n_pos, n_neg


def hanley_mcneil_ci(auc: float, n1: int, n0: int, z: float = 1.96) -> tuple[float, float]:
    if math.isnan(auc) or n1 == 0 or n0 == 0:
        return (float("nan"), float("nan"))
    q1 = auc / (2 - auc)
    q0 = 2 * auc * auc / (1 + auc)
    var = (auc * (1 - auc) + (n1 - 1) * (q1 - auc * auc) + (n0 - 1) * (q0 - auc * auc)) / (n1 * n0)
    se = math.sqrt(max(var, 0.0))
    return (max(0.0, auc - z * se), min(1.0, auc + z * se))


def load_label() -> tuple[dict, dict]:
    train, holdout = {}, {}
    with open(RELABEL_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row["collapsed_t0_primary"]
            if v == "":
                continue
            key = (row["symbol"], row["event_date"])
            if row["event_date"] < TRAIN_CUTOFF:
                train[key] = v == "True"
            else:
                holdout[key] = v == "True"
    return train, holdout


def load_features() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["symbol"], row["event_date"])
            asm = row["asm_stage"] not in ("", "None") if "asm_stage" in row else False
            gsm = row["gsm_stage"] not in ("", "None") if "gsm_stage" in row else False
            out[key] = {
                "zscore_60d": row["zscore_60d"],
                "volume_ratio": row["volume_ratio"],
                "delivery_pct_percentile_60d": row["delivery_pct_percentile_60d"],
                "return_20d_context_only": row["return_20d_context_only"],
                "asm_gsm_labelled": 1.0 if (asm or gsm) else 0.0,
            }
    with open(CLOSE_TO_CLOSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["symbol"], row["event_date"])
            if key in out:
                out[key]["close_to_close_60d"] = row["close_to_close_60d"]
    with open(CLUSTERING_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["symbol"], row["event_date"])
            if key in out:
                out[key]["same_date_event_count"] = row["same_date_event_count"]
    # 5-way cap_band from the classification files (see module note above), not the catalogue.
    for path in (TRAIN_CLASS_PATH, HOLDOUT_CLASS_PATH):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["symbol"], row["event_date"])
                if key in out:
                    out[key]["cap_band"] = row["cap_band"]
    return out


def get_value(feat_row: dict, feature: str) -> float | None:
    v = feat_row.get(feature)
    if v is None or v in ("", "None"):
        return None
    val = float(v)
    return abs(val) if USE_ABS[feature] else val


def auc_for_group(feature: str, outcomes: dict, features: dict, band: str | None) -> tuple[float, int, int]:
    scores, labels = [], []
    for key, actual in outcomes.items():
        fv = features.get(key)
        if fv is None:
            continue
        if band is not None and fv.get("cap_band") != band:
            continue
        v = get_value(fv, feature)
        if v is None:
            continue
        scores.append(v)
        labels.append(actual)
    return rank_auc(scores, labels)


def fmt(auc: float, n1: int, n0: int) -> str:
    if math.isnan(auc):
        return "n/a"
    lo, hi = hanley_mcneil_ci(auc, n1, n0)
    return f"{auc:.4f} [{lo:.4f},{hi:.4f}] (n={n1+n0})"


def main() -> None:
    train_outcomes, holdout_outcomes = load_label()
    features = load_features()
    print(f"TRAIN n={len(train_outcomes)}  HOLD-OUT n={len(holdout_outcomes)}")
    bands = ["Micro", "Small", "Mid", "Large", "Mega"]

    for feature in FEATURES:
        print(f"\n{'='*110}\n{feature}  (direction tested: {'HIGH abs-value' if USE_ABS[feature] else 'HIGH raw value'} -> collapse under relative_t0_primary)\n{'='*110}")
        auc, n1, n0 = auc_for_group(feature, train_outcomes, features, None)
        print(f"  TRAIN    pooled   AUC = {fmt(auc, n1, n0)}")
        auc, n1, n0 = auc_for_group(feature, holdout_outcomes, features, None)
        print(f"  HOLD-OUT pooled   AUC = {fmt(auc, n1, n0)}")
        print(f"  -- stratified by cap_band --")
        for band in bands:
            auc_t, n1t, n0t = auc_for_group(feature, train_outcomes, features, band)
            auc_h, n1h, n0h = auc_for_group(feature, holdout_outcomes, features, band)
            print(f"    {band:8s} TRAIN AUC = {fmt(auc_t, n1t, n0t):40s}  HOLD-OUT AUC = {fmt(auc_h, n1h, n0h)}")


if __name__ == "__main__":
    main()
