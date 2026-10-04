"""The Strategy 0 outcome seal (session item B4; TRADING_BLUEPRINT.md amendment 3).

Profit, loss and outcome metrics of a sealed strategy's decisions dated on or after the forward
start are stored but never computed into reports or displayed before outcomes open. Operational
metrics stay visible. Both dates come from the Desk's single forward-window boundary
(desk/outcome_firewall.py: FORWARD_START, OUTCOMES_OPEN); none is restated here.

Every outcome reader goes through `require_unsealed`, with no exception. In particular the P&L
brakes (drawdown and losing streak) are EXEMPT for a sealed strategy until outcomes open (user
decision 2026-10-04): they are not evaluated at all, so no sealed P&L is read and no freeze can
disclose anything about the forward window. After outcomes open they apply normally.
"""
from datetime import date

from desk.outcome_firewall import FORWARD_START, OUTCOMES_OPEN
from shared.market_time import market_today

SEALED_STRATEGIES = frozenset({'S0'})


class SealedOutcome(PermissionError):
    pass


def _today(today):
    if today is None:
        return market_today()
    return date.fromisoformat(today) if isinstance(today, str) else today


def is_sealed(strategy_id, decision_date, today=None):
    return (strategy_id in SEALED_STRATEGIES and date.fromisoformat(decision_date) >= FORWARD_START
            and _today(today) < OUTCOMES_OPEN)


def require_unsealed(strategy_id, decision_date, today=None):
    if is_sealed(strategy_id, decision_date, today):
        raise SealedOutcome(f'{strategy_id} outcomes for decisions dated {decision_date} are sealed until '
                            f'{OUTCOMES_OPEN.isoformat()}.')


def pnl_brake_exemption(strategy_id, today=None):
    """Reason the P&L brakes are exempt for `strategy_id` today, or None when they apply."""
    if strategy_id in SEALED_STRATEGIES and _today(today) < OUTCOMES_OPEN:
        return (f'P&L brakes exempt until {OUTCOMES_OPEN.isoformat()}: outcomes are sealed and this paper '
                'book protects no real capital (user decision 2026-10-04)')
    return None


def realized_pnl(entry, exit_):
    """Cost-inclusive realized P&L of one closed position from its stored fill events."""
    return (exit_['price'] * exit_['quantity'] - exit_['sell_cost_inr']
            - entry['price'] * entry['quantity'] - entry['buy_cost_inr'])


def position_outcomes(positions, strategy_id, today=None):
    """Realized P&L per closed position. Refused for any sealed decision."""
    out = {}
    for pid, position in positions.items():
        if position.get('exit') is None or position.get('entry') is None:
            continue
        require_unsealed(strategy_id, position['decision_date'], today)
        out[pid] = realized_pnl(position['entry'], position['exit'])
    return out


def brake_inputs(positions, strategy_id, today=None, since_recorded_at=None):
    """(exit_date, pnl) in exit order for positions closed after the latest reset, for the P&L
    brakes. Refused for any sealed decision, exactly like every other outcome reader."""
    closed = [p for p in positions.values() if p.get('exit') is not None and p.get('entry') is not None
              and (since_recorded_at is None or p['exit']['recorded_at'] > since_recorded_at)]
    for p in closed:
        require_unsealed(strategy_id, p['decision_date'], today)
    closed.sort(key=lambda p: (p['exit']['event_date'], p['exit']['event_id']))
    return [(p['exit']['event_date'], realized_pnl(p['entry'], p['exit'])) for p in closed]
