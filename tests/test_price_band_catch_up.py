"""P8-082: a price-band list missed by an early nightly is fetched later; the brief says so."""
import contextlib
import io
import json
import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import ingest_price_bands as bands
from requests import HTTPError
from desk.circuit_bands import ingest_report
from desk.ingestion_health import price_band_health_line
from desk.lib.schema import init_desk_db

FIXTURE = Path(__file__).parent / "fixtures/circuit_bands/nse_20260930_sample.csv"


def praman(days):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE bhavcopy (symbol TEXT, series TEXT, event_date TEXT)")
    conn.executemany("INSERT INTO bhavcopy VALUES ('SBIN','EQ',?)", [(d,) for d in days])
    return conn


def desk(stored=()):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_desk_db(conn)
    for day, published in stored:
        ingest_report(conn, FIXTURE.read_bytes(), report_date=day, published_at=datetime.fromisoformat(published),
                      recorded_at=datetime.fromisoformat("2026-10-14T20:00:00+05:30"))
    return conn


class KeepOpen:
    """The step closes its desk connection; the test keeps the in-memory store to inspect it."""
    def __init__(self, conn):
        self.conn, self.closed = conn, 0

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __enter__(self):
        return self.conn.__enter__()

    def __exit__(self, *exc):
        return self.conn.__exit__(*exc)

    def close(self):
        self.closed += 1


SESSIONS = ["2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12", "2026-10-13", "2026-10-14"]


class SessionsToFetchTest(unittest.TestCase):
    def test_a_list_missed_on_an_earlier_night_is_asked_for_again(self):
        self.assertEqual(bands.sessions_to_fetch(praman(SESSIONS), desk([("2026-10-12", "2026-10-12T18:23:09+05:30")])),
                         ["2026-10-13", "2026-10-14"])

    def test_nothing_stored_or_already_current_asks_only_for_the_latest(self):
        self.assertEqual(bands.sessions_to_fetch(praman(SESSIONS), desk()), ["2026-10-14"])
        self.assertEqual(bands.sessions_to_fetch(praman(SESSIONS), desk([("2026-10-14", "2026-10-14T18:30:00+05:30")])),
                         ["2026-10-14"])

    def test_the_catch_up_uses_store_sessions_only_and_is_bounded(self):
        many = [f"2026-09-{d:02d}" for d in (14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 28, 29)]
        days = bands.sessions_to_fetch(praman(many), desk([("2026-09-14", "2026-09-14T18:00:00+05:30")]))
        self.assertEqual(days, many[-bands.CATCH_UP_SESSIONS:])
        holiday = bands.sessions_to_fetch(praman(["2026-10-01", "2026-10-05"]),
                                          desk([("2026-10-01", "2026-10-01T19:39:09+05:30")]))
        self.assertEqual(holiday, ["2026-10-05"])          # 2 October has no session, so it is not requested


