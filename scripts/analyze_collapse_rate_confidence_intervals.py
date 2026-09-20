"""Phase 7b follow-up: confidence intervals on every cell of the collapse-rate-by-class table
(data/processed/collapse_rate_by_class.csv, produced by measure_collapse_rate_by_class.py), plus
an explicit check of whether the classes are distinguishable from chance within each band -- a
table of bare point estimates invites over-reading (e.g. a one-cell ordering flip that is well
within noise being read as a real reversal).

Wilson score interval (not the normal approximation) -- correct near p=0/1 and at small n, which
matters here since some cells are thin. z=1.96 for a 95% interval.

This script does NOT re-derive collapse_30d/60d/90d -- it aggregates the already-computed,
already-verified per-event rows.
"""
from __future__ import annotations
import csv
import math
from collections import defaultdict
from pathlib import Path

INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "collapse_rate_by_class.csv"
HORIZONS = ("collapsed_30d", "collapsed_60d", "collapsed_90d")
INSUFFICIENT_N = 50  # below this, a point estimate is not reported as a number -- see module docstring

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Returns (point_estimate, lower, upper), all as fractions in [0,1]."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))

def intervals_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]

def main() -> None:
    with open(INPUT_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} events")

    for horizon in HORIZONS:
        print(f"\n{'='*90}\n{horizon}\n{'='*90}")
        cells: dict[tuple[str, str], list[bool]] = defaultdict(list)
        for r in rows:
            v = r[horizon]
            if v == "":
                continue
            cells[(r["cap_band"], r["classification"])].append(v == "True")

        bands = sorted({k[0] for k in cells})
        classes = ["GROUNDED", "PARTIALLY_GROUNDED", "UNEXPLAINED_ISOLATED", "UNEXPLAINED", "UNEXPLAINED_UNKNOWN_COVERAGE"]

        band_results: dict[str, dict[str, tuple]] = {}
        for band in bands:
            print(f"\n[{band}]")
            results = {}
            for cls in classes:
                vals = cells.get((band, cls), [])
                n = len(vals)
                k = sum(vals)
                if n < INSUFFICIENT_N:
                    print(f"  {cls:32s} n={n:6d}  INSUFFICIENT (below n={INSUFFICIENT_N}) -- no rate reported")
                    results[cls] = None
                    continue
                p, lo, hi = wilson_ci(k, n)
                results[cls] = (p, lo, hi, n)
                print(f"  {cls:32s} n={n:6d}  rate={100*p:5.1f}%  95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")
            band_results[band] = results

        print(f"\n  -- distinguishability checks, {horizon} --")
        for band in bands:
            results = band_results[band]
            grounded = results.get("GROUNDED")
            others = {c: results[c] for c in ("PARTIALLY_GROUNDED", "UNEXPLAINED_ISOLATED", "UNEXPLAINED") if results.get(c)}
            if grounded is None:
                print(f"  [{band}] GROUNDED insufficient -- cannot compare")
                continue
            g_ci = (grounded[1], grounded[2])
            for cls, res in others.items():
                overlap = intervals_overlap(g_ci, (res[1], res[2]))
                print(f"  [{band}] GROUNDED vs {cls:22s} {'CI OVERLAP (not distinguishable)' if overlap else 'CIs disjoint (distinguishable)'}")
            # pairwise among the three non-grounded classes -- do they separate from EACH OTHER,
            # or only collectively from GROUNDED (the reframed claim under test)
            names = list(others.keys())
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    a, b = others[names[i]], others[names[j]]
                    overlap = intervals_overlap((a[1], a[2]), (b[1], b[2]))
                    print(f"  [{band}] {names[i]:22s} vs {names[j]:22s} {'CI OVERLAP' if overlap else 'CIs disjoint'}")

if __name__ == "__main__":
    main()
