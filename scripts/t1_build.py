"""Build T1 inputs and features (no outcome) and write the coverage and missingness report.

    python -B scripts/t1_build.py

Reads Praman's store read-only, the cached dated ISIN snapshots and the T1 source downloads; writes
a new data/t1/build_<stamp>.sqlite and docs/desk/t1_coverage_<date>.md. Never during the nightly.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desk.t1 import build, features as F, inputs
from desk.t1.panel import load_panel, snapshot_identities
from shared.sqlite_readonly import open_readonly

PRAMAN_DB = ROOT / "data" / "processed" / "praman.db"
RAW = ROOT / "data" / "raw" / "t1_sources"
ISIN = ROOT / "data" / "raw" / "isin_snapshots"


def main() -> int:
    F.refuse_outside_study(F.STUDY_END)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    index_closes, mismatches = inputs.load(RAW)
    if mismatches:
        raise SystemExit(f"Index close mismatches between sources: {mismatches}")
    snapshots = snapshot_identities(ISIN)
    conn = open_readonly(PRAMAN_DB)
    try:
        panel = load_panel(conn, index_closes, snapshots)
        late = build.late_known_sessions(conn)
    finally:
        conn.close()
    out = F.compute(panel)
    cause = F.exclusion_causes(panel)
    period = F.periods(panel.sessions, panel.forward_sessions)
    bounds = F.quintile_bounds(out["atr_pct"], cause, period)
    artifact = ROOT / "data" / "t1" / f"build_{stamp}.sqlite"
    index_files = sorted({r["source_sha256"] for s in index_closes.values() for r in s.values()})
    meta = dict(artifact=str(artifact.relative_to(ROOT)).replace("\\", "/"), code_commit=commit, built_at=stamp,
                praman_db_sha256=build.file_sha256(PRAMAN_DB), index_files=index_files,
                isin_snapshots=[d for d, _ in snapshots], quintile_bounds=bounds,
                store_missing_sessions=panel.store_missing_sessions, weekend_specials=panel.weekend_specials,
                knowledge_rule_index=inputs.KNOWLEDGE_RULE, outcomes="none loaded or computed")
    build.write_artifact(artifact, panel, out, cause, period, bounds, index_closes, meta)
    text = build.report(panel, out, cause, period, bounds, index_closes, meta, late)
    from shared.market_time import IST
    target = ROOT / "docs" / "desk" / f"t1_coverage_{datetime.now(IST).strftime('%Y%m%d')}.md"
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Artifact {artifact}; report {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
