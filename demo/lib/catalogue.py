"""Picker/search data access for the Event Browser -- reads this demo's OWN
data/demo/event_classifications.csv (built by demo/build_demo_store.py from the cutoff-truncated
demo store, via the existing, unmodified scripts/build_event_classifications.py pipeline), never
the production data/processed/event_classifications.csv. The production file was built with full
knowledge -- an event's own sessions_to_subsequent_flag/subsequent_flag_note there can name a flag
that happened after the demo's cutoff. The demo's own copy cannot: it was computed from a store
that has no rows past the cutoff at all, so a flag that would only be visible after the cutoff was
never in the data this file's own build pipeline saw, not merely blanked after the fact.
"""
from __future__ import annotations
import csv
from functools import lru_cache

from .store import DEMO_CLASSIFICATIONS_PATH


@lru_cache(maxsize=1)
def load_rows() -> list[dict]:
    if not DEMO_CLASSIFICATIONS_PATH.exists():
        raise FileNotFoundError(
            f"{DEMO_CLASSIFICATIONS_PATH} does not exist. Run `python demo/build_demo_store.py` first."
        )
    with open(DEMO_CLASSIFICATIONS_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def filter_rows(*, event_date_from: str | None = None, event_date_to: str | None = None,
                 classification: str | None = None, cap_band: str | None = None,
                 symbol_contains: str | None = None) -> list[dict]:
    rows = load_rows()
    out = []
    for r in rows:
        if event_date_from and r["event_date"] < event_date_from:
            continue
        if event_date_to and r["event_date"] > event_date_to:
            continue
        if classification and r["classification"] != classification:
            continue
        if cap_band and r["cap_band"] != cap_band:
            continue
        if symbol_contains and symbol_contains.upper() not in r["symbol"].upper():
            continue
        out.append(r)
    return out


def symbol_events(symbol: str) -> list[dict]:
    """Every catalogued event for one symbol, sorted by date -- used by the "search a symbol/date
    range" panel, including to show that a real, large move is ABSENT from the catalogue (e.g.
    RELIANCE around its 2023-07-20 demerger exclusion) rather than silently misrepresented."""
    rows = [r for r in load_rows() if r["symbol"].upper() == symbol.upper()]
    return sorted(rows, key=lambda r: r["event_date"])


def known_classifications() -> list[str]:
    return sorted({r["classification"] for r in load_rows()})


def known_cap_bands() -> list[str]:
    return sorted({r["cap_band"] for r in load_rows() if r["cap_band"]})
