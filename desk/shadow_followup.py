"""Registered follow-up calculations over immutable historical replay records."""
from __future__ import annotations

import math
import numpy as np

from desk.gates.checks import g5_liquidity, g6_risk
from desk.outcome_firewall import require_outcome_access
from desk.risk.officer import planned_loss_inr
from desk.shadow_analysis import SEED, REPLICATES, percentile

HEADROOM = 0.90
CAPS = ('per_trade', 'open_risk', 'per_stock', 'per_sector', 'order_adv', 'exit_days')
PERIODS = (('Primary 2019-2025', '2019-10-01', '2025-12-31'),
           ('Descriptive 2026', '2026-01-01', '2026-09-15'))


def check_event(row):
    require_outcome_access(row['event_date'])
    if not PERIODS[0][1] <= row['event_date'] <= PERIODS[-1][2]:
        raise ValueError('Follow-up record lies outside the registered periods.')
    if row['state'] not in ('SCREEN_PASS', 'SCREEN_FAIL'):
        raise ValueError('Unrecognized historical screening state.')


def volatility(row):
    atr, price = row['plan'].get('atr20'), row['plan'].get('decision_price')
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (atr, price)):
        return float('nan')
    return 100 * atr / price


def quintile_boundaries(rows):
    for row in rows:
        check_event(row)
    values = [volatility(r) for r in rows if PERIODS[0][1] <= r['event_date'] <= PERIODS[0][2]]
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    if not len(values):
        raise ValueError('No primary-period decision volatility is available.')
    return np.quantile(values, [.2, .4, .6, .8], method='linear')


def repeated_quantiles(sorted_values, multiplicities, probabilities=(.5, .9)):
    """Linear quantiles of the exact multiset, without materializing repetitions."""
    cumulative = np.cumsum(multiplicities, dtype=np.int64)
    total = cumulative[-1] if len(cumulative) else 0
    if not total:
        return np.full(len(probabilities), np.nan)
    positions = (total - 1) * np.asarray(probabilities)
    lower, upper = np.floor(positions).astype(int), np.ceil(positions).astype(int)
    lo = sorted_values[np.searchsorted(cumulative, lower, side='right')]
    hi = sorted_values[np.searchsorted(cumulative, upper, side='right')]
    return lo + (hi - lo) * (positions - lower)


class DateBootstrap:
    """Shared date multiplicities for every comparison within one cohort."""

    def __init__(self, rows, replicates=REPLICATES):
        self.dates = sorted({r['event_date'] for r in rows})
        lookup = {day: i for i, day in enumerate(self.dates)}
        self.ids = np.asarray([lookup[r['event_date']] for r in rows], dtype=int)
        self.replicates = replicates
        n = len(self.dates)
        self.weights = (np.random.default_rng(SEED).multinomial(n, np.full(n, 1 / n), size=replicates)
                        if n else np.empty((replicates, 0), dtype=int))

    def describe(self, estimate, draws, mask):
        n, dates = int(np.count_nonzero(mask)), len(np.unique(self.ids[mask]))
        return dict(estimate=None if estimate is None or not np.isfinite(estimate) else float(estimate),
                    n_events=n, date_clusters=dates, small_sample_warning=n < 30 or dates < 10,
                    **percentile(draws))

    def mean(self, values, mask=None):
        values = np.asarray(values, dtype=float)
        valid = np.isfinite(values)
        if mask is not None:
            valid &= mask
        sums = np.bincount(self.ids[valid], weights=values[valid], minlength=len(self.dates))
        counts = np.bincount(self.ids[valid], minlength=len(self.dates))
        denominator = self.weights @ counts
        draws = np.divide(self.weights @ sums, denominator,
                          out=np.full(self.replicates, np.nan), where=denominator > 0)
        estimate = float(np.mean(values[valid])) if valid.any() else None
        return self.describe(estimate, draws, valid), draws

    def quantiles(self, values, mask):
        values = np.asarray(values, dtype=float)
        valid = mask & np.isfinite(values)
        ordered = np.flatnonzero(valid)
        ordered = ordered[np.argsort(values[ordered], kind='stable')]
        sorted_values, ids = values[ordered], self.ids[ordered]
        draws = np.full((self.replicates, 2), np.nan)
        if len(ordered):
            for i, weights in enumerate(self.weights):
                draws[i] = repeated_quantiles(sorted_values, weights[ids])
            estimates = np.quantile(sorted_values, [.5, .9], method='linear')
        else:
            estimates = [None, None]
        stats = {key: self.describe(estimates[j], draws[:, j], valid)
                 for j, key in enumerate(('median', 'p90'))}
        return stats, draws


def difference(left, left_draws, right, right_draws):
    estimate = (left['estimate'] - right['estimate']
                if left['estimate'] is not None and right['estimate'] is not None else None)
    return dict(estimate=estimate, **percentile(left_draws - right_draws))


