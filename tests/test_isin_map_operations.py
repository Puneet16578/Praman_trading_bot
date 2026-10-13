"""Operational refresh failure, provenance, trading-day freshness, and migration."""
import contextlib
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from requests import HTTPError, Response
from scripts import build_isin_map, weekly_ingest
from shared.isin_map_metadata import (
    IST, bootstrap_metadata, companion_path, read_metadata, trading_days_since_build,
)
from desk.gates.checks import g1_data_quality
from desk.lib.schema import DECISIONS, init_desk_db, migrate_decisions_isin_map
from desk.ingestion_health import ingestion_health_line, isin_map_health_line


class IsinRefreshTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "map.json"
        self.path.write_text('{"OLD":"INE000000001"}', encoding="utf-8")
        self.output = patch.object(build_isin_map, "OUTPUT_PATH", self.path)
        self.output.start()
        self.addCleanup(self.output.stop)
        self.today = date(2026, 9, 28)
        clock = patch.object(build_isin_map, "market_today", return_value=self.today)
        clock.start()
        self.addCleanup(clock.stop)

    def http_error(self, status):
        response = Response()
        response.status_code = status
        return HTTPError(response=response)

    def test_today_404_warns_and_preserves_map_and_companion(self):
        bootstrap_metadata(self.path)
        before = self.path.read_bytes(), companion_path(self.path).read_bytes()
        with patch.object(build_isin_map, "fetch_isin_snapshot", side_effect=self.http_error(404)):
            result = weekly_ingest._run_capturing("isin_map", build_isin_map.main)
        self.assertEqual(result["status"], "WARN")
        self.assertIn("HTTP 404", result["output"])
        self.assertEqual(before, (self.path.read_bytes(), companion_path(self.path).read_bytes()))

    def test_other_http_error_remains_error(self):
        with patch.object(build_isin_map, "fetch_isin_snapshot", side_effect=self.http_error(503)):
            self.assertEqual(weekly_ingest._run_capturing("isin_map", build_isin_map.main)["status"], "ERROR")

    def test_partial_refresh_retains_old_identity_and_today_wins_conflict(self):
        self.path.write_text(json.dumps({'DELISTED':'INE000000001','REUSED':'INE000000002'}),encoding='utf-8')
        with patch.object(build_isin_map,'SNAPSHOT_DATES',[date(2020,1,2),date(2022,6,15)]), patch.object(
            build_isin_map,'fetch_isin_snapshot',side_effect=[
                {'REUSED':'INE000000003'}, {'REUSED':'INE000000002'},self.http_error(404)]):
            build_isin_map.main()
        self.assertEqual(json.loads(self.path.read_text()),{'DELISTED':'INE000000001','REUSED':'INE000000003'})

    def test_404_without_existing_map_is_error(self):
        self.path.unlink()
        with patch.object(build_isin_map, "fetch_isin_snapshot", side_effect=self.http_error(404)):
            self.assertEqual(weekly_ingest._run_capturing("isin_map", build_isin_map.main)["status"], "ERROR")

    def test_success_records_checksum_offset_and_only_used_dates(self):
        old, missing = date(2020, 1, 2), date(2021, 1, 4)
        with (
            patch.object(build_isin_map, "SNAPSHOT_DATES", [old, missing]),
            patch.object(build_isin_map, "fetch_isin_snapshot", side_effect=[
                {"NEW": "INE000000002"}, {"OLD": "INE000000001"}, self.http_error(404),
            ]),
        ):
            result = weekly_ingest._run_capturing("isin_map", build_isin_map.main)
        self.assertEqual(result["status"], "WARN")
        metadata = read_metadata(self.path)
        self.assertIsNotNone(datetime.fromisoformat(metadata["built_at"]).utcoffset())
        self.assertEqual(metadata["map_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(metadata["snapshot_dates"], [self.today.isoformat(), old.isoformat()])
        self.assertEqual(json.loads(self.path.read_text()), {"NEW": "INE000000002", "OLD": "INE000000001"})

    def test_bootstrap_uses_mtime_once_and_labels_unknown_snapshot_dates(self):
        stamp = datetime(2026, 9, 23, 17, 35, tzinfo=IST).timestamp()
        os.utime(self.path, (stamp, stamp))
        metadata = bootstrap_metadata(self.path)
        self.assertEqual(datetime.fromisoformat(metadata["built_at"]).timestamp(), stamp)
        self.assertEqual(metadata["build_time_source"], "file_mtime")
        self.assertEqual(metadata["snapshot_dates_source"], "not_recorded")
        before = companion_path(self.path).read_bytes()
        bootstrap_metadata(self.path)
        self.assertEqual(before, companion_path(self.path).read_bytes())

    def test_checksum_mismatch_is_rejected(self):
        bootstrap_metadata(self.path)
        self.path.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_metadata(self.path)

    def test_summary_health_levels_and_warn_exit_status(self):
        log = Path(self.tmp.name) / "ingest.log"
        def warn():
            print("WARN snapshot skipped")
        def fail():
            raise ValueError("fixture failure")
        for steps, status, exit_code in [([], "OK", 0), ([("isin_map", warn)], "WARN", 0),
                                         ([("isin_map", warn), ("other", fail)], "ERROR", 1)]:
            with self.subTest(status=status), patch.object(weekly_ingest, "LOG_PATH", log), \
                    patch.object(weekly_ingest, "STEPS", steps), \
                    patch.object(weekly_ingest, "power_status", return_value=(False, None)), \
                    patch.object(weekly_ingest, "head_branch", return_value="master"), \
                    patch.object(weekly_ingest, "uncommitted_nightly_inputs", return_value=[]), \
                    contextlib.redirect_stdout(io.StringIO()):   # P8-055: never the machine's real battery
                self.assertEqual(weekly_ingest.main(), exit_code)
            with patch("desk.ingestion_health.LOG_PATH", log):
                self.assertIn(f"overall={status}", ingestion_health_line())
        self.assertIn("WARN snapshot skipped", log.read_text())


class HistoricalSnapshotCacheTest(unittest.TestCase):
    """P8-060: fixed historical snapshots are downloaded once into a checksummed cache."""

    DATES = [date(2020, 1, 2), date(2022, 6, 15)]

    def setUp(self):
        from src.ingestion.nse_market_data import isin_mapping
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.cache, self.path, self.today = root / "cache", root / "map.json", date(2026, 9, 28)
        self.downloads, self.fail, self.html = [], {}, set()
        real_fetch = isin_mapping.fetch_isin_snapshot

        def fetch(d, bhavcopy_save=None):        # today's (no cache) and the cached path both reach the fake
            return real_fetch(d, bhavcopy_save or self.download)
        for name, new in dict(OUTPUT_PATH=self.path, CACHE_DIR=self.cache, SNAPSHOT_DATES=self.DATES,
                              download_bhavcopy=self.download, market_today=lambda: self.today,
                              fetch_isin_snapshot=fetch).items():
            patcher = patch.object(build_isin_map, name, new)
            patcher.start()
            self.addCleanup(patcher.stop)

    def download(self, d, folder):
        self.downloads.append(d)
        if d in self.fail:
            raise self.fail[d]
        out = Path(folder) / d.strftime("cm%d%b%Ybhav.csv")
        out.write_text("<html>busy</html>" if d in self.html else f"SYMBOL,SERIES,ISIN\nS{d:%Y},EQ,INE{d:%Y}00001\n",
                       encoding="utf-8")
        return str(out)

    def run_main(self):
        self.downloads.clear()
        return weekly_ingest._run_capturing("isin_map", build_isin_map.main)

    def cached(self, d):
        return self.cache / f"cm_{d.isoformat()}.csv"

    def test_downloaded_once_then_read_from_the_cache_with_the_same_map(self):
        first = self.run_main()
        self.assertEqual((first["status"], self.downloads), ("OK", [self.today, *self.DATES]))
        built = self.path.read_bytes()
        for d in self.DATES:
            record = json.loads(self.cached(d).with_name(self.cached(d).name + ".sha256.json").read_text())
            self.assertEqual(record["sha256"], hashlib.sha256(self.cached(d).read_bytes()).hexdigest())
        self.assertFalse(self.cached(self.today).exists())               # today's is never cached
        second = self.run_main()
        self.assertEqual((second["status"], self.downloads), ("OK", [self.today]))
        self.assertEqual(second["output"].count("cached snapshot, hash verified"), 2)
        self.assertEqual(self.path.read_bytes(), built)
        self.assertEqual(json.loads(built), {"S2020": "INE202000001", "S2022": "INE202200001", "S2026": "INE202600001"})

    def test_a_damaged_or_missing_cached_file_is_downloaded_again(self):
        self.run_main()
        sidecar = lambda d: self.cached(d).with_name(self.cached(d).name + ".sha256.json")
        for damage, words in ((lambda d: self.cached(d).write_text("SYMBOL,SERIES,ISIN\nX,EQ,BAD\n"), "its hash does not match"),
                              (lambda d: self.cached(d).unlink(), "its file is missing"),
                              (lambda d: sidecar(d).unlink(), "its hash record is missing or unreadable"),
                              (lambda d: sidecar(d).write_text("not json"), "its hash record is missing or unreadable")):
            with self.subTest(words=words):
                damage(self.DATES[0])
                result = self.run_main()
                self.assertEqual((result["status"], self.downloads), ("WARN", [self.today, self.DATES[0]]))
                self.assertIn(f"WARN {self.DATES[0].isoformat()}: cached snapshot rejected ({words})", result["output"])
                self.assertIn("S2020", json.loads(self.path.read_text()))
                again = self.run_main()                                   # repaired: read from the cache again
                self.assertEqual((again["status"], self.downloads), ("OK", [self.today]))

    def test_failures_name_the_http_status_and_an_unusable_download_is_not_cached(self):
        response = Response()
        response.status_code = 503
        self.fail = {self.DATES[0]: HTTPError("503 Server Error", response=response)}
        self.html = {self.DATES[1]}
        result = self.run_main()
        self.assertEqual(result["status"], "WARN")
        self.assertIn(f"WARN {self.DATES[0].isoformat()}: snapshot failed (HTTPError, HTTP 503", result["output"])
        self.assertIn(f"WARN {self.DATES[1].isoformat()}: snapshot failed (ValueError", result["output"])
        self.assertFalse(any(self.cached(d).exists() for d in self.DATES))
        self.fail, self.html = {}, set()
        self.assertEqual(self.run_main()["status"], "OK")              # the next run fetches and caches both
        self.assertTrue(all(self.cached(d).exists() for d in self.DATES))


class IsinAgeTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        self.conn.execute("CREATE TABLE bhavcopy (symbol TEXT, event_date TEXT, knowledge_date TEXT)")
        dates = ["2026-09-18", "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25", "2026-09-28"]
        self.conn.executemany("INSERT INTO bhavcopy VALUES ('X', ?, ?)", [(d, d) for d in dates] * 2)
        self.built = "2026-09-18T18:00:00+05:30"

    def test_five_trading_days_pass_six_fail_duplicates_and_weekend_do_not_count(self):
        self.assertEqual(trading_days_since_build(self.conn, self.built, "2026-09-25"), 5)
        self.assertEqual(g1_data_quality(self.conn, "X", "2026-09-25", isin_map_built_at=self.built).result, "PASS")
        result = g1_data_quality(self.conn, "X", "2026-09-28", isin_map_built_at=self.built)
        self.assertEqual(result.result, "FAIL")
        self.assertIn("6 trading days", result.reasons[0])

    def test_same_day_build_has_zero_age(self):
        self.assertEqual(trading_days_since_build(self.conn, self.built, "2026-09-18"), 0)

    def test_new_unknown_timestamp_fails_legacy_null_retains_previous_behavior(self):
        self.assertEqual(g1_data_quality(self.conn, "X", "2026-09-28", isin_map_built_at="").result, "FAIL")
        self.assertEqual(g1_data_quality(self.conn, "X", "2026-09-28", isin_map_built_at=None).result, "PASS")

    def test_status_uses_same_trading_day_age(self):
        with patch("shared.isin_map_metadata.read_metadata", return_value={
            "built_at": self.built, "build_time_source": "file_mtime",
        }):
            line = isin_map_health_line(self.conn, "2026-09-28")
        self.assertIn("ERROR", line)
        self.assertIn("age=6 trading days", line)
        self.assertIn("inferred from file timestamp", line)


class DecisionMigrationTest(unittest.TestCase):
    def test_existing_rows_survive_explicit_alter_and_repeated_migration(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        self.addCleanup(conn.close)
        legacy_ddl = "\n".join(line for line in DECISIONS.ddl.splitlines() if "isin_map_built_at" not in line)
        conn.execute(legacy_ddl)
        columns = list(conn.execute("PRAGMA table_info(decisions)"))
        names = [r["name"] for r in columns if r["notnull"]]
        conn.execute(f"INSERT INTO decisions ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
                     [1 if name == "as_of_is_live" else "legacy" for name in names])
        before = dict(conn.execute("SELECT * FROM decisions").fetchone())
        statements = []
        conn.set_trace_callback(statements.append)
        self.assertEqual(migrate_decisions_isin_map(conn), (1, 1))
        self.assertTrue(any("ALTER TABLE decisions ADD COLUMN" in s for s in statements))
        after = dict(conn.execute("SELECT * FROM decisions").fetchone())
        self.assertIsNone(after.pop("isin_map_built_at"))
        self.assertEqual(before, after)
        self.assertEqual(migrate_decisions_isin_map(conn), (1, 1))
        init_desk_db(conn)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM decisions")
