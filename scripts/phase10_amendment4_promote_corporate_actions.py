"""Amendment 4 prep, Part 3: promote the full live corporate-actions sweep into PRODUCTION, with
ISIN-reconciled identity (P8-010 fix, item 4). The first write this corrections-session family of
work makes to production -- backed up first
(data/processed/praman_pre_p8007_promotion_backup_*.db).

Append-only throughout: no row is deleted or updated. Re-derives every row from the cached full
sweep (data/raw/p8007_full_sweep_cache/, the exact data already used to build the staging DB) using
the CURRENT, fixed ingestion code (fail-closed RIGHTS/RATIO_CONFLICT exclusion markers, the
corrected Bonus- regex, ISIN-based symbol resolution), and lets write_facts's own
UNIQUE-constraint-driven duplicate handling decide what's genuinely new. A row whose
(symbol, action_type, event_date, knowledge_date) 4-tuple already exists is skipped (P4-009); one
matching only the 3-part business key with a DIFFERENT knowledge_date (the PFC case -- see
docs/phase10_amendment4_prep.md) is inserted as a new, distinct vintage, coexisting with the old
row, not replacing it -- exactly what append-only requires. Reported explicitly below, not
silently left for a reader to discover.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import latest_as_of, read_as_of
from src.config.settings import get_settings
from src.ingestion.nse_market_data.corporate_actions import ingest_corporate_actions

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "raw" / "p8007_full_sweep_cache"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
SOURCE_FILE = "p8007_full_sweep_2019_2026_live_promoted"
YEAR_FROM, YEAR_TO = 2019, 2026


def main() -> None:
    all_actions: list[dict] = []
    for year in range(YEAR_FROM, YEAR_TO + 1):
        with open(CACHE_DIR / f"actions_{year}.json", encoding="utf-8") as f:
            all_actions.extend(json.load(f))
    print(f"Loaded {len(all_actions)} cached actions ({YEAR_FROM}-{YEAR_TO})")

    with open(CACHE_DIR / "announcements.json", encoding="utf-8") as f:
        announcements_by_key = json.load(f)
    print(f"Loaded {len(announcements_by_key)} cached announcement windows")

    isin_map = json.loads(ISIN_MAP_PATH.read_text(encoding="utf-8"))
    print(f"Loaded ISIN map: {len(isin_map)} symbols")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    before = len(read_as_of(conn, "corporate_actions", "2099-01-01"))
    print(f"\nProduction corporate_actions before promotion: {before} rows")

    report, write_result = ingest_corporate_actions(
        conn, all_actions, announcements_by_key, source_file=SOURCE_FILE, isin_map=isin_map)

    after = len(read_as_of(conn, "corporate_actions", "2099-01-01"))
    print(f"\n=== PROMOTION RESULT ===")
    print(f"Inserted: {write_result.inserted}")
    print(f"Skipped duplicate (identical symbol/action_type/event_date/knowledge_date): {write_result.skipped_duplicate}")
    print(f"Tier counts (this run's build): {report.tier_counts}")
    print(f"Production corporate_actions: {before} -> {after} rows")

    print(f"\n=== SPOT CHECKS ===")
    for symbol in ("UNIVASTU", "AJANTPHARM", "HEG", "HEGAM", "PFC", "M&MFIN"):
        rows = read_as_of(conn, "corporate_actions", "2099-01-01", symbol=symbol)
        print(f"\n{symbol}: {len(rows)} row(s)")
        for r in sorted(rows, key=lambda r: (r["action_type"], r["event_date"], r["knowledge_date"])):
            print(f"  {r['action_type']:16s} {r['event_date']}  ratio={r['ratio_numerator']}:{r['ratio_denominator']} "
                  f"tier={r['confidence_tier']:24s} knowledge_date={r['knowledge_date']} source={r['source_file']}")

    print(f"\n=== PFC latest_as_of resolution (the one same-business-key, different-knowledge_date row) ===")
    pfc_latest_early = latest_as_of(conn, "corporate_actions", "2023-08-15", symbol="PFC")
    pfc_latest_late = latest_as_of(conn, "corporate_actions", "2026-09-23", symbol="PFC")
    print(f"as_of=2023-08-15 (between the two knowledge_dates): "
          f"{[(r['knowledge_date'], r['confidence_tier']) for r in pfc_latest_early]}")
    print(f"as_of=2026-09-23 (today): "
          f"{[(r['knowledge_date'], r['confidence_tier']) for r in pfc_latest_late]}")
    print("Expected and accepted (docs/phase10_amendment4_prep.md): as_of=2023-08-15 sees the "
          "corrected CONFIRMED row (fixes the bitemporal-visibility gap); as_of=2026-09-23 still "
          "resolves to the OLD EX_DATE_FALLBACK row under latest_as_of's max-knowledge_date "
          "tie-break -- harmless for adjustment (identical ratio both rows), a known, narrow, "
          "disclosed limitation of this one row's confidence_tier metadata only.")

    conn.close()


if __name__ == "__main__":
    main()
