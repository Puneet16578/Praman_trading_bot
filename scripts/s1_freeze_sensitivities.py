"""Enrich a primary S1 input artifact with registered input-only variants."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.s1.sensitivities import enrich
from desk.s1.report import sha256, markdown, timing_audit
from desk.s1.inputs import summarize
from desk.t1.panel import snapshot_identities
from desk.t1.read_guard import holdout_reads
from shared.sqlite_readonly import open_readonly
from desk.lib.rulebook import load_active_rulebook
from desk.lib.costs import load_active_cost_config


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if any(p.exists() for p in (args.output, args.report, args.report.with_suffix(".json"))):
        raise FileExistsError(args.output)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Commit tested code before freezing sensitivities.")
    artifact = json.loads(args.inputs.read_text(encoding="utf-8"))
    rb, costs = load_active_rulebook(), load_active_cost_config()
    rule_paths = ["rulebook/ACTIVE", "rulebook/"+rb.version_file]
    subprocess.run(["git", "diff", "--exit-code", artifact["meta"]["code_commit"], "--", *rule_paths],
                   cwd=ROOT, check=True, capture_output=True)
    artifact["meta"]["manifest"].update({p: sha256(ROOT/p) for p in rule_paths})
    artifact["meta"].update(rulebook_sha256=rb.sha256, cost_config_sha256=costs.sha256)
    for relative, digest in artifact["meta"]["manifest"].items():
        if sha256(ROOT/relative) != digest:
            raise ValueError("Primary input source changed: "+relative)
    with holdout_reads():
        snapshots = snapshot_identities(ROOT/"data/raw/isin_snapshots", end="2025-12-31")
    last = [""]
    def progress(day):
        if day[:7] != last[0]:
            print("S1 sensitivity inputs through "+day, flush=True)
            last[0] = day[:7]
    with closing(open_readonly(ROOT/"data/processed/praman.db")) as conn:
        enrich(conn, artifact, snapshots, progress)
    artifact["meta"].update(primary_artifact_sha256=sha256(args.inputs),
        sensitivity_code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
    summary = summarize(artifact["records"])
    # Additional reason detail must not change any population/tercile count.
    for old, new in zip(artifact["summary"]["cells"], summary["cells"]):
        for key in ("retained", "inputs_eligible", "distinct_dates", "scheduled_overlap_count", "turnover_bands"):
            if old[key] != new[key]:
                raise AssertionError("Sensitivity enrichment changed primary inputs.")
    if artifact["summary"]["tercile_boundaries"] != summary["tercile_boundaries"]:
        raise AssertionError("Sensitivity enrichment changed frozen terciles.")
    artifact["summary"] = summary
    with (ROOT/"logs/weekly_ingest.log").open(encoding="utf-8") as log:
        artifact["meta"]["timing_audit"] = timing_audit(log, artifact["calendars"]["s1"])
    for relative, digest in artifact["meta"]["manifest"].items():
        if sha256(ROOT/relative) != digest:
            raise ValueError("Primary input source changed during enrichment: "+relative)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(artifact, f, sort_keys=True, allow_nan=False)
    with args.report.with_suffix(".json").open("x", encoding="utf-8") as f:
        json.dump(dict(meta=artifact["meta"], summary=summary, artifact_sha256=sha256(args.output)), f, indent=2, sort_keys=True)
    with args.report.open("x", encoding="utf-8") as f:
        f.write(markdown(summary, artifact["meta"], str(args.output)))
        f.write("\nInput sensitivities frozen at `" + artifact["meta"]["sensitivity_code_commit"] +
                "`. Primary counts and tercile boundaries are unchanged; peer-unknown and peer-explained "
                "reasons are now also split in the companion JSON.\n")
    print("Frozen inputs with sensitivities: "+str(args.output))


if __name__ == "__main__":
    main()
