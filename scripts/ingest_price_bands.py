"""Fetch exact dated NSE price-band snapshots into the append-only Desk store."""
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from requests import HTTPError, Session
from desk.circuit_bands import fetch_report, ingest_report
from desk.lib.connection import get_desk_connection
from desk.lib.store import get_live_connection
from shared.market_time import market_today

RAW_DIR = Path(__file__).resolve().parents[1] / "data/raw/circuit_bands"
# NSE posts the dated list after the close at no published time: Last-Modified has been 17:10 to
# 19:39 IST (docs/desk/price_band_source.md), so an 18:00 nightly can ask too early (P8-082). A
# list missed one night is fetched on a later night, for at most this many sessions back.
CATCH_UP_SESSIONS = 5


def sessions_to_fetch(praman, desk) -> list[str]:
    """The store's latest trading date, plus the store's sessions after the latest stored band
    list (a list that 404'd on an earlier night), at most CATCH_UP_SESSIONS in all. A list fetched
    on a later night is known only from that night (ingest_report, P8-083), so a decision dated
    earlier never sees it; recorded_at keeps the exact fetch time."""
    latest = praman.execute("SELECT MAX(event_date) FROM bhavcopy").fetchone()[0]
    if latest is None:
        raise ValueError("No trading date in Praman store")
    stored = desk.execute("SELECT MAX(event_date) FROM circuit_bands").fetchone()[0]
    if stored is None or stored >= latest:
        return [latest]
    days = [row[0] for row in praman.execute(
        "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? AND event_date <= ? ORDER BY event_date",
        (stored, latest))]
    return days[-CATCH_UP_SESSIONS:] or [latest]


def run(start: str | None = None, end: str | None = None) -> dict:
    conn = get_desk_connection()
    try:
        if start is None:
            praman = get_live_connection()
            try:
                days = sessions_to_fetch(praman, conn)
            finally:
                praman.close()
        else:
            first, last = date.fromisoformat(start), date.fromisoformat(end or start)
            if first > last or last > market_today():
                raise ValueError("Invalid price-band date range")
            days = [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)
                    if (first + timedelta(days=i)).weekday() < 5]
        report = {"reports": 0, "inserted": 0, "missing": []}
        with Session() as session:
            session.headers["User-Agent"] = "Mozilla/5.0"
            for dated in days:
                try:
                    content, published = fetch_report(session, dated, RAW_DIR)
                except HTTPError as error:
                    if error.response is None or error.response.status_code != 404:
                        raise
                    report["missing"].append(dated)
                    print(f"WARN price-band report {dated} unavailable (404); remains UNKNOWN", flush=True)
                except ValueError:
                    # A catch-up list NSE rewrote later (its Last-Modified no longer its own date) or
                    # one that no longer parses stays UNKNOWN; it must not stop tonight's list.
                    if start is not None or dated == days[-1]:
                        raise
                    report["missing"].append(dated)
                    print(f"WARN price-band report {dated} refused on catch-up (date or format); remains UNKNOWN",
                          flush=True)
                else:
                    inserted = ingest_report(conn, content, report_date=dated, published_at=published)
                    report["inserted"] += inserted
                    report["reports"] += 1
                    print(f"[BANDS] snapshot={dated} next-session inserted={inserted}", flush=True)
    finally:
        conn.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    print(run(args.start, args.end))


if __name__ == "__main__":
    main()
