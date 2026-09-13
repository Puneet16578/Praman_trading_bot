"""Bitemporal table registry.

Every fact table this project ever writes is declared here, once. A table's DDL, its business
key (the columns that identify "the same fact" across restatements), its full column list, and
now its declared per-column type/nullability all live in one place -- `guard.py` and `store.py`
both read this registry rather than knowing about individual tables, so a new fact table cannot
silently skip the event_date/knowledge_date requirement (Section 7) the way a hand-rolled CREATE
TABLE elsewhere could. `FactTable.__post_init__` raises if any entry violates that requirement --
this is enforced by construction, not by reviewer attention.

`column_types`/`nullable_columns` exist specifically so `store.py` can independently validate a
row's *shape* (declared columns present, correct type, no null in a required field) before it
reaches SQLite -- this is what caught P2-001 (`docs/DEFECT_REGISTER.md`): a data source or parser
bug that produces a malformed row must never reach storage just because nothing upstream happened
to raise an exception.
"""
from __future__ import annotations
from dataclasses import dataclass
import numbers

# Type markers used in `column_types`. Numeric columns are checked with `numbers.Integral`/
# `numbers.Real` rather than bare `int`/`float` because ingestion sources are frequently pandas/
# numpy-backed (numpy.int64, numpy.float64 do not subclass Python's builtin int/float, but they do
# register with these ABCs). `bool` is its own marker, checked separately, because Python's `bool`
# is an `int` subclass and would otherwise silently pass an Integral check -- a column that is
# genuinely boolean-shaped (e.g. sebi_orders.needs_review) declares `bool` explicitly; no numeric
# column should ever accept a bare `True`/`False`.
INTEGER = numbers.Integral
REAL = numbers.Real

@dataclass(frozen=True)
class FactTable:
    name: str
    ddl: str
    columns: frozenset[str]
    business_key: tuple[str, ...]  # columns identifying "the same fact" across knowledge_date restatements
    column_types: dict[str, type]  # every column in `columns` -> its declared Python type marker
    nullable_columns: frozenset[str] = frozenset()  # subset of columns allowed to be None

    def __post_init__(self) -> None:
        if "event_date" not in self.columns or "knowledge_date" not in self.columns:
            raise ValueError(f"Fact table '{self.name}' is missing event_date and/or knowledge_date -- Section 7 violation.")
        if not set(self.business_key) <= self.columns:
            raise ValueError(f"Fact table '{self.name}' business_key references undeclared column(s): {set(self.business_key) - self.columns}.")
        if "knowledge_date" in self.business_key:
            raise ValueError(f"Fact table '{self.name}' business_key must not include knowledge_date -- it is what distinguishes vintages of the same fact, not part of identifying the fact.")
        if set(self.column_types) != self.columns:
            raise ValueError(f"Fact table '{self.name}' column_types must declare a type for exactly every column; "
                              f"missing={self.columns - set(self.column_types)}, extra={set(self.column_types) - self.columns}.")
        if not self.nullable_columns <= self.columns:
            raise ValueError(f"Fact table '{self.name}' nullable_columns references undeclared column(s): {self.nullable_columns - self.columns}.")

    @property
    def caller_supplied_columns(self) -> frozenset[str]:
        """Columns a writer must supply -- everything except the store-owned row_id/recorded_at."""
        return self.columns - {"row_id", "recorded_at"}

# prev_close, as reported in the source bhavcopy file, is provenance only -- it is NSE's own
# unadjusted prior close following the exchange's own ex-date convention, not a value this project
# computed. Signal code must NEVER treat this column as "the previous close" for a return or move
# calculation: the actual previous close for signal purposes is derived from this project's own
# as-of, corporate-action-adjusted price series (Section 11), which this raw column deliberately
# does not encode. Using prev_close directly for a return calculation silently reintroduces
# look-ahead/adjustment bugs this project exists to avoid.
BHAVCOPY = FactTable(
    name="bhavcopy",
    ddl="""
        CREATE TABLE bhavcopy (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            event_date TEXT NOT NULL,
            knowledge_date TEXT NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            prev_close REAL NOT NULL,  -- as reported by NSE; NOT the as-of adjusted previous close, see module note above
            traded_qty INTEGER NOT NULL,
            delivery_qty INTEGER,
            delivery_pct REAL,
            series TEXT NOT NULL,
            source_file TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            UNIQUE (symbol, event_date, knowledge_date, series)
        )
    """,
    columns=frozenset({"row_id", "symbol", "event_date", "knowledge_date", "open_price", "high_price",
                        "low_price", "close_price", "prev_close", "traded_qty", "delivery_qty",
                        "delivery_pct", "series", "source_file", "recorded_at"}),
    business_key=("symbol", "event_date", "series"),
    column_types={
        "row_id": INTEGER, "symbol": str, "event_date": str, "knowledge_date": str,
        "open_price": REAL, "high_price": REAL, "low_price": REAL, "close_price": REAL, "prev_close": REAL,
        "traded_qty": INTEGER, "delivery_qty": INTEGER, "delivery_pct": REAL,
        "series": str, "source_file": str, "recorded_at": str,
    },
    nullable_columns=frozenset({"delivery_qty", "delivery_pct"}),
)

