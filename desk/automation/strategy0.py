"""Strategy 0 automatic paper engine (session item B4; automation level A1).

Nightly, after ingestion and `desk scan`, with no human step: evaluate kill switches, settle
yesterday's entry orders, monitor open positions and exits, then decide on today's SCREEN_PASS
candidates. Everything is computed in memory first and written as one transaction: a run row, then
separate append-only events (CANDIDATE_*, ENTRY_*, MONITORED, EXIT_*), each candidate linked to
its blueprint decision contract. A run date is processed at most once.

Share basis (P8-044): the frozen decision price, limit, stop and quantity are stated as of the
decision date. An entry is evaluated and recorded on that basis (raw session price times the
store's point-in-time adjustment factor since the decision; exactly the raw price when no bonus or
split intervenes). While held, the stop and quantity are re-expressed from the decision date to
each session, and exits are recorded at raw prices with the re-expressed quantity, so notional
and P&L stay consistent. Operational metrics are stored in the run row; P&L never is (seal).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math

from desk.automation import kill_switches as ks
from desk.automation import registry, seal
from desk.automation.levels import require_level
from desk.decision_contract import build_contract, known, record_contract, unknown
from desk.risk.officer import planned_loss_inr, round_trip_cost_inr
from desk.shadow_followup2 import limit_fill
from src.bitemporal.guard import latest_as_of
from desk.paper.execution import basis_factor
from src.signals.price_adjustment import UnadjustableWindowError

STRATEGY_ID = 'S0'
SERIES = ('EQ', 'BE', 'BZ')


class EngineRefused(RuntimeError):
    pass


@dataclass
class Plan:
    """In-memory result of one run, written atomically afterwards."""
    events: list = field(default_factory=list)       # (event dict, contract or None)
    operational: dict = field(default_factory=dict)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def sessions_between(conn, after, upto):
    """Global trading sessions strictly after `after`, up to and including `upto`, known by `upto`."""
    return [r[0] for r in conn.execute('SELECT DISTINCT event_date FROM bhavcopy WHERE event_date>? AND event_date<=? '
                                       'AND knowledge_date<=? ORDER BY event_date', (after, upto, upto))]


def session_bar(conn, symbol, day, as_of):
    rows = [r for r in latest_as_of(conn, 'bhavcopy', as_of, symbol=symbol, event_date=day) if r['series'] in SERIES]
    rows.sort(key=lambda r: SERIES.index(r['series']))
    return rows[0] if rows else None


def load_book(conn, version):
    """Rebuild every Strategy 0 position from its events (current state is derived, never stored)."""
    positions = {}
    for row in conn.execute('SELECT * FROM strategy_paper_events WHERE strategy_id=? AND strategy_version=? '
                            'AND position_id IS NOT NULL ORDER BY event_id', (STRATEGY_ID, version)):
        detail = json.loads(row['detail'])
        p = positions.setdefault(row['position_id'], dict(symbol=row['symbol'], decision_date=row['decision_date'],
                                                          accepted=None, entry=None, entry_outcome=None,
                                                          exit_order=None, exit=None))
        record = dict(detail, event_date=row['event_date'], event_id=row['event_id'], recorded_at=row['recorded_at'])
        if row['event_type'] == 'CANDIDATE_ACCEPTED':
            p['accepted'] = record
        elif row['event_type'] in ('ENTRY_FILLED', 'ENTRY_NO_FILL', 'ENTRY_FILL_FAILED'):
            p['entry_outcome'] = row['event_type']
            if row['event_type'] == 'ENTRY_FILLED':
                p['entry'] = record
        elif row['event_type'] == 'EXIT_ORDERED':
            p['exit_order'] = record
        elif row['event_type'] == 'EXIT_FILLED':
            p['exit'] = record
    for pid, p in positions.items():
        if p['accepted'] is None:
            raise EngineRefused(f'{pid}: events exist without an acceptance; book inconsistent.')
        p['status'] = ('PENDING_ENTRY' if p['entry_outcome'] is None else
                       'NOT_FILLED' if p['entry'] is None else
                       'CLOSED' if p['exit'] is not None else
                       'EXIT_PENDING' if p['exit_order'] is not None else 'OPEN')
    return positions


def _holding(p):
    return p['status'] in ('PENDING_ENTRY', 'OPEN', 'EXIT_PENDING')


def _event(event_type, p_or_symbol, run_date, detail, *, position_id=None, opportunity_id=None, decision_date=None):
    symbol = p_or_symbol if isinstance(p_or_symbol, str) else p_or_symbol['symbol']
    return dict(event_type=event_type, symbol=symbol, event_date=run_date, detail=detail, position_id=position_id,
                opportunity_id=opportunity_id,
                decision_date=decision_date or (None if isinstance(p_or_symbol, str) else p_or_symbol['decision_date']))


def _last_reset(conn, switch):
    row = conn.execute("SELECT recorded_at FROM kill_switch_events WHERE scope=? AND switch=? AND state='RESET' "
                       'ORDER BY event_id DESC LIMIT 1', (STRATEGY_ID, switch)).fetchone()
    return row[0] if row else None


def _isin_status(conn, run_date):
    from desk.ingestion_health import isin_map_health_line
    line = isin_map_health_line(conn, run_date)
    return 'OK' if line.startswith('ISIN map: OK') else line.split(':', 1)[1].strip().split(',')[0].split(' ')[0]


def run(praman_conn, desk_conn, run_date, *, rulebook, costs, rulebook_file, rulebook_hash, cost_config_hash,
        code_commit, praman_watermark, today, defect_path=None, isin_status=None):
    """One nightly Strategy 0 run. Returns the operational summary (never P&L)."""
    require_level(rulebook, 'paper_auto')
    strategy = registry.ensure_registered(desk_conn)
    version = strategy['version']
    if desk_conn.execute('SELECT 1 FROM strategy_runs WHERE strategy_id=? AND strategy_version=? AND run_date=?',
                         (STRATEGY_ID, version, run_date)).fetchone():
        return dict(status='ALREADY_RUN', run_date=run_date)
    definition = strategy['definition']
    use_limit = definition['entry']['policy'].startswith('LIMIT')
    positions = load_book(desk_conn, version)
    plan = Plan()
    budget = rulebook.risk.capital_allocated_inr * rulebook.risk.max_open_risk_pct / 100
    per_trade = rulebook.risk.capital_allocated_inr * rulebook.risk.risk_per_trade_pct / 100

    candidates = [dict(r) | dict(plan=json.loads(r['inputs'])['plan'], gates=json.loads(r['gate_results']))
                  for r in desk_conn.execute("SELECT * FROM opportunity_log WHERE event_date=? AND state='SCREEN_PASS' "
                                             'ORDER BY symbol, opportunity_id', (run_date,))]

    # 1. Kill switches.
    from desk.ingestion_health import STALE_AFTER_DAYS
    from desk.readiness import open_defects
    from pathlib import Path
    latest = praman_conn.execute('SELECT MAX(event_date) FROM bhavcopy').fetchone()[0]
    holding_stress = {pid: p['accepted'].get('stress_loss_inr') for pid, p in positions.items() if _holding(p)}
    high, unclassified = open_defects(defect_path or Path(__file__).resolve().parents[2] / 'docs/DEFECT_REGISTER.md')
    params = definition['kill_switch_parameters']
    trips = [
        ks.data_health(run_date, latest, today, isin_status or _isin_status(praman_conn, run_date),
                       [(c['symbol'], c['plan']) for c in candidates], STALE_AFTER_DAYS),
        ks.risk_state(holding_stress, budget),
        ks.fill_failures(_entry_outcomes_since(desk_conn, version, _last_reset(desk_conn, 'REPEATED_FILL_FAILURES')),
                         params['fill_failure_threshold']),
        ks.open_critical_defect(high, unclassified),
        ks.calibration_degradation(),
    ]
    exemption = seal.pnl_brake_exemption(STRATEGY_ID, today)
    if exemption is None:
        # Only once outcomes are open: the brake reads realized P&L through the seal's checked path.
        trips.append(ks.drawdown_or_streak(
            seal.brake_inputs(positions, STRATEGY_ID, today, _last_reset(desk_conn, 'DRAWDOWN_OR_LOSING_STREAK')),
            run_date, rulebook.risk.capital_allocated_inr, rulebook.risk.monthly_drawdown_brake_pct,
            rulebook.behavioural_brakes.consecutive_loss_brake_count, sealed=False))
    active = ks.evaluate_and_log(desk_conn, trips, scope=STRATEGY_ID, run_date=run_date)
    blocking = sorted(s for s, on in active.items() if on and ks.SWITCHES[s] in ks.BLOCKS_ENTRIES)
    exiting = sorted(s for s, on in active.items() if on and ks.SWITCHES[s] == 'EXIT_POSITIONS')

    ops = dict(run_date=run_date, candidates=len(candidates), accepted=0, rejected={}, entries_filled=0,
               entries_no_fill=0, entries_failed=0, entries_cancelled=0, cap_breaches_at_fill=0,
               monitored=0, missing_bars=0, kill_switches_active=sorted(s for s, on in active.items() if on),
               entry_blocked_by=blocking, entry_policy=definition['entry']['policy'],
               exempt_switches={s: exemption for s in ks.P_AND_L_BRAKES} if exemption else {})

    # 2. Settle entry orders on the first session after their decision date.
    for pid, p in sorted(positions.items()):
        if p['status'] != 'PENDING_ENTRY':
            continue
        sessions = sessions_between(praman_conn, p['decision_date'], run_date)
        if not sessions:
            continue
        acc, day = p['accepted'], sessions[0]
        if blocking:
            plan.events.append((_event('ENTRY_NO_FILL', p, run_date, dict(reason='CANCELLED: kill switch ' + ','.join(blocking),
                                session=day), position_id=pid), None))
            ops['entries_cancelled'] += 1
            continue
        try:
            event = _settle_entry(praman_conn, p, pid, acc, day, run_date, use_limit, costs, per_trade)
        except Exception as exc:  # an engine error is an operational failure, never a crash of the whole run
            event = _event('ENTRY_FILL_FAILED', p, day, dict(session=day, failure='ENGINE_ERROR',
                           error_type=type(exc).__name__, reason='Engine error while settling the entry.'),
                           position_id=pid)
        if event['event_type'] == 'ENTRY_FILLED':
            ops['entries_filled'] += 1
            ops['cap_breaches_at_fill'] += event['detail']['per_trade_cap_breach_at_fill']
        elif event['event_type'] == 'ENTRY_NO_FILL':
            ops['entries_no_fill'] += 1
        else:
            ops['entries_failed'] += 1
        plan.events.append((event, None))

    # 3. Monitor positions filled before today; settle exit orders.
    for pid, p in sorted(positions.items()):
        if p['status'] == 'EXIT_PENDING':
            sessions = sessions_between(praman_conn, p['exit_order']['event_date'], run_date)
            if not sessions:
                continue
            bar = session_bar(praman_conn, p['symbol'], sessions[0], run_date)
            if bar is None or not _finite(bar['open_price']) or bar['open_price'] <= 0:
                ops['missing_bars'] += 1
                plan.events.append((_event('MONITORED', p, run_date, dict(note='Exit pending: no usable bar.',
                                    session=sessions[0]), position_id=pid), None))
                continue
            qty = _quantity_now(praman_conn, p, sessions[0])
            plan.events.append((_event('EXIT_FILLED', p, sessions[0], dict(
                price=bar['open_price'], quantity=qty, reason=p['exit_order']['reason'], kind='exit_open',
                sell_cost_inr=round_trip_cost_inr(bar['open_price'], qty, costs, 'sell'), row_id=bar['row_id']),
                position_id=pid), None))
            continue
        if p['status'] != 'OPEN' or p['entry']['event_date'] >= run_date:
            continue
        ops['monitored'] += 1
        try:
            # Decision share basis (P8-044): stop and quantity are stated as of the decision date.
            factor = basis_factor(praman_conn, p['symbol'], p['decision_date'], run_date)
        except UnadjustableWindowError as exc:
            # No factor exists, so the stop cannot be monitored: leave at the next open.
            plan.events.append((_event('MONITORED', p, run_date, dict(note=f'Unadjustable corporate action: {exc}'),
                                       position_id=pid), None))
            plan.events.append((_event('EXIT_ORDERED', p, run_date, dict(reason='UNADJUSTABLE_CORPORATE_ACTION'),
                                       position_id=pid), None))
            continue
        stop_now = p['accepted']['stop_level'] / factor
        qty = p['entry']['quantity'] * factor
        bar = session_bar(praman_conn, p['symbol'], run_date, run_date)
        held = len(sessions_between(praman_conn, p['entry']['event_date'], run_date))
        if bar is None or not all(_finite(bar[k]) and bar[k] > 0 for k in ('open_price', 'low_price')):
            ops['missing_bars'] += 1
            plan.events.append((_event('MONITORED', p, run_date, dict(note='No usable bar today.', stop=stop_now,
                                sessions_held=held), position_id=pid), None))
            continue
        hit = ('stop_gap', bar['open_price']) if bar['open_price'] <= stop_now else (
               ('stop_touch', stop_now) if bar['low_price'] <= stop_now else None)
        plan.events.append((_event('MONITORED', p, run_date, dict(stop=stop_now, factor=factor, sessions_held=held,
                            row_id=bar['row_id']), position_id=pid), None))
        if hit:
            plan.events.append((_event('EXIT_FILLED', p, run_date, dict(
                price=hit[1], quantity=qty, reason='STOP', kind=hit[0],
                sell_cost_inr=round_trip_cost_inr(hit[1], qty, costs, 'sell'), row_id=bar['row_id']),
                position_id=pid), None))
        elif held >= definition['time_limit_sessions'] or exiting:
            reason = 'TIME_LIMIT' if held >= definition['time_limit_sessions'] else 'KILL_SWITCH ' + ','.join(exiting)
            plan.events.append((_event('EXIT_ORDERED', p, run_date, dict(reason=reason, sessions_held=held),
                                       position_id=pid), None))

    # 4. Today's candidates, in the registered order, against the open-risk budget.
    exited_today = {e['position_id'] for e, _ in plan.events if e['event_type'] == 'EXIT_FILLED'}
    not_filled_today = {e['position_id'] for e, _ in plan.events if e['event_type'] in ('ENTRY_NO_FILL', 'ENTRY_FILL_FAILED')}
    used = {pid: p['accepted']['stress_loss_inr'] for pid, p in positions.items()
            if _holding(p) and pid not in exited_today and pid not in not_filled_today}
    held_symbols = {positions[pid]['symbol'] for pid in used}
    for c in candidates:
        stress = (c['plan'].get('stress') or {}).get('stress_loss_inr')
        reasons = []
        if blocking:
            reasons.append('KILL_SWITCH: ' + ','.join(blocking))
        if c['symbol'] in held_symbols:
            reasons.append('ALREADY_HOLDING')
        if not _valid_plan(c['plan']):
            reasons.append('INVALID_PLAN')
        elif sum(used.values()) + stress > budget:
            reasons.append(f'OPEN_RISK_BUDGET: used {sum(used.values()):.2f} + candidate {stress:.2f} > budget {budget:.2f}')
        pid = f"{STRATEGY_ID}:{c['symbol']}:{run_date}"
        contract = _contract(c, reasons, definition, rulebook_file, praman_watermark, code_commit, stress)
        if reasons:
            key = reasons[0].split(':')[0]
            ops['rejected'][key] = ops['rejected'].get(key, 0) + 1
            plan.events.append((_event('CANDIDATE_REJECTED', c['symbol'], run_date, dict(reasons=reasons),
                                       opportunity_id=c['opportunity_id'], decision_date=run_date), contract))
            continue
        p = c['plan']
        limit = p['decision_price'] + 0.5 * p['atr20'] if use_limit else None
        plan.events.append((_event('CANDIDATE_ACCEPTED', c['symbol'], run_date, dict(
            decision_price=p['decision_price'], atr20=p['atr20'], stop_level=p['stop_level'], quantity=p['quantity'],
            stress_loss_inr=stress, limit_price=limit, entry_policy=definition['entry']['policy'],
            budget_used_before_inr=sum(used.values()), budget_inr=budget),
            position_id=pid, opportunity_id=c['opportunity_id'], decision_date=run_date), contract))
        used[pid] = stress
        held_symbols.add(c['symbol'])
        ops['accepted'] += 1

    ops['positions_holding'] = len(used)
    ops['open_risk_inr'] = sum(used.values())
    ops['open_risk_budget_inr'] = budget
    ops['no_trade'] = ops['accepted'] == 0
    _write(desk_conn, version, run_date, plan, ops, rulebook.automation_level, rulebook_hash, cost_config_hash,
           code_commit, praman_watermark)
    return ops


def _settle_entry(praman_conn, p, pid, acc, day, run_date, use_limit, costs, per_trade):
    """One entry attempt on its single eligible session. Missing or unusable data is an operational
    failure (MISSING_DATA); an untouched limit is a normal NO_FILL. Session prices are put on the
    decision's share basis first (P8-044), so a bonus or split between decision and fill cannot
    make a raw post-split open look like a bargain against a pre-split limit."""
    bar = session_bar(praman_conn, p['symbol'], day, run_date)
    raw_open, raw_low = (bar or {}).get('open_price'), (bar or {}).get('low_price')
    try:
        factor = basis_factor(praman_conn, p['symbol'], p['decision_date'], day)
    except UnadjustableWindowError as exc:
        # Data are present and the engine works: an observed market event, not an operational failure.
        return _event('ENTRY_NO_FILL', p, day, dict(session=day, open=raw_open, low=raw_low, status='NO_FILL',
                      reason=f'UNADJUSTABLE_CORPORATE_ACTION between decision and fill: {exc}'), position_id=pid)
    opening = raw_open * factor if _finite(raw_open) else raw_open
    low = raw_low * factor if _finite(raw_low) else raw_low
    if use_limit:
        fill = limit_fill(dict(decision_price=acc['decision_price'], atr20=acc['atr20']), opening, low)
    else:
        usable = _finite(opening) and opening > 0
        fill = dict(limit=None, fill=opening if usable else None, status='FILL_OPEN' if usable else 'UNKNOWN',
                    reason='' if usable else 'Opening price unavailable')
    evidence = dict(session=day, open=opening, low=low, raw_open=raw_open, raw_low=raw_low, basis_factor=factor,
                    series=(bar or {}).get('series'), knowledge_date=(bar or {}).get('knowledge_date'),
                    row_id=(bar or {}).get('row_id'), limit=fill['limit'], status=fill['status'], reason=fill['reason'])
    if fill['fill'] is not None:
        price, qty = fill['fill'], acc['quantity']
        loss = planned_loss_inr(price, min(acc['stop_level'], price), qty, costs)
        return _event('ENTRY_FILLED', p, day, evidence | dict(
            price=price, quantity=qty, buy_cost_inr=round_trip_cost_inr(price, qty, costs, 'buy'),
            planned_loss_at_fill_inr=loss, per_trade_cap_inr=per_trade, per_trade_cap_breach_at_fill=loss > per_trade),
            position_id=pid)
    if fill['status'] == 'NO_FILL':
        return _event('ENTRY_NO_FILL', p, day, evidence, position_id=pid)
    return _event('ENTRY_FILL_FAILED', p, day, evidence | dict(failure='MISSING_DATA'), position_id=pid)


def _quantity_now(conn, p, day):
    try:
        return p['entry']['quantity'] * basis_factor(conn, p['symbol'], p['decision_date'], day)
    except UnadjustableWindowError:
        return p['entry']['quantity']  # recorded as-is; the exit reason already names the unadjustable action


def _valid_plan(plan):
    stress = (plan.get('stress') or {}).get('stress_loss_inr')
    return (all(_finite(plan.get(k)) and plan.get(k) > 0 for k in ('decision_price', 'atr20', 'stop_level'))
            and isinstance(plan.get('quantity'), int) and plan['quantity'] > 0 and _finite(stress) and stress >= 0)


RUN_FAILED_EVENT = 'S0_RUN_FAILED'


def classify_entry(event_type, detail):
    """Operational classification for the fill-failure switch (user decision 2026-10-04)."""
    if event_type == 'ENTRY_FILL_FAILED':
        return ks.OPERATIONAL_FAILURE
    if event_type == 'ENTRY_FILLED':
        return ks.ATTEMPT_OK
    if event_type == 'ENTRY_NO_FILL':
        return ks.NOT_ATTEMPTED if str(detail.get('reason', '')).startswith('CANCELLED') else ks.ATTEMPT_OK
    raise ValueError(f'{event_type} is not an entry outcome.')


def _entry_outcomes_since(conn, version, since):
    """Entry outcomes and whole-run engine failures (journalled by the nightly wrapper), in the order
    they were recorded, after the latest human reset."""
    rows = [(r['recorded_at'], classify_entry(r['event_type'], json.loads(r['detail'])))
            for r in conn.execute("SELECT event_type, detail, recorded_at FROM strategy_paper_events WHERE strategy_id=? "
                                  "AND strategy_version=? AND event_type IN ('ENTRY_FILLED','ENTRY_FILL_FAILED','ENTRY_NO_FILL') "
                                  'ORDER BY event_id', (STRATEGY_ID, version))]
    rows += [(r['recorded_at'], ks.OPERATIONAL_FAILURE)
             for r in conn.execute('SELECT recorded_at FROM journal_events WHERE event_type=? ORDER BY journal_event_id',
                                   (RUN_FAILED_EVENT,))]
    rows.sort(key=lambda r: r[0])
    return [outcome for recorded, outcome in rows if since is None or recorded > since]


def _contract(c, reasons, definition, rulebook_file, watermark, commit, stress):
    gates = c['gates']
    g5 = gates.get('G5')
    hard = any(r.split(':')[0] in ('KILL_SWITCH', 'OPEN_RISK_BUDGET', 'INVALID_PLAN', 'ALREADY_HOLDING') for r in reasons)
    return build_contract(
        symbol=c['symbol'], desk_state='SCREEN_PASS', hard_veto=hard,
        horizon=known('10d', 'Strategy 0 time limit: 10 global sessions after the fill session.'),
        evidence_completeness=known(dict(G2=gates.get('G2', {}).get('result')),
                                    'G2 evidence-sufficiency result; per-dimension coverage is not stored in the opportunity log.'),
        liquidity_state=(known(dict(result=g5['result'], reasons=g5['reasons']), 'G5 liquidity gate result.')
                         if g5 else unknown('G5 not recorded.', 'T0')),
        portfolio_incremental_risk=(known(dict(stress_loss_inr=stress), 'Frozen cost-inclusive stress loss of the plan.')
                                    if _finite(stress) else unknown('Plan stress loss unavailable.', 'T0')),
        invalidations=[f"Stop {c['plan'].get('stop_level')} (adjusted for corporate actions)",
                       f"Time limit {definition['time_limit_sessions']} sessions", 'Kill switch with EXIT_POSITIONS effect'],
        rejection_reasons=reasons, model_version='NONE: Strategy 0 baseline screen; no model',
        rulebook_version=rulebook_file, data_as_of=watermark, commit_hash=commit,
        extra=dict(strategy_id=STRATEGY_ID, opportunity_id=c['opportunity_id'],
                   purpose='Paper burn-in; acceptance is not an eligibility judgement.'))


def _write(conn, version, run_date, plan, ops, level, rulebook_hash, cost_hash, commit, watermark):
    conn.execute('SAVEPOINT strategy0_run')
    try:
        cursor = conn.execute('INSERT INTO strategy_runs (strategy_id,strategy_version,run_date,automation_level,rulebook_hash,'
                              'cost_config_hash,code_commit,praman_watermark,operational,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
                              (STRATEGY_ID, version, run_date, level, rulebook_hash, cost_hash, commit, watermark,
                               json.dumps(ops, sort_keys=True), _now()))
        run_id = cursor.lastrowid
        for event, contract in plan.events:
            cur = conn.execute('INSERT INTO strategy_paper_events (strategy_id,strategy_version,run_id,position_id,opportunity_id,'
                               'symbol,decision_date,event_type,event_date,detail,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                               (STRATEGY_ID, version, run_id, event['position_id'], event['opportunity_id'], event['symbol'],
                                event['decision_date'], event['event_type'], event['event_date'],
                                json.dumps(event['detail'], sort_keys=True, allow_nan=False), _now()))
            if contract is not None:
                record_contract(conn, contract, strategy_event_id=cur.lastrowid)
    except Exception:
        conn.execute('ROLLBACK TO strategy0_run')
        conn.execute('RELEASE strategy0_run')
        raise
    conn.execute('RELEASE strategy0_run')
    conn.commit()


def latest_operational(conn, run_date=None):
    """Operational summary of a run (visible); never contains P&L."""
    query = 'SELECT * FROM strategy_runs WHERE strategy_id=? ' + ('AND run_date=? ' if run_date else '') + 'ORDER BY run_id DESC LIMIT 1'
    row = conn.execute(query, (STRATEGY_ID, run_date) if run_date else (STRATEGY_ID,)).fetchone()
    return None if row is None else dict(row) | dict(operational=json.loads(row['operational']))
