"""Official index inputs for T1: NIFTY 50, NIFTY 500 and India VIX daily closes.

Sources (docs/desk/t1_sourcing_probe_20261014.md): niftyindices' historical-data endpoint, one
response per series and year (no Last-Modified; the response Date is kept), and the dated Daily
Snapshot files for sessions the history lacks. Knowledge rule (T1 addendum 2, an ASSUMPTION): a
close for session D is known from the next global session, never on D itself.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from pathlib import Path

SERIES = ("NIFTY 50", "NIFTY 500", "INDIA VIX")
KNOWLEDGE_RULE = "known from the next global session (ASSUMPTION, T1 addendum 2)"


def _ledger(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def history_rows(phase2_dir: Path) -> list[dict]:
    """Rows from the historical-data responses: series, event_date, OHLC and provenance."""
    rows = []
    for e in _ledger(phase2_dir / "requests.jsonl"):
        if not e["label"].startswith("history_") or e.get("status") != 200:
            continue
        for r in json.loads((phase2_dir / e["file"]).read_bytes()):
            name = r["INDEX_NAME"].strip().upper()
            if name not in SERIES:
                raise ValueError(f"Unexpected series {name!r} in {e['file']}")
            rows.append(dict(series=name, event_date=datetime.strptime(r["HistoricalDate"], "%d %b %Y").date().isoformat(),
                             open=float(r["OPEN"]), high=float(r["HIGH"]), low=float(r["LOW"]), close=float(r["CLOSE"]),
                             source_kind="historical-data", source_url=e["url"], source_sha256=e["sha256"],
                             source_last_modified=None, retrieved_at=(e.get("headers") or {}).get("Date")))
    return rows


def snapshot_rows(*dirs: Path) -> list[dict]:
    """The three series from dated Daily Snapshot files, with each file's Last-Modified."""
    rows = []
    for folder in dirs:
        for e in _ledger(folder / "requests.jsonl"):
            if not e["label"].startswith("snapshot_") or e.get("status") != 200:
                continue
            requested = e["label"].split("_", 1)[1]
            for r in csv.DictReader(io.StringIO((folder / e["file"]).read_bytes().decode("utf-8-sig", "replace"))):
                name = r["Index Name"].strip().upper()
                if name not in SERIES:
                    continue
                own = datetime.strptime(r["Index Date"].strip(), "%d-%m-%Y").date().isoformat()
                if own != requested:
                    raise ValueError(f"Daily Snapshot for {requested} carries the date {own}")
                rows.append(dict(series=name, event_date=own, open=float(r["Open Index Value"]),
                                 high=float(r["High Index Value"]), low=float(r["Low Index Value"]),
                                 close=float(r["Closing Index Value"]), source_kind="daily-snapshot",
                                 source_url=e["url"], source_sha256=e["sha256"],
                                 source_last_modified=(e.get("headers") or {}).get("Last-Modified"),
                                 retrieved_at=(e.get("headers") or {}).get("Date")))
    return rows


def combine(history: list[dict], snapshots: list[dict]) -> tuple[dict, list[dict]]:
    """{series: {date: row}} from the history, gaps filled from the snapshots, and every snapshot
    that disagrees with the history on the close (the only value T1 uses)."""
    out = {s: {} for s in SERIES}
    for r in history:
        if r["event_date"] in out[r["series"]] and out[r["series"]][r["event_date"]]["close"] != r["close"]:
            raise ValueError(f"Conflicting history closes for {r['series']} {r['event_date']}")
        out[r["series"]][r["event_date"]] = r
    mismatches = []
    for r in snapshots:
        known = out[r["series"]].get(r["event_date"])
        if known is None:
            out[r["series"]][r["event_date"]] = r
        elif abs(known["close"] - r["close"]) > 1e-9:
            mismatches.append(dict(series=r["series"], event_date=r["event_date"], history=known["close"], snapshot=r["close"]))
    return out, mismatches


def load(raw_root: Path) -> tuple[dict, list[dict]]:
    return combine(history_rows(raw_root / "phase2"), snapshot_rows(raw_root, raw_root / "phase2"))


def is_weekday(day: str) -> bool:
    return date.fromisoformat(day).weekday() < 5
