"""Ingestion health, OUTSIDE any decision -- item 5. `logs/weekly_ingest.log` is deliberately never
read by G1 or anything else that feeds a decision record (it's mutable, gitignored, and outside the
bitemporal store, so reading it there would make `desk replay` non-reproducible -- see
desk/gates/checks.py's module docstring). But a failing or stale ingestion is still real information
a personal desk user should see, so `desk status` surfaces it as a plain, non-gating health line.
Best-effort only: never raises, since nothing here is allowed to block or alter an assessment.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from shared.log_paths import logs_dir

LOG_PATH = logs_dir() / "weekly_ingest.log"   # a temporary folder under tests (shared/log_paths.py)

_SUMMARY_RE = re.compile(
    r"^=== (?P<start>\S+) weekly_ingest \(finished (?P<finish>\S+)\) overall=(?P<overall>\w+) "
    r"steps: (?P<steps>.*?) ===\s*$"
)
_GAPS_RE = re.compile(r"^\s*GAPs: (?P<n>\d+)")
_START_RE = re.compile(r"^=== (?P<start>\S+) weekly_ingest started ===\s*$")
_STEP_RE = re.compile(r"^=== (?P<start>\S+) weekly_ingest step=(?P<label>\S+) status=(?P<status>\w+) completed=\S+ ===\s*$")
_SKIP_RE = re.compile(r"^=== (?P<start>\S+) weekly_ingest skipped: (?P<detail>.*?) ===\s*$")

# PROPOSED when ingestion was weekly (weekly_ingest.py keeps that name); it has run every weekday since
# 2026-09-28 (docs/OPERATIONS.md, "Daily ingestion"). Strategy 0's registered definition cites this value.
STALE_AFTER_DAYS = 7


def _previous_display_session(today):
    """Display-only weekday proxy: no forward holiday calendar exists (P8-063).

    Never infer a holiday from missing ingestion, which would hide a stale store.
    Strategy 0 retains its separately registered STALE_AFTER_DAYS value.
    """
    day = today - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def latest_trading_date_line(conn) -> str:
    """The store's latest bhavcopy date -- the fact the health line alone cannot prove (a run can
    report OK without having ingested the date you expect)."""
    row = conn.execute("SELECT MAX(event_date) FROM bhavcopy").fetchone()
    return f"Latest trading date in store: {row[0] or 'NONE (no bhavcopy rows)'}"


def price_band_health_line(desk_conn, run_date: str | None) -> str:
    """NSE's price-band list dated the latest trading date: the bands for the next session
    (P8-082). Missing is a WARN: those bands stay UNKNOWN and a flat bar counts as possibly locked."""
    if run_date is None:
        return "Price bands: UNKNOWN (no trading dates in store)."
    row = desk_conn.execute("SELECT COUNT(*), MIN(published_at) FROM circuit_bands WHERE event_date=? "
                            "AND knowledge_date<=?", (run_date, run_date)).fetchone()
    if not row or not row[0]:
        return (f"Price bands: WARN, no NSE list dated {run_date} yet; the next session's bands are UNKNOWN, "
                "so a flat bar counts as possibly locked (a later run fetches the list).")
    from datetime import datetime
    from shared.market_time import IST
    published = datetime.fromisoformat(row[1]).astimezone(IST)
    return f"Price bands: OK, list dated {run_date} ({row[0]} rows, published {published:%H:%M} IST)."


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


_SKIP_REASONS = (("WARN on battery", "BATTERY_SKIP"), ("WARN uncommitted changes", "UNCOMMITTED_CODE"),
                 ("WARN HEAD is", "NOT_ON_MASTER"), ("WARN git status could not run", "GIT_UNAVAILABLE"),
                 ("WARN git could not read HEAD", "GIT_UNAVAILABLE"))
MARKET_CLOSE = (15, 30)


def skips_by_decision_date() -> dict:
    """Nightly runs skipped before any step (P8-053, P8-059), keyed by the date each would have
    decided: a skip at or after 15:30 IST belongs to that day; an earlier one (a morning recovery)
    to the previous weekday. Labels Strategy 0's burn-in gap records only (P8-056); nothing here
    feeds a decision. {date: {'reason': the latest skip's reason, 'skips': [their lines]}}."""
    from datetime import timedelta
    from shared.market_time import IST, parse_logged_timestamp
    out = {}
    if not LOG_PATH.exists():
        return out
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        m = _SKIP_RE.match(line)
        if not m:
            continue
        moment = parse_logged_timestamp(m.group("start")).astimezone(IST)
        day = moment.date()
        if (moment.hour, moment.minute) < MARKET_CLOSE:
            day -= timedelta(days=1)
            while day.weekday() >= 5:
                day -= timedelta(days=1)
        reason = next((code for prefix, code in _SKIP_REASONS if m.group("detail").startswith(prefix)), "NO_RUN")
        entry = out.setdefault(day.isoformat(), dict(reason=reason, skips=[]))
        entry["reason"] = reason
        entry["skips"].append(f"{m.group('start')}: {m.group('detail')}")
    return out


def ingestion_health_line(current_run_start: str | None = None) -> str:
    """`current_run_start` is the start stamp of the run asking for this line, i.e. the nightly
    brief, which is written before its own run finishes (P8-050): that run is reported as in
    progress, with the steps it has logged so far, never as unfinished. Every other unmatched start
    keeps P8-045's rule. A run skipped before any step (low battery, P8-053; the code guard, P8-059)
    is reported when it is later than the last finished run; it never counts as a run, so staleness
    is unaffected."""
    if not LOG_PATH.exists():
        return "Ingestion health: UNKNOWN (logs/weekly_ingest.log not found)."

    try:
        text = LOG_PATH.read_text(encoding="utf-8")
        last_summary = None
        last_gaps = None
        unfinished = {}
        steps = {}
        last_skip = None
        last_successful_start = None
        from shared.market_time import parse_logged_timestamp
        for line in text.splitlines():
            started = _START_RE.match(line)
            if started:
                unfinished[started.group("start")] = None
                continue
            skipped = _SKIP_RE.match(line)
            if skipped:
                last_skip = skipped.groupdict()
                continue
            step = _STEP_RE.match(line)
            if step:
                steps.setdefault(step.group("start"), []).append((step.group("label"), step.group("status")))
                continue
            m = _SUMMARY_RE.match(line)
            if m:
                last_summary = m.groupdict()
                unfinished.pop(last_summary["start"], None)
                # WARN is a completed, zero-exit run (e.g. a missing ISIN snapshot).
                # ERROR does not clear an earlier interruption's current warning.
                if last_summary["overall"] in ("OK", "WARN"):
                    completed_start = parse_logged_timestamp(last_summary["start"])
                    if last_successful_start is None or completed_start > last_successful_start:
                        last_successful_start = completed_start
                last_gaps = None
                continue
            gm = _GAPS_RE.match(line)
            if gm and last_summary is not None:
                last_gaps = int(gm.group("n"))

        in_progress = current_run_start if current_run_start in unfinished else None
        current_unfinished = [stamp for stamp in unfinished if stamp != in_progress and (
                              last_successful_start is None or parse_logged_timestamp(stamp) > last_successful_start)]
        unfinished_notice = (
            f"started {max(current_unfinished, key=parse_logged_timestamp)}, never finished "
            "(no matching finish recorded; may still be running)"
        ) if current_unfinished else ""
        progress_notice = ""
        if in_progress:
            logged = steps.get(in_progress, [])
            problems = [f"{label}={status}" for label, status in logged if status != "OK"]
            progress_notice = (f"this run (started {in_progress}) is in progress: {len(logged)} "
                               f"step{'' if len(logged) == 1 else 's'} logged so far, "
                               + (", ".join(problems) if problems else "all OK")
                               + "; later steps run after this line is written")

        skip_notice = (f"latest attempt {last_skip['start']} skipped: {last_skip['detail']}"
                       if last_skip and (last_summary is None or parse_logged_timestamp(last_skip["start"])
                                         > parse_logged_timestamp(last_summary["start"])) else "")

        if last_summary is None:
            notices = [n for n in (progress_notice, skip_notice, unfinished_notice) if n]
            if notices:
                return f"Ingestion health: {'; '.join(notices)}."
            return "Ingestion health: UNKNOWN (no run summary found in the log)."

        from shared.market_time import IST
        finished = parse_logged_timestamp(last_summary["finish"])
        now = datetime.now(timezone.utc)
        age_days = (now - finished).days
        stale = finished.astimezone(IST).date() < _previous_display_session(now.astimezone(IST).date())
        staleness = f"STALE ({age_days}d ago)" if stale else f"{age_days}d ago"
        summary = (f"{last_summary['start']} ({staleness}), overall={last_summary['overall']}, "
                   f"gaps={last_gaps if last_gaps is not None else '?'}")
        tail = [n for n in (skip_notice, unfinished_notice) if n]

        return (
            (f"Ingestion health: {progress_notice}. Previous finished run {summary}" if progress_notice
             else f"Ingestion health: last run {summary}")
            + (f"; {'; '.join(tail)}." if tail else "")
        )
    except Exception as exc:  # best-effort only -- never lets a log-parsing problem break `desk status`
        return f"Ingestion health: UNKNOWN (could not parse log: {exc})."
