"""Recovery proof, read-only WAL snapshots, corruption detection, cadence and retention."""
import json
import shutil
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
        self.logs = self.root / "logs"                       # a stand-in logs/ folder
        (self.logs / "_quarantine").mkdir(parents=True)
        (self.logs / "weekly_ingest.log").write_bytes(b"=== run 1 ===\n")
        (self.logs / "brief_2026-09-28.txt").write_bytes(b"PRAMAN - DAILY DECISION DESK\n")
        (self.logs / "_quarantine" / "NOTE.txt").write_bytes(b"note\n")
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
        return backups.run_backups(self.config_path, sources={"desk": self.source, "praman": self.source,
                                                              "logs": self.logs},
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
        self.assertEqual({proof["kind"] for proof in proofs}, {"desk", "praman", "logs"})
        self.assertFalse(self.cloud.exists())
        line = backups.status_line(self.event_path)
        self.assertIn("last backup 2026-09-28", line)
        self.assertIn("last successful restore check", line)
        self.assertIn("logs: last backup 2026-09-28", line)

    def test_daily_and_weekly_cadence(self):
        events = lambda reports: [(r["kind"], r["event"]) for r in reports]
        self.assertEqual(events(self.run_backup()), [("desk", "backup"), ("praman", "backup"), ("logs", "backup")])
        self.assertEqual(events(self.run_backup()), [("desk", "already_backed_up"), ("praman", "already_backed_up"),
                                                     ("logs", "already_backed_up")])
        next_day = self.run_backup(self.now + timedelta(days=1))
        self.assertEqual(events(next_day), [("desk", "backup"), ("praman", "already_backed_up"), ("logs", "backup")])
        next_week = self.run_backup(self.now + timedelta(days=7))
        self.assertEqual(events(next_week), [("desk", "backup"), ("praman", "backup"), ("logs", "backup")])

    def test_retention_keeps_14_daily_and_8_local_2_cloud_weekly(self):
        self.config["cloud"]["enabled"] = True
        self.write_config()
        for day in range(15):
            self.run_backup(self.now + timedelta(days=day))
        self.assertEqual(len(backups.archives(self.local, "desk")), 14)
        self.assertEqual(len(backups.archives(self.cloud, "desk")), 14)
        self.assertEqual(len(backups.archives(self.local, "logs")), 14)    # the desk backups' retention
        self.assertEqual(len(backups.archives(self.cloud, "logs")), 14)
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

    def test_logs_backup_restores_the_snapshot_not_the_live_folder(self):
        path = backups.create_logs_backup(self.logs, self.local, self.now)
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(archive.getinfo("logs/weekly_ingest.log").compress_type, zipfile.ZIP_DEFLATED)
        self.assertEqual(sorted(manifest["files"]), ["_quarantine/NOTE.txt", "brief_2026-09-28.txt", "weekly_ingest.log"])
        # The live folder keeps growing after the snapshot; the restore check never looks at it.
        with (self.logs / "weekly_ingest.log").open("ab") as stream:
            stream.write(b"=== run 2 ===\n")
        (self.logs / "brief_2026-09-29.txt").write_bytes(b"later\n")
        proof = backups.verify_archive(path)
        self.assertEqual((proof["kind"], proof["integrity_check"], proof["file_count"]), ("logs", "ok", 3))
        self.assertEqual(manifest["files"]["weekly_ingest.log"]["size"], len(b"=== run 1 ===\n"))
        shutil.rmtree(self.logs)                         # even with the live folder gone
        self.assertEqual(backups.verify_archive(path)["integrity_check"], "ok")

    def test_logs_manifest_describes_the_copies_while_the_live_log_grows(self):
        real_copy = shutil.copy2
        def copy_then_grow(source, target):
            result = real_copy(source, target)
            if Path(source).name == "weekly_ingest.log":
                with open(source, "ab") as stream:                     # the nightly appends mid-backup
                    stream.write(b"=== written during the backup ===\n")
            return result
        with patch("desk.backups.shutil.copy2", side_effect=copy_then_grow):
            path = backups.create_logs_backup(self.logs, self.local, self.now)
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            archived = archive.read("logs/weekly_ingest.log")
        self.assertEqual(archived, b"=== run 1 ===\n")
        self.assertEqual(manifest["files"]["weekly_ingest.log"]["size"], len(archived))
        self.assertGreater((self.logs / "weekly_ingest.log").stat().st_size, len(archived))
        self.assertEqual(backups.verify_archive(path)["integrity_check"], "ok")

    def test_logs_restore_rejects_an_archive_that_differs_from_its_manifest(self):
        for minute, change in enumerate(("content", "missing", "extra"), start=1):
            with self.subTest(change=change):
                path = backups.create_logs_backup(self.logs, self.local, self.now + timedelta(minutes=minute))
                with zipfile.ZipFile(path) as archive:
                    manifest = json.loads(archive.read("manifest.json"))
                    members = {n: archive.read(n) for n in archive.namelist() if n != "manifest.json"}
                if change == "content":
                    members["logs/brief_2026-09-28.txt"] = b"PRAMAN - DAILY DECISION DESK, edited\n"
                elif change == "missing":
                    del members["logs/_quarantine/NOTE.txt"]
                else:
                    members["logs/unexpected.txt"] = b"x"
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("manifest.json", json.dumps(manifest))
                    for name, data in members.items():
                        archive.writestr(name, data)
                with self.assertRaisesRegex(ValueError, "differ"):
                    backups.verify_archive(path)

    def test_missing_backup_cannot_record_success(self):
        with self.assertRaises(FileNotFoundError):
            backups.verify_latest(self.config_path, event_path=self.event_path)
        self.assertFalse(self.event_path.exists())


if __name__ == "__main__":
    unittest.main()
