"""Phase 6: cross-stock clustering -- the one signal in the original six that is not a per-stock
price-volume statistic. Per the ensemble result (docs/phase6_signals.md Part A): three per-stock
price-volume features (volume_ratio, delivery, z-score-derived cap_band) top out around 0.61 held
out, because they measure overlapping aspects of the same phenomenon. Clustering is structurally
different -- it looks across symbols, not within one.

Mechanism this operationalizes: an operator running several names at once produces same-date
co-movement among symbols that are NOT otherwise related (no shared sector/index history);
genuine sector- or market-wide news produces co-movement among symbols that ARE otherwise related.
This project has never ingested sector/index membership data (a real gap, recorded in the phase
doc), so "related" is approximated the only way available from data already in the store:
historical return correlation. Two symbols that have historically moved together are treated as
"related"; a cluster of same-date co-movers with LOW historical correlation to the event symbol is
the more distinctive, harder-to-explain-by-coincidence pattern.

Three features per event, all as-of correct (same-date co-movers and their identities are known
the moment the event itself is known; historical correlation uses only trading days strictly
before the event date):
  - same_date_event_count: how many OTHER catalogued events share this event's date
  - same_date_same_band_count: the same, restricted to symbols in the same cap_band that day
  - max_comover_correlation / mean_comover_correlation: correlation of the event symbol's own
    prior daily returns (up to 250 trading days before the event, capped for cost) against each
    same-date co-mover's, over their prior overlapping history -- summarized as the max and mean
    across co-movers (capped at 30 co-movers per event, chosen deterministically -- alphabetical
    by symbol -- for events on unusually busy dates, so a single 497-co-mover day does not dominate
    total runtime; the raw count features are unaffected by this cap, only the correlation summary).
"""
from __future__ import annotations
import bisect
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
from src.signals.event_catalogue import FAR_FUTURE_AS_OF, _return, build_symbol_history

CORR_LOOKBACK = 250        # trading sessions of prior history used for the correlation proxy
MAX_COMOVERS_FOR_CORR = 30 # cap per event, to bound cost on unusually busy dates

INPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "clustering.csv"
ISIN_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nse_symbol_isin_current.json"

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    with open(INPUT_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Loaded {len(events)} catalogued events")

    by_date: dict[str, list[str]] = defaultdict(list)
    band_by_key: dict[tuple, str] = {}
    for e in events:
        by_date[e["event_date"]].append(e["symbol"])
        band_by_key[(e["symbol"], e["event_date"])] = e["cap_band"]

    symbols = sorted(set(e["symbol"] for e in events))
    print(f"{len(symbols)} distinct symbols, {len(by_date)} distinct event dates")

    # Amendment 4 prep item 5: stitch a renamed security's symbols (P8-010) so a lookback window
    # crossing a rename isn't starved of real prior trading days. Missing map file falls back to
    # no stitching (P8-006's lesson -- not a hard dependency).
    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}

    # Precompute, once per symbol, a date-indexed array of daily adjusted returns (prior-history
    # only usage enforced later by index slicing, not by this build step).
    print("Building per-symbol return series...")
    t0 = time.time()
    hist_cache = {}
    return_series: dict[str, tuple[list[str], np.ndarray]] = {}
    for i, symbol in enumerate(symbols):
        hist = build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]))
        hist_cache[symbol] = hist
        days = hist.trading_days
        rets = []
        for k in range(1, len(days)):
            r = _return(hist, days[k - 1], days[k], as_of=FAR_FUTURE_AS_OF)
            rets.append(r if r is not None else np.nan)
        return_series[symbol] = (days[1:], np.array(rets, dtype=float))
        if (i + 1) % 500 == 0:
            print(f"  ...{i + 1}/{len(symbols)} symbols, {time.time() - t0:.0f}s elapsed")
    print(f"Return series built in {time.time() - t0:.0f}s")

    def prior_window(symbol: str, event_date: str) -> np.ndarray:
        dates, rets = return_series[symbol]
        idx = bisect.bisect_left(dates, event_date)  # strictly before event_date
        start = max(0, idx - CORR_LOOKBACK)
        return rets[start:idx]

    pair_corr_cache: dict[frozenset, float] = {}

    def pair_correlation(sym_a: str, sym_b: str, event_date: str) -> float | None:
        key = frozenset({(sym_a, event_date), (sym_b, event_date)})
        if key in pair_corr_cache:
            return pair_corr_cache[key]
        dates_a, rets_a = return_series[sym_a]
        dates_b, rets_b = return_series[sym_b]
        idx_a = bisect.bisect_left(dates_a, event_date)
        idx_b = bisect.bisect_left(dates_b, event_date)
        start_a, start_b = max(0, idx_a - CORR_LOOKBACK), max(0, idx_b - CORR_LOOKBACK)
        da, ra = dates_a[start_a:idx_a], rets_a[start_a:idx_a]
        db, rb = dates_b[start_b:idx_b], rets_b[start_b:idx_b]
        common = sorted(set(da) & set(db))
        if len(common) < 20:
            pair_corr_cache[key] = None
            return None
        idx_map_a = {d: i for i, d in enumerate(da)}
        idx_map_b = {d: i for i, d in enumerate(db)}
        va = np.array([ra[idx_map_a[d]] for d in common])
        vb = np.array([rb[idx_map_b[d]] for d in common])
        mask = ~(np.isnan(va) | np.isnan(vb))
        if mask.sum() < 20 or np.std(va[mask]) == 0 or np.std(vb[mask]) == 0:
            pair_corr_cache[key] = None
            return None
        corr = float(np.corrcoef(va[mask], vb[mask])[0, 1])
        pair_corr_cache[key] = corr
        return corr

    print("\nComputing clustering features per event...")
    out_rows = []
    t0 = time.time()
    for i, e in enumerate(events):
        symbol, event_date = e["symbol"], e["event_date"]
        comovers_all = [s for s in by_date[event_date] if s != symbol]
        same_date_event_count = len(comovers_all)
        band = e["cap_band"]
        same_band_comovers = [s for s in comovers_all if band_by_key.get((s, event_date)) == band]
        same_date_same_band_count = len(same_band_comovers)

        sample = sorted(comovers_all)[:MAX_COMOVERS_FOR_CORR]
        corrs = [c for c in (pair_correlation(symbol, s, event_date) for s in sample) if c is not None]
        max_corr = max(corrs) if corrs else None
        mean_corr = float(np.mean(corrs)) if corrs else None

        out_rows.append({
            "symbol": symbol, "event_date": event_date,
            "same_date_event_count": same_date_event_count,
            "same_date_same_band_count": same_date_same_band_count,
            "max_comover_correlation": max_corr,
            "mean_comover_correlation": mean_corr,
            "n_comovers_sampled": len(sample),
        })
        if (i + 1) % 10000 == 0:
            print(f"  ...{i + 1}/{len(events)} events, {time.time() - t0:.0f}s elapsed, "
                  f"{len(pair_corr_cache)} pair-correlations cached")

    print(f"Done in {time.time() - t0:.0f}s. {len(pair_corr_cache)} unique pair-correlations computed.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Persisted {len(out_rows)} rows to {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
