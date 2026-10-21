"""User-launched S1 development sensitivities only; never evaluate primary.

No store is opened at import. --check-only seals real readers and selects only
schema/recording metadata from stores. Outcomes require an explicit normal CLI
invocation by the user. Frozen S1 and shared readers are not modified.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack, closing
from datetime import datetime, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared.market_time import IST
from shared.sqlite_readonly import open_readonly
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.s1 import statistics as S
from desk.s1.evaluation import evaluate_inputs, sensitivity_inputs
from desk.s1.inputs import DEV_END, summarize
from desk.s1.reader import RealReader, seal_real_reads
from desk.s1.report import sha256
from desk.s1.sensitivities import VARIANTS
from desk.t1 import inputs as T
from desk.t1.panel import snapshot_identities

INPUT = "data/s1/inputs_complete_20261020_v1.json"
INPUT_SHA = "c0d88d62719f090d1bde5430e9801ddad57d03715555f37914d2d6c3597bb309"
PRIMARY = "docs/desk/s1_development_results_20261021_primary.json"
PRIMARY_SHA = "2d3c312399d8fa5083f73a4a46eeab17b594f89ef0204f59bcddcde61c6cf354"
RECORDED_BEFORE = datetime.fromisoformat("2026-10-21T08:35:49+05:30")
SOURCES = {
    "data/processed/praman.db": ("bhavcopy", "corporate_actions", "corporate_announcements"),
    "data/desk/desk.sqlite": ("circuit_bands", "tick_sizes"),
}


class Refused(RuntimeError):
    """Controlled diagnostic, never raw exception text from a source."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def now():
    return datetime.now(timezone.utc)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


@lru_cache(maxsize=8192)
def before_primary(value):
    try:
        stamp = datetime.fromisoformat(value)
        require(stamp.utcoffset() is not None, "Recording timestamp lacks timezone")
        require(stamp.isoformat() == value.replace("Z", "+00:00"), "Noncanonical recording timestamp")
        return stamp < RECORDED_BEFORE
    except (TypeError, ValueError):
        raise Refused("Invalid recording timestamp") from None


class RecordedConnection:
    """Route frozen SELECTs, including BoundedInputs' main-qualified queries,
    through private temporary views. Main remains mode=ro; only TEMP schema is
    populated. The SQLite authorizer rejects any bypass or unreviewed table.
    """
    def __init__(self, conn, tables):
        self._conn = conn
        self._tables = tuple(tables)
        conn.execute("BEGIN")
        for table in tables:
            columns = {r[1] for r in conn.execute(f'PRAGMA main.table_info("{table}")')}
            require({"event_date", "knowledge_date", "recorded_at"} <= columns,
                    "Required source table or recording columns absent: " + table)
            # Metadata only. Validate all potentially visible timestamp formats
            # before outcomes, including late rows which the views will exclude.
            for row in conn.execute(f'SELECT DISTINCT recorded_at FROM main."{table}" '
                                    'WHERE event_date<=? AND knowledge_date<=?', (DEV_END, DEV_END)):
                before_primary(row[0])
        conn.create_function("s1_before_primary", 1, before_primary, deterministic=True)
        for table in tables:
            conn.execute(f'CREATE TEMP VIEW "s1_frozen_{table}" AS SELECT * FROM main."{table}" '
                         f"WHERE event_date<='{DEV_END}' AND knowledge_date<='{DEV_END}' "
                         # Writers use canonical UTC. Keep that common path in SQLite;
                         # offset timestamps use the exact, microsecond-aware function.
                         "AND CASE WHEN substr(recorded_at,-6)='+00:00' THEN "
                         "recorded_at<'2026-10-21T03:05:49' ELSE s1_before_primary(recorded_at) END")
        conn.execute("PRAGMA query_only=ON")
        conn.set_authorizer(self._authorize)

    def _authorize(self, action, arg1, arg2, database, source):
        if action == sqlite3.SQLITE_READ:
            if database == "main":
                ok = arg1 in self._tables and source == "s1_frozen_" + arg1
            else:
                ok = database == "temp" and arg1 in {"s1_frozen_" + t for t in self._tables}
            return sqlite3.SQLITE_OK if ok else sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and arg2 != "load_extension":
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def execute(self, sql, parameters=()):
        require(sql.lstrip().upper().startswith("SELECT"), "Outcome connection accepts SELECT only")
        for table in self._tables:
            sql = re.sub(r"\b(FROM|JOIN)\s+(?:main\.)?" + table + r"\b",
                         lambda m: m[1] + " temp.s1_frozen_" + table, sql, flags=re.I)
        return self._conn.execute(sql, parameters)


@contextmanager
def recorded_sources(root):
    with ExitStack() as stack:
        handles = [RecordedConnection(stack.enter_context(closing(open_readonly(root / path))), tables)
                   for path, tables in SOURCES.items()]
        yield handles


def paths(root, variant):
    return (root / f"docs/desk/s1_development_results_20261021_sensitivity_{variant}.json",
            root / f"data/s1/sensitivity_attempts/{variant}.attempt.json")


