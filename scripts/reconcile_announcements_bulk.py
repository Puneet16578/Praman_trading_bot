"""Offline, read-only reconciliation of the approved September 7-13 probe."""
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config.settings import get_settings
from src.ingestion.nse_market_data.announcements import build_announcement_rows
from scripts.probe_announcements_bulk import compare

AS_OF = '2026-10-05'
START, END = '2026-09-07', '2026-09-13'
CAPTURE = ROOT / 'data/processed/announcements_bulk_reconcile_20261005'
FIELDS = ('symbol', 'seq_id', 'event_date', 'knowledge_date', 'category', 'description', 'sort_timestamp')


def canonical(row):
    return {field: row[field] for field in FIELDS}


def key(row):
    return row['symbol'], str(row['seq_id']), row['knowledge_date']


def facts(raw):
    return [row for item in raw for row in build_announcement_rows(item['symbol'], [item], 'probe')]


def signatures(rows):
    return {json.dumps(canonical(row), sort_keys=True) for row in rows}


def rename_match(stored, raw, isin_map):
    """An ID alone is insufficient: require equal contents and matching ISIN evidence."""
    converted = facts([raw])
    if len(converted) != 1 or stored['symbol'] == raw['symbol']:
        return False
    return (bool(isin_map.get(stored['symbol']))
            and isin_map[stored['symbol']] == raw.get('sm_isin')
            and all(stored[f] == converted[0][f] for f in FIELDS if f != 'symbol'))


