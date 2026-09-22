"""Phase 8 robustness check 1: re-derive TRAIN-only (2019-2025) score tables and re-score
baseline 3 (disclosure tier alone) vs. baseline 4 (deterministic classifier) under FOUR labels,
so a Brier/precision comparison is never scoring one label's TRAIN-derived table against a
different label's hold-out outcomes (addition 1 of the robustness review):

  raw_t20          collapsed_90d              (existing Phase 8 label -- anchor t-20, path-crossing)
  relative_t20     collapsed_relative         (existing Phase 6 label -- anchor t-20, path-crossing,
                                                market-relative)
  relative_t0_pri  collapsed_t0_primary       (NEW, pre-registered -- anchor t0, endpoint return < 0,
                                                market-relative)
  relative_t0_sec  collapsed_t0_secondary     (NEW, pre-registered -- anchor t0, endpoint return <
                                                -10%, market-relative)

Classifications and thresholds are NOT re-derived or re-fit here -- only the outcome label used to
build the TRAIN rate table and to score the hold-out changes. This isolates the label's own effect
from any change to the classifier itself (addition 1's explicit requirement).

Also reports each label's own TRAIN and 2026 hold-out unconditional rate, feeding the
raw(t-20) -> relative(t-20) -> relative(t0) decomposition (addition 3): the first step holds the
anchor fixed and changes only market-relativity (isolates MARKET DRIFT); the second holds
market-relativity fixed and changes only the anchor (isolates MECHANICAL COUPLING).
"""
from __future__ import annotations
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TRAIN_CUTOFF = "2026-01-01"
ROOT = Path(__file__).resolve().parents[1]

EVENT_CLASSIFICATIONS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
RAW_TRAIN_OUTCOMES_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
RAW_HOLDOUT_OUTCOMES_PATH = ROOT / "data" / "processed" / "phase8_2026_outcomes.csv"
RELATIVE_T20_PATH = ROOT / "data" / "processed" / "outcome_labels_relative.csv"
RELATIVE_T0_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


def load_classifications(path: Path, before: bool) -> dict[tuple[str, str], dict]:
    out = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            is_before = row["event_date"] < TRAIN_CUTOFF
            if is_before != before:
                continue
            out[(row["symbol"], row["event_date"])] = row
    return out


# ---- Label loaders: each returns {(symbol,event_date): bool}, split TRAIN vs HOLDOUT ----

def load_raw_label() -> tuple[dict, dict]:
    train, holdout = {}, {}
    with open(RAW_TRAIN_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["collapsed_90d"]
            if v == "":
                continue
            train[(row["symbol"], row["event_date"])] = v == "True"
    with open(RAW_HOLDOUT_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row["collapsed_90d"]
            if v == "":
                continue
            holdout[(row["symbol"], row["event_date"])] = v == "True"
    return train, holdout


def load_full_catalogue_label(path: Path, field: str) -> tuple[dict, dict]:
    train, holdout = {}, {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row[field]
            if v == "":
                continue
            key = (row["symbol"], row["event_date"])
            if row["event_date"] < TRAIN_CUTOFF:
                train[key] = v == "True"
            else:
                holdout[key] = v == "True"
    return train, holdout


def build_rate_table(key_field: str, train_class: dict, train_outcomes: dict) -> dict[tuple[str, str], float]:
    cells: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for key, cls_row in train_class.items():
        if key not in train_outcomes:
            continue
        cells[(cls_row[key_field], cls_row["cap_band"])].append(train_outcomes[key])
    return {cell: sum(v) / len(v) for cell, v in cells.items() if v}


def brier(scored: list[tuple[float, bool]]) -> float:
    return sum((s - (1.0 if a else 0.0)) ** 2 for s, a in scored) / len(scored)


def precision_at_max_tier(scored: list[tuple[float, bool]]) -> tuple[int, int, float, float]:
    max_score = max(s for s, _ in scored)
    tied = [a for s, a in scored if s == max_score]
    hits = sum(1 for a in tied if a)
    return hits, len(tied), max_score, hits / len(tied) if tied else float("nan")


def score_baseline(key_field: str, train_class: dict, train_outcomes: dict,
                    holdout_class: dict, holdout_outcomes: dict) -> dict:
    table = build_rate_table(key_field, train_class, train_outcomes)
    scored = []
    for key, cls_row in holdout_class.items():
        if key not in holdout_outcomes:
            continue
        cell = (cls_row[key_field], cls_row["cap_band"])
        score = table.get(cell)
        if score is None:
            continue
        scored.append((score, holdout_outcomes[key]))
    if not scored:
        return {"n": 0}
    b = brier(scored)
    hits, n_tied, max_score, rate = precision_at_max_tier(scored)
    p, lo, hi = wilson_ci(hits, n_tied)
    max_cells = [cell for cell, s in table.items() if s == max_score]
    return {"n": len(scored), "n_cells": len(table), "brier": b, "hits": hits, "n_tied": n_tied,
            "max_score": max_score, "precision": rate, "ci_lo": lo, "ci_hi": hi, "max_cells": max_cells}


def main() -> None:
    train_class = load_classifications(EVENT_CLASSIFICATIONS_PATH, before=True)
    holdout_class = load_classifications(HOLDOUT_CLASS_PATH, before=False)
    print(f"TRAIN classifications: {len(train_class)}   HOLD-OUT classifications: {len(holdout_class)}")

    labels = {
        "raw_t20 (existing, collapsed_90d)": load_raw_label(),
        "relative_t20 (existing, collapsed_relative)": load_full_catalogue_label(RELATIVE_T20_PATH, "collapsed_relative"),
        "relative_t0_primary (NEW, R<0)": load_full_catalogue_label(RELATIVE_T0_PATH, "collapsed_t0_primary"),
        "relative_t0_secondary (NEW, R<-10%)": load_full_catalogue_label(RELATIVE_T0_PATH, "collapsed_t0_secondary"),
    }

    print(f"\n{'='*100}\nUnconditional rates under each label (context for the drift/coupling decomposition)\n{'='*100}")
    for name, (train_outcomes, holdout_outcomes) in labels.items():
        train_rate = sum(train_outcomes.values()) / len(train_outcomes) if train_outcomes else float("nan")
        holdout_rate = sum(holdout_outcomes.values()) / len(holdout_outcomes) if holdout_outcomes else float("nan")
        print(f"  {name:42s} TRAIN (n={len(train_outcomes):6d}) rate={100*train_rate:5.1f}%   "
              f"HOLD-OUT (n={len(holdout_outcomes):6d}) rate={100*holdout_rate:5.1f}%")

    print(f"\n{'='*100}\nBaseline 3 (disclosure_tier) vs Baseline 4 (classification) under each label\n{'='*100}")
    for name, (train_outcomes, holdout_outcomes) in labels.items():
        print(f"\n-- {name} --")
        for key_field, label_name in (("disclosure_tier", "Baseline 3"), ("classification", "Baseline 4")):
            r = score_baseline(key_field, train_class, train_outcomes, holdout_class, holdout_outcomes)
            if r["n"] == 0:
                print(f"  {label_name}: no scoreable events")
                continue
            print(f"  {label_name:12s} n={r['n']:5d}  cells={r['n_cells']:3d}  Brier={r['brier']:.4f}  "
                  f"max-tier: {r['hits']}/{r['n_tied']} = {100*r['precision']:.1f}% "
                  f"95% CI [{100*r['ci_lo']:.1f}%, {100*r['ci_hi']:.1f}%]  "
                  f"max_score={r['max_score']:.4f}  max_cells={r['max_cells']}")


if __name__ == "__main__":
    main()
