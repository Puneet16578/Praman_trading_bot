"""Deterministic kill switches (TRADING_BLUEPRINT.md section 6.3; session item B2).

Each switch is a pure function of explicit inputs returning a Trip (triggered or not, with the
evidence). `evaluate_and_log` appends a kill_switch_events row whenever a switch's state changes
(TRIGGERED / CLEARED); a latched switch stays TRIGGERED until a human appends a RESET with a
reason. Nothing is ever updated or deleted.

Effects, strongest first:
- NO_NEW_TRADES: stale or inconsistent data, or risk state unavailable. Re-evaluated every run.
- FREEZE_ENTRIES: drawdown or losing-streak brake; exits are still managed. Latched.
- DISABLE_AUTO_ENTRIES: repeated paper-fill failures. Latched.
- OPERATIONAL_GATE_FAIL: an open high-severity or critical defect (the readiness gate also fails).
- REVERT_TO_PAPER_ONLY: calibration/edge degradation. Defined, INACTIVE until T4: it never trips.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import json
import math

from desk.outcome_firewall import OUTCOMES_OPEN

BLOCKS_ENTRIES = {'NO_NEW_TRADES', 'FREEZE_ENTRIES', 'DISABLE_AUTO_ENTRIES'}
LATCHED = {'DRAWDOWN_OR_LOSING_STREAK', 'REPEATED_FILL_FAILURES'}

SWITCHES = {
    'DATA_STALE_OR_INCONSISTENT': 'NO_NEW_TRADES',
    'RISK_STATE_UNAVAILABLE': 'NO_NEW_TRADES',
    'DRAWDOWN_OR_LOSING_STREAK': 'FREEZE_ENTRIES',
    'REPEATED_FILL_FAILURES': 'DISABLE_AUTO_ENTRIES',
    'OPEN_CRITICAL_DEFECT': 'OPERATIONAL_GATE_FAIL',
    'CALIBRATION_EDGE_DEGRADATION': 'REVERT_TO_PAPER_ONLY',
}
INACTIVE = {'CALIBRATION_EDGE_DEGRADATION': 'Defined now; inactive until T4 supplies calibrated models.'}

PLAN_FIELDS = ('decision_price', 'atr20', 'stop_level', 'quantity', 'stress')


@dataclass(frozen=True)
class Trip:
    switch: str
    triggered: bool
    detail: dict = field(default_factory=dict)
    sealed: bool = False

    @property
    def effect(self):
        return SWITCHES[self.switch]


def data_health(run_date, latest_store_date, today, isin_status, candidate_plans, stale_after_days):
    """Stale: the run is not for the store's latest session, or that session is too old.
    Inconsistent: identity map unhealthy, or a passed candidate lacks a field the engine needs."""
    problems = []
    if latest_store_date is None:
        problems.append('No bhavcopy session in the store.')
    else:
        if run_date != latest_store_date:
            problems.append(f'Run date {run_date} is not the latest stored session {latest_store_date}.')
        age = (date.fromisoformat(today) - date.fromisoformat(latest_store_date)).days
        if age > stale_after_days:
            problems.append(f'Latest stored session is {age} calendar days old (limit {stale_after_days}).')
    if isin_status != 'OK':
        problems.append(f'ISIN map health is {isin_status}.')
    for symbol, plan in candidate_plans:
        missing = [k for k in PLAN_FIELDS if not _present(plan.get(k))]
        if isinstance(plan.get('stress'), dict) and not _finite(plan['stress'].get('stress_loss_inr')):
            missing.append('stress.stress_loss_inr')
        if missing:
            problems.append(f'{symbol}: passed plan lacks {missing}.')
    return Trip('DATA_STALE_OR_INCONSISTENT', bool(problems), dict(problems=problems))


def risk_state(open_stress_losses, budget_inr, config_error=None):
    """Unavailable when the rulebook/cost config cannot load, the budget is unusable, or any open
    or pending position lacks a finite, non-negative stress loss."""
    problems = [] if config_error is None else [f'Configuration unavailable: {config_error}']
    if not _finite(budget_inr) or budget_inr <= 0:
        problems.append('Open-risk budget is unavailable.')
    bad = [pid for pid, loss in open_stress_losses.items() if not _finite(loss) or loss < 0]
    if bad:
        problems.append(f'Positions without a usable stress loss: {sorted(bad)}.')
    return Trip('RISK_STATE_UNAVAILABLE', bool(problems), dict(problems=problems))


def drawdown_or_streak(closed_pnl_by_exit_date, run_date, capital_inr, drawdown_pct, streak_count, *, sealed):
    """Freeze entries if this calendar month's realized loss reaches the brake, or the latest
    `streak_count` closed trades all lost. Inputs are (exit_date, realized_pnl_inr) in exit order.
    For a sealed strategy only the trigger is visible; the amounts stay in the sealed detail."""
    month = run_date[:7]
    month_pnl = sum(p for d, p in closed_pnl_by_exit_date if d[:7] == month and d <= run_date)
    limit = capital_inr * drawdown_pct / 100
    recent = [p for d, p in closed_pnl_by_exit_date if d <= run_date][-streak_count:]
    streak = len(recent) == streak_count and all(p < 0 for p in recent)
    triggered = month_pnl <= -limit or streak
    detail = dict(month=month, month_realized_pnl_inr=month_pnl, drawdown_limit_inr=limit,
                  losing_streak=streak, streak_count=streak_count)
    return Trip('DRAWDOWN_OR_LOSING_STREAK', triggered, detail, sealed=sealed)


def fill_failures(entry_outcomes, threshold):
    """Disable automatic entries after `threshold` consecutive fill failures (unusable price data,
    not an untouched limit). `entry_outcomes` lists entry event types in chronological order."""
    run = 0
    for outcome in entry_outcomes:
        if outcome == 'ENTRY_FILL_FAILED':
            run += 1
        elif outcome == 'ENTRY_FILLED':
            run = 0
    return Trip('REPEATED_FILL_FAILURES', run >= threshold, dict(consecutive_failures=run, threshold=threshold))


def open_critical_defect(high, unclassified):
    return Trip('OPEN_CRITICAL_DEFECT', bool(high or unclassified),
                dict(open_high_or_critical=list(high), unclassified_open=list(unclassified)))


def calibration_degradation():
    return Trip('CALIBRATION_EDGE_DEGRADATION', False, dict(status='INACTIVE', why=INACTIVE['CALIBRATION_EDGE_DEGRADATION']))


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _present(value):
    return value not in (None, {}, '') and (not isinstance(value, (int, float)) or _finite(value))


def latest_states(conn, scope):
    """Latest logged state per switch for `scope` (TRIGGERED / CLEARED / RESET)."""
    rows = conn.execute('SELECT * FROM kill_switch_events WHERE scope=? ORDER BY event_id', (scope,)).fetchall()
    states = {}
    for row in rows:
        states[row['switch']] = dict(row)
    return states


def evaluate_and_log(conn, trips, *, scope, run_date):
    """Append a row for every state change, honouring latches. Returns the effective state per
    switch after this run: True means the switch is active (its effect applies)."""
    previous = latest_states(conn, scope)
    effective = {}
    for trip in trips:
        before = previous.get(trip.switch)
        was_active = before is not None and before['state'] == 'TRIGGERED'
        latched = trip.switch in LATCHED and was_active
        active = trip.triggered or latched
        if trip.triggered and not was_active:
            _append(conn, trip, 'TRIGGERED', scope, run_date)
        elif not active and was_active:
            _append(conn, trip, 'CLEARED', scope, run_date)
        effective[trip.switch] = active
    conn.commit()
    return effective


def reset(conn, switch, *, scope, run_date, reason):
    """Human release of a latched switch. Requires a reason; appended, never an edit."""
    if switch not in LATCHED:
        raise ValueError(f'{switch} is not latched; it clears itself when its condition clears.')
    if not reason or not reason.strip():
        raise ValueError('A kill-switch reset requires a reason.')
    state = latest_states(conn, scope).get(switch)
    if state is None or state['state'] != 'TRIGGERED':
        raise ValueError(f'{switch} is not currently triggered for {scope}.')
    conn.execute('INSERT INTO kill_switch_events (switch,state,effect,scope,run_date,detail,sealed,reason,recorded_at) '
                 'VALUES (?,?,?,?,?,?,?,?,?)',
                 (switch, 'RESET', SWITCHES[switch], scope, run_date, json.dumps({}), 0, reason.strip(), _now()))
    conn.commit()


def _append(conn, trip, state, scope, run_date):
    conn.execute('INSERT INTO kill_switch_events (switch,state,effect,scope,run_date,detail,sealed,reason,recorded_at) '
                 'VALUES (?,?,?,?,?,?,?,?,?)',
                 (trip.switch, state, trip.effect, scope, run_date, json.dumps(trip.detail, sort_keys=True, default=str),
                  int(trip.sealed), None, _now()))


def display_lines(conn, scope, *, sealed_display=lambda row: bool(row['sealed'])):
    """Status lines for every defined switch; sealed detail is replaced, never shown early."""
    states = latest_states(conn, scope)
    lines = []
    for switch, effect in SWITCHES.items():
        row = states.get(switch)
        if switch in INACTIVE:
            lines.append(f'  {switch}: INACTIVE ({INACTIVE[switch]})')
            continue
        if row is None:
            lines.append(f'  {switch}: clear (never triggered)')
            continue
        active = row['state'] == 'TRIGGERED'
        detail = f'detail sealed until {OUTCOMES_OPEN.isoformat()}' if sealed_display(row) else row['detail']
        lines.append(f"  {switch}: {'ACTIVE -> ' + effect if active else 'clear'} "
                     f"(last {row['state']} {row['run_date']}; {detail})")
    return lines


def _now():
    return datetime.now(timezone.utc).isoformat()
