"""Phase 5: build the full event catalogue from the real store and report the threshold
comparison. Reproducible with one command: `python scripts/build_event_catalogue.py`. No new
tables are written -- the catalogue is derived data, recomputed fresh from bhavcopy +
corporate_actions + surveillance_flags every run (see event_catalogue.py's module docstring).
"""
from __future__ import annotations
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.signals.event_catalogue import DailyStat, build_symbol_history, compute_daily_stats
from src.signals.surveillance_state import current_surveillance_state

GSM_FLOOR = "2025-01-01"  # before this, GSM cannot be surveillance-labeled at all (scope decision)

# Three candidate thresholds, bracketing the user's own suggested starting point (B).
THRESHOLDS = {
    "A_loose":  {"z": 2.5, "cum20": 0.20, "vol": 2.0},
    "B_suggested": {"z": 3.0, "cum20": 0.25, "vol": 3.0},
    "C_tight": {"z": 3.5, "cum20": 0.35, "vol": 4.0},
}

def classify(stat: DailyStat, thr: dict) -> str | None:
    """Returns which path(s) triggered, or None. Volume is a required AND-gate on top of
    whichever return-based path fires, per the spec's "... AND volume above Nx" structure."""
    if stat.volume_ratio is None or stat.volume_ratio <= thr["vol"]:
        return None
    z_path = stat.zscore_60d is not None and abs(stat.zscore_60d) > thr["z"]
    cum_path = stat.return_20d is not None and abs(stat.return_20d) > thr["cum20"]
    if z_path and cum_path:
        return "both"
    if z_path:
        return "z_only"
    if cum_path:
        return "cum20_only"
    return None

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    symbols = [r[0] for r in conn.execute("SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ' ORDER BY symbol").fetchall()]
    print(f"Building event catalogue for {len(symbols)} EQ symbols...")

    all_stats: list[DailyStat] = []
    turnover_by_year: dict[str, list[float]] = defaultdict(list)
    demerger_excluded_1d = 0
    demerger_excluded_20d = 0
    gsm_gap_count = 0
    delivery_missing_count = 0

    t0 = time.time()
    for i, symbol in enumerate(symbols):
        hist = build_symbol_history(conn, symbol)
        stats = compute_daily_stats(hist)
        all_stats.extend(stats)
        for s in stats:
            year = s.event_date[:4]
            turnover_by_year[year].append(s.close_price_raw * s.traded_qty)
            if s.return_1d_demerger_excluded:
                demerger_excluded_1d += 1
            if s.return_20d_demerger_excluded:
                demerger_excluded_20d += 1
            if s.event_date < GSM_FLOOR:
                gsm_gap_count += 1
            if s.delivery_pct is None:
                delivery_missing_count += 1
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(symbols)} symbols, {len(all_stats)} stat-rows so far, {time.time() - t0:.0f}s elapsed")

    print(f"\nDone: {len(all_stats)} total daily-stat rows across {len(symbols)} symbols in {time.time() - t0:.0f}s")

    # Market-cap-proxy terciles, computed PER YEAR (absolute rupee turnover isn't comparable across
    # 7 years of market growth) from the turnover distribution of every emitted stat that year.
    year_terciles: dict[str, tuple[float, float]] = {}
    for year, values in turnover_by_year.items():
        values_sorted = sorted(values)
        n = len(values_sorted)
        year_terciles[year] = (values_sorted[n // 3], values_sorted[2 * n // 3])

    def cap_band(stat: DailyStat) -> str:
        year = stat.event_date[:4]
        lo, hi = year_terciles[year]
        turnover = stat.close_price_raw * stat.traded_qty
        if turnover <= lo:
            return "Small"
        if turnover <= hi:
            return "Mid"
        return "Large"

    print("\nJoining surveillance state (as-of each event_date)...")
    surv_cache: dict[tuple[str, str], dict] = {}
    def surv_status(symbol: str, event_date: str) -> str:
        key = (symbol, event_date)
        if key not in surv_cache:
            surv_cache[key] = current_surveillance_state(conn, symbol, event_date)
        state = surv_cache[key]
        active = {m: s for m, s in state.items() if s is not None}
        return "UNDER_SURVEILLANCE" if active else "NOT_FLAGGED"

    print("\n" + "=" * 80)
    print("THRESHOLD COMPARISON")
    print("=" * 80)
    for label, thr in THRESHOLDS.items():
        matched = [(s, classify(s, thr)) for s in all_stats]
        matched = [(s, path) for s, path in matched if path is not None]
        print(f"\n--- {label}: |z|>{thr['z']} or 20d-cum>{thr['cum20']*100:.0f}%, AND vol>{thr['vol']}x ---")
        print(f"  Total events: {len(matched)}")
        path_counts = defaultdict(int)
        for _, path in matched:
            path_counts[path] += 1
        print(f"  z-score path alone: {path_counts['z_only']}")
        print(f"  20-day cumulative path alone: {path_counts['cum20_only']}")
        print(f"  both paths together: {path_counts['both']}")

        by_year = defaultdict(int)
        by_band = defaultdict(int)
        by_surv = defaultdict(int)
        for s, _ in matched:
            by_year[s.event_date[:4]] += 1
            by_band[cap_band(s)] += 1
            by_surv[surv_status(s.symbol, s.event_date)] += 1
        print(f"  By year: {dict(sorted(by_year.items()))}")
        print(f"  By market-cap-proxy band (turnover tercile, per-year): {dict(by_band)}")
        print(f"  By ASM/GSM status at the time: {dict(by_surv)}")

    print("\n" + "=" * 80)
    print("EXCLUSIONS / GAPS")
    print("=" * 80)
    print(f"1-day return windows excluded by demerger overlap: {demerger_excluded_1d}")
    print(f"20-day cumulative windows excluded by demerger overlap: {demerger_excluded_20d}")
    print(f"Events before {GSM_FLOOR} (GSM coverage gap -- cannot be GSM-labeled, ASM labeling still valid): "
          f"{gsm_gap_count} / {len(all_stats)} ({100*gsm_gap_count/len(all_stats):.1f}%)")
    print(f"Events with missing delivery_pct that day: {delivery_missing_count} / {len(all_stats)} "
          f"({100*delivery_missing_count/len(all_stats):.3f}%)")

    conn.close()

if __name__ == "__main__":
    main()