def main():
    raw = {name: json.loads((CAPTURE / (name+'.response')).read_text(encoding='utf-8'))
           for name in ('bulk_week', 'bulk_first', 'bulk_last', 'HEG', 'SANGINITA', 'HMT', 'MELSTAR')}
    bulk = facts(raw['bulk_week'])
    before = facts(json.loads((ROOT/'data/processed/announcements_bulk_probe_20260907_13/bulk.response').read_text(encoding='utf-8')))
    isin_map = json.loads((ROOT/'data/raw/nse_symbol_isin_current.json').read_text(encoding='utf-8'))
    path = Path(get_settings().database_path).resolve()
    conn = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        stored = [dict(r) for r in conn.execute(
            'SELECT * FROM corporate_announcements WHERE event_date BETWEEN ? AND ? AND knowledge_date<=?',
            (START, END, AS_OF))]
        bmap, smap = {key(r): r for r in bulk}, {key(r): r for r in stored}
        missing = [r for k, r in smap.items() if k not in bmap]
        extra = [r for k, r in bmap.items() if k not in smap]
        ids = sorted({r['seq_id'] for r in extra})
        # One table scan, with a knowledge cutoff, checks alternate symbols/dates.
        matches = [dict(r) for r in conn.execute(
            'SELECT * FROM corporate_announcements WHERE knowledge_date<=? AND seq_id IN ('
            + ','.join('?' for _ in ids)+')', (AS_OF, *ids))]
        stored_by_id = defaultdict(list)
        for r in stored + matches:
            if r not in stored_by_id[r['seq_id']]:
                stored_by_id[r['seq_id']].append(r)
        raw_by_id = defaultdict(list)
        for r in raw['bulk_week']:
            raw_by_id[str(r['seq_id'])].append(r)
        universe = {}
        for symbol in sorted({r['symbol'] for r in extra}):
            price = [dict(r) for r in conn.execute(
                'SELECT series,count(*) AS rows,min(event_date) AS first_date,max(event_date) AS last_date '
                'FROM bhavcopy WHERE symbol=? AND knowledge_date<=? GROUP BY series', (symbol, AS_OF))]
            count = conn.execute('SELECT count(*) FROM corporate_announcements WHERE symbol=? AND knowledge_date<=?',
                                 (symbol, AS_OF)).fetchone()[0]
            universe[symbol] = dict(price_series=price, stored_announcement_rows=count,
                                    any_eq=any(r['series']=='EQ' for r in price))
        ledger = []
        for row in sorted(missing, key=key):
            candidates = raw_by_id[row['seq_id']]
            aliases = [r for r in candidates if rename_match(row, r, isin_map)]
            entry = dict(direction='missing_from_bulk_by_symbol_key', row=canonical(row),
                         classification='symbol_rename' if len(aliases)==1 else 'UNRESOLVED',
                         stored_recorded_at=row['recorded_at'])
            if len(aliases)==1:
                alias = aliases[0]
                entry['evidence'] = dict(bulk_symbol=alias['symbol'], bulk_isin=alias['sm_isin'],
                    old_symbol_isin=isin_map[row['symbol']], identical_non_symbol_fields=True,
                    attachment=alias.get('attchmntFile'), bulk_company_name=alias.get('sm_name'),
                    counterpart=facts([alias])[0])
            ledger.append(entry)
        for row in sorted(extra, key=key):
            item = next(r for r in raw_by_id[row['seq_id']] if r['symbol']==row['symbol'])
            candidates = stored_by_id[row['seq_id']]
            aliases = [r for r in candidates if rename_match(r, item, isin_map)]
            entry = dict(direction='missing_from_store_by_symbol_key', row=canonical(row))
            if len(aliases)==1:
                entry.update(classification='symbol_rename', evidence=dict(
                    stored_symbol=aliases[0]['symbol'], bulk_isin=item['sm_isin'],
                    old_symbol_isin=isin_map[aliases[0]['symbol']], identical_non_symbol_fields=True,
                    counterpart=canonical(aliases[0])))
            elif not candidates and not universe[row['symbol']]['any_eq'] and universe[row['symbol']]['stored_announcement_rows']==0:
                entry.update(classification='backfill_universe_exclusion', evidence=universe[row['symbol']] | dict(
                    same_seq_id_any_stored_symbol_or_date=0,
                    selector='ingest_announcements_full_history.py: distinct bhavcopy symbols with series=EQ'))
            else:
                entry.update(classification='UNRESOLVED', evidence=dict(same_id_rows=len(candidates)))
            ledger.append(entry)
        common = set(smap) & set(bmap)
        changed = [list(k) for k in sorted(common) if canonical(smap[k]) != canonical(bmap[k])]
        split = facts(raw['bulk_first']+raw['bulk_last'])
        request_report = json.loads((CAPTURE/'requests.json').read_text(encoding='utf-8'))
        report = dict(as_of=AS_OF, week=[START,END], requests=request_report,
            stored_rows=len(stored), stored_unique_keys=len(smap), bulk_rows=len(bulk),
            bulk_unique_keys=len(bmap), exact_shared_keys=len(common)-len(changed), changed_shared_keys=changed,
            missing_from_bulk=len(missing), missing_from_store=len(extra),
            classifications=dict(Counter(e['classification'] for e in ledger)),
            split_windows=dict(first=len(raw['bulk_first']),last=len(raw['bulk_last']),
                               identical_persisted_fields=signatures(split)==signatures(bulk)),
            original_capture_identical_persisted_fields=signatures(before)==signatures(bulk),
            sample_parity=compare(raw['bulk_week'], {s:raw[s] for s in ('HMT','MELSTAR')}),
            old_symbol_responses={s:len(raw[s]) for s in ('HEG','SANGINITA')},
            daily_counts=dict(sorted(Counter(r['event_date'] for r in bulk).items())),
            all_response_dates_within_week=all(START<=r['event_date']<=END for r in bulk),
            publication_text_matches_sort_timestamp=all(datetime.strptime(r['an_dt'],'%d-%b-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')==r['sort_date'] for r in raw['bulk_week']),
            store_comparison_sha256=hashlib.sha256('\n'.join(sorted(signatures(stored))).encode()).hexdigest(),
            isin_map_sha256=hashlib.sha256((ROOT/'data/raw/nse_symbol_isin_current.json').read_bytes()).hexdigest(),
            ledger=ledger)
        report['all_stored_rows_present_or_explained'] = not changed and all(
            e['classification']=='symbol_rename' for e in ledger if e['direction']=='missing_from_bulk_by_symbol_key')
        out=ROOT/'docs/desk/announcements_bulk_reconciliation.json'
        out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('ledger','requests')},indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
