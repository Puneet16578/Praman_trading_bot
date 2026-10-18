"""The approved development evaluation and full tables; callers supply bounded inputs.

No store or network access here. Real labels enter only through the existing reader.
Settings are those locked in addenda 1-3, not selected from results.
"""
from __future__ import annotations

from collections import Counter
import numpy as np

from desk.t1 import features as F
from desk.t1_outcome import reader as R, contrasts as C, uncertainty as U


def counts(base, mask):
    valid = mask & np.isfinite(base['outcome'])
    n = int(valid.sum())
    adverse = int((base['outcome'][valid] == 1).sum())
    return dict(candidates=int(mask.sum()), valid=n, missing=int(mask.sum())-n,
                dates=int(np.unique(base['date_idx'][valid]).size), adverse=adverse,
                rate=adverse/n if n else None)


def evaluate(panel, out, cause, period, bounds, *, evaluated_period='development', locked_weights=None):
    """Call the guarded reader once, then evaluate all three preregistered contrasts."""
    if evaluated_period not in R.PERIODS:
        raise R.OutcomeReadRefused('Unknown evaluation period')
    if evaluated_period == 'holdout_2025' and locked_weights is None:
        raise ValueError('Hold-out requires locked development weights')
    dev = np.flatnonzero(period == evaluated_period)
    if panel.sessions[-1] > R.PERIODS[evaluated_period][1]:
        raise R.OutcomeReadRefused('Panel extends beyond evaluation period')
    eligible = cause[dev] == ''
    date_idx, cols = np.nonzero(eligible)
    decisions = {panel.sessions[i]: [panel.symbols[j] for j in np.flatnonzero(cause[i] == '')] for i in dev}
    labels = R.read_adverse20(panel, decisions, period=evaluated_period)
    base = dict(date_idx=date_idx, quintile=F.quintile(out['atr_pct'][dev][eligible], bounds),
                outcome=np.concatenate([labels[panel.sessions[i]] for i in dev]))
    states = {'V1': out['v1_adverse'][dev][date_idx], 'V2': out['v2_adverse'][dev][date_idx],
              'V3': out['v3_negative'][dev][eligible]}
    weights = C.baseline_weights(base['quintile']) if locked_weights is None else dict(locked_weights)
    draws = U.period_draws(len(dev))
    purged = 'development_purged' if evaluated_period == 'development' else 'holdout_censored'
    report = dict(period=evaluated_period, first=panel.sessions[dev[0]], last=panel.sessions[dev[-1]],
                  decision_sessions=len(dev), purged_sessions=[panel.sessions[i] for i in
                  np.flatnonzero(period == purged)], eligible=len(date_idx),
                  identity_excluded=int((cause[dev] == 'identity_unknown').sum()), bounds=bounds,
                  weights=weights, baseline={q: counts(base, base['quintile'] == q) for q in C.QUINTILES},
                  variants={}, descriptive={}, exclusions={})
    for year in sorted({panel.sessions[i][:4] for i in dev}):
        idx = [i for i in dev if panel.sessions[i][:4] == year]
        stored = np.isfinite(panel.raw_close[idx])
        report['exclusions'][year] = dict(Counter(cause[idx][stored].tolist()))
    for name in ('share_above50', 'share_above200', 'net_breadth', 'new_high_rate', 'new_low_rate',
                 'dispersion', 'atr_pct', 'rel_ew_1', 'rel_ew_5', 'rel_ew_20', 'rel_ew_60',
                 'rel_n50_1', 'rel_n50_5', 'rel_n50_20', 'rel_n50_60'):
        values = out[name][dev]
        if values.ndim == 2:
            values = values[eligible]
        known = values[np.isfinite(values)]
        report['descriptive'][name] = dict(total=int(values.size), known=int(known.size),
            distribution=[float(x) for x in np.percentile(known, [0, 25, 50, 75, 100], method='linear')]
            if known.size else None)
    # Descriptive NIFTY 50 trend, using the existing D-1 close and its inclusive average.
    ok = np.isfinite(out['n50_prev'][dev]) & np.isfinite(out['n50_sma200_prev'][dev])
    report['nifty50_trend'] = dict(known=int(ok.sum()), unknown=int((~ok).sum()),
        below_average=int((ok & (out['n50_prev'][dev] < out['n50_sma200_prev'][dev])).sum()))
    for variant, state in states.items():
        rows = dict(base, state=state)
        table = C.cells(rows)
        difference = C.standardized(table, weights)
        replicates = U.replicate_differences(rows, weights, draws[U.BLOCK[variant]],
                                           usable='computable_with_sample_minimums')
        intervals = U.intervals(replicates, method='linear')
        spell_list = None
        if variant in C.SPELL_VARIANTS:
            values = out[variant.lower()+'_adverse'][dev]
            spell_list = F.spells([(panel.sessions[i], None if not np.isfinite(v) else bool(v))
                                  for i, v in zip(dev, values)])
        coverage = C.coverage(rows, numerator='state_known')
        verdict = C.decide(variant, table=table, standardized_difference=difference, cover=coverage,
                          usable_draws=intervals['usable_draws'], family_interval=intervals['family'] or (np.nan, np.nan),
                          spells_in_period=len(spell_list) if spell_list is not None else None)
        matched = C.matched_baseline(rows, weights)
        matched['coverage'] = matched['rows']/len(date_idx)
        paired = U.replicate_baseline(rows, weights, draws[U.BLOCK[variant]])
        paired[~np.isfinite(replicates)] = np.nan
        matched['intervals'] = U.intervals(paired, method='linear')
        matched['cells'] = {q: counts(base, np.isfinite(state) & (base['quintile'] == q)
                                     & np.isfinite(base['outcome'])) for q in C.QUINTILES}
        report['variants'][variant] = dict(
            verdict={'SUCCESS': 'PASS', 'NOT_SUCCESS': 'FAIL', 'INCONCLUSIVE': 'INCONCLUSIVE'}[verdict['result']],
            reasons=verdict['reasons'], difference=difference, intervals=intervals,
            positive_quintiles=C.positive_quintiles(table), coverage=coverage, spells=spell_list,
            block=U.BLOCK[variant], unusable_draws=len(replicates)-intervals['usable_draws'], matched=matched,
            cells={f'{s}:{q}': table[(s,q)] for s in C.STATES for q in C.QUINTILES},
            differences={q: table[('difference',q)] for q in C.QUINTILES},
            ratios={q: table[('ratio',q)] for q in C.QUINTILES},
            availability={name: counts(base, mask) for name, mask in
                          [('adverse', state == 1), ('other', state == 0), ('unknown', ~np.isfinite(state))]})
    if evaluated_period == 'holdout_2025':
        for result in report['variants'].values():
            result['verdict'] = {'PASS': 'replication success', 'FAIL': 'not met',
                                 'INCONCLUSIVE': 'INCONCLUSIVE'}[result['verdict']]
    return report