# confidence_tier records HOW this row's knowledge_date/ratio were established -- see
# src/ingestion/nse_market_data/corporate_actions.py for the full scheme (CONFIRMED,
# MATCHED_UNCONFIRMED, EX_DATE_FALLBACK, QUARANTINE-never-written, DEMERGER_EXCLUSION). Any
# timing-sensitive signal (e.g. pre-announcement accumulation detection) MUST filter out
# EX_DATE_FALLBACK rows explicitly -- their knowledge_date is a safe stand-in for adjustment
# purposes only, not a real announcement date. Enforced by
# tests/test_corporate_actions_ingestion.py, not left to a future caller to remember.
CORPORATE_ACTIONS = FactTable(
    name="corporate_actions",
    ddl="""
        CREATE TABLE corporate_actions (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action_type TEXT NOT NULL,
            event_date TEXT NOT NULL,
            knowledge_date TEXT NOT NULL,
            ratio_numerator REAL,
            ratio_denominator REAL,
            confidence_tier TEXT NOT NULL,
            details TEXT,
            source_file TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            UNIQUE (symbol, action_type, event_date, knowledge_date)
        )
    """,
    columns=frozenset({"row_id", "symbol", "action_type", "event_date", "knowledge_date",
                        "ratio_numerator", "ratio_denominator", "confidence_tier", "details",
                        "source_file", "recorded_at"}),
    business_key=("symbol", "action_type", "event_date"),
    column_types={
        "row_id": INTEGER, "symbol": str, "action_type": str, "event_date": str, "knowledge_date": str,
        "ratio_numerator": REAL, "ratio_denominator": REAL, "confidence_tier": str, "details": str,
        "source_file": str, "recorded_at": str,
    },
    nullable_columns=frozenset({"ratio_numerator", "ratio_denominator", "details"}),
)

SURVEILLANCE_FLAGS = FactTable(
    name="surveillance_flags",
    ddl="""
        CREATE TABLE surveillance_flags (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            stage TEXT NOT NULL,
            event_date TEXT NOT NULL,
            knowledge_date TEXT NOT NULL,
            source_file TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            UNIQUE (symbol, stage, event_date, knowledge_date)
        )
    """,
    columns=frozenset({"row_id", "symbol", "stage", "event_date", "knowledge_date", "source_file", "recorded_at"}),
    business_key=("symbol", "stage", "event_date"),
    column_types={
        "row_id": INTEGER, "symbol": str, "stage": str, "event_date": str,
        "knowledge_date": str, "source_file": str, "recorded_at": str,
    },
)

SEBI_ORDERS = FactTable(
    name="sebi_orders",
    ddl="""
        CREATE TABLE sebi_orders (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            symbol TEXT,
            event_date TEXT NOT NULL,
            knowledge_date TEXT NOT NULL,
            needs_review INTEGER NOT NULL DEFAULT 1,
            pdf_url TEXT NOT NULL,
            raw_text_excerpt TEXT,
            recorded_at TEXT NOT NULL,
            UNIQUE (order_id, knowledge_date)
        )
    """,
    columns=frozenset({"row_id", "order_id", "entity_name", "symbol", "event_date", "knowledge_date",
                        "needs_review", "pdf_url", "raw_text_excerpt", "recorded_at"}),
    business_key=("order_id",),
    column_types={
        "row_id": INTEGER, "order_id": str, "entity_name": str, "symbol": str,
        "event_date": str, "knowledge_date": str, "needs_review": bool,
        "pdf_url": str, "raw_text_excerpt": str, "recorded_at": str,
    },
    nullable_columns=frozenset({"symbol", "raw_text_excerpt"}),
)

BITEMPORAL_TABLES: dict[str, FactTable] = {
    t.name: t for t in (BHAVCOPY, CORPORATE_ACTIONS, SURVEILLANCE_FLAGS, SEBI_ORDERS)
}

def get_fact_table(name: str) -> FactTable:
    if name not in BITEMPORAL_TABLES:
        raise ValueError(f"'{name}' is not a registered bitemporal fact table.")
    return BITEMPORAL_TABLES[name]
