"""Phase 10 pre-registration amendment, item 2: MECHANISM CHECK ONLY, not a result.

Verifies the top-decile LIFT procedure (with seeded tie-break) specified in
docs/phase10_preregistration_amendments.md is well-defined and runs correctly, on the 2026
hold-out -- data already spent for model selection (praman/CLAUDE.md), so nothing computed here
is a finding about the redesign's performance. It exists only to confirm the METHOD works
(handles a coarse, heavily-tied score correctly) before the amendment commits to it for a forward
evaluation that does not exist yet.

Procedure: sort descending by score; k = round(n * 0.10); every event strictly above the boundary
score is "clearly in"; remaining slots are filled from the tied-at-boundary group via
random.Random(SEED).sample(), SEED fixed and stated in the amendment (42, this project's
established default -- Layer 1's own 2,000-event sample used the same seed).
"""
from __future__ import annotations
import csv
import random
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
RELABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
TRAIN_COLLAPSE_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
TRAIN_CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
TRAIN_CUTOFF = "2026-01-01"


def top_decile_lift(scored: list[tuple[float, bool]], seed: int = SEED) -> dict:
    """scored: list of (score, actual). Returns hits/n/precision/lift/boundary-tie info."""
    n_total = len(scored)
    k = round(n_total * 0.10)
    ordered = sorted(scored, key=lambda x: -x[0])
    boundary_score = ordered[k - 1][0]
    clearly_in = [x for x in ordered if x[0] > boundary_score]
    tied_at_boundary = [x for x in scored if x[0] == boundary_score]
    need = k - len(clearly_in)
    rng = random.Random(seed)
    chosen_tied = rng.sample(tied_at_boundary, need) if need > 0 else []
    top_k = clearly_in + chosen_tied
    hits = sum(1 for _, a in top_k if a)
    base_rate = sum(1 for _, a in scored if a) / n_total
    precision = hits / len(top_k)
    return {
        "n_total": n_total, "k": k, "boundary_score": boundary_score,
        "n_clearly_in": len(clearly_in), "n_tied_at_boundary": len(tied_at_boundary),
        "n_needed_from_tie": need, "hits": hits, "precision": precision,
        "base_rate": base_rate, "lift_pp": 100 * precision - 100 * base_rate,
    }


def load_classification_score() -> list[tuple[float, bool]]:
    """The CURRENT classifier's (classification, cap_band) TRAIN-rate score under
    relative_t0_primary, on the 2026 hold-out -- the same score check1_rescoring computed,
    recomputed here only to feed the mechanism check."""
    train_outcomes: dict[tuple[str, str], bool] = {}
    with open(RELABEL_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["collapsed_t0_primary"]
            if v != "":
                train_outcomes[(row["symbol"], row["event_date"])] = v == "True"

    train_class: dict[tuple[str, str], str] = {}
    with open(TRAIN_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            train_class[(row["symbol"], row["event_date"])] = row["classification"]

    from collections import defaultdict
    cells: dict[str, list[bool]] = defaultdict(list)
    for key, cls in train_class.items():
        if key in train_outcomes:
            cells[cls].append(train_outcomes[key])
    rate_table = {cls: sum(v) / len(v) for cls, v in cells.items() if v}
    print(f"  TRAIN (classification)->rate table: {rate_table}")

    holdout_outcomes: dict[tuple[str, str], bool] = {}
    with open(RELABEL_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] < TRAIN_CUTOFF:
                continue
            v = row["collapsed_t0_primary"]
            if v != "":
                holdout_outcomes[(row["symbol"], row["event_date"])] = v == "True"

    scored = []
    with open(HOLDOUT_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["symbol"], row["event_date"])
            if key not in holdout_outcomes:
                continue
            score = rate_table.get(row["classification"])
            if score is None:
                continue
            scored.append((score, holdout_outcomes[key]))
    return scored


def main() -> None:
    print("MECHANISM CHECK ONLY -- 2026 data is already spent for model selection.")
    print("This validates the top-decile/tie-break procedure runs correctly; it is NOT a result")
    print("about the redesign and must not be cited as one.\n")

    print("Current (existing) classifier's (classification)-only score, 2026 hold-out:")
    scored = load_classification_score()
    result = top_decile_lift(scored)
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
