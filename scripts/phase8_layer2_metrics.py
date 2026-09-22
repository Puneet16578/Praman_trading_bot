"""Phase 8, Layer 2: classification performance on the 2026 hold-out ONLY -- the first time this
data is touched in this evaluation (thresholds were frozen on 2019-2025 in
scripts/phase8_freeze_thresholds.py, before this script ever ran).

Four measurements, all stratified where the roster asked for it, all with confidence intervals
(Wilson score, matching scripts/analyze_collapse_rate_confidence_intervals.py's method):
1. Collapse rate by class x cap-band x horizon (30/60/90d) -- carried forward from the Phase 7b
   methodology, now correctly scoped to the frozen hold-out.
2. Precision@20: of the 20 hold-out events with the highest scored probability of collapse, how
   many actually collapsed (90d). Score = TRAIN-period (2019-2025) collapse rate for that event's
   (classification, cap_band) cell -- the same score doubles as the calibration input below.
3. Calibration: Brier score and a binned calibration table (predicted vs. observed, n per bin).
4. Lead time: for hold-out events not already under surveillance at event_date but later flagged,
   the distribution of sessions-to-flag, overall and by classification.
"""
from __future__ import annotations
import bisect
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, build_symbol_history

PRE_MOVE_LOOKBACK = 20
HORIZONS = (30, 60, 90)
PRIMARY_HORIZON = 90

HOLDOUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase8_2026_classifications.csv"
TRAIN_COLLAPSE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "collapse_rate_by_class.csv"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))

def g(hist, event_date: str, as_of: str):
    row = hist.price_row_as_of(event_date, as_of)
    if row is None:
        return None
    return row["close_price"] * hist.cum_factor_up_to(event_date)

def compute_multi_horizon_collapse(hist, event_date: str, direction: int) -> dict[int, bool | None]:
    days = hist.trading_days
    idx = bisect.bisect_left(days, event_date)
    if idx >= len(days) or days[idx] != event_date:
        return {h: None for h in HORIZONS}
    pre_idx = idx - PRE_MOVE_LOOKBACK
    if pre_idx < 0:
        return {h: None for h in HORIZONS}
    pre_date = days[pre_idx]
    base = g(hist, pre_date, FAR_FUTURE_AS_OF)
    if base is None or base == 0:
        return {h: None for h in HORIZONS}
    max_h = max(HORIZONS)
    scan_end = min(idx + max_h, len(days) - 1)
    first_collapse_k = None
    for k in range(idx + 1, scan_end + 1):
        gk = g(hist, days[k], FAR_FUTURE_AS_OF)
        if gk is None:
            continue
        if (direction > 0 and gk < base) or (direction < 0 and gk > base):
            first_collapse_k = k
            break
    out: dict[int, bool | None] = {}
    for h in HORIZONS:
        collapse_idx = idx + h
        if collapse_idx >= len(days):
            out[h] = None
            continue
        if hist.structural_break_in_window(pre_date, days[collapse_idx]):
            out[h] = None
            continue
        out[h] = first_collapse_k is not None and first_collapse_k <= collapse_idx
    return out

