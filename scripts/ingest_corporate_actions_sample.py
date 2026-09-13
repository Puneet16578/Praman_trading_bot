"""Real-data corporate-actions ingestion, reusing the cache already built during Phase 3 source
evaluation (this session's scratchpad) so this run makes ZERO new network calls. Writes to the
same real DB as scripts/ingest_bhavcopy_sample.py.
"""
from __future__ import annotations
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.corporate_actions import announcement_cache_key, ingest_corporate_actions

SCRATCH_CACHE = Path(r"C:\Users\VICTUS\AppData\Local\Temp\claude\d--Agentic-ai-project\693aa27b-1dbb-463f-b783-329123a86aff\scratchpad\cache")
FETCH_WINDOW_DAYS = 200  # must match what validate_ratio_parser.py used when building the cache

def rekey_announcements(actions: list[dict], raw_cache: dict) -> dict[str, list[dict]]:
    rekeyed = {}
    for action in actions:
        if action.get("series") != "EQ":
            continue
        symbol = action["symbol"]
        ex_date = datetime.strptime(action["exDate"], "%d-%b-%Y").date()
        from_date = (ex_date - timedelta(days=FETCH_WINDOW_DAYS)).strftime("%d-%m-%Y")
        to_date = ex_date.strftime("%d-%m-%Y")
        old_key = f"{symbol}|{from_date}|{to_date}"
        data = raw_cache.get(old_key)
        if data is None or (isinstance(data, dict) and "error" in data):
            continue
        rekeyed[announcement_cache_key(symbol, ex_date)] = data
    return rekeyed

def main() -> None:
    actions = json.loads((SCRATCH_CACHE / "actions_2019_2026.json").read_text(encoding="utf-8"))
    raw_ann_cache = json.loads((SCRATCH_CACHE / "announcements.json").read_text(encoding="utf-8"))
    announcements_by_key = rekey_announcements(actions, raw_ann_cache)
    print(f"Loaded {len(actions)} corporate-action rows and {len(announcements_by_key)} announcement windows from cache (zero network calls).")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    report, write_result = ingest_corporate_actions(conn, actions, announcements_by_key, source_file="nse_corporate_actions_2019_2026_cached.json")

    print("\n=== TIER COUNTS ===")
    total = sum(report.tier_counts.values())
    for tier, count in sorted(report.tier_counts.items()):
        print(f"  {tier}: {count} ({100*count/total:.1f}%)" if total else f"  {tier}: {count}")
    print(f"  TOTAL WRITTEN ROWS: {total}")
    print(f"  Downgraded to EX_DATE_FALLBACK for out-of-range gap: {report.downgraded_count}")
    print(f"  Unhandled action types (dividends, rights, etc. -- not ingested this session): {report.unhandled_action_types}")

    print(f"\n=== WRITE RESULT === inserted={write_result.inserted} skipped_duplicate={write_result.skipped_duplicate}")

    print(f"\n=== QUARANTINED (n={len(report.quarantined)}) -- NOT written to the store ===")
    for q in report.quarantined:
        print(f"  {q}")

    conn.close()

if __name__ == "__main__":
    main()
