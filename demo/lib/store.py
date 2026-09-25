"""Read-only access to the demo store. The demo NEVER opens the production database
(data/processed/praman.db) -- it only ever opens the cutoff-truncated copy that
demo/build_demo_store.py produces. No function in this module accepts a caller-supplied path for
that reason: there is exactly one path the demo is allowed to read, and it is a constant.

Opened via `mode=ro` (SQLite's read-only URI mode), never `src.bitemporal.connection.get_connection`
-- verified directly (see tests/test_demo_readonly_guard.py) that mode=ro permits every read this
demo needs and raises sqlite3.OperationalError on any write attempt. init_db() is deliberately never
called here: the demo store already has the full schema (it is a backup of the production store),
and calling a schema-bootstrap function against a read-only connection is not a step this demo
needs, however harmless it happens to be.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DB_PATH = PROJECT_ROOT / "data" / "demo" / "praman_demo.sqlite"
DEMO_CLASSIFICATIONS_PATH = PROJECT_ROOT / "data" / "demo" / "event_classifications.csv"
DEMO_THRESHOLDS_PATH = PROJECT_ROOT / "data" / "demo" / "classification_thresholds.json"


class DemoStoreMissingError(FileNotFoundError):
    """Raised when data/demo/praman_demo.sqlite does not exist yet -- the demo cannot fall back to
    the production store under any circumstance, so this is a hard stop with instructions, not a
    silent substitution."""


def get_demo_connection() -> sqlite3.Connection:
    if not DEMO_DB_PATH.exists():
        raise DemoStoreMissingError(
            f"{DEMO_DB_PATH} does not exist. Run `python demo/build_demo_store.py` first -- "
            "the demo never opens the production store."
        )
    uri = f"file:{DEMO_DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def patch_reference_data_paths() -> None:
    """src/agent/reference_data.py reads classification_thresholds.json/event_classifications.csv
    from two hardcoded, project-root-relative paths -- it has no as_of or database-path parameter,
    because those two files are catalogue-wide batch artifacts, not something the live agent layer
    recomputes per call (see that module's own docstring). Left as-is (CLAUDE.md: no pipeline
    changes), this demo would silently score every event against the PRODUCTION, full-knowledge
    catalogue reference and thresholds -- cap_band and same_date_event_count computed with
    knowledge of dates after the cutoff, and a lead-time/ASM reference sourced from the untruncated
    history. Reassigning the two module-level path constants here points the SAME, unmodified
    functions at this demo's own cutoff-truncated artifacts instead -- no line of src/ is edited,
    only where an already-parameterized-by-module-constant path points is changed, from outside the
    module, before its @lru_cache(maxsize=1) is ever populated. Must be called before the first
    call to lookup_catalogue_reference()/load_thresholds() in this process."""
    from src.agent import reference_data

    reference_data.THRESHOLDS_PATH = DEMO_THRESHOLDS_PATH
    reference_data.CLASSIFICATIONS_PATH = DEMO_CLASSIFICATIONS_PATH
