"""Approved 2025 rehearsal and once-only evaluation. No automatic retries.

python -B scripts/t1_holdout.py rehearse --development-rehearsal PATH
python -B scripts/t1_holdout.py evaluate
"""
from __future__ import annotations
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.t1 import features as F, inputs
from desk.t1.panel import load_panel, snapshot_identities
from desk.t1.provenance import input_hashes
from desk.t1.read_guard import HOLDOUT_END, holdout_reads
from desk.t1_outcome import development as D, holdout as H
from desk.t1_outcome.rehearsal import REHEARSAL_RATE, REHEARSAL_SEED, outcomes_sealed, rehearse
from scripts.t1_rehearsal import peak_memory_bytes
from shared.sqlite_readonly import open_readonly

SETTINGS = dict(weekends='exclude', coverage_numerator='state_known', usable='computable_with_sample_minimums',
                method='linear', replicates=2000, seed=20261001, blocks={'V1':60, 'V2':60, 'V3':20})


def write_new(path, value):
    with path.open('x', encoding='utf-8') as f:
        f.write(value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False))


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('rehearse', 'evaluate'))
    parser.add_argument('--development-rehearsal', type=Path)
    args = parser.parse_args(argv)
    real = args.mode == 'evaluate'
    reference_path = ROOT/'data/t1/holdout_rehearsal_2025.json'
    target = ROOT/'docs/desk/t1_holdout_results_2025.md'
    manifest_path = ROOT/'docs/desk/t1_holdout_manifest_2025.json'
    machine = ROOT/'data/t1/holdout_2025.json'
    marker = ROOT/'data/t1/holdout_2025.started.json'
    if real:
        if git('branch', '--show-current') != 'master' or git('status', '--porcelain'):
            raise RuntimeError('Hold-out evaluation requires clean master')
        if any(p.exists() for p in (target, manifest_path, machine, marker)):
            raise FileExistsError('A hold-out attempt already exists; stop, no retry')
        reference = json.loads(reference_path.read_text(encoding='utf-8'))
        if reference['source_sha256'] != H.source_hashes(ROOT) or reference['settings'] != SETTINGS:
            raise ValueError('Code/settings changed after hold-out rehearsal; stop')
        regression = H.check_development_rehearsal(ROOT, reference['development_regression']['current'])
    else:
        if not args.development_rehearsal:
            parser.error('--development-rehearsal is required for rehearsal')
        if reference_path.exists():
            raise FileExistsError('Hold-out rehearsal already exists; no overwrite')
        regression = H.check_development_rehearsal(ROOT, args.development_rehearsal)
    before = H.development_hashes(ROOT)
    bounds, weights = H.locked_constants(ROOT)
    print('Locked development weights:', weights, 'Hold-out weights:', weights, 'identical:', True, flush=True)
    started = datetime.now(timezone.utc).isoformat()
    manifest = dict(code_commit=git('rev-parse', 'HEAD'), started_at=started, read_end=HOLDOUT_END,
                    decision_period=['2025-01-01', HOLDOUT_END], settings=SETTINGS,
                    development_hashes_before=before, locked_weights=weights, used_weights=dict(weights),
                    locked_quintile_bounds=bounds, source_sha256=H.source_hashes(ROOT),
                    development_regression=regression)
    if real:
        write_new(marker, dict(code_commit=manifest['code_commit'], started_at=started))
    clock = time.perf_counter()
    with holdout_reads(), (nullcontext() if real else outcomes_sealed()):
        conn = open_readonly(ROOT/'data/processed/praman.db')
        try:
            conn.execute('BEGIN')
            raw, isin = ROOT/'data/raw/t1_sources', ROOT/'data/raw/isin_snapshots'
            manifest['inputs'] = json.loads(json.dumps(input_hashes(conn, raw, isin, end=HOLDOUT_END)))
            if real:
                if manifest['inputs'] != reference['inputs']:
                    raise ValueError('Inputs differ from hold-out rehearsal; stop')
                write_new(manifest_path, manifest)  # Before any real-outcome call.
            index, mismatches = inputs.load(raw, end=HOLDOUT_END)
            if mismatches:
                raise ValueError('Index source mismatch; stop')
            panel = load_panel(conn, index, snapshot_identities(isin, end=HOLDOUT_END), end=HOLDOUT_END)
        finally:
            conn.close()
        loaded = time.perf_counter()
        out, cause = F.compute(panel), F.exclusion_causes(panel)
        period = F.periods(panel.sessions, panel.forward_sessions)
        purged = H.check_holdout_calendar(panel, period)
        featured = time.perf_counter()
        if real:
            selected = period == 'holdout_2025'
            if (int((cause[selected] == '').sum()) != reference['eligible_stock_days'] or
                int((cause[selected] == 'identity_unknown').sum()) != reference['identity_excluded'] or
                int(selected.sum()) != reference['development_sessions'] or purged != reference['purged_sessions']):
                raise ValueError('Hold-out population/calendar differs from rehearsal; stop')
            result = D.evaluate(panel, out, cause, period, bounds,
                                evaluated_period='holdout_2025', locked_weights=weights)
            manifest['development_hashes_after'] = H.development_hashes(ROOT)
            write_new(machine, result)
            write_new(target, D.render(result, manifest))
            print('Locked hold-out results:', target)
            for v, r in result['variants'].items():
                print(v, r['verdict'], 'difference', r['difference'], 'family', r['intervals']['family'],
                      'positive_quintiles', r['positive_quintiles'], 'coverage', r['coverage'],
                      'usable_draws', r['intervals']['usable_draws'])
        else:
            result = rehearse(panel, out, cause, period, bounds, seed=REHEARSAL_SEED, rate=REHEARSAL_RATE,
                              usable=SETTINGS['usable'], method=SETTINGS['method'],
                              coverage_numerator=SETTINGS['coverage_numerator'],
                              evaluated_period='holdout_2025', locked_weights=weights)
            end = time.perf_counter()
            result.update(manifest, kind='holdout_random_labels', outcomes='none read; random labels',
                          label_seed=REHEARSAL_SEED, label_rate=REHEARSAL_RATE, quintile_bounds=bounds,
                          purged_sessions=purged, development_hashes_after=H.development_hashes(ROOT),
                          seconds=dict(load=round(loaded-clock,1), features=round(featured-loaded,1),
                                       rehearsal=round(end-featured,1), total=round(end-clock,1)),
                          peak_memory_bytes=peak_memory_bytes())
            write_new(reference_path, result)
            write_new(ROOT/'docs/desk/t1_holdout_rehearsal_2025.md', H.render_rehearsal(result))
            print('Saved hold-out rehearsal:', reference_path)
            print(H.render_rehearsal(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
