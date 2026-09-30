"""P8-018: one NSE (IST) calendar clock -- log timestamps, the ingestion-health age, and the G7
override month."""
import sqlite3
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.gates.engine import _g7_overrides_this_month
from desk.ingestion_health import ingestion_health_line
from desk.lib.schema import init_desk_db
from shared.market_time import IST, market_date, parse_logged_timestamp


class MarketDateTest(unittest.TestCase):
    def test_desk_and_scripts_use_the_market_calendar_clock(self):
        root = Path(__file__).resolve().parents[1]
        forbidden = re.compile(r"\b(?:date|datetime)\s*\.\s*today\s*\(")
        violations = []
        for folder in ("desk", "scripts"):
            for path in sorted((root / folder).rglob("*.py")):
                for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                    if forbidden.search(line):
                        violations.append(f"{path.relative_to(root)}:{number}: {line.strip()}")
        self.assertEqual(violations, [], "Use shared.market_time.market_today():\n" + "\n".join(violations))

    def test_utc_evening_is_next_ist_date(self):
        self.assertEqual(market_date(datetime(2026, 9, 30, 19, 0, tzinfo=timezone.utc)).isoformat(), "2026-10-01")

    def test_naive_datetime_is_refused(self):
        with self.assertRaises(ValueError):
            market_date(datetime(2026, 9, 30, 19, 0))

    def test_legacy_naive_log_timestamp_is_read_as_ist(self):
        self.assertEqual(parse_logged_timestamp("2026-09-28T13:53:03").utcoffset(), timedelta(hours=5, minutes=30))
        self.assertEqual(parse_logged_timestamp("2026-09-28T13:53:03+00:00").utcoffset(), timedelta(0))


class SameDayIngestionHealthTest(unittest.TestCase):
    """The run that printed "(-1d ago)": a naive IST start time was labelled UTC, putting a run
    from minutes earlier 5.5 hours in the future."""

    now = datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc)

    def _line_for(self, start: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "weekly_ingest.log"
            log.write_text(f"=== {start} weekly_ingest (finished {start}) overall=OK steps: bhavcopy=OK ===\n"
                           "  GAPs: 0\n", encoding="utf-8")
            with patch("desk.ingestion_health.LOG_PATH", log), \
                    patch("desk.ingestion_health.datetime", wraps=datetime) as clock:
                clock.now.return_value = self.now
                return ingestion_health_line()

    def test_same_day_run_with_offset_is_zero_days_old(self):
        start = (self.now.astimezone(IST) - timedelta(minutes=1)).isoformat(timespec="seconds")
        self.assertIn("(0d ago)", self._line_for(start))

    def test_same_day_legacy_naive_run_is_zero_days_old(self):
        start = (self.now.astimezone(IST) - timedelta(minutes=1)).replace(tzinfo=None).isoformat(timespec="seconds")
        line = self._line_for(start)
        self.assertIn("(0d ago)", line)
        self.assertNotIn("-1d", line)


class LatestTradingDateLineTest(unittest.TestCase):
    def test_reports_max_event_date_and_empty_store(self):
        from desk.ingestion_health import latest_trading_date_line
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.execute("CREATE TABLE bhavcopy (symbol TEXT, event_date TEXT)")
        self.assertIn("NONE", latest_trading_date_line(conn))
        conn.executemany("INSERT INTO bhavcopy VALUES ('X', ?)", [("2026-09-24",), ("2026-09-25",)])
        self.assertEqual(latest_trading_date_line(conn), "Latest trading date in store: 2026-09-25")


class G7OverrideMonthTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        init_desk_db(self.conn)
        # 2026-09-30T19:00Z is 2026-10-01 00:30 IST.
        self.conn.execute(
            "INSERT INTO journal_events (event_type, trade_id, decision_id, detail, reason, recorded_at) "
            "VALUES ('G7_OVERRIDE', NULL, NULL, '{}', 'test', '2026-09-30T19:00:00+00:00')"
        )

    def test_override_at_0030_ist_on_the_1st_counts_toward_the_new_month(self):
        self.assertEqual(_g7_overrides_this_month(self.conn, "2026-10-05"), 1)
        self.assertEqual(_g7_overrides_this_month(self.conn, "2026-09-29"), 0)


if __name__ == "__main__":
    unittest.main()
