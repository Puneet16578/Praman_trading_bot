"""S1 funnel v1: decision-bounded, read-only inputs; never an outcome loader."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from dataclasses import asdict
from datetime import datetime
import csv
import math
import statistics

import numpy as np

from scripts import abc_followup_counts as A
from scripts import abc_event_day_context as C
from desk.automation.strategy0 import _size_at_limit
from desk.circuit_bands import band_as_of
from desk.paper.locks import buy_cap_at_decision
from desk.risk.officer import compute_stress_loss
from desk.t1.inputs import is_weekday
from desk.t1.features import build_calendar

VERSION = "s1_funnel_v1_addendum1"
START, END, DEV_END = "2019-10-01", "2025-12-31", "2024-12-31"
HORIZONS = (1, 3)
GROUPS = ("unexplained", "explained")
STEP_NAMES = ("market_drop", "material", "unclear", "sebi", "no_filing_90d",
              "coverage_gap", "dividend", "peer_explained_or_unknown", "g3_g5_failure")


def catalogue(path):
    out = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as stream:
        for r in csv.DictReader(stream):
            if START <= r["event_date"] <= END and float(r["return_1d"]) < 0:
                out[r["event_date"]].append(dict(symbol=r["symbol"],
                    return_1d=float(r["return_1d"]), zscore_60d=float(r["zscore_60d"])))
    return dict(sorted(out.items()))


def eligible_at(snapshots, day):
    """T1's per-symbol carry-forward, strictly after snapshot S."""
    known = {}
    for stamp, mapping in snapshots:
        if stamp >= day:
            break
        known.update(mapping)
    return {s for s, isin in known.items() if isin and not isin.startswith("INF")}


def calendars(conn, index_dates):
    # Dates only: no future price, volume, fill or availability check.
    observed = [r[0] for r in conn.execute(
        "SELECT DISTINCT event_date FROM bhavcopy WHERE series='EQ' "
        "AND event_date BETWEEN ? AND ? AND knowledge_date<=? ORDER BY event_date",
        (START, END, END))]
    s1, missing, _ = build_calendar(set(observed), set(index_dates), END)
    return dict(observed=observed, funnel=C._calendar(conn, "", END),
                s1=[d for d in s1 if d >= START], store_missing=missing)


def stream_context(conn, events, snapshots, minimum_overlap=200):
    """Frozen A/B/C stream with dated eligibility replacing the current roster.

    Historical return observations and turnover contributions require eligibility
    on their own dates. Peer candidates also require eligibility on D.
    """
    previous, names, columns = {}, [], {}
    rolling = np.empty((0, 0))
    turnovers = defaultdict(lambda: deque(maxlen=60))
    last = ""
    for requested in sorted(events):
        found = False
        for day in C._calendar(conn, last, requested):
            eligible = eligible_at(snapshots, day)
            bars, actions = C._bars_for_day(conn, day), C._actions_asof(conn, day)
            returns = {}
            prior_closes = {s: p[1] for s, p in previous.items()}
            for symbol, close in bars.items():
                prior = previous.get(symbol)
                ret = C._return(prior, day, close, actions.get(symbol, ()))
                if symbol in eligible and prior and prior[0] == last and ret is not None:
                    returns[symbol] = ret
                previous[symbol] = day, close
            mean = statistics.fmean(returns.values()) if returns else None
            for symbol in returns:
                if symbol not in columns:
                    columns[symbol] = len(names)
                    names.append(symbol)
            rolling = np.pad(rolling, ((0, 0), (0, len(names)-rolling.shape[1])),
                             constant_values=np.nan)
            row = np.full(len(names), np.nan)
            for symbol, ret in returns.items():
                row[columns[symbol]] = ret - mean
            seen = set()
            for r in conn.execute(
                "SELECT symbol,close_price,traded_qty FROM bhavcopy WHERE event_date=? "
                "AND knowledge_date<=? AND series='EQ' ORDER BY knowledge_date DESC,row_id DESC", (day, day)):
                if r["symbol"] not in seen and r["symbol"] in eligible:
                    turnovers[r["symbol"]].append(r["close_price"] * r["traded_qty"])
                seen.add(r["symbol"])
            if day == requested:
                found = True
                averages = {s: statistics.fmean(turnovers[s]) for s in bars
                            if s in eligible and len(turnovers[s]) == 60}
                bounds = np.quantile(list(averages.values()), [.2, .4, .6, .8], method="linear") if averages else []
                for event in events[day]:
                    symbol = event["symbol"]
                    share, status = None, "UNKNOWN"
                    if symbol in returns and mean is not None:
                        peers = C._repaired_correlations(rolling[-250:], names, symbol, set(returns), minimum_overlap)
                        if peers:
                            residual = returns[symbol] - mean
                            status = "KNOWN" if abs(residual) >= .01 else "UNSTABLE"
                            if status == "KNOWN":
                                share = (statistics.fmean(returns[p] for _, _, p in peers)-mean)/residual
                    yield day, event, dict(market=mean, peer_status=status, peer_share=share,
                        previous_close=prior_closes.get(symbol), eligible=symbol in eligible,
                        turnover_band=int(np.searchsorted(bounds, averages[symbol], side="right"))+1
                        if symbol in averages else "UNKNOWN")
            rolling = np.vstack((rolling, row))[-250:]
            last = day
        if not found:
            for event in events[requested]:
                yield requested, event, dict(market=None, peer_status="UNKNOWN", peer_share=None,
                    previous_close=None, eligible=event["symbol"] in eligible_at(snapshots, requested),
                    turnover_band="UNKNOWN")


