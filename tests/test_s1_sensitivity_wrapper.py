"""Synthetic-only wrapper tests. Production sources and real outcome readers sealed."""
from contextlib import contextmanager
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from research_runs import s1_development_sensitivities as W
from desk.s1.reader import seal_real_reads, RealReader, OutcomeReadRefused
from scripts.abc_followup_counts import BoundedInputs
from tests.test_s1_execution import record, dates, FakeReader, Bar
from desk.lib.costs import load_active_cost_config


class RecordedCutoffTest(unittest.TestCase):
    def connection(self, stamp="2026-10-21T03:05:48.999999+00:00"):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.execute("CREATE TABLE bhavcopy (event_date TEXT, knowledge_date TEXT, recorded_at TEXT, open_price REAL)")
        rows = [("2024-01-01", "2024-01-01", stamp, 101),
                ("2024-01-01", "2024-01-01", "2026-10-21T03:05:49+00:00", 902),
                ("2024-01-01", "2024-01-01", "2026-10-22T00:00:00+00:00", 903),
                ("2025-01-01", "2025-01-01", stamp, 904),
                ("2024-01-01", "2025-01-01", stamp, 905)]
        conn.executemany("INSERT INTO bhavcopy VALUES (?,?,?,?)", rows)
        conn.commit()
        return conn

    def test_views_filter_strict_recording_cutoff_and_both_date_columns(self):
        conn = self.connection()
        wrapped = W.RecordedConnection(conn, ["bhavcopy"])
        self.assertEqual(wrapped.execute("SELECT open_price FROM bhavcopy").fetchall(), [(101,)])
        bounded = BoundedInputs(wrapped, "2024-01-01", "2024-01-01")
        self.assertEqual(bounded.execute("SELECT open_price FROM bhavcopy").fetchall(), [(101,)])
        self.assertEqual(wrapped.execute("SELECT open_price FROM main.bhavcopy").fetchall(), [(101,)])
        for sql in ('SELECT open_price FROM main."bhavcopy"', 'SELECT * FROM sqlite_master'):
            with self.assertRaises(sqlite3.DatabaseError):
                wrapped.execute(sql)
        with self.assertRaises(sqlite3.DatabaseError):
            conn.execute("SELECT open_price FROM main.bhavcopy")
        with self.assertRaises(W.Refused):
            wrapped.execute("DELETE FROM bhavcopy")

    def test_invalid_or_naive_recording_stamp_fails_before_outcomes(self):
        for stamp in (None, "invalid", "2026-10-21T03:00:00"):
            with self.subTest(stamp=stamp), self.assertRaises(W.Refused):
                W.RecordedConnection(self.connection(stamp), ["bhavcopy"])

    def test_timezone_equivalence_and_microseconds(self):
        self.assertTrue(W.before_primary("2026-10-21T08:35:48.999999+05:30"))
        self.assertFalse(W.before_primary("2026-10-21T08:35:49+05:30"))
        self.assertFalse(W.before_primary("2026-10-21T03:05:49.000001Z"))

    def test_schema_missing_fails(self):
        with self.assertRaises(W.Refused):
            W.RecordedConnection(self.connection(), ["corporate_actions"])

    def test_setup_reads_metadata_only(self):
        conn = self.connection()
        def metadata_only(action, table, column, database, source):
            if action == sqlite3.SQLITE_READ and table == "bhavcopy" and column == "open_price":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        conn.set_authorizer(metadata_only)
        W.RecordedConnection(conn, ["bhavcopy"])

    def test_readonly_disk_store_unchanged_by_temporary_views(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.sqlite"
            disk = sqlite3.connect(path)
            try:
                self.connection().backup(disk)
            finally:
                disk.close()
            before = path.read_bytes()
            conn = W.open_readonly(path)
            try:
                guarded = W.RecordedConnection(conn, ["bhavcopy"])
                self.assertEqual(guarded.execute("SELECT open_price FROM bhavcopy").fetchone()[0], 101)
                with self.assertRaises(W.Refused):
                    guarded.execute("UPDATE bhavcopy SET open_price=0")
            finally:
                conn.close()
            self.assertEqual(path.read_bytes(), before)

    def test_frozen_reader_on_synthetic_database_with_late_price_excluded(self):
        from desk.lib.schema import CIRCUIT_BANDS, TICK_SIZES
        conn, desk = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
        self.addCleanup(conn.close); self.addCleanup(desk.close)
        conn.row_factory = desk.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE bhavcopy (row_id INTEGER, symbol TEXT, event_date TEXT, knowledge_date TEXT, recorded_at TEXT, series TEXT, open_price REAL, high_price REAL, low_price REAL, close_price REAL)")
        conn.execute("CREATE TABLE corporate_actions (row_id INTEGER, symbol TEXT, action_type TEXT, event_date TEXT, knowledge_date TEXT, recorded_at TEXT, ratio_numerator REAL, ratio_denominator REAL)")
        conn.execute("CREATE TABLE corporate_announcements (symbol TEXT, event_date TEXT, knowledge_date TEXT, recorded_at TEXT, category TEXT, description TEXT, sort_timestamp TEXT)")
        desk.execute(CIRCUIT_BANDS.ddl); desk.execute(TICK_SIZES.ddl)
        for i, day in enumerate(("2024-01-01", "2024-01-02")):
            conn.execute("INSERT INTO bhavcopy VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (i, "A", day, day, "2026-10-20T00:00:00+00:00", "EQ", 100, 104, 99, 102))
        conn.execute("INSERT INTO bhavcopy VALUES (3,'A','2024-01-02','2024-01-02','2026-10-22T00:00:00+00:00','EQ',999,999,999,999)")
        conn.commit(); desk.commit()
        guarded = W.RecordedConnection(conn, W.SOURCES["data/processed/praman.db"])
        desk_guarded = W.RecordedConnection(desk, W.SOURCES["data/desk/desk.sqlite"])
        reader = RealReader(guarded, desk_guarded, W.DEV_END, authorized=True,
                            snapshots=[("2023-12-31", {"A": "INE000000000"})])
        # Only temporary synthetic databases are connected to this reader.
        self.assertEqual(reader.bar("2024-01-01", "A", "2024-01-02").opening, 100)
        self.assertEqual(reader.benchmark_open("2024-01-01", "A", "2024-01-02", "2024-01-01"), 100)
        self.assertEqual(reader.market_members("2024-01-02"), ["A"])
        reader.index_closes = {s: {d: {"close": 100.} for d in ("2024-01-01", "2024-01-02")}
                              for s in W.T.SERIES}
        self.assertEqual(set(reader.market_states("2024-01-02", "A")), {"V1", "V2", "V3"})
        with self.assertRaises(OutcomeReadRefused):
            reader.bar("2024-01-01", "A", "2025-01-01")


class WrapperTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        self.preflight = patch.object(W, "load_inputs", return_value=({}, {}, {}, [], {})).start()
        @contextmanager
        def sources(_):
            yield Mock(), Mock()
        patch.object(W, "recorded_sources", sources).start()
        self.reader = patch.object(W, "RealReader", return_value=Mock()).start()
        self.evaluate = patch.object(W, "evaluate_variant", return_value={"synthetic_fixture": True}).start()
        self.seal = seal_real_reads()
        self.seal.__enter__()
        self.addCleanup(self.seal.__exit__, None, None, None)

    def args(self, *extra):
        return W.parser().parse_args(["--variants", "cutoff_0900", "lookback_1", *extra])

    def test_check_only_loads_inputs_without_reader_evaluation_or_files(self):
        self.assertEqual(W.run(self.args("--check-only"), self.root), 0)
        self.preflight.assert_called_once()
        self.reader.assert_not_called()
        self.evaluate.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_order_outputs_times_and_no_overwrite(self):
        W.run(self.args(), self.root)
        self.assertEqual([c.args[-1] for c in self.evaluate.call_args_list], ["cutoff_0900", "lookback_1"])
        for variant in ("cutoff_0900", "lookback_1"):
            output, marker = W.paths(self.root, variant)
            value = json.loads(output.read_text())
            self.assertEqual(value["meta"]["variant"], variant)
            self.assertLessEqual(value["meta"]["started_utc"], value["meta"]["ended_utc"])
            self.assertFalse(value["meta"]["rerun_interrupted"])
            self.assertTrue(marker.exists())
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                W.atomic_create(output, {})
            self.assertEqual(before, output.read_bytes())
        with self.assertRaises(W.Refused):
            W.run(self.args("--rerun-interrupted"), self.root)

    def test_failure_stops_batch_and_explicit_rerun_is_recorded(self):
        self.evaluate.side_effect = RuntimeError("untrusted detail")
        with self.assertRaises(RuntimeError):
            W.run(self.args(), self.root)
        output, marker = W.paths(self.root, "cutoff_0900")
        self.assertTrue(marker.exists())
        self.assertFalse(output.exists())
        self.assertFalse(W.paths(self.root, "lookback_1")[1].exists())
        original = marker.read_bytes()
        with self.assertRaises(W.Refused):
            W.run(self.args("--check-only"), self.root)
        self.evaluate.side_effect = None
        # Real preflight supplies this stable provenance field.
        value = json.loads(marker.read_text()); value["input_sha256"] = W.INPUT_SHA
        marker.write_text(json.dumps(value))
        original = marker.read_bytes()
        W.run(self.args("--rerun-interrupted"), self.root)
        self.assertEqual(marker.read_bytes(), original)
        self.assertTrue(json.loads(output.read_text())["meta"]["rerun_interrupted"])
        failure = json.loads(next(marker.parent.glob("*.failure.json")).read_text())
        self.assertEqual(failure["error_type"], "RuntimeError")
        self.assertNotIn("untrusted detail", json.dumps(failure))

    def test_deadline_finishes_current_and_does_not_mark_next(self):
        start = W.now()
        clock = [start]
        def compute(*_):
            clock[0] += timedelta(hours=2)
            return {}
        self.evaluate.side_effect = compute
        with patch.object(W, "now", side_effect=lambda: clock[0]):
            args = self.args(); args.no_start_after = start + timedelta(hours=1)
            W.run(args, self.root)
        self.assertTrue(W.paths(self.root, "cutoff_0900")[0].exists())
        self.assertFalse(W.paths(self.root, "lookback_1")[1].exists())
        self.assertEqual(self.evaluate.call_count, 1)

    def test_live_lock_cannot_be_bypassed_with_rerun_flag(self):
        marker = W.paths(self.root, "cutoff_0900")[1]
        with W.variant_lock(marker), self.assertRaises(W.Refused):
            with W.variant_lock(marker):
                pass

    def test_primary_and_duplicate_variants_refused(self):
        with self.assertRaises(SystemExit):
            W.parser().parse_args(["--variants", "primary"])
        args = self.args(); args.variants = ["lookback_1", "lookback_1"]
        with self.assertRaises(W.Refused):
            W.run(args, self.root)
        self.evaluate.assert_not_called()


class SyntheticIntegrationTest(unittest.TestCase):
    def test_all_eight_use_frozen_evaluation_with_real_reads_sealed(self):
        r = record()
        r["sensitivity_exclusions"] = {v: r["exclusions"] for v in W.VARIANTS[:5]}
        artifact = dict(records=[r], calendars={"s1": dates()}, summary={"tercile_boundaries": [2, 3]})
        reader = FakeReader({d: Bar(100, 104, 99, 102) for d in dates()})
        with seal_real_reads():
            for variant in W.VARIANTS:
                result = W.evaluate_variant(artifact, reader, load_active_cost_config().costs, variant)
                self.assertEqual([t["horizon"] for t in result["tests"]], [1, 3])
                self.assertEqual(result["period"], "development")
            actual = RealReader(Mock(), Mock(), W.DEV_END, authorized=True)
            with self.assertRaises(OutcomeReadRefused):
                actual.bar("2024-01-01", "A", "2024-01-02")


class InputPreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        artifact = dict(records=[], summary={"tercile_boundaries": [2, 3]}, meta=dict(manifest={}, rulebook_sha256="rule",
                        cost_config_sha256="cost", index_source_hashes=[W.PRIMARY_SHA]))
        target = self.root / W.INPUT; target.parent.mkdir(parents=True); target.write_text(json.dumps(artifact))
        self.addCleanup(patch.stopall)
        self.hash = patch.object(W, "sha256", side_effect=lambda p: W.INPUT_SHA if str(p).endswith(W.INPUT.split('/')[-1]) else W.PRIMARY_SHA).start()
        self.git = patch.object(W, "git", side_effect=lambda root, *a: "master" if a[0] == "branch" else "" if a[0] == "diff" else "commit").start()
        patch.object(W.subprocess, "check_output", return_value=b"").start()
        patch.object(W, "load_active_rulebook", return_value=Mock(sha256="rule")).start()
        self.cost = patch.object(W, "load_active_cost_config", return_value=Mock(sha256="cost", costs={})).start()
        self.ledger = patch.object(W.T, "_ledger", return_value=[dict(status=200,
            label="history_2024-01-01_2024-12-31", file="synthetic.json", sha256=W.PRIMARY_SHA)]).start()
        self.indices = patch.object(W.T, "load", return_value=(
            {s: {"2024-01-01": {"source_sha256": W.PRIMARY_SHA, "close": 100.}} for s in W.T.SERIES}, [])).start()
        patch.object(W, "snapshot_identities", return_value=[]).start()

    def test_artifact_hash_is_first_and_stops_before_git_or_readers(self):
        self.hash.side_effect = lambda _: "wrong"
        with self.assertRaises(W.Refused):
            W.load_inputs(self.root)
        self.git.assert_not_called(); self.indices.assert_not_called()

    def test_cost_hash_mismatch_stops_before_index_loading(self):
        self.cost.return_value.sha256 = "wrong"
        with self.assertRaises(W.Refused):
            W.load_inputs(self.root)
        self.indices.assert_not_called()

    def test_frozen_code_mismatch_refused(self):
        self.git.side_effect = lambda root, *a: "master" if a[0] == "branch" else "changed" if a[0] == "diff" else "commit"
        with self.assertRaises(W.Refused):
            W.load_inputs(self.root)
        self.indices.assert_not_called()

    def test_success_returns_fixed_cutoff_and_bounded_input_loader(self):
        out = W.load_inputs(self.root)
        self.indices.assert_called_once_with(self.root / "data/raw/t1_sources", end="2024-12-31")
        self.assertEqual(out[-1]["recorded_before"], "2026-10-21T08:35:49+05:30")
        self.assertEqual(out[-1]["reader_end"], "2024-12-31")

    def test_interrupted_publication_partial_preserved_and_requires_marker(self):
        output, marker = W.paths(self.root, "cutoff_0900")
        partial = output.with_name(output.name + "." + "a" * 32 + ".partial")
        partial.parent.mkdir(parents=True); partial.write_bytes(b'{"incomplete":')
        status = ("?? " + partial.relative_to(self.root).as_posix() + "\0").encode()
        with patch.object(W.subprocess, "check_output", return_value=status):
            with self.assertRaises(W.Refused):
                W.load_inputs(self.root)
            marker.parent.mkdir(parents=True); marker.write_text("{}")
            W.load_inputs(self.root)
        self.assertEqual(partial.read_bytes(), b'{"incomplete":')

    def test_missing_ledger_or_index_series_refused(self):
        original = self.ledger.return_value
        self.ledger.return_value = []
        with self.assertRaises(W.Refused):
            W.load_inputs(self.root)
        self.indices.assert_not_called()
        self.ledger.return_value = original
        self.indices.return_value = ({}, [])
        with self.assertRaises(W.Refused):
            W.load_inputs(self.root)


if __name__ == "__main__":
    unittest.main()
