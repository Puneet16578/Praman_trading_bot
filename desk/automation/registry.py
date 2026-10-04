"""Trading strategy registry (session item B4; blueprint section 7, "keep failed strategies visible").

Every strategy is versioned and never deleted (append-only triggers). A changed definition needs a
new version; a status change appends a new revision with the same definition. Strategy 0's
definition, including its entry policy, is fixed here in code and verified against the stored row
on every run, so the engine can never silently run rules other than the registered ones.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from desk.outcome_firewall import FORWARD_START, OUTCOMES_OPEN

ROOT = Path(__file__).resolve().parents[2]
FOLLOWUP2 = ROOT / 'docs/desk/shadow_replay_followup2_results.json'
PRIMARY = 'Primary 2019-2025'

ENTRY_RULE = ('Use the limit entry if follow-up 2 shows a lower per-trade breach rate at the fill than the '
              'original convention, with the paired difference\'s 95% interval entirely below zero, AND a '
              'fill rate of at least 60%. Otherwise use the original convention. Stated by the user in their '
              'message of 2026-10-04, applied to the registered primary period.')


class RegistryError(RuntimeError):
    pass


def entry_policy(path=FOLLOWUP2):
    """Apply the user's pre-stated rule to the committed follow-up 2 results."""
    raw = path.read_bytes().replace(b'\r\n', b'\n')  # stable across checkout line endings
    period = json.loads(raw)['periods'][PRIMARY]
    diff = period['differences']['per_trade_breach_rate']
    fill = period['variants']['limit']['fill_rate']
    lower_breach = diff['estimate'] is not None and diff['estimate'] < 0
    interval_below = diff['interval95'] is not None and diff['interval95'][1] < 0
    fill_ok = fill['estimate'] is not None and fill['estimate'] >= 0.60
    use_limit = lower_breach and interval_below and fill_ok
    return dict(
        policy='LIMIT_DECISION_PLUS_0.5_ATR20' if use_limit else 'NEXT_OPEN',
        rule=ENTRY_RULE,
        evaluation=dict(period=PRIMARY, breach_difference=diff['estimate'], breach_difference_interval95=diff['interval95'],
                        limit_fill_rate=fill['estimate'], lower_breach_rate=lower_breach,
                        interval_entirely_below_zero=interval_below, fill_rate_at_least_60pct=fill_ok),
        why=('All three conditions hold, so the limit entry applies.' if use_limit else
             'At least one condition fails, so the original next-open convention applies.'),
        source=f"{path.relative_to(ROOT).as_posix()}; LF-normalized sha256={hashlib.sha256(raw).hexdigest()}",
    )


def strategy0_definition(path=FOLLOWUP2):
    policy = entry_policy(path)
    return dict(
        candidates='SCREEN_PASS rows of opportunity_log for the run date (desk scan), ordered by symbol then '
                   'opportunity_id; stated before any run.',
        sizing='Frozen plan quantity from the active rulebook, cost-inclusive per the G6 fix (7801550); never resized.',
        entry=policy,
        entry_mechanics=('Limit = decision price + 0.5 x ATR20 on the next global session only: fill at the open if '
                         'at or below the limit, else at the limit if the session low reaches it, else NO_FILL. '
                         'Missing or unusable bars are a fill FAILURE. Pending entries are cancelled if an '
                         'entry-blocking kill switch is active.' if policy['policy'].startswith('LIMIT') else
                         'Fill at the next global session open. Missing or unusable bars are a fill FAILURE.'),
        stop='Frozen plan stop, adjusted for corporate actions with the store adjustment factor. Monitoring '
             'starts the session after the fill: open at or below the stop fills at the open, else a low at or '
             'below the stop fills at the stop.',
        time_limit_sessions=10,
        exits='Stop; 10 global sessions after the fill session (exit at the next open); or a kill switch whose '
              'effect is EXIT_POSITIONS (none is active today).',
        portfolio='Own notional book, separate from manual paper trades: one position per symbol; open, pending '
                  'and exiting positions count against the rulebook open-risk budget on stress loss '
                  '(capital x max_open_risk_pct). Candidates over the budget are rejected with the reason logged.',
        kill_switch_parameters=dict(
            fill_failure_threshold=3,
            fill_failure_threshold_status=(
                'APPROVED by the user on 2026-10-04: 3 consecutive OPERATIONAL failures (missing or unusable '
                'next-session data, or an engine error, including a crashed nightly run). An untouched limit is '
                'a normal NO_FILL: never a failure, and it ends a failure streak; a cancelled entry is not counted.'),
            drawdown_and_streak=(
                f'EXEMPT for Strategy 0 until {OUTCOMES_OPEN.isoformat()} (user decision 2026-10-04): the brakes '
                'would read sealed P&L, and even a visible freeze discloses forward-window information; the '
                'paper book protects no real capital. From that date the rulebook values apply '
                '(risk.monthly_drawdown_brake_pct, behavioural_brakes.consecutive_loss_brake_count). '
                'All data and operational kill switches stay active.'),
            stale_after_days='desk.ingestion_health.STALE_AFTER_DAYS (existing PROPOSED value).'),
        seal=(f'P&L and outcome metrics for decisions dated on or after {FORWARD_START.isoformat()} are stored but '
              f'never computed into reports or displayed before {OUTCOMES_OPEN.isoformat()}; operational metrics '
              'stay visible.'),
    )


