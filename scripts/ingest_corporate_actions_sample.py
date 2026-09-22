"""Real-data corporate-actions ingestion, full historical range.

P8-006 (docs/DEFECT_REGISTER.md): this script used to load its corporate-actions and announcement
data from cached JSON files inside a PAST Claude session's own temp scratchpad directory --
ephemeral and unavailable to a fresh clone. Now calls `fetch_all()` directly, which fetches both
live over the network and already returns `announcements_by_key` in the exact key format
`ingest_corporate_actions()` expects -- the old `rekey_announcements()` bridging step is no longer
needed at all, not merely pointed at a different cache.

Verification scope, stated plainly rather than implied: `fetch_corporate_actions_year` was
spot-checked live for 2026 (1,819 real rows returned, correct bare-list shape, no envelope
problem the way the SURV circulars endpoint had -- P8-004) before this fix was written. The full
`fetch_all()` sweep -- 7 years of corporate actions plus one announcements-window fetch per
distinct (symbol, ex_date) pair, potentially thousands of real network calls at ~0.3s delay each
-- was NOT run end to end today; that is a real, multi-hour operation, out of scope for this
specific fix. DOCUMENTED, NOT VERIFIED at full historical scale (CLAUDE.md's verification-honesty
convention) -- run it once, end to end, before relying on this script's full-history output.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.corporate_actions import fetch_all, ingest_corporate_actions

YEAR_FROM = 2019  # the project's hard floor (2019-10-01) falls inside this year
YEAR_TO = 2026


def main() -> None:
    print(f"Fetching corporate actions {YEAR_FROM}..{YEAR_TO} live (no cache) -- this can take a while "
          f"(one announcement-window fetch per distinct symbol/ex-date pair).")
    actions, announcements_by_key = fetch_all(YEAR_FROM, YEAR_TO)
    print(f"Fetched {len(actions)} corporate-action rows and {len(announcements_by_key)} announcement windows.")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    report, write_result = ingest_corporate_actions(conn, actions, announcements_by_key, source_file="nse_corporate_actions_live_fetch")

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
