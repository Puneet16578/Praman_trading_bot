"""NSE complete price-band snapshots, known after close for the next session.

event_date is the dated report, not the session during which its bands apply.
Missing exact reports stay UNKNOWN; a historic assessment never reads today's list.
"""
from __future__ import annotations
import csv
import hashlib
import io
import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from shared.market_time import IST

BASE_URL = "https://nsearchives.nseindia.com/content/equities/"
HEADER = ["Symbol", "Series", "Security Name", "Band", "Remarks"]


@dataclass(frozen=True)
class CircuitBand:
    kind: str = "UNKNOWN"
    percent: float | None = None
    report_date: str | None = None
    source_sha256: str | None = None
    series: str | None = None

    def label(self) -> str:
        if self.kind == "FIXED":
            return f"{self.percent:g}% fixed; next-session snapshot {self.report_date}"
        if self.kind == "DYNAMIC":
            return f"DYNAMIC operating range (No Band); next-session snapshot {self.report_date}"
        return "UNKNOWN (no exact dated snapshot visible as of the assessment)"


def report_url(report_date: str) -> str:
    return BASE_URL + "sec_list_" + date.fromisoformat(report_date).strftime("%d%m%Y") + ".csv"


def parse_report(content: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    if reader.fieldnames != HEADER:
        raise ValueError("Unexpected price-band CSV header (HTML and other reports are refused)")
    rows, seen = [], set()
    for raw in reader:
        if None in raw or any(value is None for value in raw.values()):
            raise ValueError("Malformed price-band row")
        row = {key: value.strip() for key, value in raw.items()}
        identity = (row["Symbol"], row["Series"])
        if not all(identity) or identity in seen:
            raise ValueError("Missing or duplicate symbol/series in price-band report")
        seen.add(identity)
        kind = "DYNAMIC" if row["Band"] == "No Band" else "FIXED"
        percent = None if kind == "DYNAMIC" else float(row["Band"])
        if percent is not None and (not math.isfinite(percent) or not 0 < percent <= 100):
            raise ValueError("Invalid fixed circuit band")
        rows.append({"symbol": identity[0], "series": identity[1], "security_name": row["Security Name"],
                     "band_kind": kind, "band_pct": percent, "remarks": row["Remarks"]})
    if not rows:
        raise ValueError("Empty price-band report")
    return rows


def ingest_report(conn, content: bytes, *, report_date: str, published_at: datetime,
                  recorded_at: datetime | None = None) -> int:
    day = date.fromisoformat(report_date)
    if published_at.utcoffset() is None:
        raise ValueError("Price-band publication timestamp must carry a timezone")
    # The downloader validates original dated files. A separately reviewed correction
    # may be published later: preserve its true knowledge date, never backdate it.
    if published_at.astimezone(IST).date() < day:
        raise ValueError("Price-band publication precedes the dated snapshot")
    rows = parse_report(content)
    digest = hashlib.sha256(content).hexdigest()
    recorded = recorded_at or datetime.now(timezone.utc)
    if recorded.utcoffset() is None or published_at > recorded:
        raise ValueError("Price-band publication cannot be in the future")
    before = conn.total_changes
    with conn:
        conn.executemany(
            "INSERT INTO circuit_bands (symbol,series,security_name,event_date,knowledge_date,recorded_at,"
            "band_kind,band_pct,remarks,source_url,source_sha256,published_at) "
            "VALUES (:symbol,:series,:security_name,:event_date,:knowledge_date,:recorded_at,"
            ":band_kind,:band_pct,:remarks,:source_url,:source_sha256,:published_at) "
            "ON CONFLICT(symbol,series,event_date,knowledge_date,source_sha256) DO NOTHING",
            [{**row, "event_date": report_date, "knowledge_date": published_at.astimezone(IST).date().isoformat(),
              "recorded_at": recorded.astimezone(timezone.utc).isoformat(), "source_url": report_url(report_date),
              "source_sha256": digest, "published_at": published_at.isoformat()} for row in rows],
        )
    return conn.total_changes - before


def band_as_of(conn, symbol: str, as_of_date: str, *, report_date: str | None = None) -> CircuitBand:
    report_date = report_date or as_of_date
    date.fromisoformat(as_of_date)
    date.fromisoformat(report_date)
    rows = conn.execute(
        "SELECT * FROM circuit_bands WHERE symbol=? AND event_date=? AND knowledge_date<=? "
        "ORDER BY knowledge_date DESC, published_at DESC, row_id DESC",
        (symbol, report_date, as_of_date),
    ).fetchall()
    by_series = {}
    for row in rows:
        by_series.setdefault(row["series"], row)
    chosen = by_series.get("EQ")
    if chosen is None and len(by_series) == 1:
        chosen = next(iter(by_series.values()))
    if chosen is None:
        return CircuitBand()
    return CircuitBand(chosen["band_kind"], chosen["band_pct"], chosen["event_date"],
                       chosen["source_sha256"], chosen["series"])


def fetch_report(session, report_date: str, cache_dir: Path) -> tuple[bytes, datetime]:
    url = report_url(report_date)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    content = response.content
    parse_report(content)
    published = parsedate_to_datetime(response.headers["Last-Modified"])
    if published.astimezone(IST).date().isoformat() != report_date:
        raise ValueError("Archive served a mismatched publication date")
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    target = cache_dir / f"{report_date}_{digest}.csv"
    if not target.exists():
        target.write_bytes(content)
    return content, published
