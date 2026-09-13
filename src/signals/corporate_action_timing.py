"""The only sanctioned way for a TIMING-based signal (e.g. pre-announcement accumulation
detection) to read corporate_actions. EX_DATE_FALLBACK's knowledge_date is a safe stand-in for
adjustment purposes (see CLAUDE.md / docs/phase3_corporate_actions.md: an ex_date always follows
its announcement, so no adjusted-price query is ever wrong from using it) -- but it is NOT a real
announcement date, and a timing signal asking "how many days before the move did this become
public" would be silently wrong if it saw one. This module exists so that guarantee is structural,
not a comment future code has to remember.
"""
from __future__ import annotations

from ..bitemporal.guard import latest_as_of
from ..ingestion.nse_market_data.corporate_actions import EX_DATE_FALLBACK

def timing_reliable_corporate_actions(conn, symbol: str, as_of: str) -> list[dict]:
    """Same as `latest_as_of(conn, "corporate_actions", as_of, symbol=symbol)`, minus every row
    whose confidence_tier is EX_DATE_FALLBACK. Use this, never the raw guard call, for anything
    that reasons about WHEN an action became public rather than just whether/how to adjust a
    price.
    """
    rows = latest_as_of(conn, "corporate_actions", as_of, symbol=symbol)
    return [row for row in rows if row["confidence_tier"] != EX_DATE_FALLBACK]
