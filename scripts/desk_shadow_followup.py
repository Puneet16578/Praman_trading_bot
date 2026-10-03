"""Foreground follow-up runner; reads the frozen replay, never a durable database."""
from __future__ import annotations
import os
for _variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[_variable] = '1'
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.costs import LoadedCostConfig
from desk.lib.rulebook import LoadedRulebook
from desk.shadow_analysis import SEED, REPLICATES
from desk.shadow_followup import (PERIODS, HEADROOM, cap_analysis, check_event,
                                  quintile_boundaries, volatility_analysis)
from desk.shadow_followup_report import report_markdown
from shared.market_time import market_today

BASE_COMMIT = '64ac2f13a3d419ce63b19b8c9c3b6e3e5b063af5'
PREREG_COMMIT = 'bbd5268'
PREREG_PATH = 'docs/desk/shadow_replay_followup_prereg.md'
SOURCE_PATHS = (PREREG_PATH, 'desk/shadow_followup.py', 'desk/shadow_followup_report.py',
                'scripts/desk_shadow_followup.py', 'tests/test_shadow_followup.py')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_records(path):
    rows = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            check_event(row)
            rows.append({key: row[key] for key in ('symbol', 'event_date', 'state', 'plan',
                         'execution', 'fill', 'adverse20', 'signed_return_90d')})
    return rows


def main():
    for name in SOURCE_PATHS:
        git('ls-files', '--error-unmatch', name)
    if git('diff', 'HEAD', '--', *SOURCE_PATHS):
        raise ValueError('Follow-up implementation and preregistration must be committed before running.')
    prereg = git('show', f'{PREREG_COMMIT}:{PREREG_PATH}')
    if (ROOT / PREREG_PATH).read_bytes().replace(b'\r\n', b'\n') != prereg:
        raise ValueError('The registered follow-up protocol has changed.')
    base_bytes = git('show', f'{BASE_COMMIT}:docs/desk/shadow_replay_results.json')
    original = json.loads(base_bytes)
    original_provenance = original['provenance']
    raw = ROOT / original_provenance['raw_path']
    raw_hash = sha256(raw)
    if raw_hash != original_provenance['raw_sha256']:
        raise ValueError('Frozen replay hash mismatch; no follow-up performed.')
    for name, digest in original_provenance['source_hashes'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError('An original replay input or source changed; inspect provenance before running.')
    rows = load_records(raw)
    catalogue = ROOT / 'data/processed/event_catalogue_loose_zscore_only.csv'
    with catalogue.open(encoding='utf-8') as stream:
        identities = sorted((r['symbol'], r['event_date']) for r in csv.DictReader(stream)
                            if PERIODS[0][1] <= r['event_date'] <= PERIODS[-1][2])
    if [(r['symbol'], r['event_date']) for r in rows] != identities:
        raise ValueError('Frozen event identities do not match the original catalogue.')
    if len(rows) != original_provenance['eligible_events']:
        raise ValueError('Frozen record count differs from the original provenance.')
    rb = LoadedRulebook.model_validate(original_provenance['rulebook']).rulebook
    costs = LoadedCostConfig.model_validate(original_provenance['costs']).costs
    boundaries = quintile_boundaries(rows)
    result = dict(boundaries_pct=boundaries.tolist(), periods={}, provenance=dict(
        code_commit=git('rev-parse', 'HEAD').decode().strip(), preregistration_commit=git('rev-parse', PREREG_COMMIT).decode().strip(),
        base_results_commit=BASE_COMMIT, run_date=market_today().isoformat(), seed=SEED,
        bootstrap_replicates=REPLICATES, decision_cap_fraction=HEADROOM,
        raw_sha256=raw_hash, base_results_git_blob_sha256=hashlib.sha256(base_bytes).hexdigest(),
        preregistration_sha256=hashlib.sha256(prereg).hexdigest(),
        source_hashes={name: sha256(ROOT / name) for name in SOURCE_PATHS},
        original_provenance=original_provenance,
        database_access='None: all measurements reuse immutable frozen replay records.'))
    for period, start, end in PERIODS:
        selected = [r for r in rows if start <= r['event_date'] <= end]
        expected = original['results'][period]['All candidates']
        for state in ('SCREEN_PASS', 'SCREEN_FAIL'):
            group = [r for r in selected if r['state'] == state]
            if len(group) != expected[state]['n'] or sum(r['fill'] is None for r in group) != expected[state]['no_fill']:
                raise ValueError('Original screening or fill denominator mismatch.')
        output = dict(n=len(selected), missing90=sum(r['signed_return_90d'] is None for r in selected), volatility={})
        for cohort, subset in [('All candidates', selected), ('Filled only', [r for r in selected if r['fill'] is not None])]:
            print(f'Volatility control: {period}, {cohort}, {len(subset)} events', flush=True)
            output['volatility'][cohort] = volatility_analysis(subset, boundaries)
        print(f'Cap sizes and fixed 90% variant: {period}', flush=True)
        output['caps'] = cap_analysis(selected, rb, costs)
        if output['caps']['unknown_inputs'] == 0 and output['caps']['any_cap']['baseline']['breaches'] != expected['SCREEN_PASS']['fill_cap_breaches']:
            raise ValueError('Original any-cap breach total was not reproduced.')
        result['periods'][period] = output
    output_dir = ROOT / 'docs/desk'
    (output_dir / 'shadow_replay_followup_results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    (output_dir / 'shadow_replay_followup_results.md').write_text(report_markdown(result), encoding='utf-8', newline='\n')
    print('Wrote shadow_replay_followup_results.md and .json', flush=True)


if __name__ == '__main__':
    main()