class RunTest(unittest.TestCase):
    def test_the_missed_list_is_ingested_and_tonights_404_stays_unknown(self):
        store = desk([("2026-10-12", "2026-10-12T18:23:09+05:30")])
        store_proxy = KeepOpen(store)

        def fetch(session, dated, cache):
            if dated == "2026-10-14":
                raise HTTPError(response=Mock(status_code=404))
            return FIXTURE.read_bytes(), datetime.fromisoformat(f"{dated}T18:41:00+05:30")
        output = io.StringIO()
        with patch.object(bands, "get_desk_connection", return_value=store_proxy), \
                patch.object(bands, "get_live_connection", return_value=praman(SESSIONS)), \
                patch.object(bands, "fetch_report", side_effect=fetch) as fetched, \
                patch.object(bands, "Session"), contextlib.redirect_stdout(output):
            report = bands.run()
        self.assertEqual([c.args[1] for c in fetched.call_args_list], ["2026-10-13", "2026-10-14"])
        self.assertEqual((report["reports"], report["missing"]), (1, ["2026-10-14"]))
        self.assertIn("WARN price-band report 2026-10-14 unavailable (404); remains UNKNOWN", output.getvalue())
        known = store.execute("SELECT DISTINCT knowledge_date FROM circuit_bands WHERE event_date='2026-10-13'").fetchall()
        self.assertEqual([r[0] for r in known], ["2026-10-13"])      # its own Last-Modified date, not today
        self.assertEqual(store_proxy.closed, 1)

    def test_a_rewritten_catch_up_list_stays_unknown_and_tonights_is_still_fetched(self):
        store = KeepOpen(desk([("2026-10-12", "2026-10-12T18:23:09+05:30")]))

        def fetch(session, dated, cache):
            if dated == "2026-10-13":
                raise ValueError("Archive served a mismatched publication date")
            return FIXTURE.read_bytes(), datetime.fromisoformat(f"{dated}T00:30:00+05:30")   # never in the future
        output = io.StringIO()
        with patch.object(bands, "get_desk_connection", return_value=store),                 patch.object(bands, "get_live_connection", return_value=praman(SESSIONS)),                 patch.object(bands, "fetch_report", side_effect=fetch),                 patch.object(bands, "Session"), contextlib.redirect_stdout(output):
            report = bands.run()
        self.assertEqual((report["reports"], report["missing"]), (1, ["2026-10-13"]))
        self.assertIn("WARN price-band report 2026-10-13 refused on catch-up", output.getvalue())
        with patch.object(bands, "get_desk_connection", return_value=KeepOpen(desk())),                 patch.object(bands, "get_live_connection", return_value=praman(SESSIONS)),                 patch.object(bands, "fetch_report", side_effect=ValueError("x")),                 patch.object(bands, "Session"), self.assertRaises(ValueError):
            bands.run()                                   # tonight's own list keeps failing loudly

    def test_an_explicit_range_keeps_the_weekday_loop(self):
        store = desk()
        with patch.object(bands, "get_desk_connection", return_value=store), \
                patch.object(bands, "get_live_connection") as live, \
                patch.object(bands, "fetch_report", side_effect=HTTPError(response=Mock(status_code=404))) as fetched, \
                patch.object(bands, "Session"), contextlib.redirect_stdout(io.StringIO()):
            report = bands.run("2026-10-09", "2026-10-12")
        live.assert_not_called()
        self.assertEqual([c.args[1] for c in fetched.call_args_list], ["2026-10-09", "2026-10-12"])
        self.assertEqual(report["missing"], ["2026-10-09", "2026-10-12"])


class HealthLineTest(unittest.TestCase):
    def test_missing_list_is_a_warn_and_a_present_one_says_when_it_was_published(self):
        store = desk([("2026-10-12", "2026-10-12T18:23:09+05:30")])
        self.assertEqual(price_band_health_line(store, "2026-10-13"),
                         "Price bands: WARN, no NSE list dated 2026-10-13 yet; the next session's bands are UNKNOWN, "
                         "so a flat bar counts as possibly locked (a later run fetches the list).")
        self.assertRegex(price_band_health_line(store, "2026-10-12"),
                         r"^Price bands: OK, list dated 2026-10-12 \(\d+ rows, published 18:23 IST\)\.$")
        self.assertEqual(price_band_health_line(store, None), "Price bands: UNKNOWN (no trading dates in store).")

    def test_the_brief_shows_the_line_under_data_health(self):
        from desk import brief
        store = desk()
        with patch("desk.ingestion_health.ingestion_health_line", return_value="Ingestion health: x"), \
                patch("desk.ingestion_health.isin_map_health_line", return_value="ISIN map: x"):
            lines = brief.health_lines(praman(SESSIONS), "2026-10-14", None, store)
        self.assertTrue(lines[-1].startswith("Price bands: WARN, no NSE list dated 2026-10-14"))


if __name__ == "__main__":
    unittest.main()
