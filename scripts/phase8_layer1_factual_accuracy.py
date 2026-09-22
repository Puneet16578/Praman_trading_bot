"""Phase 8, Layer 1: factual accuracy of report generation across a large, seeded, real sample.

Scope decision (confirmed with user): this tests the report-generation/Adversary PIPELINE's own
correctness, not predictive generalization -- there is no train/test leakage risk in sampling from
any year, so this draws from the FULL 2019-2026 catalogue, not just the 2026 hold-out. Broadest
real-world coverage gives the best chance of surfacing a rare edge case.

Resumable by design (matching this project's established pattern for long-running real-data jobs,
e.g. the bhavcopy/announcement backfills): real measured cost is ~5.6s/event (dominated by
build_symbol_history being rebuilt fresh per tool call -- a known, accepted cost here, since
Layer 1 must exercise the REAL, unmodified production path; a caching shortcut in exactly the
layer whose job is "catch every fabrication" would be the wrong place to introduce a new class of
bug). ~2000 events therefore takes on the order of 3 hours -- run in the background, writes
progress incrementally, checks already-processed (symbol,event_date) pairs on restart.

Per CLAUDE.md: anything below 100% verified is a fabrication bug, reported individually with
cause, never averaged away.
"""
from __future__ import annotations
import csv
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.agent.orchestrator import MultiAgentOrchestrator

SEED = 42
SAMPLE_SIZE = 2000
CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "event_classifications.csv"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase8_layer1_claims.csv"
FAILURES_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase8_layer1_failures.csv"
PROGRESS_EVERY = 50

CLAIM_FIELDS = ["symbol", "event_date", "claim_id", "agent_role", "claim_type",
                "transcription_verdict", "derivation_verdict"]
FAILURE_FIELDS = ["symbol", "event_date", "claim_id", "agent_role", "check", "verdict", "detail"]

def claim_type_of(claim_id: str) -> str:
    return claim_id.split(":")[-1] if ":announcement:" not in claim_id else "announcement"

def already_processed_events() -> set[tuple[str, str]]:
    if not OUTPUT_PATH.exists():
        return set()
    done = set()
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add((row["symbol"], row["event_date"]))
    return done

def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    rng = random.Random(SEED)
    sample = rng.sample(all_rows, SAMPLE_SIZE)
    print(f"Sampled {SAMPLE_SIZE} events (seed={SEED}) from {len(all_rows)} catalogued events")

    done = already_processed_events()
    if done:
        print(f"Resuming: {len(done)} events already processed in a prior run")
    remaining = [r for r in sample if (r["symbol"], r["event_date"]) not in done]
    print(f"{len(remaining)} events remaining this run")

    orchestrator = MultiAgentOrchestrator()
    claims_out_exists = OUTPUT_PATH.exists()
    failures_out_exists = FAILURES_PATH.exists()
    claims_f = open(OUTPUT_PATH, "a", newline="", encoding="utf-8")
    failures_f = open(FAILURES_PATH, "a", newline="", encoding="utf-8")
    claims_writer = csv.DictWriter(claims_f, fieldnames=CLAIM_FIELDS)
    failures_writer = csv.DictWriter(failures_f, fieldnames=FAILURE_FIELDS)
    if not claims_out_exists:
        claims_writer.writeheader()
    if not failures_out_exists:
        failures_writer.writeheader()

    t0 = time.time()
    n_errors = 0
    for i, r in enumerate(remaining):
        symbol, event_date = r["symbol"], r["event_date"]
        try:
            report = orchestrator.run_for_event(conn, symbol, event_date)
        except Exception as exc:
            n_errors += 1
            failures_writer.writerow({"symbol": symbol, "event_date": event_date, "claim_id": "",
                                       "agent_role": "ORCHESTRATOR", "check": "orchestrator_exception",
                                       "verdict": "FAIL", "detail": f"{type(exc).__name__}: {exc}"})
            failures_f.flush()
            continue

        for claim in report.accepted_claims:
            v = claim["verification"]
            claims_writer.writerow({
                "symbol": symbol, "event_date": event_date, "claim_id": claim["claim_id"],
                "agent_role": claim["agent_role"], "claim_type": claim_type_of(claim["claim_id"]),
                "transcription_verdict": v.get("transcription", ""), "derivation_verdict": v.get("derivation", ""),
            })
            # An ACCEPTED claim must never show FAIL at any tier -- that would mean the Adversary's
            # own accept/reject control flow is broken (a claim that failed a check still reached
            # output). Checked here, not assumed.
            if v.get("transcription") == "FAIL" or v.get("derivation") == "FAIL":
                failures_writer.writerow({"symbol": symbol, "event_date": event_date,
                                           "claim_id": claim["claim_id"], "agent_role": claim["agent_role"],
                                           "check": "accepted_claim_control_flow", "verdict": "FAIL",
                                           "detail": f"Claim reached accepted_claims with a FAIL verification: {v}"})

        for rejected in report.rejected_claims:
            # Rejected claims are individually recorded too -- not a failure of THIS layer's
            # accuracy claim (rejection is the Adversary working correctly), but tracked so the
            # rate and cause of real rejections on real data is visible, not silently discarded.
            matching_findings = [f for f in report.adversary_findings if f["claim_id"] == rejected["claim_id"] and f["verdict"] == "FAIL"]
            for finding in matching_findings:
                failures_writer.writerow({"symbol": symbol, "event_date": event_date,
                                           "claim_id": rejected["claim_id"], "agent_role": rejected["agent_role"],
                                           "check": finding["check"], "verdict": "FAIL_REJECTED_CORRECTLY",
                                           "detail": finding["detail"]})

        claims_f.flush()
        failures_f.flush()

        if (i + 1) % PROGRESS_EVERY == 0:
            elapsed = time.time() - t0
            rate = elapsed / (i + 1)
            remaining_est = rate * (len(remaining) - i - 1)
            print(f"  ...{i + 1}/{len(remaining)} this run, {elapsed:.0f}s elapsed, "
                  f"~{remaining_est/60:.0f} min remaining, {n_errors} orchestrator exceptions so far")

    claims_f.close()
    failures_f.close()
    print(f"Done. {len(remaining)} events processed this run, {n_errors} orchestrator exceptions.")
    print(f"Claims: {OUTPUT_PATH}")
    print(f"Failures/rejections log: {FAILURES_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