STRATEGY_0 = dict(strategy_id='S0', version=1, name='baseline screen', status='PAPER_BURN_IN',
                  purpose='Exercise the automation end to end: candidates, sizing, kill switches, fills, monitoring, '
                          'exits and the seal. It is NOT expected to be profitable, and its results are not evidence '
                          'of an edge.')
MANUAL = dict(strategy_id='manual', version=1, name='manual discretionary paper trades', status='ACTIVE_MANUAL',
              purpose="The user's own discretionary paper trades (desk assess / desk paper open). Kept separate "
                      'from Strategy 0 and fully visible; never sealed.',
              definition=dict(book='paper_trade_events'))


def _hash(definition):
    return hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def current(conn, strategy_id):
    row = conn.execute('SELECT * FROM trading_strategies WHERE strategy_id=? ORDER BY version DESC, revision DESC LIMIT 1',
                       (strategy_id,)).fetchone()
    return None if row is None else dict(row) | dict(definition=json.loads(row['definition']))


def register(conn, *, strategy_id, version, name, status, purpose, definition):
    """Idempotent for an identical definition; refuses a changed definition under the same version."""
    existing = conn.execute('SELECT * FROM trading_strategies WHERE strategy_id=? AND version=? ORDER BY revision',
                            (strategy_id, version)).fetchall()
    digest = _hash(definition)
    if existing:
        if existing[-1]['content_hash'] != digest:
            raise RegistryError(f'{strategy_id} v{version} is registered with a different definition; '
                                'register a new version instead.')
        return dict(existing[-1]) | dict(definition=json.loads(existing[-1]['definition']))
    conn.execute('INSERT INTO trading_strategies (strategy_id,version,revision,name,status,purpose,definition,content_hash,recorded_at) '
                 'VALUES (?,?,?,?,?,?,?,?,?)',
                 (strategy_id, version, 1, name, status, purpose, json.dumps(definition, sort_keys=True), digest,
                  datetime.now(timezone.utc).isoformat()))
    conn.commit()
    return current(conn, strategy_id)


def set_status(conn, strategy_id, version, status):
    rows = conn.execute('SELECT * FROM trading_strategies WHERE strategy_id=? AND version=? ORDER BY revision',
                        (strategy_id, version)).fetchall()
    if not rows:
        raise RegistryError(f'{strategy_id} v{version} is not registered.')
    last = rows[-1]
    conn.execute('INSERT INTO trading_strategies (strategy_id,version,revision,name,status,purpose,definition,content_hash,recorded_at) '
                 'VALUES (?,?,?,?,?,?,?,?,?)',
                 (strategy_id, version, last['revision'] + 1, last['name'], status, last['purpose'], last['definition'],
                  last['content_hash'], datetime.now(timezone.utc).isoformat()))
    conn.commit()


def ensure_registered(conn, path=FOLLOWUP2):
    """Register Strategy 0 and the manual book if absent; verify Strategy 0's stored definition."""
    register(conn, **MANUAL)
    return register(conn, **STRATEGY_0, definition=strategy0_definition(path))