def check_destinations(root, variants, rerun):
    for variant in variants:
        output, marker = paths(root, variant)
        require(not output.exists(), "Completed result exists: " + variant + "; request only remaining variants")
        require(rerun or not marker.exists(), "Attempt without result: " + variant + "; explicit --rerun-interrupted required")
        if marker.exists():
            old = json.loads(marker.read_text(encoding="utf-8"))
            require(old.get("variant") == variant and old.get("input_sha256") == INPUT_SHA,
                    "Attempt marker identity mismatch")


def atomic_create(path, value):
    """Publish a fully flushed file atomically, with no overwrite even in a race.
    Hard-link creation is atomic and fails if target exists (including on NTFS).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def variant_lock(marker):
    """OS lock releases on process death; a rerun flag cannot duplicate a live run."""
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.with_suffix(".lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise Refused("Variant is already running") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def load_inputs(root):
    # Hash first, before parsing the artifact or touching any outcome source.
    require(sha256(root / INPUT) == INPUT_SHA, "Input artifact hash mismatch")
    artifact = json.loads((root / INPUT).read_text(encoding="utf-8"))
    require(git(root, "branch", "--show-current") == "master", "Master branch required")
    # Completed outputs are expected while running the next batch. Other dirt fails.
    status = subprocess.check_output(["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=root).decode()
    expected = {str(paths(root, v)[0].relative_to(root)).replace("\\", "/") for v in VARIANTS}
    # A hard kill during publication can leave an incomplete temporary file.
    # Preserve it as evidence; only an existing attempt marker can explain it.
    # Destination checks still require --rerun-interrupted for that variant.
    for variant in VARIANTS:
        output, marker = paths(root, variant)
        if marker.exists():
            for partial in output.parent.glob(output.name + ".*.partial"):
                if re.fullmatch(re.escape(output.name) + r"\.[0-9a-f]{32}\.partial", partial.name):
                    expected.add(partial.relative_to(root).as_posix())
    require(all(x[:2] == "??" and x[3:] in expected for x in status.split("\0") if x),
            "Commit source/config changes before invocation")
    require(git(root, "rev-parse", "HEAD") == git(root, "rev-parse", "origin/master"), "HEAD differs from local origin/master; fetch and align first")
    require(not git(root, "diff", "b539e7e", "--", "desk/s1", "scripts/s1_*"), "Frozen S1 code differs")
    require(sha256(root / PRIMARY) == PRIMARY_SHA, "Locked primary hash mismatch")
    rb, costs = load_active_rulebook(), load_active_cost_config()
    require(rb.sha256 == artifact["meta"]["rulebook_sha256"], "Rulebook hash mismatch")
    require(costs.sha256 == artifact["meta"]["cost_config_sha256"], "Cost hash mismatch")
    require((S.SEED, S.DRAWS, S.BLOCK, S.MIN_USABLE) == (20261001, 2000, 20, 1900)
            and S.FAMILY == (("a", 1), ("b", 1), ("a", 3), ("b", 3)), "Bootstrap settings differ")
    manifest = artifact["meta"]["manifest"]
    for relative, digest in manifest.items():
        if relative in SOURCES:
            continue  # normal nightly appends; recording-cutoff views bind reads
        match = re.search(r"cm_(\d{4}-\d{2}-\d{2})", relative)
        if match and match[1] > DEV_END:
            continue
        require(sha256(root / relative) == digest, "Frozen source hash mismatch: " + relative)
    ledger_hashes = set()
    for folder in (root / "data/raw/t1_sources", root / "data/raw/t1_sources/phase2"):
        for entry in T._ledger(folder / "requests.jsonl"):
            label = entry.get("label", "")
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", label)
            if entry.get("status") == 200 and label.startswith(("history_", "snapshot_")):
                ledger_hashes.add(entry["sha256"])
                if dates and max(dates) <= DEV_END:
                    require(sha256(folder / entry["file"]) == entry["sha256"], "Index payload hash mismatch")
    # Ledger metadata may name later files, but their payloads are never opened.
    require(set(artifact["meta"]["index_source_hashes"]) <= ledger_hashes, "Frozen index source missing from ledgers")
    indices, mismatches = T.load(root / "data/raw/t1_sources", end=DEV_END)
    require(not mismatches, "Index sources disagree")
    require(all(indices.get(series) for series in T.SERIES), "Development index series missing")
    require(all(row["source_sha256"] in artifact["meta"]["index_source_hashes"]
                for rows in indices.values() for row in rows.values()), "Unfrozen index source")
    snapshots = snapshot_identities(root / "data/raw/isin_snapshots", end=DEV_END)
    for day, _ in snapshots:
        require("data/raw/isin_snapshots/cm_" + day + ".csv" in manifest, "Unfrozen ISIN snapshot")
    artifact["records"] = [r for r in artifact["records"] if r["day"] <= DEV_END]
    require(all(set(VARIANTS[:5]) <= set(r["sensitivity_exclusions"]) for r in artifact["records"]),
            "Frozen sensitivity input missing")
    return artifact, costs.costs, indices, snapshots, dict(
        code_commit=git(root, "rev-parse", "HEAD"), input_sha256=INPUT_SHA,
        primary_sha256=PRIMARY_SHA, rulebook_sha256=rb.sha256, cost_config_sha256=costs.sha256,
        wrapper_sha256=sha256(Path(__file__)), recorded_before=RECORDED_BEFORE.isoformat(),
        reader_end=DEV_END, tercile_boundaries=artifact["summary"]["tercile_boundaries"],
        bootstrap=dict(seed=S.SEED, draws=S.DRAWS, block=S.BLOCK, minimum_usable=S.MIN_USABLE,
                                          family=S.FAMILY, family_confidence=.9875))


def audit(data):
    from collections import Counter
    result = {}
    for h in (1, 3):
        result[str(h)] = {}
        for group in ("unexplained", "explained"):
            rows = [r for r in data["records"] if r["horizon"] == h and r["group"] == group]
            overlaps = Counter("+".join(k for k in ("missing_sessions", "circuit_delays", "dividend_sessions", "dividend_unknown_sessions")
                                        if r.get(k)) or "none" for r in rows if r.get("filled"))
            result[str(h)][group] = dict(filled=sum(bool(r.get("filled")) for r in rows),
                benchmark_member_observations=sum(r.get("benchmark", {}).get("members", 0) for r in rows),
                benchmark_missing_member_observations=sum(r.get("benchmark", {}).get("missing", 0) for r in rows),
                hold_reason_overlaps=dict(overlaps))
    return result


def evaluate_variant(artifact, reader, costs, variant):
    require(variant in VARIANTS, "Unregistered variant")
    inputs = artifact if variant == "exit_slippage_040" else sensitivity_inputs(artifact, variant)
    result = evaluate_inputs(inputs, reader, costs, period="development",
                             slippage=.004 if variant == "exit_slippage_040" else .0015)
    result["input_cells"] = [c for c in summarize(inputs["records"])["cells"] if c["year"] <= 2024]
    result["audit"] = audit(result)
    return result


def run(args, root=ROOT):
    require(bool(args.variants) and len(set(args.variants)) == len(args.variants) and all(v in VARIANTS for v in args.variants),
            "Variants must be a nonempty, unique registered list")
    artifact, costs, indices, snapshots, meta = load_inputs(root)
    check_destinations(root, args.variants, args.rerun_interrupted)
    # Run all store setup/metadata validation even in check-only, with real reads sealed.
    with seal_real_reads(), recorded_sources(root):
        pass
    if args.check_only:
        print("CHECK_ONLY_OK: inputs loaded; recording metadata checked; no outcome read", flush=True)
        return 0
    for variant in args.variants:
        if args.no_start_after is not None and now() > args.no_start_after:
            print("NO_START_AFTER: remaining variants not started", flush=True)
            return 0
        output, marker = paths(root, variant)
        with variant_lock(marker):
            check_destinations(root, [variant], args.rerun_interrupted)
            if args.no_start_after is not None and now() > args.no_start_after:
                print("NO_START_AFTER: remaining variants not started", flush=True)
                return 0
            rerun = marker.exists()
            attempt = marker if not rerun else marker.with_name(variant + ".rerun." + uuid.uuid4().hex + ".attempt.json")
            started = now().isoformat()
            info = dict(meta, variant=variant, started_utc=started, rerun_interrupted=rerun,
                        rerun_interrupted_requested=args.rerun_interrupted,
                        original_attempt_sha256=sha256(marker) if rerun else None,
                        attempt_path=str(attempt.relative_to(root)),
                        no_start_after=args.no_start_after.isoformat() if args.no_start_after else None)
            atomic_create(attempt, info)
            print("START " + variant + " " + started, flush=True)
            try:
                with recorded_sources(root) as (conn, desk):
                    reader = RealReader(conn, desk, DEV_END, authorized=True, snapshots=snapshots, index_closes=indices)
                    data = evaluate_variant(artifact, reader, costs, variant)
                ended = now().isoformat()
                atomic_create(output, dict(status="COMPLETE", meta=dict(info, ended_utc=ended), result=data))
                print("COMPLETE " + variant + " " + ended, flush=True)
            except BaseException as exc:
                atomic_create(attempt.with_suffix(".failure.json"), dict(info, ended_utc=now().isoformat(),
                              status="STOPPED", error_type=type(exc).__name__))
                raise
    return 0


def deadline(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except ValueError:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD HH:MM (IST)") from None


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variants", nargs="+", choices=VARIANTS, required=True)
    p.add_argument("--no-start-after", type=deadline, help="IST; a running variant finishes")
    p.add_argument("--rerun-interrupted", action="store_true")
    p.add_argument("--check-only", action="store_true")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return run(args)
    except Refused as exc:
        print("STOPPED: " + str(exc), file=sys.stderr)
    except BaseException as exc:
        print("STOPPED: " + type(exc).__name__ + "; inspect attempt metadata; no automatic retry", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
