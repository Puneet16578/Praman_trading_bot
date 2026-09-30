"""Operational backups and restore proof; all database sources are read-only.

These are whole-store recovery snapshots, not as-of research queries. Every Desk
table is journal content for verification, including tables added in later phases.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from shared.market_time import IST
from shared.sqlite_backup import online_backup
from shared.sqlite_readonly import open_readonly

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "backup_stores.json"
EVENT_PATH = ROOT / "logs" / "backups.jsonl"
SOURCES = {"desk": ROOT / "data/desk/desk.sqlite", "praman": ROOT / "data/processed/praman.db"}
ARCHIVE_RE = re.compile(r"^(desk|praman)_\d{8}T\d{12}Z\.zip$")


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config["cloud"]["encrypted"]:
        raise ValueError("Encrypted backups are not configured")
    for destination in destinations(config):
        folder = Path(destination["folder"])
        if not folder.is_absolute() or folder.resolve().is_relative_to(ROOT) or folder.parent == folder:
            raise ValueError("Backup folders must be absolute, outside the repository, and not a drive root")
        if any(type(destination[key]) is not int or destination[key] < 1
               for key in ("desk_keep", "praman_keep")):
            raise ValueError("Backup retention must be a positive integer")
    return config


def destinations(config: dict) -> list[dict]:
    return [config["local"]] + ([config["cloud"]] if config["cloud"]["enabled"] else [])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def database_facts(path: Path, journal: bool) -> dict:
    conn = open_readonly(path)
    try:
        integrity = [row[0] for row in conn.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise ValueError("Restored database failed integrity_check")
        tables = sorted(row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        counts, hashes = {}, {}
        for table in tables:
            quoted = _quoted(table)
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
            if journal:
                columns = [row[1] for row in conn.execute(f"PRAGMA table_info({quoted})")]
                digest = hashlib.sha256(json.dumps(columns, ensure_ascii=False).encode("utf-8"))
                ordering = ", ".join(str(i + 1) for i in range(len(columns)))
                for row in conn.execute(f"SELECT * FROM {quoted} ORDER BY {ordering}"):
                    values = [{"blob_hex": value.hex()} if isinstance(value, bytes) else value for value in row]
                    digest.update(b"\n" + json.dumps(values, ensure_ascii=False, separators=(",", ":"),
                                                   allow_nan=False).encode("utf-8"))
                hashes[table] = digest.hexdigest()
        return {"row_counts": counts, "journal_hashes": hashes}
    finally:
        conn.close()


def _record(event: dict, event_path: Path) -> None:
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def archives(folder: Path, kind: str) -> list[Path]:
    return sorted(path for path in folder.glob(f"{kind}_*.zip")
                  if ARCHIVE_RE.fullmatch(path.name) and path.is_file() and not path.is_symlink())


def _manifest(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        if archive.getinfo("manifest.json").file_size > 2 * 1024 * 1024:
            raise ValueError("Oversized backup manifest")
        manifest = json.loads(archive.read("manifest.json"))
    if manifest["version"] != 1 or manifest["kind"] not in SOURCES:
        raise ValueError("Unsupported backup manifest")
    return manifest


def create_backup(source: Path, folder: Path, kind: str, now: datetime) -> Path:
    if kind not in SOURCES or now.utcoffset() is None:
        raise ValueError("Backup requires a known store and an aware timestamp")
    folder.mkdir(parents=True, exist_ok=True)
    timestamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = folder / f"{kind}_{timestamp}.zip"
    if target.exists():
        raise FileExistsError("Backup archive already exists")
    with tempfile.TemporaryDirectory(prefix="praman_backup_") as temporary:
        snapshot = Path(temporary) / f"{kind}.sqlite"
        online_backup(source, snapshot)
        manifest = {"version": 1, "kind": kind, "created_at": now.isoformat(),
                    "market_date": now.astimezone(IST).date().isoformat(),
                    "database_sha256": _sha256(snapshot), **database_facts(snapshot, kind == "desk")}
        partial = target.with_suffix(".zip.partial")
        try:
            with partial.open("xb") as output:
                with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                    archive.write(snapshot, f"{kind}.sqlite")
                    archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
                output.flush()
                os.fsync(output.fileno())
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    return target


def verify_archive(path: Path) -> dict:
    manifest = _manifest(path)
    kind = manifest["kind"]
    with tempfile.TemporaryDirectory(prefix="praman_restore_") as temporary:
        restored = Path(temporary) / f"{kind}.sqlite"
        with zipfile.ZipFile(path) as archive, archive.open(f"{kind}.sqlite") as source, restored.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        actual = database_facts(restored, kind == "desk")
        if actual["row_counts"] != manifest["row_counts"]:
            raise ValueError("Restore row counts differ from backup manifest")
        if actual["journal_hashes"] != manifest["journal_hashes"]:
            raise ValueError("Restore journal content hashes differ from backup manifest")
        if _sha256(restored) != manifest["database_sha256"]:
            raise ValueError("Restored database hash differs from backup manifest")
    return {"kind": kind, "archive": str(path), "integrity_check": "ok", **actual}


def _prune(folder: Path, kind: str, keep: int) -> None:
    root = folder.resolve()
    for path in archives(folder, kind)[:-keep]:
        if path.resolve().parent != root:
            raise ValueError("Retention target escaped backup folder")
        path.unlink()


def run_backups(config_path: Path = CONFIG_PATH, *, sources: dict | None = None,
                event_path: Path = EVENT_PATH, now: datetime | None = None) -> list[dict]:
    config = load_config(config_path)
    sources = SOURCES if sources is None else sources
    now = now or datetime.now(IST)
    today = now.astimezone(IST).date()
    reports = []
    for kind in ("desk", "praman"):
        local = Path(config["local"]["folder"])
        existing = archives(local, kind)
        previous = _manifest(existing[-1]) if existing else None
        last_date = datetime.fromisoformat(previous["created_at"]).astimezone(IST).date() if previous else None
        due = last_date is None or (last_date != today if kind == "desk"
                                   else last_date.isocalendar()[:2] != today.isocalendar()[:2])
        if due:
            path = create_backup(sources[kind], local, kind, now)
            proof = verify_archive(path)
            report = {"event": "backup", "at": now.isoformat(), "kind": kind,
                      "archive": str(path), "compressed_bytes": path.stat().st_size}
            _record(report, event_path)
            _record({"event": "restore_ok", "at": datetime.now(IST).isoformat(), **proof}, event_path)
            reports.append(report)
        elif existing:
            path = existing[-1]
            proof = verify_archive(path)
            _record({"event": "restore_ok", "at": datetime.now(IST).isoformat(), **proof}, event_path)
            reports.append({"event": "already_backed_up", "kind": kind, "archive": str(path),
                            "compressed_bytes": path.stat().st_size})
        for destination in destinations(config):
            folder = Path(destination["folder"])
            folder.mkdir(parents=True, exist_ok=True)
            if folder.resolve() != local.resolve():
                copied = folder / path.name
                if not copied.exists():
                    partial = copied.with_suffix(".zip.partial")
                    try:
                        with path.open("rb") as source, partial.open("xb") as target:
                            shutil.copyfileobj(source, target, length=1024 * 1024)
                            target.flush()
                            os.fsync(target.fileno())
                        partial.replace(copied)
                    finally:
                        partial.unlink(missing_ok=True)
                proof = verify_archive(copied)
                _record({"event": "restore_ok", "at": datetime.now(IST).isoformat(), **proof}, event_path)
            _prune(folder, kind, destination[f"{kind}_keep"])
    return reports


def verify_latest(config_path: Path = CONFIG_PATH, *, event_path: Path = EVENT_PATH) -> list[dict]:
    reports = []
    for destination in destinations(load_config(config_path)):
        for kind in ("desk", "praman"):
            available = archives(Path(destination["folder"]), kind)
            if not available:
                raise FileNotFoundError(f"No {kind} backup found")
            report = verify_archive(available[-1])
            _record({"event": "restore_ok", "at": datetime.now(IST).isoformat(), **report}, event_path)
            reports.append(report)
    return reports


def status_line(event_path: Path = EVENT_PATH) -> str:
    if not event_path.exists():
        return "Backups: none recorded; successful restore check: none."
    try:
        events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
        lines = []
        for kind in ("desk", "praman"):
            backup = next((e for e in reversed(events) if e["event"] == "backup" and e["kind"] == kind), None)
            restore = next((e for e in reversed(events) if e["event"] == "restore_ok" and e["kind"] == kind), None)
            lines.append(f"{kind}: last backup {backup['at'] if backup else 'none'}, "
                         f"last successful restore check {restore['at'] if restore else 'none'}")
        return "Backups: " + "; ".join(lines)
    except (OSError, ValueError, KeyError):
        return "Backups: UNKNOWN (backup log unavailable or invalid)."
