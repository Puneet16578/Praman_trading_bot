"""Phase 5 final event definition, per the LOOSE/z-score-only decision recorded in
docs/phase5_event_catalogue.md Sec.4b. Distinct from build_event_catalogue.py, which stays as-is
as the historical record of the three-bracket AND/OR threshold comparison that informed this
decision -- this script implements the definition actually chosen and persists its output.

Event definition: |z-score(60d)| > 2.5 AND volume_ratio > 2.0x. The 20-day cumulative-return path
is NOT part of the trigger (dropped per instruction) -- return_20d is still computed and recorded
on every matched row as context, just not used to decide membership.

On top of that trigger, a matched day is further excluded if it falls within the ex-date of a
demerger for that same symbol plus the following 60 real trading sessions (matching
TRAILING_WINDOW) -- not just the single day whose 1-day return spans the ex-date. Rationale
(docs/phase5_event_catalogue.md Sec.4d): the demerger's mechanical price-level shift contaminates
the trailing distribution and price-discovery period for weeks afterward (e.g. RELIANCE/Jio
Financial: JioFin's reference price was set the morning of the ex-date, but did not begin separate
trading until 2023-08-21, over four weeks later) -- a single-day exclusion removes the sharpest
artifact but leaves this residual window's events computed against a baseline that just underwent
a real, structural, non-volatility-driven step change. Measured cost before adopting this (Sec.4d):
93 events (0.12% of the un-widened 90-demerger catalogue) fell inside such a window across 49
symbols -- judged cheap relative to removing structurally-confounded data.

Persists to data/processed/event_catalogue_loose_zscore_only.csv (gitignored, same as the DB
itself -- this is a derived, fully reproducible artifact, not a new fact source; re-running this
script regenerates it from the store, and per the bitemporal-republication note in the phase doc,
a re-run after NSE republishes a correction inside some trailing window can legitimately differ
slightly from a prior run).
"""
from __future__ import annotations
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
from src.signals.event_catalogue import DailyStat, build_symbol_history, compute_daily_stats
from src.signals.surveillance_state import current_surveillance_state

ISIN_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"

Z_THRESHOLD = 2.5
VOL_THRESHOLD = 2.0
GSM_FLOOR = "2025-01-01"
POST_DEMERGER_EXCLUSION_SESSIONS = 60

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"

def is_event(stat: DailyStat) -> bool:
    if stat.volume_ratio is None or stat.volume_ratio <= VOL_THRESHOLD:
        return False
    return stat.zscore_60d is not None and abs(stat.zscore_60d) > Z_THRESHOLD

def build_demerger_windows(conn) -> dict[str, list[tuple[str, str]]]:
    """symbol -> list of (start_inclusive, end_inclusive) windows, each covering a structural
    break's (DEMERGER or CAPITAL_REDUCTION -- both are real, accurately-labeled action types that
    share the same "no disclosed ratio" exclusion treatment, docs/phase5_event_catalogue.md
    Sec.4j) ex-date plus the following POST_DEMERGER_EXCLUSION_SESSIONS real trading sessions for
    that symbol (not calendar days)."""
    demergers = conn.execute(
        "SELECT symbol, event_date FROM corporate_actions "
        "WHERE action_type IN ('DEMERGER', 'CAPITAL_REDUCTION') ORDER BY symbol, event_date"
    ).fetchall()
    windows: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for symbol, ex_date in demergers:
        days = [r[0] for r in conn.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol=? AND series='EQ' AND event_date>=? ORDER BY event_date",
            (symbol, ex_date)).fetchall()]
        if not days:
            windows[symbol].append((ex_date, ex_date))
            continue
        end = days[min(POST_DEMERGER_EXCLUSION_SESSIONS, len(days) - 1)]
        windows[symbol].append((ex_date, end))
    return dict(windows)

