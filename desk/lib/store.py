"""Read-only access to the REAL, current production Praman store (data/processed/praman.db) --
never the demo's cutoff-truncated copy. The Desk needs today's real data; nothing here is
cutoff-truncated the way demo/lib/store.py's target deliberately is.

Two connection modes:
- `get_live_connection()`: an ordinary mode=ro connection, unfiltered -- what `desk assess` and
  `desk monitor` use to see the full, current store.
- `get_replay_connection(watermark)`: a mode=ro connection with a TEMP VIEW shadowing every Praman
  fact table, each filtered to `recorded_at <= watermark`. Every unqualified table reference made by
  ANY Praman function called through this connection -- read_as_of, latest_as_of,
  build_symbol_history, get_disclosure_window, current_surveillance_state, anything -- transparently
  sees only rows that existed as of the watermark, with no change to Praman's own code and no need
  to know which tables a given assessment path touches. SQLite resolves an unqualified table name
  against TEMP before MAIN, which is what makes this work; `main.<table>` still reaches the real,
  unfiltered table if anything ever needs it explicitly.

Chosen over reconstructing a scratch copy (the method used for the Phase 8 reproducibility check)
specifically because "does this specific Praman function happen to be covered by the copy" is a
question you'd have to keep re-answering by hand as Praman itself grows; view-shadowing is complete
by construction; a table added or a cross-sectional read added to any Praman function later is
automatically covered without desk/ code changing at all.

Verified directly before relying on this (not assumed from SQLite documentation alone):
  - CREATE TEMP VIEW succeeds against a connection opened mode=ro (TEMP objects live in a separate
    temp store, not the read-only main file).
  - An unqualified `SELECT * FROM bhavcopy` resolves to the shadowing view, not main.bhavcopy.
  - EXPLAIN QUERY PLAN is IDENTICAL with and without the shadow view for a query that already uses
    an index (corporate_announcements' symbol+event_date index) -- SQLite flattens the simple view
    and pushes the caller's predicate into the same index scan; the view's own recorded_at filter is
    applied as a cheap residual condition, not a second full scan.
"""
from __future__ import annotations
import re
import sqlite3
from pathlib import Path

from shared.sqlite_readonly import open_readonly

# ISO-8601 with a UTC offset, e.g. "2026-09-22T04:53:49.123456+00:00" -- the exact shape
# datetime.now(timezone.utc).isoformat() produces (src/bitemporal/store.py's `_now()`), which is
# what every recorded_at value in the store actually is.
_WATERMARK_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?[+-]\d{2}:\d{2}$")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_DB_PATH = PROJECT_ROOT / "data" / "processed" / "praman.db"

# Every fact table Praman's bitemporal store registers (src/bitemporal/schema.py's
# BITEMPORAL_TABLES) -- kept as a literal tuple here, not imported from schema.py, so a change to
# that registry is a visible, deliberate edit to this list too, not a silent new gap in replay
# coverage. test_desk_replay_view_coverage.py asserts this tuple still matches schema.py's registry.
PRAMAN_FACT_TABLES = (
    "bhavcopy",
    "corporate_actions",
    "surveillance_flags",
    "corporate_announcements",
    "sebi_orders",
)


class ProductionStoreMissingError(FileNotFoundError):
    """Raised when data/processed/praman.db does not exist -- the Desk never falls back to any
    other store (not the demo copy, not a fixture) under any circumstance."""


def get_live_connection() -> sqlite3.Connection:
    """Unfiltered, read-only connection to the real, current production store."""
    if not PRODUCTION_DB_PATH.exists():
        raise ProductionStoreMissingError(
            f"{PRODUCTION_DB_PATH} does not exist. The Desk requires the real Praman store; "
            "it never substitutes the demo copy or a fixture."
        )
    return open_readonly(PRODUCTION_DB_PATH)


def get_replay_connection(watermark: str) -> sqlite3.Connection:
    """Read-only connection to production with every Praman fact table shadowed by a TEMP VIEW
    filtered to `recorded_at <= watermark`. `watermark` must be the exact ISO-8601 string recorded
    on the decision being replayed (praman_watermark, not desk_watermark -- see desk/replay.py)."""
    if not _WATERMARK_RE.match(watermark):
        raise ValueError(
            f"watermark {watermark!r} is not a recorded_at-shaped ISO-8601 timestamp "
            "(expected e.g. '2026-09-22T04:53:49.123456+00:00') -- refusing to interpolate an "
            "unvalidated string into a CREATE VIEW statement (SQLite does not allow bound "
            "parameters inside a view definition)."
        )
    conn = get_live_connection()
    for table in PRAMAN_FACT_TABLES:
        conn.execute(
            f"CREATE TEMP VIEW {table} AS SELECT * FROM main.{table} WHERE recorded_at <= '{watermark}'"
        )
    return conn


def max_recorded_at(conn: sqlite3.Connection) -> str:
    """The Praman store watermark: the maximum recorded_at across every fact table, as read through
    THIS connection. Deliberately unqualified (`FROM {table}`, not `FROM main.{table}`) so that on a
    replay connection this resolves to the shadowing TEMP VIEW and correctly returns the replay's
    own bound, not production's current one; on a live connection there is no shadow and it reads
    main.<table> directly, identically either way."""
    values = []
    for table in PRAMAN_FACT_TABLES:
        row = conn.execute(f"SELECT MAX(recorded_at) AS m FROM {table}").fetchone()
        if row["m"] is not None:
            values.append(row["m"])
    if not values:
        raise RuntimeError("No rows in any Praman fact table -- cannot compute a watermark.")
    return max(values)
