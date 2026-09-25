"""The demo's forward-window cutoff -- two layers, not one.

Layer 1 (structural, primary): demo/build_demo_store.py deletes every row with event_date OR
knowledge_date after DEMO_DATA_CUTOFF from every fact table in the demo store's own copy, before
the demo ever opens it. This is what actually stops a value DERIVED from a post-cutoff record (a
lead-time session count, an ASM stage) from ever being computable in the first place -- a pattern
filter over rendered text cannot catch a number like "40 sessions" that reveals a post-cutoff flag
exists without containing a date at all.

Layer 2 (redaction, secondary): redact_post_cutoff() below, applied to every dict the demo renders.
Belt-and-suspenders for any literal date string that reaches the demo despite layer 1 -- it cannot
by itself close the derived-value gap layer 1 exists to close, and is not relied on to.
"""
from __future__ import annotations
import re
from datetime import date

DEMO_DATA_CUTOFF = "2026-09-15"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REDACTED = "[redacted: after demo cutoff]"


def cutoff_as_date() -> date:
    y, m, d = (int(x) for x in DEMO_DATA_CUTOFF.split("-"))
    return date(y, m, d)


def redact_post_cutoff(value, cutoff: str = DEMO_DATA_CUTOFF):
    """Recursively walks dicts/lists/tuples; any string shaped exactly like a date (YYYY-MM-DD)
    and later than `cutoff` is replaced with REDACTED. Non-date strings, numbers, and dates on or
    before cutoff pass through unchanged. This is a pattern filter, not a data-level guarantee --
    see the module docstring for why layer 1 (the truncated store) is the real control."""
    if isinstance(value, dict):
        return {k: redact_post_cutoff(v, cutoff) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        seq = [redact_post_cutoff(v, cutoff) for v in value]
        return type(value)(seq) if not isinstance(value, list) else seq
    if isinstance(value, str) and _DATE_RE.match(value) and value > cutoff:
        return REDACTED
    return value
