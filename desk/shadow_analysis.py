"""Preregistered tail measures and paired event-date cluster uncertainty."""
from __future__ import annotations
import bisect
import math
from collections import Counter, defaultdict
import numpy as np
from desk.circuit_bands import band_as_of

SEED, REPLICATES = 20261001, 2000
METRICS = ('signed_return_90d', 'collapse', 'adverse20', 'stop_gap', 'entry_gap',
           'mae_decision', 'mae_fill', 'locked_rate')


def tails(hist, day, global_days, plan, observation, desk, cutoff):
    """20 GLOBAL sessions; missing paths stay missing, action-adjusted price basis."""
    start = bisect.bisect_right(global_days, day)
    window = global_days[start:start+20]
    result = dict(adverse20=None, stop_gap=None, entry_gap=None, mae_decision=None,
                  mae_fill=None, locked_days=0, band_covered=0, band_unknown=20,
                  incomplete20=True, tail_reason='', observed_sessions=0)
    decision = plan.get('decision_price')
    if not decision or decision <= 0 or not plan.get('stop_level'):
        result['tail_reason'] = 'invalid_plan'
        return result
    if hist.structural_break_in_window(day, window[-1] if window else day):
        result['tail_reason'] = 'structural_break'
        return result
    anchor_factor = hist.cum_factor_up_to(day)
    lows, fill_lows = [], []
    stopped, gap, path_unknown = False, False, False
    fill = observation.get('fill_price') if observation else None
    fill_factor = hist.cum_factor_up_to(observation['fill_date']) if fill else None
    for offset, session in enumerate(window):
        row = hist.price_row_as_of(session, cutoff)
        if row is None or any(not row.get(k) or not math.isfinite(row[k]) or row[k] <= 0
                              for k in ('open_price','high_price','low_price','close_price')):
            path_unknown = True
            continue
        result['observed_sessions'] += 1
        factor = hist.cum_factor_up_to(session)
        low = row['low_price'] * factor / anchor_factor
        opening = row['open_price'] * factor / anchor_factor
        lows.append(low)
        if fill:
            fill_lows.append(row['low_price'] * factor / fill_factor)
        if offset == 0:
            result['entry_gap'] = opening <= plan['stop_level']
        if not stopped and not path_unknown:
            gap = gap or opening <= plan['stop_level']
            stopped = low <= plan['stop_level'] or gap
        previous_day = global_days[start+offset-1]
        band = band_as_of(desk, row['symbol'], session, report_date=previous_day)
        previous = hist.price_row_as_of(previous_day, cutoff)
        if band.kind == 'FIXED' and band.percent is not None and previous and previous['close_price'] > 0:
            previous_close = previous['close_price'] * hist.cum_factor_up_to(previous_day) / factor
            limit = round(previous_close * (1-band.percent/100) * 20) / 20
            result['band_covered'] += 1
            if all(abs(row[k]-limit) <= 0.025000001 for k in ('open_price','high_price','low_price','close_price')):
                result['locked_days'] += 1
    complete = len(window) == 20 and len(lows) == 20
    result.update(incomplete20=not complete, band_unknown=20-result['band_covered'],
                  tail_reason='' if complete else 'missing_global_sessions_or_security_bars')
    if complete:
        result.update(adverse20=min(lows) <= .8*decision, stop_gap=gap,
                      mae_decision=max(0.0, 1-min(lows)/decision),
                      mae_fill=max(0.0, 1-min(fill_lows)/fill) if fill else None)
    return result


def reason_key(gate, reason):
    """Group semantic checks, not symbol names or numeric magnitudes in their text."""
    patterns = (
        ('no bhavcopy data at all', 'market_missing'), ('no bhavcopy row', 'security_missing'),
        ('isin map', 'map_metadata'), ('Required dimension', 'required_dimension'),
        ('Structural break', 'structural_break'), ('trades in series', 'trade_for_trade'),
        ('under ASM', 'ASM'), ('under GSM', 'GSM'), ('Order is', 'order_ADV_cap'),
        ('Exiting under stressed', 'stressed_exit_cap'), ('No candidate order', 'no_plan'),
        ('Average daily turnover', 'ADV_unknown'), ('No candidate trade', 'no_plan'),
        ('open-risk budget', 'open_risk_cap'), ('per-stock cap', 'stock_cap'),
        ('per-sector cap', 'sector_cap'),
    )
    for text, key in patterns:
        if text.lower() in reason.lower():
            if key == 'required_dimension':
                key += '_' + reason.split("'")[1]
            return gate + ':' + key
    return gate + ':unknown_coverage'


