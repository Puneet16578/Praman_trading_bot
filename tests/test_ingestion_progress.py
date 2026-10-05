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

    def test_later_success_clears_current_flag_but_preserves_history(self):
        self.log.write_text("=== 2026-09-28T18:00:00+05:30 weekly_ingest started ===\n")
        self.assertEqual(self.run_steps([]), 0)
        self.assertNotIn("never finished", self.health())
        self.assertIn("2026-09-28T18:00:00+05:30 weekly_ingest started", self.log.read_text())
        self.assertIn("overall=OK", self.health())
        self.assertIn("last run", self.health())

    def test_completed_old_run_does_not_hide_new_start(self):
        self.assertEqual(self.run_steps([]), 0)
        with self.log.open("a") as stream:
            stream.write("=== 2099-10-01T18:00:00+05:30 weekly_ingest started ===\n")
        self.assertIn("started 2099-10-01T18:00:00+05:30, never finished", self.health())

    def test_run_asking_for_its_own_health_is_in_progress_not_unfinished(self):
        """P8-050: the nightly brief is written before its own run finishes."""
        seen = {}

        def first():
            pass

        def brief():
            with patch("desk.ingestion_health.LOG_PATH", self.log):
                seen["own"] = ingestion_health_line(weekly_ingest._CURRENT_RUN_START)
                seen["outside"] = ingestion_health_line()

        self.log.write_text("=== 2026-10-04T18:00:00+05:30 weekly_ingest started ===\n"
                            "=== 2026-10-04T18:00:00+05:30 weekly_ingest (finished 2026-10-04T18:50:00+05:30) "
                            "overall=OK steps: sample=OK ===\n  GAPs: 0\n")
        self.assertEqual(self.run_steps([("first", first), ("brief", brief)]), 0)
        self.assertRegex(seen["own"], r"this run \(started \S+\) is in progress: 1 step logged so far, all OK")
        self.assertIn("Previous finished run 2026-10-04T18:00:00+05:30", seen["own"])
        self.assertIn("overall=OK, gaps=0", seen["own"])
        self.assertNotIn("never finished", seen["own"])
        self.assertIn("never finished", seen["outside"])     # an outside observer cannot know it is alive
        self.assertIsNone(weekly_ingest._CURRENT_RUN_START)  # cleared once the steps end
        self.assertNotIn("in progress", self.health())

    def test_in_progress_run_still_reports_an_earlier_interruption_and_problem_steps(self):
        text = ('=== 2026-10-01T18:00:00+05:30 weekly_ingest started ===\n'
                '=== 2026-10-02T18:00:00+05:30 weekly_ingest started ===\n'
                '=== 2026-10-02T18:00:00+05:30 weekly_ingest step=bhavcopy status=OK completed=2026-10-02T18:07:00+05:30 ===\n'
                '=== 2026-10-02T18:00:00+05:30 weekly_ingest step=isin_map status=WARN completed=2026-10-02T18:08:00+05:30 ===\n')
        self.log.write_text(text)
        with patch("desk.ingestion_health.LOG_PATH", self.log):
            line = ingestion_health_line("2026-10-02T18:00:00+05:30")
        self.assertIn("this run (started 2026-10-02T18:00:00+05:30) is in progress: 2 steps logged so far, "
                      "isin_map=WARN", line)
        self.assertIn("started 2026-10-01T18:00:00+05:30, never finished", line)
        self.assertEqual(self.log.read_text(), text)

    def test_warn_completion_supersedes_but_error_does_not(self):
        for status in ('WARN', 'ERROR'):
            with self.subTest(status=status):
                text = ('=== 2026-10-01T18:00:00+05:30 weekly_ingest started ===\n'
                        '=== 2026-10-03T18:00:00+05:30 weekly_ingest started ===\n'
                        f'=== 2026-10-03T18:00:00+05:30 weekly_ingest (finished 2026-10-03T19:00:00+05:30) overall={status} steps: sample={status} ===\n')
                self.log.write_text(text)
                self.assertEqual('never finished' in self.health(), status == 'ERROR')
                self.assertEqual(self.log.read_text(), text)


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
