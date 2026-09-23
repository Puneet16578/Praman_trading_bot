"""P8-007 scoping, item 4 (continued): re-run Phase 8b's clean-label feature AUC table
(scripts/phase8b_feature_reauc.py) excluding the 342 contaminated events
(data/raw/phase10_p8007_contaminated_events.csv), as a SENSITIVITY CHECK ONLY -- does not change
any published Phase 8b number, does not refit anything, does not amend the pre-registration.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase8b_feature_reauc as base  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
CONTAMINATED_PATH = ROOT / "data" / "raw" / "phase10_p8007_contaminated_events.csv"


def load_exclusion_set() -> set[tuple[str, str]]:
    with open(CONTAMINATED_PATH, encoding="utf-8") as f:
        return {(row["symbol"], row["event_date"]) for row in csv.DictReader(f)}


def main() -> None:
    exclude = load_exclusion_set()
    print(f"Excluding {len(exclude)} contaminated events from both TRAIN and HOLD-OUT populations.")

    train_outcomes, holdout_outcomes = base.load_label()
    train_outcomes = {k: v for k, v in train_outcomes.items() if k not in exclude}
    holdout_outcomes = {k: v for k, v in holdout_outcomes.items() if k not in exclude}
    features = base.load_features()
    print(f"TRAIN n={len(train_outcomes)} (was 63,363)  HOLD-OUT n={len(holdout_outcomes)} (was 6,049)")

    bands = ["Micro", "Small", "Mid", "Large", "Mega"]
    for feature in base.FEATURES:
        auc_t, n1t, n0t = base.auc_for_group(feature, train_outcomes, features, None)
        auc_h, n1h, n0h = base.auc_for_group(feature, holdout_outcomes, features, None)
        print(f"\n{feature}")
        print(f"  TRAIN    pooled AUC = {base.fmt(auc_t, n1t, n0t)}")
        print(f"  HOLD-OUT pooled AUC = {base.fmt(auc_h, n1h, n0h)}")


if __name__ == "__main__":
    main()