def volatility_analysis(rows, boundaries, replicates=REPLICATES):
    for row in rows:
        check_event(row)
    boot = DateBootstrap(rows, replicates)
    vol = np.asarray([volatility(r) for r in rows])
    valid = np.isfinite(vol)
    quintiles = np.searchsorted(boundaries, vol, side='right')
    passed = np.asarray([r['state'] == 'SCREEN_PASS' for r in rows], dtype=bool)
    outcome = np.asarray([np.nan if r['adverse20'] is None else float(r['adverse20']) for r in rows])
    result = dict(n=len(rows), missing_volatility={}, quintiles=[])
    for state, mask in [('SCREEN_PASS', passed), ('SCREEN_FAIL', ~passed)]:
        excluded = mask & ~valid
        result['missing_volatility'][state] = dict(n=int(excluded.sum()),
            missing_outcomes=int((excluded & ~np.isfinite(outcome)).sum()))

    def compare(mask):
        p, pd = boot.mean(outcome, mask & passed)
        f, fd = boot.mean(outcome, mask & ~passed)
        return dict(passed=p, failed=f, difference=difference(f, fd, p, pd),
                    pass_candidates=int((mask & passed).sum()), fail_candidates=int((mask & ~passed).sum()),
                    pass_missing=int((mask & passed & ~np.isfinite(outcome)).sum()),
                    fail_missing=int((mask & ~passed & ~np.isfinite(outcome)).sum())), fd - pd

    unstratified, unstratified_draws = compare(valid)
    result['unstratified'] = unstratified
    adjusted, adjusted_draws = 0., np.zeros(replicates)
    available = bool(valid.any())
    for i in range(5):
        mask = valid & (quintiles == i)
        item, draws = compare(mask)
        weight = float(mask.sum() / valid.sum()) if valid.any() else 0.
        item.update(quintile=i + 1, weight=weight)
        result['quintiles'].append(item)
        if weight:
            value = item['difference']['estimate']
            if value is None:
                available = False
            else:
                adjusted += weight * value
            adjusted_draws += weight * draws
    if not available:
        adjusted_draws[:] = np.nan
    standardized = dict(estimate=adjusted if available else None, **percentile(adjusted_draws))
    result['standardized'] = standardized
    result['attenuation'] = difference(unstratified['difference'], unstratified_draws,
                                      standardized, adjusted_draws)
    return result


def cap_measurements(plan, price, quantity, rulebook, costs):
    """Reprice the original frozen scenarios for a supplied whole-share quantity."""
    decision, stop, original = (plan.get(k) for k in ('decision_price', 'stop_level', 'quantity'))
    stress = plan.get('stress')
    adv = plan.get('adv_turnover')
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0
               for v in (decision, stop, original, price, adv)) or not stress:
        raise ValueError('Missing or invalid frozen price, size, stress, or ADV.')
    if not isinstance(quantity, (int, np.integer)) or quantity <= 0:
        raise ValueError('A measurement requires positive whole shares.')
    planned = planned_loss_inr(price, min(stop, price), quantity, costs)
    components = [planned]
    for key in ('floor_component_inr', 'worst_gap_component_inr', 'locked_circuit_loss_inr'):
        value = stress.get(key)
        if value is None and key != 'floor_component_inr':
            continue
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('Invalid frozen stress component.')
        components.append(value * (quantity / original) * price / decision)
    risk, liquidity = rulebook.risk, rulebook.liquidity
    capital, position = risk.capital_allocated_inr, price * quantity
    achievable = liquidity.participation_pct_of_stressed_volume / 100 * liquidity.stressed_volume_factor * adv
    if achievable <= 0:
        raise ValueError('Unknown achievable turnover.')
    used = (planned, max(components), position, position, position, position / achievable)
    caps = (capital * risk.risk_per_trade_pct / 100, capital * risk.max_open_risk_pct / 100,
            capital * risk.max_per_stock_pct / 100, capital * risk.max_per_sector_pct / 100,
            adv * liquidity.max_order_pct_of_adv / 100, liquidity.max_days_to_exit_stressed)
    if not all(math.isfinite(v) and v > 0 for v in caps):
        raise ValueError('Unknown or nonpositive cap.')
    return {key: dict(usage=float(value), cap=float(cap), ratio=float(value / cap))
            for key, value, cap in zip(CAPS, used, caps)}


def buffered_quantity(plan, rulebook, costs):
    """Largest feasible integer, determined entirely from decision-time inputs."""
    original = plan.get('quantity')
    if not isinstance(original, int) or original < 1:
        raise ValueError('Missing original whole-share quantity.')
    low, high = 0, original
    while low < high:
        mid = (low + high + 1) // 2
        measures = cap_measurements(plan, plan['decision_price'], mid, rulebook, costs)
        if all(v['usage'] <= HEADROOM * v['cap'] for v in measures.values()):
            low = mid
        else:
            high = mid - 1
    return low


