"""P8-059: the nightly runs nothing while a file it runs or reads has an uncommitted change.

Uses a real temporary git repository (never this one) for the status parsing."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import weekly_ingest


def git(root, *args):
    subprocess.run([weekly_ingest._git(), *args], cwd=root, check=True, capture_output=True)


@unittest.skipUnless(weekly_ingest._git(), "git is not installed")
class UncommittedInputsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        files = {"desk/a.py": "x = 1\n", "scripts/s.py": "y = 1\n", "config/c.json": "{}\n",
                 "docs/notes.md": "notes\n", "docs/DEFECT_REGISTER.md": "# register\n", "theses/t.yaml": "a: 1\n"}
        for name, text in files.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding="utf-8")
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "fixture")

    def inputs(self):
        return weekly_ingest.uncommitted_nightly_inputs(self.root)

    def test_clean_tree_has_no_uncommitted_inputs(self):
        self.assertEqual(self.inputs(), [])

    def test_code_config_and_read_docs_trip_it_other_docs_and_theses_do_not(self):
        (self.root / "desk/a.py").write_text("x = 2\n", encoding="utf-8")                 # tracked, modified
        (self.root / "scripts/new.py").write_text("z = 1\n", encoding="utf-8")            # untracked
        (self.root / "desk/sub").mkdir()
        (self.root / "desk/sub/deep.py").write_text("w = 1\n", encoding="utf-8")          # untracked, new folder
        (self.root / "config/with space.json").write_text("{}\n", encoding="utf-8")       # untracked, odd name
        (self.root / "docs/DEFECT_REGISTER.md").write_text("# edited\n", encoding="utf-8")  # read by the nightly
        (self.root / "docs/notes.md").write_text("edited\n", encoding="utf-8")            # other docs: ignored
        (self.root / "theses/t.yaml").write_text("a: 2\n", encoding="utf-8")              # theses: ignored
        (self.root / "theses/new.yaml").write_text("b: 1\n", encoding="utf-8")
        self.assertEqual(self.inputs(), ["config/with space.json", "desk/a.py", "desk/sub/deep.py",
                                         "docs/DEFECT_REGISTER.md", "scripts/new.py"])

    def test_a_rename_reports_both_paths(self):
        git(self.root, "mv", "scripts/s.py", "scripts/renamed.py")
        self.assertEqual(self.inputs(), ["scripts/renamed.py", "scripts/s.py"])

    def test_the_status_check_never_writes_to_the_repository(self):
        index = self.root / ".git" / "index"
        before = index.stat().st_mtime_ns
        later = before + 5_000_000_000
        os.utime(self.root / "desk/a.py", ns=(later, later))     # stat change only: a refresh would rewrite the index
        self.assertEqual(self.inputs(), [])
        self.assertEqual(index.stat().st_mtime_ns, before)
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_git_missing_or_failing_returns_none(self):
        with patch.object(weekly_ingest, "_git", return_value=None):
            self.assertIsNone(self.inputs())
        self.assertIsNone(weekly_ingest.uncommitted_nightly_inputs(self.root / "no such folder"))   # cannot start
        failed = subprocess.CompletedProcess(args=[], returncode=128, stdout=b"", stderr=b"fatal")
        with patch.object(weekly_ingest.subprocess, "run", return_value=failed):
            self.assertIsNone(self.inputs())                                                     # git errors

    def test_git_is_found_without_it_on_path(self):
        with patch.object(weekly_ingest.shutil, "which", return_value=None):
            expected = str(weekly_ingest.GIT_FALLBACK) if weekly_ingest.GIT_FALLBACK.exists() else None
            self.assertEqual(weekly_ingest._git(), expected)


@unittest.skipUnless(weekly_ingest._git(), "git is not installed")
class HeadBranchTest(unittest.TestCase):
    """P8-059 follow-up: the nightly runs only with master checked out."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "desk").mkdir()
        (self.root / "desk/a.py").write_text("x = 1\n", encoding="utf-8")
        git(self.root, "init", "-q")
        git(self.root, "symbolic-ref", "HEAD", "refs/heads/master")
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "fixture")

    def test_master_another_branch_and_detached_head(self):
        self.assertEqual(weekly_ingest.head_branch(self.root), "master")
        git(self.root, "checkout", "-q", "-b", "other")
        self.assertEqual(weekly_ingest.head_branch(self.root), "other")
        git(self.root, "checkout", "-q", "--detach", "master")
        self.assertEqual(weekly_ingest.head_branch(self.root), "HEAD")

    def test_reading_the_branch_never_writes_to_the_repository(self):
        index = self.root / ".git" / "index"
        before = index.stat().st_mtime_ns
        self.assertEqual(weekly_ingest.head_branch(self.root), "master")
        self.assertEqual(index.stat().st_mtime_ns, before)
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_git_missing_or_failing_returns_none(self):
        with patch.object(weekly_ingest, "_git", return_value=None):
            self.assertIsNone(weekly_ingest.head_branch(self.root))
        self.assertIsNone(weekly_ingest.head_branch(self.root / "no such folder"))
        failed = subprocess.CompletedProcess(args=[], returncode=128, stdout=b"", stderr=b"fatal")
        with patch.object(weekly_ingest.subprocess, "run", return_value=failed):
            self.assertIsNone(weekly_ingest.head_branch(self.root))


class NightlyGuardTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.log = Path(temporary.name) / "ingest.log"

    def run_main(self, inputs, branch="master"):
        ran = []
        with patch.object(weekly_ingest, "LOG_PATH", self.log), \
                patch.object(weekly_ingest, "STEPS", [("first", lambda: ran.append("first"))]), \
                patch.object(weekly_ingest, "_prevent_sleep", contextlib.nullcontext), \
                patch.object(weekly_ingest, "power_status", return_value=(False, None)), \
                patch.object(weekly_ingest, "head_branch", return_value=branch), \
                patch.object(weekly_ingest, "uncommitted_nightly_inputs", return_value=inputs), \
                patch("desk.brief.record_skipped_run") as brief, \
                contextlib.redirect_stdout(io.StringIO()):
            return weekly_ingest.main(), ran, brief

    def test_clean_tree_runs_normally(self):
        code, ran, brief = self.run_main([])
        self.assertEqual((code, ran), (0, ["first"]))
        self.assertIn("weekly_ingest started", self.log.read_text(encoding="utf-8"))
        brief.assert_not_called()

    def test_dirty_tree_skips_with_a_warn_naming_the_files(self):
        code, ran, brief = self.run_main(["desk/monitor.py", "scripts/new.py"])
        self.assertEqual((code, ran), (0, []))
        text = self.log.read_text(encoding="utf-8")
        self.assertIn("weekly_ingest skipped: WARN uncommitted changes in files the nightly runs or reads: "
                      "desk/monitor.py, scripts/new.py; no step ran; the next run catches up", text)
        self.assertNotIn("weekly_ingest started", text)
        self.assertIn("desk/monitor.py, scripts/new.py", brief.call_args.args[1])

    def test_long_lists_are_shortened(self):
        self.run_main([f"desk/m{i:02d}.py" for i in range(13)])
        self.assertIn("desk/m09.py and 3 more", self.log.read_text(encoding="utf-8"))

    def test_git_unavailable_skips(self):
        code, ran, _ = self.run_main(None)
        self.assertEqual((code, ran), (0, []))
        self.assertIn("skipped: WARN git status could not run", self.log.read_text(encoding="utf-8"))

    def test_another_branch_or_detached_head_skips(self):
        from desk.ingestion_health import skips_by_decision_date
        for branch, where in (("other", "on branch other"), ("HEAD", "detached")):
            with self.subTest(branch=branch):
                code, ran, brief = self.run_main([], branch=branch)
                self.assertEqual((code, ran), (0, []))
                warn = f"HEAD is {where}, not master; the nightly runs only on master"
                self.assertIn(f"skipped: WARN {warn}; no step ran", self.log.read_text(encoding="utf-8"))
                self.assertIn(warn, brief.call_args.args[1])
        with patch("desk.ingestion_health.LOG_PATH", self.log):
            self.assertEqual({s["reason"] for s in skips_by_decision_date().values()}, {"NOT_ON_MASTER"})

    def test_branch_is_checked_before_the_tree_and_an_unreadable_head_skips(self):
        self.run_main(["desk/x.py"], branch="other")
        text = self.log.read_text(encoding="utf-8")
        self.assertIn("WARN HEAD is on branch other", text)
        self.assertNotIn("uncommitted", text)
        code, ran, _ = self.run_main([], branch=None)
        self.assertEqual((code, ran), (0, []))
        self.assertIn("skipped: WARN git could not read HEAD", self.log.read_text(encoding="utf-8"))
        from desk.ingestion_health import skips_by_decision_date
        with patch("desk.ingestion_health.LOG_PATH", self.log):
            (skips,) = skips_by_decision_date().values()       # both runs would have decided the same date
        self.assertEqual((skips["reason"], len(skips["skips"])), ("GIT_UNAVAILABLE", 2))


if __name__ == "__main__":
    unittest.main()
