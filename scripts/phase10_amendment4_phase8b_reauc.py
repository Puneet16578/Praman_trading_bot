"""Amendment 4 prep round 2, item 4: re-run Phase 8b's clean-label feature AUC analysis
(scripts/phase8b_feature_reauc.py) against the corrected catalogue -- equity-only universe,
promoted corporate actions, symbol-group/series-extended labels. NOT an edit to the original
script: that script's own committed output (docs/phase10_p8007_corrections.md's contamination
sensitivity check, RESULTS.md's citations) is a historical record against the PRE-correction data
and must not silently change meaning underneath those citations. This is a separate, explicitly
Amendment-4-labeled re-run for comparison.

One real fix needed to do this correctly, not just a re-point of file paths: the original script
merges TWO classification files (`event_classifications.csv` for TRAIN, `phase8_2026_
classifications.csv` for HOLD-OUT), with the second READ LAST, so its cap_band values overwrite
whatever was loaded first for the same (symbol, event_date) key. `event_classifications.csv` now
already covers the FULL catalogue (TRAIN and HOLD-OUT together, per this session's rebuild) --
naively reusing the original script as-is would have the STALE, pre-correction
`phase8_2026_classifications.csv` (never rebuilt this session, and not rebuilt here either: it
underpins several already-spent, historically-frozen Phase 8 analyses that must not be
disturbed) silently overwrite the freshly-rebuilt HOLD-OUT cap_band values. Fixed here by reading
ONLY `event_classifications.csv`.

Caveat, stated plainly: `close_to_close_60d.csv` (one of the seven features tested) is NOT
rebuilt this session (a Phase 6 artifact, out of this round's explicit scope) -- its numbers below
mix stale close-to-close values with the freshly-corrected population and label. Every other
feature (zscore_60d, volume_ratio, delivery_pct_percentile_60d, return_20d_context_only,
same_date_event_count, asm_gsm_labelled) is fully corrected.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAIN_CUTOFF = "2026-01-01"

CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLOSE_TO_CLOSE_PATH = ROOT / "data" / "processed" / "close_to_close_60d.csv"  # NOT rebuilt -- see caveat above
CLUSTERING_PATH = ROOT / "data" / "processed" / "clustering.csv"
RELABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"  # now covers TRAIN+HOLD-OUT

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
    with open(CLASS_PATH, encoding="utf-8") as f:
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
