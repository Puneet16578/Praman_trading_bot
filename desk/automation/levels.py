"""Automation levels A0-A4 (TRADING_BLUEPRINT.md section 8, amendments 4-5).

Every automated action names the minimum level it needs; `require_level` refuses anything above
the active rulebook's `automation_level`. Broker-API order placement is refused at every level:
amendment 5 makes it a separate, explicitly approved task, and no broker code exists.
"""
LEVELS = ('A0', 'A1', 'A2', 'A3', 'A4')

# Minimum level per action. Unknown actions are refused, never guessed.
ACTION_LEVELS = {
    'research': 'A0',            # historical scanning and evaluation; no orders or paper fills
    'paper_auto': 'A1',          # automatic paper decisions, fills, monitoring and exits
    'order_ticket': 'A2',        # system-prepared ticket the user enters manually in their broker
    'auto_order_small': 'A3',    # constrained automatic orders (not implemented)
    'auto_order_broad': 'A4',    # not implemented
}
NEVER_PERMITTED = {
    'broker_api_order': 'Broker-API order placement needs a separate, explicitly approved task '
                        'including a SEBI retail-algo compliance check (TRADING_BLUEPRINT.md amendment 5).',
}


class AutomationRefused(PermissionError):
    pass


def require_level(rulebook, action):
    """Raise AutomationRefused unless `action` is permitted at the rulebook's automation level."""
    if action in NEVER_PERMITTED:
        raise AutomationRefused(NEVER_PERMITTED[action])
    if action not in ACTION_LEVELS:
        raise AutomationRefused(f'Unknown automated action {action!r}; refused.')
    active = getattr(rulebook, 'automation_level', None)
    if active not in LEVELS:
        raise AutomationRefused(f'Rulebook automation level {active!r} is invalid; refused.')
    needed = ACTION_LEVELS[action]
    if LEVELS.index(needed) > LEVELS.index(active):
        raise AutomationRefused(f'{action} needs automation level {needed}; the active rulebook allows {active}. '
                                'Raising it requires a new rulebook version and explicit user approval.')
    return needed
