"""Builds the demo's own store: a structurally cutoff-truncated COPY of production, plus the
derived picker catalogue rebuilt from that same truncated copy. Run this before a demo session, and
again whenever weekly ingestion has moved the production store forward and you want a fresher demo
(re-run always regenerates deterministically from production + the current cutoff).

Two things this script deliberately does NOT do, and why:
  - It does not touch data/processed/praman.db or any file under data/processed/ -- it only ever
    OPENS that store read-only (mode=ro) as the backup source. This is the one place in `demo/`
    that references the production path, because building the demo store's only job is to read
    from production once and never again for the rest of a demo session.
  - It does not edit scripts/build_final_event_catalogue.py, compute_clustering.py,
    compute_close_to_close.py, or build_event_classifications.py to accept a custom output path --
    those are pinned, and CLAUDE.md forbids modifying pinned code for this demo. Instead it runs
    them, UNMODIFIED, inside a throwaway `git worktree` (a second, physically separate checkout of
    this same repository) with PRAMAN_DATABASE_PATH pointed at the demo store copy -- their
    hardcoded, project-root-relative output paths then resolve to the WORKTREE's own data/processed/,
    never this repository's real one, so nothing here can ever clobber production's own derived
    artifacts. Only the two files the picker actually needs are copied back out:
    event_classifications.csv and classification_thresholds.json.

The structural-cutoff step (deleting every row with event_date OR knowledge_date after the cutoff,
BEFORE the catalogue rebuild ever runs) is what makes the picker's own sessions_to_subsequent_flag/
subsequent_flag_note correct for free: build_event_classifications.py is not modified or told about
any cutoff -- it simply cannot see a surveillance flag, or a trading day, that the demo store's own
tables no longer contain. A "no subsequent flag" result for an event whose real flag came after the
cutoff is not a special case this script handles; it is what the unmodified script naturally
computes when handed a store that stops at the cutoff.
"""
from __future__ import annotations
import hashlib
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo.lib.cutoff import DEMO_DATA_CUTOFF
from demo.lib.store import DEMO_CLASSIFICATIONS_PATH, DEMO_DB_PATH, DEMO_THRESHOLDS_PATH
from src.config.settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FACT_TABLES = ("bhavcopy", "corporate_actions", "surveillance_flags", "corporate_announcements", "sebi_orders")

PIPELINE_SCRIPTS = (
    "scripts/build_final_event_catalogue.py",
    "scripts/compute_clustering.py",
    "scripts/compute_close_to_close.py",
    "scripts/build_event_classifications.py",
)
ARTIFACTS_TO_COPY = {
    "data/processed/event_classifications.csv": DEMO_CLASSIFICATIONS_PATH,
    "data/processed/classification_thresholds.json": DEMO_THRESHOLDS_PATH,
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_production_readonly(dest: Path) -> None:
    settings = get_settings()
    source_uri = f"file:{Path(settings.database_path).as_posix()}?mode=ro"
    print(f"Backing up (read-only source): {settings.database_path}")
    source_conn = sqlite3.connect(source_uri, uri=True)
    dest_conn = sqlite3.connect(str(dest))
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()


def truncate_to_cutoff(db_path: Path, cutoff: str) -> None:
    conn = sqlite3.connect(str(db_path))
    print(f"\nTruncating every fact table to event_date <= {cutoff} AND knowledge_date <= {cutoff}:")
    for table in FACT_TABLES:
        before = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.execute(f"DELETE FROM {table} WHERE event_date > ? OR knowledge_date > ?", (cutoff, cutoff))
        after = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {before} -> {after} (removed {before - after})")
    conn.commit()
    print("VACUUM...")
    conn.execute("VACUUM")
    conn.close()


def verify_truncation(db_path: Path, cutoff: str) -> None:
    conn = sqlite3.connect(str(db_path))
    for table in FACT_TABLES:
        row = conn.execute(f"SELECT MAX(event_date) me, MAX(knowledge_date) mk FROM {table}").fetchone()
        me, mk = row
        if me is not None and me > cutoff:
            raise RuntimeError(f"{table}: max(event_date)={me} exceeds cutoff {cutoff}")
        if mk is not None and mk > cutoff:
            raise RuntimeError(f"{table}: max(knowledge_date)={mk} exceeds cutoff {cutoff}")
        print(f"  {table}: max(event_date)={me}  max(knowledge_date)={mk}  (both <= {cutoff}: OK)")
    conn.close()


def rebuild_catalogue_in_worktree(demo_db_path: Path) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT).decode().strip()
    worktree_dir = Path.home() / ".praman_demo_build_worktree"
    if worktree_dir.exists():
        subprocess.run(["git", "worktree", "remove", str(worktree_dir), "--force"],
                        cwd=PROJECT_ROOT, check=False)
        shutil.rmtree(worktree_dir, ignore_errors=True)

    print(f"\nCreating isolated worktree at {worktree_dir} (HEAD={head})")
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree_dir), head],
                    cwd=PROJECT_ROOT, check=True)
    try:
        env = {"PRAMAN_DATABASE_PATH": str(demo_db_path)}
        import os
        full_env = {**os.environ, **env}
        for script in PIPELINE_SCRIPTS:
            print(f"\n=== {script} (in worktree, against demo store) ===")
            subprocess.run([sys.executable, script], cwd=worktree_dir, env=full_env, check=True)

        for src_rel, dest_abs in ARTIFACTS_TO_COPY.items():
            src_abs = worktree_dir / src_rel
            dest_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_abs, dest_abs)
            print(f"Copied {src_rel} -> {dest_abs}")
    finally:
        subprocess.run(["git", "worktree", "remove", str(worktree_dir), "--force"],
                        cwd=PROJECT_ROOT, check=False)


def main() -> None:
    DEMO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DEMO_DB_PATH.exists():
        DEMO_DB_PATH.unlink()

    backup_production_readonly(DEMO_DB_PATH)
    truncate_to_cutoff(DEMO_DB_PATH, DEMO_DATA_CUTOFF)

    print(f"\nVerifying truncation (every table, event_date and knowledge_date <= {DEMO_DATA_CUTOFF}):")
    verify_truncation(DEMO_DB_PATH, DEMO_DATA_CUTOFF)

    rebuild_catalogue_in_worktree(DEMO_DB_PATH)

    digest = sha256_of(DEMO_DB_PATH)
    size = DEMO_DB_PATH.stat().st_size
    print(f"\n=== DEMO STORE BUILD RECORD (paste into docs/OPERATIONS.md) ===")
    print(f"File: {DEMO_DB_PATH.relative_to(PROJECT_ROOT)}")
    print(f"SHA-256: {digest}")
    print(f"Size: {size} bytes")
    print(f"Cutoff: {DEMO_DATA_CUTOFF}")


if __name__ == "__main__":
    main()
