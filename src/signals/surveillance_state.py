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
from dataclasses import dataclass

from ..bitemporal.guard import read_as_of

ENTRY = "ENTRY"
STAGE_CHANGE = "STAGE_CHANGE"
EXIT = "EXIT"

FAR_FUTURE_AS_OF = "2099-01-01"  # same "give me everything, filter in memory" convention as
                                 # event_catalogue.py -- see build_surveillance_timeline below

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

@dataclass
class SurveillanceTimeline:
    """Precomputed per-symbol ENTRY timeline for a question `current_surveillance_state()` cannot
    answer on its own: not "what was the state as of T" but "when, if ever, was this symbol FIRST
    flagged after T." Built once per symbol (one query) from every ENTRY transition, not
    per-question -- the same batch-then-replay shape as event_catalogue.py's SymbolHistory.

    Deliberately retrospective (FAR_FUTURE_AS_OF, full/later knowledge), like Phase 6's outcome
    labels -- this answers "what actually happened later," not a live-as-of-T signal, so using
    complete knowledge is correct here and would NOT be for a predictive signal (see
    event_catalogue.py's module docstring for that distinction, which is why this class lives
    next to current_surveillance_state() rather than replacing its bitemporal-correct behavior)."""
    entries: list[dict]  # every ENTRY row, any mechanism, sorted by event_date

    def first_entry_after(self, date: str) -> dict | None:
        """Earliest ENTRY strictly after `date`, or None if this symbol was never (subsequently)
        flagged. Takes the min by event_date rather than assuming `entries` arrives pre-sorted --
        real per-symbol ENTRY counts are small (a handful at most), so this is cheap regardless."""
        candidates = [row for row in self.entries if row["event_date"] > date]
        if not candidates:
            return None
        return min(candidates, key=lambda r: r["event_date"])

def build_surveillance_timeline(conn, symbol: str) -> SurveillanceTimeline:
    rows = read_as_of(conn, "surveillance_flags", FAR_FUTURE_AS_OF, symbol=symbol)
    entries = sorted(
        (r for r in rows if r["action_type"] == ENTRY),
        key=lambda r: (r["event_date"], r["knowledge_date"]),
    )
    return SurveillanceTimeline(entries=entries)
