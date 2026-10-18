"""Development-only input boundary, checked before queries and source-file reads."""
from datetime import date
from contextlib import contextmanager
from contextvars import ContextVar

READ_END = "2024-12-31"
HOLDOUT_END = "2025-12-31"
_read_end = ContextVar('t1_read_end', default=READ_END)


@contextmanager
def holdout_reads():
    """Explicit authorisation scope; development defaults remain sealed at 2024."""
    token = _read_end.set(HOLDOUT_END)
    try:
        yield
    finally:
        _read_end.reset(token)


class T1ReadRefused(ValueError):
    """A requested source range reaches beyond the authorised development data."""


def check_date(day: str) -> str:
    date.fromisoformat(day)
    if day > _read_end.get():
        raise T1ReadRefused(f"T1 input read after {_read_end.get()} refused: {day}")
    return day


def select_range(first: str, last: str, end: str = READ_END) -> bool:
    """Skip wholly later files; refuse mixed ranges before opening their contents."""
    check_date(end)
    date.fromisoformat(first)
    date.fromisoformat(last)
    if first > last:
        raise T1ReadRefused("Invalid input-file date range")
    if first > end:
        return False
    if last > end:
        raise T1ReadRefused("Input file crosses the authorised end; cannot read it")
    return True
