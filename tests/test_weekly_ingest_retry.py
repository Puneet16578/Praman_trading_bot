"""The daily bhavcopy step must survive an unpublished snapshot and retry."""
import contextlib
import io
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from scripts import weekly_ingest


class BhavcopyTodayRetryTest(unittest.TestCase):
    def run_step(self, outcomes):
        today = date(2026, 9, 28)
        conn = Mock()
        output = io.StringIO()
        with (
            patch.object(weekly_ingest, "date") as clock,
            patch("src.config.settings.get_settings") as settings,
            patch("src.bitemporal.connection.get_connection", return_value=conn),
            patch("src.bitemporal.connection.init_db"),
            patch("src.ingestion.nse_market_data.bhavcopy.ingest_bhavcopy_date",
                  side_effect=outcomes) as ingest,
            patch("time.sleep") as sleep,
            contextlib.redirect_stdout(output),
        ):
            clock.today.return_value = today
            settings.return_value.database_path = ":memory:"
            weekly_ingest.step_bhavcopy_today()
        conn.close.assert_called_once_with()
        self.assertEqual(ingest.call_args_list, [call(conn, today)] * len(outcomes))
        self.assertEqual(sleep.call_args_list,
                         [call(weekly_ingest.BHAVCOPY_TODAY_RETRY_DELAY_SECONDS)]
                         * (len(outcomes) - 1))
        return output.getvalue()

    def test_retries_until_today_is_published(self):
        prior = SimpleNamespace(status="ingested", actual_event_date="2026-09-25")
        published = SimpleNamespace(status="ingested", actual_event_date="2026-09-28",
                                    rows_inserted=42)
        output = self.run_step([prior, prior, published])
        self.assertIn("ingested on attempt 3/6", output)
        self.assertNotIn("GAP", output)

    def test_exhausts_retry_budget_without_exception(self):
        unavailable = SimpleNamespace(status="gap", reason="not published")
        output = self.run_step([unavailable] * weekly_ingest.BHAVCOPY_TODAY_MAX_ATTEMPTS)
        self.assertIn("GAP 2026-09-28: still not published after 6 attempts", output)
