"""Phase 8 robustness check 3: lead time is conditional on being flagged -- every number in
docs/phase8_evaluation_results.md's lead-time section describes events that WERE flagged; it says
nothing about whether the classification predicts WHICH events get flagged at all.

For each horizon N in (20, 60, 120) sessions, computes the fraction of hold-out events flagged
WITHIN N sessions, per classification and per cap_band, against the whole-catalogue (pooled)
rate, with Wilson CIs -- using ALL eligible events as the denominator (not just the subset that
happened to get a lead time), so "never flagged" and "flagged after N" both count as misses.

Right-censoring (addition 5 of the robustness review): data ends 2026-09-15. An event from late
in the hold-out window has not had N sessions to BE flagged within yet, for any real reason -- this
is not evidence the flag rate is low, it is a calendar-time artifact. For each horizon N, only
events whose event_date is at least N GLOBAL trading sessions before the data's own most recent
date are included, and the eligible n is reported per (horizon, class, band) cell rather than
reusing the full 10,850 or 6,049 populations from other sections.

Two buckets are excluded from every horizon's denominator, for reasons stated once here:
  - "already under surveillance as of event_date" (no lead time to measure -- not a miss, not a hit)
  - "flag found but session gap not computable" (a real, small trading-calendar data gap, ~8 events
    -- we cannot say whether it was within N or not, so it is excluded rather than guessed)
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
    print(f"Global trading calendar: {len(calendar)} sessions, {calendar[0]} -> {calendar[-1]}")

    with open(HOLDOUT_CLASS_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Hold-out events: {len(rows)}")

    already_flagged = 0
    gap_not_computable = 0
    eligible_events: list[dict] = []
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
        eligible_events.append({
            "symbol": r["symbol"], "event_date": r["event_date"], "classification": r["classification"],
            "cap_band": r["cap_band"], "gap": int(gap) if gap not in ("", "None") else None,
            "global_idx": g_idx,
        })

    print(f"Excluded: {already_flagged} already under surveillance at event_date, "
          f"{gap_not_computable} flagged but session gap not computable")
    print(f"Base population for this check: {len(eligible_events)} events "
          f"(= {len(rows)} - {already_flagged} - {gap_not_computable})")

    for horizon in HORIZONS:
        print(f"\n{'='*100}\nHORIZON = {horizon} sessions -- fraction flagged WITHIN {horizon} sessions, "
              f"right-censoring applied\n{'='*100}")
        elig = [e for e in eligible_events if e["global_idx"] + horizon <= last_idx]
        dropped = len(eligible_events) - len(elig)
        print(f"Right-censoring: {dropped} of {len(eligible_events)} events dropped "
              f"(event_date is within {horizon} global sessions of the data's own end, 2026-09-15)")
        print(f"Eligible n for this horizon: {len(elig)}")

        hits_pooled = sum(1 for e in elig if e["gap"] is not None and e["gap"] <= horizon)
        p, lo, hi = wilson_ci(hits_pooled, len(elig))
        print(f"\n  POOLED (whole-catalogue rate): {hits_pooled}/{len(elig)} = {100*p:.1f}% "
              f"95% CI [{100*lo:.1f}%, {100*hi:.1f}%]")

        print(f"\n  By classification:")
        by_class: dict[str, list[dict]] = defaultdict(list)
        for e in elig:
            by_class[e["classification"]].append(e)
        for cls in sorted(by_class):
            group = by_class[cls]
            hits = sum(1 for e in group if e["gap"] is not None and e["gap"] <= horizon)
            p, lo, hi = wilson_ci(hits, len(group))
            print(f"    {cls:32s} n={len(group):5d}  {hits:4d}/{len(group):5d} = {100*p:5.1f}%  "
                  f"95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")

        print(f"\n  By cap_band:")
        by_band: dict[str, list[dict]] = defaultdict(list)
        for e in elig:
            by_band[e["cap_band"]].append(e)
        for band in sorted(by_band):
            group = by_band[band]
            hits = sum(1 for e in group if e["gap"] is not None and e["gap"] <= horizon)
            p, lo, hi = wilson_ci(hits, len(group))
            print(f"    {band:32s} n={len(group):5d}  {hits:4d}/{len(group):5d} = {100*p:5.1f}%  "
                  f"95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")


if __name__ == "__main__":
    main()
