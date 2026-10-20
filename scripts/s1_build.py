"""Build frozen S1 inputs, read-only. Foreground only; no outcome imports."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.s1 import inputs as S
from desk.s1.report import sha256, markdown, timing_audit
from desk.t1 import inputs as T
from desk.t1.panel import snapshot_identities
from desk.t1.read_guard import holdout_reads
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config
from shared.sqlite_readonly import open_readonly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    json_report = args.report.with_suffix(".json")
    if any(p.exists() for p in (args.output, args.report, json_report)):
        raise FileExistsError("S1 artifacts are immutable; choose new paths.")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Commit the tested implementation before freezing inputs.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    rb, costs = load_active_rulebook(), load_active_cost_config()
    with holdout_reads():  # Input permission only, not T1/S1 outcome permission.
        indices, mismatches = T.load(ROOT/"data/raw/t1_sources", end=S.END)
        snapshots = snapshot_identities(ROOT/"data/raw/isin_snapshots", end=S.END)
    if mismatches:
        raise ValueError("Conflicting official index sources.")
    index_dates = set().union(*(set(s) for s in indices.values()))
    db, desk = ROOT/"data/processed/praman.db", ROOT/"data/desk/desk.sqlite"
    source_paths = [ROOT/"data/processed/event_catalogue_loose_zscore_only.csv", db, desk]
    source_paths += sorted((ROOT/"config").glob("*.yaml"))
    source_paths += [ROOT/"config/COSTS_ACTIVE", ROOT/"docs/desk/abc_sourcing_check.md",
                    ROOT/"docs/desk/s1_unexplained_drop_prereg.md"]
    source_paths += [ROOT/"rulebook/ACTIVE", ROOT/"rulebook"/rb.version_file]
    source_paths += [p for p in (ROOT/"data/raw/isin_snapshots").glob("cm_*")
                     if p.name[3:13] <= S.END]
    manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in source_paths}
    last = [""]
    def progress(day):
        if day[:7] != last[0]:
            print("S1 inputs through " + day, flush=True)
            last[0] = day[:7]
    with closing(open_readonly(db)) as conn, closing(open_readonly(desk)) as desk_conn:
        cal = S.calendars(conn, index_dates)
        records = S.build_records(conn, desk_conn, S.catalogue(source_paths[0]), snapshots, cal,
                                  rb.rulebook, costs.costs, progress)
    # Store bytes must be unchanged; never hash or inspect an outcome artifact.
    for p in (db, desk):
        if sha256(p) != manifest[str(p.relative_to(ROOT)).replace("\\", "/")]:
            raise RuntimeError("Source store changed during input build.")
    audit = timing_audit((ROOT/"logs/weekly_ingest.log").read_text(encoding="utf-8").splitlines(), cal["s1"])
    summary = S.summarize(records)
    meta = dict(code_commit=commit, version=S.VERSION, manifest=manifest,
                rulebook_sha256=rb.sha256, cost_config_sha256=costs.sha256,
                index_source_hashes=sorted({r["source_sha256"] for series in indices.values() for r in series.values()}),
                category_map=S.A.draft_map(), timing_audit=audit,
                outcomes="not read", knowledge_rule="D 18:00 IST; EQ same-day assumption; dated ISIN strictly before D")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(dict(meta=meta, calendars=cal, records=records, summary=summary), f, sort_keys=True, allow_nan=False)
    with json_report.open("x", encoding="utf-8") as f:
        json.dump(dict(meta=meta, summary=summary, artifact_sha256=sha256(args.output)), f, indent=2, sort_keys=True)
    with args.report.open("x", encoding="utf-8") as f:
        f.write(markdown(summary, meta, str(args.output)))
    print(f"Inputs saved: {args.output}; report: {args.report}")


if __name__ == "__main__":
    main()
