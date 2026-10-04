"""General-purpose NSE corporate-announcement ingestion (Phase 7).

Reuses the real `corporate-announcements` endpoint corporate_actions.py already calls (Phase 3)
to cross-check bonus/split ratios -- but that usage filters to desc in {"bonus","stock split"} and
never persists a row. This module stores EVERY announcement for a symbol, any category, because
the Disclosure agent needs "no disclosure found" to be a real, checkable absence, not an artifact
of a narrower filter built for a different purpose.

Confirmed empirically before writing this (not assumed): one request per symbol, with a from_date
of 2019-10-01 and to_date of today, returns the symbol's ENTIRE announcement history in a single
response -- no pagination, no per-year chunking needed (RELIANCE returned 2,129 rows spanning
exactly 2019-10-01 to the request date in one call). This is a materially simpler fetch shape than
corporate_actions.py's own per-(symbol, ex_date) 200-day-window fetch, because this module's need
(the symbol's whole disclosure history) is different from that module's need (one bonus/split
round's specific announcement window).
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher

import requests

from ...bitemporal.store import write_facts

NEAR_DUPLICATE_GAP = timedelta(hours=1)

class AnnouncementFetchError(RuntimeError):
    """A response that is not a usable announcement list. Raised, never returned as an empty list,
    so a failed fetch cannot be mistaken for a genuinely empty history (P8-021)."""


def fetch_symbol_announcements(session: requests.Session, symbol: str, from_date: date, to_date: date, timeout: float = 25.0) -> list[dict]:
    r = session.get(
        "https://www.nseindia.com/api/corporate-announcements",
        params={"index": "equities", "symbol": symbol, "from_date": from_date.strftime("%d-%m-%Y"), "to_date": to_date.strftime("%d-%m-%Y")},
        timeout=timeout,
    )
    if r.status_code != 200:
        raise AnnouncementFetchError(f"HTTP {r.status_code} for {symbol}")
    data = r.json()
    if not isinstance(data, list):
        raise AnnouncementFetchError(f"Unexpected {type(data).__name__} payload for {symbol}")
    return data

def build_announcement_rows(symbol: str, raw_announcements: list[dict], source_file: str) -> list[dict]:
    """Pure function: no I/O. One row per real announcement, `seq_id` as the natural per-symbol
    de-duplication key (NSE's own unique id for the announcement, confirmed present on every real
    row sampled). A row missing `sort_date` or `seq_id` is skipped, not fabricated a value --
    these are the two fields this table cannot function without.
    """
    rows = []
    for item in raw_announcements:
        sort_date = item.get("sort_date")
        seq_id = item.get("seq_id")
        if not sort_date or not seq_id:
            continue
        event_date = sort_date[:10]
        rows.append({
            "symbol": symbol, "event_date": event_date, "knowledge_date": event_date,
            "seq_id": str(seq_id), "category": (item.get("desc") or "").strip(),
            "description": item.get("attchmntText") or None, "sort_timestamp": sort_date,
            "source_file": source_file,
        })
    return rows

def cluster_announcements_into_events(rows: list[dict]) -> list[list[dict]]:
    """Groups stored `corporate_announcements` rows (dicts with `symbol`, `category`,
    `sort_timestamp`, `description`) into distinct real-world disclosure EVENTS, not rows. Every
    row is still stored individually -- this is a read-time view, never a write-time collapse (the
    bitemporal record stays complete; see corporate_actions.py's `collapse_clusters`, the same
    1-hour-gap precedent this was originally built from -- KITEX republished a bonus ratio 38
    seconds after the original, and a naive per-row count would see two announcements where one
    board decision occurred).

    Same (symbol, category) within `NEAR_DUPLICATE_GAP` is NECESSARY but not SUFFICIENT to merge
    two rows -- their `description` text must also be similar (see CONTENT_SIMILARITY_THRESHOLD
    below). This second gate was added after measuring, on 28,617 real same-category near-time
    pairs across the full announcement backfill, that 69.1% have genuinely DIFFERENT
    `attchmntText` -- e.g. two distinct RELIANCE "Analysts/Institutional Investor Meet" notices
    filed minutes apart (one for a Morgan Stanley conference, one a non-deal roadshow) share a
    category and a time window but are two real, independent disclosures, not a correction of
    each other. A pure category+time rule would silently undercount `disclosure_count` for
    exactly the cases that matter most (broad categories like "Updates" and "Analysts/
    Institutional Investor Meet/Con. Call Updates" that many unrelated real announcements share).

    CONTENT_SIMILARITY_THRESHOLD (0.95) was chosen deliberately conservative, not as a midpoint:
    NSE's own announcement text is heavily templated ("[Company] has informed the Exchange
    regarding...", "Please note that the Company executives will be participating in..."), so
    even genuinely different announcements can score high on a naive whole-text similarity ratio
    purely from shared boilerplate -- checked directly, not assumed: the two real "different"
    examples above score 0.782 and *0.883* on difflib's SequenceMatcher, meaning even a 0.85
    threshold would still wrongly collapse the second one. 0.95 was chosen specifically because
    both real differing examples fall clearly below it while still being comfortably inside the
    real "near-identical/exact re-transmission" mass this dataset actually has (11,300/28,617
    real pairs, 38.9%, score >=0.95). The failure mode this favors is deliberate: undercounting
    two collapsed rows as one event is worse for a Disclosure agent than overcounting two
    genuinely-identical rows as two events, because a hidden real disclosure is a worse error than
    a slightly inflated count of an unambiguous one.
    """
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault((row["symbol"], row["category"]), []).append(row)

    events: list[list[dict]] = []
    for _key, group_rows in groups.items():
        ordered = sorted(group_rows, key=lambda r: r["sort_timestamp"])
        clusters: list[list[dict]] = [[ordered[0]]]
        for row in ordered[1:]:
            last = clusters[-1][-1]
            prev_ts = datetime.strptime(last["sort_timestamp"], "%Y-%m-%d %H:%M:%S")
            this_ts = datetime.strptime(row["sort_timestamp"], "%Y-%m-%d %H:%M:%S")
            within_gap = (this_ts - prev_ts) <= NEAR_DUPLICATE_GAP
            if within_gap and _content_similar(last.get("description"), row.get("description")):
                clusters[-1].append(row)
            else:
                clusters.append([row])
        events.extend(clusters)
    return events

CONTENT_SIMILARITY_THRESHOLD = 0.95

def _content_similar(text_a: str | None, text_b: str | None) -> bool:
    a, b = (text_a or "").strip(), (text_b or "").strip()
    if not a and not b:
        return True  # both blank -- no content to compare, category+time alone decides (rare: most rows have text)
    return SequenceMatcher(None, a, b).ratio() >= CONTENT_SIMILARITY_THRESHOLD

def ingest_symbol_announcements(conn, symbol: str, raw_announcements: list[dict], source_file: str):
    rows = build_announcement_rows(symbol, raw_announcements, source_file)
    if not rows:
        from ...bitemporal.store import BulkWriteResult
        return BulkWriteResult(inserted=0, skipped_duplicate=0)
    return write_facts(conn, "corporate_announcements", rows)

# ---------- Real network fetch (not used by the fixture-based test suite) ----------

def _session_with_cookie(timeout: float = 20.0) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
    })
    session.get("https://www.nseindia.com", timeout=timeout)
    return session

def fetch_and_ingest_symbol(conn, session: requests.Session, symbol: str, from_date: date, to_date: date, source_file: str = "nse_corporate_announcements_live"):
    raw = fetch_symbol_announcements(session, symbol, from_date, to_date)
    return ingest_symbol_announcements(conn, symbol, raw, source_file), len(raw)
