"""Follow-up 3 (preregistered b2df2a2): size plans against the limit price. Research only; no
production sizing, registry or paper convention is changed."""
import numpy as np

from desk.risk.officer import compute_position_size, planned_loss_inr
from desk.shadow_followup import DateBootstrap, cap_measurements, check_event, difference
from desk.shadow_followup2 import LIMIT_ATR
from desk.shadow_analysis import REPLICATES

FILLED = ('FILL_OPEN', 'FILL_LIMIT')


class ProtocolViolation(AssertionError):
    pass


def prepare(rows, executions, rulebook, costs):
    """Join corrected passes with follow-up 2's frozen execution evidence and size each plan at its
    limit price. Aborts on any parity, monotonicity or decision-cap violation (preregistered)."""
    evidence = {(e['symbol'], e['event_date']): e for e in executions}
    if len(evidence) != len(executions):
        raise ProtocolViolation('Duplicate execution evidence identities.')
    out = []
    for row in rows:
        check_event(row)
        if row['state'] != 'SCREEN_PASS':
            raise ProtocolViolation('Follow-up 3 accepts corrected passes only.')
        e = evidence.get((row['symbol'], row['event_date']))
        if e is None:
            raise ProtocolViolation(f"No follow-up 2 evidence for {row['symbol']} {row['event_date']}.")
        plan = row['plan']
        q = plan['quantity']
        if compute_position_size(plan['decision_price'], plan['stop_level'], rulebook, 0, 0, 0, costs=costs) != q:
            raise ProtocolViolation(f"Screening sizing parity failed for {row['symbol']} {row['event_date']}.")
        limit = plan['decision_price'] + LIMIT_ATR * plan['atr20']
        if e['limit']['limit'] is None or abs(e['limit']['limit'] - limit) > 1e-9 * max(1.0, limit):
            raise ProtocolViolation(f"Limit differs from follow-up 2 for {row['symbol']} {row['event_date']}.")
        q_limit = int(compute_position_size(limit, plan['stop_level'], rulebook, 0, 0, 0, costs=costs))
        if q_limit > q:
            raise ProtocolViolation(f"Limit sizing exceeds decision sizing for {row['symbol']} {row['event_date']}.")
        if q_limit:
            caps = cap_measurements(plan, plan['decision_price'], q_limit, rulebook, costs)
            over = [k for k, v in caps.items() if v['usage'] > v['cap']]
            if over:
                raise ProtocolViolation(f"Decision caps {over} exceeded with limit sizing for {row['symbol']} {row['event_date']}.")
        out.append(dict(symbol=row['symbol'], event_date=row['event_date'], state=row['state'], plan=plan,
                        quantity=q, limit_quantity=q_limit, limit=limit, status=e['limit']['status'],
                        fill=e['limit']['fill']))
    return out


def analyze(rows, rulebook, costs, replicates=REPLICATES):
    for row in rows:
        check_event(row)
    boot = DateBootstrap(rows, replicates)
    every = np.ones(len(rows), dtype=bool)
    cap = rulebook.risk.capital_allocated_inr * rulebook.risk.risk_per_trade_pct / 100
    q = np.asarray([r['quantity'] for r in rows], dtype=float)
    q_limit = np.asarray([r['limit_quantity'] for r in rows], dtype=float)
    ratio = q_limit / q
    executed = np.asarray([r['status'] in FILLED for r in rows], dtype=bool)
    variant_fill = executed & (q_limit >= 1)
    unknown = np.asarray([r['status'] == 'UNKNOWN' for r in rows], dtype=bool)
    loss_decision = lambda qty: np.asarray([planned_loss_inr(r['plan']['decision_price'], r['plan']['stop_level'], k, costs)
                                            if k else 0.0 for r, k in zip(rows, qty)]) / cap
    def loss_at_fill(qty):
        return np.asarray([planned_loss_inr(r['fill'], min(r['plan']['stop_level'], r['fill']), k, costs) / cap
                           if r['fill'] is not None and k else np.nan for r, k in zip(rows, qty)])
    used_variant, used_frozen = loss_at_fill(q_limit), loss_at_fill(q)

    mean_ratio, mean_draws = boot.mean(ratio, every)
    ratio_q, _ = boot.quantiles(ratio, every)
    reduced, _ = boot.mean((q_limit < q).astype(float), every)
    abstain, _ = boot.mean((q_limit == 0).astype(float), every)
    fill_rate, fill_draws = boot.mean(variant_fill.astype(float), every)
    fu2_rate, fu2_draws = boot.mean(executed.astype(float), every)
    breach, _ = boot.mean((used_variant > 1).astype(float), variant_fill)
    decision_variant, _ = boot.quantiles(100 * loss_decision(q_limit), q_limit >= 1)
    decision_frozen, _ = boot.quantiles(100 * loss_decision(q), every)
    fill_used_variant, _ = boot.quantiles(100 * used_variant, variant_fill)
    fill_used_frozen, _ = boot.quantiles(100 * used_frozen, executed)
    return dict(
        candidates=len(rows), abstentions=int((q_limit == 0).sum()), reduced=int((q_limit < q).sum()),
        unknown_execution_inputs=int(unknown.sum()), variant_fills=int(variant_fill.sum()),
        follow_up_2_limit_fills=int(executed.sum()), per_trade_breaches_at_fill=int((used_variant > 1).sum()),
        quantity_ratio=dict(mean=mean_ratio, median=ratio_q['median'], p90=ratio_q['p90'],
                            points={f'p{int(100 * k)}': float(np.quantile(ratio, k, method='linear'))
                                    for k in (.10, .25, .50, .75, .90)}),
        share_reduced=reduced, abstention_rate=abstain,
        fill_rate=fill_rate, follow_up_2_fill_rate=fu2_rate,
        fill_rate_difference=difference(fill_rate, fill_draws, fu2_rate, fu2_draws),
        per_trade_breach_rate_at_fill=breach,
        planned_loss_at_decision_pct_of_cap=dict(variant=decision_variant, frozen=decision_frozen),
        planned_loss_at_fill_pct_of_cap=dict(variant=fill_used_variant, frozen_follow_up_2=fill_used_frozen))