def in_demerger_window(windows: dict[str, list[tuple[str, str]]], symbol: str, event_date: str) -> bool:
    for start, end in windows.get(symbol, ()):
        if start <= event_date <= end:
            return True
    return False

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    symbols = [r[0] for r in conn.execute(
        "SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ' ORDER BY symbol").fetchall()]
    print(f"Building final event catalogue (z-only, LOOSE, 60-session post-demerger exclusion) "
          f"for {len(symbols)} EQ symbols...")

    # Amendment 4 prep item 5: stitch a renamed security's symbols into one continuous history
    # (P8-010 -- this project's own symbol-string-keyed tables otherwise treat a rename as two
    # unrelated series). Missing map file falls back to no stitching, same as before this change
    # (P8-006's lesson: a real pipeline step must not be blocked on having run a refresh script
    # first) -- run scripts/build_isin_map.py to enable it.
    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}
    if not symbol_groups:
        print("No ISIN map found -- building per-symbol, unstitched (run scripts/build_isin_map.py to enable stitching)")
    renamed_groups = {tuple(sorted(g)) for g in symbol_groups.values() if len(g) > 1}
    print(f"Rename groups that will be stitched: {len(renamed_groups)}")

    demerger_windows = build_demerger_windows(conn)
    n_demergers = sum(len(w) for w in demerger_windows.values())
    print(f"Structural-break windows loaded: {n_demergers} occurrences (DEMERGER + CAPITAL_REDUCTION) "
          f"across {len(demerger_windows)} symbols.")

    matched: list[DailyStat] = []
    excluded_by_window: list[DailyStat] = []
    turnover_by_year: dict[str, list[float]] = defaultdict(list)
    total_stat_rows = 0
    distinct_days: set[str] = set()

    t0 = time.time()
    processed_groups: set[tuple[str, ...]] = set()
    for i, symbol in enumerate(symbols):
        group = tuple(sorted(symbol_groups.get(symbol, [symbol])))
        if group in processed_groups:
            continue  # already built as part of an earlier member's stitched history
        processed_groups.add(group)

        hist = build_symbol_history(conn, symbol, symbol_group=list(group))
        stats = compute_daily_stats(hist)
        total_stat_rows += len(stats)
        for s in stats:
            distinct_days.add(s.event_date)
            turnover_by_year[s.event_date[:4]].append(s.close_price_raw * s.traded_qty)
            if is_event(s):
                # s.symbol (not the outer `symbol`/group representative) -- a stitched group's
                # rows are labeled by whichever member ACTUALLY traded on that date, and the
                # demerger window must be looked up under that same real symbol.
                if in_demerger_window(demerger_windows, s.symbol, s.event_date):
                    excluded_by_window.append(s)
                else:
                    matched.append(s)
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(symbols)} symbols, {len(matched)} events so far, {time.time() - t0:.0f}s elapsed")

    print(f"\nDone: {len(matched)} events out of {total_stat_rows} daily-stat rows "
          f"across {len(symbols)} symbols, {len(distinct_days)} distinct trading days, in {time.time() - t0:.0f}s")
    print(f"Excluded by the 60-session post-demerger window: {len(excluded_by_window)} "
          f"(would otherwise have qualified as events)")

    year_terciles: dict[str, tuple[float, float]] = {}
    for year, values in turnover_by_year.items():
        values_sorted = sorted(values)
        n = len(values_sorted)
        year_terciles[year] = (values_sorted[n // 3], values_sorted[2 * n // 3])

    def cap_band(stat: DailyStat) -> str:
        lo, hi = year_terciles[stat.event_date[:4]]
        turnover = stat.close_price_raw * stat.traded_qty
        if turnover <= lo:
            return "Small"
        if turnover <= hi:
            return "Mid"
        return "Large"

    surv_cache: dict[tuple[str, str], dict] = {}
    def surv_state(symbol: str, event_date: str) -> dict:
        key = (symbol, event_date)
        if key not in surv_cache:
            surv_cache[key] = current_surveillance_state(conn, symbol, event_date)
        return surv_cache[key]

    by_year = defaultdict(int)
    by_band = defaultdict(int)
    asm_active = 0
    gsm_active = 0
    neither = 0
    gsm_gap_events = 0  # matched events that predate GSM_FLOOR -- GSM structurally unavailable

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "symbol", "event_date", "close_price_raw", "return_1d", "zscore_60d", "percentile_60d",
            "volume_ratio", "traded_qty", "delivery_pct", "delivery_pct_percentile_60d",
            "return_20d_context_only", "cap_band", "asm_stage", "gsm_stage", "gsm_available_at_the_time",
        ])
        for s in matched:
            by_year[s.event_date[:4]] += 1
            band = cap_band(s)
            by_band[band] += 1
            state = surv_state(s.symbol, s.event_date)
            asm_stage = state.get("ASM_LT") or state.get("ASM_ST")
            gsm_stage = state.get("GSM")
            gsm_available = s.event_date >= GSM_FLOOR
            if not gsm_available:
                gsm_gap_events += 1
            if gsm_stage is not None:
                gsm_active += 1
            elif asm_stage is not None:
                asm_active += 1
            else:
                neither += 1
            writer.writerow([
                s.symbol, s.event_date, s.close_price_raw, s.return_1d, s.zscore_60d, s.percentile_60d,
                s.volume_ratio, s.traded_qty, s.delivery_pct, s.delivery_pct_percentile_60d,
                s.return_20d, band, asm_stage, gsm_stage, gsm_available,
            ])

    print(f"\nPersisted {len(matched)} rows to {OUTPUT_PATH}")

    # ASM-labelled count among the EXCLUDED events -- the scarce-resource cost of this exclusion.
    excluded_asm_labelled = 0
    excluded_gsm_labelled = 0
    for s in excluded_by_window:
        state = surv_state(s.symbol, s.event_date)
        if state.get("GSM") is not None:
            excluded_gsm_labelled += 1
        elif state.get("ASM_LT") is not None or state.get("ASM_ST") is not None:
            excluded_asm_labelled += 1

    print("\n" + "=" * 80)
    print("FINAL EVENT CATALOGUE -- LOOSE, z-score only (|z|>2.5, vol>2.0x), 60-session post-demerger exclusion")
    print("=" * 80)
    print(f"Total events (final, after exclusion): {len(matched)}")
    print(f"Events excluded by the 60-session post-demerger window: {len(excluded_by_window)}")
    print(f"By year: {dict(sorted(by_year.items()))}")
    print(f"By market-cap-proxy band: {dict(by_band)}")
    print(f"\nSurveillance status at the time (mechanism-level, GSM checked first since GSM is the")
    print(f"stricter/rarer label -- an event with both active is counted under GSM):")
    print(f"  GSM active:      {gsm_active}")
    print(f"  ASM active (no GSM): {asm_active}")
    print(f"  Neither (NOT_FLAGGED): {neither}")
    print(f"  Total labelled (ASM+GSM) after exclusion: {asm_active + gsm_active} / {len(matched)} "
          f"({100*(asm_active+gsm_active)/len(matched):.2f}%)")
    print(f"\nGSM coverage reality:")
    print(f"  Events before {GSM_FLOOR} (GSM structurally unavailable): {gsm_gap_events} / {len(matched)} "
          f"({100*gsm_gap_events/len(matched):.1f}%)")
    print(f"  Events with GSM specifically active: {gsm_active} / {len(matched)} ({100*gsm_active/len(matched):.1f}%)")
    print(f"  Events with NO GSM coverage at all (gap OR simply not GSM-flagged): "
          f"{len(matched) - gsm_active} / {len(matched)} ({100*(len(matched)-gsm_active)/len(matched):.1f}%)")
    print(f"\nOf the {len(excluded_by_window)} events excluded by the post-demerger window:")
    print(f"  ASM-labelled: {excluded_asm_labelled}")
    print(f"  GSM-labelled: {excluded_gsm_labelled}")
    print(f"  Unlabelled:   {len(excluded_by_window) - excluded_asm_labelled - excluded_gsm_labelled}")

    conn.close()

if __name__ == "__main__":
    main()
