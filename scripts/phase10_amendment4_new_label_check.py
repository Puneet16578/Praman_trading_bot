"""Amendment 4 prep round 4, items 2-3: old-vs-new label agreement, and the new definition's
missing-outcome rate for TRAIN vs. HOLD-OUT -- the number the commit rule is decided from.
"""
from __future__ import annotations
import bisect
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
OLD_LABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative_OLD_own_session.csv"
NEW_LABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
TRAIN_CUTOFF = "2026-01-01"
HORIZON = 90


def load(path):
    with open(path, encoding="utf-8") as f:
        return {(r["symbol"], r["event_date"]): r for r in csv.DictReader(f)}


def main() -> None:
    old = load(OLD_LABEL_PATH)
    new = load(NEW_LABEL_PATH)
    print(f"OLD rows: {len(old)}  NEW rows: {len(new)}")

    # --- item 2: old vs new agreement, overall and by cap_band ---
    both = []
    for key, o in old.items():
        n = new.get(key)
        if n is None:
            continue
        if o["collapsed_t0_primary"] in ("", "None") or n["collapsed_t0_primary"] in ("", "None"):
            continue
        both.append((key, o["collapsed_t0_primary"] == "True", n["collapsed_t0_primary"] == "True", o["cap_band"]))

    agree = sum(1 for _, ov, nv, _ in both if ov == nv)
    print(f"\nBoth old and new have a computable label: {len(both)}")
    print(f"Agreement: {agree} ({100*agree/len(both):.3f}%)")

    print("\nBy cap_band:")
    by_band = defaultdict(lambda: [0, 0])
    for _, ov, nv, band in both:
        by_band[band][0] += 1
        if ov == nv:
            by_band[band][1] += 1
    for band in ("Micro", "Small", "Mid", "Large", "Mega"):
        n, a = by_band.get(band, [0, 0])
        rate = 100 * a / n if n else float("nan")
        print(f"  {band:8s} n={n:6d}  agree={a:6d}  rate={rate:.3f}%")

    # --- item 3: new definition's missing-outcome rate, TRAIN vs HOLD-OUT ---
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        global_days = [r["date"] for r in csv.DictReader(f)]

    def fully_elapsed_missing(rows):
        n, missing = 0, 0
        for key, r in rows.items():
            ed = key[1]
            idx = bisect.bisect_left(global_days, ed)
            if not (idx < len(global_days) and global_days[idx] == ed):
                continue
            if idx + HORIZON >= len(global_days):
                continue  # global t+90 hasn't happened yet as of data end
            n += 1
            if r["signed_return_90d"] in ("", "None"):
                missing += 1
        return n, missing

    train_rows = {k: r for k, r in new.items() if k[1] < TRAIN_CUTOFF}
    holdout_rows = {k: r for k, r in new.items() if k[1] >= TRAIN_CUTOFF}

    n_tr, m_tr = fully_elapsed_missing(train_rows)
    n_ho, m_ho = fully_elapsed_missing(holdout_rows)
    rate_tr = 100 * m_tr / n_tr if n_tr else float("nan")
    rate_ho = 100 * m_ho / n_ho if n_ho else float("nan")

    print(f"\n=== NEW DEFINITION missing-outcome rate (global t+90 has occurred as of data end) ===")
    print(f"TRAIN:    n={n_tr}  missing={m_tr}  rate={rate_tr:.3f}%")
    print(f"HOLD-OUT: n={n_ho}  missing={m_ho}  rate={rate_ho:.3f}%")
    print(f"Gap: {abs(rate_tr - rate_ho):.3f}pp")
    print(f"\nCommit rule: gap must be <= 2.0pp. {'PASS -> COMMIT' if abs(rate_tr-rate_ho) <= 2.0 else 'FAIL -> STOP'}")


if __name__ == "__main__":
    main()
