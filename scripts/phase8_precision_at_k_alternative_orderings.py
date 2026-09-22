"""Phase 8 follow-up: precision@20 under alternative CONTINUOUS orderings, requested to
distinguish "the class is uninformative" from "the ordering (categorical class x band score) was
wrong."

Correction to the request as given, stated directly rather than silently substituted: the two
specific AUC figures cited (z_score 0.495-0.522, volume_ratio 0.586-0.607 "the one feature that
survived stratification") do not match this project's own real, already-published Phase 6 numbers
(docs/phase6_signals.md). Checked directly against that doc:
  - volume_ratio: EVERY reported cut is below 0.50 (0.40-0.50 pooled and by-band, both labels) --
    the doc's own words: "volume_ratio and abs(zscore_60d) are both below 0.50." It did NOT survive
    stratification; it is the weaker of the two, and its own stratification check ("Stratified by
    market-cap band: is volume_ratio a real feature or a size proxy?") found it "does not cleanly
    hold or collapse... close to a coin flip" in Small/Mid once market drift is controlled for.
  - z_score: also consistently below 0.50 (0.44-0.49). Phase 6's OWN doc already flagged this exact
    "0.495-0.522" range once before, as not matching its real numbers ("not the near-exactly-random
    0.495-0.522 range described").
  - The feature that actually DID survive stratification, per Phase 6's own explicit language
    ("does not degrade by band, unlike volume_ratio") is `return_20d_context_only` /
    `close_to_close_60d` (0.53-0.58 by band, oriented; 0.611-0.70 in the ensemble).

This script still runs EXACTLY what was asked -- z_score and volume_ratio orderings, "do not drop
the z_score result" -- and additionally runs `return_20d_context_only` as the substitute for "the
ensemble score from Phase 6" (never persisted as a reusable artifact; refitting a full model was
out of scope for this specific ask). All three are reported side by side, ranked in whichever
direction TRAIN data actually supports (determined here, not assumed), so a below-random result
cannot be blamed on a naive "bigger number = more suspicious" assumption where TRAIN data itself
says the opposite direction is the real one.
"""
from __future__ import annotations
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PRIMARY_HORIZON = 90
TOP_K = 20

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
TRAIN_COLLAPSE_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
HOLDOUT_OUTCOMES_PATH = ROOT / "data" / "processed" / "phase8_2026_outcomes.csv"

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
    """Mann-Whitney U / rank-sum AUC -- P(a randomly chosen positive scores higher than a randomly
    chosen negative). Hand-rolled, matching Phase 6's own cross-checked method, not a new one."""
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

def load_train_feature_outcome(feature: str) -> tuple[list[float], list[bool]]:
    """TRAIN-period (event_date < 2026) abs(feature) vs. collapsed_90d, joined from the real
    catalogue (features) and collapse_rate_by_class.csv (outcomes, already computed)."""
    outcomes: dict[tuple[str, str], bool] = {}
    with open(TRAIN_COLLAPSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            v = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if v == "":
                continue
            outcomes[(row["symbol"], row["event_date"])] = v == "True"

    scores, labels = [], []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            key = (row["symbol"], row["event_date"])
            if key not in outcomes:
                continue
            v = row[feature]
            if v in ("", "None"):
                continue
            scores.append(abs(float(v)))
            labels.append(outcomes[key])
    return scores, labels

def load_holdout_scored() -> list[dict]:
    feature_vals: dict[tuple[str, str], dict] = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] < "2026-01-01":
                continue
            feature_vals[(row["symbol"], row["event_date"])] = row

    out = []
    with open(HOLDOUT_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            actual = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if actual == "":
                continue
            key = (row["symbol"], row["event_date"])
            fv = feature_vals.get(key)
            if fv is None:
                continue
            entry = {"symbol": row["symbol"], "event_date": row["event_date"], "actual": actual == "True"}
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
    holdout = load_holdout_scored()
    print(f"{len(holdout)} hold-out events with all three features and a known {PRIMARY_HORIZON}d outcome")

    print(f"\n{'='*90}\nSTEP 1: determine each feature's empirically correct ranking direction from TRAIN data\n{'='*90}")
    directions: dict[str, int] = {}
    for feature in FEATURES:
        scores, labels = load_train_feature_outcome(feature)
        auc = rank_auc(scores, labels)
        direction = 1 if auc >= 0.5 else -1
        directions[feature] = direction
        print(f"  {feature:28s} TRAIN AUC (high abs-value -> collapse): {auc:.4f}  "
              f"-> ranking {'HIGH' if direction == 1 else 'LOW'} abs-value as more collapse-prone "
              f"(n={len(scores)})")

    print(f"\n{'='*90}\nSTEP 2: precision@{TOP_K} on the 2026 hold-out, each feature's own empirically-correct direction\n{'='*90}")
    results = {}
    for feature in FEATURES:
        direction = directions[feature]
        ranked = sorted(holdout, key=lambda e: direction * e[feature], reverse=True)
        top = ranked[:TOP_K]
        hits = sum(1 for x in top if x["actual"])
        p, lo, hi = wilson_ci(hits, len(top))
        results[feature] = (hits, len(top), p, lo, hi)
        print(f"  {feature:28s} {hits}/{len(top)} = {100*p:.1f}%  95% CI [{100*lo:.1f}%, {100*hi:.1f}%]  "
              f"(ranked by {'HIGH' if direction==1 else 'LOW'} |value|)")

    base_rate = sum(1 for e in holdout if e["actual"]) / len(holdout)
    print(f"\nBase rate for comparison (this {len(holdout)}-event subset): {100*base_rate:.1f}%")

    print(f"\n{'='*90}\nSTEP 3: naive direction check -- what if we (wrongly) always rank by HIGH |value|,")
    print(f"ignoring what TRAIN data says about direction? (this is the failure mode the review warned about)")
    print(f"{'='*90}")
    for feature in FEATURES:
        ranked = sorted(holdout, key=lambda e: e[feature], reverse=True)  # always descending, no direction correction
        top = ranked[:TOP_K]
        hits = sum(1 for x in top if x["actual"])
        p, lo, hi = wilson_ci(hits, len(top))
        flag = "  <-- WRONG DIRECTION for this feature" if directions[feature] == -1 else ""
        print(f"  {feature:28s} {hits}/{len(top)} = {100*p:.1f}%  95% CI [{100*lo:.1f}%, {100*hi:.1f}%]{flag}")

if __name__ == "__main__":
    main()
