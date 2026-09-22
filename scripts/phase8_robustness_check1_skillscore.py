"""Phase 8 robustness follow-up, framing fix 1 + item 5: raw Brier/precision are not comparable
across labels with different base rates (a lower-base-rate label mechanically produces a lower
Brier for EVERY strategy, informative or not). Two corrected quantities, computed per label:

  LIFT  = a baseline's own max-tier precision minus THAT LABEL's own hold-out base rate
          (comparable across labels; a strategy with no information at all has LIFT = 0)
  BSS   = Brier Skill Score = 1 - Brier(baseline) / Brier(FAIR), where FAIR is the constant
          TRAIN-rate baseline scored on the SAME label's hold-out set (comparable across labels;
          FAIR itself always has BSS = 0 by construction)

Also adds a CAP-BAND-ONLY baseline (score = TRAIN rate for the event's cap_band alone, no
disclosure_tier or classification) under every label, since baseline 3 and 4's score tables both
already condition on cap_band -- if cap-band-only matches or nearly matches B3/B4, whatever skill
they have is coming from band composition, not from the disclosure/classification axis.
"""
from __future__ import annotations
import csv
import math
from collections import defaultdict
from pathlib import Path

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


def build_rate_table(key_fn, train_class: dict, train_outcomes: dict) -> dict:
    cells: dict = defaultdict(list)
    for key, cls_row in train_class.items():
        if key not in train_outcomes:
            continue
        cells[key_fn(cls_row)].append(train_outcomes[key])
    return {cell: sum(v) / len(v) for cell, v in cells.items() if v}


def score_with_table(key_fn, table: dict, holdout_class: dict, holdout_outcomes: dict) -> list[tuple[float, bool]]:
    scored = []
    for key, cls_row in holdout_class.items():
        if key not in holdout_outcomes:
            continue
        score = table.get(key_fn(cls_row))
        if score is None:
            continue
        scored.append((score, holdout_outcomes[key]))
    return scored


def brier(scored: list[tuple[float, bool]]) -> float:
    return sum((s - (1.0 if a else 0.0)) ** 2 for s, a in scored) / len(scored)


def precision_at_max_tier(scored: list[tuple[float, bool]]) -> tuple[int, int, float]:
    max_score = max(s for s, _ in scored)
    tied = [a for s, a in scored if s == max_score]
    hits = sum(1 for a in tied if a)
    return hits, len(tied), hits / len(tied) if tied else float("nan")


def main() -> None:
    train_class = load_classifications(EVENT_CLASSIFICATIONS_PATH, before=True)
    holdout_class = load_classifications(HOLDOUT_CLASS_PATH, before=False)

    labels = {
        "raw_t20": load_raw_label(),
        "relative_t20": load_full_catalogue_label(RELATIVE_T20_PATH, "collapsed_relative"),
        "relative_t0_primary": load_full_catalogue_label(RELATIVE_T0_PATH, "collapsed_t0_primary"),
        "relative_t0_secondary": load_full_catalogue_label(RELATIVE_T0_PATH, "collapsed_t0_secondary"),
    }

    key_fns = {
        "B3_disclosure_tier": lambda r: (r["disclosure_tier"], r["cap_band"]),
        "B4_classification": lambda r: (r["classification"], r["cap_band"]),
        "CAPBAND_ONLY": lambda r: r["cap_band"],
    }

    print(f"{'='*120}\nLIFT (max-tier precision minus that label's OWN hold-out base rate) and "
          f"BSS (Brier Skill Score vs. that label's own FAIR/TRAIN-rate constant)\n{'='*120}")
    header = f"{'Label':24s} {'HO base rate':>12s} {'Baseline':16s} {'n':>6s} {'Brier':>8s} {'BSS':>8s} {'MaxTier precision':>20s} {'LIFT':>8s}"
    print(header)

    for label_name, (train_outcomes, holdout_outcomes) in labels.items():
        holdout_rate = sum(holdout_outcomes.values()) / len(holdout_outcomes)
        train_rate = sum(train_outcomes.values()) / len(train_outcomes)

        # FAIR constant baseline: predict the TRAIN rate for every hold-out event under THIS label
        fair_scored = [(train_rate, holdout_outcomes[k]) for k in holdout_outcomes]
        fair_brier = brier(fair_scored)
        print(f"{label_name:24s} {100*holdout_rate:11.1f}% {'FAIR (TRAIN rate)':16s} {len(fair_scored):6d} "
              f"{fair_brier:8.4f} {'0.0%':>8s} {'n/a (constant)':>20s} {'n/a':>8s}")

        for base_name, key_fn in key_fns.items():
            table = build_rate_table(key_fn, train_class, train_outcomes)
            scored = score_with_table(key_fn, table, holdout_class, holdout_outcomes)
            if not scored:
                continue
            b = brier(scored)
            bss = 1.0 - b / fair_brier
            hits, n_tied, prec = precision_at_max_tier(scored)
            lift = 100 * prec - 100 * holdout_rate
            p, lo, hi = wilson_ci(hits, n_tied)
            print(f"{'':24s} {'':12s} {base_name:16s} {len(scored):6d} {b:8.4f} {100*bss:7.1f}% "
                  f"{f'{hits}/{n_tied}={100*prec:.1f}% [{100*lo:.1f},{100*hi:.1f}]':>20s} {lift:+7.1f}pp")
        print()


if __name__ == "__main__":
    main()
