"""Read-only reproduction of the original A/B/C section 8 event-day tables.

Only EQ close-to-close inputs through each processed session are queried. Corporate
actions are selected as known on that session. No writes, outcomes, or later prices.
The default mode reproduces the original descriptive section 8. ``--repaired``
produces the follow-up fund-free market and market-adjusted peer tables.
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
MIN_MAIN_OVERLAP = 200
MIN_SENSITIVITY_OVERLAP = 120
SANITY_DATE = "2024-10-01"
SANITY_SYMBOLS = {
    "HDFCBANK": "private bank",
    "TCS": "IT services",
    "SUNPHARMA": "pharma",
    "ULTRACEMCO": "cement",
    "MARUTI": "carmaker",
    "IOC": "oil marketer",
}


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
    """EQ sessions after `after` up to `through` that have at least one EQ bar known on its own
    day: the point-in-time rule `_bars_for_day` applies to the bars themselves. Membership depends
    only on the store, never on which dates a run requests (P8-093, fixed 2026-10-19; before, a
    session was admitted if any bar was known by `through`, so late-published sessions entered as
    empty sessions or not depending on the requests). Both bounds are on the source query; no
    post-D dates are read."""
    return [row[0] for row in _rows_asof(
        conn,
        "SELECT DISTINCT event_date FROM bhavcopy "
        "WHERE series='EQ' AND event_date>=? AND event_date>? AND event_date<=? "
        "AND knowledge_date<=event_date ORDER BY event_date",
        (START, after, through),
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


def _repaired_correlations(history: np.ndarray, names: list[str], focal_symbol: str,
                           candidates_today: set[str], minimum_overlap: int,
                           limit: int | None = PEER_COUNT) -> list[tuple[float, int, str]]:
    """Top market-adjusted correlations, restricted to today's valid EQ universe."""
    if history.size == 0 or focal_symbol not in names:
        return []
    focal_index = names.index(focal_symbol)
    focal = history[:, focal_index]
    valid_focal = np.isfinite(focal)
    if valid_focal.sum() < minimum_overlap or np.nanstd(focal) == 0:
        return []
    allowed = np.array([name in candidates_today and name != focal_symbol for name in names])
    mask = np.isfinite(history) & valid_focal[:, None]
    n = mask.sum(axis=0)
    x = np.where(mask, focal[:, None], 0.0)
    y = np.where(mask, history, 0.0)
    sx, sy = x.sum(axis=0), y.sum(axis=0)
    sxx, syy = (x * x).sum(axis=0), (y * y).sum(axis=0)
    sxy = (x * y).sum(axis=0)
    denominator = np.sqrt(np.maximum(sxx - sx * sx / np.maximum(n, 1), 0)
                          * np.maximum(syy - sy * sy / np.maximum(n, 1), 0))
    correlation = np.divide(sxy - sx * sy / np.maximum(n, 1), denominator,
                            out=np.full(len(names), np.nan), where=denominator > 0)
    valid = np.flatnonzero(allowed & (n >= minimum_overlap) & np.isfinite(correlation))
    if not len(valid):
        return []
    order = np.lexsort((np.asarray(names, dtype=object)[valid], -n[valid], -correlation[valid]))
    ordered = valid[order]
    if limit is not None:
        ordered = ordered[:limit]
    return [(float(correlation[index]), int(n[index]), names[index]) for index in ordered]


