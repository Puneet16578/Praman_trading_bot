"""desk replay DECISION_ID -- reconstructs BOTH stores as they stood at decision time and reruns
the identical assessment, diffing the result against what was recorded. Uses the same TEMP-VIEW
shadowing approach for the Desk's own store as desk/lib/store.py uses for Praman's (G6/G7 read the
journal, so a trade logged AFTER the decision must not leak into a replay of it either).
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path

from desk.evidence.bundle import assemble_evidence_bundle  # noqa: F401 (re-exported for callers)
from desk.gates.engine import run_assessment
from desk.journal.store import get_decision, get_thesis
from desk.lib.connection import DESK_DB_PATH
from desk.lib.costs import CostConfig, load_active_cost_config
from desk.lib.rulebook import DeskRulebook, load_active_rulebook
from desk.lib.store import get_replay_connection
from shared.sqlite_readonly import open_readonly

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReplayError(RuntimeError):
    pass


def current_git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    return result.stdout.strip()


def get_desk_replay_connection(desk_db_path: Path, watermark: str):
    """Same TEMP-VIEW-shadowing approach as desk/lib/store.py, applied to the Desk's own tables."""
    from desk.lib.schema import DESK_TABLES

    conn = open_readonly(desk_db_path)
    for table in DESK_TABLES:
        conn.execute(f"CREATE TEMP VIEW {table} AS SELECT * FROM main.{table} WHERE recorded_at <= '{watermark}'")
    return conn


@dataclass
class ReplayResult:
    decision_id: int
    matched: bool
    original_state: str
    replayed_state: str
    original_gate_results: dict
    replayed_gate_results: dict
    code_commit_matches: bool
    diff: list[str]


def replay_decision(decision_id: int, desk_db_path: Path = DESK_DB_PATH,
                     rulebook_override: DeskRulebook | None = None,
                     costs_override: CostConfig | None = None) -> ReplayResult:
    import sqlite3

    bootstrap_conn = sqlite3.connect(str(desk_db_path))
    bootstrap_conn.row_factory = sqlite3.Row
    decision = get_decision(bootstrap_conn, decision_id)
    bootstrap_conn.close()
    if decision is None:
        raise ReplayError(f"No decision with id {decision_id}.")

    head = current_git_head()
    code_commit_matches = (head == decision["code_commit"])
    if not code_commit_matches:
        raise ReplayError(
            f"Recorded code_commit {decision['code_commit']} does not match current HEAD {head}. "
            "Check out that commit (e.g. in a separate worktree) before replaying -- this function "
            "refuses to replay against different code than the one that made the original decision."
        )

    if rulebook_override is not None:
        rulebook, rulebook_hash = rulebook_override, decision["rulebook_hash"]
    else:
        loaded = load_active_rulebook()
        if loaded.sha256 != decision["rulebook_hash"]:
            raise ReplayError(
                f"Active rulebook hash {loaded.sha256} does not match decision's recorded hash "
                f"{decision['rulebook_hash']} -- load the exact rulebook version this decision used."
            )
        rulebook, rulebook_hash = loaded.rulebook, loaded.sha256

    if costs_override is not None:
        costs = costs_override
    else:
        loaded_costs = load_active_cost_config()
        if loaded_costs.sha256 != decision["cost_config_hash"]:
            raise ReplayError(
                f"Active cost config hash {loaded_costs.sha256} does not match decision's recorded "
                f"hash {decision['cost_config_hash']}."
            )
        costs = loaded_costs.costs

    praman_conn = get_replay_connection(decision["praman_watermark"])
    desk_conn = get_desk_replay_connection(desk_db_path, decision["desk_watermark"])

    thesis = get_thesis(desk_conn, decision["thesis_id"]) if decision["thesis_id"] else None
    if thesis is not None:
        thesis["thesis_id"] = decision["thesis_id"]

    result = run_assessment(
        praman_conn, desk_conn, symbol=decision["symbol"], as_of_date=decision["as_of_date"],
        sector=(thesis or {}).get("sector"), thesis=thesis, rulebook=rulebook, costs=costs,
    )

    original_gate_results = decision["gate_results"]
    replayed_gate_results = result.gate_results_json()
    diff = []
    if result.state != decision["state"]:
        diff.append(f"state: original={decision['state']!r} replayed={result.state!r}")
    for gate in sorted(set(original_gate_results) | set(replayed_gate_results)):
        if original_gate_results.get(gate) != replayed_gate_results.get(gate):
            diff.append(f"{gate}: original={original_gate_results.get(gate)!r} replayed={replayed_gate_results.get(gate)!r}")

    praman_conn.close()
    desk_conn.close()

    return ReplayResult(
        decision_id=decision_id, matched=(len(diff) == 0), original_state=decision["state"],
        replayed_state=result.state, original_gate_results=original_gate_results,
        replayed_gate_results=replayed_gate_results, code_commit_matches=code_commit_matches, diff=diff,
    )
