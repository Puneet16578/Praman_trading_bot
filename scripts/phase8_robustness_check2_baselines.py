"""Phase 8 robustness check 2: the 0.192 constant baseline in docs/phase8_evaluation_results.md is
an ORACLE (it predicts 2026's own true mean, unknowable as of 2025-12-31) -- relabelled here, kept,
and joined by a FAIR baseline (a constant at the real 2019-2025 base rate, computable before 2026
ever happened) scored on the identical 6,049 hold-out events. Also replaces the random baseline's
degenerate n=1 precision row with its expected precision (the base rate), since a continuous random
score's arg-max is a uniformly random event -- P(hit) = the population base rate in expectation,
not a measured statistic over a sample of 1.

Uses the SAME label (raw collapsed_90d) and the SAME 6,049-event hold-out as the original Layer 3
table -- this check is about the baseline TABLE's framing, not the label (that is Check 1).
"""
from __future__ import annotations
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_SCORES_PATH = ROOT / "data" / "processed" / "phase8_baseline_scores.csv"
TRAIN_OUTCOMES_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
TRAIN_CUTOFF = "2026-01-01"


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


def main() -> None:
    with open(BASELINE_SCORES_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    actuals = [row["actual"] == "True" for row in rows]
    n = len(actuals)
    holdout_rate = sum(actuals) / n
    print(f"2026 hold-out: n={n}, true collapse rate = {100*holdout_rate:.4f}% (this is what ORACLE predicts)")

    train_vals = []
    with open(TRAIN_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= TRAIN_CUTOFF:
                continue
            v = row["collapsed_90d"]
            if v == "":
                continue
            train_vals.append(v == "True")
    fair_rate = sum(train_vals) / len(train_vals)
    print(f"2019-2025 TRAIN: n={len(train_vals)}, true collapse rate = {100*fair_rate:.4f}% "
          f"(this is what the FAIR baseline predicts -- computable as of 2025-12-31, unlike ORACLE)")

    def brier_const(c: float) -> float:
        return sum((c - (1.0 if a else 0.0)) ** 2 for a in actuals) / n

    oracle_brier = brier_const(holdout_rate)
    fair_brier = brier_const(fair_rate)
    print(f"\nORACLE (constant={holdout_rate:.4f}, the 2026 hold-out's own mean) Brier on 2026 hold-out: {oracle_brier:.4f}")
    print(f"FAIR   (constant={fair_rate:.4f}, the 2019-2025 TRAIN mean)         Brier on 2026 hold-out: {fair_brier:.4f}")

    # Random baseline's real, existing per-event scores (already in phase8_baseline_scores.csv)
    random_scores = [float(row["1_random"]) for row in rows]
    random_brier = sum((s - (1.0 if a else 0.0)) ** 2 for s, a in zip(random_scores, actuals)) / n
    max_score = max(random_scores)
    tied_n = sum(1 for s in random_scores if s == max_score)
    print(f"\nRandom baseline: real measured Brier (per-event random scores, unchanged) = {random_brier:.4f}")
    print(f"Random baseline: max score={max_score:.6f}, n tied at max = {tied_n} "
          f"(degenerate -- a continuous uniform score essentially never ties)")
    p, lo, hi = wilson_ci(sum(actuals), n)
    print(f"Random baseline's EXPECTED precision at its own arg-max = the population base rate "
          f"(the identity of the arg-max event is uniformly distributed over all n, by construction): "
          f"{100*p:.1f}% 95% CI [{100*lo:.1f}%, {100*hi:.1f}%] (n={n}, same interval as the base rate itself)")

    print(f"\n{'='*90}\nRevised Layer 3 baseline framing\n{'='*90}")
    print(f"{'Baseline':45s} {'Brier':>8s}  Precision(max tier)")
    print(f"{'1. Random':45s} {random_brier:8.4f}  {100*p:.1f}% [{100*lo:.1f}%, {100*hi:.1f}%]  "
          f"(theoretical expectation, not a measured n=1 sample)")
    print(f"{'FAIR (constant = 2019-2025 TRAIN rate)':45s} {fair_brier:8.4f}  n/a (constant score, no ranking)")
    print(f"{'ORACLE (constant = 2026 hold-out true rate)':45s} {oracle_brier:8.4f}  n/a (constant score, no ranking)")
    print(f"{'3. Disclosure tier alone':45s} {'(see docs/phase8_evaluation_results.md Layer 3)':>8s}")
    print(f"{'4. Deterministic classifier':45s} {'(see docs/phase8_evaluation_results.md Layer 3)':>8s}")


if __name__ == "__main__":
    main()
