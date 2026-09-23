"""Amendment 4 prep round 2, item 1: diagnose WHY HOLD-OUT's fully-elapsed missing-outcome rate
(10.80%) is so much higher than TRAIN's (1.67%) before setting any missing-data threshold from it.

Exact mechanism, stated precisely (not assumed): `compute_outcome_labels.py`'s `compute_outcome`
computes `forward_return_90d`/`collapsed` from `idx = bisect_left(hist.trading_days, event_date)`,
`fwd_idx = idx + 90` -- this is the SYMBOL'S OWN 90th REAL TRADED SESSION after event_date (EQ
series only, per `build_symbol_history`'s default), NOT the 90th GLOBAL calendar session and NOT
a 90-calendar-day window. "Fully elapsed" in this project's own measurement
(scripts/phase10_amendment4_missing_outcomes.py) means the GLOBAL calendar (market_index.csv) has
90+ sessions after event_date -- a DIFFERENT, looser condition than the symbol's own 90th session
actually having occurred. The gap between these two conditions is exactly what this script tests.

Two candidate explanations, each tested directly against real data:
  (a) BOUNDARY ARTIFACT -- a symbol trading slightly less densely than the global index (missing
      even a few real sessions) needs MORE calendar time than 90 global sessions to accumulate its
      own 90 REAL sessions. Events sitting close to the data's true end don't have that extra
      calendar slack yet, even though the crude "global has 90 sessions" gate already passed --
      this affects any population near ITS OWN contemporaneous data end, not something specific to
      2026.
  (b) SERIES MOVE -- this project's own ingestion (`build_symbol_history`'s default `series="EQ"`)
      only looks at EQ rows. A stock moved to trade-for-trade settlement (BE/BZ) leaves the EQ
      series while continuing to trade -- exactly the kind of stock a surveillance/forensic
      classifier disproportionately flags. Its EQ trading_days list stops abruptly at the
      series-change date, mimicking "delisted" in the missing-outcome measurement when the security
      never actually stopped trading.
"""
from __future__ import annotations
import bisect
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"
OUTCOME_LABELS_PATH = ROOT / "data" / "processed" / "outcome_labels.csv"
TRAIN_CUTOFF = "2026-01-01"
HORIZON = 90
BUFFER_SESSIONS = 30          # extra global sessions of slack required beyond naive t+90
TRUNCATION_DATE = "2024-06-30"
NEAR_BOUNDARY_RANGE = (0, 30)   # sessions of buffer before the truncation, inclusive
SAFELY_EARLIER_RANGE = (90, 999999)


def load_global_days() -> list[str]:
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        return [r["date"] for r in csv.DictReader(f)]


