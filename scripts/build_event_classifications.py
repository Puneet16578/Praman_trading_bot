"""Phase 7b production run: classify every catalogued event (GROUNDED / PARTIALLY_GROUNDED /
UNEXPLAINED / UNEXPLAINED_ISOLATED / UNEXPLAINED_UNKNOWN_COVERAGE) via
src/classification/event_classifier.py, with every required signal field attached regardless of
class. Thresholds (per-band momentum medians, isolated co-movement cutoff) are computed fresh from
the real data here, exactly as scripts/design_classification_rules.py validated them -- this
script applies the same approved rules, it does not re-derive or tune them.

Output: data/processed/event_classifications.csv, one row per usable catalogued event.
"""
from __future__ import annotations
import bisect
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
from src.signals.disclosure_classification import classify_disclosure_window
from src.signals.event_catalogue import build_symbol_history
from src.signals.surveillance_state import build_surveillance_timeline
from src.classification.event_classifier import (
    ClassificationThresholds, EventSignals, classify_event, momentum_is_high,
    sessions_to_subsequent_flag, PROVENANCE_NOTE,
)

DISCLOSURE_WINDOW_SESSIONS = 10
ISOLATED_COMOVEMENT_THRESHOLD = 36  # real p25 of same_date_event_count, all 75,300 events -- see
                                     # docs/phase7b_classification_design.md

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLUSTERING_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "clustering.csv"
CLOSE_TO_CLOSE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "close_to_close_60d.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_classifications.csv"
THRESHOLDS_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "classification_thresholds.json"
ISIN_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"