def groups_for(row):
    names = {row['state']}
    for gate, item in row['gates'].items():
        if gate in ('G7','G8') or item['result'] == 'PASS':
            continue
        names.add(gate)
        names.update(reason_key(gate, r) for r in item['reasons'])
    return sorted(names)


def percentile(values):
    values = values[np.isfinite(values)]
    return dict(interval95=np.percentile(values, [2.5,97.5]).tolist() if len(values) else None,
                usable_replicates=len(values))


def summarize(rows):
    """Same event-date bootstrap draw for every group and the PASS comparator."""
    dates = sorted({r['event_date'] for r in rows})
    if not dates:
        return {}
    date_id = {d:i for i,d in enumerate(dates)}
    rng = np.random.default_rng(SEED)
    weights = rng.multinomial(len(dates), np.full(len(dates), 1/len(dates)), size=REPLICATES)
    by_group = defaultdict(list)
    for row in rows:
        for group in groups_for(row):
            by_group[group].append(row)
    by_group.setdefault('SCREEN_PASS', [])
    output, boot = {}, {}
    for name in sorted(by_group, key=lambda n: (n != 'SCREEN_PASS', n)):
        group = by_group[name]
        unique_dates = len({r['event_date'] for r in group})
        item = dict(n=len(group), date_clusters=unique_dates,
                    small_sample_warning=len(group)<30 or unique_dates<10,
                    no_fill=sum(r['fill'] is None for r in group),
                    zero_size=sum(r['plan']['quantity'] <= 0 for r in group),
                    invalid_plan=sum('plan_error' in r['plan'] for r in group),
                    incomplete20=sum(r['incomplete20'] for r in group),
                    missing90=sum(r['signed_return_90d'] is None for r in group),
                    band_covered=sum(r['band_covered'] for r in group),
                    band_unknown=sum(r['band_unknown'] for r in group),
                    fill_cap_breaches=sum(bool((r['execution'] or {}).get('cap_breach_reasons')) for r in group),
                    missing90_reasons=dict(Counter(r['label']['excluded_reason'] for r in group if r['signed_return_90d'] is None)),
                    no_fill_reasons=dict(Counter((r['execution'] or {}).get('no_fill_reason','pending') for r in group if r['fill'] is None)),
                    tail_missing_reasons=dict(Counter(r['tail_reason'] for r in group if r['incomplete20'])),
                    metrics={})
        boot[name] = {}
        for metric in METRICS:
            sums, counts = np.zeros(len(dates)), np.zeros(len(dates))
            n = 0
            for row in group:
                value, denominator = row.get(metric), 1
                if metric == 'locked_rate':
                    value, denominator = row['locked_days'], row['band_covered']
                if value is None or not denominator:
                    continue
                idx = date_id[row['event_date']]
                sums[idx] += value
                counts[idx] += denominator
                n += 1
            denominator = float(counts.sum())
            estimate = float(sums.sum()/denominator) if denominator else None
            draws_n = weights @ counts
            draws = np.divide(weights @ sums, draws_n, out=np.full(REPLICATES, np.nan), where=draws_n>0)
            boot[name][metric] = draws
            stat = dict(estimate=estimate, n_events=n, denominator=denominator, missing_events=len(group)-n, **percentile(draws))
            if name != 'SCREEN_PASS':
                base = output['SCREEN_PASS']['metrics'][metric]['estimate']
                stat['difference_vs_pass'] = dict(estimate=estimate-base if estimate is not None and base is not None else None,
                                                  **percentile(draws-boot['SCREEN_PASS'][metric]))
            item['metrics'][metric] = stat
        output[name] = item
    return output
