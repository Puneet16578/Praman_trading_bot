"""NSE EQ tick sizes, recorded daily from Angel One's public scrip master (P8-064; user decision
2026-10-14). Point-in-time from the first recording on; nothing before it is known.

The master is a public file (no login, no SDK; CLAUDE.md's read-only broker rule allows downloading
it). Its `tick_size` is in paise. It is regenerated each morning before the session (observed
Last-Modified 08:00 IST), so a copy whose Last-Modified falls on IST date S gives the ticks in
force on session S: `event_date` and `knowledge_date` are that date, `recorded_at` the download.
Only exact, unique NSE `-EQ` rows are kept (the wrapper's own matching rule); a symbol with more
than one such row is skipped as ambiguous. A session with no recording has an UNKNOWN tick.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from shared.market_time import IST

MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


def parse_master(content: bytes) -> dict[str, float]:
    """{symbol: tick in paise} for exact, unique NSE EQ rows with a positive finite tick."""
    rows = json.loads(content)
    if not isinstance(rows, list):
        raise ValueError("Scrip master is not a list")
    found: dict[str, set[float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name, token = str(row.get("symbol", "")), str(row.get("token", ""))
        if row.get("exch_seg") != "NSE" or not name.endswith("-EQ") or row.get("expiry") \
                or row.get("instrumenttype", "") not in ("", "EQ") or not token.isdigit():
            continue
        try:
            tick = float(row.get("tick_size"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(tick) and tick > 0:
            found.setdefault(name[:-3], set()).add(tick)
    return {symbol: next(iter(ticks)) for symbol, ticks in found.items() if len(ticks) == 1}


def ingest_master(desk_conn, content: bytes, last_modified: str, *, recorded_at: datetime | None = None,
                  source_url: str = MASTER_URL) -> int:
    """Append one master's ticks under the session its Last-Modified names. Idempotent per file."""
    generated = parsedate_to_datetime(last_modified)
    if generated.utcoffset() is None:
        raise ValueError("Scrip master Last-Modified carries no timezone")
    session = generated.astimezone(IST).date().isoformat()
    recorded = recorded_at or datetime.now(timezone.utc)
    if generated > recorded:
        raise ValueError("Scrip master Last-Modified is in the future")
    ticks = parse_master(content)
    if not ticks:
        raise ValueError("Scrip master holds no usable NSE EQ tick sizes")
    digest = hashlib.sha256(content).hexdigest()
    before = desk_conn.total_changes
    with desk_conn:
        desk_conn.executemany(
            "INSERT INTO tick_sizes (symbol,event_date,knowledge_date,recorded_at,tick_rupees,tick_paise,source_url,"
            "source_last_modified,source_sha256) VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(symbol,event_date,source_sha256) DO NOTHING",
            [(symbol, session, session, recorded.astimezone(timezone.utc).isoformat(), paise / 100, paise,
              source_url, last_modified, digest) for symbol, paise in sorted(ticks.items())])
    return desk_conn.total_changes - before


def tick_for_session(desk_conn, symbol: str, session: str, as_of: str) -> float | None:
    """The tick in rupees recorded for exactly `session`, visible by `as_of`; None if unknown, or
    if that session's recordings disagree."""
    rows = desk_conn.execute("SELECT DISTINCT tick_rupees FROM tick_sizes WHERE symbol=? AND event_date=? "
                             "AND knowledge_date<=?", (symbol, session, as_of)).fetchall()
    return rows[0][0] if len(rows) == 1 else None


def fetch_and_record(desk_conn, session=None, *, timeout: int = 120) -> str:
    """The nightly step: one GET of the public master, then `ingest_master`. Returns a summary."""
    import requests
    own = session is None
    session = session or requests.Session()
    try:
        response = session.get(MASTER_URL, timeout=timeout, verify=True, allow_redirects=False)
        if response.status_code != 200:
            raise ValueError(f"Scrip master unavailable (HTTP {response.status_code})")
        last_modified = response.headers.get("Last-Modified")
        if not last_modified:
            raise ValueError("Scrip master response has no Last-Modified header; not recorded")
        inserted = ingest_master(desk_conn, response.content, last_modified)
    finally:
        if own:
            session.close()
    generated = parsedate_to_datetime(last_modified).astimezone(IST)
    return f"[TICK_SIZES] master generated {generated.isoformat()}; {inserted} rows recorded for {generated.date()}"
