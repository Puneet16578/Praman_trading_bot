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


def run(start: str | None = None, end: str | None = None) -> dict:
    if start is None:
        praman = get_live_connection()
        try:
            start = praman.execute("SELECT MAX(event_date) FROM bhavcopy").fetchone()[0]
        finally:
            praman.close()
        if start is None:
            raise ValueError("No trading date in Praman store")
    first, last = date.fromisoformat(start), date.fromisoformat(end or start)
    if first > last or last > market_today():
        raise ValueError("Invalid price-band date range")
    conn = get_desk_connection()
    report = {"reports": 0, "inserted": 0, "missing": []}
    try:
        with Session() as session:
            session.headers["User-Agent"] = "Mozilla/5.0"
            day = first
            while day <= last:
                if day.weekday() < 5:
                    dated = day.isoformat()
                    try:
                        content, published = fetch_report(session, dated, RAW_DIR)
                    except HTTPError as error:
                        if error.response is None or error.response.status_code != 404:
                            raise
                        report["missing"].append(dated)
                        print(f"WARN price-band report {dated} unavailable (404); remains UNKNOWN", flush=True)
                    else:
                        inserted = ingest_report(conn, content, report_date=dated, published_at=published)
                        report["inserted"] += inserted
                        report["reports"] += 1
                        print(f"[BANDS] snapshot={dated} next-session inserted={inserted}", flush=True)
                day += timedelta(days=1)
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
