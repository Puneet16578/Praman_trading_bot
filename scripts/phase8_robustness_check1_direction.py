"""Phase 8 robustness check 1: re-run the naive-vs-correct direction comparison
(scripts/phase8_precision_at_k_alternative_orderings.py) under the NEW pre-registered label
(collapsed_t0_primary, data/processed/phase8_relabel_t0_relative.csv) instead of the raw
collapsed_90d it originally used -- same method (rank-sum AUC direction on TRAIN, precision@20 on
the 2026 hold-out, both directions reported), only the outcome label differs.
"""
from __future__ import annotations
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PRIMARY_LABEL_FIELD = "collapsed_t0_primary"
TOP_K = 20
TRAIN_CUTOFF = "2026-01-01"

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
RELABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"

FEATURES = ["zscore_60d", "volume_ratio", "return_20d_context_only"]


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


def rank_auc(scores: list[float], labels: list[bool]) -> float:
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
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
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def load_new_label() -> tuple[dict, dict]:
    train, holdout = {}, {}
    with open(RELABEL_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row[PRIMARY_LABEL_FIELD]
            if v == "":
                continue
            key = (row["symbol"], row["event_date"])
            if row["event_date"] < TRAIN_CUTOFF:
                train[key] = v == "True"
            else:
                holdout[key] = v == "True"
    return train, holdout


def load_train_feature_outcome(feature: str, train_outcomes: dict) -> tuple[list[float], list[bool]]:
    scores, labels = [], []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            key = (row["symbol"], row["event_date"])
            if key not in train_outcomes:
                continue
            v = row[feature]
            if v in ("", "None"):
                continue
            scores.append(abs(float(v)))
            labels.append(train_outcomes[key])
    return scores, labels


def load_holdout_scored(holdout_outcomes: dict) -> list[dict]:
    feature_vals: dict[tuple[str, str], dict] = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] < TRAIN_CUTOFF:
                continue
            feature_vals[(row["symbol"], row["event_date"])] = row

    out = []
    for key, actual in holdout_outcomes.items():
        fv = feature_vals.get(key)
        if fv is None:
            continue
        entry = {"symbol": key[0], "event_date": key[1], "actual": actual}
        ok = True
        for feature in FEATURES:
            v = fv[feature]
            if v in ("", "None"):
                ok = False
                break
            entry[feature] = abs(float(v))
        if ok:
            out.append(entry)
    return out


def main() -> None:
    train_outcomes, holdout_outcomes = load_new_label()
    print(f"NEW label (collapsed_t0_primary): TRAIN n={len(train_outcomes)}  HOLD-OUT n={len(holdout_outcomes)}")

    holdout = load_holdout_scored(holdout_outcomes)
    print(f"{len(holdout)} hold-out events with all three features and a known new-label outcome")

    print(f"\n{'='*90}\nSTEP 1 (re-run under NEW label): empirically correct ranking direction from TRAIN data\n{'='*90}")
    directions: dict[str, int] = {}
    for feature in FEATURES:
        scores, labels = load_train_feature_outcome(feature, train_outcomes)
        auc = rank_auc(scores, labels)
        direction = 1 if auc >= 0.5 else -1
        directions[feature] = direction
        print(f"  {feature:28s} TRAIN AUC (high abs-value -> collapse, NEW label): {auc:.4f}  "
              f"-> ranking {'HIGH' if direction == 1 else 'LOW'} abs-value as more collapse-prone "
              f"(n={len(scores)})")

    print(f"\n{'='*90}\nSTEP 2 (re-run under NEW label): precision@{TOP_K} on the 2026 hold-out, correct direction\n{'='*90}")
    for feature in FEATURES:
        direction = directions[feature]
        ranked = sorted(holdout, key=lambda e: direction * e[feature], reverse=True)
        top = ranked[:TOP_K]
        hits = sum(1 for x in top if x["actual"])
        p, lo, hi = wilson_ci(hits, len(top))
        print(f"  {feature:28s} {hits}/{len(top)} = {100*p:.1f}%  95% CI [{100*lo:.1f}%, {100*hi:.1f}%]  "
              f"(ranked by {'HIGH' if direction==1 else 'LOW'} |value|)")

    base_rate = sum(1 for e in holdout if e["actual"]) / len(holdout)
    print(f"\nBase rate under NEW label (this {len(holdout)}-event subset): {100*base_rate:.1f}%")

    print(f"\n{'='*90}\nSTEP 3 (re-run under NEW label): naive direction (always high |value|)\n{'='*90}")
    for feature in FEATURES:
        ranked = sorted(holdout, key=lambda e: e[feature], reverse=True)
        top = ranked[:TOP_K]
        hits = sum(1 for x in top if x["actual"])
        p, lo, hi = wilson_ci(hits, len(top))
        flag = "  <-- WRONG DIRECTION for this feature" if directions[feature] == -1 else ""
        print(f"  {feature:28s} {hits}/{len(top)} = {100*p:.1f}%  95% CI [{100*lo:.1f}%, {100*hi:.1f}%]{flag}")


if __name__ == "__main__":
    main()
