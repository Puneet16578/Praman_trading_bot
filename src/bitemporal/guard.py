"""The temporal query guard -- Section 7's enforcement point.

This is the ONLY sanctioned way to read a bitemporal fact table. It is deliberately as strict as
`authorization.py` is in InsightForge: `as_of` is mandatory and validated, filter columns are
checked against an allowlist (the table's declared columns) before they ever reach a query
string, and an unknown table name fails closed rather than returning an empty result. A caller
that reaches SQLite directly, bypassing this module, is the bug Section 7 describes -- there is
no other path into these tables' data by design.

Two read shapes, because they answer genuinely different questions:
- `read_as_of`: every vintage of every fact visible as of a given date (audit / "what did we
  know, and when, about this fact" -- Section 8's restatement history has to be queryable).
- `latest_as_of`: one row per business key -- the most-recently-known version of each fact as of
  that date. This is what signal computation actually wants.
"""
from __future__ import annotations
import sqlite3

from .dates import DateValidationError, parse_date_str
from .schema import get_fact_table

class TemporalGuardError(ValueError):
    """Raised for any as_of, table, or filter misuse. Always fails closed -- never returns a
    partial or best-effort result for malformed input."""

def _validate_as_of(as_of) -> str:
    try:
        return parse_date_str(as_of, "as_of")
    except DateValidationError as exc:
        raise TemporalGuardError(str(exc)) from exc

def _validate_filters(table_name: str, columns: frozenset[str], filters: dict) -> None:
    unknown = set(filters) - columns
    if unknown:
        raise TemporalGuardError(f"'{table_name}' has no column(s) {sorted(unknown)} to filter on.")

def read_as_of(conn: sqlite3.Connection, table_name: str, as_of, **filters) -> list[dict]:
    table = get_fact_table(table_name)  # raises TemporalGuardError-compatible ValueError for unknown table
    as_of_str = _validate_as_of(as_of)
    _validate_filters(table_name, table.columns, filters)

    clauses = ["knowledge_date <= ?"]
    params: list = [as_of_str]
    for column, value in filters.items():
        clauses.append(f"{column} = ?")
        params.append(value)

    query = f"SELECT * FROM {table.name} WHERE {' AND '.join(clauses)}"
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]

def latest_as_of(conn: sqlite3.Connection, table_name: str, as_of, **filters) -> list[dict]:
    table = get_fact_table(table_name)
    rows = read_as_of(conn, table_name, as_of, **filters)

    best: dict[tuple, dict] = {}
    for row in rows:
        key = tuple(row[col] for col in table.business_key)
        current = best.get(key)
        if current is None or (row["knowledge_date"], row["row_id"]) > (current["knowledge_date"], current["row_id"]):
            best[key] = row
    return list(best.values())
