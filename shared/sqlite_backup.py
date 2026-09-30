"""SQLite's online backup API, with a read-only source and a fresh destination."""
import sqlite3
from pathlib import Path

from shared.sqlite_readonly import open_readonly


def online_backup(source: Path, destination: Path) -> None:
    # Exclusive creation prevents accidentally replacing another database.
    with destination.open("xb"):
        pass
    source_conn = open_readonly(source)
    try:
        destination_conn = sqlite3.connect(str(destination))
        try:
            source_conn.backup(destination_conn)
        finally:
            destination_conn.close()
    finally:
        source_conn.close()