def sized_plan(conn, desk_conn, symbol, day, previous, rulebook, costs):
    bounded = A.BoundedInputs(conn, day, previous)
    try:
        plan = A.decision_plan(bounded, symbol, day, stop_multiple=rulebook.screening.stop_multiple)
        q = int(A.compute_position_size(plan["decision_price"], plan["stop_level"], rulebook, 0, 0, 0, costs=costs))
        _, adv = A._average_daily_volume_and_turnover(bounded, symbol, day, A.ADV_LOOKBACK_SESSIONS)
        stress = compute_stress_loss(bounded, symbol, day, plan["decision_price"], plan["stop_level"],
                                    q, costs, rulebook, band_as_of(desk_conn, symbol, day))
        plan.update(quantity=q, adv_turnover=adv, stress=asdict(stress))
        qty, _, limit, rejection = _size_at_limit(plan, rulebook, costs)
        cap = buy_cap_at_decision(bounded, desk_conn, symbol, day, day+"T18:00:00+05:30")
        # S0 sizes at its uncapped limit, then caps the submitted price without resizing.
        accepted_limit = min(limit, cap["cap"]) if cap else limit
        g5 = A.g5_liquidity(qty * accepted_limit, adv, rulebook).result if qty > 0 else "UNKNOWN"
        return plan | dict(quantity=qty, screening_quantity=q, limit=accepted_limit,
                           uncapped_limit=limit, limit_cap=cap, rejection=rejection), g5
    except ValueError:
        return None, "UNKNOWN"


def reasons(flags, inputs, gates, limit_g5, day, next_observed, group):
    f = list(flags)
    if group == "explained":
        f[1], f[2] = not f[1], False
    result = [name if not (group == "explained" and i == 1) else "no_material"
              for i, (name, hit) in enumerate(zip(STEP_NAMES, f)) if hit]
    extras = dict(unstable_ratio=inputs["peer_status"] == "UNSTABLE",
                  g3_failure=gates["g3"] is True, g5_failure=gates["g5"] == "FAIL",
                  g3_unknown=gates["g3"] is None, g5_unknown=gates["g5"] == "UNKNOWN",
                  limit_g5_unknown=limit_g5 == "UNKNOWN", limit_g5_failure=limit_g5 == "FAIL",
                  active_asm=gates["asm"], identity_ineligible=not inputs["eligible"],
                  weekend_decision=not is_weekday(day),
                  next_session_weekend=next_observed is not None and not is_weekday(next_observed))
    return result + [k for k, v in extras.items() if v]


