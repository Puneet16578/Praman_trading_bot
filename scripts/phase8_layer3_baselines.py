"""Phase 8, Layer 3: five baselines on the identical 2026 hold-out set Layer 2 used.

1. Random            -- seeded uniform [0,1] score, no information used at all.
2. Naive threshold    -- flag if |return_1d| > 10% (round, pre-specified, not fit to this data).
3. Disclosure tier alone -- TRAIN-period (disclosure_tier, cap_band) collapse rate. The single
   strongest input per Phase 6/7b's own findings; the one to take seriously.
4. Deterministic classifier (rules, no agents) -- classify_event()'s own 5-class output, scored by
   its TRAIN-period (classification, cap_band) collapse rate. This IS what
   scripts/phase8_layer2_metrics.py already measured and reports as "the full agent system" --
   see the note below for why 4 and 5 are the same number, not two separately-run pipelines.
5. Full agent system  -- the real MultiAgentOrchestrator, Adversary included.

Baselines 4 and 5 are NOT independently re-run at full scale here. SynthesisAgent.render() calls
the exact same classify_event() rule regardless of whether the Adversary rejected zero, some, or
all of the evidentiary claims feeding it (a rejected claim removes that piece of evidence from the
report, it does not substitute a different classification rule) -- so GIVEN THE SAME THRESHOLDS,
the agent system's classification and the bare deterministic rule's classification are identical
by construction. Running the real orchestrator (~5.6s/event, ~17 hours for the full 10,850-event
hold-out) would remeasure a number already fixed by construction -- IF the thresholds matched.
They do not quite: the live orchestrator loads PRODUCTION thresholds (fit on the full available
history, correct for a live system), while this evaluation's baseline 4 uses the FROZEN,
train-only thresholds scripts/phase8_freeze_thresholds.py computed. A direct spot-check
(SPOT_CHECK_N real orchestrator runs, seeded) found exactly this: 99/100 matched, one mismatch
(CIEINDIA/2026-02-10) traced directly to the event's abs(return_20d) falling between the frozen
and production Mid-band medians (0.1195 vs 0.1161) -- the SAME logic, two different threshold
vintages, not a control-flow bug. Reported as a real, quantified sensitivity (~1% of events near a
band-median boundary can flip class depending on threshold vintage), not smoothed over.
"""
from __future__ import annotations
import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NAIVE_RETURN_THRESHOLD = 0.10
RANDOM_SEED = 7
SPOT_CHECK_N = 100
SPOT_CHECK_SEED = 99
PRIMARY_HORIZON = 90

ROOT = Path(__file__).resolve().parents[1]
PROD_CLASSIFICATIONS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
TRAIN_COLLAPSE_PATH = ROOT / "data" / "processed" / "collapse_rate_by_class.csv"
HOLDOUT_CLASS_PATH = ROOT / "data" / "processed" / "phase8_2026_classifications.csv"
HOLDOUT_OUTCOMES_PATH = ROOT / "data" / "processed" / "phase8_2026_outcomes.csv"
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "phase8_baseline_scores.csv"

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))

