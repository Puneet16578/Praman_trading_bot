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
end - FIRST_RUN_MAX_DAYS; later runs, from (last complete refresh - OVERLAP_DAYS). Cadence: every
nightly run (CADENCE_DAYS = 1), because the Desk treats disclosures as UNKNOWN unless the source is
complete through the day before the decision (desk/source_freshness.py); daily is a strict
superset of Amendment 2 sec. 5's weekly requirement. A refresh is complete only when no symbol
failed; any failure prints a WARN line (the nightly step then reports WARN), the failed symbols
stay stale for the Desk, and the next nightly run retries.
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
CADENCE_DAYS = 1          # nightly; a strict superset of Amendment 2 sec. 5's weekly schedule
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


def per_symbol_main(end_date: date | None = None, *, conn=None, session=None, isin_map=None, state_path=STATE_PATH,
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
                       failed_symbols=sorted(failed), seconds=round(time.time() - t0, 1), universe=universe)
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


BULK_STATE_PATH = ROOT / 'data/processed/announcements_bulk_state.json'
BULK_START = date(2026, 9, 10)


def main(end_date=None, *, mode=None, conn=None, session=None, isin_map=None,
         state_path=None, force=False, fetch_and_ingest=None, start_date=None,
         client=None, max_requests=30, identity_dir=None):
    """Default market-wide bulk path. The legacy per-symbol mode is opt-in only."""
    from src.config.settings import get_settings
    mode = mode or get_settings().announcement_fetch_mode
    if mode == 'per_symbol':
        result = per_symbol_main(end_date, conn=conn, session=session, isin_map=isin_map,
                                 state_path=state_path or STATE_PATH, force=force, fetch_and_ingest=fetch_and_ingest)
        result['scope'] = 'PER_SYMBOL'
        return result
    if mode != 'bulk':
        raise ValueError('PRAMAN_ANNOUNCEMENTS_MODE must be bulk or per_symbol')
    from src.ingestion.nse_market_data.announcements_bulk import (
        CaptureSession, IDENTITY_DIR, windows, cache_identity, load_identities,
        fetch_checked_window, ingest_bulk, ingest_identity_snapshots, identity_snapshots_from_store)
    from datetime import datetime, timezone
    end_date = end_date or market_today()
    state_path = Path(state_path or BULK_STATE_PATH)
    identity_dir = Path(identity_dir or IDENTITY_DIR)
    prior_state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    last_complete = date.fromisoformat(prior_state['last_complete']) if prior_state.get('last_complete') else None
    # Always re-read the current day: an early-morning run cannot cover disclosures
    # that will arrive before the scheduled evening refresh.
    start = start_date or (max(BULK_START, last_complete-timedelta(days=OVERLAP_DAYS)) if last_complete else BULK_START)
    if last_complete and start > last_complete+timedelta(days=1):
        raise ValueError('Bulk refresh would leave a gap before the requested start')
    if not last_complete and start > BULK_START:
        raise ValueError('First market-wide refresh must include the initial coverage date')
    own_conn, own_client = conn is None, client is None
    if own_conn:
        from src.bitemporal.connection import get_connection, init_db
        conn = get_connection(get_settings().database_path)
        init_db(conn)
    if own_client:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        client = CaptureSession(ROOT/'data/raw/announcement_runs'/stamp, {'backfill': max_requests}, session=session)
    summary = dict(scope='MARKET', status='PARTIAL', start_date=start.isoformat(), end_date=end_date.isoformat(),
                   coverage_from=prior_state.get('coverage_from', start.isoformat()),
                   previous_complete=last_complete.isoformat() if last_complete else None,
                   windows=[], failed_windows=[], failed_symbols=[], inserted=0, skipped_duplicate=0,
                   raw_rows=0, unresolved_identity=0)
    started = time.monotonic()
    try:
        if own_client:
            client.get('cookie', 'https://www.nseindia.com')
        days = {r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy '
            'WHERE event_date BETWEEN ? AND ? AND knowledge_date<=?', (start.isoformat(), end_date.isoformat(), end_date.isoformat()))}
        earlier = conn.execute('SELECT MAX(event_date) FROM bhavcopy WHERE event_date<=? AND knowledge_date<=?',
                               (start.isoformat(), start.isoformat())).fetchone()[0]
        if earlier:
            days.add(earlier)
        for day in sorted(days):
            cache_identity(client, date.fromisoformat(day), identity_dir)
        identities = ingest_identity_snapshots(conn, load_identities(identity_dir), end_date.isoformat())
        summary['identity_rows_inserted'] = identities.inserted
        # Resolve from the append-only fact table, not the cache files that transported it.
        snapshots = identity_snapshots_from_store(conn, end_date.isoformat())
        for first, last in windows(start, end_date):
            entry = dict(start=first.isoformat(), end=last.isoformat())
            try:
                raw = fetch_checked_window(client, first, last)
                counts = ingest_bulk(conn, raw, snapshots=snapshots, fetched_on=end_date.isoformat(),
                                     source_file=str(client.directory))
                entry.update(status='COMPLETE', **counts)
                print(f'Announcements {first}..{last}: {counts["raw_rows"]} rows, {counts["inserted"]} inserted', flush=True)
                for field in ('inserted', 'skipped_duplicate', 'raw_rows', 'unresolved_identity'):
                    summary[field] += counts[field]
            except Exception as exc:
                entry.update(status='WARN', error_type=type(exc).__name__)
                summary['failed_windows'].append(entry)
                print(f'WARN announcements bulk {first}..{last}: {type(exc).__name__}')
            summary['windows'].append(entry)
        if not summary['failed_windows']:
            summary['status'] = 'COMPLETE'
            state_path.parent.mkdir(parents=True, exist_ok=True)
            # This operational pointer is not a fact store. Replace atomically;
            # append-only receipts remain in source_freshness and the capture directory.
            temporary = state_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(dict(last_complete=end_date.isoformat(),
                coverage_from=summary['coverage_from'], summary=summary), indent=2)+'\n', encoding='utf-8')
            temporary.replace(state_path)
    except Exception as exc:
        summary['failed_windows'].append(dict(stage='identity_or_session', error_type=type(exc).__name__))
        print(f'WARN announcements bulk setup: {type(exc).__name__}')
    finally:
        summary['seconds'] = round(time.monotonic()-started, 3)
        summary['requests'] = sum(r['component']=='backfill' for r in client.trace)
        summary['failed'] = len(summary['failed_windows'])
        (client.directory/'backfill_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
        print('Announcements bulk: '+json.dumps(summary, sort_keys=True))
        if own_client:
            client.close()
        if own_conn:
            conn.close()
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=date.fromisoformat)
    parser.add_argument('--end', type=date.fromisoformat)
    parser.add_argument('--max-requests', type=int, default=30)
    args = parser.parse_args()
    result = main(args.end, start_date=args.start, max_requests=args.max_requests)
    raise SystemExit(0 if result.get('status') == 'COMPLETE' else 1)
