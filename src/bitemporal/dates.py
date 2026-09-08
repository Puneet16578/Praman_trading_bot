"""One date-string validator, shared by the guard (as_of) and the store (event_date/knowledge_date)
-- Section 7 has no room for two independent notions of "a valid date" drifting apart."""
from __future__ import annotations
from datetime import date
import re

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class DateValidationError(ValueError):
    """Raised when a value that must be a calendar date is missing, malformed, or the wrong type."""

def parse_date_str(value, field_name: str = "date") -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and _DATE_RE.match(value):
        return value
    raise DateValidationError(f"{field_name} must be a date or 'YYYY-MM-DD' string; got {value!r}.")
