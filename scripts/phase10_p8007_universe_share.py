"""P8-007 scoping, item 3: ETF share of the catalogue and UNKNOWN_COVERAGE composition.

Classification is via NSE's current live /api/etf list ONLY (data/raw/nse_etf_list_current.json)
-- a LOWER BOUND on the true ETF share, stated explicitly: a symbol renamed or delisted before
today (e.g. HDFCNIFETF -> HDFCNIFTY, confirmed in docs/phase10_p8007_scoping.md) will not appear
in a current snapshot and is undercounted here, not misclassified as non-ETF with confidence.
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
ETF_LIST_PATH = ROOT / "data" / "raw" / "nse_etf_list_current.json"


def main() -> None:
    etf_list = set(json.load(open(ETF_LIST_PATH, encoding="utf-8")))

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = list(csv.DictReader(f))
    train_events = [r for r in catalogue if r["event_date"] < TRAIN_CUTOFF]
    holdout_events = [r for r in catalogue if r["event_date"] >= TRAIN_CUTOFF]

    for label, events in [("TRAIN (2019-2025)", train_events), ("HOLD-OUT (2026)", holdout_events)]:
        etf_events = [e for e in events if e["symbol"] in etf_list]
        print(f"{label}: {len(events)} events, {len(etf_events)} ETF-confirmed "
              f"({100*len(etf_events)/len(events):.2f}%), "
              f"{len(set(e['symbol'] for e in etf_events))} distinct ETF symbols")

    disclosure_tier: dict[tuple[str, str], str] = {}
    for path in (TRAIN_CLASS_PATH, HOLDOUT_CLASS_PATH):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                disclosure_tier[(row["symbol"], row["event_date"])] = row["disclosure_tier"]

    print(f"\nDisclosure tier x ETF status, full catalogue (n with a classification: {len(disclosure_tier)}):")
    from collections import defaultdict
    tier_etf_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"etf": 0, "non_etf": 0})
    for (symbol, event_date), tier in disclosure_tier.items():
        bucket = "etf" if symbol in etf_list else "non_etf"
        tier_etf_counts[tier][bucket] += 1

    for tier in sorted(tier_etf_counts):
        etf_n = tier_etf_counts[tier]["etf"]
        non_etf_n = tier_etf_counts[tier]["non_etf"]
        total = etf_n + non_etf_n
        print(f"  {tier:32s} total={total:6d}  ETF={etf_n:5d} ({100*etf_n/total:.2f}%)  non-ETF={non_etf_n:6d}")


if __name__ == "__main__":
    main()
