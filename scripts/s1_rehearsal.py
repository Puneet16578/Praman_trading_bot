"""Foreground S1 rehearsal, real readers sealed; no real evaluation entry point."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desk.s1.rehearsal import rehearse
from desk.s1.report import sha256
from desk.lib.costs import load_active_cost_config


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists() or args.report.exists():
        raise FileExistsError("Rehearsal artifacts are immutable.")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Commit tested code before rehearsal.")
    artifact = json.loads(args.inputs.read_text(encoding="utf-8"))
    result = rehearse(artifact, load_active_cost_config().costs)
    result.update(code_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  input_sha256=sha256(args.inputs), input_artifact=str(args.inputs))
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, indent=2, allow_nan=False)
    lines = ["# S1 synthetic random-label rehearsal", "", "**NOT an S1 evaluation.**",
             result["limitation"], "", f"Code: `{result['code_commit']}`; seed: `{result['seed']}`.",
             f"Input artifact SHA-256: `{result['input_sha256']}`.",
             f"Real-reader seal verified: {result['real_reader_block_verified']}; real outcome reads: 0.",
             f"Elapsed: {result['elapsed_seconds']:.2f} seconds.", "",
             "| h | Test (a) usable draws | Test (b) usable draws |",
             "|---|---|---|"]
    for t in result["primary"]["tests"]:
        lines.append(f"| {t['horizon']} | {t['a']['usable_draws']} | {t['b']['usable_draws']} |")
    lines += ["", f"Registered one-change sensitivities exercised: {len(result['sensitivities'])}.",
              "The full JSON contains synthetic coverage, draw-rejection reasons and report cells.",
              "Development evaluation remains unrun and requires separate approval.", ""]
    with args.report.open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Rehearsal complete; real outcomes sealed. Report: {args.report}")


if __name__ == "__main__":
    main()