def verdict(result):
    primary, descriptive = result['periods']['Primary 2019-2025'], result['periods']['Descriptive 2026']
    p1 = primary['per_trade_breaches_at_fill'] == 0 and descriptive['per_trade_breaches_at_fill'] == 0
    rate = primary['fill_rate']['estimate']
    p2 = rate is not None and rate >= 0.60
    return dict(P1_zero_per_trade_breaches_at_fill=p1, P2_primary_fill_rate_at_least_60pct=p2, passed=p1 and p2)


def report_markdown(result):
    from desk.shadow_followup_report import stat
    import json
    v = result['verdict']
    lines = ['# Shadow replay follow-up 3: size against the limit price', '',
             'Research only (preregistration `b2df2a2`). The active rulebook, strategy registry and paper '
             'conventions are unchanged. Every corrected SCREEN_PASS plan is re-sized with the screening '
             'sizing function at L = decision price + 0.5 x ATR20 instead of the decision price; execution '
             "uses follow-up 2's frozen limit evidence. No outcome is computed.", '',
             f"**Verdict: {'PASS' if v['passed'] else 'FAIL'}.** P1 zero per-trade breaches at the fill: "
             f"{'PASS' if v['P1_zero_per_trade_breaches_at_fill'] else 'FAIL'}. P2 primary fill rate >= 60%: "
             f"{'PASS' if v['P2_primary_fill_rate_at_least_60pct'] else 'FAIL'}. Size reduction is reported, not gated.", '',
             'Intervals: 2,000 event-date-cluster draws, seed 20261001, percentile 95%. Full denominators, '
             'date counts and usable draws are in the JSON companion.', '']
    for period, o in result['periods'].items():
        r = o['quantity_ratio']
        lines += [f'## {period}', '',
                  f"Passes {o['candidates']}; quantity reduced for {o['reduced']}; abstentions (q_L = 0) "
                  f"{o['abstentions']}; unknown execution inputs {o['unknown_execution_inputs']}.", '',
                  '| Statistic | Estimate [95% CI] |', '|---|---|',
                  f"| Quantity ratio q_L / q, mean | {stat(r['mean'])} |",
                  f"| Quantity ratio, median | {stat(r['median'])} |",
                  f"| Quantity ratio, p90 | {stat(r['p90'])} |",
                  f"| Quantity ratio p10 / p25 / p50 / p75 / p90 (points) | "
                  + ' / '.join(f"{v_:.4f}" for v_ in r['points'].values()) + ' |',
                  f"| Share of passes reduced, % | {stat(o['share_reduced'], 100)} |",
                  f"| Abstention rate, % | {stat(o['abstention_rate'], 100)} |",
                  f"| Fill rate, limit-sized, % | {stat(o['fill_rate'], 100)} |",
                  f"| Fill rate, follow-up 2 (frozen size), % | {stat(o['follow_up_2_fill_rate'], 100)} |",
                  f"| Fill-rate difference, pp | {stat(o['fill_rate_difference'], 100)} |",
                  f"| Per-trade breaches at the fill | {o['per_trade_breaches_at_fill']} of {o['variant_fills']} fills |",
                  f"| Planned loss at decision, % of cap, median (limit-sized / frozen) | "
                  f"{stat(o['planned_loss_at_decision_pct_of_cap']['variant']['median'])} / "
                  f"{stat(o['planned_loss_at_decision_pct_of_cap']['frozen']['median'])} |",
                  f"| Planned loss at fill, % of cap, median (limit-sized / frozen) | "
                  f"{stat(o['planned_loss_at_fill_pct_of_cap']['variant']['median'])} / "
                  f"{stat(o['planned_loss_at_fill_pct_of_cap']['frozen_follow_up_2']['median'])} |",
                  f"| Planned loss at fill, % of cap, p90 (limit-sized / frozen) | "
                  f"{stat(o['planned_loss_at_fill_pct_of_cap']['variant']['p90'])} / "
                  f"{stat(o['planned_loss_at_fill_pct_of_cap']['frozen_follow_up_2']['p90'])} |", '']
    lines += ['## Provenance', '', '```json', json.dumps(result['provenance'], indent=2), '```', '']
    return '\n'.join(lines)
