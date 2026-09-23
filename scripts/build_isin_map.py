"""Builds/refreshes data/raw/nse_symbol_isin_current.json (P8-010's identity-resolution input) --
the reproducible replacement for the ad hoc multi-snapshot fetch this file was originally built
from during the P8-007 corrections session. A single current-day snapshot only resolves symbols
still listed today; these dates span both the legacy (pre-mid-2024) and UDiFF (current) CM
bhavcopy schemas so a renamed or delisted symbol is still resolved from whichever era it traded in.

Not run automatically by weekly_ingest.py -- this is a periodic refresh (new renames/listings
appear over time), not a per-run dependency. `scripts/weekly_ingest.py`'s corporate_actions step
falls back to no resolution if this file doesn't exist yet, so a fresh clone is never blocked on
having run this first (P8-006's lesson: a real ingestion path must not silently depend on a file
nothing in the repo can reproduce).
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.nse_market_data.isin_mapping import fetch_isin_snapshot, merge_isin_snapshots

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"

# Chronological -- merge_isin_snapshots lets a later date win on conflict (a symbol legitimately
# reused for a different company). Legacy schema (SYMBOL/SERIES) through 2023-06-15; UDiFF
# (TckrSymb/SctySrs) from 2025-02-04 -- the 2024-01-15 date was tried during the original build and
# failed with a 404 (the format-transition gap) and is skipped here for the same reason.
SNAPSHOT_DATES = [
    date(2019, 11, 15), date(2020, 6, 15), date(2021, 2, 17), date(2021, 6, 15),
    date(2021, 7, 22), date(2022, 6, 15), date(2023, 6, 15),
    date(2025, 2, 4), date(2025, 6, 16), date(2025, 10, 13),
]


def main() -> None:
    snapshots = []
    snapshots.append(fetch_isin_snapshot(date.today()))
    print(f"  {date.today().isoformat()} (today): {len(snapshots[-1])} symbols")
    for d in SNAPSHOT_DATES:
        try:
            snap = fetch_isin_snapshot(d)
            print(f"  {d.isoformat()}: {len(snap)} symbols")
            snapshots.append(snap)
        except Exception as exc:
            print(f"  {d.isoformat()}: FAILED ({exc}) -- skipped, not fatal to the overall map")

    merged = merge_isin_snapshots(snapshots)
    print(f"\nMerged map: {len(merged)} distinct symbols")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(merged, indent=0, sort_keys=True), encoding="utf-8")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
