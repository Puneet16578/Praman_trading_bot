"""Amendment 4 prep, Part 1 item 3: among catalogued events whose 90-session window has FULLY
ELAPSED on the GLOBAL trading calendar (market_index.csv) by the data end, what share lacks a
computable 90-session outcome (`forward_return_90d` blank in outcome_labels.csv), and why --
rename, delisting, suspension, or a gap in this project's own bhavcopy ingestion -- reported for
TRAIN and HOLD-OUT separately.

Phase 8's robustness check (docs/phase8_robustness_checks.md, Addition 4) found 770 HOLD-OUT
events (16.1% of the 4,795 with no computable outcome under any label) where "the global calendar
has 90+ sessions after event_date, but this symbol's own trading history ends first" -- flagged
as a bare "possible delisting/suspension" heuristic, explicitly because this project "has no
direct delisting-event feed." This script sharpens that heuristic using evidence gathered this
session: the ISIN-based rename map (this file's own item-1 sibling script) can now separate
"the symbol's own history ends because it was renamed" (not missing at all -- filed under a
different symbol) from a genuine stop, and market_index.csv's own `n_symbols_contributing`
column can flag a whole-day, multi-symbol ingestion gap distinctly from a single symbol's own
trading halt.

Why this matters for Amendment 2: it declares the forward evaluation COMPROMISED above 5% of
events missing a 90-session outcome. If the NORMAL historical rate of "fully elapsed but no
outcome" is itself close to 5%, that threshold could trip for reasons that have nothing to do
with the hypothesis under test (renames and routine suspensions happen every year, at some
baseline rate, regardless of anything this project is trying to measure).

Classification waterfall, in order, each a criterion actually checked against real data, not
assumed:
  1. RENAME -- the symbol is the "old" side of a real ISIN-sharing pair (this file's own item-1
     detection), and a successor symbol's first bhavcopy date falls within 30 calendar days of
     this symbol's own last bhavcopy date. Not missing at all -- filed under a different symbol.
  2. SUSPENSION -- not a rename, and the symbol's own last bhavcopy date is recent (within 10
     trading days of the global calendar's own last date) -- it did not stop, so a missing
     90-session outcome must come from an internal gap (missing individual sessions) somewhere
     inside its own history, consistent with a temporary halt rather than a full stop.
  3. DATA GAP -- not a rename, symbol did stop early, but its stop date coincides with a
     whole-market low-coverage day (market_index.csv's n_symbols_contributing drops sharply,
     i.e. many OTHER symbols are also missing that day) -- evidence of an ingestion-side gap,
     not a symbol-specific event.
  4. DELISTING -- the residual: not a rename, stopped early, and no evidence of a whole-market
     ingestion gap at its stop date. This project has no delisting-notice feed (Addition 4's own
     limitation still holds) -- reported as the best-supported remaining explanation, not as an
     independently confirmed fact.
"""
from __future__ import annotations
import bisect
import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
OUTCOME_LABELS_PATH = ROOT / "data" / "processed" / "outcome_labels.csv"
ISIN_MAP_PATH = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
TRAIN_CUTOFF = "2026-01-01"
RENAME_GAP_DAYS = 30
SUSPENSION_RECENCY_DAYS = 10  # trading days, not calendar days
LOW_COVERAGE_FRACTION = 0.90  # a day where n_symbols_contributing drops below 90% of the
                               # trailing median is flagged as a whole-market ingestion gap


def load_global_days() -> list[str]:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        return [r["date"] for r in csv.DictReader(f)]


def load_low_coverage_days(global_days: list[str]) -> set[str]:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    counts = [int(r["n_symbols_contributing"]) for r in rows]
    low_coverage = set()
    window = 20
    for i, r in enumerate(rows):
        lo = max(0, i - window)
        trailing = counts[lo:i] if i > 0 else counts[i:i + window]
        if not trailing:
            continue
        median = sorted(trailing)[len(trailing) // 2]
        if median > 0 and counts[i] < LOW_COVERAGE_FRACTION * median:
            low_coverage.add(r["date"])
    return low_coverage


def load_isin_groups() -> dict[str, list[str]]:
    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))
    by_isin: dict[str, list[str]] = defaultdict(list)
    for sym, isin in isin_map.items():
        by_isin[isin].append(sym)
    return {isin: syms for isin, syms in by_isin.items() if len(syms) > 1}