def load_holdout() -> list[dict]:
    with open(HOLDOUT_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_direction_from_catalogue() -> dict[tuple[str, str], int]:
    path = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
    directions = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            directions[(row["symbol"], row["event_date"])] = 1 if float(row["return_1d"]) > 0 else -1
    return directions

def train_collapse_rate_by_cell(horizon: int) -> dict[tuple[str, str], float]:
    """TRAIN-period (event_date < 2026) collapse rate per (classification, cap_band) cell, from
    the already-computed data/processed/collapse_rate_by_class.csv (production classifications,
    filtered to pre-2026 rows here) -- this is the score used for both precision@k ranking and
    calibration below."""
    field = f"collapsed_{horizon}d"
    cells: dict[tuple[str, str], list[bool]] = defaultdict(list)
    with open(TRAIN_COLLAPSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            v = row[field]
            if v == "":
                continue
            cells[(row["classification"], row["cap_band"])].append(v == "True")
    return {cell: sum(vals) / len(vals) for cell, vals in cells.items() if vals}

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    holdout = load_holdout()
    print(f"Loaded {len(holdout)} hold-out (2026) classified events")
    directions = load_direction_from_catalogue()

    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for r in holdout:
        by_symbol[r["symbol"]].append(r)

    rows_out = []
    import time
    t0 = time.time()
    n_sym = 0
    for symbol, events in by_symbol.items():
        n_sym += 1
        hist = build_symbol_history(conn, symbol)
        for e in events:
            direction = directions.get((symbol, e["event_date"]))
            if direction is None:
                continue
            collapse = compute_multi_horizon_collapse(hist, e["event_date"], direction)
            rows_out.append({
                "symbol": symbol, "event_date": e["event_date"], "classification": e["classification"],
                "cap_band": e["cap_band"], "sessions_to_subsequent_flag": e["sessions_to_subsequent_flag"],
                "collapsed_30d": collapse[30], "collapsed_60d": collapse[60], "collapsed_90d": collapse[90],
            })
        if n_sym % 500 == 0:
            print(f"  ...{n_sym}/{len(by_symbol)} symbols, {time.time()-t0:.0f}s elapsed")
    print(f"Outcome labels computed for {len(rows_out)} hold-out events in {time.time()-t0:.0f}s")

    out_path = OUTPUT_DIR / "phase8_2026_outcomes.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Persisted {out_path}")

    # Re-load from disk for every measurement below rather than reusing the in-memory `rows_out`
    # list: csv.DictWriter serializes True/False/None to the strings "True"/"False"/"" on write,
    # but `rows_out` itself still holds real Python booleans/None in memory. Comparing those
    # directly against string literals (`r[field] == "True"`) silently evaluates to False for
    # every row (True == "True" is False in Python) -- exactly the bug that produced an initial,
    # impossible 0.0% collapse rate across every single class/band/horizon cell on the first run
    # of this script. Re-reading as strings, the same convention the original
    # measure_collapse_rate_by_class.py/analyze_collapse_rate_confidence_intervals.py scripts use,
    # avoids this whole class of error rather than fixing the comparison in six separate places.
    with open(out_path, encoding="utf-8") as f:
        rows_out = list(csv.DictReader(f))

    # ============================================================
    # Measurement 1: collapse rate by class x band x horizon, CIs
    # ============================================================
    print(f"\n{'='*90}\nMEASUREMENT 1: collapse rate by class x cap-band x horizon (2026 hold-out)\n{'='*90}")
    for horizon in HORIZONS:
        field = f"collapsed_{horizon}d"
        print(f"\n-- {horizon}-session horizon --")
        bands = sorted({r["cap_band"] for r in rows_out})
        classes = sorted({r["classification"] for r in rows_out})
        for band in bands:
            print(f"  [{band}]")
            for cls in classes:
                vals = [r[field] == "True" for r in rows_out if r["cap_band"] == band and r["classification"] == cls and r[field] != ""]
                n = len(vals)
                if n == 0:
                    print(f"    {cls:32s} n=0")
                    continue
                p, lo, hi = wilson_ci(sum(vals), n)
                print(f"    {cls:32s} n={n:5d}  rate={100*p:5.1f}%  95% CI [{100*lo:5.1f}%, {100*hi:5.1f}%]")

    # ============================================================
    # Measurement 2 + 3: precision@20 and calibration (train-derived score)
    # ============================================================
    train_scores = train_collapse_rate_by_cell(PRIMARY_HORIZON)
    print(f"\n{'='*90}\nMEASUREMENT 2+3: precision@20 and calibration (score = TRAIN {PRIMARY_HORIZON}d collapse rate for (class,band))\n{'='*90}")
    print(f"TRAIN-derived (class, band) -> P(collapse) cells: {len(train_scores)}")

    scored = []
    for r in rows_out:
        actual = r[f"collapsed_{PRIMARY_HORIZON}d"]
        if actual == "":
            continue
        cell = (r["classification"], r["cap_band"])
        score = train_scores.get(cell)
        if score is None:
            continue
        scored.append({"symbol": r["symbol"], "event_date": r["event_date"], "score": score, "actual": actual == "True"})
    print(f"{len(scored)} hold-out events have both a score and a known {PRIMARY_HORIZON}d outcome")

    scored_sorted = sorted(scored, key=lambda x: -x["score"])
    top20 = scored_sorted[:20]
    k_hits = sum(1 for x in top20 if x["actual"])
    p, lo, hi = wilson_ci(k_hits, len(top20))
    print(f"\nPrecision@20 (highest-scored events, whole 2026 hold-out as one period):")
    print(f"  {k_hits}/{len(top20)} collapsed within {PRIMARY_HORIZON} sessions -- rate {100*p:.1f}% 95% CI [{100*lo:.1f}%, {100*hi:.1f}%]")
    print(f"  Score range in top 20: [{top20[-1]['score']:.3f}, {top20[0]['score']:.3f}]")

    # Honesty check, not a footnote: the score is a coarse (classification, cap_band) lookup with
    # only ~25 distinct values, so "top 20" is very likely 20 arbitrarily-ordered events from a
    # much larger group tied at the maximum score -- NOT a genuine fine-grained top-20 ranking.
    # Reported explicitly rather than presenting an arbitrary subsample as if it were precise.
    max_score = scored_sorted[0]["score"]
    tied_at_max = [x for x in scored if x["score"] == max_score]
    tied_hits = sum(1 for x in tied_at_max if x["actual"])
    tp, tlo, thi = wilson_ci(tied_hits, len(tied_at_max))
    print(f"  CAVEAT: {len(tied_at_max)} events are tied at this max score ({max_score:.3f}) -- the")
    print(f"  'top 20' above is an arbitrary 20 of these {len(tied_at_max)}, not a fine-grained ranking.")
    print(f"  Precision over the FULL tied-at-max group (n={len(tied_at_max)}): {tied_hits}/{len(tied_at_max)} "
          f"= {100*tp:.1f}% 95% CI [{100*tlo:.1f}%, {100*thi:.1f}%] -- the more statistically meaningful number.")

    brier = sum((x["score"] - (1.0 if x["actual"] else 0.0)) ** 2 for x in scored) / len(scored)
    print(f"\nBrier score (full agent system, n={len(scored)}): {brier:.4f}  (0=perfect, 0.25=always predicting 0.5, 1=perfectly wrong)")

    print(f"\nCalibration table (5 bins by predicted score):")
    bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]
    for lo_e, hi_e in zip(bin_edges[:-1], bin_edges[1:]):
        bucket = [x for x in scored if lo_e <= x["score"] < hi_e]
        n = len(bucket)
        if n == 0:
            print(f"  [{lo_e:.1f}, {hi_e:.1f}) n=0")
            continue
        mean_pred = sum(x["score"] for x in bucket) / n
        observed = sum(1 for x in bucket if x["actual"]) / n
        p, clo, chi = wilson_ci(sum(1 for x in bucket if x["actual"]), n)
        print(f"  [{lo_e:.1f}, {hi_e:.1f})  n={n:5d}  mean predicted={mean_pred:.3f}  observed={observed:.3f} 95% CI [{clo:.3f}, {chi:.3f}]")

    calibration_path = OUTPUT_DIR / "phase8_calibration.csv"
    with open(calibration_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "event_date", "score", "actual"])
        writer.writeheader()
        writer.writerows(scored)
    print(f"Persisted per-event scores/outcomes to {calibration_path}")

    # ============================================================
    # Measurement 4: lead time to subsequent flag, by classification
    # ============================================================
    print(f"\n{'='*90}\nMEASUREMENT 4: lead time to subsequent surveillance flag (2026 hold-out)\n{'='*90}")
    lead_times_all = []
    lead_times_by_class: dict[str, list[int]] = defaultdict(list)
    for r in rows_out:
        v = r["sessions_to_subsequent_flag"]
        if v in ("", "None"):
            continue
        gap = int(v)
        lead_times_all.append(gap)
        lead_times_by_class[r["classification"]].append(gap)

    def summarize(vals: list[int]) -> str:
        if not vals:
            return "n=0"
        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        median = vals_sorted[n // 2]
        p25 = vals_sorted[int(n * 0.25)]
        p75 = vals_sorted[int(n * 0.75)]
        return f"n={n:4d}  median={median:3d}  p25={p25:3d}  p75={p75:3d}  min={vals_sorted[0]:3d}  max={vals_sorted[-1]:3d}"

    print(f"Overall: {summarize(lead_times_all)}")
    for cls in sorted(lead_times_by_class):
        print(f"  {cls:32s} {summarize(lead_times_by_class[cls])}")

    leadtime_path = OUTPUT_DIR / "phase8_lead_time.csv"
    with open(leadtime_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "event_date", "classification", "sessions_to_subsequent_flag"])
        for r in rows_out:
            v = r["sessions_to_subsequent_flag"]
            if v not in ("", "None"):
                writer.writerow([r["symbol"], r["event_date"], r["classification"], v])
    print(f"Persisted lead-time rows to {leadtime_path}")

    conn.close()

if __name__ == "__main__":
    main()
