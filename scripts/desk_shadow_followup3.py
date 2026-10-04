"""Foreground runner for preregistered follow-up 3 (b2df2a2): size against the limit price."""
import os
for _name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[_name] = '1'
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.lib.costs import LoadedCostConfig
from desk.lib.rulebook import LoadedRulebook
from desk.shadow_followup import PERIODS
from desk.shadow_followup3 import analyze, prepare, report_markdown, verdict
from scripts.desk_shadow_followup import git, load_records, sha256
from shared.market_time import market_today

PREREG = 'docs/desk/shadow_replay_followup3_prereg.md'
PREREG_COMMIT = 'b2df2a2'
SOURCES = (PREREG, 'desk/shadow_followup3.py', 'scripts/desk_shadow_followup3.py', 'tests/test_shadow_followup3.py',
           'desk/shadow_followup.py', 'desk/shadow_followup2.py', 'desk/risk/officer.py')


def main():
    for name in SOURCES:
        git('ls-files', '--error-unmatch', name)
    if git('diff', 'HEAD', '--', *SOURCES):
        raise ValueError('Commit the tested implementation before running.')
    if (ROOT / PREREG).read_bytes().replace(b'\r\n', b'\n') != git('show', f'{PREREG_COMMIT}:{PREREG}'):
        raise ValueError('The registered follow-up 3 protocol has changed.')
    base_path = ROOT / 'docs/desk/shadow_replay_results.json'
    base = json.loads(base_path.read_text(encoding='utf-8'))['provenance']
    raw = ROOT / base['raw_path']
    if sha256(raw) != base['raw_sha256']:
        raise ValueError('Corrected replay hash mismatch.')
    fu2_path = ROOT / 'docs/desk/shadow_replay_followup2_results.json'
    fu2 = json.loads(fu2_path.read_text(encoding='utf-8'))['provenance']
    execution_path = ROOT / fu2['execution_path']
    if sha256(execution_path) != fu2['execution_sha256'] or fu2['raw_sha256'] != base['raw_sha256']:
        raise ValueError('Follow-up 2 execution evidence does not match its recorded provenance.')
    rb = LoadedRulebook.model_validate(base['rulebook']).rulebook
    costs = LoadedCostConfig.model_validate(base['costs']).costs
    passes = [r for r in load_records(raw) if r['state'] == 'SCREEN_PASS']
    with execution_path.open(encoding='utf-8') as stream:
        executions = [json.loads(line) for line in stream]
    rows = prepare(passes, executions, rb, costs)
    result = dict(provenance=dict(
        code_commit=git('rev-parse', 'HEAD').decode().strip(),
        preregistration_commit=git('rev-parse', PREREG_COMMIT).decode().strip(),
        run_date=market_today().isoformat(), seed=20261001, bootstrap_replicates=2000,
        raw_sha256=base['raw_sha256'], execution_path=fu2['execution_path'], execution_sha256=fu2['execution_sha256'],
        followup2_results_sha256=sha256(fu2_path), base_results_sha256=sha256(base_path),
        source_hashes={name: sha256(ROOT / name) for name in SOURCES}, passes=len(rows),
        command='python -u scripts/desk_shadow_followup3.py', database_access='None: frozen artifacts only.'),
        periods={})
    for name, start, end in PERIODS:
        print('Bootstrap ' + name, flush=True)
        result['periods'][name] = analyze([r for r in rows if start <= r['event_date'] <= end], rb, costs)
    result['verdict'] = verdict(result)
    out = ROOT / 'docs/desk/shadow_replay_followup3_results'
    out.with_suffix('.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    out.with_suffix('.md').write_text(report_markdown(result), encoding='utf-8', newline='\n')
    print(json.dumps(result['verdict']), flush=True)
    print('Wrote followup3 results.', flush=True)


if __name__ == '__main__':
    main()
