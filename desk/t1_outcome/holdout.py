"""Frozen development constants and pre-outcome checks for the approved 2025 run."""
import hashlib
import json
from pathlib import Path

DEVELOPMENT_HASHES = {
    'docs/desk/t1_development_results_20261018.md': 'f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483',
    'docs/desk/t1_development_manifest_20261018.json': '3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b',
    'data/t1/development_20261018.json': '023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8',
    'data/t1/development_20261018.started.json': '1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377',
}
THIRD_REHEARSAL = 'data/t1/rehearsal_20261018T105905Z.json'
EXECUTION_METADATA = {'code_commit', 'source_sha256', 'seconds', 'peak_memory_bytes'}


def development_hashes(root):
    hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in DEVELOPMENT_HASHES}
    if hashes != DEVELOPMENT_HASHES:
        raise ValueError('Locked development artifacts changed; stop')
    return hashes


def locked_constants(root):
    development_hashes(root)
    result = json.loads((root/'data/t1/development_20261018.json').read_text(encoding='utf-8'))
    return list(result['bounds']), {int(q): value for q, value in result['weights'].items()}


def source_hashes(root):
    paths = [*(root/'desk/t1').glob('*.py'), *(root/'desk/t1_outcome').glob('*.py'),
             root/'scripts/t1_holdout.py', root/'scripts/t1_rehearsal.py', root/'desk/outcome_firewall.py',
             root/'docs/desk/t1_market_context_prereg.md']
    return {str(p.relative_to(root).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def check_development_rehearsal(root, path):
    previous = json.loads((root/THIRD_REHEARSAL).read_text(encoding='utf-8'))
    current = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in (previous.keys() | current.keys()) - EXECUTION_METADATA:
        if previous.get(key) != current.get(key):
            raise ValueError(f'Development rehearsal mismatch: {key}; stop')
    for name, digest in current['source_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Code changed after development rehearsal; stop')
    return dict(reference=THIRD_REHEARSAL, current=str(path), analytical_fields_identical=True,
                current_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                prior_seconds=previous['seconds'], current_seconds=current['seconds'],
                prior_peak_memory=previous['peak_memory_bytes'], current_peak_memory=current['peak_memory_bytes'])


def check_holdout_calendar(panel, period):
    import numpy as np
    dates = [panel.sessions[i] for i in np.flatnonzero(period == 'holdout_2025')]
    purged = [panel.sessions[i] for i in np.flatnonzero(period == 'holdout_censored')]
    if not dates or len(purged) != 20 or panel.sessions[-1] != '2025-12-31':
        raise ValueError('Incomplete hold-out calendar or purge; stop')
    if not all('2025-01-01' <= day <= '2025-12-31' for day in dates + purged):
        raise ValueError('Hold-out decision/purge outside 2025; stop')
    for i in np.flatnonzero(period == 'holdout_2025'):
        if panel.sessions[i+20] > '2025-12-31':
            raise ValueError('Hold-out outcome window outside 2025; stop')
    return purged


def render_rehearsal(report):
    lines = ['# T1 2025 random-label rehearsal', '',
        'No real outcomes read. The reader and firewall entry points raised throughout the rehearsal.',
        '2025 PARTIALLY EXPOSED. Decisions and outcome windows within 2025; warm-up before 2025 permitted.',
        'Read ceiling 2025-12-31; fixed development boundaries and weights; registered settings unchanged.', '',
        f"Runtime seconds: {report['seconds']}; peak working set bytes: {report['peak_memory_bytes']}.",
        f"Decision sessions: {report['development_sessions']} ({report['first_session']} to {report['last_session']}).",
        f"Eligible stock-days: {report['eligible_stock_days']}; identity exclusions: {report['identity_excluded']}.",
        f"Complete windows: {report['complete_windows']} ({report['complete_windows']/report['eligible_stock_days']:.10%}).",
        f"Purged sessions: {report['purged_sessions']}.",
        f"Locked boundaries: {report['quintile_bounds']}.",
        f"Locked weights: {report['locked_weights']}; used weights: {report['weights']}; exact equality verified.", '',
        '| Variant | Coverage | Smallest valid cell | Fewest dates | Spells | Usable draws | Unusable draws |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for v, r in report['variants'].items():
        lines.append(f"| {v} | {r['coverage']:.10%} | {min(c['valid'] for c in r['cells'].values())} | "
                     f"{min(c['dates'] for c in r['cells'].values())} | {r['spells']} | {r['usable_draws']} | {r['unusable_draws']} |")
    for v, r in report['variants'].items():
        lines += ['', f'## {v}', '', '| Cell | Candidates | Valid windows | Dates |', '|---|---:|---:|---:|']
        for name, cell in r['cells'].items():
            lines.append(f"| {name} | {cell['candidates']} | {cell['valid']} | {cell['dates']} |")
        lines += ['', '| State | Stock-days | Complete windows | Share |', '|---|---:|---:|---:|']
        for name, a in r['availability'].items():
            share = f"{a['complete_windows']/a['stock_days']:.10%}" if a['stock_days'] else 'unavailable'
            lines.append(f"| {name} | {a['stock_days']} | {a['complete_windows']} | {share} |")
        lines += ['', f"Input-only failures: {r['input_only_failures']}"]
    lines += ['', '## Development regression and artifact integrity', '', '```json',
              json.dumps({k: report[k] for k in ('development_regression', 'development_hashes_before',
                                                'development_hashes_after')}, indent=2), '```', '']
    return '\n'.join(lines)
