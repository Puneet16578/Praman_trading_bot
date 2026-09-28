"""Ingestion health, OUTSIDE any decision -- item 5. `logs/weekly_ingest.log` is deliberately never
read by G1 or anything else that feeds a decision record (it's mutable, gitignored, and outside the
bitemporal store, so reading it there would make `desk replay` non-reproducible -- see
desk/gates/checks.py's module docstring). But a failing or stale ingestion is still real information
a personal desk user should see, so `desk status` surfaces it as a plain, non-gating health line.
Best-effort only: never raises, since nothing here is allowed to block or alter an assessment.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "weekly_ingest.log"

_SUMMARY_RE = re.compile(
    r"^=== (?P<start>\S+) weekly_ingest \(finished (?P<finish>\S+)\) overall=(?P<overall>\w+) "
    r"steps: (?P<steps>.*?) ===\s*$"
)
_GAPS_RE = re.compile(r"^\s*GAPs: (?P<n>\d+)")

STALE_AFTER_DAYS = 7  # PROPOSED, matching the roughly-weekly cadence weekly_ingest.py's own name implies


def latest_trading_date_line(conn) -> str:
    """The store's latest bhavcopy date -- the fact the health line alone cannot prove (a run can
    report OK without having ingested the date you expect)."""
    row = conn.execute("SELECT MAX(event_date) FROM bhavcopy").fetchone()
    return f"Latest trading date in store: {row[0] or 'NONE (no bhavcopy rows)'}"


def isin_map_health_line(conn, as_of_date: str | None) -> str:
    from shared.isin_map_metadata import MAX_AGE_TRADING_DAYS, read_metadata, trading_days_since_build
    try:
        metadata = read_metadata()
        if as_of_date is None:
            return "ISIN map: UNKNOWN (no trading dates in store)."
        age = trading_days_since_build(conn, metadata["built_at"], as_of_date)
        status = "ERROR" if age > MAX_AGE_TRADING_DAYS else "OK"
        provenance = " (inferred from file timestamp)" if metadata["build_time_source"] == "file_mtime" else ""
        return (f"ISIN map: {status}, built {metadata['built_at']}{provenance}, "
                f"age={age} trading days (limit {MAX_AGE_TRADING_DAYS}).")
    except (OSError, ValueError, KeyError, TypeError):
        return "ISIN map: ERROR (build metadata unavailable or checksum invalid)."


def ingestion_health_line() -> str:
    if not LOG_PATH.exists():
        return "Ingestion health: UNKNOWN (logs/weekly_ingest.log not found)."

    try:
        text = LOG_PATH.read_text(encoding="utf-8")
        last_summary = None
        last_gaps = None
        for line in text.splitlines():
            m = _SUMMARY_RE.match(line)
            if m:
                last_summary = m.groupdict()
                last_gaps = None
                continue
            gm = _GAPS_RE.match(line)
            if gm and last_summary is not None:
                last_gaps = int(gm.group("n"))

        if last_summary is None:
            return "Ingestion health: UNKNOWN (no run summary found in the log)."

        from shared.market_time import parse_logged_timestamp
        start = parse_logged_timestamp(last_summary["start"])
        age_days = (datetime.now(timezone.utc) - start).days
        staleness = f"STALE ({age_days}d ago)" if age_days > STALE_AFTER_DAYS else f"{age_days}d ago"

        return (
            f"Ingestion health: last run {last_summary['start']} ({staleness}), "
            f"overall={last_summary['overall']}, gaps={last_gaps if last_gaps is not None else '?'}"
        )
    except Exception as exc:  # best-effort only -- never lets a log-parsing problem break `desk status`
        return f"Ingestion health: UNKNOWN (could not parse log: {exc})."