def _bucket(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "unavailable"
    if value < 0:
        return "counter"
    if value < 0.25:
        return "under25"
    if value < 0.5:
        return "25_50"
    if value <= 0.75:
        return "50_75"
    return "over75"


def calculate_repaired(conn: sqlite3.Connection, isin_map: dict[str, str],
                       catalogue: Path = CATALOGUE,
                       sanity_date: str | None = SANITY_DATE, years=None) -> dict:
    """Calculate requested fund-free, consecutive-session market and peer descriptions.

    Every market-data SQL query is bounded at the session currently being processed.
    Returns contain inputs through D only; there are no outcome-window reads.
    `years` (Claude, 2026-10-19): report only those event years. Every session is still streamed
    and every event date still requested, so a one-year run gives the same rows for its year as
    the all-years run, and the same identity universe and sanity check.
    """
    events = _events(catalogue)
    eligible = {symbol for symbol, isin in isin_map.items() if isin and not isin.startswith("INF")}
    observed_symbols: set[str] = set()
    event_dates = set(events)
    if sanity_date:
        event_dates.add(sanity_date)
    market_by_year: dict[int, dict] = defaultdict(lambda: {
        "event_dates": 0, "catalogue_event_days": 0, "unknown_market_events": 0,
        "used_returns": 0, "gap_dropped_returns": 0,
        "daily_means": [], "daily_medians": [], "mean_up_events": 0,
        "mean_down_events": 0, "median_up_events": 0, "median_down_events": 0,
    })
    peer_by_key: dict[tuple[int, str, int], dict] = defaultdict(lambda: {
        "events": 0, "focal_valid": 0, "unknown": 0, "unstable": 0,
        "peer_status_known": 0, "peer_buckets": defaultdict(int),
        "market_buckets": defaultdict(int), "peer_count_sum": 0,
    })
    previous_close: dict[str, tuple[str, float]] = {}
    symbol_columns: dict[str, int] = {}
    symbols: list[str] = []
    rolling = np.empty((0, 0), dtype=float)
    last_session = ""
    sanity_result: dict[str, list[dict]] = {}

    def process_session(day: str) -> tuple[dict[str, float], float | None, float | None, int]:
        nonlocal rolling, last_session
        previous_market_session = last_session or None
        bars = _bars_for_day(conn, day)
        observed_symbols.update(bars)
        actions = _actions_asof(conn, day)
        own_returns: dict[str, float | None] = {}
        valid_market_returns: dict[str, float] = {}
        stale_count = 0
        for symbol, close in bars.items():
            prior = previous_close.get(symbol)
            ret = _return(prior, day, close, actions.get(symbol, ()))
            own_returns[symbol] = ret
            if ret is not None and symbol in eligible:
                if prior and prior[0] == previous_market_session:
                    valid_market_returns[symbol] = ret
                else:
                    stale_count += 1
            previous_close[symbol] = (day, close)

        market_mean = statistics.fmean(valid_market_returns.values()) if valid_market_returns else None
        market_median = statistics.median(valid_market_returns.values()) if valid_market_returns else None
        market_adjusted = ({symbol: ret - market_mean for symbol, ret in valid_market_returns.items()}
                           if market_mean is not None else {})
        for symbol in market_adjusted:
            if symbol not in symbol_columns:
                symbol_columns[symbol] = len(symbols)
                symbols.append(symbol)
        if rolling.shape[1] < len(symbols):
            rolling = np.pad(rolling, ((0, 0), (0, len(symbols) - rolling.shape[1])), constant_values=np.nan)
        row = np.full(len(symbols), np.nan)
        for symbol, value in market_adjusted.items():
            row[symbol_columns[symbol]] = value
        rolling = np.vstack((rolling, row))[-(PEER_SESSIONS + 1):]
        last_session = day
        return valid_market_returns, market_mean, market_median, stale_count

    for requested_day in sorted(event_dates):
        if not (START <= requested_day <= END):
            continue
        new_sessions = _calendar(conn, last_session, requested_day)
        for day in new_sessions:
            current_returns, current_mean, current_median, stale_drops = process_session(day)
            session_year = int(day[:4])
            if 2020 <= session_year <= 2025:
                market_by_year[session_year]["used_returns"] += len(current_returns)
                market_by_year[session_year]["gap_dropped_returns"] += stale_drops
            if day in event_dates and day in events and (years is None or int(day[:4]) in years):
                year = int(day[:4])
                summary = market_by_year[year]
                summary["catalogue_event_days"] += 1
                if current_mean is not None and current_median is not None:
                    summary["event_dates"] += 1
                    summary["daily_means"].append(current_mean)
                    summary["daily_medians"].append(current_median)
                    for event in events[day]:
                        if current_mean > 0.02:
                            summary["mean_up_events"] += 1
                        if current_mean < -0.02:
                            summary["mean_down_events"] += 1
                        if current_median > 0.02:
                            summary["median_up_events"] += 1
                        if current_median < -0.02:
                            summary["median_down_events"] += 1
                        focal = current_returns.get(event["symbol"])
                        direction = "up" if event["return_1d"] > 0 else "down"
                        event_counts = {
                            minimum: peer_by_key[(int(day[:4]), direction, minimum)]
                            for minimum in (MIN_MAIN_OVERLAP, MIN_SENSITIVITY_OVERLAP)
                        }
                        for counts in event_counts.values():
                            counts["events"] += 1
                        if focal is None:
                            for counts in event_counts.values():
                                counts["unknown"] += 1
                            continue
                        adjusted_move = focal - current_mean
                        market_share = current_mean / focal if focal != 0 else None
                        focal_history = (int(np.isfinite(rolling[:-1, symbol_columns[event["symbol"]]]).sum())
                                         if event["symbol"] in symbol_columns else 0)
                        for counts in event_counts.values():
                            counts["focal_valid"] += 1
                            counts["market_buckets"][_bucket(market_share)] += 1
                            if abs(adjusted_move) < 0.01:
                                counts["unstable"] += 1
                        correlations = []
                        if focal_history >= MIN_SENSITIVITY_OVERLAP:
                            correlations = _repaired_correlations(
                                rolling[:-1], symbols, event["symbol"], set(current_returns),
                                MIN_SENSITIVITY_OVERLAP, limit=None,
                            )
                        for minimum, counts in event_counts.items():
                            if focal_history < minimum:
                                counts["unknown"] += 1
                                continue
                            selected = [item for item in correlations if item[1] >= minimum][:PEER_COUNT]
                            if not selected:
                                counts["unknown"] += 1
                                continue
                            peer_mean = statistics.fmean(current_returns[name] for _, _, name in selected)
                            counts["peer_status_known"] += 1
                            counts["peer_count_sum"] += len(selected)
                            if abs(adjusted_move) < 0.01:
                                continue
                            peer_share = (peer_mean - current_mean) / adjusted_move
                            counts["peer_buckets"][_bucket(peer_share)] += 1
                else:
                    summary["unknown_market_events"] += len(events[day])
                    for event in events[day]:
                        direction = "up" if event["return_1d"] > 0 else "down"
                        for minimum in (MIN_MAIN_OVERLAP, MIN_SENSITIVITY_OVERLAP):
                            counts = peer_by_key[(int(day[:4]), direction, minimum)]
                            counts["events"] += 1
                            counts["unknown"] += 1

            if sanity_date and day == sanity_date:
                history = rolling[:-1]
                for symbol, industry in SANITY_SYMBOLS.items():
                    focal_history = (int(np.isfinite(history[:, symbol_columns[symbol]]).sum())
                                     if symbol in symbol_columns else 0)
                    if symbol not in current_returns or focal_history < MIN_MAIN_OVERLAP:
                        sanity_result[symbol] = [{"industry": industry, "status": "UNKNOWN"}]
                        continue
                    selected = _repaired_correlations(
                        history, symbols, symbol, set(current_returns), MIN_MAIN_OVERLAP, limit=5
                    )
                    sanity_result[symbol] = [{"industry": industry, "status": "KNOWN",
                                              "peer": peer, "correlation": corr, "overlap": overlap}
                                             for corr, overlap, peer in selected]

        # If D is a special catalogue date absent from EQ calendar, keep every event
        # in the population and report the market/peer input as unavailable.
        if (requested_day in events and requested_day not in new_sessions
                and (years is None or int(requested_day[:4]) in years)):
            year = int(requested_day[:4])
            market_by_year[year]["catalogue_event_days"] += 1
            market_by_year[year]["unknown_market_events"] += len(events[requested_day])
            for event in events[requested_day]:
                direction = "up" if event["return_1d"] > 0 else "down"
                for minimum in (MIN_MAIN_OVERLAP, MIN_SENSITIVITY_OVERLAP):
                    peer_by_key[(year, direction, minimum)]["events"] += 1
                    peer_by_key[(year, direction, minimum)]["unknown"] += 1

    market_rows = []
    for year, row in sorted(market_by_year.items()):
        if years is not None and year not in years:
            continue
        event_dates_count = row["event_dates"]
        market_rows.append({
            "year": year,
            "market_available_event_days": event_dates_count,
            "catalogue_event_days": row["catalogue_event_days"],
            "unknown_market_events": row["unknown_market_events"],
            "used_returns": row["used_returns"],
            "gap_dropped_returns": row["gap_dropped_returns"],
            "mean_of_daily_market_means": statistics.fmean(row["daily_means"]) if row["daily_means"] else None,
            "median_of_daily_market_means": statistics.median(row["daily_means"]) if row["daily_means"] else None,
            "mean_of_daily_stock_medians": statistics.fmean(row["daily_medians"]) if row["daily_medians"] else None,
            "median_of_daily_stock_medians": statistics.median(row["daily_medians"]) if row["daily_medians"] else None,
            "mean_up_events": row["mean_up_events"],
            "mean_down_events": row["mean_down_events"],
            "median_up_events": row["median_up_events"],
            "median_down_events": row["median_down_events"],
        })
    peer_rows = []
    for (year, direction, minimum), row in sorted(peer_by_key.items()):
        if years is not None and year not in years:
            continue
        peer_rows.append({
            "year": year, "direction": direction, "minimum_overlap": minimum,
            "events": row["events"], "focal_valid": row["focal_valid"], "unknown": row["unknown"],
            "unstable": row["unstable"], "peer_status_known": row["peer_status_known"],
            "mean_peer_count": row["peer_count_sum"] / row["peer_status_known"] if row["peer_status_known"] else None,
            "peer_buckets": dict(row["peer_buckets"]), "market_buckets": dict(row["market_buckets"]),
        })
    return {"market": market_rows, "peers": peer_rows,
            "identity_universe": {
                "observed_eq_symbols": len(observed_symbols),
                "fund_isin_symbols_excluded": sum(
                    1 for symbol in observed_symbols if isin_map.get(symbol, "").startswith("INF")
                ),
                "unresolved_isin_symbols_excluded": sum(
                    1 for symbol in observed_symbols if symbol not in isin_map
                ),
            },
            "sanity_date": sanity_date, "sanity": sanity_result}


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
    import argparse
    import json
    from src.config.settings import get_settings
    from src.ingestion.nse_market_data.isin_mapping import load_isin_map
    from shared.sqlite_readonly import open_readonly

    parser = argparse.ArgumentParser()
    parser.add_argument("--repaired", action="store_true", help="produce the follow-up market/peer convention tables")
    parser.add_argument("--years", help="comma-separated event years for --repaired (default: all)")
    args = parser.parse_args()
    years = {int(y) for y in args.years.split(",")} if args.years else None
    with open_readonly(Path(get_settings().database_path)) as conn:
        if args.repaired:
            isin_path = ROOT / "data" / "raw" / "nse_symbol_isin_current.json"
            result = calculate_repaired(conn, load_isin_map(isin_path), years=years)
        else:
            market, peers = calculate(conn)
            result = {"market": market, "peers": peers}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
