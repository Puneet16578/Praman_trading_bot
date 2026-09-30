"""Operational snapshot tool (docs/OPERATIONS.md's snapshot rule).

Uses SQLite's online backup API (Connection.backup()), not a raw file copy: this store runs in
WAL mode (src/bitemporal/connection.py), and a plain filesystem copy of just the .db file can miss
committed content still sitting in the -wal file, producing a snapshot that silently omits recent
writes. The backup API copies the database's true logical content page-by-page through SQLite
itself, which is correct regardless of journal mode.

The SOURCE connection is opened mode=ro so this script can never itself write to the live store --
it only ever reads from it and writes to a brand-new destination file.

Usage: python scripts/snapshot_store.py <label>
Output: data/snapshots/<YYYY-MM-DDTHHMMSS>_<label>.sqlite (gitignored), plus its SHA-256 and the
current git HEAD printed for pasting into docs/OPERATIONS.md.
"""
from __future__ import annotations
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import get_settings
from shared.sqlite_backup import online_backup

SNAPSHOT_DIR = Path(__file__).resolve().parents[1] / "data" / "snapshots"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1]).decode().strip()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/snapshot_store.py <label>", file=sys.stderr)
        raise SystemExit(1)
    label = sys.argv[1]

    settings = get_settings()
    source_path = settings.database_path
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = SNAPSHOT_DIR / f"{timestamp}_{label}.sqlite"

    print(f"Source (read-only): {source_path}")
    print(f"Destination: {dest_path}")

    online_backup(Path(source_path), dest_path)

    digest = sha256_of(dest_path)
    head = git_head()
    size = dest_path.stat().st_size

    print(f"\n=== SNAPSHOT RECORD (paste into docs/OPERATIONS.md) ===")
    print(f"File: data/snapshots/{dest_path.name}")
    print(f"SHA-256: {digest}")
    print(f"Size: {size} bytes")
    print(f"Git HEAD at snapshot time: {head}")
    print(f"Taken (UTC): {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
