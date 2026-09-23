"""P8-007 scoping investigation (measurement only -- no fixes applied here).

For every symbol in the 96 split/bonus-shape hits (scripts/phase10_scan_split_bonus_shapes.py),
checks:
  1. ETF classification against NSE's live /api/etf list (current snapshot).
  2. For non-ETF-list symbols: queries NSE's live, symbol-specific corporate-actions endpoint
     (confirmed working: /api/corporates-corporateActions?symbol=X&from_date=..&to_date=..) for a
     real action near the event date, and separately tests parse_subject_ratio on whatever real
     subject text comes back -- this distinguishes "the fetch/subject exists but our parser can't
     read it" from "no real action exists at all (likely a genuine price move)."
"""
from __future__ import annotations
import csv
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings
from src.ingestion.nse_market_data.asm import session_with_cookie
from src.ingestion.nse_market_data.corporate_actions import parse_subject_ratio

TOLERANCE_PP = 2.0
TARGET_SHAPES_PCT = [-33.3, -50.0, -66.7, -75.0, -80.0, -83.3, -90.0]
ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
ETF_LIST_PATH = ROOT / "data" / "raw" / "nse_etf_list_current.json"
DELAY_SECONDS = 0.4


def matches_target_shape(pct: float) -> float | None:
    for shape in TARGET_SHAPES_PCT:
        if abs(pct - shape) <= TOLERANCE_PP:
            return shape
    return None


def load_hits() -> list[dict]:
    hits = []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r1 = row["return_1d"]
            if r1 in ("", "None"):
                continue
            pct = float(r1) * 100
            shape = matches_target_shape(pct)
            if shape is None:
                continue
            hits.append({"symbol": row["symbol"], "event_date": row["event_date"],
                         "return_1d_pct": pct, "matched_shape_pct": shape})
    return hits


def query_symbol_actions(session, symbol: str, event_date: str) -> list[dict]:
    ev = date.fromisoformat(event_date)
    frm = ev - timedelta(days=45)
    to = ev + timedelta(days=45)
    try:
        r = session.get("https://www.nseindia.com/api/corporates-corporateActions",
                         params={"index": "equities", "symbol": symbol,
                                 "from_date": frm.strftime("%d-%m-%Y"), "to_date": to.strftime("%d-%m-%Y")},
                         timeout=20)
        if r.status_code != 200:
            return [{"_error": f"status={r.status_code}"}]
        return r.json()
    except Exception as exc:
        return [{"_error": str(exc)}]


def main() -> None:
    etf_list = set(json.load(open(ETF_LIST_PATH, encoding="utf-8")))
    hits = load_hits()
    print(f"{len(hits)} total hits, {len(set(h['symbol'] for h in hits))} unique symbols")

    session = session_with_cookie()
    results = []
    seen_symbols: dict[str, list] = {}

    for h in hits:
        symbol, event_date = h["symbol"], h["event_date"]
        is_etf_confirmed = symbol in etf_list

        if is_etf_confirmed:
            results.append({**h, "classification": "ETF_API_CONFIRMED", "detail": ""})
            continue

        # Query live, symbol-specific corporate actions (cache per symbol to avoid duplicate calls
        # across multiple hit-dates for the same symbol)
        if symbol not in seen_symbols:
            actions = query_symbol_actions(session, symbol, event_date)
            seen_symbols[symbol] = actions
            time.sleep(DELAY_SECONDS)
        else:
            actions = seen_symbols[symbol]

        if actions and "_error" in actions[0]:
            results.append({**h, "classification": "QUERY_ERROR", "detail": actions[0]["_error"]})
            continue

        ev = date.fromisoformat(event_date)
        near_actions = []
        for a in actions:
            try:
                ex = datetime.strptime(a["exDate"].strip(), "%d-%b-%Y").date()
            except Exception:
                continue
            if abs((ex - ev).days) <= 3:
                near_actions.append(a)

        if not near_actions:
            results.append({**h, "classification": "NO_ACTION_FOUND_LIVE", "detail": "genuine price move candidate"})
            continue

        for a in near_actions:
            subj = a.get("subject", "")
            parsed = parse_subject_ratio(subj)
            if parsed:
                results.append({**h, "classification": "ACTION_FOUND_PARSER_WOULD_SUCCEED",
                                 "detail": f"subject={subj!r} parsed={parsed} -- fetch/parse OK, drop must be tier/announcement-matching or DB write"})
            else:
                results.append({**h, "classification": "ACTION_FOUND_PARSER_FAILS",
                                 "detail": f"subject={subj!r} -- parse_subject_ratio returned None, this is the drop point"})

    # Summary
    from collections import Counter
    counts = Counter(r["classification"] for r in results)
    print("\n=== CLASSIFICATION SUMMARY ===")
    for k, v in counts.most_common():
        print(f"  {k}: {v}")

    print("\n=== FULL DETAIL ===")
    for r in results:
        print(f"  {r['symbol']:16s} {r['event_date']}  {r['classification']:32s} {r['detail']}")

    out_path = ROOT / "data" / "raw" / "phase10_p8007_investigation.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    main()
