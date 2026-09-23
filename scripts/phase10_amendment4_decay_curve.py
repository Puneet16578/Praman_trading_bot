"""Amendment 4 prep round 3, item 1: measure the missing-outcome rate's DECAY CURVE by buffer
band, on the TRAIN replicate (artificial truncation at 2024-06-30), WITH the P8-012 series
extension (EQ, extended through BE/BZ strictly after EQ's own last date) applied to the truncated
view -- exactly the logic build_symbol_history/compute_outcome_labels.py use in production, just
restricted to bhavcopy rows with event_date <= the truncation date.

Round 2's diagnosis (docs/phase10_amendment4_prep2.md) used two buffer bands (near-boundary vs.
safely-earlier) and picked 20 sessions by matching the fix's own stated delay -- not derived from
where the artifact actually stops mattering. This measures the full decay curve instead, so the
plateau (and the buffer B that reaches it) is read off real data, not assumed.
"""
from __future__ import annotations
import bisect
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
OUTCOME_LABELS_PATH = ROOT / "data" / "processed" / "outcome_labels.csv"
TRAIN_CUTOFF = "2026-01-01"
TRUNCATION_DATE = "2024-06-30"
HORIZON = 90
EXTEND_SERIES = ("BE", "BZ")

BANDS = [(0, 15), (15, 30), (30, 45), (45, 60), (60, 75), (75, 90), (90, 120), (120, None)]


def load_global_days() -> list[str]:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        return [r["date"] for r in csv.DictReader(f)]


def load_outcomes() -> list[dict]:
    with open(OUTCOME_LABELS_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def band_for(buffer: int) -> str:
    for lo, hi in BANDS:
        if hi is None:
            if buffer >= lo:
                return f"{lo}+"
        elif lo <= buffer < hi:
            return f"{lo}-{hi}"
    raise AssertionError(buffer)


def main() -> None:
    global_days = load_global_days()
    outcomes = load_outcomes()
    train = [r for r in outcomes if r["event_date"] < TRAIN_CUTOFF]

    trunc_idx = bisect.bisect_right(global_days, TRUNCATION_DATE) - 1
    print(f"Truncation date {TRUNCATION_DATE} -> real global index {trunc_idx} "
          f"({global_days[trunc_idx]})")

    # Assign each TRAIN event (whose naive global t+90 falls at/before the truncation) a buffer
    # and a band.
    banded_events: dict[str, list[dict]] = {band_for(lo): [] for lo, hi in BANDS}
    for r in train:
        if r["event_date"] >= TRUNCATION_DATE:
            continue
        idx = bisect.bisect_left(global_days, r["event_date"])
        if not (idx < len(global_days) and global_days[idx] == r["event_date"]):
            continue
        t90_idx = idx + HORIZON
        if t90_idx > trunc_idx:
            continue  # doesn't even naively fit before the truncation
        buffer = trunc_idx - t90_idx
        banded_events[band_for(buffer)].append(r)

    total_n = sum(len(v) for v in banded_events.values())
    print(f"Total TRAIN events assigned to a band: {total_n}")

    all_symbols = sorted({r["symbol"] for v in banded_events.values() for r in v})
    print(f"Distinct symbols involved: {len(all_symbols)}")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    placeholders = ",".join("?" * len(all_symbols))
    primary_rows = conn.execute(
        f"SELECT symbol, event_date FROM bhavcopy WHERE series='EQ' AND event_date <= ? "
        f"AND symbol IN ({placeholders}) ORDER BY symbol, event_date",
        (TRUNCATION_DATE, *all_symbols),
    ).fetchall()
    primary_days: dict[str, list[str]] = {}
    for r in primary_rows:
        primary_days.setdefault(r["symbol"], []).append(r["event_date"])

    ext_rows = conn.execute(
        f"SELECT symbol, event_date FROM bhavcopy WHERE series IN ({','.join('?' * len(EXTEND_SERIES))}) "
        f"AND event_date <= ? AND symbol IN ({placeholders}) ORDER BY symbol, event_date",
        (*EXTEND_SERIES, TRUNCATION_DATE, *all_symbols),
    ).fetchall()
    ext_days: dict[str, list[str]] = {}
    for r in ext_rows:
        ext_days.setdefault(r["symbol"], []).append(r["event_date"])

    combined_days: dict[str, list[str]] = {}
    for sym in all_symbols:
        p_days = primary_days.get(sym, [])
        primary_last = p_days[-1] if p_days else None
        e_days = [d for d in ext_days.get(sym, []) if primary_last is not None and d > primary_last]
        combined_days[sym] = sorted(p_days + e_days)

    conn.close()

    print(f"\n{'Band':>10s}  {'n':>7s}  {'lacking':>8s}  {'rate':>8s}")
    band_results = {}
    for lo, hi in BANDS:
        label = band_for(lo)
        events = banded_events[label]
        n = len(events)
        lacking = 0
        for r in events:
            days = combined_days.get(r["symbol"], [])
            idx = bisect.bisect_left(days, r["event_date"])
            if not (idx < len(days) and days[idx] == r["event_date"]):
                continue
            if idx + HORIZON >= len(days):
                lacking += 1
        rate = 100 * lacking / n if n else float("nan")
        band_results[label] = (n, lacking, rate)
        print(f"{label:>10s}  {n:>7d}  {lacking:>8d}  {rate:>7.3f}%")

    # Plateau: smallest buffer B such that every band with lower bound >= B has a rate within
    # 1.0pp of the 120+ band's rate.
    ref_rate = band_results["120+"][2]
    print(f"\n120+ band rate (reference): {ref_rate:.3f}%")
    print("\nDeviation from 120+ band, per band lower bound:")
    plateau_b = None
    lower_bounds = [lo for lo, hi in BANDS]
    for lo in lower_bounds:
        label = band_for(lo)
        rate = band_results[label][2]
        dev = abs(rate - ref_rate)
        print(f"  buffer>={lo:4d}: band={label:>7s} rate={rate:.3f}%  |dev from 120+|={dev:.3f}pp")

    # Find smallest B (among band lower bounds) such that this band AND every band above it are
    # within 1.0pp of the 120+ rate.
    for i, lo in enumerate(lower_bounds):
        remaining = lower_bounds[i:]
        if all(abs(band_results[band_for(b)][2] - ref_rate) <= 1.0 for b in remaining):
            plateau_b = lo
            break

    print(f"\nPLATEAU B (smallest buffer beyond which every band is within 1.0pp of 120+): "
          f"{plateau_b if plateau_b is not None else 'NOT REACHED by 120+ sessions'}")


if __name__ == "__main__":
    main()
