"""Read-only reproduction of the original A/B/C section 8 event-day tables.

Only EQ close-to-close inputs through each processed session are queried. Corporate
actions are selected as known on that session. No writes, outcomes, or later prices.
This preserves the original descriptive peer convention; the follow-up report's
repaired peer measure is implemented separately in a later item.
"""
from __future__ import annotations

import csv
import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CATALOGUE = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
START = "2019-10-01"
END = "2025-12-31"
PEER_SESSIONS = 250
PEER_COUNT = 20


def _rows_asof(conn: sqlite3.Connection, sql: str, params: tuple) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))


def _events(path: Path) -> dict[str, list[dict]]:
    by_date: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            day = row["event_date"]
            if START <= day <= END:
                by_date[day].append({"symbol": row["symbol"], "return_1d": float(row["return_1d"])})
    return dict(sorted(by_date.items()))


def _calendar(conn: sqlite3.Connection, after: str, through: str) -> list[str]:
    # Both bounds are deliberately on the source query; no post-D dates are read.
    return [row[0] for row in _rows_asof(
        conn,
        "SELECT DISTINCT event_date FROM bhavcopy "
        "WHERE series='EQ' AND event_date>=? AND event_date>? AND event_date<=? "
        "AND knowledge_date<=? ORDER BY event_date",
        (START, after, through, through),
    )]


def _bars_for_day(conn: sqlite3.Connection, day: str) -> dict[str, float]:
    # A bar vintage is visible only if known by its own bar date, matching the original
    # section 8 description of historical return construction.
    rows = _rows_asof(
        conn,
        "SELECT symbol, close_price, knowledge_date FROM bhavcopy "
        "WHERE series='EQ' AND event_date=? AND knowledge_date<=? ORDER BY symbol, knowledge_date DESC, row_id DESC",
        (day, day),
    )
    result: dict[str, float] = {}
    for row in rows:
        result.setdefault(row["symbol"], float(row["close_price"]))
    return result


def _actions_asof(conn: sqlite3.Connection, day: str) -> dict[str, list[dict]]:
    rows = _rows_asof(
        conn,
        "SELECT symbol, action_type, event_date, knowledge_date, ratio_numerator, ratio_denominator "
        "FROM corporate_actions WHERE event_date<=? AND knowledge_date<=? "
        "ORDER BY symbol, action_type, event_date, knowledge_date, row_id",
        (day, day),
    )
    latest: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        latest[(row["symbol"], row["action_type"], row["event_date"])] = dict(row)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for (symbol, _kind, _date), row in latest.items():
        grouped[symbol].append(row)
    return grouped


def _return(previous: tuple[str, float] | None, day: str, close: float,
            actions: Iterable[dict]) -> float | None:
    if previous is None or previous[1] <= 0 or close <= 0:
        return None
    prior_day, prior_close = previous
    factor = 1.0
    for action in actions:
        ex_date = action["event_date"]
        if not prior_day < ex_date <= day:
            continue
        kind = action["action_type"]
        if kind in {"DEMERGER", "CAPITAL_REDUCTION", "RIGHTS", "RATIO_CONFLICT"}:
            return None
        numerator, denominator = action["ratio_numerator"], action["ratio_denominator"]
        if numerator is None or denominator in (None, 0):
            continue
        if kind == "BONUS":
            factor *= (float(numerator) + float(denominator)) / float(denominator)
        elif kind == "SPLIT":
            factor *= float(numerator) / float(denominator)
    return close * factor / prior_close - 1.0


def _correlations(history: np.ndarray, names: list[str], symbol: str) -> list[tuple[float, int, str]]:
    if history.size == 0 or symbol not in names:
        return []
    focal_index = names.index(symbol)
    focal = history[:, focal_index]
    valid_focal = np.isfinite(focal)
    if valid_focal.sum() < 2 or np.nanstd(focal) == 0:
        return []
    mask = np.isfinite(history) & valid_focal[:, None]
    n = mask.sum(axis=0)
    x = np.where(mask, focal[:, None], 0.0)
    y = np.where(mask, history, 0.0)
    sx, sy = x.sum(axis=0), y.sum(axis=0)
    sxx, syy = (x * x).sum(axis=0), (y * y).sum(axis=0)
    sxy = (x * y).sum(axis=0)
    numerator = sxy - sx * sy / np.maximum(n, 1)
    vx = sxx - sx * sx / np.maximum(n, 1)
    vy = syy - sy * sy / np.maximum(n, 1)
    denominator = np.sqrt(np.maximum(vx, 0) * np.maximum(vy, 0))
    correlations = np.divide(numerator, denominator, out=np.full(len(names), np.nan), where=denominator > 0)
    correlations[focal_index] = np.nan
    valid = np.flatnonzero((n >= 2) & np.isfinite(correlations))
    order = np.lexsort((np.asarray(names, dtype=object)[valid], -n[valid], -correlations[valid]))
    return [(float(correlations[index]), int(n[index]), names[index]) for index in valid[order[:PEER_COUNT]]]


