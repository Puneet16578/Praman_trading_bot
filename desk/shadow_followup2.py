"""Fixed limit-entry experiment; no production execution policy is changed."""
import math
import numpy as np

from desk.risk.officer import planned_loss_inr
from desk.shadow_followup import check_event, DateBootstrap, difference
from desk.shadow_analysis import REPLICATES

LIMIT_ATR = 0.5


def limit_fill(plan, opening, low):
    limit = plan['decision_price'] + LIMIT_ATR * plan['atr20']
    if not isinstance(opening, (float, int)) or not math.isfinite(opening) or opening <= 0:
        return dict(limit=limit, fill=None, status='UNKNOWN', reason='Opening price unavailable')
    if opening <= limit:
        return dict(limit=limit, fill=opening, status='FILL_OPEN', reason='')
    if not isinstance(low, (float, int)) or not math.isfinite(low) or low <= 0 or low > opening:
        return dict(limit=limit, fill=None, status='UNKNOWN', reason='Usable session low unavailable')
    if low <= limit:
        return dict(limit=limit, fill=limit, status='FILL_LIMIT', reason='')
    return dict(limit=limit, fill=None, status='NO_FILL', reason='Session low above limit')


def analyze(rows, rulebook, costs, replicates=REPLICATES):
    for row in rows:
        check_event(row)
        if row['state'] != 'SCREEN_PASS':
            raise ValueError('Limit experiment accepts corrected passes only.')
    boot = DateBootstrap(rows, replicates)
    all_rows = np.ones(len(rows), dtype=bool)
    adverse = np.asarray([np.nan if r['adverse20'] is None else float(r['adverse20']) for r in rows])
    result = dict(candidates=len(rows), variants={}, differences={}, common_fills={})
    saved = {}
    budget = rulebook.risk.capital_allocated_inr * rulebook.risk.risk_per_trade_pct / 100
    for name in ('baseline', 'limit'):
        fills = np.asarray([np.nan if r[name]['fill'] is None else r[name]['fill'] for r in rows], dtype=float)
        filled = np.isfinite(fills)
        ratio = np.full(len(rows), np.nan)
        for i in np.flatnonzero(filled):
            plan = rows[i]['plan']
            ratio[i] = planned_loss_inr(fills[i], min(plan['stop_level'], fills[i]), plan['quantity'], costs) / budget
        breach = filled & (ratio > 1)
        fill_rate, fd = boot.mean(filled.astype(float), all_rows)
        breach_rate, bd = boot.mean((ratio > 1).astype(float), filled)
        adverse_rate, ad = boot.mean(adverse, filled)
        sizes, sd = boot.quantiles(100 * (ratio - 1), breach)
        result['variants'][name] = dict(fills=int(filled.sum()), no_fill=int((~filled).sum()),
            unknown_inputs=sum(r[name]['status'] == 'UNKNOWN' for r in rows),
            fills_at_open=sum(r[name]['status'] == 'FILL_OPEN' for r in rows),
            fills_at_limit=sum(r[name]['status'] == 'FILL_LIMIT' for r in rows),
            observed_no_touch=sum(r[name]['status'] == 'NO_FILL' for r in rows),
            breaches=int(breach.sum()), missing_adverse=int((filled & ~np.isfinite(adverse)).sum()),
            fill_rate=fill_rate, per_trade_breach_rate=breach_rate,
            conditional_excess_pct=sizes, adverse20_rate=adverse_rate)
        saved[name] = dict(fill_rate=fd, per_trade_breach_rate=bd, adverse20_rate=ad,
                           sizes=sd, filled=filled, ratio=ratio)
    for key in ('fill_rate', 'per_trade_breach_rate', 'adverse20_rate'):
        result['differences'][key] = difference(result['variants']['limit'][key], saved['limit'][key],
                                              result['variants']['baseline'][key], saved['baseline'][key])
    for k, key in enumerate(('median', 'p90')):
        result['differences'][key+'_excess_pct'] = difference(
            result['variants']['limit']['conditional_excess_pct'][key], saved['limit']['sizes'][:, k],
            result['variants']['baseline']['conditional_excess_pct'][key], saved['baseline']['sizes'][:, k])
    common = saved['baseline']['filled'] & saved['limit']['filled']
    result['common_fills']['n'] = int(common.sum())
    for key in ('per_trade_breach_rate', 'adverse20_rate'):
        stats, draws = {}, {}
        for name in ('baseline', 'limit'):
            values = (saved[name]['ratio'] > 1).astype(float) if key == 'per_trade_breach_rate' else adverse
            stats[name], draws[name] = boot.mean(values, common)
        result['common_fills'][key] = stats | {'difference': difference(stats['limit'], draws['limit'], stats['baseline'], draws['baseline'])}
    return result


