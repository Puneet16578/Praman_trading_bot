"""P8-007 corrections, item 4: measure (do not apply) an equity-only universe rule via ISIN
prefix, per instruction. INE = company equity, INF = mutual-fund/ETF unit (confirmed directly:
GROWWGOLD/GROWWSLVR/SILVERBEES/NIFTYBEES all INF; AJANTPHARM/RELIANCE/TCS/ZEEL all INE) --
preferred over the live /api/etf list because it also resolves renamed/delisted ETFs that list
misses (e.g. HDFCNIFETF).

Source: data/raw/nse_symbol_isin_current.json, built from a real NSE UDiFF bhavcopy
(jugaad_data.nse.bhavcopy_save -- a DIFFERENT file from this project's own ingestion, which uses
full_bhavcopy_save/sec_bhavdata_full and does NOT carry ISIN, confirmed directly). A single current
snapshot -- symbols delisted before today will not resolve; that resolution rate is reported
directly, not assumed.
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TRAIN_CUTOFF = "2026-01-01"
ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
TRAIN_CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"


def main() -> None:
    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = list(csv.DictReader(f))
    all_symbols = set(r["symbol"] for r in catalogue)

    resolved = {s: isin_map[s] for s in all_symbols if s in isin_map}
    unresolved = all_symbols - set(resolved)
    print(f"Distinct catalogued symbols: {len(all_symbols)}")
    print(f"Resolved to an ISIN: {len(resolved)} ({100*len(resolved)/len(all_symbols):.2f}%)")
    print(f"Unresolved (not in today's live bhavcopy -- likely delisted/renamed): {len(unresolved)} "
          f"({100*len(unresolved)/len(all_symbols):.2f}%)")

    fund_unit_symbols = {s for s, isin in resolved.items() if isin.startswith("INF")}
    equity_symbols = {s for s, isin in resolved.items() if isin.startswith("INE")}
    other_symbols = set(resolved) - fund_unit_symbols - equity_symbols
    print(f"\nOf resolved: INE (equity)={len(equity_symbols)}  INF (fund unit)={len(fund_unit_symbols)}  "
          f"other prefix={len(other_symbols)} ({[isin_map[s] for s in list(other_symbols)[:5]]})")

    train_events = [r for r in catalogue if r["event_date"] < TRAIN_CUTOFF]
    holdout_events = [r for r in catalogue if r["event_date"] >= TRAIN_CUTOFF]

    for label, events in [("TRAIN", train_events), ("HOLD-OUT", holdout_events)]:
        removed = [e for e in events if e["symbol"] in fund_unit_symbols]
        print(f"\n{label}: {len(events)} events; equity-only rule (INF-ISIN removal) would remove "
              f"{len(removed)} ({100*len(removed)/len(events):.2f}%)")

    disclosure_tier: dict[tuple[str, str], str] = {}
    for path in (TRAIN_CLASS_PATH, HOLDOUT_CLASS_PATH):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                disclosure_tier[(row["symbol"], row["event_date"])] = row["disclosure_tier"]

    uc_total = sum(1 for t in disclosure_tier.values() if t == "UNKNOWN_COVERAGE")
    uc_fund_unit = sum(1 for (sym, ed), t in disclosure_tier.items()
                        if t == "UNKNOWN_COVERAGE" and sym in fund_unit_symbols)
    uc_remaining = uc_total - uc_fund_unit
    print(f"\nUNKNOWN_COVERAGE total: {uc_total}")
    print(f"UNKNOWN_COVERAGE that is INF-ISIN-confirmed fund unit: {uc_fund_unit} ({100*uc_fund_unit/uc_total:.2f}%)")
    print(f"UNKNOWN_COVERAGE remaining after equity-only removal: {uc_remaining} "
          f"({100*uc_remaining/uc_total:.2f}% of original, "
          f"{100*uc_remaining/(len(disclosure_tier)-uc_fund_unit):.2f}% of remaining catalogue)")


if __name__ == "__main__":
    main()
