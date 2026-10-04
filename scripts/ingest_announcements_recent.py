"""Bounded recent-announcement refresh (P8-021).

`ingest_announcements_full_history.py` is a resumable BACKFILL: it skips every symbol that already
has a stored announcement, so once the 2026-09-18/19 backfill finished, new disclosures for those
symbols were never fetched again. Amendment 2 §5 of the frozen pre-registration requires
announcements to be ingested on a regular WEEKLY schedule through the forward window, not as a
single backfill, so this refresh implements that existing commitment.

Scope (source-scope review, P8-021): the same per-symbol `corporate-announcements` endpoint and the
same fetch/row-building/write path as the backfill (`fetch_and_ingest_symbol`, default
source_file), so rows are identical to what the backfill would store. Re-fetched announcements
are skipped by the table's UNIQUE (symbol, seq_id, knowledge_date); knowledge_date is the
announcement's own publication date, so a late fetch stays point-in-time correct. Symbols:
equities (resolved, non-INF ISIN) with an EQ session in the last ACTIVE_DAYS and at least one
stored announcement; symbols with none remain the backfill's job.

Window: first run, from (latest stored announcement - OVERLAP_DAYS), but no earlier than
end - FIRST_RUN_MAX_DAYS; later runs, from (last complete refresh - OVERLAP_DAYS). Weekly cadence:
skipped when the last COMPLETE refresh is under CADENCE_DAYS old. A refresh is complete only when
no symbol failed; any failure prints a WARN line (the nightly step then reports WARN) and the next
nightly run retries.
"""
from __future__ import annotations
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared.market_time import market_today

STATE_PATH = ROOT / 'data/processed/announcements_refresh_state.json'
ISIN_MAP_PATH = ROOT / 'data/raw/nse_symbol_isin_current.json'
START_DATE = date(2019, 10, 1)
CADENCE_DAYS = 7          # Amendment 2 §5: weekly
OVERLAP_DAYS = 7          # re-read a week of overlap; duplicates are skipped by the UNIQUE key
FIRST_RUN_MAX_DAYS = 120
ACTIVE_DAYS = 60


def read_state(path):
    try:
        return date.fromisoformat(json.loads(path.read_text(encoding='utf-8'))['last_complete'])
    except FileNotFoundError:
        return None


def refresh_plan(conn, isin_map, end_date, last_complete):
    """(symbol, from_date) pairs to fetch, using only rows known by end_date."""
    as_of = end_date.isoformat()
    active = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM bhavcopy WHERE series='EQ' AND event_date>=? "
                                         "AND knowledge_date<=?", ((end_date - timedelta(days=ACTIVE_DAYS)).isoformat(), as_of))}
    latest = dict(conn.execute('SELECT symbol, MAX(event_date) FROM corporate_announcements WHERE knowledge_date<=? '
                               'GROUP BY symbol', (as_of,)).fetchall())
    equity = {s for s in active if isin_map.get(s) and not isin_map[s].startswith('INF')}
    plan = []
    for symbol in sorted(equity & set(latest)):
        if last_complete is not None:
            start = last_complete - timedelta(days=OVERLAP_DAYS)
        else:
            start = max(date.fromisoformat(latest[symbol]) - timedelta(days=OVERLAP_DAYS),
                        end_date - timedelta(days=FIRST_RUN_MAX_DAYS))
        plan.append((symbol, max(START_DATE, min(start, end_date))))
    return plan, dict(active=len(active), equity_active=len(equity), without_stored_rows=len(equity - set(latest)))


def main(end_date: date | None = None, *, conn=None, session=None, isin_map=None, state_path=STATE_PATH,
         force=False, fetch_and_ingest=None) -> dict:
    end_date = end_date or market_today()
    last_complete = read_state(state_path)
    if not force and last_complete is not None and (end_date - last_complete).days < CADENCE_DAYS:
        print(f'Announcements refresh not due: last complete {last_complete}, next due '
              f'{last_complete + timedelta(days=CADENCE_DAYS)}.')
        return dict(status='NOT_DUE', last_complete=last_complete.isoformat())
    own_conn = conn is None
    if own_conn:
        from src.bitemporal.connection import get_connection, init_db
        from src.config.settings import get_settings
        conn = get_connection(get_settings().database_path)
        init_db(conn)
    if isin_map is None:
        from src.ingestion.nse_market_data.isin_mapping import load_isin_map
        isin_map = load_isin_map(ISIN_MAP_PATH)   # missing map raises: never fetch an unclassified universe
    if fetch_and_ingest is None:
        from src.ingestion.nse_market_data.announcements import fetch_and_ingest_symbol as fetch_and_ingest
    try:
        plan, universe = refresh_plan(conn, isin_map, end_date, last_complete)
        print(f"Announcements refresh to {end_date}: {len(plan)} equity symbols "
              f"({universe['without_stored_rows']} active equities without stored rows are left to the backfill).")
        if session is None:
            from src.ingestion.nse_market_data.announcements import _session_with_cookie
            session = _session_with_cookie()
        t0, raw_total, inserted, skipped, failed = time.time(), 0, 0, 0, []
        for i, (symbol, start) in enumerate(plan, 1):
            try:
                result, raw_count = fetch_and_ingest(conn, session, symbol, start, end_date)
            except Exception as exc:
                failed.append(symbol)
                print(f'WARN announcements refresh: FAILED {symbol}: {type(exc).__name__}: {exc}')
                continue
            raw_total += raw_count
            inserted += result.inserted
            skipped += result.skipped_duplicate
            if i % 250 == 0:
                print(f'  ...{i}/{len(plan)} symbols, {inserted} new rows, {time.time() - t0:.0f}s')
        summary = dict(status='COMPLETE' if not failed else 'PARTIAL', end_date=end_date.isoformat(), symbols=len(plan),
                       raw_rows=raw_total, inserted=inserted, skipped_duplicate=skipped, failed=len(failed),
                       seconds=round(time.time() - t0, 1), universe=universe)
        print(f"Refresh {summary['status']}: {len(plan) - len(failed)}/{len(plan)} symbols, {raw_total} rows fetched, "
              f"{inserted} new, {skipped} already stored, {summary['seconds']}s")
        if failed:
            print(f'WARN announcements refresh: {len(failed)} symbols FAILED; refresh not marked complete: {failed}')
        else:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(dict(last_complete=end_date.isoformat(), summary=summary), indent=2) + '\n',
                                  encoding='utf-8')
        return summary
    finally:
        if own_conn:
            conn.close()


if __name__ == '__main__':
    main(force='--force' in sys.argv)
