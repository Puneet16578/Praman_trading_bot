"""Test package setup (P8-055 follow-up, 2026-10-12): no test writes into the real logs/ folder.

PRAMAN_LOGS_DIR (shared/log_paths.py) is pointed at a fresh temporary directory before any test
module can import a writer: discovery imports tests/test_000_logs_isolation.py first (sorted
names), which imports this package, and `python -m unittest tests.<module>` imports this package
first. REAL_LOGS_SNAPSHOT records the real folder at that moment; tests/test_zzz_real_logs_untouched.py
(last in discovery) fails if it changed during the run.
"""
import atexit
import os
from pathlib import Path
import shutil
import tempfile

REAL_LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"


def logs_snapshot(folder: Path) -> dict:
    """{relative path: (size, mtime_ns)} of every file under `folder`."""
    if not folder.exists():
        return {}
    return {p.relative_to(folder).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in folder.rglob("*") if p.is_file()}


def logs_changes(before: dict, after: dict, ignore=frozenset()) -> list:
    """Created, removed or modified files between two snapshots, except the `ignore` names."""
    names = (set(before) | set(after)) - set(ignore)
    return sorted(f"{name}: {'created' if name not in before else 'removed' if name not in after else 'modified'}"
                  for name in names if before.get(name) != after.get(name))


TEST_LOGS_DIR = Path(tempfile.mkdtemp(prefix="praman_test_logs_"))
os.environ["PRAMAN_LOGS_DIR"] = str(TEST_LOGS_DIR)
atexit.register(shutil.rmtree, TEST_LOGS_DIR, True)
REAL_LOGS_SNAPSHOT = logs_snapshot(REAL_LOGS_DIR)
