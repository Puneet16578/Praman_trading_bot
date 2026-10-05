"""Announcement-source freshness watermark (P8-021 addition; user decision 2026-10-04).

Missing data must never read as "no disclosure". The disclosure dimension checks the announcements
in the 10 sessions strictly BEFORE the decision date, so it can be a FACT only if the announcement
source is known to be complete through at least the day before the decision.

Stated limit: STALENESS_LIMIT_DAYS = 0 -- the source must be complete through the calendar day
before the decision date; any further lag makes the disclosure dimension UNKNOWN, so G2 fails and
the assessment is INSUFFICIENT (a screen is SCREEN_FAIL), never ELIGIBLE.

Where completeness comes from:
- BACKFILL_COMPLETE_THROUGH: the full-history backfill fetched every covered symbol's history on
  2026-09-18/19 (P8-021's measurement), so the source is complete through 2026-09-17 for any symbol
  that has stored announcements. Historical assessments and replays before that are unaffected.
- The bulk refresh writes a MARKET receipt only after every contiguous window succeeds.
  PARTIAL receipts never advance any symbol's watermark; legacy per-symbol fallback receipts
  cannot establish market-wide coverage. Historical COMPLETE receipts remain replay-visible.
  Rows are read through the caller's Desk connection, so a replay connection limited to the
  decision's Desk watermark sees exactly the freshness the decision saw.
- A receipt never certifies past the last calendar day fully elapsed in IST when it was recorded
  (P8-049): a refresh that runs during day D cannot know D's later filings (25-38% of a trading
  day's announcements are published after the 18:07 nightly refresh), so a receipt recorded on D
  stating D certifies only D-1. The cap is applied on read: stored receipts are never edited, and
  replay applies the same rule to the same visible rows.
"""
from datetime import date, datetime, timedelta, timezone
import json

from shared.market_time import market_date

ANNOUNCEMENTS = 'nse_corporate_announcements'
BACKFILL_COMPLETE_THROUGH = '2026-09-17'
STALENESS_LIMIT_DAYS = 0


def required_through(as_of_date: str) -> str:
    """The latest date the source must be complete through for a decision dated `as_of_date`."""
    return (date.fromisoformat(as_of_date) - timedelta(days=1 + STALENESS_LIMIT_DAYS)).isoformat()


def certified_through(through_date: str, recorded_at: str) -> str | None:
    """What one receipt can certify (P8-049): its stated date, but never past the IST calendar day
    before the one it was recorded on. None (certifies nothing) if `recorded_at` is not an aware
    timestamp: which day it was recorded on is then unknown."""
    try:
        recorded = market_date(datetime.fromisoformat(recorded_at))
    except (TypeError, ValueError):
        return None
    return min(through_date, (recorded - timedelta(days=1)).isoformat())


def _complete_receipts(desk_conn, source):
    """(certified date, detail) of every COMPLETE receipt visible on this connection."""
    for row in desk_conn.execute("SELECT through_date, detail, recorded_at FROM source_freshness "
                                 "WHERE source=? AND status='COMPLETE' ORDER BY row_id", (source,)):
        certified = certified_through(row['through_date'], row['recorded_at'])
        if certified is not None:
            yield certified, json.loads(row['detail'])


def complete_through(desk_conn, symbol: str, source: str = ANNOUNCEMENTS) -> str:
    """Latest complete source date as visible on this connection; partial runs cannot advance it."""
    best = BACKFILL_COMPLETE_THROUGH
    if desk_conn is None:
        return best
    for certified, detail in _complete_receipts(desk_conn, source):
        if not detail.get('failed_symbols') and detail.get('summary', {}).get('scope') != 'PER_SYMBOL':
            best = max(best, certified)
    return best


def record_refresh(desk_conn, *, through_date: str, status: str, failed_symbols, summary, source: str = ANNOUNCEMENTS,
                   now: datetime | None = None):
    """Append one refresh's completeness statement. Never updates an earlier row. `now` (aware) is
    for tests only; production receipts are stamped with the real time."""
    if status not in ('COMPLETE', 'PARTIAL'):
        raise ValueError(f'Only a COMPLETE or PARTIAL refresh establishes freshness, not {status!r}.')
    recorded_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    desk_conn.execute('INSERT INTO source_freshness (source, through_date, status, detail, recorded_at) VALUES (?,?,?,?,?)',
                      (source, through_date, status,
                       json.dumps(dict(failed_symbols=sorted(failed_symbols), summary=summary), sort_keys=True, default=str),
                       recorded_at))
    desk_conn.commit()


def market_coverage_from(desk_conn, through_date, source=ANNOUNCEMENTS):
    """Earliest market-wide coverage start among COMPLETE receipts that certify `through_date`."""
    if desk_conn is None:
        return None
    starts = []
    for certified, detail in _complete_receipts(desk_conn, source):
        summary = detail.get('summary', {})
        if certified >= through_date and summary.get('scope') == 'MARKET' and summary.get('coverage_from'):
            starts.append(summary['coverage_from'])
    return min(starts) if starts else None
