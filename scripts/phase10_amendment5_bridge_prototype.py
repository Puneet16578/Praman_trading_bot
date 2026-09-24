"""Amendment 5 prep, item 2: prototype the EQ/BE/BZ bridge -- outcome only, no pipeline change.
Confirmed root cause (item 1(b)): P8-012's extend_with_series appends BE/BZ rows STRICTLY AFTER a
symbol's own LAST-EVER EQ date, so a temporary EQ -> BE -> EQ trade-for-trade stint (the common
real shape for a surveillance-affected micro-cap) is invisible -- the merged calendar has a GAP
during the stint, and if a target_date lands inside that gap, the staleness cap fires using a
stale pre-stint EQ close even though the security kept trading (under BE) and even resumed EQ
afterward. Confirmed directly: 92.37% of TRAIN events missing due to the staleness cap have a
BE/BZ close within the 10-session window the current code simply never looks at.

Bridge: the last available close on or before target_date, taken from the UNION of EQ/BE/BZ rows
for the security, with EQ preferred on any date more than one series has a close (the ambiguous-
overlap case P8-012 deliberately left alone; here it is resolved explicitly, not avoided, since
the whole point is now to bridge across a series change rather than only extend past its end).
"""
from __future__ import annotations
import bisect
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
TRAIN_CUTOFF = "2026-01-01"
HORIZON = 90
STALENESS_CAP = 10
BRIDGE_SERIES = ("EQ", "BE", "BZ")


def main() -> None:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        global_days = [r["date"] for r in csv.DictReader(f)]
    market_index = {}
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            market_index[r["date"]] = float(r["index_level"])

    cap_band = {}
    with open(CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cap_band[(row["symbol"], row["event_date"])] = row["cap_band"]

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        events = list(csv.DictReader(f))
    print(f"Total catalogued events: {len(events)}")

    symbol_groups = build_symbol_groups(load_isin_map(ISIN_MAP_PATH)) if ISIN_MAP_PATH.exists() else {}

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        by_symbol.setdefault(e["symbol"], []).append(e)

    def build_bridged(symbol_list):
        placeholders = ",".join("?" * len(symbol_list))
        rows = conn.execute(
            f"SELECT symbol, event_date, series, close_price FROM bhavcopy "
            f"WHERE series IN ('EQ','BE','BZ') AND symbol IN ({placeholders}) "
            f"ORDER BY event_date", tuple(symbol_list),
        ).fetchall()
        # EQ preferred on any date with multiple series
        by_date: dict[str, tuple[str, float]] = {}  # date -> (series, close)
        priority = {"EQ": 0, "BE": 1, "BZ": 2}
        for r in rows:
            d = r["event_date"]
            cur = by_date.get(d)
            if cur is None or priority[r["series"]] < priority[cur[0]]:
                by_date[d] = (r["series"], r["close_price"])
        dates = sorted(by_date.keys())
        closes = [by_date[d][1] for d in dates]
        return dates, closes

    results = {"TRAIN": [0, 0], "HOLD-OUT": [0, 0]}
    band_results = {"TRAIN": {}, "HOLD-OUT": {}}
    n_syms = 0
    t0_symbols = len(by_symbol)
    for symbol, symbol_events in by_symbol.items():
        n_syms += 1
        group = symbol_groups.get(symbol, [symbol])
        dates, closes = build_bridged(group)
        for e in symbol_events:
            ed = e["event_date"]
            pop = "TRAIN" if ed < TRAIN_CUTOFF else "HOLD-OUT"
            idx = bisect.bisect_left(global_days, ed)
            if not (idx < len(global_days) and global_days[idx] == ed):
                continue
            target_idx = idx + HORIZON
            if target_idx >= len(global_days):
                continue  # not fully elapsed
            target_date = global_days[target_idx]

            didx = bisect.bisect_left(dates, ed)
            if didx >= len(dates) or dates[didx] != ed:
                continue  # event_date itself not in bridged calendar (shouldn't normally happen)

            last_didx = bisect.bisect_right(dates, target_date) - 1
            if last_didx < didx:
                last_didx = didx
            last_date = dates[last_didx]
            last_g_idx = bisect.bisect_left(global_days, last_date)
            staleness = target_idx - last_g_idx

            band = cap_band.get((symbol, ed), "UNKNOWN")
            band_results[pop].setdefault(band, [0, 0])
            band_results[pop][band][0] += 1
            results[pop][0] += 1
            if staleness > STALENESS_CAP:
                results[pop][1] += 1
                band_results[pop][band][1] += 1
        if n_syms % 500 == 0:
            print(f"  ...{n_syms}/{t0_symbols} symbols")

    conn.close()

    for pop in ("TRAIN", "HOLD-OUT"):
        n, m = results[pop]
        rate = 100 * m / n if n else float("nan")
        print(f"\n=== {pop} (bridged EQ/BE/BZ) ===")
        print(f"n={n}  missing={m}  rate={rate:.3f}%")
        print("By cap_band:")
        for band in ("Micro", "Small", "Mid", "Large", "Mega"):
            bn, bm = band_results[pop].get(band, [0, 0])
            brate = 100 * bm / bn if bn else float("nan")
            print(f"  {band:8s} n={bn:6d}  missing={bm:5d}  rate={brate:.3f}%")

    n_tr, m_tr = results["TRAIN"]
    n_ho, m_ho = results["HOLD-OUT"]
    rate_tr = 100 * m_tr / n_tr
    rate_ho = 100 * m_ho / n_ho
    print(f"\nGap: {abs(rate_tr - rate_ho):.3f}pp")

    micro_tr = 100 * band_results["TRAIN"]["Micro"][1] / band_results["TRAIN"]["Micro"][0]
    mega_tr = 100 * band_results["TRAIN"]["Mega"][1] / band_results["TRAIN"]["Mega"][0]
    print(f"TRAIN Micro-minus-Mega gap (bridged): {micro_tr - mega_tr:.3f}pp")
    print(f"(for reference: current P8-012-only definition's TRAIN Micro-minus-Mega gap: 14.099pp)")
    print(f"(for reference: current P8-012-only definition's TRAIN overall missing rate: 6.838%)")


if __name__ == "__main__":
    main()
