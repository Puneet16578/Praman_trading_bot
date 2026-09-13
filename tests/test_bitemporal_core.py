"""Phase 1: bitemporal core tests. Fixture data only (synthetic, clearly not real NSE/SEBI data)
-- this proves the plumbing, not the guard against real-world messiness. Per CLAUDE.md, the guard
must additionally be re-tested against real ingested data once it exists; that is a separate,
still-owed test file, not a substitute for this one.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.dates import DateValidationError, parse_date_str
from src.bitemporal.guard import TemporalGuardError, latest_as_of, read_as_of
from src.bitemporal.schema import BITEMPORAL_TABLES, FactTable
from src.bitemporal.store import StoreValidationError, write_fact, write_facts

def make_bhavcopy_row(**overrides) -> dict:
    base = {
        "symbol": "FIXTURECO", "event_date": "2021-06-01", "knowledge_date": "2021-06-02",
        "open_price": 100.0, "high_price": 105.0, "low_price": 99.0, "close_price": 104.0,
        "prev_close": 98.0, "traded_qty": 10000, "delivery_qty": 4000, "delivery_pct": 40.0,
        "series": "EQ", "source_file": "fixture_bhavcopy_20210601.csv",
    }
    base.update(overrides)
    return base

class SchemaRegistrySelfCheckTest(unittest.TestCase):
    def test_rejects_fact_table_missing_event_or_knowledge_date(self):
        with self.assertRaises(ValueError):
            FactTable(name="bad", ddl="CREATE TABLE bad (event_date TEXT)",
                      columns=frozenset({"event_date"}), business_key=(),
                      column_types={"event_date": str})

    def test_rejects_business_key_referencing_undeclared_column(self):
        with self.assertRaises(ValueError):
            FactTable(name="bad", ddl="x", columns=frozenset({"event_date", "knowledge_date"}),
                      business_key=("not_a_column",),
                      column_types={"event_date": str, "knowledge_date": str})

    def test_rejects_business_key_containing_knowledge_date(self):
        with self.assertRaises(ValueError):
            FactTable(name="bad", ddl="x", columns=frozenset({"event_date", "knowledge_date"}),
                      business_key=("knowledge_date",),
                      column_types={"event_date": str, "knowledge_date": str})

    def test_rejects_column_types_not_matching_columns_exactly(self):
        with self.assertRaises(ValueError):
            FactTable(name="bad", ddl="x", columns=frozenset({"event_date", "knowledge_date"}),
                      business_key=(), column_types={"event_date": str})  # missing knowledge_date

    def test_every_registered_table_is_actually_bitemporal(self):
        for table in BITEMPORAL_TABLES.values():
            self.assertIn("event_date", table.columns)
            self.assertIn("knowledge_date", table.columns)

class DateValidatorTest(unittest.TestCase):
    def test_accepts_iso_string(self):
        self.assertEqual(parse_date_str("2021-06-01"), "2021-06-01")

    def test_rejects_none(self):
        with self.assertRaises(DateValidationError):
            parse_date_str(None)

    def test_rejects_non_iso_string(self):
        with self.assertRaises(DateValidationError):
            parse_date_str("06/01/2021")

    def test_rejects_empty_string(self):
        with self.assertRaises(DateValidationError):
            parse_date_str("")

class GuardFailsClosedTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row())

    def test_missing_as_of_raises(self):
        with self.assertRaises(TypeError):
            read_as_of(self.conn, "bhavcopy")  # as_of is a required positional arg

    def test_none_as_of_raises(self):
        with self.assertRaises(TemporalGuardError):
            read_as_of(self.conn, "bhavcopy", None)

    def test_malformed_as_of_raises(self):
        with self.assertRaises(TemporalGuardError):
            read_as_of(self.conn, "bhavcopy", "not-a-date")

    def test_unknown_table_raises(self):
        with self.assertRaises(ValueError):
            read_as_of(self.conn, "not_a_real_table", "2021-06-02")

    def test_unknown_filter_column_raises(self):
        with self.assertRaises(TemporalGuardError):
            read_as_of(self.conn, "bhavcopy", "2021-06-02", not_a_column="x")

    def test_row_visible_on_or_after_its_knowledge_date(self):
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2021-06-02")), 1)
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2021-12-31")), 1)

    def test_row_invisible_before_its_knowledge_date(self):
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2021-06-01")), 0)

class RestatementNeverOverwritesTest(unittest.TestCase):
    """Section 8: a corrected bhavcopy file is a NEW row with a later knowledge_date -- proves
    both read_as_of (full vintage history) and latest_as_of (deduped) see this correctly."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row(close_price=104.0, knowledge_date="2021-06-02"))
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row(close_price=104.5, knowledge_date="2021-06-05"))

    def test_original_row_still_present_after_restatement(self):
        vintages = read_as_of(self.conn, "bhavcopy", "2021-12-31")
        self.assertEqual(len(vintages), 2)
        self.assertEqual(sorted(v["close_price"] for v in vintages), [104.0, 104.5])

    def test_latest_as_of_before_correction_sees_only_original(self):
        latest = latest_as_of(self.conn, "bhavcopy", "2021-06-03")
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["close_price"], 104.0)

    def test_latest_as_of_after_correction_sees_only_corrected_value(self):
        latest = latest_as_of(self.conn, "bhavcopy", "2021-12-31")
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["close_price"], 104.5)

    def test_duplicate_exact_vintage_is_rejected_not_silently_ignored(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(close_price=999.0, knowledge_date="2021-06-02"))

class StoreValidationTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_missing_required_field_rejected(self):
        row = make_bhavcopy_row()
        del row["close_price"]
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", row)

    def test_unrecognized_field_rejected(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(made_up_field=1))

    def test_caller_cannot_set_store_owned_fields(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(recorded_at="2021-01-01T00:00:00Z"))

    def test_invalid_event_date_rejected(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(event_date="not-a-date"))

    def test_successful_write_returns_row_id(self):
        row_id = write_fact(self.conn, "bhavcopy", make_bhavcopy_row())
        self.assertIsInstance(row_id, int)
        self.assertGreater(row_id, 0)

class StoreShapeValidationTest(unittest.TestCase):
    """P2-001 mitigation: the store independently rejects a malformed row/batch regardless of
    what any ingestion module did or didn't check upstream."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_wrong_type_numeric_field_rejected(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(close_price="104.0"))

    def test_bool_rejected_for_numeric_field_even_though_bool_is_an_int_subclass(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(traded_qty=True))

    def test_null_rejected_for_non_nullable_field(self):
        with self.assertRaises(StoreValidationError):
            write_fact(self.conn, "bhavcopy", make_bhavcopy_row(close_price=None))

    def test_null_accepted_for_declared_nullable_field(self):
        row_id = write_fact(self.conn, "bhavcopy", make_bhavcopy_row(delivery_qty=None, delivery_pct=None))
        self.assertGreater(row_id, 0)

    def test_bulk_write_rejects_empty_batch(self):
        with self.assertRaises(StoreValidationError):
            write_facts(self.conn, "bhavcopy", [])

    def test_bulk_write_rejects_whole_batch_on_one_malformed_row(self):
        rows = [make_bhavcopy_row(symbol="A"), make_bhavcopy_row(symbol="B", close_price="not-a-number")]
        with self.assertRaises(StoreValidationError):
            write_facts(self.conn, "bhavcopy", rows)
        # fail-closed: neither row was written, not just the malformed one skipped
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2021-12-31")), 0)

    def test_bulk_write_reports_inserted_count(self):
        rows = [make_bhavcopy_row(symbol="A"), make_bhavcopy_row(symbol="B")]
        result = write_facts(self.conn, "bhavcopy", rows)
        self.assertEqual(result.inserted, 2)
        self.assertEqual(result.skipped_duplicate, 0)

    def test_bulk_write_is_idempotent_reingestion_skips_duplicates_not_error(self):
        rows = [make_bhavcopy_row(symbol="A"), make_bhavcopy_row(symbol="B")]
        write_facts(self.conn, "bhavcopy", rows)
        second = write_facts(self.conn, "bhavcopy", rows)  # re-ingesting the identical file
        self.assertEqual(second.inserted, 0)
        self.assertEqual(second.skipped_duplicate, 2)
        self.assertEqual(len(read_as_of(self.conn, "bhavcopy", "2021-12-31")), 2)  # no new rows

class NumericCoercionTest(unittest.TestCase):
    """P2-002: numpy scalar types (what pandas-sourced ingestion actually hands the store) must
    be coerced to native int/float before reaching sqlite3, or they silently land as BLOBs."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_numpy_int_and_float_stored_as_real_sqlite_types_not_blob(self):
        import numpy as np
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row(
            traded_qty=np.int64(10000), close_price=np.float64(104.0),
            delivery_qty=np.int64(4000), delivery_pct=np.float64(40.0)))
        row = self.conn.execute(
            "SELECT typeof(traded_qty), traded_qty, typeof(close_price), close_price FROM bhavcopy"
        ).fetchone()
        self.assertEqual(row[0], "integer")
        self.assertEqual(row[1], 10000)
        self.assertEqual(row[2], "real")
        self.assertEqual(row[3], 104.0)

    def test_bulk_write_also_coerces_numpy_types(self):
        import numpy as np
        write_facts(self.conn, "bhavcopy", [make_bhavcopy_row(traded_qty=np.int64(555))])
        row = self.conn.execute("SELECT typeof(traded_qty), traded_qty FROM bhavcopy").fetchone()
        self.assertEqual(row[0], "integer")
        self.assertEqual(row[1], 555)

