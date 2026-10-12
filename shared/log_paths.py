"""Where the `logs/` folder is: the one place every writer resolves it (P8-055 follow-up, 2026-10-12).

Tests never write into the real folder, the same rule the databases follow (tests use temporary
stores): `tests/__init__.py` points PRAMAN_LOGS_DIR at a fresh temporary directory before any test
module imports a writer, and `tests/test_zzz_real_logs_untouched.py` fails the suite if the real
folder changed during the run anyway. Production never sets the variable.
"""
from __future__ import annotations

import os
from pathlib import Path

REAL_LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
ENV = "PRAMAN_LOGS_DIR"


def logs_dir() -> Path:
    override = os.environ.get(ENV)
    return Path(override) if override else REAL_LOGS_DIR