def build_records(conn, desk_conn, events, snapshots, cal, rulebook, costs, progress=lambda _: None):
    mapping, records = A.draft_map(), []
    observed, s1 = cal["observed"], cal["s1"]
    for day, event, inputs in stream_context(conn, events, snapshots):
        symbol = event["symbol"]
        i, j = bisect_left(observed, day), bisect_right(observed, day)
        previous = observed[i-1] if i else START
        nxt = observed[j] if j < len(observed) else None
        rows = [dict(r) for r in conn.execute(
            "SELECT seq_id,category,description,sort_timestamp,knowledge_date,event_date,recorded_at "
            "FROM corporate_announcements WHERE symbol=? AND knowledge_date<=? AND event_date<=?", (symbol, day, day))]
        dividends = [r for r in rows if r["category"] in A.DIV_CATEGORIES]
        orders = [dict(r) for r in conn.execute(
            "SELECT order_id,knowledge_date FROM sebi_orders WHERE symbol=? AND knowledge_date<=?", (symbol, day))]
        gates = A.gate_inputs(conn, symbol, day, previous, rulebook, costs)
        plan, limit_g5 = sized_plan(conn, desk_conn, symbol, day, previous, rulebook, costs)
        flags, _, _, _ = A.steps_for(rows, day, datetime.fromisoformat(day+"T18:00:00"),
            observed, mapping, inputs, gates, orders, dividends, 5)
        pos = bisect_right(s1, day)
        schedules = {str(h): s1[pos+h] if pos+h < len(s1) else None for h in HORIZONS}
        records.append(dict(day=day, **event, **inputs, gates=gates, limit_g5=limit_g5,
            filing_provenance=[{k: r[k] for k in ("seq_id", "event_date", "knowledge_date", "sort_timestamp", "recorded_at")}
                               for r in rows if A.available_at(r, observed) <= datetime.fromisoformat(day+"T18:00:00")],
            plan=plan, entry_session=s1[pos] if pos < len(s1) else None, scheduled_exits=schedules,
            exclusions={g: reasons(flags, inputs, gates, limit_g5, day, nxt, g) for g in GROUPS}))
        progress(day)
    return records


def boundary(day, scheduled):
    return scheduled is None or scheduled > (DEV_END if day <= DEV_END else END)


def summarize(records):
    values = [abs(r["zscore_60d"]) for r in records if r["day"] <= DEV_END
              and any(not r["exclusions"][g] for g in GROUPS) and math.isfinite(r["zscore_60d"])]
    bounds = np.quantile(values, [1/3, 2/3], method="linear").tolist() if values else []
    cells = []
    for group in GROUPS:
        for h in HORIZONS:
            earlier = defaultdict(list)
            overlaps = Counter()
            for r in sorted(records, key=lambda r: (r["day"], r["symbol"])):
                exit_day = r["scheduled_exits"][str(h)]
                if r["exclusions"][group] or boundary(r["day"], exit_day):
                    continue
                key = (r["symbol"], "development" if r["day"] <= DEV_END else "2025")
                # Decisions occur at 18:00: a scheduled open exit on D has passed.
                overlaps[r["day"][:4]] += any(e > r["day"] for e in earlier[key])
                earlier[key].append(exit_day)
            for year in range(2019, 2026):
                rows = [r for r in records if r["day"].startswith(str(year))]
                retained = [r for r in rows if not r["exclusions"][group]]
                usable = [r for r in retained if not boundary(r["day"], r["scheduled_exits"][str(h)])]
                standalone, combinations = Counter(), Counter()
                for r in rows:
                    detail = list(r["exclusions"][group])
                    if "peer_explained_or_unknown" in detail:
                        detail.append("peer_unknown" if r.get("peer_status") == "UNKNOWN" else "peer_explained")
                    standalone.update(detail)
                    combinations[" + ".join(sorted(detail)) or "RETAINED"] += 1
                cells.append(dict(year=year, group=group, horizon=h, catalogue=len(rows),
                    retained=len(retained), scheduled_boundary_removed=len(retained)-len(usable),
                    inputs_eligible=len(usable), distinct_dates=len({r["day"] for r in usable}),
                    turnover_bands=dict(Counter(str(r["turnover_band"]) for r in usable)),
                    scheduled_overlap_count=overlaps[str(year)], exclusions=dict(standalone),
                    exclusion_combinations=dict(combinations)))
    return dict(tercile_boundaries=bounds, cells=cells,
        overlap_note="Scheduled-overlap count, not a bound: delayed exits can add exclusions and early stops "
                     "can remove them. Actual one-position exclusions are evaluation-only.")
