"""P8-020: interrupted ingestion leaves durable progress and releases its sleep request."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from desk.ingestion_health import ingestion_health_line
from scripts import weekly_ingest


class IngestionProgressTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.log = Path(temporary.name) / "ingest.log"

    def run_steps(self, steps):
        with patch.object(weekly_ingest, "LOG_PATH", self.log), \
                patch.object(weekly_ingest, "STEPS", steps), \
                patch.object(weekly_ingest, "_prevent_sleep", contextlib.nullcontext), \
                contextlib.redirect_stdout(io.StringIO()):
            return weekly_ingest.main()

    def health(self):
        with patch("desk.ingestion_health.LOG_PATH", self.log):
            return ingestion_health_line()

    def test_start_and_step_are_visible_before_next_step_and_interrupt(self):
        def first():
            self.assertIn("weekly_ingest started", self.log.read_text())
            self.assertIn("never finished", self.health())

        def interrupted():
            self.assertIn("step=first status=OK", self.log.read_text())
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.run_steps([("first", first), ("second", interrupted)])
        self.assertIn("never finished", self.health())
        self.assertNotIn("(finished", self.log.read_text())

    def test_failed_step_is_logged_before_next_step_and_summary_matches(self):
        def failed():
            raise ValueError("test failure")

        def next_step():
            self.assertIn("step=failed status=ERROR", self.log.read_text())

        self.assertEqual(self.run_steps([("failed", failed), ("next", next_step)]), 1)
        self.assertIn("overall=ERROR", self.health())
        self.assertNotIn("never finished", self.health())

    def test_later_finish_does_not_hide_an_earlier_unmatched_start(self):
        self.log.write_text("=== 2026-09-28T18:00:00+05:30 weekly_ingest started ===\n")
        self.assertEqual(self.run_steps([]), 0)
        self.assertIn("started 2026-09-28T18:00:00+05:30, never finished", self.health())

    def test_completed_old_run_does_not_hide_new_start(self):
        self.assertEqual(self.run_steps([]), 0)
        with self.log.open("a") as stream:
            stream.write("=== 2026-10-01T18:00:00+05:30 weekly_ingest started ===\n")
        self.assertIn("started 2026-10-01T18:00:00+05:30, never finished", self.health())


class SleepPreventionTest(unittest.TestCase):
    def test_windows_restores_previous_state_on_success_and_interrupt(self):
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted):
                set_state = Mock(side_effect=[0x80000002, 0x80000001])
                api = SimpleNamespace(kernel32=SimpleNamespace(SetThreadExecutionState=set_state))
                with patch.object(weekly_ingest.sys, "platform", "win32"), \
                        patch.object(weekly_ingest.ctypes, "windll", api, create=True):
                    try:
                        with weekly_ingest._prevent_sleep():
                            if interrupted:
                                raise KeyboardInterrupt
                    except KeyboardInterrupt:
                        self.assertTrue(interrupted)
                self.assertEqual(set_state.call_args_list, [call(0x80000001), call(0x80000002)])

    def test_non_windows_does_not_access_windows_api(self):
        api = Mock()
        with patch.object(weekly_ingest.sys, "platform", "linux"), \
                patch.object(weekly_ingest.ctypes, "windll", api, create=True):
            with weekly_ingest._prevent_sleep():
                pass
        self.assertEqual(api.mock_calls, [])

    def test_failed_windows_request_is_reported(self):
        api = SimpleNamespace(kernel32=SimpleNamespace(SetThreadExecutionState=Mock(return_value=0)))
        with patch.object(weekly_ingest.sys, "platform", "win32"), \
                patch.object(weekly_ingest.ctypes, "windll", api, create=True):
            with self.assertRaisesRegex(RuntimeError, "Could not request Windows sleep prevention"):
                with weekly_ingest._prevent_sleep():
                    self.fail("Should not start work without acquiring the request")


if __name__ == "__main__":
    unittest.main()
