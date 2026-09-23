"""ISIN identity resolution -- P8-010's fix. NSE's live corporate-actions endpoint retroactively
reports a security's ENTIRE historical disclosure record under its CURRENT symbol string, not the
symbol actually in effect on each historical date (confirmed: HEG renamed to HEGAM around its
2026-09-07 demerger; every HEGAM-labeled action fetched live, including a real 2019 buyback,
carries the same ISIN, INE545A01024, that HEG traded under through 2026-09-21). This project's own
`corporate_actions`/`bhavcopy` join is symbol-string-based throughout, so a raw action's `symbol`
field cannot be trusted as-is when a rename has happened -- it must be resolved via the security's
ISIN to whichever symbol string this project's OWN bhavcopy shows was actually trading on the
action's ex-date.

This is a DIFFERENT NSE file from this project's own ingestion (`bhavcopy.py`'s
`sec_bhavdata_full`, confirmed to carry no ISIN column at all): `jugaad_data.nse.bhavcopy_save`,
the CM/UDiFF bhavcopy, under two historical schemas -- legacy (`SYMBOL,SERIES,...,ISIN`, roughly
pre-mid-2024) and UDiFF (`TckrSymb,SctySrs,...,ISIN`, current). A single snapshot only resolves
symbols still listed on that exact date; `scripts/build_isin_map.py` merges several historical
snapshots (one per schema era) into a durable map, refreshed periodically, not fetched live on
every ingestion run.
"""
from __future__ import annotations
import csv
import io
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Callable

import jugaad_data.nse as jugaad_nse


def fetch_isin_snapshot(target_date: date,
                         bhavcopy_save: Callable = jugaad_nse.bhavcopy_save) -> dict[str, str]:
    """One CM/UDiFF bhavcopy snapshot -> {symbol: isin} for that date's EQ-series rows. Handles
    both the legacy (SYMBOL/SERIES) and UDiFF (TckrSymb/SctySrs) column names -- the same ISIN
    field name, `ISIN`, is shared by both schemas. Real network call; not exercised by the
    fixture-based test suite (see `merge_isin_snapshots`/`build_symbol_groups` for the pure,
    tested logic downstream of this)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = bhavcopy_save(target_date, tmpdir)
        with open(out_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    result: dict[str, str] = {}
    for r in rows:
        symbol = (r.get("SYMBOL") or r.get("TckrSymb") or "").strip()
        series = (r.get("SERIES") or r.get("SctySrs") or "").strip()
        isin = (r.get("ISIN") or "").strip()
        if symbol and series == "EQ" and isin:
            result[symbol] = isin
    return result


def merge_isin_snapshots(snapshots: list[dict[str, str]]) -> dict[str, str]:
    """Pure merge of several {symbol: isin} snapshots into one map. Later snapshots in the list
    win on conflict (a symbol string legitimately reused for a different company after enough
    time has passed is rare but real; the most recent evidence is preferred) -- callers should
    pass snapshots in chronological order."""
    merged: dict[str, str] = {}
    for snapshot in snapshots:
        merged.update(snapshot)
    return merged


def build_symbol_groups(isin_map: dict[str, str]) -> dict[str, list[str]]:
    """symbol -> every symbol string (including itself) known to share its ISIN, i.e. its full
    rename group. A symbol with no known rename maps to a single-element list containing only
    itself. Pure function of the map -- no I/O."""
    by_isin: dict[str, list[str]] = defaultdict(list)
    for symbol, isin in isin_map.items():
        by_isin[isin].append(symbol)
    groups: dict[str, list[str]] = {}
    for symbols in by_isin.values():
        for s in symbols:
            groups[s] = list(symbols)
    return groups


def load_isin_map(path: Path) -> dict[str, str]:
    import json
    return json.loads(Path(path).read_text(encoding="utf-8"))
