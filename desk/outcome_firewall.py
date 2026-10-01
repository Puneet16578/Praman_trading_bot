"""Single calendar boundary for Desk outcome reads and calculations."""
from datetime import date

from shared.market_time import market_today

FORWARD_START = date(2026, 9, 16)
OUTCOMES_OPEN = date(2027, 6, 1)


class ForwardOutcomeBlocked(ValueError):
    pass


def require_outcome_access(event_date: str) -> None:
    event = date.fromisoformat(event_date)
    if event >= FORWARD_START and market_today() < OUTCOMES_OPEN:
        raise ForwardOutcomeBlocked("Forward-window outcomes are blocked before 2027-06-01.")


def evaluate_event(event_date: str, evaluator, *args, **kwargs):
    """Check before invoking any loader, query or calculation supplied by the evaluator."""
    require_outcome_access(event_date)
    return evaluator(*args, **kwargs)
