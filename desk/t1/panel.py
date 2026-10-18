"""Load the T1 panel: Praman's store (read-only), dated ISIN snapshots, official index inputs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from desk.t1.features import ADJUSTABLE, EQUITY, FUND, STUDY_END, STUDY_START, UNADJUSTABLE, UNKNOWN, Panel, build_calendar
from desk.t1.inputs import SERIES
from src.signals.price_adjustment import factor_for_action


def snapshot_identities(isin_dir: Path) -> list[tuple[str, dict]]:
    """(snapshot date, {symbol: ISIN}) for each cached historical CM snapshot whose SHA-256 sidecar
    matches (P8-060 cache). Each is public from its own session."""
    from src.ingestion.nse_market_data.isin_mapping import fetch_isin_snapshot
    from datetime import date
    out = []
    for csv_path in sorted(isin_dir.glob("cm_*.csv")):
        sidecar = csv_path.with_name(csv_path.name + ".sha256.json")
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        if hashlib.sha256(csv_path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"{csv_path.name} fails its hash check")
        day = record["snapshot_date"]
        out.append((day, fetch_isin_snapshot(date.fromisoformat(day), bhavcopy_save=lambda _d, _f, p=csv_path: str(p))))
    return out


def identity_matrix(sessions: list[str], symbols: list[str], snapshots: list[tuple[str, dict]]) -> np.ndarray:
    """UNKNOWN / EQUITY / FUND for each (session, symbol): from the latest snapshot on or before
    the session that lists the symbol; a resolved non-INF ISIN is equity (the Amendment 4 rule)."""
    ident = np.full((len(sessions), len(symbols)), UNKNOWN, dtype=np.int8)
    col = {s: j for j, s in enumerate(symbols)}
    session_arr = np.array(sessions)
    for day, mapping in sorted(snapshots):
        first = int(np.searchsorted(session_arr, day, side="left"))
        for symbol, isin in mapping.items():
            j = col.get(symbol)
            if j is not None:
                ident[first:, j] = FUND if isin.startswith("INF") else EQUITY
    return ident


def load_panel(praman_conn, index_closes: dict, snapshots: list[tuple[str, dict]], *, end: str = STUDY_END) -> Panel:
    store_sessions = {r[0] for r in praman_conn.execute(
        "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date BETWEEN ? AND ?", (STUDY_START, end))}
    index_dates = set().union(*(set(index_closes[s]) for s in SERIES))
    sessions, missing, specials = build_calendar(store_sessions, index_dates, end)
    pos = {d: i for i, d in enumerate(sessions)}
    session_arr = np.array(sessions)
    forward = [r[0] for r in praman_conn.execute(
        "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? ORDER BY 1 LIMIT 40", (end,))]
    bars = praman_conn.execute(
        "SELECT symbol, event_date, knowledge_date, open_price, high_price, low_price, close_price FROM bhavcopy "
        "WHERE series='EQ' AND event_date BETWEEN ? AND ?", (STUDY_START, end)).fetchall()
    symbols = sorted({b[0] for b in bars})
    col = {s: j for j, s in enumerate(symbols)}
    shape = (len(sessions), len(symbols))
    raw = {k: np.full(shape, np.nan) for k in ("open", "high", "low", "close")}
    known = np.full(shape, np.inf)
    for symbol, day, kd, o, h, l, c in bars:
        i, j = pos[day], col[symbol]
        if np.isfinite(known[i, j]):
            raise ValueError(f"More than one EQ vintage for {symbol} {day}; the loader assumes one")
        raw["open"][i, j], raw["high"][i, j], raw["low"][i, j], raw["close"][i, j] = o, h, l, c
        known[i, j] = float(np.searchsorted(session_arr, kd, side="left")) if kd <= sessions[-1] else np.inf
    logf = np.zeros(shape)
    brk = np.zeros(shape)
    latest = {}
    for row in praman_conn.execute(
            "SELECT symbol, action_type, event_date, knowledge_date, ratio_numerator, ratio_denominator, row_id "
            "FROM corporate_actions WHERE event_date <= ? ORDER BY knowledge_date, row_id", (end,)):
        latest[(row[0], row[1], row[2])] = row                      # the latest vintage of each action
    for symbol, kind, ex, kd, num, den, _ in latest.values():
        j = col.get(symbol)
        i = int(np.searchsorted(session_arr, ex, side="left"))
        if j is None or i >= len(sessions):
            continue
        if kind in UNADJUSTABLE:
            brk[i, j] += 1
        elif kind in ADJUSTABLE and num and den:
            logf[i, j] += math.log(factor_for_action(kind, num, den))
    cum = np.cumsum(logf, axis=0)
    scale = np.exp(cum - cum[-1])                                   # back-adjusted to the latest basis
    breaks = np.cumsum(brk, axis=0)
    index = {}
    for s in SERIES:
        arr = np.full(len(sessions), np.nan)
        for d, r in index_closes[s].items():
            if d in pos:
                arr[pos[d]] = r["close"]
        index[s] = arr
    return Panel(sessions=sessions, symbols=symbols, raw_close=raw["close"], close=raw["close"] * scale,
                 high=raw["high"] * scale, low=raw["low"] * scale, known=known, breaks=breaks,
                 identity=identity_matrix(sessions, symbols, snapshots), index=index,
                 store_missing_sessions=missing, weekend_specials=specials, forward_sessions=forward,
                 open=raw["open"] * scale)