def load_train_rate_table(key_field: str) -> dict[tuple[str, str], float]:
    """TRAIN-period (key_field, cap_band) -> collapse rate at PRIMARY_HORIZON, joining
    event_classifications.csv (has disclosure_tier/classification/cap_band for every event, all
    years) against collapse_rate_by_class.csv (has the outcome labels, all years), restricted to
    event_date < 2026."""
    outcomes: dict[tuple[str, str], bool] = {}
    with open(TRAIN_COLLAPSE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            v = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if v == "":
                continue
            outcomes[(row["symbol"], row["event_date"])] = v == "True"

    cells: dict[tuple[str, str], list[bool]] = defaultdict(list)
    with open(PROD_CLASSIFICATIONS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                continue
            key = (row["symbol"], row["event_date"])
            if key not in outcomes:
                continue
            cells[(row[key_field], row["cap_band"])].append(outcomes[key])
    return {cell: sum(vals) / len(vals) for cell, vals in cells.items() if vals}

def load_holdout_joined() -> list[dict]:
    """One row per 2026 hold-out event with everything every baseline needs: classification,
    disclosure_tier, cap_band, return_1d, and the actual collapsed_{PRIMARY_HORIZON}d outcome."""
    class_by_key: dict[tuple[str, str], dict] = {}
    with open(HOLDOUT_CLASS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            class_by_key[(row["symbol"], row["event_date"])] = row

    return_by_key: dict[tuple[str, str], float] = {}
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["event_date"] >= "2026-01-01":
                return_by_key[(row["symbol"], row["event_date"])] = float(row["return_1d"])

    joined = []
    with open(HOLDOUT_OUTCOMES_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            actual_str = row[f"collapsed_{PRIMARY_HORIZON}d"]
            if actual_str == "":
                continue
            key = (row["symbol"], row["event_date"])
            cls_row = class_by_key.get(key)
            r1 = return_by_key.get(key)
            if cls_row is None or r1 is None:
                continue
            joined.append({
                "symbol": row["symbol"], "event_date": row["event_date"],
                "classification": row["classification"], "cap_band": row["cap_band"],
                "disclosure_tier": cls_row["disclosure_tier"], "return_1d": r1,
                "actual": actual_str == "True",
            })
    return joined

def score_baseline(events: list[dict], score_fn) -> list[dict]:
    return [{**e, "score": score_fn(e)} for e in events]

def brier(scored: list[dict]) -> float:
    return sum((x["score"] - (1.0 if x["actual"] else 0.0)) ** 2 for x in scored) / len(scored)

def precision_at_max_tier(scored: list[dict]) -> tuple[int, int, float]:
    """Same honest treatment as Layer 2: report precision over the full group tied at the max
    score, not an arbitrary 20-of-many-tied subsample, for baselines whose score is similarly
    coarse (2 and 3). Returns (hits, n, rate)."""
    max_score = max(x["score"] for x in scored)
    tied = [x for x in scored if x["score"] == max_score]
    hits = sum(1 for x in tied if x["actual"])
    return hits, len(tied), hits / len(tied) if tied else float("nan")

def spot_check_agent_vs_deterministic(sample_events: list[dict]) -> tuple[int, int, list[str]]:
    from src.bitemporal.connection import get_connection, init_db
    from src.config.settings import get_settings
    from src.agent.orchestrator import MultiAgentOrchestrator

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)
    orchestrator = MultiAgentOrchestrator()

    matches = 0
    mismatches: list[str] = []
    for e in sample_events:
        report = orchestrator.run_for_event(conn, e["symbol"], e["event_date"])
        if report.classification == e["classification"]:
            matches += 1
        else:
            mismatches.append(f"{e['symbol']}/{e['event_date']}: deterministic={e['classification']} agent={report.classification}")
    conn.close()
    return matches, len(sample_events), mismatches

def main() -> None:
    print(f"Loading TRAIN-period (disclosure_tier, cap_band) collapse rates for Baseline 3...")
    disclosure_scores = load_train_rate_table("disclosure_tier")
    print(f"  {len(disclosure_scores)} cells")
    print(f"Loading TRAIN-period (classification, cap_band) collapse rates for Baseline 4/5 (from Layer 2)...")
    classification_scores = load_train_rate_table("classification")
    print(f"  {len(classification_scores)} cells")

    holdout = load_holdout_joined()
    print(f"\n{len(holdout)} hold-out events with a known {PRIMARY_HORIZON}d outcome")

    rng = random.Random(RANDOM_SEED)
    baselines = {
        "1_random": score_baseline(holdout, lambda e: rng.random()),
        "2_naive_threshold_10pct": score_baseline(holdout, lambda e: 1.0 if abs(e["return_1d"]) > NAIVE_RETURN_THRESHOLD else 0.0),
        "3_disclosure_tier_alone": score_baseline(holdout, lambda e: disclosure_scores.get((e["disclosure_tier"], e["cap_band"]), 0.5)),
        "4_deterministic_classifier": score_baseline(holdout, lambda e: classification_scores.get((e["classification"], e["cap_band"]), 0.5)),
    }

    print(f"\n{'='*90}\nBASELINE COMPARISON (n={len(holdout)}, {PRIMARY_HORIZON}-session horizon, 2026 hold-out)\n{'='*90}")
    print(f"{'Baseline':32s} {'Brier':>8s} {'Precision(max tier)':>22s} {'n(max tier)':>12s}")
    results_summary = {}
    for name, scored in baselines.items():
        b = brier(scored)
        hits, n_tied, rate = precision_at_max_tier(scored)
        p, lo, hi = wilson_ci(hits, n_tied)
        print(f"{name:32s} {b:8.4f} {f'{hits}/{n_tied} = {100*rate:.1f}%':>22s} {n_tied:12d}   95% CI [{100*lo:.1f}%, {100*hi:.1f}%]")
        results_summary[name] = {"brier": b, "precision_hits": hits, "precision_n": n_tied, "precision_rate": rate}

    overall_rate = sum(1 for e in holdout if e["actual"]) / len(holdout)
    print(f"\nBase rate (unconditional collapse rate, whole hold-out): {100*overall_rate:.1f}% (n={len(holdout)})")
    print("Baseline 1 (random) and 2 (naive) Brier scores above show what 'no real information'")
    print("and 'a single hand-picked threshold' achieve on this exact data, for comparison.")

    print(f"\n{'='*90}\nSPOT-CHECK: does the full agent system (with Adversary) classify identically")
    print(f"to the bare deterministic rule, on a real {SPOT_CHECK_N}-event sample?\n{'='*90}")
    spot_rng = random.Random(SPOT_CHECK_SEED)
    spot_sample = spot_rng.sample(holdout, min(SPOT_CHECK_N, len(holdout)))
    matches, total, mismatches = spot_check_agent_vs_deterministic(spot_sample)
    print(f"{matches}/{total} matched")
    if mismatches:
        print("MISMATCHES (investigate, do not assume Baseline 4 == Baseline 5 if any appear):")
        for m in mismatches:
            print(f"  {m}")
    else:
        print("Zero mismatches -- Baseline 4 and Baseline 5 are confirmed identical on this sample, ")
        print("consistent with the by-construction argument in this script's module docstring.")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "event_date", "actual"] + list(baselines.keys()))
        by_key = {(e["symbol"], e["event_date"]): e["actual"] for e in holdout}
        score_by_key = {name: {(e["symbol"], e["event_date"]): e["score"] for e in scored} for name, scored in baselines.items()}
        for key, actual in by_key.items():
            writer.writerow([key[0], key[1], actual] + [score_by_key[name][key] for name in baselines])
    print(f"\nPersisted per-event baseline scores to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
