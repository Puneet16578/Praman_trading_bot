"""P8-007 corrections, item 1: a full live corporate-actions sweep (2019-2026), staged
SEPARATELY from production so it can be diffed against it (see
scripts/phase10_p8007_sweep_diff.py) without ever writing to the production database
(src/config/settings.py's database_path) or any table derived from it. No refit, no amendment.

Resumable by construction, not by a retry wrapper: every year's raw action fetch and every
(symbol, ex_date) announcement-window fetch is written to disk immediately after it succeeds
(data/raw/p8007_full_sweep_cache/). A run killed at any point -- network failure, session
expiry over an overnight run, an environment restart -- is resumed by re-invoking this exact
script; every already-cached year and (symbol, ex_date) pair is skipped before any network call,
so at most one in-flight request is ever lost. The final staging write
(ingest_corporate_actions -> write_facts) is itself idempotent on the (symbol, action_type,
event_date) business key (P4-009), so re-running it against an already-populated staging DB is
also safe.

Only fetches ONE announcement window per distinct (symbol, ex_date) pair among EQ-series,
bonus/split-shaped subjects -- identical scope to fetch_all's own `_fetch_announcements_for_actions`
(demergers, rights, and other non-ratio types need no announcement cross-check, per CLAUDE.md).
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.ingestion.nse_market_data.corporate_actions import (
    _session_with_cookie, announcement_cache_key, fetch_announcements_window,
    fetch_corporate_actions_year, ingest_corporate_actions, parse_subject_ratio,
)

YEAR_FROM = 2019
YEAR_TO = 2026
DELAY_SECONDS = 0.3
ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "raw" / "p8007_full_sweep_cache"
STAGING_DB_PATH = ROOT / "data" / "processed" / "praman_staging_p8007_sweep.db"
SOURCE_FILE = "p8007_full_sweep_2019_2026_live"


def _actions_cache_path(year: int) -> Path:
    return CACHE_DIR / f"actions_{year}.json"


def _announcements_cache_path() -> Path:
    return CACHE_DIR / "announcements.json"


def fetch_actions_resumable(session) -> list[dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    all_actions: list[dict] = []
    for year in range(YEAR_FROM, YEAR_TO + 1):
        cache_path = _actions_cache_path(year)
        if cache_path.exists():
            year_actions = json.loads(cache_path.read_text(encoding="utf-8"))
            print(f"  {year}: {len(year_actions)} actions (cached, skipped live fetch)", flush=True)
        else:
            year_actions = fetch_corporate_actions_year(session, year)
            cache_path.write_text(json.dumps(year_actions), encoding="utf-8")
            print(f"  {year}: {len(year_actions)} actions (fetched live)", flush=True)
            time.sleep(DELAY_SECONDS)
        all_actions.extend(year_actions)
    return all_actions


def fetch_announcements_resumable(session, actions: list[dict]) -> dict[str, list[dict]]:
    cache_path = _announcements_cache_path()
    cache: dict[str, list[dict]] = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    keys_needed: list[tuple[str, str, object]] = []
    seen: set[str] = set()
    for action in actions:
        if action.get("series") != "EQ":
            continue
        subject = action.get("subject", "") or ""
        if parse_subject_ratio(subject) is None:
            continue
        symbol = action["symbol"]
        try:
            ex_date = datetime.strptime(action["exDate"], "%d-%b-%Y").date()
        except ValueError:
            continue
        key = announcement_cache_key(symbol, ex_date)
        if key in seen:
            continue
        seen.add(key)
        if key not in cache:
            keys_needed.append((key, symbol, ex_date))

    print(f"  Distinct (symbol, ex_date) bonus/split-shaped pairs: {len(seen)}", flush=True)
    print(f"  Already cached (resumed, skipped): {len(seen) - len(keys_needed)}", flush=True)
    print(f"  To fetch this run: {len(keys_needed)}", flush=True)

    for i, (key, symbol, ex_date) in enumerate(keys_needed):
        cache[key] = fetch_announcements_window(session, symbol, ex_date)
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        if (i + 1) % 50 == 0:
            print(f"    ...{i + 1}/{len(keys_needed)} fetched", flush=True)
        time.sleep(DELAY_SECONDS)

    return cache


def main() -> None:
    print(f"=== P8-007 corrections, item 1: full live sweep {YEAR_FROM}-{YEAR_TO} (staging only) ===", flush=True)
    session = _session_with_cookie()

    print("\nStep 1: corporate actions by year", flush=True)
    actions = fetch_actions_resumable(session)
    print(f"Total raw actions fetched: {len(actions)}", flush=True)

    print("\nStep 2: announcement windows (bonus/split-shaped EQ subjects only)", flush=True)
    announcements = fetch_announcements_resumable(session, actions)

    print(f"\nStep 3: writing to STAGING database (production is never touched)", flush=True)
    print(f"  staging path: {STAGING_DB_PATH}", flush=True)
    conn = get_connection(str(STAGING_DB_PATH))
    init_db(conn)
    report, write_result = ingest_corporate_actions(conn, actions, announcements, SOURCE_FILE)
    conn.close()

    print(f"\n=== STAGING WRITE RESULT ===", flush=True)
    print(f"Inserted: {write_result.inserted}", flush=True)
    print(f"Skipped duplicate: {write_result.skipped_duplicate}", flush=True)
    print(f"Tier counts: {report.tier_counts}", flush=True)
    print(f"Downgraded for gap: {report.downgraded_count}", flush=True)
    print(f"Quarantined (logged + written as RATIO_CONFLICT_EXCLUSION): {len(report.quarantined)}", flush=True)
    print(f"Unhandled action types (not written): {report.unhandled_action_types}", flush=True)
    print("\nDONE.", flush=True)


if __name__ == "__main__":
    main()
