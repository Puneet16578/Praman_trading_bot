"""Phase 6 pre-flight, part 5: does combining what we already have get anywhere close to a usable
ceiling? Logistic regression on volume_ratio + delivery_pct_percentile_60d + market-cap quintile
band, with a delivery x band interaction (since docs/phase6_signals.md's 5-way stratification
found delivery's sign itself flips with band -- a plain additive term cannot represent that).
Target: collapsed_relative (the benchmark-relative outcome label -- the one that survived the
market-drift check). Time-based split: train on events through 2024, test on 2025-2026, reported
separately from an in-sample (pooled, no holdout) fit for comparison.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]

def load_rows():
    turnover = {}
    with open(ROOT / "data/processed/event_catalogue_loose_zscore_only.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            turnover[(row["symbol"], row["event_date"])] = float(row["close_price_raw"]) * float(row["traded_qty"])

    rows = []
    with open(ROOT / "data/processed/outcome_labels_relative.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["collapsed_relative"] == "" or row["delivery_pct_percentile_60d"] == "":
                continue
            key = (row["symbol"], row["event_date"])
            t = turnover.get(key)
            if t is None:
                continue
            row["turnover"] = t
            rows.append(row)

    r20 = {}
    with open(ROOT / "data/processed/event_catalogue_loose_zscore_only.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r20[(row["symbol"], row["event_date"])] = row["return_20d_context_only"]
    for row in rows:
        v = r20.get((row["symbol"], row["event_date"]), "")
        row["return_20d"] = v if v not in ("", "None") else None

    ctc = {}
    with open(ROOT / "data/processed/close_to_close_60d.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["close_to_close_60d"] not in ("", "None"):
                ctc[(row["symbol"], row["event_date"])] = float(row["close_to_close_60d"])
    for row in rows:
        row["ctc60"] = ctc.get((row["symbol"], row["event_date"]))

    clust = {}
    with open(ROOT / "data/processed/clustering.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            clust[(row["symbol"], row["event_date"])] = row
    for row in rows:
        c = clust.get((row["symbol"], row["event_date"]))
        if c is None or c["max_comover_correlation"] in ("", "None"):
            row["clust"] = None
        else:
            row["clust"] = (float(c["same_date_event_count"]), float(c["same_date_same_band_count"]),
                             float(c["max_comover_correlation"]), float(c["mean_comover_correlation"]))

    return [r for r in rows if r["return_20d"] is not None and r["ctc60"] is not None and r["clust"] is not None]

def assign_quintile_bands(rows):
    by_year = defaultdict(list)
    for r in rows:
        by_year[r["event_date"][:4]].append(r)
    for year, yrows in by_year.items():
        vals = sorted(r["turnover"] for r in yrows)
        n = len(vals)
        cuts = [vals[int(n * p)] for p in (0.2, 0.4, 0.6, 0.8)]
        for r in yrows:
            t = r["turnover"]
            if t <= cuts[0]: r["qband"] = "Micro"
            elif t <= cuts[1]: r["qband"] = "Small"
            elif t <= cuts[2]: r["qband"] = "Mid"
            elif t <= cuts[3]: r["qband"] = "Large"
            else: r["qband"] = "Mega"
    return rows

BAND_ORDER = ["Micro", "Small", "Mid", "Large", "Mega"]

def build_design_matrix(rows):
    """volume_ratio, delivery percentile, 4 band dummies (Micro is reference), 4 delivery x band
    interaction terms -- 9 features total, plus intercept (handled by LogisticRegression)."""
    X = []
    for r in rows:
        vol = float(r["volume_ratio"])
        deliv = float(r["delivery_pct_percentile_60d"])
        band = r["qband"]
        dummies = [1.0 if band == b else 0.0 for b in BAND_ORDER[1:]]  # Small,Mid,Large,Mega
        interactions = [d * deliv for d in dummies]
        X.append([vol, deliv] + dummies + interactions)
    return np.array(X)

def build_design_matrix_with_r20(rows):
    """As-specified design plus abs(return_20d_context_only) -- the strongest single predictor
    found in the pre-flight investigation, excluded from the as-specified 3-feature spec."""
    base = build_design_matrix(rows)
    r20 = np.array([[abs(float(r["return_20d"]))] for r in rows])
    return np.hstack([base, r20])

def build_design_matrix_full(rows):
    """As-specified design plus abs(return_20d_context_only) AND abs(close_to_close_60d) -- the
    free NSE-criteria feature, added because it showed strong, band-stable discrimination on its
    own (0.35-0.42 AUC in every quintile band, docs/phase6_signals.md)."""
    with_r20 = build_design_matrix_with_r20(rows)
    ctc = np.array([[abs(float(r["ctc60"]))] for r in rows])
    return np.hstack([with_r20, ctc])

def build_design_matrix_everything(rows):
    """Full design plus the 4 clustering features."""
    base = build_design_matrix_full(rows)
    clust = np.array([list(r["clust"]) for r in rows])
    return np.hstack([base, clust])

def main() -> None:
    rows = load_rows()
    rows = assign_quintile_bands(rows)
    print(f"Total usable rows: {len(rows)}")

    y = np.array([1 if r["collapsed_relative"] == "True" else 0 for r in rows])
    X = build_design_matrix(rows)
    years = np.array([int(r["event_date"][:4]) for r in rows])

    feature_names = ["volume_ratio", "delivery_pctile", "band_Small", "band_Mid", "band_Large", "band_Mega",
                      "deliv_x_Small", "deliv_x_Mid", "deliv_x_Large", "deliv_x_Mega"]
    print(f"Design matrix: {X.shape}, features: {feature_names}")

    # --- In-sample (pooled, no holdout) fit, for a ceiling reference ---
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model_pooled = LogisticRegression(max_iter=1000)
    model_pooled.fit(Xs, y)
    p_pooled = model_pooled.predict_proba(Xs)[:, 1]
    auc_pooled = roc_auc_score(y, p_pooled)
    print(f"\nIn-sample (pooled, fit and evaluated on all data): AUC = {auc_pooled:.4f}")
    for name, coef in zip(feature_names, model_pooled.coef_[0]):
        print(f"    {name}: {coef:+.4f}")

    # --- Time-based split: train through 2024, test 2025-2026 ---
    train_mask = years <= 2024
    test_mask = years >= 2025
    print(f"\nTrain (<=2024): n={train_mask.sum()}   Test (2025-2026): n={test_mask.sum()}")

    scaler2 = StandardScaler()
    X_train = scaler2.fit_transform(X[train_mask])
    X_test = scaler2.transform(X[test_mask])
    y_train, y_test = y[train_mask], y[test_mask]

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    p_train = model.predict_proba(X_train)[:, 1]
    p_test = model.predict_proba(X_test)[:, 1]
    auc_train = roc_auc_score(y_train, p_train)
    auc_test = roc_auc_score(y_test, p_test)
    print(f"Train AUC: {auc_train:.4f}")
    print(f"Test AUC (held out, 2025-2026): {auc_test:.4f}")
    print("Coefficients (time-split model):")
    for name, coef in zip(feature_names, model.coef_[0]):
        print(f"    {name}: {coef:+.4f}")

    # per-band test AUC
    print("\nTest-set AUC by band:")
    test_rows = [r for r, m in zip(rows, test_mask) if m]
    for b in BAND_ORDER:
        idx = [i for i, r in enumerate(test_rows) if r["qband"] == b]
        if len(idx) < 20:
            print(f"  {b}: n={len(idx)} (too few for a stable AUC)")
            continue
        yb = y_test[idx]
        pb = p_test[idx]
        if len(set(yb)) < 2:
            print(f"  {b}: n={len(idx)} (single class in test set)")
            continue
        print(f"  {b}: n={len(idx)}  AUC={roc_auc_score(yb, pb):.4f}")

    # single-feature baselines on the SAME test set, for direct comparison
    print("\nSingle-feature baselines, same held-out test set:")
    print(f"  volume_ratio alone:  AUC={roc_auc_score(y_test, X[test_mask][:,0]):.4f}")
    print(f"  delivery_pctile alone (raw, non-negated): AUC={roc_auc_score(y_test, X[test_mask][:,1]):.4f}")

    # --- Supplementary: same ensemble + abs(return_20d_context_only), the strongest single
    # predictor found, excluded from the as-specified 3-feature spec -- reported separately as
    # the true achievable ceiling with everything already in the catalogue, not a substitute for
    # the as-specified result above.
    print("\n" + "=" * 70)
    print("SUPPLEMENTARY: as-specified ensemble + abs(return_20d_context_only)")
    print("=" * 70)
    X2 = build_design_matrix_with_r20(rows)
    feature_names2 = feature_names + ["abs_return_20d"]

    scaler3 = StandardScaler()
    X2s = scaler3.fit_transform(X2)
    model2_pooled = LogisticRegression(max_iter=1000)
    model2_pooled.fit(X2s, y)
    auc2_pooled = roc_auc_score(y, model2_pooled.predict_proba(X2s)[:, 1])
    print(f"In-sample pooled AUC: {auc2_pooled:.4f}")

    X2_train = scaler3.fit_transform(X2[train_mask])
    X2_test = scaler3.transform(X2[test_mask])
    model2 = LogisticRegression(max_iter=1000)
    model2.fit(X2_train, y_train)
    auc2_train = roc_auc_score(y_train, model2.predict_proba(X2_train)[:, 1])
    auc2_test = roc_auc_score(y_test, model2.predict_proba(X2_test)[:, 1])
    print(f"Train AUC: {auc2_train:.4f}")
    print(f"Test AUC (held out, 2025-2026): {auc2_test:.4f}")
    for name, coef in zip(feature_names2, model2.coef_[0]):
        print(f"    {name}: {coef:+.4f}")

    # --- Full ensemble: as-specified + return_20d + close_to_close_60d ---
    print("\n" + "=" * 70)
    print("FULL ENSEMBLE: as-specified + abs(return_20d) + abs(close_to_close_60d)")
    print("=" * 70)
    X3 = build_design_matrix_full(rows)
    feature_names3 = feature_names2 + ["abs_close_to_close_60d"]

    scaler4 = StandardScaler()
    X3s = scaler4.fit_transform(X3)
    model3_pooled = LogisticRegression(max_iter=1000)
    model3_pooled.fit(X3s, y)
    auc3_pooled = roc_auc_score(y, model3_pooled.predict_proba(X3s)[:, 1])
    print(f"In-sample pooled AUC: {auc3_pooled:.4f}")

    X3_train = scaler4.fit_transform(X3[train_mask])
    X3_test = scaler4.transform(X3[test_mask])
    model3 = LogisticRegression(max_iter=1000)
    model3.fit(X3_train, y_train)
    auc3_train = roc_auc_score(y_train, model3.predict_proba(X3_train)[:, 1])
    auc3_test = roc_auc_score(y_test, model3.predict_proba(X3_test)[:, 1])
    print(f"Train AUC: {auc3_train:.4f}")
    print(f"Test AUC (held out, 2025-2026): {auc3_test:.4f}")
    for name, coef in zip(feature_names3, model3.coef_[0]):
        print(f"    {name}: {coef:+.4f}")

    p3_test = model3.predict_proba(X3_test)[:, 1]
    print("\nFull-ensemble test-set AUC by band:")
    for b in BAND_ORDER:
        idx = [i for i, r in enumerate(test_rows) if r["qband"] == b]
        if len(idx) < 20 or len(set(y_test[idx])) < 2:
            continue
        print(f"  {b}: n={len(idx)}  AUC={roc_auc_score(y_test[idx], p3_test[idx]):.4f}")

    # --- Everything, including clustering ---
    print("\n" + "=" * 70)
    print("EVERYTHING: full ensemble + 4 clustering features")
    print("=" * 70)
    X4 = build_design_matrix_everything(rows)
    feature_names4 = feature_names3 + ["same_date_count", "same_band_count", "max_comover_corr", "mean_comover_corr"]

    scaler5 = StandardScaler()
    X4_train = scaler5.fit_transform(X4[train_mask])
    X4_test = scaler5.transform(X4[test_mask])
    model4 = LogisticRegression(max_iter=1000)
    model4.fit(X4_train, y_train)
    auc4_train = roc_auc_score(y_train, model4.predict_proba(X4_train)[:, 1])
    auc4_test = roc_auc_score(y_test, model4.predict_proba(X4_test)[:, 1])
    print(f"Train AUC: {auc4_train:.4f}")
    print(f"Test AUC (held out, 2025-2026): {auc4_test:.4f}")
    for name, coef in zip(feature_names4, model4.coef_[0]):
        print(f"    {name}: {coef:+.4f}")

if __name__ == "__main__":
    main()