def main() -> None:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    global_days = load_global_days()
    data_end = global_days[-1]
    print(f"Global calendar: {global_days[0]} .. {data_end} ({len(global_days)} sessions)")

    low_coverage_days = load_low_coverage_days(global_days)
    print(f"Whole-market low-coverage days flagged: {len(low_coverage_days)} -> {sorted(low_coverage_days)}")

    with open(OUTCOME_LABELS_PATH, encoding="utf-8") as f:
        outcomes = list(csv.DictReader(f))
    print(f"Loaded {len(outcomes)} outcome rows")

    # fully elapsed: global calendar has >=90 sessions strictly after event_date
    fully_elapsed = []
    for row in outcomes:
        idx = bisect.bisect_left(global_days, row["event_date"])
        if idx < len(global_days) and global_days[idx] == row["event_date"] and idx + 90 < len(global_days):
            fully_elapsed.append(row)
    print(f"\nFully elapsed on the global calendar: {len(fully_elapsed)} of {len(outcomes)}")

    lacking = [r for r in fully_elapsed if r["forward_return_90d"] in ("", "None")]
    print(f"Fully elapsed but lacking a 90-session outcome: {len(lacking)} "
          f"({100 * len(lacking) / len(fully_elapsed):.2f}% of fully-elapsed)")

    # symbols involved -- get bhavcopy date ranges only for these (not all 3000+ symbols)
    affected_symbols = {r["symbol"] for r in lacking}
    placeholders = ",".join("?" * len(affected_symbols))
    bh_rows = conn.execute(
        f"SELECT symbol, MIN(event_date) lo, MAX(event_date) hi FROM bhavcopy "
        f"WHERE series='EQ' AND symbol IN ({placeholders}) GROUP BY symbol",
        tuple(affected_symbols),
    ).fetchall()
    date_range = {r["symbol"]: (r["lo"], r["hi"]) for r in bh_rows}

    isin_groups = load_isin_groups()
    isin_map = json.load(open(ISIN_MAP_PATH, encoding="utf-8"))

    def classify(symbol: str, last_date: str) -> str:
        isin = isin_map.get(symbol)
        if isin is not None:
            for sibling in isin_groups.get(isin, []):
                if sibling == symbol:
                    continue
                succ_start = successor_starts.get(sibling)
                if succ_start is None:
                    continue
                gap = (date.fromisoformat(succ_start) - date.fromisoformat(last_date)).days
                if 0 <= gap <= RENAME_GAP_DAYS:
                    return "RENAME"
        # recency: is this symbol still trading near the global data end?
        idx_last = bisect.bisect_left(global_days, last_date)
        if idx_last < len(global_days) and global_days[idx_last] == last_date:
            sessions_from_end = (len(global_days) - 1) - idx_last
        else:
            sessions_from_end = 9999
        if sessions_from_end <= SUSPENSION_RECENCY_DAYS:
            return "SUSPENSION"
        if last_date in low_coverage_days:
            return "DATA_GAP"
        return "DELISTING"

    # precompute successor start dates for ANY symbol (needed by classify's sibling lookup)
    all_group_symbols = {s for syms in isin_groups.values() for s in syms}
    placeholders2 = ",".join("?" * len(all_group_symbols)) if all_group_symbols else "''"
    succ_rows = conn.execute(
        f"SELECT symbol, MIN(event_date) lo FROM bhavcopy WHERE series='EQ' AND symbol IN "
        f"({placeholders2}) GROUP BY symbol", tuple(all_group_symbols),
    ).fetchall() if all_group_symbols else []
    successor_starts = {r["symbol"]: r["lo"] for r in succ_rows}

    causes: dict[str, dict[str, int]] = {"TRAIN": defaultdict(int), "HOLD-OUT": defaultdict(int)}
    fully_elapsed_counts = {"TRAIN": 0, "HOLD-OUT": 0}
    for r in fully_elapsed:
        pop = "TRAIN" if r["event_date"] < TRAIN_CUTOFF else "HOLD-OUT"
        fully_elapsed_counts[pop] += 1
    for r in lacking:
        pop = "TRAIN" if r["event_date"] < TRAIN_CUTOFF else "HOLD-OUT"
        symbol = r["symbol"]
        _, last_date = date_range.get(symbol, (None, r["event_date"]))
        cause = classify(symbol, last_date)
        causes[pop][cause] += 1

    for pop in ("TRAIN", "HOLD-OUT"):
        total_fe = fully_elapsed_counts[pop]
        total_lacking = sum(causes[pop].values())
        print(f"\n=== {pop} ===")
        print(f"Fully elapsed: {total_fe}")
        print(f"Lacking a 90-session outcome: {total_lacking} ({100 * total_lacking / total_fe:.3f}% of fully-elapsed)")
        for cause, n in sorted(causes[pop].items(), key=lambda kv: -kv[1]):
            print(f"  {cause:12s} {n:5d}  ({100 * n / total_fe:.3f}% of fully-elapsed, "
                  f"{100 * n / total_lacking:.1f}% of lacking)")
        rename_n = causes[pop].get("RENAME", 0)
        print(f"  -> RENAME specifically: {100 * rename_n / total_fe:.3f}% of fully-elapsed {pop} events")

    conn.close()


if __name__ == "__main__":
    main()
