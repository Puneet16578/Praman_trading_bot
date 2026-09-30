"""Recovery proof, read-only WAL snapshots, corruption detection, cadence and retention."""
import json
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from desk import backups
from shared.market_time import IST
from shared.sqlite_readonly import open_readonly


class BackupTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.sqlite"
        self.conn = sqlite3.connect(self.source)
        self.addCleanup(self.conn.close)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA wal_autocheckpoint=0")
        self.conn.execute("CREATE TABLE journal_events (id INTEGER PRIMARY KEY, detail TEXT)")
        self.conn.executemany("INSERT INTO journal_events VALUES (?, ?)", [(1, "first"), (2, "second")])
        self.conn.commit()
        self.now = datetime(2026, 9, 28, 18, 0, tzinfo=IST)
        self.local = self.root / "local"
        self.cloud = self.root / "cloud"
        self.config_path = self.root / "config.json"
        self.event_path = self.root / "events.jsonl"
        self.config = {
            "local": {"folder": str(self.local), "desk_keep": 14, "praman_keep": 8},
            "cloud": {"enabled": False, "folder": str(self.cloud), "desk_keep": 14,
                      "praman_keep": 2, "encrypted": False},
        }
        self.write_config()

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def run_backup(self, now=None):
        return backups.run_backups(self.config_path, sources={"desk": self.source, "praman": self.source},
                                   event_path=self.event_path, now=now or self.now)

    def test_online_readonly_snapshot_includes_committed_wal_and_restores(self):
        connections = []
        def readonly(path):
            conn = open_readonly(path)
            with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                conn.execute("INSERT INTO journal_events VALUES (3, 'forbidden')")
            connections.append(conn)
            return conn
        self.assertTrue(Path(str(self.source) + "-wal").exists())
        with patch("shared.sqlite_backup.open_readonly", side_effect=readonly):
            path = backups.create_backup(self.source, self.local, "desk", self.now)
        self.assertEqual(len(connections), 1)
        proof = backups.verify_archive(path)
        self.assertEqual(proof["row_counts"]["journal_events"],
                         self.conn.execute("SELECT COUNT(*) FROM journal_events").fetchone()[0])
        self.assertEqual(proof["journal_hashes"], backups.database_facts(self.source, True)["journal_hashes"])
        self.assertEqual(proof["integrity_check"], "ok")

    def rewrite_archive(self, path, *, change_database=False, change_count=False):
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            database = archive.read("desk.sqlite")
        if change_database:
            tampered = self.root / "tampered.sqlite"
            tampered.write_bytes(database)
            conn = sqlite3.connect(tampered)
            try:
                conn.execute("UPDATE journal_events SET detail='different' WHERE id=1")
                conn.commit()
            finally:
                conn.close()
            database = tampered.read_bytes()
            # Even if a whole-file hash matches, the recorded journal hash must catch this.
            manifest["database_sha256"] = backups._sha256(tampered)
        if change_count:
            manifest["row_counts"]["journal_events"] += 1
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr("desk.sqlite", database)

    def test_restore_rejects_journal_change_with_identical_row_count(self):
        path = backups.create_backup(self.source, self.local, "desk", self.now)
        self.rewrite_archive(path, change_database=True)
        with self.assertRaisesRegex(ValueError, "journal content hashes"):
            backups.verify_archive(path)

    def test_restore_rejects_row_count_mismatch(self):
        path = backups.create_backup(self.source, self.local, "desk", self.now)
        self.rewrite_archive(path, change_count=True)
        with self.assertRaisesRegex(ValueError, "row counts"):
            backups.verify_archive(path)

    def test_verify_latest_records_proof_and_status_without_cloud_access(self):
        self.run_backup()
        proofs = backups.verify_latest(self.config_path, event_path=self.event_path)
        self.assertEqual({proof["kind"] for proof in proofs}, {"desk", "praman"})
        self.assertFalse(self.cloud.exists())
        line = backups.status_line(self.event_path)
        self.assertIn("last backup 2026-09-28", line)
        self.assertIn("last successful restore check", line)

    def test_daily_and_weekly_cadence(self):
        self.assertEqual([r["event"] for r in self.run_backup()], ["backup", "backup"])
        self.assertEqual([r["event"] for r in self.run_backup()], ["already_backed_up"] * 2)
        next_day = self.run_backup(self.now + timedelta(days=1))
        self.assertEqual([r["event"] for r in next_day], ["backup", "already_backed_up"])
        next_week = self.run_backup(self.now + timedelta(days=7))
        self.assertEqual([r["event"] for r in next_week], ["backup", "backup"])

    def test_retention_keeps_14_daily_and_8_local_2_cloud_weekly(self):
        self.config["cloud"]["enabled"] = True
        self.write_config()
        for day in range(15):
            self.run_backup(self.now + timedelta(days=day))
        self.assertEqual(len(backups.archives(self.local, "desk")), 14)
        self.assertEqual(len(backups.archives(self.cloud, "desk")), 14)
        for week in range(3, 10):
            self.run_backup(self.now + timedelta(weeks=week))
        self.assertEqual(len(backups.archives(self.local, "praman")), 8)
        self.assertEqual(len(backups.archives(self.cloud, "praman")), 2)
        self.assertEqual(len(backups.archives(self.local, "desk")), 14)
        self.assertEqual(len(backups.archives(self.cloud, "desk")), 14)

    def test_failed_snapshot_does_not_prune_or_record_success(self):
        self.run_backup()
        before = self.event_path.read_bytes()
        files = set(self.local.iterdir())
        with patch("desk.backups.online_backup", side_effect=OSError("test failure")):
            with self.assertRaises(OSError):
                self.run_backup(self.now + timedelta(days=1))
        self.assertEqual(set(self.local.iterdir()), files)
        self.assertEqual(self.event_path.read_bytes(), before)

    def test_archive_publication_is_atomic_on_compression_failure(self):
        with patch("zipfile.ZipFile.write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                backups.create_backup(self.source, self.local, "desk", self.now)
        self.assertEqual(list(self.local.iterdir()), [])

    def test_repository_destination_is_rejected(self):
        self.config["local"]["folder"] = str(backups.ROOT / "data" / "backups")
        self.write_config()
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            backups.load_config(self.config_path)

    def test_missing_backup_cannot_record_success(self):
        with self.assertRaises(FileNotFoundError):
            backups.verify_latest(self.config_path, event_path=self.event_path)
        self.assertFalse(self.event_path.exists())


if __name__ == "__main__":
    unittest.main()