def load_catalogue() -> list[dict]:
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_comovement_counts() -> dict[tuple[str, str], int]:
    counts = {}
    with open(CLUSTERING_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            counts[(row["symbol"], row["event_date"])] = int(row["same_date_event_count"])
    return counts

def load_close_to_close() -> dict[tuple[str, str], float | None]:
    out = {}
    with open(CLOSE_TO_CLOSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = row["close_to_close_60d"]
            out[(row["symbol"], row["event_date"])] = float(v) if v not in ("", "None") else None
    return out

def compute_quintile_bands(rows: list[dict]) -> dict[tuple[str, str], str]:
    turnover_by_year = defaultdict(list)
    for r in rows:
        t = float(r["close_price_raw"]) * float(r["traded_qty"])
        turnover_by_year[r["event_date"][:4]].append(t)
    cuts = {}
    for year, vals in turnover_by_year.items():
        vals = sorted(vals)
        n = len(vals)
        cuts[year] = [vals[int(n * p)] for p in (0.2, 0.4, 0.6, 0.8)]
    names = ["Micro", "Small", "Mid", "Large", "Mega"]
    bands = {}
    for r in rows:
        t = float(r["close_price_raw"]) * float(r["traded_qty"])
        c = cuts[r["event_date"][:4]]
        idx = sum(1 for x in c if t > x)
        bands[(r["symbol"], r["event_date"])] = names[idx]
    return bands

def compute_band_medians(rows: list[dict], bands: dict[tuple[str, str], str]) -> dict[str, float]:
    r20_by_band = defaultdict(list)
    for r in rows:
        v = r["return_20d_context_only"]
        if v in ("", "None"):
            continue
        band = bands[(r["symbol"], r["event_date"])]
        r20_by_band[band].append(abs(float(v)))
    return {b: float(np.median(vals)) for b, vals in r20_by_band.items()}

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    rows = load_catalogue()
    print(f"Loaded {len(rows)} catalogued events")
    bands = compute_quintile_bands(rows)
    band_medians = compute_band_medians(rows, bands)
    thresholds = ClassificationThresholds(
        band_median_abs_return_20d=band_medians,
        isolated_comovement_threshold=ISOLATED_COMOVEMENT_THRESHOLD,
    )
    print("Per-band median abs(return_20d):")
    for b, m in sorted(band_medians.items()):
        print(f"  {b}: {m:.4f}")

    comovement = load_comovement_counts()
    close_to_close = load_close_to_close()
    print(f"Loaded co-movement counts for {len(comovement)} events, close-to-close for {len(close_to_close)} events")

    fetched_symbols = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM corporate_announcements").fetchall()}

    # Amendment 4 prep item 5: stitch a renamed security's symbols (P8-010), consistent with the
    # catalogue/outcome-label rebuild. Missing map file falls back to no stitching (P8-006's lesson).
    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}

    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_symbol[r["symbol"]].append(r)

    out_rows: list[dict] = []
    t0 = time.time()
    n_symbols = 0
    for symbol, symbol_events in by_symbol.items():
        n_symbols += 1
        has_coverage = symbol in fetched_symbols
        timeline = build_surveillance_timeline(conn, symbol)
        hist = build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]))
        days = hist.trading_days

        ann_rows = []
        ann_dates: list[str] = []
        rows_by_date: dict[str, list[dict]] = defaultdict(list)
        if has_coverage:
            ann_rows = conn.execute(
                "SELECT event_date, category FROM corporate_announcements WHERE symbol=? ORDER BY event_date",
                (symbol,),
            ).fetchall()
            ann_dates = sorted(r[0] for r in ann_rows)
            for event_date_, category in ann_rows:
                rows_by_date[event_date_].append({"category": category})

        for e in symbol_events:
            event_date = e["event_date"]
            band = bands[(symbol, event_date)]
            r20_str = e["return_20d_context_only"]
            abs_r20 = abs(float(r20_str)) if r20_str not in ("", "None") else None
            momentum_high = momentum_is_high(abs_r20, band, thresholds)

            same_date_count = comovement.get((symbol, event_date))
            c2c = close_to_close.get((symbol, event_date))

            asm_stage = e["asm_stage"] or None
            gsm_stage = e["gsm_stage"] or None
            gap, gap_note = sessions_to_subsequent_flag(
                timeline=timeline, event_date=event_date, trading_days=days,
                asm_stage_as_of=asm_stage, gsm_stage_as_of=gsm_stage,
            )

            if not has_coverage:
                tier = "UNKNOWN_COVERAGE"
            else:
                idx = bisect.bisect_left(days, event_date)
                if idx < DISCLOSURE_WINDOW_SESSIONS:
                    window_rows: list[dict] = []
                else:
                    window_start = days[idx - DISCLOSURE_WINDOW_SESSIONS]
                    lo = bisect.bisect_left(ann_dates, window_start)
                    hi = bisect.bisect_left(ann_dates, event_date)
                    window_rows = []
                    for d in ann_dates[lo:hi]:
                        window_rows.extend(rows_by_date.get(d, []))
                tier = classify_disclosure_window(window_rows)

            cls, is_isolated = classify_event(
                disclosure_tier=tier, has_coverage=has_coverage, momentum_high=momentum_high,
                same_date_event_count=same_date_count, thresholds=thresholds,
            )

            signals = EventSignals(
                symbol=symbol, event_date=event_date, classification=cls, disclosure_tier=tier,
                momentum_high=momentum_high, is_isolated=is_isolated, cap_band=band,
                volume_ratio=(float(e["volume_ratio"]) if e["volume_ratio"] not in ("", "None") else None),
                delivery_pct=(float(e["delivery_pct"]) if e["delivery_pct"] not in ("", "None") else None),
                delivery_pct_percentile_60d=(float(e["delivery_pct_percentile_60d"]) if e["delivery_pct_percentile_60d"] not in ("", "None") else None),
                zscore_60d=(float(e["zscore_60d"]) if e["zscore_60d"] not in ("", "None") else None),
                close_to_close_60d=c2c, same_date_event_count=same_date_count,
                asm_stage_as_of=asm_stage, gsm_stage_as_of=gsm_stage,
                sessions_to_subsequent_flag=gap, subsequent_flag_note=gap_note,
            )
            out_rows.append(vars(signals))

        if n_symbols % 500 == 0:
            print(f"  ...{n_symbols}/{len(by_symbol)} symbols, {time.time() - t0:.0f}s elapsed")

    print(f"Done in {time.time() - t0:.0f}s. {len(out_rows)} events classified across {n_symbols} symbols.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Persisted {len(out_rows)} rows to {OUTPUT_PATH}")

    with open(THRESHOLDS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "band_median_abs_return_20d": band_medians,
            "isolated_comovement_threshold": ISOLATED_COMOVEMENT_THRESHOLD,
        }, f, indent=2)
    print(f"Persisted thresholds to {THRESHOLDS_OUTPUT_PATH} (single source of truth for the agent layer's live classification)")
    print(f"\nProvenance note (for report rendering): {PROVENANCE_NOTE}")

    from collections import Counter
    counts = Counter(r["classification"] for r in out_rows)
    total = sum(counts.values())
    print(f"\nFinal class distribution ({total} events):")
    for cls, n in counts.most_common():
        print(f"  {cls}: {n} ({100*n/total:.1f}%)")

    conn.close()

if __name__ == "__main__":
    main()
