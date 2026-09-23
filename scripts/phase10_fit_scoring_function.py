"""Phase 10 pre-registration amendment, item 1: fit the actual scoring function the spec was
missing -- a logistic regression on 2019-2025 TRAIN data only, target relative_t0_primary
(PRIMARY threshold, R<0), inputs exactly as pre-registered in
docs/phase10_preregistration_amendments.md:

  delivery_low                    = 1 if delivery_pct_percentile_60d < 15.0 else 0   (pooled TRAIN median)
  isolated                        = 1 if same_date_event_count < 47 else 0            (pooled TRAIN median)
  disclosure_tier                 = SUBSTANTIVE / ROUTINE_ONLY / NONE / UNKNOWN_COVERAGE, one-hot,
                                     NONE as the reference level (the "no disclosure" baseline)
  volume_ratio_high_band_eligible = 1 if volume_ratio >= that event's own band median
                                     AND cap_band in {Small, Large, Mega} else 0
                                     (a single interaction term, not per-band dummies -- the
                                     simplest reading of "interacted with a Small/Large/Mega
                                     indicator so it carries no weight in Micro/Mid")

Unregularized logistic regression (sklearn LogisticRegression(penalty=None), equivalent to
classical MLE) -- no hyperparameter to silently tune. Fit ONCE, on TRAIN only, and the resulting
intercept/coefficients are written verbatim into the amendment document and never refit.
"""
from __future__ import annotations
import csv
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

TRAIN_CUTOFF = "2026-01-01"
# Amendment 4 refit: recomputed via scripts/phase10_compute_thresholds.py against the CORRECTED
# TRAIN population (equity-only filter + promoted corporate-actions sweep, P8-007/P8-010) --
# "same median rule," per instruction, means recomputing the median of the corrected TRAIN data,
# not reusing the literal old values computed from the pre-correction population. Old values
# (docs/phase10_preregistration.md, pre-correction TRAIN n=64,450): delivery 15.0000, isolated
# 47.0000, volume_ratio Micro/Small/Mid/Large/Mega = 4.7182/6.6737/7.2739/8.4210/7.5811.
DELIVERY_THRESHOLD = 13.3333
ISOLATED_THRESHOLD = 45.0
VOLUME_RATIO_BAND_MEDIAN = {
    "Micro": 5.0926, "Small": 6.8397, "Mid": 7.6364, "Large": 8.6042, "Mega": 7.4616,
}
BAND_ELIGIBLE = {"Small", "Large", "Mega"}
DISCLOSURE_LEVELS = ["SUBSTANTIVE", "ROUTINE_ONLY", "UNKNOWN_COVERAGE"]  # NONE is reference

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLUSTERING_PATH = ROOT / "data" / "processed" / "clustering.csv"
TRAIN_CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
RELABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"


def load_train_classifications() -> dict[tuple[str, str], dict]:
    out = {}
    with open(TRAIN_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            out[(row["symbol"], row["event_date"])] = row
    return out


def load_same_date_counts() -> dict[tuple[str, str], float]:
    out = {}
    with open(CLUSTERING_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["same_date_event_count"]
            if v not in ("", "None"):
                out[(row["symbol"], row["event_date"])] = float(v)
    return out


def load_label() -> dict[tuple[str, str], bool]:
    out = {}
    with open(RELABEL_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["collapsed_t0_primary"]
            if v != "":
                out[(row["symbol"], row["event_date"])] = v == "True"
    return out


def main() -> None:
    classifications = load_train_classifications()
    same_date_counts = load_same_date_counts()
    labels = load_label()
    print(f"TRAIN classifications: {len(classifications)}  same_date lookups: {len(same_date_counts)}  labels: {len(labels)}")

    rows = []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            key = (row["symbol"], row["event_date"])
            if key not in labels:
                continue
            cls_row = classifications.get(key)
            same_date = same_date_counts.get(key)
            delivery = row["delivery_pct_percentile_60d"]
            volume_ratio = row["volume_ratio"]
            if cls_row is None or same_date is None or delivery in ("", "None") or volume_ratio in ("", "None"):
                continue
            band = cls_row["cap_band"]
            tier = cls_row["disclosure_tier"]

            delivery_low = 1.0 if float(delivery) < DELIVERY_THRESHOLD else 0.0
            isolated = 1.0 if same_date < ISOLATED_THRESHOLD else 0.0
            vol_high_eligible = 1.0 if (float(volume_ratio) >= VOLUME_RATIO_BAND_MEDIAN[band] and band in BAND_ELIGIBLE) else 0.0
            disclosure_dummies = [1.0 if tier == level else 0.0 for level in DISCLOSURE_LEVELS]

            rows.append({
                "features": [delivery_low, isolated, vol_high_eligible] + disclosure_dummies,
                "label": 1.0 if labels[key] else 0.0,
            })

    print(f"Usable TRAIN rows (all features + label present): {len(rows)}")

    X = np.array([r["features"] for r in rows])
    y = np.array([r["label"] for r in rows])
    feature_names = ["delivery_low", "isolated", "volume_ratio_high_band_eligible"] + \
        [f"disclosure_{lvl}" for lvl in DISCLOSURE_LEVELS]

    print(f"\nFeature prevalence (TRAIN):")
    for name, col in zip(feature_names, X.T):
        print(f"  {name:36s} mean={col.mean():.4f}  n_positive={int(col.sum())}")
    print(f"  {'label (collapsed_t0_primary)':36s} mean={y.mean():.4f}  n_positive={int(y.sum())}")

    model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=1000)
    model.fit(X, y)

    print(f"\n{'='*90}\nFITTED LOGISTIC REGRESSION (TRAIN 2019-2025 ONLY, unregularized MLE)\n{'='*90}")
    print(f"intercept: {model.intercept_[0]:.6f}")
    for name, coef in zip(feature_names, model.coef_[0]):
        print(f"  {name:36s} {coef:+.6f}")

    train_pred = model.predict_proba(X)[:, 1]
    from sklearn.metrics import roc_auc_score, brier_score_loss
    print(f"\nIn-sample (TRAIN) AUC: {roc_auc_score(y, train_pred):.4f}")
    print(f"In-sample (TRAIN) Brier: {brier_score_loss(y, train_pred):.4f}")


if __name__ == "__main__":
    main()