def render(report, manifest):
    """Render all preregistered tables before the caller locks the result file."""
    import json
    holdout = report['period'] == 'holdout_2025'
    def value(x, scale=1):
        return 'unavailable' if x is None else f'{x*scale:.8f}'
    def band(x):
        return 'unavailable' if x is None else f'[{value(x[0],100)}, {value(x[1],100)}]'
    def cell_line(label, c):
        return f"| {label} | {c['candidates']} | {c['valid']} | {c['missing']} | {c['dates']} | {c['adverse']} | {value(c['rate'],100)} |"
    header = ['| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |',
              '|---|---:|---:|---:|---:|---:|---:|']
    scope = ('Hold-out only: decisions and outcome windows inside 2025; pre-2025 warm-up reads allowed. '
             '**2025: PARTIALLY EXPOSED**; prior shadow studies viewed aggregate adverse-move rates, '
             'but no trading model was fitted or selected on it. No input or outcome payload after '
             '2025-12-31 was opened for this run.' if holdout else
        'Development only: 2019-10-01 through 2024-12-31. **2025: PARTIALLY EXPOSED**; '
        'prior shadow studies viewed aggregate adverse-move rates, but no trading model was fitted or selected on it. '
        'No 2025 input or outcome payload was opened for this run and no hold-out evaluation was performed.')
    lines = ['# T1 locked 2025 hold-out results' if holdout else '# T1 locked development results (18 October 2026)', '',
        scope, '',
        f"Code commit before the run: `{manifest['code_commit']}`. Input hashes were recorded before real outcome access;",
        'the complete manifest is reproduced below. Results are locked; no threshold or setting was changed after outcome access.', '',
        'Timing ASSUMPTIONS: same-session EQ bars subject to their stored knowledge dates; index/VIX through D-1; '
        'ISIN snapshots from S+1, ignoring October download dates. Missing inputs remain missing, '
        'including the five late-known sessions and 2022-08-08. Weekend sessions excluded everywhere.', '',
        f"Eligible stock-days: {report['eligible']}; identity-exclusion category: **{report['identity_excluded']}**.",
        'Identity exclusions include rows that also fail fund/ATR conditions; they are not all otherwise eligible equities.',
        f"Decision sessions: {report['decision_sessions']}, {report['first']} to {report['last']}.",
        f"Purged sessions ({len(report['purged_sessions'])}): {', '.join(report['purged_sessions'])}.",
        'Purged bars complete the final windows but supply no decisions or bootstrap dates. Empty dates remain in blocks.', '',
        'Features and adverse20 share price inputs and the decision-close anchor. Volatility quintiles reduce imbalance '
        'but do not remove mechanical coupling or establish causation. These are historical conditional associations, '
        'not profitability, calibration, readiness or permission to change live risk limits.', '',
        '## Frozen quintiles and baseline V0', '',
        f"ATR% linear quintile boundaries: {report['bounds']}. Ties go upward.",
        f"Development candidate weights (including missing outcomes): {report['weights']}.", ''] + header
    for q, c in report['baseline'].items():
        lines.append(cell_line(f'V0 q{q}', c))
    lines += ['', '## Preregistered decisions', '',
        'All differences and interval endpoints below are percentage points. Family intervals are 98.333333% '
        '(three contrasts); 95% intervals are descriptive. Bootstrap: 2,000 draws, seed 20261001, '
        '60-session blocks for V1/V2 and 20 for V3; linear percentiles. Every usable draw meets all cell sample minimums.', '',
        '| Variant | Verdict | Standardised difference pp | Family interval pp | 95% interval pp | Positive quintiles | State coverage | Usable / unusable | Spells |',
        '|---|---|---:|---|---|---:|---:|---|---|']
    for v, r in report['variants'].items():
        lines.append(f"| {v} | {r['verdict']} | {value(r['difference'],100)} | {band(r['intervals']['family'])} | "
                     f"{band(r['intervals']['descriptive_95'])} | {r['positive_quintiles']}/5 | {value(r['coverage'],100)}% | "
                     f"{r['intervals']['usable_draws']} / {r['unusable_draws']} | {len(r['spells']) if r['spells'] is not None else 'not required'} |")
    for v, r in report['variants'].items():
        lines += ['', f'## {v}: full cells and comparisons', '', 'Decision reasons: '+('; '.join(r['reasons']) or 'All preregistered criteria met.'), ''] + header
        for key, c in r['cells'].items():
            state, q = key.split(':')
            lines.append(cell_line(f"{'adverse' if state=='1.0' else 'other'} q{q}", c))
        lines += ['', '| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |', '|---|---:|---:|---|']
        for q in C.QUINTILES:
            d = r['differences'][q]
            lines.append(f"| {q} | {value(d,100)} | {value(r['ratios'][q])} | {d is not None and d>0} |")
        lines += ['', 'Outcome availability by state (no availability threshold):', ''] + header
        for state, c in r['availability'].items():
            lines.append(cell_line(state, c))
        m = r['matched']
        lines += ['', f"Matched V0: {m['rows']} rows, {value(m['coverage'],100)}% of eligible stock-days;",
                  f"standardised rate {value(m['standardized_rate'],100)}%; descriptive 95% {band(m['intervals']['descriptive_95'])};",
                  f"family {band(m['intervals']['family'])}; usable paired draws {m['intervals']['usable_draws']}.",
                  'Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.', ''] + header
        for q, c in m['cells'].items():
            lines.append(cell_line(f'matched V0 q{q}', c))
        if r['spells'] is not None:
            lines += ['', '| Spell | First | Last | Adverse sessions |', '|---:|---|---|---:|']
            for n, spell in enumerate(r['spells'],1):
                lines.append(f"| {n} | {spell['first']} | {spell['last']} | {spell['adverse_sessions']} |")
    lines += ['', '## Input exclusions by hold-out year' if holdout else '## Input exclusions by development year', '', '| Year | Cause | Stock-days |', '|---|---|---:|']
    for year, causes in report['exclusions'].items():
        for cause, count in sorted(causes.items()):
            lines.append(f"| {year} | {cause or 'eligible'} | {count} |")
    lines += ['', '## Descriptive input coverage and distributions (no extra contrasts)', '',
              '| Feature | Known | Total | Min / Q25 / median / Q75 / max |', '|---|---:|---:|---|']
    for name, d in report['descriptive'].items():
        lines.append(f"| {name} | {d['known']} | {d['total']} | {d['distribution']} |")
    lines += ['', f"Descriptive NIFTY 50 trend (D-1): {report['nifty50_trend']}.", '',
              '## Input manifest recorded before outcome access', '', '```json', json.dumps(manifest, indent=2), '```', '',
              ('Each variant is reported independently under the registered replication rule. '
               'PARTIALLY EXPOSED: even replication success is not independent proof of new trading edge '
               'and cannot activate risk limits or satisfy T4/readiness.' if holdout else
               'No 2025 replication claim is made. Even a development PASS cannot activate a trading policy '
               'or satisfy T4. Any subsequent hold-out evaluation needs separate approval.'), '']
    return '\n'.join(lines)