def calculate(conn: sqlite3.Connection, catalogue: Path = CATALOGUE) -> tuple[list[dict], list[dict]]:
    """Return annual market and peer tables, with each SQL read bounded by its D."""
    events = _events(catalogue)
    market_by_day: dict[str, float] = {}
    returns_by_day: dict[str, dict[str, float | None]] = {}
    sessions: list[str] = []
    previous_close: dict[str, tuple[str, float]] = {}
    symbol_columns: dict[str, int] = {}
    symbols: list[str] = []
    rolling_returns = np.empty((0, 0), dtype=float)
    market_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"events": 0, "up": 0, "down": 0})
    peer_counts: dict[int, dict[str, float]] = defaultdict(lambda: {
        "full": 0, "short": 0, "events_with_peer_average": 0,
        "peers": 0.0, "overlap": 0.0, "peer_pairs": 0,
        "counter": 0, "lt25": 0, "25_50": 0, "50_75": 0, "gt75": 0, "unavailable": 0,
    })
    last_session = ""

    # Process sessions chronologically, extending the store read only as far as the
    # current event date. No global all-years price read or post-D cache is created.
    for event_day, day_events in events.items():
        new_sessions = _calendar(conn, last_session, event_day)
        for day in new_sessions:
            bars = _bars_for_day(conn, day)
            actions = _actions_asof(conn, day)
            day_returns: dict[str, float | None] = {}
            for symbol, close in bars.items():
                ret = _return(previous_close.get(symbol), day, close, actions.get(symbol, ()))
                day_returns[symbol] = ret
                previous_close[symbol] = (day, close)
            valid = [value for value in day_returns.values() if value is not None and math.isfinite(value)]
            market_by_day[day] = statistics.fmean(valid) if valid else float("nan")
            returns_by_day[day] = day_returns
            for symbol in bars:
                if symbol not in symbol_columns:
                    symbol_columns[symbol] = len(symbols)
                    symbols.append(symbol)
            if rolling_returns.shape[1] < len(symbols):
                rolling_returns = np.pad(
                    rolling_returns, ((0, 0), (0, len(symbols) - rolling_returns.shape[1])),
                    constant_values=np.nan,
                )
            current = np.full(len(symbols), np.nan, dtype=float)
            for symbol, value in day_returns.items():
                if value is not None:
                    current[symbol_columns[symbol]] = value
            rolling_returns = np.vstack((rolling_returns, current))[-(PEER_SESSIONS + 1):]
            sessions.append(day)
            last_session = day

        # Catalogue dates without an EQ session have no daily return context.
        if event_day not in returns_by_day:
            for event in day_events:
                y = int(event_day[:4])
                market_counts[y]["events"] += 1
                peer_counts[y]["unavailable"] += 1
            continue

        y = int(event_day[:4])
        market = market_by_day[event_day]
        day_returns = returns_by_day[event_day]
        pre_history = rolling_returns[:-1]
        for event in day_events:
            market_counts[y]["events"] += 1
            if market > 0.02:
                market_counts[y]["up"] += 1
            if market < -0.02:
                market_counts[y]["down"] += 1
            focal_return = event["return_1d"]
            correlations = _correlations(pre_history, symbols, event["symbol"])
            selected = correlations[:PEER_COUNT]
            counts = peer_counts[y]
            if len(selected) == PEER_COUNT:
                counts["full"] += 1
            else:
                counts["short"] += 1
            counts["overlap"] += sum(item[1] for item in selected)
            counts["peer_pairs"] += len(selected)
            on_day = [day_returns.get(item[2]) for item in selected if day_returns.get(item[2]) is not None]
            if on_day:
                counts["events_with_peer_average"] += 1
                counts["peers"] += len(on_day)
                peer_mean = statistics.fmean(on_day)
                if focal_return == 0:
                    counts["unavailable"] += 1
                else:
                    ratio = peer_mean / focal_return
                    if ratio < 0:
                        counts["counter"] += 1
                    elif ratio < 0.25:
                        counts["lt25"] += 1
                    elif ratio < 0.5:
                        counts["25_50"] += 1
                    elif ratio <= 0.75:
                        counts["50_75"] += 1
                    else:
                        counts["gt75"] += 1
            else:
                counts["unavailable"] += 1

    market_table = []
    for year in sorted(market_counts):
        row = market_counts[year]
        row["beyond"] = row["up"] + row["down"]
        market_table.append({"year": year, **row})
    peer_table = []
    for year in sorted(peer_counts):
        row = peer_counts[year]
        n = row["full"] + row["short"]
        peer_table.append({"year": year, **row,
                           "mean_peers": row["peers"] / row["events_with_peer_average"]
                           if row["events_with_peer_average"] else 0,
                           "mean_overlap": row["overlap"] / row["peer_pairs"]
                           if row["peer_pairs"] else 0})
    return market_table, peer_table


def main() -> None:
    import json
    from src.config.settings import get_settings
    from shared.sqlite_readonly import open_readonly

    with open_readonly(Path(get_settings().database_path)) as conn:
        market, peers = calculate(conn)
    print(json.dumps({"market": market, "peers": peers}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
