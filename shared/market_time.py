"""NSE's calendar clock. NSE trades in India Standard Time (UTC+05:30, no daylight saving), so
"today" or "the date a command ran on" means the IST calendar date, whatever timezone this machine
happens to be set to. Stored timestamps (`recorded_at`, replay watermarks, snapshots) stay UTC and
are compared UTC-to-UTC; convert to IST only where a timestamp meets an NSE trading date.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def market_today() -> date:
    """Today's NSE calendar date (IST)."""
    return datetime.now(IST).date()


def market_date(moment: datetime) -> date:
    """The NSE calendar date (IST) of an aware timestamp. A naive timestamp is refused rather than
    guessed at: which clock it came from is exactly the ambiguity this module exists to remove."""
    if moment.utcoffset() is None:
        raise ValueError("market_date() requires a timezone-aware datetime")
    return moment.astimezone(IST).date()


def parse_logged_timestamp(text: str) -> datetime:
    """A timestamp from logs/weekly_ingest.log. Entries written before 2026-09-28 carry no offset
    and were written in this machine's local time, IST; newer entries carry their offset."""
    moment = datetime.fromisoformat(text)
    return moment if moment.utcoffset() is not None else moment.replace(tzinfo=IST)
