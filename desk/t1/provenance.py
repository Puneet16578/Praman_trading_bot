"""Hash only the selected development payloads and bounded logical store rows."""
import hashlib
import json
import re
from pathlib import Path

from desk.t1.inputs import _ledger
from desk.t1.read_guard import READ_END, T1ReadRefused, check_date, select_range


STORE_QUERIES = {
    'calendar': ("SELECT DISTINCT event_date FROM bhavcopy WHERE event_date BETWEEN ? AND ? ORDER BY event_date",
                 ('2019-10-01', READ_END)),
    'eq_bars': ("SELECT symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price FROM bhavcopy "
                "WHERE series='EQ' AND event_date BETWEEN ? AND ? AND knowledge_date<=? ORDER BY event_date,symbol,row_id",
                ('2019-10-01', READ_END, READ_END)),
    'actions': ("SELECT symbol,action_type,event_date,knowledge_date,ratio_numerator,ratio_denominator,row_id "
                "FROM corporate_actions WHERE event_date<=? AND knowledge_date<=? ORDER BY knowledge_date,row_id",
                (READ_END, READ_END)),
}


def input_hashes(conn, raw: Path, isin: Path, *, end=READ_END):
    check_date(end)
    paths = set()
    expected = {}
    for folder in (raw, raw/'phase2'):
        ledger = folder/'requests.jsonl'
        if ledger.exists():
            paths.add(ledger)  # Metadata only; no price observations in the file-selection ledger.
        for entry in _ledger(ledger):
            label = entry['label']
            if entry.get('status') != 200 or not label.startswith(('history_', 'snapshot_')):
                continue
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', label)
            if len(dates) not in (1, 2):
                raise T1ReadRefused('Cannot bound source-file dates for hashing')
            if select_range(dates[0], dates[-1], end):
                path = folder/entry['file']
                file_dates = re.findall(r'\d{4}-\d{2}-\d{2}', path.name)
                if file_dates != dates:
                    raise T1ReadRefused('Source filename and declared dates differ')
                paths.add(path)
                expected[str(path.as_posix())] = entry['sha256']
    for path in isin.glob('cm_*.csv'):
        day = path.stem[3:]
        if select_range(day, day, end):
            paths.update((path, path.with_name(path.name+'.sha256.json')))
    files = {str(p.as_posix()): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    if any(files[p] != digest for p, digest in expected.items()):
        raise T1ReadRefused('Selected index payload differs from its recorded source hash')
    store = {}
    for name, (sql, args) in STORE_QUERIES.items():
        args = tuple(end if arg == READ_END else arg for arg in args)
        digest, count = hashlib.sha256(), 0
        for row in conn.execute(sql, args):
            digest.update((json.dumps(list(row), separators=(',', ':'), allow_nan=False)+'\n').encode())
            count += 1
        store[name] = dict(sha256=digest.hexdigest(), rows=count, sql=sql, parameters=args)
    return dict(files=files, logical_store_rows=store,
                hash_encoding='SHA-256; SQL rows as compact JSON arrays plus LF, in the recorded SQL order')
