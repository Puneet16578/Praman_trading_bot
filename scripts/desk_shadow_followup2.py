"""Foreground runner for the preregistered fixed entry-limit experiment."""
import os
for _name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[_name] = '1'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.costs import LoadedCostConfig
from desk.lib.rulebook import LoadedRulebook
from desk.lib.store import PRODUCTION_DB_PATH, max_recorded_at
from desk.research_snapshot import SnapshotQueries
from desk.shadow_followup import PERIODS, check_event
from desk.shadow_followup2 import limit_fill, analyze, report_markdown
from scripts.desk_shadow_followup import load_records, sha256, git
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly
from shared.market_time import market_today
from src.bitemporal.guard import latest_as_of

PREREG = 'docs/desk/shadow_replay_followup2_prereg.md'
SOURCES = (PREREG, 'desk/shadow_followup2.py', 'scripts/desk_shadow_followup2.py',
           'tests/test_shadow_followup2.py', 'desk/shadow_followup.py', 'desk/risk/officer.py')


def next_session_bar(conn,row,provenance):
    check_event(row)
    execution=row['execution']
    day=execution['fill_date'] if execution else None
    bars=latest_as_of(conn,'bhavcopy',provenance['run_date'],symbol=row['symbol'],event_date=day) if day else []
    bars=sorted((r for r in bars if r['series'] in ('EQ','BE','BZ')),
                key=lambda r:('EQ','BE','BZ').index(r['series']))
    return bars[0] if bars else {}


def main():
    for name in SOURCES:
        git('ls-files', '--error-unmatch', name)
    if git('diff', 'HEAD', '--', *SOURCES):
        raise ValueError('Commit tested experiment implementation before running.')
    prereg = git('show', 'cb89f96:'+PREREG)
    if (ROOT/PREREG).read_bytes().replace(b'\r\n', b'\n') != prereg:
        raise ValueError('Registered limit protocol changed.')
    base_path = ROOT/'docs/desk/shadow_replay_results.json'
    base = json.loads(base_path.read_text(encoding='utf-8'))['provenance']
    raw = ROOT/base['raw_path']
    if sha256(raw) != base['raw_sha256']:
        raise ValueError('Corrected replay hash mismatch.')
    rows = [r for r in load_records(raw) if r['state'] == 'SCREEN_PASS']
    rb, costs = LoadedRulebook.model_validate(base['rulebook']).rulebook, LoadedCostConfig.model_validate(base['costs']).costs
    provenance = dict(code_commit=git('rev-parse','HEAD').decode().strip(),
        preregistration_commit=git('rev-parse','cb89f96').decode().strip(),
        run_date=market_today().isoformat(), seed=20261001, bootstrap_replicates=2000,
        raw_sha256=base['raw_sha256'], base_results_sha256=sha256(base_path),
        source_hashes={name:sha256(ROOT/name) for name in SOURCES},
        original_provenance=base, limit_atr_multiple=0.5)
    observed = ROOT/'data/processed/desk_shadow_followup2_execution.jsonl'
    with tempfile.TemporaryDirectory(prefix='praman_limit_') as temp:
        snapshot = Path(temp)/'praman.sqlite'
        online_backup(PRODUCTION_DB_PATH, snapshot)
        provenance['snapshot_sha256'] = sha256(snapshot)
        conn = open_readonly(snapshot)
        try:
            if max_recorded_at(conn) != base['praman_watermark']:
                raise ValueError('Store watermark differs from corrected replay.')
            cached = SnapshotQueries(conn)
            last = None
            with observed.open('w', encoding='utf-8', newline='\n') as stream:
                for i, row in enumerate(rows, 1):
                    check_event(row)
                    if row['symbol'] != last:
                        cached.cache.clear()
                        last = row['symbol']
                    execution = row['execution']
                    day = execution['fill_date'] if execution else None
                    bar = next_session_bar(cached,row,base)
                    opening, low = bar.get('open_price'), bar.get('low_price')
                    if not isinstance(row['plan'].get('quantity'), int) or row['plan']['quantity'] <= 0:
                        raise ValueError('Corrected pass lacks a positive frozen quantity.')
                    usable_open = isinstance(opening, (float, int)) and opening > 0
                    if (row['fill'] is not None and opening != row['fill']) or (row['fill'] is None and usable_open):
                        raise ValueError('Next opening differs from corrected frozen observation.')
                    row['baseline'] = dict(fill=row['fill'], status='FILL_OPEN' if row['fill'] is not None else 'UNKNOWN')
                    row['limit'] = limit_fill(row['plan'], opening, low)
                    evidence = dict(symbol=row['symbol'], event_date=row['event_date'], next_session=day,
                        open=opening, low=low, series=bar.get('series'), knowledge_date=bar.get('knowledge_date'),
                        row_id=bar.get('row_id'), quantity=row['plan']['quantity'], baseline=row['baseline'], limit=row['limit'])
                    stream.write(json.dumps(evidence, sort_keys=True)+'\n')
                    if i % 5000 == 0 or i == len(rows):
                        print(f'Execution observations {i}/{len(rows)}', flush=True)
        finally:
            conn.close()
    provenance['execution_path'] = observed.relative_to(ROOT).as_posix()
    provenance['execution_sha256'] = sha256(observed)
    result = dict(provenance=provenance, periods={})
    for name, start, end in PERIODS:
        print('Bootstrap '+name, flush=True)
        result['periods'][name] = analyze([r for r in rows if start<=r['event_date']<=end], rb, costs)
    output = ROOT/'docs/desk/shadow_replay_followup2_results'
    output.with_suffix('.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
    output.with_suffix('.md').write_text(report_markdown(result), encoding='utf-8', newline='\n')
    print('Wrote followup2 results.', flush=True)


if __name__ == '__main__':
    main()
