"""Section 8's enforcement point: append-only writes. This module contains the only INSERT path
onto a bitemporal fact table and issues no UPDATE, ever -- a revised fact is a new row with a
later knowledge_date; the original row is never touched. `tests/test_no_update_on_fact_tables.py`
greps the whole src/ tree for UPDATE statements against these table names so this stays true by
construction, not by convention.

Shape validation (declared columns present, correct type, no null in a required field, non-empty
batch) lives HERE, not only in an ingestion module -- P2-001 (`docs/DEFECT_REGISTER.md`) is
exactly the failure mode this guards against: a data source or parser that produces a malformed
row without raising must still be caught before it reaches SQLite. Validation that lived only in
one ingestion module would be silently bypassed by the next source, or by a manual backfill.
"""
from __future__ import annotations
from datetime import datetime, timezone
import sqlite3

from .dates import DateValidationError, parse_date_str
from .schema import INTEGER, REAL, FactTable, get_fact_table

class StoreValidationError(ValueError):
    """Raised when a row/batch is malformed: missing a required field, an unrecognized field, a
    store-owned field set by the caller, a value of the wrong type, a null in a non-nullable
    field, or an empty batch. Always raised with a specific reason -- never a silent skip.
    """

_STORE_OWNED_FIELDS = {"row_id", "recorded_at"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _check_row_shape(table: FactTable, row: dict) -> None:
    if not isinstance(row, dict):
        raise StoreValidationError(f"Row for '{table.name}' must be a dict, got {type(row).__name__}.")

    owned_present = _STORE_OWNED_FIELDS & set(row)
    if owned_present:
        raise StoreValidationError(f"'{table.name}' row must not set store-owned field(s) {sorted(owned_present)}.")

    required = table.caller_supplied_columns
    missing = required - set(row)
    if missing:
        raise StoreValidationError(f"'{table.name}' row is missing required field(s): {sorted(missing)}.")
    unknown = set(row) - required
    if unknown:
        raise StoreValidationError(f"'{table.name}' row has unrecognized field(s): {sorted(unknown)}.")

    for column, value in row.items():
        if value is None:
            if column not in table.nullable_columns:
                raise StoreValidationError(f"'{table.name}'.{column} must not be null.")
            continue
        expected_type = table.column_types[column]
        if expected_type is bool:
            if not isinstance(value, bool):
                raise StoreValidationError(f"'{table.name}'.{column} must be bool, got {type(value).__name__}.")
        else:
            if isinstance(value, bool) or not isinstance(value, expected_type):
                raise StoreValidationError(f"'{table.name}'.{column} must be {expected_type.__name__}, got {type(value).__name__}.")

def _coerce_native(table: FactTable, row: dict) -> dict:
    """P2-002: `sqlite3` silently mis-binds a numpy.int64/float64 (what pandas-sourced ingestion
    values actually are) as a raw BLOB rather than an integer/float -- no exception, and
    `_check_row_shape`'s `numbers.Integral`/`numbers.Real` check does not catch it, since numpy
    scalars satisfy those ABCs. Coercing to the declared native type here, after shape validation
    has already confirmed the value IS a valid Integral/Real, is lossless and guarantees sqlite3
    receives a type it actually knows how to persist -- regardless of what numeric type a future
    ingestion source happens to hand the store.
    """
    values = dict(row)
    for column, value in row.items():
        if value is None:
            continue
        expected_type = table.column_types[column]
        if expected_type is INTEGER:
            values[column] = int(value)
        elif expected_type is REAL:
            values[column] = float(value)
    return values

def _normalized_values(table: FactTable, row: dict) -> dict:
    """Row already shape-checked by `_check_row_shape`; parses event_date/knowledge_date to a
    canonical string, coerces numeric values to native types (P2-002), and stamps the store-owned
    recorded_at."""
    try:
        event_date = parse_date_str(row["event_date"], "event_date")
        knowledge_date = parse_date_str(row["knowledge_date"], "knowledge_date")
    except DateValidationError as exc:
        raise StoreValidationError(str(exc)) from exc

    values = _coerce_native(table, row)
    values["event_date"] = event_date
    values["knowledge_date"] = knowledge_date
    values["recorded_at"] = _now()
    return values

def write_fact(conn: sqlite3.Connection, table_name: str, row: dict) -> int:
    """Inserts one fact row. Every column except row_id/recorded_at must be supplied explicitly
    (nullable columns included, as None) -- there is no silent 'missing means null'. A re-insert
    of an existing (business key, knowledge_date) is rejected, not silently ignored -- a genuine
    restatement needs a new knowledge_date. Returns the new row_id.
    """
    table = get_fact_table(table_name)
    _check_row_shape(table, row)
    values = _normalized_values(table, row)

    columns = sorted(values)
    placeholders = ",".join("?" for _ in columns)
    query = f"INSERT INTO {table.name} ({','.join(columns)}) VALUES ({placeholders})"
    try:
        cursor = conn.execute(query, [values[c] for c in columns])
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise StoreValidationError(
            f"'{table_name}' already has a row with this exact (business key, knowledge_date) -- "
            "a genuine restatement needs a new knowledge_date, not a re-insert of the same vintage."
        ) from exc
    return cursor.lastrowid

class BulkWriteResult:
    def __init__(self, inserted: int, skipped_duplicate: int):
        self.inserted = inserted
        self.skipped_duplicate = skipped_duplicate

    def __repr__(self) -> str:
        return f"BulkWriteResult(inserted={self.inserted}, skipped_duplicate={self.skipped_duplicate})"

def write_facts(conn: sqlite3.Connection, table_name: str, rows: list[dict]) -> BulkWriteResult:
    """Bulk ingestion write path. Every row is shape-validated BEFORE any row is written -- one
    malformed row rejects the whole batch (fail-closed), never a partial write. This is what
    'idempotent and re-runnable' ingestion actually calls: re-ingesting a file whose rows are
    already present (identical business key + knowledge_date) is expected and reports those rows
    as `skipped_duplicate`, not an error -- that is what makes re-running ingestion produce no new
    rows. This is a distinct, intentional difference from `write_fact()`, which raises on a
    duplicate single insert; a bulk ingestion re-run hitting the same fact it already recorded is
    the normal case, not a caller mistake.
    """
    if not isinstance(rows, list) or not rows:
        raise StoreValidationError(f"'{table_name}' batch must be a non-empty list of rows.")

    table = get_fact_table(table_name)
    normalized = []
    for row in rows:
        _check_row_shape(table, row)
        normalized.append(_normalized_values(table, row))

    columns = sorted(normalized[0])
    placeholders = ",".join("?" for _ in columns)
    query = f"INSERT INTO {table.name} ({','.join(columns)}) VALUES ({placeholders})"

    inserted = 0
    skipped_duplicate = 0
    for values in normalized:
        try:
            conn.execute(query, [values[c] for c in columns])
            inserted += 1
        except sqlite3.IntegrityError:
            skipped_duplicate += 1
    conn.commit()
    return BulkWriteResult(inserted=inserted, skipped_duplicate=skipped_duplicate)
