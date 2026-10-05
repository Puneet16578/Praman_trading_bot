"""Can the pinned forward pipeline (afe3e2b) still read the restructured announcement store?

Read-only verification requested by the user on 2026-10-06 (P8-046 follow-up). It computes
disclosure tiers, a model INPUT, for recent events; it never reads or computes an outcome label, so
the forward-window firewall is not touched, and it changes no frozen artifact.

1. Copy the production Praman store to a temporary folder (SQLite online backup; the source is
   opened read-only). Every read below uses that copy, opened read-only.
2. Events (seed 20261006): every distinct (symbol, event_date) the Desk scan logged from
   2026-09-16; a seeded random sample of EQ sessions 2026-09-24..2026-10-05 (windows wholly after
   the bulk coverage start, 2026-09-10); every 2026-09-16..2026-10-05 session of the securities
   renamed recently (a member of a multi-symbol ISIN group first trading on or after 2026-08-01).
3. Pinned tiers: scripts/pinned_disclosure_tiers.py in a subprocess with the pinned worktree first
   on sys.path (asserted), repeating build_event_classifications.py's tier code verbatim.
4. HEAD tiers: src.mcp.tools.get_disclosure_window (identity-aware, as of the event date, one row
   per announcement), with the same any-row coverage rule.
5. Compare tiers and window rows; explain every difference from the copy itself.
6. Run the pinned init_db on the temporary copy (writable) and report what it adds: the pinned
   evaluation calls init_db before reading.

Pass criteria, fixed before the first run:
  A. The pinned code runs on the restructured store without error, including its init_db, and
     init_db removes nothing.
  B. Every tier difference is explained by an intended reader difference: HEAD also reads a
     security's rows filed under another symbol of the same ISIN (rename_alias), applies
     knowledge_date <= event date (known_after_event), keeps one row per announcement
     (duplicate_vintage), drops fund units (fund_unit), or uses the unstitched trading history
     (window_boundary).
  C. No row HEAD attributes to an event is filed under a symbol that was not trading on the row's
     publication date (misfiled): the symbol-keyed pinned reader could never find such a row.
Anything else is UNEXPLAINED and is reported as a possible evaluation-blocking defect.
Also measured for every event (added after the first run showed criterion B's window_boundary
cases are exactly the renamed securities): rows inside the pinned, ISIN-stitched window that are
filed under ANOTHER symbol of the same security, which the symbol-keyed pinned reader cannot see
(the P8-046 class), split by whether the bulk path or the legacy per-symbol path filed them.
Writes docs/desk/pinned_reader_verification.json.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PINNED = 'afe3e2bd07abe8b602c4119b916f7696a3c12131'
SEED = 20261006
FORWARD_START = '2026-09-16'
BULK_START = '2026-09-10'
RANDOM_SESSIONS = ('2026-09-24', '2026-10-05')
RANDOM_N = 500
RECENT_RENAME_FROM = '2026-08-01'
RESULT = ROOT / 'docs/desk/pinned_reader_verification.json'
ISIN_MAP = ROOT / 'data/raw/nse_symbol_isin_current.json'


def select_events(conn, desk):
    from src.ingestion.nse_market_data.isin_mapping import build_symbol_groups, load_isin_map
    scanned = {(r[0], r[1]) for r in desk.execute(
        'SELECT DISTINCT symbol, event_date FROM opportunity_log WHERE event_date>=?', (FORWARD_START,))}
    sessions = sorted({(r[0], r[1]) for r in conn.execute(
        "SELECT DISTINCT symbol, event_date FROM bhavcopy WHERE series='EQ' AND event_date BETWEEN ? AND ?",
        RANDOM_SESSIONS)})
    sampled = set(random.Random(SEED).sample(sessions, RANDOM_N))
    groups = {tuple(g) for g in build_symbol_groups(load_isin_map(ISIN_MAP)).values() if len(g) > 1}
    renamed = set()
    for group in sorted(groups):
        first = {s: conn.execute("SELECT MIN(event_date) FROM bhavcopy WHERE symbol=? AND series='EQ'", (s,)).fetchone()[0]
                 for s in group}
        if any(d and d >= RECENT_RENAME_FROM for d in first.values()):
            for s in group:
                renamed |= {(s, r[0]) for r in conn.execute(
                    "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol=? AND series='EQ' AND event_date BETWEEN ? AND ?",
                    (s, FORWARD_START, RANDOM_SESSIONS[1]))}
    sources = defaultdict(list)
    for name, pairs in (('desk_scan', scanned), ('random_sessions', sampled), ('recent_renames', renamed)):
        for pair in pairs:
            sources[pair].append(name)
    return [dict(symbol=s, event_date=d, sources=sorted(sources[(s, d)])) for s, d in sorted(sources)]


def head_tiers(conn, events):
    from src.ingestion.nse_market_data.announcements_bulk import read_equity_announcements
    from src.mcp.tools import get_disclosure_window, has_announcement_coverage
    out = {}
    for e in events:
        symbol, day = e['symbol'], e['event_date']
        covered = has_announcement_coverage(conn, symbol)
        try:
            w = get_disclosure_window(conn, symbol, day)
        except Exception as exc:             # e.g. not a trading day on the unstitched history
            out[(symbol, day)] = dict(tier='UNKNOWN_COVERAGE' if not covered else None, coverage=type(exc).__name__,
                                      window_start=None, rows=[], full=[])
            continue
        full = []
        if w['window_start']:
            full = [dict(seq_id=r['seq_id'], event_date=r['event_date'], category=r['category'], symbol=r['symbol'],
                         isin=r.get('isin'), knowledge_date=r['knowledge_date'], identity_status=r.get('identity_status'))
                    for r in read_equity_announcements(conn, symbol, day) if w['window_start'] <= r['event_date'] < day]
        out[(symbol, day)] = dict(tier='UNKNOWN_COVERAGE' if not covered else w['tier'], coverage=w['coverage'],
                                  window_start=w['window_start'], rows=sorted([r['event_date'], r['category']] for r in w['rows']),
                                  full=full)
    return out


def explain(conn, e, pinned, head):
    """Reasons for each row difference, from the store copy itself."""
    symbol, day = e['symbol'], e['event_date']
    reasons = Counter()
    if pinned['window_start'] and head['window_start'] and pinned['window_start'] != head['window_start']:
        reasons['window_boundary'] += 1
        return reasons
    if (pinned['window_start'] is None) != (head['window_start'] is None) and pinned['tier'] != 'UNKNOWN_COVERAGE':
        reasons['window_boundary'] += 1    # one history is too short for a 10-session window
        return reasons
    start = pinned['window_start'] or head['window_start']
    stored = [] if start is None or pinned['tier'] == 'UNKNOWN_COVERAGE' else [dict(r) for r in conn.execute(
        'SELECT seq_id, event_date, category, knowledge_date, isin, symbol FROM corporate_announcements '
        'WHERE symbol=? AND event_date>=? AND event_date<?', (symbol, start, day))]
    kept = {r['seq_id'] for r in head['full']}
    seen = Counter()
    for r in stored:                      # rows the pinned reader saw
        seen[r['seq_id']] += 1
        if (r['isin'] or '').startswith('INF'):
            reasons['fund_unit'] += 1
        elif r['knowledge_date'] > day:
            reasons['known_after_event'] += 1
        elif seen[r['seq_id']] > 1:
            reasons['duplicate_vintage'] += 1
        elif r['seq_id'] not in kept:
            reasons['UNEXPLAINED_pinned_only'] += 1
    for r in head['full']:                # rows HEAD saw
        if r['symbol'] != symbol:
            traded = conn.execute("SELECT 1 FROM bhavcopy WHERE symbol=? AND event_date<=? AND event_date>=date(?, '-7 day') LIMIT 1",
                                  (r['symbol'], r['event_date'], r['event_date'])).fetchone()
            reasons['rename_alias' if traded else 'UNEXPLAINED_misfiled'] += 1
        elif not any(s['seq_id'] == r['seq_id'] for s in stored):
            reasons['UNEXPLAINED_head_only'] += 1
    return reasons


def unseen_alias_rows(conn, e, pinned):
    """Rows in the pinned stitched window filed under another symbol of the same security: the
    pinned reader keys on the event's own symbol, so it cannot see them (P8-046 class)."""
    others = [s for s in pinned['stitched_group'] if s != e['symbol']]
    if not others or not pinned['window_start'] or pinned['tier'] == 'UNKNOWN_COVERAGE':
        return []
    marks = ','.join('?' for _ in others)
    return [dict(r) for r in conn.execute(
        f'SELECT symbol, seq_id, event_date, category, knowledge_date, identity_status FROM corporate_announcements '
        f'WHERE symbol IN ({marks}) AND event_date>=? AND event_date<? AND knowledge_date<=?',
        (*others, pinned['window_start'], e['event_date'], e['event_date']))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worktree', required=True, help='temporary git worktree checked out at the pinned commit')
    args = parser.parse_args()
    worktree = Path(args.worktree).resolve()
    head = subprocess.run(['git', '-C', str(worktree), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    if head != PINNED:
        raise SystemExit(f'Worktree is at {head}, not the pinned {PINNED}.')
    from shared.sqlite_backup import online_backup
    from shared.sqlite_readonly import open_readonly
    started = time.monotonic()
    report = dict(pinned_commit=PINNED, head_commit=subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                  capture_output=True, text=True, check=True).stdout.strip(), seed=SEED,
                  plan=__doc__.split('Pass criteria')[1].strip())
    with tempfile.TemporaryDirectory(prefix='pinned_reader_') as tmp:
        copy = Path(tmp) / 'praman_copy.db'
        online_backup(ROOT / 'data/processed/praman.db', copy)
        print(f'Store copied in {time.monotonic() - started:.0f}s', flush=True)
        conn = open_readonly(copy)
        desk = open_readonly(ROOT / 'data/desk/desk.sqlite')
        try:
            report['store_copy'] = dict(corporate_announcements=conn.execute('SELECT COUNT(*) FROM corporate_announcements').fetchone()[0],
                                        latest_session=conn.execute('SELECT MAX(event_date) FROM bhavcopy').fetchone()[0])
            events = select_events(conn, desk)
        finally:
            desk.close()
        events_path = Path(tmp) / 'events.json'
        events_path.write_text(json.dumps(events), encoding='utf-8')
        report['events'] = dict(total=len(events), sha256=hashlib.sha256(events_path.read_bytes()).hexdigest(),
                                by_source=dict(Counter(s for e in events for s in e['sources'])))
        print(f"{len(events)} events {report['events']['by_source']}", flush=True)

        pinned_out = Path(tmp) / 'pinned.json'
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/pinned_disclosure_tiers.py'), '--worktree', str(worktree),
                              '--store', str(copy), '--mode', 'tiers', '--isin-map', str(ISIN_MAP),
                              '--events', str(events_path), '--out', str(pinned_out)],
                             cwd=str(worktree), capture_output=True, text=True, env={k: v for k, v in __import__('os').environ.items()
                                                                                       if k != 'PYTHONPATH'})
        report['pinned_tiers_run'] = dict(exit_code=run.returncode, stderr_tail=run.stderr[-2000:])
        if run.returncode != 0:
            raise SystemExit(f'Pinned tier computation failed (exit {run.returncode}):\n{run.stderr[-2000:]}')
        pinned_data = json.loads(pinned_out.read_text(encoding='utf-8'))
        report['pinned_modules'] = pinned_data['modules']
        pinned = {(r['symbol'], r['event_date']): r for r in pinned_data['results']}
        print(f'Pinned tiers done at {time.monotonic() - started:.0f}s', flush=True)

        heads = head_tiers(conn, events)
        print(f'HEAD tiers done at {time.monotonic() - started:.0f}s', flush=True)
        outcomes, reasons_total, differing, unseen = Counter(), Counter(), [], []
        for e in events:
            key = (e['symbol'], e['event_date'])
            p, h = pinned[key], heads[key]
            hidden = unseen_alias_rows(conn, e, p)
            if hidden:
                with_hidden = [[r['event_date'], r['category']] for r in hidden] + p['rows']
                from src.signals.disclosure_classification import classify_disclosure_window
                unseen.append(dict(e, pinned_tier=p['tier'], pinned_window_start=p['window_start'],
                                   tier_if_seen=classify_disclosure_window([dict(category=c) for _, c in with_hidden]),
                                   rows=[dict(r, filed_by='bulk' if r['identity_status'] else 'legacy') for r in hidden]))
            same_tier, same_rows = p['tier'] == h['tier'], p['rows'] == h['rows']
            outcome = 'identical' if same_tier and same_rows else ('rows_differ_same_tier' if same_tier else 'tier_differs')
            outcomes[outcome] += 1
            if outcome == 'identical':
                continue
            reasons = explain(conn, e, p, h)
            reasons_total.update({f'{outcome}:{k}': v for k, v in reasons.items()})
            differing.append(dict(e, outcome=outcome, pinned_tier=p['tier'], head_tier=h['tier'], head_coverage=h['coverage'],
                                  pinned_window_start=p['window_start'], head_window_start=h['window_start'],
                                  pinned_rows=p['rows'], head_rows=h['rows'], reasons=dict(reasons),
                                  head_rows_detail=[r for r in h['full'] if r['symbol'] != e['symbol']]))
        conn.close()
        unknown_identity = sum(1 for h in heads.values() if h['coverage'] == 'unknown_identity')

        init_out = Path(tmp) / 'init_db.json'
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/pinned_disclosure_tiers.py'), '--worktree', str(worktree),
                              '--store', str(copy), '--mode', 'init_db', '--out', str(init_out)],
                             cwd=str(worktree), capture_output=True, text=True, env={k: v for k, v in __import__('os').environ.items()
                                                                                       if k != 'PYTHONPATH'})
        report['pinned_init_db'] = (dict(exit_code=0, **json.loads(init_out.read_text(encoding='utf-8')))
                                    if run.returncode == 0 else dict(exit_code=run.returncode, stderr_tail=run.stderr[-2000:]))

    unexplained = sum(v for k, v in reasons_total.items() if 'UNEXPLAINED' in k)
    tier_unexplained = [d for d in differing if d['outcome'] == 'tier_differs' and (not d['reasons'] or
                        any('UNEXPLAINED' in k for k in d['reasons']))]
    report['pinned_tier_counts'] = dict(Counter(p['tier'] for p in pinned.values()))
    report.update(outcomes=dict(outcomes), reasons=dict(reasons_total), head_unknown_identity_windows=unknown_identity,
                  differing_events=differing, seconds=round(time.monotonic() - started, 1),
                  unseen_alias_rows=dict(
                      events=len(unseen), rows=sum(len(u['rows']) for u in unseen),
                      rows_filed_by=dict(Counter(r['filed_by'] for u in unseen for r in u['rows'])),
                      events_whose_tier_would_change=sum(u['tier_if_seen'] != u['pinned_tier'] for u in unseen),
                      detail=unseen))
    init = report['pinned_init_db']
    report['criteria'] = dict(
        A_runs_including_init_db=init.get('exit_code') == 0 and not init.get('removed'),
        B_every_tier_difference_explained=not tier_unexplained,
        C_no_misfiled_rows=not any('UNEXPLAINED_misfiled' in k for k in reasons_total),
        no_unexplained_row_difference=unexplained == 0)
    report['verdict'] = ('PASS: the pinned code reads the restructured store as it read the per-symbol store'
                         if all(report['criteria'].values()) else
                         'FAIL: possible evaluation-blocking defect; see criteria and differing_events')
    RESULT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('outcomes', 'reasons', 'criteria', 'verdict', 'seconds')}, indent=2))


if __name__ == '__main__':
    main()
