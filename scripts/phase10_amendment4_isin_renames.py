"""Amendment 4 prep, Part 1 items 1-2: find every ISIN mapping to more than one symbol (a
ticker rename this project's symbol-string-based joins cannot see across), report each
rename's actions that would be orphaned from the OLD symbol's own price history, and check
whether any of the P8-007 corrections' 52 persisting "unexplained" shape hits are explained by
one of these renames once the ISIN-sharing symbol's actions are considered too.

Read-only: reads production bhavcopy, the staged full-sweep corporate_actions
(data/processed/praman_staging_p8007_sweep.db), and the ISIN map. Writes nothing.

HEG/HEGAM (P8-010) surfaced only because the old, pre-P8-006 cache happened to predate the
rename -- a company that renamed BEFORE that cache was built would have its historical actions
filed under the NEW ticker in BOTH the old cache and the live sweep, orphaned from the OLD
ticker's price history in every source this project has, with no diff able to show it (there is
nothing to disagree about -- both sources agree on the wrong thing). This script finds those
cases directly, from the ISIN map, not from a diff.
"""
from __future__ import annotations
import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
STAGING_DB_PATH = ROOT / "data" / "processed" / "praman_staging_p8007_sweep.db"
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"

TARGET_SHAPES_PCT = [-33.3, -50.0, -66.7, -75.0, -80.0, -83.3, -90.0]
TOLERANCE_PP = 2.0

# The 52 persisting unexplained hits from scripts/phase10_p8007_shape_scan_rerun.py's real
# output (docs/phase10_p8007_corrections.md Sec.5) -- reproduced here as data, not recomputed
# by shape logic, so this script checks the EXACT same 52 the corrections doc reported.
UNEXPLAINED_52 = [
    ("ADROITINFO", "2021-04-27"), ("ANKITMETAL", "2021-02-08"), ("ANTGRAPHIC", "2023-11-20"),
    ("ASAHISONG", "2025-08-18"), ("ATLANTAA", "2026-01-12"), ("COMPUSOFT", "2024-03-04"),
    ("COSMOFILMS", "2022-06-16"), ("DGCONTENT", "2022-06-21"), ("ELGIRUBCO", "2020-08-18"),
    ("ESSARSHPNG", "2022-03-29"), ("ESSENTIA", "2024-08-12"), ("FLEXITUFF", "2020-11-10"),
    ("GLOBE", "2024-04-22"), ("GODHA", "2022-06-21"), ("GODHA", "2024-05-06"),
    ("IBULHSGFIN", "2020-03-19"), ("IDEA", "2020-03-18"), ("IMPEXFERRO", "2022-09-13"),
    ("INCREDIBLE", "2022-03-29"), ("INFIBEAM", "2022-03-14"), ("JBFIND", "2022-03-29"),
    ("KANANIIND", "2020-03-04"), ("KARDA", "2021-09-13"), ("KBCGLOBAL", "2025-05-05"),
    ("KHANDSE", "2023-10-09"), ("LFIC", "2020-08-18"), ("MALUPAPER", "2024-07-15"),
    ("MCDHOLDING", "2020-03-04"), ("MINDAIND", "2022-07-07"), ("NXTDIGITAL", "2022-12-06"),
    ("OMAXAUTO", "2025-11-03"), ("PANACHE", "2023-05-23"), ("PREMEXPLN", "2024-09-23"),
    ("RNBDENIMS", "2026-05-19"), ("RTNPOWER", "2021-10-12"), ("SELMC", "2023-07-03"),
    ("SELMC", "2024-02-26"), ("SGL", "2024-12-02"), ("SHANTI", "2024-08-26"),
    ("SHANTI", "2025-09-09"), ("SKIL", "2021-07-20"), ("SONAMLTD", "2025-02-03"),
    ("SRPL", "2024-08-26"), ("SUMEETINDS", "2024-07-19"), ("SURANASOL", "2020-03-04"),
    ("TICL", "2026-02-16"), ("TIDEWATER", "2021-10-18"), ("TIPSINDLTD", "2023-04-21"),
    ("TNTELE", "2025-10-06"), ("VIJIFIN", "2025-11-24"), ("VINNY", "2025-08-04"),
    ("ZEEL", "2024-01-23"),
]


def load_isin_groups() -> dict[str, list[str]]:
    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))
    by_isin: dict[str, list[str]] = defaultdict(list)
    for sym, isin in isin_map.items():
        by_isin[isin].append(sym)
    return {isin: syms for isin, syms in by_isin.items() if len(syms) > 1}


def bhavcopy_date_ranges(conn, symbols: set[str]) -> dict[str, tuple[str, str, int]]:
    """symbol -> (first_date, last_date, n_rows), EQ series only, only symbols with >=1 row."""
    placeholders = ",".join("?" * len(symbols))
    rows = conn.execute(
        f"SELECT symbol, MIN(event_date) lo, MAX(event_date) hi, COUNT(DISTINCT event_date) n "
        f"FROM bhavcopy WHERE series='EQ' AND symbol IN ({placeholders}) GROUP BY symbol",
        tuple(symbols),
    ).fetchall()
    return {r["symbol"]: (r["lo"], r["hi"], r["n"]) for r in rows}


