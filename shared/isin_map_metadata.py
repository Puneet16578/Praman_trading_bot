"""Companion metadata for the operational ISIN map; no research calculations."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path

from shared.market_time import IST
MAX_AGE_TRADING_DAYS = 5  # G1 fails, and desk status reports ERROR, above this age
MAP_PATH = Path(__file__).resolve().parents[1] / "data/raw/nse_symbol_isin_current.json"


def companion_path(map_path: Path) -> Path:
    return map_path.with_suffix(".meta.json")


def write_metadata(map_path: Path, *, built_at: str, snapshot_dates: list[str],
                   build_time_source: str = "refresh") -> dict:
    timestamp = datetime.fromisoformat(built_at)
    if timestamp.utcoffset() is None:
        raise ValueError("ISIN build timestamp requires a timezone offset")
    metadata = {
        "built_at": built_at,
        "build_time_source": build_time_source,
        "map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest(),
        "snapshot_dates": snapshot_dates,
        "snapshot_dates_source": "not_recorded" if build_time_source == "file_mtime" else "refresh",
    }
    target = companion_path(map_path)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return metadata


def bootstrap_metadata(map_path: Path = MAP_PATH) -> dict:
    """One-time attribution from file mtime; never invent historical snapshot dates."""
    if companion_path(map_path).exists():
        return read_metadata(map_path)
    built_at = datetime.fromtimestamp(map_path.stat().st_mtime, IST).isoformat()
    return write_metadata(map_path, built_at=built_at, snapshot_dates=[],
                          build_time_source="file_mtime")


def read_metadata(map_path: Path = MAP_PATH) -> dict:
    metadata = json.loads(companion_path(map_path).read_text(encoding="utf-8"))
    if metadata["map_sha256"] != hashlib.sha256(map_path.read_bytes()).hexdigest():
        raise ValueError("ISIN map checksum does not match its companion")
    if datetime.fromisoformat(metadata["built_at"]).utcoffset() is None:
        raise ValueError("ISIN build timestamp requires a timezone offset")
    return metadata


def verified_built_at() -> str:
    """Empty string records unavailable/unverified metadata on a NEW decision."""
    try:
        return read_metadata()["built_at"]
    except (OSError, ValueError, KeyError, TypeError):
        return ""


def trading_days_since_build(conn, built_at: str, as_of_date: str) -> int:
    timestamp = datetime.fromisoformat(built_at)
    if timestamp.utcoffset() is None:
        raise ValueError("ISIN build timestamp requires a timezone offset")
    build_date = timestamp.astimezone(IST).date().isoformat()
    return conn.execute(
        "SELECT COUNT(DISTINCT event_date) FROM bhavcopy "
        "WHERE event_date > ? AND event_date <= ? AND knowledge_date <= ?",
        (build_date, as_of_date, as_of_date),
    ).fetchone()[0]
