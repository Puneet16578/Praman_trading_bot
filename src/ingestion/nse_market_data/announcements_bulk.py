"""Bulk announcement transport and ingestion; extends the existing fact writer."""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import time
import zipfile
from functools import lru_cache

import requests

from .announcements import AnnouncementFetchError, build_announcement_rows
from ...bitemporal.store import write_facts, BulkWriteResult

ROOT = Path(__file__).resolve().parents[3]
IDENTITY_DIR = ROOT / 'data/raw/announcement_identity'
ENDPOINT = 'https://www.nseindia.com/api/corporate-announcements'
CONTENT_FIELDS = ('event_date', 'category', 'description', 'sort_timestamp')


class RequestBudgetExceeded(RuntimeError):
    pass


class CaptureSession:
    """No implicit retries/redirects. Budgets count attempts, including failures."""
    def __init__(self, directory, budgets, session=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.budgets = dict(budgets)
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        self.trace = []

    def get(self, label, url, *, params=None, component='backfill'):
        if sum(r['component'] == component for r in self.trace) >= self.budgets.get(component, 0):
            raise RequestBudgetExceeded(f'{component} request budget exhausted')
        item = dict(label=label, component=component, url=url, params=params,
                    started_at=datetime.now(timezone.utc).isoformat())
        self.trace.append(item)
        started = time.monotonic()
        try:
            response = self.session.get(url, params=params, timeout=40, allow_redirects=False)
            item.update(status=response.status_code, sha256=hashlib.sha256(response.content).hexdigest())
            path = self.directory / f'{len(self.trace):02d}_{label}.response'
            path.write_bytes(response.content)
            item['capture'] = str(path)
            if response.status_code != 200:
                raise AnnouncementFetchError(f'HTTP {response.status_code}')
            return response.content
        except Exception as exc:
            item['error_type'] = type(exc).__name__
            raise
        finally:
            item['seconds'] = round(time.monotonic() - started, 3)
            (self.directory / 'requests.json').write_text(json.dumps(self.trace, indent=2)+'\n', encoding='utf-8')

    def close(self):
        self.session.close()


def windows(start, end, days=7):
    if start > end:
        raise ValueError('Reversed announcement window')
    while start <= end:
        last = min(end, start + timedelta(days=days-1))
        yield start, last
        start = last + timedelta(days=1)


def stable_id(raw):
    if raw.get('seq_id') not in (None, ''):
        return str(raw['seq_id'])
    # Exclude current ticker, company name, ISIN and retrieval metadata: all may
    # change after publication. An attachment URL or substantive text is required.
    if not raw.get('attchmntFile') and not raw.get('attchmntText'):
        raise AnnouncementFetchError('Announcement has neither identifier nor hashable content')
    payload = {k: raw.get(k) for k in ('sort_date', 'desc', 'attchmntText', 'attchmntFile')}
    return 'sha256:' + hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def parse_bulk(content, start, end):
    raw = json.loads(content)
    if not isinstance(raw, list):
        raise AnnouncementFetchError('Bulk response is not a list')
    for row in raw:
        if not isinstance(row, dict) or not row.get('symbol'):
            raise AnnouncementFetchError('Missing announcement symbol')
        try:
            publication = datetime.strptime(row['sort_date'], '%Y-%m-%d %H:%M:%S').date()
        except (KeyError, TypeError, ValueError) as exc:
            raise AnnouncementFetchError('Invalid announcement publication timestamp') from exc
        if not start <= publication <= end:
            raise AnnouncementFetchError('Announcement outside requested dates')
        stable_id(row)
    return raw


def fetch_window(client, start, end, *, component='backfill', label='bulk'):
    content = client.get(f'{label}_{start}_{end}', ENDPOINT, component=component,
                         params=dict(index='equities', from_date=start.strftime('%d-%m-%Y'), to_date=end.strftime('%d-%m-%Y')))
    return parse_bulk(content, start, end)


def payload_signatures(raw):
    # Compare all semantic fields, ignoring transient response formatting/size.
    return {json.dumps({k: r.get(k) for k in ('symbol', 'sm_isin', 'sort_date', 'desc', 'attchmntText', 'attchmntFile')}
                       | {'announcement_id': stable_id(r)}, sort_keys=True, ensure_ascii=False) for r in raw}


def fetch_checked_window(client, start, end):
    whole = fetch_window(client, start, end)
    if start < end:
        middle = start + (end-start)//2
        split = fetch_window(client, start, middle, label='check')
        split += fetch_window(client, middle+timedelta(days=1), end, label='check')
        if payload_signatures(whole) != payload_signatures(split):
            raise AnnouncementFetchError('Whole/split announcement windows differ')
    return whole


def parse_identity_archive(content, expected_date):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(names) != 1:
            raise AnnouncementFetchError('Expected one identity CSV')
        rows = list(csv.DictReader(io.StringIO(archive.read(names[0]).decode('utf-8-sig'))))
    if not rows or any(r.get('TradDt') != expected_date.isoformat() for r in rows):
        raise AnnouncementFetchError('Identity archive date mismatch')
    records = []
    for r in rows:
        symbol, isin = (r.get('TckrSymb') or '').strip(), (r.get('ISIN') or '').strip()
        if symbol and isin:
            records.append(dict(symbol=symbol, isin=isin, series=(r.get('SctySrs') or '').strip()))
    if not records:
        raise AnnouncementFetchError('Identity archive has no usable records')
    return records


def cache_identity(client, day, directory=IDENTITY_DIR):
    path = Path(directory) / f'{day}.json'
    if path.exists():
        return path
    url = f'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip'
    content = client.get(f'identity_{day}', url)
    records = parse_identity_archive(content, day)
    payload = dict(event_date=day.isoformat(), knowledge_date=day.isoformat(), source=url,
                   recorded_at=datetime.now(timezone.utc).isoformat(),
                   sha256=hashlib.sha256(content).hexdigest(), records=records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as out:
        json.dump(payload, out, ensure_ascii=False)
    return path


def load_identities(directory=IDENTITY_DIR):
    files = tuple((str(p), p.stat().st_mtime_ns) for p in sorted(Path(directory).glob('*.json')))
    return _load_identity_files(files)


@lru_cache(maxsize=4)
def _load_identity_files(files):
    snapshots = [json.loads(Path(p).read_text(encoding='utf-8')) for p, _ in files]
    for snapshot in snapshots:
        snapshot['_by_symbol'], snapshot['_by_isin'] = identity_indexes(snapshot)
    return snapshots


def identity_indexes(snapshot):
    by_symbol, by_isin = defaultdict(set), defaultdict(set)
    for row in snapshot['records']:
        by_symbol[row['symbol']].add(row['isin'])
        by_isin[row['isin']].add(row['symbol'])
    return by_symbol, by_isin


def resolve_publication_identity(raw, snapshots):
    publication = raw['sort_date'][:10]
    visible = [s for s in snapshots if s['event_date'] <= publication and s['knowledge_date'] <= publication]
    if not visible:
        return raw['symbol'], None, None, 'UNKNOWN_NO_DATED_IDENTITY'
    snapshot = max(visible, key=lambda s: (s['event_date'], s['knowledge_date']))
    if '_by_symbol' in snapshot:
        by_symbol, by_isin = snapshot['_by_symbol'], snapshot['_by_isin']
    else:
        by_symbol, by_isin = identity_indexes(snapshot)
    # A dated symbol observation wins over the live endpoint's current ISIN.
    identities = by_symbol.get(raw['symbol'], set())
    aliases = by_isin.get(raw.get('sm_isin'), set())
    if len(aliases) == 1 and raw['symbol'] not in aliases:
        return next(iter(aliases)), raw['sm_isin'], snapshot['event_date'], 'DATED_ISIN_ALIAS'
    if len(identities) == 1:
        return raw['symbol'], next(iter(identities)), snapshot['event_date'], 'DATED_SYMBOL'
    if len(aliases) == 1:
        return next(iter(aliases)), raw['sm_isin'], snapshot['event_date'], 'DATED_ISIN_ALIAS'
    return raw['symbol'], None, snapshot['event_date'], 'UNKNOWN_AMBIGUOUS_OR_ABSENT'


def identity_snapshots_from_store(conn, as_of):
    """Dated identity evidence as recorded in the append-only security_identities fact table, as
    of `as_of` -- the identities ingestion and replay use, never today's cache files. Unqualified
    reads respect a replay connection's recorded-at views."""
    grouped = defaultdict(list)
    for row in conn.execute('SELECT symbol, isin, series, event_date, knowledge_date FROM security_identities '
                            'WHERE event_date<=? AND knowledge_date<=? ORDER BY event_date, row_id', (as_of, as_of)):
        grouped[(row['event_date'], row['knowledge_date'])].append(dict(symbol=row['symbol'], isin=row['isin'], series=row['series']))
    snapshots = []
    for (event_date, knowledge_date), records in sorted(grouped.items()):
        snapshot = dict(event_date=event_date, knowledge_date=knowledge_date, records=records)
        snapshot['_by_symbol'], snapshot['_by_isin'] = identity_indexes(snapshot)
        snapshots.append(snapshot)
    return snapshots


def ingest_identity_snapshots(conn, snapshots, as_of):
    rows = [dict(r, event_date=s['event_date'], knowledge_date=s['knowledge_date'],
                 source_file=json.dumps(dict(source=s['source'],sha256=s['sha256']),sort_keys=True))
            for s in snapshots if s['knowledge_date'] <= as_of for r in s['records']]
    return write_facts(conn,'security_identities',rows) if rows else BulkWriteResult(0,0)


def ingest_bulk(conn, raw, *, snapshots, fetched_on, source_file):
    """Store every usable row, regardless of equity series/identity availability.

    Same-content repeats (including renames) never append a second announcement.
    A genuine changed-content vintage uses its later observation date.
    """
    pending, skipped, unknown = [], 0, 0
    seen = {}
    for item in raw:
        item = dict(item, seq_id=stable_id(item))
        symbol, isin, identity_date, status = resolve_publication_identity(item, snapshots)
        row = build_announcement_rows(symbol, [item], source_file)[0]
        row.update(isin=isin, identity_date=identity_date, identity_status=status)
        unknown += isin is None
        prior = seen.setdefault(row['seq_id'], [dict(r) for r in conn.execute(
            'SELECT * FROM corporate_announcements WHERE seq_id=? AND knowledge_date<=?', (row['seq_id'], fetched_on))])
        if any(all(p[f] == row[f] for f in CONTENT_FIELDS) for p in prior):
            skipped += 1
            continue
        if prior:
            row['knowledge_date'] = fetched_on
            if any(p['knowledge_date'] >= fetched_on for p in prior):
                raise AnnouncementFetchError('Conflicting same-day announcement vintage')
        pending.append(row)
        prior.append(row)
    result = write_facts(conn, 'corporate_announcements', pending) if pending else BulkWriteResult(0, 0)
    return dict(inserted=result.inserted, skipped_duplicate=skipped+result.skipped_duplicate,
                unresolved_identity=unknown, raw_rows=len(raw))


def read_equity_announcements(conn, symbol, as_of, *, snapshots=None):
    """Date-qualified identity join and stable-ID deduplication, only at read time.

    Legacy facts without identity metadata retain their symbol-based historical
    behavior. New unresolved identities are returned with an explicit coverage flag.
    """
    from ...bitemporal.guard import _validate_as_of
    as_of = _validate_as_of(as_of)
    aliases = {symbol}
    isin = None
    if snapshots is not None:  # explicit, isolated fixture evidence
        _, isin, _, _ = resolve_publication_identity(dict(symbol=symbol, sort_date=as_of+' 23:59:59'), snapshots)
        for snapshot in snapshots:
            if isin and snapshot['event_date'] <= as_of and snapshot['knowledge_date'] <= as_of:
                aliases.update(r['symbol'] for r in snapshot['records'] if r['isin'] == isin)
    elif conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='security_identities'").fetchone():
        # Unqualified table reads respect the Desk replay's recorded-at TEMP views.
        identity = conn.execute('SELECT isin FROM security_identities WHERE symbol=? AND event_date<=? '
                                'AND knowledge_date<=? ORDER BY event_date DESC,knowledge_date DESC,row_id DESC LIMIT 1',
                                (symbol,as_of,as_of)).fetchone()
        if identity:
            isin = identity['isin']
            aliases.update(r[0] for r in conn.execute('SELECT DISTINCT symbol FROM security_identities WHERE isin=? '
                                                     'AND event_date<=? AND knowledge_date<=?',(isin,as_of,as_of)))
    columns = {r['name'] for r in conn.execute("SELECT name FROM pragma_table_info('corporate_announcements')")}
    placeholders = ','.join('?' for _ in aliases)
    clause, params = f'symbol IN ({placeholders})', [*sorted(aliases)]
    if isin and 'isin' in columns:
        clause += ' OR isin=?'
        params.append(isin)
    rows = [dict(r) for r in conn.execute('SELECT * FROM corporate_announcements WHERE ('+clause+
                                         ') AND knowledge_date<=?', (*params, as_of))]
    best = {}
    for row in rows:
        # All source rows are retained, including funds; only equity reads filter.
        # Equity-only rule (build_final_event_catalogue.py): exclude fund units (INF ISINs); keep
        # INE and the small IN9 DVR class. Unresolved new identities are flagged by the caller.
        if row.get('isin') and row['isin'].startswith('INF'):
            continue
        if isin and isin.startswith('INF'):
            continue
        current = best.get(row['seq_id'])
        if current is None or (row['knowledge_date'], row['row_id']) > (current['knowledge_date'], current['row_id']):
            best[row['seq_id']] = row
    return list(best.values())
