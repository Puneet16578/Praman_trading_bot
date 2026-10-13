"""Builds/refreshes data/raw/nse_symbol_isin_current.json (P8-010's identity-resolution input) --
the reproducible replacement for the ad hoc multi-snapshot fetch this file was originally built
from during the P8-007 corrections session. A single current-day snapshot only resolves symbols
still listed today; these dates span both the legacy (pre-mid-2024) and UDiFF (current) CM
bhavcopy schemas so a renamed or delisted symbol is still resolved from whichever era it traded in.

Run automatically by weekly_ingest.py before corporate actions. Today's HTTP 404 retains the
existing map and companion unchanged and reports WARN. The fixed historical snapshots never change,
so each is downloaded once into `data/raw/isin_snapshots/` with a SHA-256 sidecar and read from
there, its hash checked on every use; a missing or damaged one is downloaded again (P8-060). Only
today's snapshot is fetched every night. The corporate_actions step
falls back to no resolution if this file doesn't exist yet, so a fresh clone is never blocked on
having run this first (P8-006's lesson: a real ingestion path must not silently depend on a file
nothing in the repo can reproduce).
"""
from __future__ import annotations
import csv
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import jugaad_data.nse as jugaad_nse
from requests import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.nse_market_data.isin_mapping import fetch_isin_snapshot, merge_isin_snapshots
from shared.isin_map_metadata import IST, write_metadata
from shared.market_time import market_today

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
CACHE_DIR = ROOT / "data" / "raw" / "isin_snapshots"      # with the other raw data, outside the repo
download_bhavcopy = jugaad_nse.bhavcopy_save               # (date, folder) -> path of the saved CSV

# Chronological -- merge_isin_snapshots lets a later date win on conflict (a symbol legitimately
# reused for a different company). Legacy schema (SYMBOL/SERIES) through 2023-06-15; UDiFF
# (TckrSymb/SctySrs) from 2025-02-04 -- the 2024-01-15 date was tried during the original build and
# failed with a 404 (the format-transition gap) and is skipped here for the same reason.
SNAPSHOT_DATES = [
    date(2019, 11, 15), date(2020, 6, 15), date(2021, 2, 17), date(2021, 6, 15),
    date(2021, 7, 22), date(2022, 6, 15), date(2023, 6, 15),
    date(2025, 2, 4), date(2025, 6, 16), date(2025, 10, 13),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _usable_bhavcopy(path: Path) -> bool:
    """A CM bhavcopy of either schema with at least one row: not an error page or an empty file."""
    try:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            header = set(reader.fieldnames or [])
            return "ISIN" in header and bool(header & {"SYMBOL", "TckrSymb"}) and next(reader, None) is not None
    except (OSError, UnicodeDecodeError, csv.Error):
        return False


def cached_bhavcopy_save(target_date: date, _folder: str | None = None) -> str:
    """`bhavcopy_save` for a fixed historical date, through the cache (P8-060). The cached CSV is
    used only if its bytes match the SHA-256 recorded when it was downloaded; otherwise (missing
    file or sidecar, or damaged) it is downloaded again into a fresh folder, checked, and replaced
    whole. Returns the cached file's path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"cm_{target_date.isoformat()}.csv"
    sidecar = cached.with_name(cached.name + ".sha256.json")
    problem = None
    if cached.exists() or sidecar.exists():
        try:
            recorded = json.loads(sidecar.read_text(encoding="utf-8"))["sha256"]
            if cached.exists() and _sha256(cached) == recorded:
                print(f"  {target_date.isoformat()}: cached snapshot, hash verified")
                return str(cached)
            problem = "its file is missing" if not cached.exists() else "its hash does not match"
        except (OSError, ValueError, KeyError, TypeError):
            problem = "its hash record is missing or unreadable"
        print(f"WARN {target_date.isoformat()}: cached snapshot rejected ({problem}); downloading it again")
    with tempfile.TemporaryDirectory() as folder:
        downloaded = Path(download_bhavcopy(target_date, folder))
        if not _usable_bhavcopy(downloaded):
            raise ValueError(f"download for {target_date.isoformat()} is not a usable CM bhavcopy; not cached")
        partial = cached.with_name(cached.name + ".partial")
        shutil.copyfile(downloaded, partial)
        digest = _sha256(partial)
        partial.replace(cached)
    sidecar.write_text(json.dumps(dict(snapshot_date=target_date.isoformat(), sha256=digest,
                                       bytes=cached.stat().st_size, source_file=downloaded.name,
                                       downloaded_at=datetime.now(IST).isoformat()), indent=1), encoding="utf-8")
    print(f"  {target_date.isoformat()}: downloaded and cached")
    return str(cached)


def _failure(exc: Exception) -> str:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return type(exc).__name__ + (f", HTTP {status}" if status is not None else "") + (f": {exc}" if str(exc) else "")


def main() -> None:
    snapshots = []
    today = market_today()
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
            snap = fetch_isin_snapshot(d, bhavcopy_save=cached_bhavcopy_save)
            print(f"  {d.isoformat()}: {len(snap)} symbols")
            snapshots.append(snap)
            used_dates.append(d.isoformat())
        except Exception as exc:
            print(f"WARN {d.isoformat()}: snapshot failed ({_failure(exc)}); skipped")

    # Keep historical identities if a snapshot becomes unavailable. Fresh dated
    # evidence overrides this retained fallback; today's snapshot wins last.
    retained = json.loads(OUTPUT_PATH.read_text(encoding='utf-8')) if OUTPUT_PATH.exists() else {}
    merged = merge_isin_snapshots([retained, *snapshots[1:], snapshots[0]])
    print(f"\nMerged map: {len(merged)} distinct symbols")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(merged, indent=0, sort_keys=True), encoding="utf-8")
    temporary.replace(OUTPUT_PATH)
    write_metadata(OUTPUT_PATH, built_at=datetime.now(IST).isoformat(), snapshot_dates=used_dates)
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