def assert_original_flags(row, measures, rulebook, costs):
    """Compare numeric reconstruction with the existing execution observer's checks."""
    fill, plan = row['fill'], row['plan']
    risk = g6_risk(measures['per_trade']['usage'], measures['open_risk']['usage'], 0,
                   fill * plan['quantity'], fill * plan['quantity'], rulebook)
    liquidity = g5_liquidity(fill * plan['quantity'], plan['adv_turnover'], rulebook)
    reasons = list(risk.reasons)
    reasons += liquidity.reasons
    if set(reasons) != set(row['execution']['cap_breach_reasons']):
        raise ValueError('Original fill-cap reconstruction does not match frozen flags.')
    if bool(reasons) != any(v['usage'] > v['cap'] for v in measures.values()):
        raise ValueError('Quantitative cap tests disagree with original gate checks.')


def cap_analysis(rows, rulebook, costs, replicates=REPLICATES):
    for row in rows:
        check_event(row)
    passes = [r for r in rows if r['state'] == 'SCREEN_PASS']
    filled = [r for r in passes if r['fill'] is not None]
    boot = DateBootstrap(filled, replicates)
    baseline, variant = np.full((len(filled), len(CAPS)), np.nan), np.full((len(filled), len(CAPS)), np.nan)
    abstained, unknown, locked_unknown, gap_unknown = 0, 0, 0, 0
    decision_breaches = 0
    quantities = []
    for i, row in enumerate(filled):
        plan = row['plan']
        try:
            # Choose size before accessing the fill in this calculation.
            quantity = buffered_quantity(plan, rulebook, costs)
            base = cap_measurements(plan, row['fill'], plan['quantity'], rulebook, costs)
            at_decision = cap_measurements(plan, plan['decision_price'], plan['quantity'], rulebook, costs)
            change = cap_measurements(plan, row['fill'], quantity, rulebook, costs) if quantity else None
        except ValueError:
            unknown += 1
            continue
        assert_original_flags(row, base, rulebook, costs)
        decision_breaches += any(v['usage'] > v['cap'] for v in at_decision.values())
        locked_unknown += plan['stress'].get('locked_circuit_loss_inr') is None
        gap_unknown += plan['stress'].get('worst_gap_component_inr') is None
        baseline[i] = [base[key]['ratio'] for key in CAPS]
        quantities.append(quantity)
        if change is None:
            abstained += 1
        else:
            variant[i] = [change[key]['ratio'] for key in CAPS]
    base_valid = np.isfinite(baseline).all(axis=1)
    variant_valid = np.isfinite(variant).all(axis=1)
    common = base_valid & variant_valid
    result = dict(original_passes=len(passes), original_fills=len(filled),
                  original_no_fill=len(passes) - len(filled), unknown_inputs=unknown,
                  variant_abstentions=abstained, variant_fills=int(variant_valid.sum()),
                  unknown_locked_components=locked_unknown, unknown_gap_components=gap_unknown,
                  original_decision_cap_breaches=decision_breaches, caps={})
    overall = {}
    overall_draws = {}
    for name, matrix, valid in [('baseline', baseline, base_valid), ('variant', variant, variant_valid)]:
        rate, draws = boot.mean((matrix > 1).any(axis=1).astype(float), valid)
        rate['breaches'] = int(((matrix > 1).any(axis=1) & valid).sum())
        overall[name], overall_draws[name] = rate, draws
    pb, pbd = boot.mean((baseline > 1).any(axis=1).astype(float), common)
    pv, pvd = boot.mean((variant > 1).any(axis=1).astype(float), common)
    overall['paired_baseline'], overall['paired_variant'] = pb, pv
    overall['paired_difference_variant_minus_baseline'] = difference(pv, pvd, pb, pbd)
    result['any_cap'] = overall
    for j, key in enumerate(CAPS):
        output, saved = {}, {}
        for name, matrix, valid in [('baseline', baseline, base_valid), ('variant', variant, variant_valid)]:
            ratio = matrix[:, j]
            breach = valid & (ratio > 1)
            excess = 100 * np.maximum(ratio - 1, 0)
            rate, draws = boot.mean((ratio > 1).astype(float), valid)
            rate['breaches'] = int(breach.sum())
            conditional, qdraws = boot.quantiles(excess, breach)
            inclusive, _ = boot.quantiles(excess, valid)
            output[name] = dict(rate=rate, conditional_excess_pct=conditional,
                                zero_inclusive_excess_pct=inclusive)
            saved[name] = qdraws
        output['conditional_size_difference_variant_minus_baseline'] = {
            q: difference(output['variant']['conditional_excess_pct'][q], saved['variant'][:, k],
                          output['baseline']['conditional_excess_pct'][q], saved['baseline'][:, k])
            for k, q in enumerate(('median', 'p90'))}
        br, bd = boot.mean((baseline[:, j] > 1).astype(float), common)
        vr, vd = boot.mean((variant[:, j] > 1).astype(float), common)
        output['paired_rate_difference_variant_minus_baseline'] = difference(vr, vd, br, bd)
        result['caps'][key] = output
    return result