def load_outcomes() -> list[dict]:
    with open(OUTCOME_LABELS_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def part_a_boundary_artifact(global_days: list[str], outcomes: list[dict]) -> None:
    print("=" * 90)
    print("PART (a): BOUNDARY ARTIFACT TEST")
    print("=" * 90)
    print(f"Outcome mechanism (stated precisely, from compute_outcome_labels.py's own code):")
    print(f"  forward_return_90d/collapsed require the SYMBOL'S OWN 90th real EQ-series traded")
    print(f"  session after event_date (bisect index idx+90 into hist.trading_days) -- NOT the")
    print(f"  90th GLOBAL calendar session, NOT a 90-calendar-day window.")
    print(f"  'Fully elapsed' (this project's own measurement) means the GLOBAL calendar has 90+")
    print(f"  sessions after event_date -- a looser, different condition.\n")

    def bucket(events: list[dict], min_buffer: int, max_buffer: int | None) -> tuple[int, int]:
        fully_elapsed_n = 0
        lacking_n = 0
        for r in events:
            idx = bisect.bisect_left(global_days, r["event_date"])
            if not (idx < len(global_days) and global_days[idx] == r["event_date"]):
                continue
            t90_idx = idx + HORIZON
            if t90_idx >= len(global_days):
                continue  # not fully elapsed at all
            buffer = (len(global_days) - 1) - t90_idx
            if buffer < min_buffer:
                continue
            if max_buffer is not None and buffer > max_buffer:
                continue
            fully_elapsed_n += 1
            if r["forward_return_90d"] in ("", "None"):
                lacking_n += 1
        return fully_elapsed_n, lacking_n

    holdout = [r for r in outcomes if r["event_date"] >= TRAIN_CUTOFF]
    train = [r for r in outcomes if r["event_date"] < TRAIN_CUTOFF]

    fe_all, lack_all = bucket(holdout, 0, None)
    fe_buf, lack_buf = bucket(holdout, BUFFER_SESSIONS, None)
    print(f"HOLD-OUT, raw fully-elapsed (buffer>=0): n={fe_all}  lacking={lack_all}  "
          f"rate={100*lack_all/fe_all:.3f}%")
    print(f"HOLD-OUT, buffered fully-elapsed (buffer>={BUFFER_SESSIONS} sessions beyond naive t+90): "
          f"n={fe_buf}  lacking={lack_buf}  rate={100*lack_buf/fe_buf:.3f}%" if fe_buf else
          "HOLD-OUT, buffered: no events in this range")

    print(f"\n--- TRAIN replicate: artificial truncation at {TRUNCATION_DATE} ---")
    trunc_idx = bisect.bisect_right(global_days, TRUNCATION_DATE) - 1
    print(f"Truncation date {TRUNCATION_DATE} -> real global index {trunc_idx} "
          f"({global_days[trunc_idx]}), {len(global_days) - 1 - trunc_idx} real sessions exist "
          f"after it in the actual (untruncated) data.")

    def buffer_before_truncation(event_date: str) -> int | None:
        idx = bisect.bisect_left(global_days, event_date)
        if not (idx < len(global_days) and global_days[idx] == event_date):
            return None
        t90_idx = idx + HORIZON
        if t90_idx > trunc_idx:
            return None  # window doesn't even naively fit before the truncation
        return trunc_idx - t90_idx

    near_boundary_events = [r for r in train if r["event_date"] < TRUNCATION_DATE
                             and (b := buffer_before_truncation(r["event_date"])) is not None
                             and NEAR_BOUNDARY_RANGE[0] <= b <= NEAR_BOUNDARY_RANGE[1]]
    safely_earlier_events = [r for r in train if r["event_date"] < TRUNCATION_DATE
                              and (b := buffer_before_truncation(r["event_date"])) is not None
                              and SAFELY_EARLIER_RANGE[0] <= b <= SAFELY_EARLIER_RANGE[1]]
    print(f"Near-boundary TRAIN events (buffer {NEAR_BOUNDARY_RANGE} sessions before truncation): "
          f"n={len(near_boundary_events)}")
    print(f"Safely-earlier TRAIN events (buffer {SAFELY_EARLIER_RANGE} sessions before truncation): "
          f"n={len(safely_earlier_events)}")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    candidate_symbols = {r["symbol"] for r in near_boundary_events + safely_earlier_events}
    placeholders = ",".join("?" * len(candidate_symbols))
    rows = conn.execute(
        f"SELECT symbol, event_date FROM bhavcopy WHERE series='EQ' AND event_date <= ? "
        f"AND symbol IN ({placeholders}) ORDER BY symbol, event_date",
        (TRUNCATION_DATE, *candidate_symbols),
    ).fetchall()
    truncated_days: dict[str, list[str]] = {}
    for r in rows:
        truncated_days.setdefault(r["symbol"], []).append(r["event_date"])

    def missing_under_truncation(events: list[dict]) -> tuple[int, int]:
        n, lacking = 0, 0
        for r in events:
            days = truncated_days.get(r["symbol"], [])
            idx = bisect.bisect_left(days, r["event_date"])
            if not (idx < len(days) and days[idx] == r["event_date"]):
                continue  # event_date itself not in the truncated trading calendar (shouldn't happen)
            n += 1
            if idx + HORIZON >= len(days):
                lacking += 1
        return n, lacking

    n_near, lack_near = missing_under_truncation(near_boundary_events)
    n_safe, lack_safe = missing_under_truncation(safely_earlier_events)
    print(f"\nUnder the {TRUNCATION_DATE} truncation (as if that were the current data end):")
    print(f"  Near-boundary: n={n_near}  lacking={lack_near}  "
          f"rate={100*lack_near/n_near:.3f}%" if n_near else "  Near-boundary: n=0")
    print(f"  Safely-earlier: n={n_safe}  lacking={lack_safe}  "
          f"rate={100*lack_safe/n_safe:.3f}%" if n_safe else "  Safely-earlier: n=0")
    conn.close()


def part_b_series_moves(outcomes: list[dict]) -> None:
    print("\n" + "=" * 90)
    print("PART (b): SERIES MOVE TEST (BE/BZ trade-for-trade)")
    print("=" * 90)

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    global_days = load_global_days()
    holdout_lacking = []
    for r in outcomes:
        if r["event_date"] < TRAIN_CUTOFF:
            continue
        idx = bisect.bisect_left(global_days, r["event_date"])
        if not (idx < len(global_days) and global_days[idx] == r["event_date"]):
            continue
        if idx + HORIZON >= len(global_days):
            continue  # not fully elapsed
        if r["forward_return_90d"] not in ("", "None"):
            continue
        holdout_lacking.append(r)

    print(f"HOLD-OUT fully-elapsed, lacking-outcome events: {len(holdout_lacking)}")

    symbols = sorted({r["symbol"] for r in holdout_lacking})
    placeholders = ",".join("?" * len(symbols))
    eq_last = conn.execute(
        f"SELECT symbol, MAX(event_date) hi FROM bhavcopy WHERE series='EQ' AND symbol IN "
        f"({placeholders}) GROUP BY symbol", tuple(symbols),
    ).fetchall()
    eq_last_date = {r["symbol"]: r["hi"] for r in eq_last}

    non_eq_after = conn.execute(
        f"SELECT symbol, series, MIN(event_date) lo, MAX(event_date) hi, COUNT(*) n FROM bhavcopy "
        f"WHERE series IN ('BE','BZ') AND symbol IN ({placeholders}) GROUP BY symbol, series",
        tuple(symbols),
    ).fetchall()
    by_symbol_non_eq: dict[str, list] = {}
    for r in non_eq_after:
        by_symbol_non_eq.setdefault(r["symbol"], []).append(dict(r))

    moved_to_be_bz = []
    for r in holdout_lacking:
        sym = r["symbol"]
        eq_last_d = eq_last_date.get(sym)
        for rec in by_symbol_non_eq.get(sym, []):
            if eq_last_d is not None and rec["hi"] > eq_last_d:
                moved_to_be_bz.append((r, rec))
                break

    print(f"Of those, symbol has BE/BZ rows AFTER its own last EQ date: {len(moved_to_be_bz)} "
          f"({100*len(moved_to_be_bz)/len(holdout_lacking):.2f}% of the {len(holdout_lacking)})")
    print(f"\nSample (up to 20):")
    for r, rec in moved_to_be_bz[:20]:
        print(f"  {r['symbol']:16s} event={r['event_date']}  EQ_last={eq_last_date[r['symbol']]}  "
              f"-> {rec['series']} {rec['lo']}..{rec['hi']} (n={rec['n']})")

    conn.close()
    return moved_to_be_bz, holdout_lacking


def main() -> None:
    global_days = load_global_days()
    outcomes = load_outcomes()
    part_a_boundary_artifact(global_days, outcomes)
    part_b_series_moves(outcomes)


if __name__ == "__main__":
    main()
