"""Development-only input boundary, checked before queries and source-file reads."""
from datetime import date

READ_END = "2024-12-31"


class T1ReadRefused(ValueError):
    """A requested source range reaches beyond the authorised development data."""


def check_date(day: str) -> str:
    date.fromisoformat(day)
    if day > READ_END:
        raise T1ReadRefused(f"T1 input read after {READ_END} refused: {day}")
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