def report_markdown(result):
    from desk.shadow_followup_report import stat
    import json
    lines = ['# Shadow replay follow-up 2: fixed entry limit', '',
        'Research only. The active rulebook and paper entry convention are unchanged.', '',
        'Limit = decision price + 0.5 ATR20. Fill at the next open if at/below the limit; '
        'otherwise at the limit only if that session low reaches it. Quantity stays frozen.', '',
        'Adverse20 is the unchanged 20-session, decision-price-referenced outcome, conditional '
        'on fills. Daily bars cannot establish intraday ordering, queue priority or tradability. '
        'The 2026 sample is descriptive spent hold-out. Unknown inputs are counted separately '
        'within nonfills; they are not evidence of an untouched limit.', '',
        'Intervals: 2,000 paired event-date-cluster draws, seed 20261001, percentile 95%. '
        'Size statistics condition on breaches; different conventions can have different cohorts. '
        'No tuning or multiplicity adjustment. Full statistic denominators, date counts, usable '
        'draws and small-sample warnings are in the JSON companion.', '']
    for period, output in result['periods'].items():
        lines += [f'## {period}', '', f"Corrected passes: {output['candidates']}.", '',
            '| Convention | Fills | Nonfills (unknown) | Per-trade breaches | Missing adverse20 among fills |',
            '|---|---:|---:|---:|---:|']
        for name, value in output['variants'].items():
            lines.append(f"| {name} | {value['fills']} | {value['no_fill']} ({value['unknown_inputs']}) | {value['breaches']} | {value['missing_adverse']} |")
        lines += ['', '| Statistic | Baseline [95% CI] | Limit [95% CI] | Limit minus baseline [95% CI] |', '|---|---|---|---|']
        for key in ('fill_rate', 'per_trade_breach_rate', 'adverse20_rate'):
            lines.append(f"| {key}, % / difference pp | {stat(output['variants']['baseline'][key],100)} | {stat(output['variants']['limit'][key],100)} | {stat(output['differences'][key],100)} |")
        for key in ('median', 'p90'):
            lines.append(f"| Conditional excess {key}, % of cap | {stat(output['variants']['baseline']['conditional_excess_pct'][key])} | {stat(output['variants']['limit']['conditional_excess_pct'][key])} | {stat(output['differences'][key+'_excess_pct'])} |")
        lines += ['', f"Limit executions: {output['variants']['limit']['fills_at_open']} at open; "
                  f"{output['variants']['limit']['fills_at_limit']} at limit; "
                  f"{output['variants']['limit']['observed_no_touch']} observed no touch.", '',
                  f"Common-fill sensitivity ({output['common_fills']['n']} events):", '']
        for key in ('per_trade_breach_rate', 'adverse20_rate'):
            v = output['common_fills'][key]
            lines.append(f"- {key}: baseline {stat(v['baseline'],100)}%; limit {stat(v['limit'],100)}%; difference {stat(v['difference'],100)} pp.")
        lines += ['']
    lines += ['## Provenance', '', '```json', json.dumps(result['provenance'], indent=2), '```', '']
    return '\n'.join(lines)
