"""Approved one-shot development evaluation. No retry or hold-out entry point.

Run only after the third rehearsal matched, on clean master. A persistent attempt
marker prevents an accidental second run, including after a crash.
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desk.t1 import features as F, inputs
from desk.t1.panel import load_panel, snapshot_identities
from desk.t1.provenance import input_hashes
from desk.t1.read_guard import READ_END, check_date
from desk.t1_outcome.development import evaluate, render
from shared.sqlite_readonly import open_readonly


def main():
    def git(*args):
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if git('branch', '--show-current') != 'master' or git('status', '--porcelain'):
        raise RuntimeError('Development evaluation requires clean master')
    check_date(READ_END)
    target = ROOT/'docs/desk/t1_development_results_20261018.md'
    manifest_path = ROOT/'docs/desk/t1_development_manifest_20261018.json'
    machine = ROOT/'data/t1/development_20261018.json'
    if any(p.exists() for p in (target, manifest_path, machine)):
        raise FileExistsError('An evaluation record already exists; no automatic rerun')
    marker = ROOT/'data/t1/development_20261018.started.json'
    commit = git('rev-parse', 'HEAD')
    started = datetime.now(timezone.utc).isoformat()
    with marker.open('x', encoding='utf-8') as f:
        json.dump(dict(code_commit=commit, started_at=started), f)
    conn = open_readonly(ROOT/'data/processed/praman.db')
    try:
        conn.execute('BEGIN')  # One consistent read-only view for the hashes and panel.
        raw, isin = ROOT/'data/raw/t1_sources', ROOT/'data/raw/isin_snapshots'
        manifest = dict(code_commit=commit, started_at=started, read_end=READ_END,
            preregistration_commit=git('log', '-1', '--format=%H', '--', 'docs/desk/t1_market_context_prereg.md'),
            settings=dict(weekends='exclude', coverage_numerator='state_known', usable='computable_with_sample_minimums',
                          method='linear', replicates=2000, seed=20261001, blocks={'V1':60,'V2':60,'V3':20}),
            inputs=input_hashes(conn, raw, isin))
        with manifest_path.open('x', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        index, mismatches = inputs.load(raw)
        if mismatches:
            raise RuntimeError('Index source mismatch; evaluation stopped')
        panel = load_panel(conn, index, snapshot_identities(isin), end=READ_END)
    finally:
        conn.close()
    out = F.compute(panel)
    cause = F.exclusion_causes(panel)
    period = F.periods(panel.sessions, panel.forward_sessions)
    bounds = F.quintile_bounds(out['atr_pct'], cause, period)
    reference = json.loads((ROOT/'data/t1/rehearsal_20261018T105905Z.json').read_text(encoding='utf-8'))
    dev = period == 'development'
    if (int((cause[dev] == '').sum()) != reference['eligible_stock_days'] or
        int((cause[dev] == 'identity_unknown').sum()) != reference['identity_excluded'] or
        bounds != reference['quintile_bounds'] or int(dev.sum()) != reference['development_sessions']):
        raise RuntimeError('Input population/bounds differ from the matched third rehearsal')
    # First and only real-outcome call, through the existing reader and firewall.
    result = evaluate(panel, out, cause, period, bounds)
    with machine.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, allow_nan=False)
    with target.open('x', encoding='utf-8') as f:
        f.write(render(result, manifest))
    print(f'Locked development results: {target}')
    for variant, r in result['variants'].items():
        print(variant, r['verdict'], 'difference', r['difference'], 'family', r['intervals']['family'],
              'positive_quintiles', r['positive_quintiles'], 'coverage', r['coverage'],
              'usable_draws', r['intervals']['usable_draws'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
