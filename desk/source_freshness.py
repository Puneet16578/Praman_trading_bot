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
"""
from datetime import date, datetime, timedelta, timezone
import json

ANNOUNCEMENTS = 'nse_corporate_announcements'
BACKFILL_COMPLETE_THROUGH = '2026-09-17'
STALENESS_LIMIT_DAYS = 0


def required_through(as_of_date: str) -> str:
    """The latest date the source must be complete through for a decision dated `as_of_date`."""
    return (date.fromisoformat(as_of_date) - timedelta(days=1 + STALENESS_LIMIT_DAYS)).isoformat()


def complete_through(desk_conn, symbol: str, source: str = ANNOUNCEMENTS) -> str:
    """Latest complete source date as visible on this connection; partial runs cannot advance it."""
    best = BACKFILL_COMPLETE_THROUGH
    if desk_conn is None:
        return best
    for row in desk_conn.execute("SELECT through_date, detail FROM source_freshness WHERE source=? AND status='COMPLETE' "
                                 'ORDER BY through_date DESC, row_id DESC', (source,)):
        detail = json.loads(row['detail'])
        if not detail.get('failed_symbols') and detail.get('summary', {}).get('scope') != 'PER_SYMBOL':
            return max(best, row['through_date'])
    return best


def record_refresh(desk_conn, *, through_date: str, status: str, failed_symbols, summary, source: str = ANNOUNCEMENTS):
    """Append one refresh's completeness statement. Never updates an earlier row."""
    if status not in ('COMPLETE', 'PARTIAL'):
        raise ValueError(f'Only a COMPLETE or PARTIAL refresh establishes freshness, not {status!r}.')
    desk_conn.execute('INSERT INTO source_freshness (source, through_date, status, detail, recorded_at) VALUES (?,?,?,?,?)',
                      (source, through_date, status,
                       json.dumps(dict(failed_symbols=sorted(failed_symbols), summary=summary), sort_keys=True, default=str),
                       datetime.now(timezone.utc).isoformat()))
    desk_conn.commit()


def market_coverage_from(desk_conn, through_date, source=ANNOUNCEMENTS):
    if desk_conn is None:
        return None
    starts = []
    for row in desk_conn.execute("SELECT detail FROM source_freshness WHERE source=? AND status='COMPLETE' AND through_date>=?",
                                 (source, through_date)):
        summary = json.loads(row['detail']).get('summary', {})
        if summary.get('scope') == 'MARKET' and summary.get('coverage_from'):
            starts.append(summary['coverage_from'])
    return min(starts) if starts else None
