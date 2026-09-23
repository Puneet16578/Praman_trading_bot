"""Phase 10 pre-registration Amendment 3, pre-specified check: scan catalogued events for one-day
returns shaped like a common, unadjusted split/bonus ratio -- the signature of a corporate action
this project's store does not yet know about. Without the real action ingested, `_return()`
(src/signals/event_catalogue.py) computes an adjustment factor of 1.0 for that date, so the
"adjusted" return is really the raw, unadjusted one -- exactly this shape.

Target shapes (a bonus/split of ratio N-for-M makes the raw one-day return read as
1 - M/N, if unadjusted): -33.3% (3-for-2), -50% (2-for-1), -66.7% (3-for-1), -75% (4-for-1),
-80% (5-for-1), -83.3% (6-for-1), -90% (10-for-1) -- the seven pre-specified in
docs/phase10_preregistration_amendment3.md, tolerance +/-2 percentage points, chosen and fixed
before any forward data exists.

This inspects PRICES (return_1d), never OUTCOMES (the relative_t0_primary label) -- it is a data-
quality check on inputs, not an interim look at results, and is safe to run against historical
data as a mechanism check for exactly that reason.

For every hit: cross-reference the real `corporate_actions` table for a BONUS/SPLIT row for that
symbol within a window of the event date.
  - A matching action EXISTS but the return still shows the raw shape -> the action is in the
    store but the adjustment did not apply -- a DIFFERENT, more serious problem than "missing
    action" (an adjustment bug), flagged distinctly.
  - No matching action -> a candidate MISSED action. Investigated directly against the live
    corporate-actions endpoint for that exact symbol/date, not assumed from the shape alone: real
    corporate actions are ingested via the normal idempotent path and the finding is reported;
    a genuine large price move with no real corporate action behind it is left untouched and
    reported as such, explicitly, not silently dropped.
"""
from __future__ import annotations
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

TOLERANCE_PP = 2.0
TARGET_SHAPES_PCT = [-33.3, -50.0, -66.7, -75.0, -80.0, -83.3, -90.0]  # percent, i.e. return*100

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"


def matches_target_shape(return_1d_pct: float) -> float | None:
    for shape in TARGET_SHAPES_PCT:
        if abs(return_1d_pct - shape) <= TOLERANCE_PP:
            return shape
    return None


def find_nearby_action(conn, symbol: str, event_date: str, window_days: int = 10) -> dict | None:
    ev = date.fromisoformat(event_date)
    lo = (ev - timedelta(days=window_days)).isoformat()
    hi = (ev + timedelta(days=window_days)).isoformat()
    row = conn.execute(
        "SELECT event_date, action_type, ratio_numerator, ratio_denominator, knowledge_date "
        "FROM corporate_actions WHERE symbol=? AND action_type IN ('BONUS','SPLIT') "
        "AND event_date BETWEEN ? AND ? ORDER BY event_date LIMIT 1",
        (symbol, lo, hi),
    ).fetchone()
    return dict(row) if row else None


def scan(event_dates_range: tuple[str, str] | None = None) -> list[dict]:
    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    hits = []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if event_dates_range and not (event_dates_range[0] <= row["event_date"] <= event_dates_range[1]):
                continue
            r1 = row["return_1d"]
            if r1 in ("", "None"):
                continue
            pct = float(r1) * 100
            shape = matches_target_shape(pct)
            if shape is None:
                continue
            action = find_nearby_action(conn, row["symbol"], row["event_date"])
            hits.append({
                "symbol": row["symbol"], "event_date": row["event_date"],
                "return_1d_pct": pct, "matched_shape_pct": shape,
                "existing_action": action,
            })
    conn.close()
    return hits


def main() -> None:
    print("MECHANISM CHECK (run against existing historical catalogue data -- forward window does "
          "not exist yet). Inspects prices (return_1d), not outcomes.")
    hits = scan()
    print(f"\n{len(hits)} events with return_1d within {TOLERANCE_PP}pp of a target split/bonus shape "
          f"{TARGET_SHAPES_PCT}")

    already_explained = [h for h in hits if h["existing_action"] is not None]
    unexplained = [h for h in hits if h["existing_action"] is None]
    print(f"  Already explained by an existing BONUS/SPLIT record: {len(already_explained)}")
    print(f"  UNEXPLAINED (no matching action in the store): {len(unexplained)}")

    print("\n-- Unexplained hits (candidates for a missed action OR a genuine large move) --")
    for h in unexplained[:100]:
        print(f"  {h['symbol']:16s} {h['event_date']}  return_1d={h['return_1d_pct']:+.2f}%  "
              f"nearest target shape={h['matched_shape_pct']:+.1f}%")

    print("\n-- Explained hits (existing action found nearby -- adjustment SHOULD have applied; "
          "if return_1d still shows the raw shape, this is a separate adjustment-bug candidate, "
          "not a missing-action one) --")
    for h in already_explained[:20]:
        a = h["existing_action"]
        print(f"  {h['symbol']:16s} {h['event_date']}  return_1d={h['return_1d_pct']:+.2f}%  "
              f"existing_action={a['action_type']} {a['ratio_numerator']}:{a['ratio_denominator']} "
              f"on {a['event_date']} (knowledge_date={a['knowledge_date']})")


if __name__ == "__main__":
    main()
