"""Builds/refreshes data/raw/nse_symbol_isin_current.json (P8-010's identity-resolution input) --
the reproducible replacement for the ad hoc multi-snapshot fetch this file was originally built
from during the P8-007 corrections session. A single current-day snapshot only resolves symbols
still listed today; these dates span both the legacy (pre-mid-2024) and UDiFF (current) CM
bhavcopy schemas so a renamed or delisted symbol is still resolved from whichever era it traded in.

Run automatically by weekly_ingest.py before corporate actions. Today's HTTP 404 retains the
existing map and companion unchanged and reports WARN. The corporate_actions step
falls back to no resolution if this file doesn't exist yet, so a fresh clone is never blocked on
having run this first (P8-006's lesson: a real ingestion path must not silently depend on a file
nothing in the repo can reproduce).
"""
from __future__ import annotations
import json
import sys
from datetime import date, datetime
from pathlib import Path

from requests import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.nse_market_data.isin_mapping import fetch_isin_snapshot, merge_isin_snapshots
from shared.isin_map_metadata import IST, write_metadata

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
    today = date.today()
    try:
        snapshots.append(fetch_isin_snapshot(today))
    except HTTPError as exc:
        if exc.response is None or exc.response.status_code != 404:
            raise
        if not OUTPUT_PATH.exists():
            raise RuntimeError("Today's ISIN snapshot is unavailable and no existing map exists") from exc
        print(f"WARN {today.isoformat()}: today's ISIN snapshot returned HTTP 404; "
              "snapshot skipped, existing map and build timestamp retained.")
        return
    if not snapshots[0]:
        raise ValueError("Today's ISIN snapshot is empty; existing map retained")
    used_dates = [today.isoformat()]
    print(f"  {today.isoformat()} (today): {len(snapshots[-1])} symbols")
    for d in SNAPSHOT_DATES:
        try:
            snap = fetch_isin_snapshot(d)
            print(f"  {d.isoformat()}: {len(snap)} symbols")
            snapshots.append(snap)
            used_dates.append(d.isoformat())
        except Exception as exc:
            print(f"WARN {d.isoformat()}: snapshot failed ({type(exc).__name__}); skipped")

    merged = merge_isin_snapshots(snapshots)
    print(f"\nMerged map: {len(merged)} distinct symbols")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(merged, indent=0, sort_keys=True), encoding="utf-8")
    temporary.replace(OUTPUT_PATH)
    write_metadata(OUTPUT_PATH, built_at=datetime.now(IST).isoformat(), snapshot_dates=used_dates)
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