class DelistedSymbolStaysQueryableTest(unittest.TestCase):
    """Section 10, at the guard level: a symbol with no data after some date must still be fully
    queryable for the period it *did* trade -- the guard must not implicitly restrict to symbols
    with 'current' data. No 'is this symbol still listed' concept exists anywhere in this module,
    which is the point."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        # DELISTEDCO trades only through 2021-06-30, then nothing -- as if delisted.
        write_fact(self.conn, "bhavcopy", make_bhavcopy_row(
            symbol="DELISTEDCO", event_date="2021-06-30", knowledge_date="2021-07-01"))

    def test_historical_rows_visible_years_after_last_trade(self):
        rows = latest_as_of(self.conn, "bhavcopy", "2026-09-08", symbol="DELISTEDCO")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_date"], "2021-06-30")

class CorporateActionKnowledgeDateOrderingTest(unittest.TestCase):
    """Section 11: an ex_date (event_date) can precede the action's own public announcement
    (knowledge_date) -- e.g. a retroactively-announced/late-filed action. The guard must block on
    knowledge_date regardless of how event_date compares to as_of; otherwise an as-of query run
    "on" the ex_date would see an adjustment factor nobody could have known about yet."""

    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        write_fact(self.conn, "corporate_actions", {
            "symbol": "FIXTURECO", "action_type": "BONUS", "event_date": "2021-01-10",
            "knowledge_date": "2021-01-15", "ratio_numerator": 1.0, "ratio_denominator": 1.0,
            "confidence_tier": "CONFIRMED", "details": "1:1 bonus (fixture)", "source_file": "fixture_corp_actions.csv",
        })

    def test_invisible_between_ex_date_and_announcement(self):
        rows = read_as_of(self.conn, "corporate_actions", "2021-01-12", symbol="FIXTURECO")
        self.assertEqual(len(rows), 0, "Action must not be visible before its own knowledge_date, even though event_date has passed.")

    def test_visible_on_or_after_announcement(self):
        rows = read_as_of(self.conn, "corporate_actions", "2021-01-15", symbol="FIXTURECO")
        self.assertEqual(len(rows), 1)

if __name__ == "__main__":
    unittest.main()
