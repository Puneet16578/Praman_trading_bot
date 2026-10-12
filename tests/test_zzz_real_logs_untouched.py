"""Runs last in discovery (sorted names): fails if the real logs/ folder changed during the test run
(P8-055 follow-up). The files this process's own stdout/stderr are redirected to are excluded: a
suite log written by the shell is not a test writing into logs/. A nightly ingestion running at the
same time would also show up here; do not run the suite during it."""
import os
import unittest

import tests
from tests import REAL_LOGS_DIR, logs_changes, logs_snapshot


def _own_output_files() -> set:
    """Real-logs file names that this process's stdout or stderr is redirected into."""
    own = set()
    for fd in (1, 2):
        try:
            stat = os.fstat(fd)
        except OSError:
            continue
        for path in REAL_LOGS_DIR.rglob("*"):
            if path.is_file():
                other = path.stat()
                if (other.st_dev, other.st_ino) == (stat.st_dev, stat.st_ino) and stat.st_ino:
                    own.add(path.relative_to(REAL_LOGS_DIR).as_posix())
    return own


class RealLogsUntouchedTest(unittest.TestCase):
    def test_no_test_wrote_into_the_real_logs_folder(self):
        changed = logs_changes(tests.REAL_LOGS_SNAPSHOT, logs_snapshot(REAL_LOGS_DIR), ignore=_own_output_files())
        self.assertEqual(changed, [], 'The real logs/ folder changed during the test run (a test wrote there, '
                                      'or a nightly ran concurrently). Tests must write only to temporary folders.')


if __name__ == "__main__":
    unittest.main()
