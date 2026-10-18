"""Retrying a skipped evening at 20:00 and 22:00 IST (user decision 2026-10-18, option A)."""
import contextlib
import io
import re
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import weekly_ingest  # noqa: E402
from desk.brief import SKIP_NOTICE_MARK, record_skipped_run  # noqa: E402
from shared.market_time import IST  # noqa: E402

NOW = datetime(2026, 10, 19, 20, 0, 3, tzinfo=IST)            # Monday's 20:00 retry


def started(stamp):
    return f"=== {stamp} weekly_ingest started ===\n"


def finished(stamp, overall):
    return f"=== {stamp} weekly_ingest (finished {stamp[:11]}19:40:00+05:30) overall={overall} steps: x={overall} ===\n"


def skipped(stamp, percent=13):
    return (f"=== {stamp} weekly_ingest skipped: WARN on battery at {percent}% (below 30%); no step ran; "
            f"the next run catches up ===\n")


class EveningRunStartedTest(unittest.TestCase):
    def test_a_started_evening_run_counts_as_done_however_it_ended(self):
        s = "2026-10-19T18:00:02.120000+05:30"
        for log in (started(s) + finished(s, "OK"), started(s) + finished(s, "WARN"),
                    started(s) + finished(s, "ERROR"), started(s)):            # the last: still running
            with self.subTest(log=log.splitlines()[-1][:80]):
                self.assertEqual(weekly_ingest.evening_run_started(log, NOW), s)

    def test_a_skipped_evening_a_morning_recovery_or_yesterday_do_not_count(self):
        cases = {
            "skipped at 18:00": skipped("2026-10-19T18:00:01.000000+05:30"),
            "morning recovery today": started("2026-10-19T07:12:00.000000+05:30") +
                                      finished("2026-10-19T07:12:00.000000+05:30", "OK"),
            "yesterday's evening": started("2026-10-16T22:00:00.000000+05:30"),
            "nothing": "",
        }
        for name, log in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(weekly_ingest.evening_run_started(log, NOW))

    def test_a_late_start_after_sleep_counts_for_that_evening(self):
        log = started("2026-10-19T19:31:09.815882+05:30")
        self.assertEqual(weekly_ingest.evening_run_started(log, NOW), "2026-10-19T19:31:09.815882+05:30")


class MainRetryTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.log = Path(temporary.name) / "ingest.log"
        self.today = datetime.now(IST).date().isoformat()

    def run_main(self, argv=(), power=(True, 13)):
        ran = []
        with patch.object(weekly_ingest, "LOG_PATH", self.log), \
                patch.object(weekly_ingest, "STEPS", [("first", lambda: ran.append("first"))]), \
                patch.object(weekly_ingest, "_prevent_sleep", contextlib.nullcontext), \
                patch.object(weekly_ingest, "power_status", return_value=power) as power_check, \
                patch.object(weekly_ingest, "head_branch", return_value="master"), \
                patch.object(weekly_ingest, "uncommitted_nightly_inputs", return_value=[]), \
                patch("desk.brief.record_skipped_run") as brief, contextlib.redirect_stdout(io.StringIO()):
            code = weekly_ingest.main(list(argv))
        return code, ran, power_check, brief

    def test_a_retry_after_this_evenings_run_does_nothing_but_say_so(self):
        first = f"{self.today}T18:00:02.000000+05:30"
        self.log.write_text(started(first) + finished(first, "ERROR"), encoding="utf-8")
        code, ran, power_check, brief = self.run_main(power=(False, None))
        self.assertEqual((code, ran), (0, []))
        power_check.assert_not_called()                      # not even the battery check
        brief.assert_not_called()
        last = self.log.read_text(encoding="utf-8").splitlines()[-1]
        self.assertRegex(last, r"^=== \S+ weekly_ingest retry not needed: this evening's run started at "
                         + re.escape(first) + r" ===$")

    def test_a_retry_after_a_skipped_evening_tries_again_under_the_30_percent_rule(self):
        self.log.write_text(skipped(f"{self.today}T18:00:01.000000+05:30"), encoding="utf-8")
        code, ran, power_check, brief = self.run_main(power=(True, 16))
        self.assertEqual((code, ran), (0, []))               # still below 30%: skipped again
        power_check.assert_called_once()
        self.assertIn("retry", brief.call_args.kwargs)
        self.assertEqual(self.log.read_text(encoding="utf-8").count("weekly_ingest skipped"), 2)
        code, ran, _, _ = self.run_main(power=(False, None))  # plugged in by 22:00: it runs
        self.assertEqual((code, ran), (0, ["first"]))

    def test_run_again_overrides_for_a_manual_rerun(self):
        first = f"{self.today}T18:00:02.000000+05:30"
        self.log.write_text(started(first) + finished(first, "OK"), encoding="utf-8")
        code, ran, power_check, _ = self.run_main(argv=["--run-again"], power=(False, None))
        self.assertEqual((code, ran), (0, ["first"]))
        power_check.assert_called_once()

    def test_the_retry_line_is_not_read_as_a_start_or_a_skip(self):
        from desk import ingestion_health
        line = "=== 2026-10-19T20:00:03.000000+05:30 weekly_ingest retry not needed: this evening's run started at x ==="
        self.assertIsNone(ingestion_health._START_RE.match(line))
        self.assertIsNone(ingestion_health._SKIP_RE.match(line))


class OneSkipNoticePerEveningTest(unittest.TestCase):
    def test_retries_add_one_line_under_the_evenings_notice(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            notice = "WARN 2026-10-19T18:00:01+05:30: nightly run skipped, on battery at 13% (below 30%). No step ran."
            record_skipped_run("2026-10-19", notice, out_dir=out, retry="Retried 18:00 IST: still skipped, x.")
            record_skipped_run("2026-10-19", notice.replace("13%", "16%"), out_dir=out,
                               retry="Retried 20:00 IST: still skipped, on battery at 16% (below 30%).")
            record_skipped_run("2026-10-19", notice.replace("13%", "19%"), out_dir=out,
                               retry="Retried 22:00 IST: still skipped, on battery at 19% (below 30%).")
            text = (out / "brief_2026-10-19.txt").read_text(encoding="utf-8")
        self.assertEqual(text.count(SKIP_NOTICE_MARK), 1)
        self.assertIn("13%", text)
        self.assertEqual(text.splitlines()[-2:], ["  Retried 20:00 IST: still skipped, on battery at 16% (below 30%).",
                                                  "  Retried 22:00 IST: still skipped, on battery at 19% (below 30%)."])

    def test_a_real_brief_still_gets_the_whole_notice(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / "brief_2026-10-19.txt").write_text("PRAMAN - DAILY DECISION DESK  2026-10-19\n\nsomething\n",
                                                     encoding="utf-8")
            record_skipped_run("2026-10-19", "WARN x: nightly run skipped, code guard.", out_dir=out, retry="Retried ...")
            text = (out / "brief_2026-10-19.txt").read_text(encoding="utf-8")
        self.assertIn("WARN x: nightly run skipped, code guard.", text)
        self.assertNotIn("Retried", text)


if __name__ == "__main__":
    unittest.main()
