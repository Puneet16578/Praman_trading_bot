"""Derives current ASM/GSM membership+stage as of a date from surveillance_flags' own transition
stream (ENTRY/STAGE_CHANGE/EXIT) -- the table records transitions, not a current-state snapshot,
so "was this symbol under ASM at date T, and at what stage" has to be replayed, not looked up
directly.

Not the same kind of timing concern as corporate_actions' EX_DATE_FALLBACK tier: surveillance_flags
carries no confidence tier at all, and every knowledge_date is a real circular publication date
(see event_catalogue.py's module docstring for why that distinction matters and where it does NOT
apply -- this module is the other place it doesn't apply either, since it answers "what was
publicly true as of T," not a corporate-action announcement-timing question).

Gates on BOTH knowledge_date<=as_of (bitemporal visibility -- was this publicly known by T) AND
event_date<=as_of (has this transition actually taken effect by T) -- deliberately not relying on
knowledge_date<=event_date the way event_catalogue.py's adjustment path relies on that guarantee
for corporate_actions. That guarantee does NOT hold here: a direct check found 4 real
surveillance_flags rows with knowledge_date > event_date (docs/phase4_asm_gsm_sourcing.md), genuine
NSE source inconsistencies, not parsing errors. Gating on both conditions independently means this
module is correct regardless of which order a given real row's two dates happen to be in.
"""
from __future__ import annotations

from ..bitemporal.guard import read_as_of

ENTRY = "ENTRY"
STAGE_CHANGE = "STAGE_CHANGE"
EXIT = "EXIT"

def current_surveillance_state(conn, symbol: str, as_of: str) -> dict[str, str | None]:
    """Returns {mechanism: current_stage} for every mechanism (ASM_LT, ASM_ST, GSM) with at least
    one transition visible and effective as of `as_of`. A mechanism mapped to None means the
    symbol WAS under it at some point but has since EXITed -- distinct from a mechanism absent
    from the dict entirely, which means no visible/effective row exists for it at all as of this
    date (never flagged, or not yet knowledge-dated/effective)."""
    rows = read_as_of(conn, "surveillance_flags", as_of, symbol=symbol)
    effective = [r for r in rows if r["event_date"] <= as_of]

    by_mechanism: dict[str, list[dict]] = {}
    for row in effective:
        by_mechanism.setdefault(row["mechanism"], []).append(row)

    state: dict[str, str | None] = {}
    for mechanism, transitions in by_mechanism.items():
        transitions.sort(key=lambda r: (r["event_date"], r["knowledge_date"], r["row_id"]))
        stage = None
        for t in transitions:
            if t["action_type"] in (ENTRY, STAGE_CHANGE):
                stage = t["to_stage"]
            elif t["action_type"] == EXIT:
                stage = None
        state[mechanism] = stage
    return state