def main() -> None:
    settings = get_settings()
    prod_conn = get_connection(settings.database_path)
    init_db(prod_conn)

    isin_groups = load_isin_groups()
    all_symbols_in_groups = {s for syms in isin_groups.values() for s in syms}
    print(f"ISINs mapping to >1 symbol in the current map: {len(isin_groups)}")
    print(f"Distinct symbols involved: {len(all_symbols_in_groups)}")

    date_ranges = bhavcopy_date_ranges(prod_conn, all_symbols_in_groups)
    print(f"Of those, symbols with real EQ bhavcopy history: {len(date_ranges)}")

    # Keep only groups where >=2 symbols actually have real bhavcopy history -- a group where
    # only one symbol string ever traded isn't a rename this project's own price series can see.
    real_renames: dict[str, list[tuple[str, str, str, int]]] = {}
    for isin, syms in isin_groups.items():
        traded = [(s, *date_ranges[s]) for s in syms if s in date_ranges]
        if len(traded) >= 2:
            traded.sort(key=lambda t: t[1])  # sort by first_date -- chronological order
            real_renames[isin] = traded

    print(f"\n=== ITEM 1: ISINs with >=2 ACTUALLY-TRADED symbols (real renames) ===")
    print(f"Count: {len(real_renames)}")
    for isin, traded in sorted(real_renames.items(), key=lambda kv: kv[1][0][1]):
        parts = "  ->  ".join(f"{s} [{lo}..{hi}, n={n}]" for s, lo, hi, n in traded)
        print(f"  {isin}: {parts}")

    # --- orphaned actions: for each rename group, any action filed under symbol Sj whose
    # event_date falls inside a DIFFERENT symbol Si's own trading window is orphaned from Si.
    if not STAGING_DB_PATH.exists():
        print(f"\nStaging DB not found at {STAGING_DB_PATH} -- cannot check orphaned actions.")
        return
    staging_conn = get_connection(str(STAGING_DB_PATH))
    init_db(staging_conn)

    print(f"\n=== Orphaned actions (ex-date inside another same-ISIN symbol's own trading window) ===")
    orphaned_total = 0
    orphaned_by_isin = {}
    for isin, traded in real_renames.items():
        syms = [t[0] for t in traded]
        placeholders = ",".join("?" * len(syms))
        actions = staging_conn.execute(
            f"SELECT symbol, action_type, event_date, ratio_numerator, ratio_denominator, "
            f"confidence_tier, details FROM corporate_actions WHERE symbol IN ({placeholders})",
            tuple(syms),
        ).fetchall()
        hits = []
        for a in actions:
            for (sym_i, lo_i, hi_i, _n) in traded:
                if a["symbol"] == sym_i:
                    continue  # not orphaned from itself
                if lo_i <= a["event_date"] <= hi_i:
                    hits.append((sym_i, dict(a)))
        if hits:
            orphaned_by_isin[isin] = (traded, hits)
            orphaned_total += len(hits)

    print(f"Renames with at least one orphaned action: {len(orphaned_by_isin)}")
    print(f"Total orphaned actions: {orphaned_total}")
    for isin, (traded, hits) in sorted(orphaned_by_isin.items()):
        parts = ", ".join(f"{s}[{lo}..{hi}]" for s, lo, hi, n in traded)
        print(f"\n  ISIN {isin}  symbols: {parts}")
        for orphaned_from_symbol, a in hits:
            print(f"    orphaned from {orphaned_from_symbol}'s own window: filed under "
                  f"{a['symbol']} action_type={a['action_type']} event_date={a['event_date']} "
                  f"ratio={a['ratio_numerator']}:{a['ratio_denominator']} tier={a['confidence_tier']}")

    # --- item 2: check the 52 unexplained shape hits against same-ISIN symbols ---
    print(f"\n=== ITEM 2: checking the 52 unexplained shape hits against same-ISIN symbols (+/-45d) ===")
    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))
    explained_by_rename = []
    still_unexplained = []
    for symbol, event_date in UNEXPLAINED_52:
        isin = isin_map.get(symbol)
        if isin is None:
            still_unexplained.append((symbol, event_date, "no ISIN resolved"))
            continue
        siblings = [s for s in isin_groups.get(isin, [symbol]) if s != symbol]
        if not siblings:
            still_unexplained.append((symbol, event_date, f"ISIN {isin} has no other known symbol"))
            continue
        ev = date.fromisoformat(event_date)
        lo, hi = (ev - timedelta(days=45)).isoformat(), (ev + timedelta(days=45)).isoformat()
        placeholders = ",".join("?" * len(siblings))
        action = staging_conn.execute(
            f"SELECT symbol, action_type, event_date, ratio_numerator, ratio_denominator, "
            f"confidence_tier, details FROM corporate_actions WHERE symbol IN ({placeholders}) "
            f"AND event_date BETWEEN ? AND ? ORDER BY event_date LIMIT 1",
            (*siblings, lo, hi),
        ).fetchone()
        if action:
            explained_by_rename.append((symbol, event_date, dict(action)))
        else:
            still_unexplained.append((symbol, event_date, f"checked siblings {siblings} via ISIN {isin}, no action found"))

    print(f"Explained by a same-ISIN sibling symbol's action: {len(explained_by_rename)}")
    for symbol, event_date, action in explained_by_rename:
        print(f"  {symbol} {event_date}  ->  sibling {action['symbol']} {action['action_type']} "
              f"{action['event_date']} ratio={action['ratio_numerator']}:{action['ratio_denominator']} "
              f"tier={action['confidence_tier']} details={str(action.get('details'))[:50]!r}")

    print(f"\nStill unexplained after the ISIN-sibling check: {len(still_unexplained)}")
    for symbol, event_date, reason in still_unexplained:
        print(f"  {symbol:16s} {event_date}  {reason}")

    prod_conn.close()
    staging_conn.close()


if __name__ == "__main__":
    main()
