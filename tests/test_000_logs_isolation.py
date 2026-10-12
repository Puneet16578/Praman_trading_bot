"""Imported first by discovery (sorted names), so the logs isolation in tests/__init__.py is in place
before any other test module imports a writer (P8-055 follow-up)."""
from pathlib import Path
import sys
import tempfile
import unittest

import tests  # noqa: F401 -- runs tests/__init__.py: PRAMAN_LOGS_DIR -> a temporary directory
from tests import logs_changes, logs_snapshot
from shared.log_paths import REAL_LOGS_DIR, logs_dir

ROOT = Path(__file__).resolve().parents[1]


class LogsIsolationTest(unittest.TestCase):
    def test_logs_folder_under_tests_is_temporary(self):
        here = logs_dir().resolve()
        self.assertNotEqual(here, REAL_LOGS_DIR.resolve())
        self.assertTrue(here.is_relative_to(Path(tempfile.gettempdir()).resolve()), here)

    def test_every_writer_resolves_into_the_temporary_folder(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import weekly_ingest
        from desk import backups, ingestion_health
        from desk.brief import record_skipped_run
        here = logs_dir().resolve()
        for path in (weekly_ingest.LOG_PATH, backups.EVENT_PATH, ingestion_health.LOG_PATH):
            self.assertTrue(path.resolve().is_relative_to(here), path)
        written = record_skipped_run("2099-01-01", "WARN fixture")   # default folder
        try:
            self.assertTrue(written.resolve().is_relative_to(here), written)
        finally:
            written.unlink()

    def test_the_p8055_scenario_now_lands_in_the_temporary_folder(self):
        """Exactly what leaked on 2026-10-11: a low-battery skip with only LOG_PATH patched."""
        import contextlib, io
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT / "scripts"))
        import weekly_ingest
        before = logs_snapshot(REAL_LOGS_DIR)
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(weekly_ingest, "LOG_PATH", Path(folder) / "ingest.log"), \
                patch.object(weekly_ingest, "STEPS", []), \
                patch.object(weekly_ingest, "power_status", return_value=(True, 10)), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(weekly_ingest.main(), 0)
        notice = logs_dir() / f"brief_{weekly_ingest.market_today().isoformat()}.txt"
        try:
            self.assertEqual(logs_snapshot(REAL_LOGS_DIR), before)        # nothing reached the real folder
            self.assertIn("nightly run skipped, on battery at 10%", notice.read_text(encoding="utf-8"))
        finally:
            notice.unlink(missing_ok=True)

    def test_snapshot_comparison_detects_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "kept.txt").write_text("a", encoding="utf-8")
            (folder / "gone.txt").write_text("b", encoding="utf-8")
            before = logs_snapshot(folder)
            (folder / "kept.txt").write_text("changed", encoding="utf-8")
            (folder / "gone.txt").unlink()
            (folder / "sub").mkdir()
            (folder / "sub" / "new.txt").write_text("c", encoding="utf-8")
            (folder / "suite.log").write_text("own output", encoding="utf-8")
            self.assertEqual(logs_changes(before, logs_snapshot(folder), ignore={"suite.log"}),
                             ["gone.txt: removed", "kept.txt: modified", "sub/new.txt: created"])


if __name__ == "__main__":
    unittest.main()
