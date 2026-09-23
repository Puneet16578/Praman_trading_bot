"""P8-007 corrections, item 5: re-run the split/bonus shape scan
(scripts/phase10_scan_split_bonus_shapes.py) using (1) the staged, corrected corporate actions
(items 1-3: full live sweep, fail-closed exclusion markers, fixed Bonus- regex) instead of
production, and (2) the equity-only population from item 4 (ISIN prefix "INE"; symbols resolving
to "INF" -- fund units -- excluded, since disclosure-tier classification and this project's
bonus/split adjustment logic both assume a company, not a fund unit, is disclosing).

Read-only against both the staging DB and the ISIN map; does not touch production or re-run item
4's rule for real. Reports three buckets per hit, not the original two, because item 2's fix adds
a real third case the original scan could not distinguish:
  - explained_by_ratio: a BONUS/SPLIT with a real, trusted ratio nearby -- adjustment should apply
  - explained_by_exclusion_marker: a DEMERGER/CAPITAL_REDUCTION/RIGHTS/RATIO_CONFLICT nearby -- a
    real corporate action happened, but no ratio is trusted enough to adjust by (this is the bucket
    UNIVASTU now falls into, instead of appearing unexplained)
  - unexplained: nothing nearby in the corrected staging data either -- a genuine candidate for a
    still-missing action, or a real move with no corporate action behind it at all

Expectation stated going in (per instruction): the 61 original "no action found" rows should
mostly persist as genuine moves under the corrected data; anything NEW appearing here (a hit that
was NOT in the original 96) would itself be another gap, and is reported as such if found.
"""
from __future__ import annotations
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db

TOLERANCE_PP = 2.0
TARGET_SHAPES_PCT = [-33.3, -50.0, -66.7, -75.0, -80.0, -83.3, -90.0]

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
STAGING_DB_PATH = ROOT / "data" / "processed" / "praman_staging_p8007_sweep.db"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"

RATIO_TYPES = ("BONUS", "SPLIT")
EXCLUSION_TYPES = ("DEMERGER", "CAPITAL_REDUCTION", "RIGHTS", "RATIO_CONFLICT")


def matches_target_shape(return_1d_pct: float) -> float | None:
    for shape in TARGET_SHAPES_PCT:
        if abs(return_1d_pct - shape) <= TOLERANCE_PP:
            return shape
    return None


def find_nearby_action(conn, symbol: str, event_date: str, action_types: tuple[str, ...],
                        window_days: int = 10) -> dict | None:
    ev = date.fromisoformat(event_date)
    lo = (ev - timedelta(days=window_days)).isoformat()
    hi = (ev + timedelta(days=window_days)).isoformat()
    placeholders = ",".join("?" * len(action_types))
    row = conn.execute(
        f"SELECT event_date, action_type, ratio_numerator, ratio_denominator, knowledge_date, "
        f"confidence_tier, details FROM corporate_actions WHERE symbol=? AND action_type IN "
        f"({placeholders}) AND event_date BETWEEN ? AND ? ORDER BY event_date LIMIT 1",
        (symbol, *action_types, lo, hi),
    ).fetchone()
    return dict(row) if row else None


def main() -> None:
    if not STAGING_DB_PATH.exists():
        print(f"Staging DB not found at {STAGING_DB_PATH} -- run "
              f"scripts/phase10_p8007_full_sweep_staging.py first.")
        return

    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))
    fund_unit_symbols = {s for s, isin in isin_map.items() if isin.startswith("INF")}

    conn = get_connection(str(STAGING_DB_PATH))
    init_db(conn)

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = list(csv.DictReader(f))

    excluded_as_fund_unit = 0
    explained_by_ratio, explained_by_exclusion, unexplained = [], [], []

    for row in catalogue:
        symbol = row["symbol"]
        if symbol in fund_unit_symbols:
            excluded_as_fund_unit += 1
            continue
        r1 = row["return_1d"]
        if r1 in ("", "None"):
            continue
        pct = float(r1) * 100
        shape = matches_target_shape(pct)
        if shape is None:
            continue

        ratio_action = find_nearby_action(conn, symbol, row["event_date"], RATIO_TYPES)
        if ratio_action is not None:
            explained_by_ratio.append({"symbol": symbol, "event_date": row["event_date"],
                                        "return_1d_pct": pct, "matched_shape_pct": shape,
                                        "action": ratio_action})
            continue
        exclusion_action = find_nearby_action(conn, symbol, row["event_date"], EXCLUSION_TYPES)
        if exclusion_action is not None:
            explained_by_exclusion.append({"symbol": symbol, "event_date": row["event_date"],
                                            "return_1d_pct": pct, "matched_shape_pct": shape,
                                            "action": exclusion_action})
            continue
        unexplained.append({"symbol": symbol, "event_date": row["event_date"],
                             "return_1d_pct": pct, "matched_shape_pct": shape})

    conn.close()

    total_hits = len(explained_by_ratio) + len(explained_by_exclusion) + len(unexplained)
    print(f"Catalogued rows excluded as fund-unit (INF-ISIN, equity-only rule): {excluded_as_fund_unit}")
    print(f"\nTotal shape-scan hits (equity-only population, staged corrected actions): {total_hits}")
    print(f"  Explained by a real BONUS/SPLIT ratio nearby: {len(explained_by_ratio)}")
    print(f"  Explained by an exclusion marker nearby (DEMERGER/CAPITAL_REDUCTION/RIGHTS/"
          f"RATIO_CONFLICT -- real action, no trusted ratio): {len(explained_by_exclusion)}")
    print(f"  UNEXPLAINED (nothing nearby even in the corrected staging data): {len(unexplained)}")

    univastu = [h for h in explained_by_exclusion if h["symbol"] == "UNIVASTU"]
    print(f"\nUNIVASTU hits now explained by an exclusion marker: {len(univastu)}")
    for h in univastu:
        print(f"  {h}")

    print(f"\n-- Explained by exclusion marker (first 30) --")
    for h in explained_by_exclusion[:30]:
        a = h["action"]
        print(f"  {h['symbol']:16s} {h['event_date']}  return_1d={h['return_1d_pct']:+.2f}%  "
              f"action={a['action_type']} tier={a['confidence_tier']} on {a['event_date']} "
              f"details={str(a.get('details'))[:50]!r}")

    print(f"\n-- UNEXPLAINED (all) --")
    for h in unexplained:
        print(f"  {h['symbol']:16s} {h['event_date']}  return_1d={h['return_1d_pct']:+.2f}%  "
              f"nearest target shape={h['matched_shape_pct']:+.1f}%")


if __name__ == "__main__":
    main()
