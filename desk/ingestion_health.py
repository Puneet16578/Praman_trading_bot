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

        start = datetime.fromisoformat(last_summary["start"]).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - start).days
        staleness = f"STALE ({age_days}d ago)" if age_days > STALE_AFTER_DAYS else f"{age_days}d ago"

        return (
            f"Ingestion health: last run {last_summary['start']} ({staleness}), "
            f"overall={last_summary['overall']}, gaps={last_gaps if last_gaps is not None else '?'}"
        )
    except Exception as exc:  # best-effort only -- never lets a log-parsing problem break `desk status`
        return f"Ingestion health: UNKNOWN (could not parse log: {exc})."
