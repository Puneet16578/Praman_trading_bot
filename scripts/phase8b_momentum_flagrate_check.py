"""Phase 8b, item 6: PARTIALLY_GROUNDED and UNEXPLAINED are, by construction
(src/classification/event_classifier.py's classify_event()), the SAME disclosure-tier population
(ROUTINE_ONLY, or NONE-and-not-isolated) split purely by momentum_high -- PARTIALLY_GROUNDED is
momentum_high=True, UNEXPLAINED is momentum_high=False, nothing else differs. So
docs/phase8_robustness_checks.md Check 3's finding that PARTIALLY_GROUNDED is flagged 2-3x more
often than UNEXPLAINED is, structurally, ALREADY a momentum_high comparison, not a disclosure-tier
one -- named here explicitly rather than left implicit.

The open question this script tests: is that flag-rate gap ABOUT momentum_high specifically (NSE's
own published ASM criteria include recent close-to-close price variation, docs/phase6_signals.md
Part B -- so momentum_high could be re-deriving one of the exchange's own trigger inputs), or does
disclosure_tier still matter once momentum_high is held fixed? Decisive test: does GROUNDED
(disclosure_tier=SUBSTANTIVE, which does NOT depend on momentum_high at all) ALSO show a flag-rate
gap by momentum_high? If yes, momentum_high has an effect that cuts across disclosure category,
supporting the re-derivation reading. If GROUNDED shows no such gap, the effect is specific to the
ROUTINE_ONLY/NONE population, not a general momentum_high property.

Same population, exclusions, and right-censoring discipline as
scripts/phase8_robustness_check3_leadtime.py.
"""
from __future__ import annotations
import bisect
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
HORIZONS = (20, 60, 120)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


def load_global_calendar() -> list[str]:
    dates = []
    with open(INDEX_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dates.append(row["date"])
    return sorted(dates)


def main() -> None:
    calendar = load_global_calendar()
    last_idx = len(calendar) - 1

    with open(HOLDOUT_CLASS_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    eligible_events: list[dict] = []
    already_flagged = gap_not_computable = 0
    for r in rows:
        note = r["subsequent_flag_note"]
        gap = r["sessions_to_subsequent_flag"]
        if note == "already under surveillance as of event_date":
            already_flagged += 1
            continue
        if gap in ("", "None") and "session gap not computable" in note:
            gap_not_computable += 1
            continue
        g_idx = bisect.bisect_left(calendar, r["event_date"])
        mh = r["momentum_high"]
        eligible_events.append({
            "disclosure_tier": r["disclosure_tier"],
            "momentum_high": mh if mh in ("True", "False") else "None",
            "classification": r["classification"],
            "gap": int(gap) if gap not in ("", "None") else None,
            "global_idx": g_idx,
        })
    print(f"Base population: {len(eligible_events)} "
          f"(excluded {already_flagged} already-flagged, {gap_not_computable} gap-not-computable)")

    for horizon in HORIZONS:
        print(f"\n{'='*105}\nHORIZON = {horizon} sessions (right-censored)\n{'='*105}")
        elig = [e for e in eligible_events if e["global_idx"] + horizon <= last_idx]
        print(f"Eligible n = {len(elig)}")

        print(f"\n  (a) Flag rate by momentum_high ALONE, pooled over every disclosure_tier/class:")
        by_mh: dict[str, list[dict]] = defaultdict(list)
        for e in elig:
            by_mh[e["momentum_high"]].append(e)
        for mh in ("True", "False", "None"):
            group = by_mh.get(mh, [])
            if not group:
                continue
            hits = sum(1 for e in group if e["gap"] is not None and e["gap"] <= horizon)
            p, lo, hi = wilson_ci(hits, len(group))
            print(f"    momentum_high={mh:6s} n={len(group):5d}  {hits:4d}/{len(group):5d} = {100*p:5.1f}%  "
                  f"95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")

        print(f"\n  (b) Flag rate by (disclosure_tier, momentum_high) -- decisive cell is SUBSTANTIVE,")
        print(f"      which does NOT depend on momentum_high in the classification rule at all:")
        by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for e in elig:
            by_cell[(e["disclosure_tier"], e["momentum_high"])].append(e)
        for tier in ("SUBSTANTIVE", "ROUTINE_ONLY", "NONE", "UNKNOWN_COVERAGE"):
            for mh in ("True", "False", "None"):
                group = by_cell.get((tier, mh), [])
                if not group:
                    continue
                hits = sum(1 for e in group if e["gap"] is not None and e["gap"] <= horizon)
                p, lo, hi = wilson_ci(hits, len(group))
                flag = "  <- GROUNDED, does not depend on momentum_high by construction" if tier == "SUBSTANTIVE" else ""
                print(f"    {tier:14s} x momentum_high={mh:6s}  n={len(group):5d}  "
                      f"{hits:4d}/{len(group):5d} = {100*p:5.1f}%  95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]{flag}")

        print(f"\n  (c) Sanity cross-check: PARTIALLY_GROUNDED vs UNEXPLAINED classification labels directly")
        by_cls: dict[str, list[dict]] = defaultdict(list)
        for e in elig:
            by_cls[e["classification"]].append(e)
        for cls in ("PARTIALLY_GROUNDED", "UNEXPLAINED"):
            group = by_cls.get(cls, [])
            if not group:
                continue
            hits = sum(1 for e in group if e["gap"] is not None and e["gap"] <= horizon)
            p, lo, hi = wilson_ci(hits, len(group))
            print(f"    {cls:20s} n={len(group):5d}  {hits:4d}/{len(group):5d} = {100*p:5.1f}%  "
                  f"95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")


if __name__ == "__main__":
    main()
