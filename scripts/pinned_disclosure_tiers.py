"""Runs under the PINNED forward pipeline (afe3e2b), not HEAD.

Invoked by scripts/verify_pinned_announcement_reader.py with the pinned commit's worktree inserted
first on sys.path, so every `src` import resolves to afe3e2b's code (asserted below). Two modes:

- tiers: repeats afe3e2b's scripts/build_event_classifications.py disclosure-tier computation
  (its main(), "fetched_symbols" through classify_disclosure_window) verbatim for the given events,
  against a read-only store copy: coverage = any row stored under the symbol; rows = SELECT
  event_date, category ... WHERE symbol=?; the 10-session window on the ISIN-stitched trading
  history; classify_disclosure_window. Inputs only: no outcome label is read or computed.
- init_db: runs the pinned init_db on a temporary (writable) copy and reports the schema objects
  it added, because the pinned evaluation calls init_db before it reads.
"""
import argparse
import bisect
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DISCLOSURE_WINDOW_SESSIONS = 10   # afe3e2b build_event_classifications.py


def _schema(conn):
    return sorted((r[0], r[1], r[2] or '') for r in conn.execute('SELECT type, name, sql FROM sqlite_master'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worktree', required=True)
    parser.add_argument('--store', required=True)
    parser.add_argument('--mode', choices=('tiers', 'init_db'), required=True)
    parser.add_argument('--isin-map')
    parser.add_argument('--events')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    worktree = Path(args.worktree).resolve()
    sys.path.insert(0, str(worktree))

    from src.bitemporal import connection as pinned_connection
    from src.signals import disclosure_classification, event_catalogue
    from src.ingestion.nse_market_data import isin_mapping
    modules = {m.__name__: m.__file__ for m in (pinned_connection, disclosure_classification, event_catalogue, isin_mapping)}
    if not all(Path(f).resolve().is_relative_to(worktree) for f in modules.values()):
        raise SystemExit(f'Refusing: an import did not resolve to the pinned worktree: {modules}')

    if args.mode == 'init_db':
        conn = sqlite3.connect(args.store)
        conn.row_factory = sqlite3.Row
        before = _schema(conn)
        pinned_connection.init_db(conn)
        after = _schema(conn)
        conn.close()
        result = dict(modules=modules, added=[list(x) for x in after if x not in before],
                      removed=[list(x) for x in before if x not in after])
        Path(args.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
        return

    conn = sqlite3.connect(f'file:{Path(args.store).as_posix()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    events = json.loads(Path(args.events).read_text(encoding='utf-8'))
    fetched_symbols = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM corporate_announcements").fetchall()}
    symbol_groups = isin_mapping.build_symbol_groups(isin_mapping.load_isin_map(Path(args.isin_map)))
    by_symbol = defaultdict(list)
    for e in events:
        by_symbol[e['symbol']].append(e['event_date'])
    out = []
    for symbol, dates in sorted(by_symbol.items()):
        has_coverage = symbol in fetched_symbols
        hist = event_catalogue.build_symbol_history(conn, symbol, symbol_group=symbol_groups.get(symbol, [symbol]))
        days = hist.trading_days
        ann_rows, ann_dates = [], []
        rows_by_date = defaultdict(list)
        if has_coverage:
            ann_rows = conn.execute(
                "SELECT event_date, category FROM corporate_announcements WHERE symbol=? ORDER BY event_date",
                (symbol,),
            ).fetchall()
            ann_dates = sorted(r[0] for r in ann_rows)
            for event_date_, category in ann_rows:
                rows_by_date[event_date_].append({"category": category})
        for event_date in dates:
            window_start, raw = None, []
            if not has_coverage:
                tier = "UNKNOWN_COVERAGE"
            else:
                idx = bisect.bisect_left(days, event_date)
                if idx < DISCLOSURE_WINDOW_SESSIONS:
                    window_rows = []
                else:
                    window_start = days[idx - DISCLOSURE_WINDOW_SESSIONS]
                    lo = bisect.bisect_left(ann_dates, window_start)
                    hi = bisect.bisect_left(ann_dates, event_date)
                    window_rows = []
                    for d in ann_dates[lo:hi]:
                        window_rows.extend(rows_by_date.get(d, []))
                    # The rows behind that window, once each (the verbatim loop repeats a date's
                    # rows once per row on that date; tiers are set-based, so this never matters).
                    raw = sorted([r[0], r[1]] for r in ann_rows if window_start <= r[0] < event_date)
                tier = disclosure_classification.classify_disclosure_window(window_rows)
            out.append(dict(symbol=symbol, event_date=event_date, has_coverage=has_coverage,
                            window_start=window_start, tier=tier, rows=raw,
                            stitched_group=sorted(symbol_groups.get(symbol, [symbol]))))
    conn.close()
    Path(args.out).write_text(json.dumps(dict(modules=modules, results=out)), encoding='utf-8')


if __name__ == '__main__':
    main()
