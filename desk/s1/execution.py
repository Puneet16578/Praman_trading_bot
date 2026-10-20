"""S1 chronological execution over a reader interface. No store opened here."""
from bisect import bisect_left
import math

from desk.paper.execution import limit_order_fill, stop_rule
from desk.risk.officer import round_trip_cost_inr
from desk.s1.inputs import HORIZONS, GROUPS, DEV_END, END, boundary


def usable(bar):
    return bar is not None and all(math.isfinite(v) and v > 0 for v in
        (bar.opening, bar.high, bar.low, bar.close)) and bar.low <= min(bar.opening, bar.close) \
        and bar.high >= max(bar.opening, bar.close)


def trade(record, horizon, calendar, reader, costs, *, slippage=.0015):
    if horizon not in HORIZONS or slippage not in (.0015, .004):
        raise ValueError("Unregistered horizon or slippage.")
    day, symbol = record["day"], record["symbol"]
    scheduled = record["scheduled_exits"][str(horizon)]
    result = dict(day=day, symbol=symbol, horizon=horizon, scheduled_exit=scheduled,
                  turnover_band=record["turnover_band"], zscore_60d=record["zscore_60d"],
                  status="CENSORED", filled=False, net_return=None, closed_on=None,
                  missing_sessions=[], circuit_delays=[], dividend_sessions=[], dividend_unknown_sessions=[])
    if boundary(day, scheduled):
        result["reason"] = "SCHEDULED_BOUNDARY"
        return result
    plan = record["plan"]
    if not plan or plan.get("rejection") or plan["quantity"] < 1:
        return result | dict(status="NO_FILL", reason="DECISION_REJECTION")
    entry = record["entry_session"]
    bar = reader.bar(day, symbol, entry)
    if bar is not None and bar.unadjustable:
        return result | dict(status="NO_FILL", reason="UNADJUSTABLE_BEFORE_FILL")
    if not usable(bar):
        return result | dict(status="FILL_FAILURE", reason="UNUSABLE_ENTRY_BAR")
    if bar.blocks_buy or (plan.get("limit_cap") is None and bar.upper is not None and plan["limit"] > bar.upper+1e-9):
        return result | dict(status="NO_FILL", reason="ENTRY_LOCK_OR_REJECTED_LIMIT")
    fill = limit_order_fill(plan["limit"], bar.opening, bar.low)
    if fill["fill"] is None:
        return result | dict(status="NO_FILL" if fill["status"] == "NO_FILL" else "FILL_FAILURE",
                             reason=fill["reason"])
    price, qty, stop = fill["fill"], plan["quantity"], plan["stop_level"]
    result.update(filled=True, fill_date=entry, fill_price=price, quantity=qty, stop=stop,
                  atr20=plan["atr20"], entry_kind=fill["status"], entry_factor=bar.factor)
    if bar.dividend:
        result["dividend_sessions"].append(entry)
    if bar.dividend is None:
        result["dividend_unknown_sessions"].append(entry)
    # Prices/quantity are on the decision basis. Economic turnover and ad-valorem
    # charges are invariant under corporate-action share-basis changes.
    buy_cost = round_trip_cost_inr(price, qty, costs, "buy")
    minimum = min(price, bar.low)
    pending = None
    end = DEV_END if day <= DEV_END else END
    scheduled_i = bisect_left(calendar, scheduled)
    for i in range(bisect_left(calendar, entry)+1, len(calendar)):
        session = calendar[i]
        if session > end:
            break                           # no next-period price query
        bar = reader.bar(day, symbol, session)
        if bar is not None and bar.unadjustable:
            return result | dict(status="MISSING", reason="UNADJUSTABLE_ACTION", closed_on=session)
        if not usable(bar):
            result["missing_sessions"].append(session)
            if session >= scheduled:
                pending = pending or "TIME"
                if i >= scheduled_i+10:
                    return result | dict(status="MISSING", reason="NO_BAR_CAP", closed_on=session)
            continue
        if bar.dividend:
            result["dividend_sessions"].append(session)
        if bar.dividend is None:
            result["dividend_unknown_sessions"].append(session)
        if pending:
            reason, exit_price = pending, bar.opening
        elif session >= scheduled:
            # Only the open exists before the time exit; no later intraday low.
            reason, exit_price = ("STOP" if bar.opening <= stop else "TIME"), bar.opening
        else:
            hit = stop_rule(bar.opening, bar.low, stop)
            reason, exit_price = ("STOP", hit[1]) if hit else (None, None)
        if reason:
            if bar.blocks_sell:
                pending = reason            # addendum 1: never clear or re-arm
                result["circuit_delays"].append(session)
            else:
                sell = exit_price*(1-slippage)
                fees = buy_cost + round_trip_cost_inr(sell, qty, costs, "sell")
                net = (sell-price)/price-fees/(price*qty)
                planned = (price-stop)/price + (buy_cost+round_trip_cost_inr(stop, qty, costs, "sell"))/(price*qty)+.0015
                return result | dict(status="VALID", reason=reason, closed_on=session,
                    exit_price=exit_price, slipped_exit=sell, net_return=net, costs_inr=fees,
                    mae=max(0., 1-min(minimum, exit_price)/price),
                    severe_loss=None if price <= stop else net < -1.5*planned,
                    fill_at_or_below_stop=price <= stop, planned_net_loss=planned,
                    gap_through_stop=reason == "STOP" and exit_price < stop,
                    exit_delayed=session > scheduled or bool(result["circuit_delays"]))
        minimum = min(minimum, bar.low)       # still held for this full session
    return result | dict(status="CENSORED", reason="DELAYED_BOUNDARY")


def run(records, calendar, reader, costs, *, slippage=.0015):
    """No portfolio budget and no cross-group/horizon occupancy constraint."""
    output = []
    for group in GROUPS:
        for h in HORIZONS:
            occupied = {}
            for record in sorted(records, key=lambda r: (r["day"], r["symbol"])):
                if record["exclusions"][group]:
                    continue
                day, symbol = record["day"], record["symbol"]
                period = "development" if day <= DEV_END else "2025"
                key = period, symbol
                if key in occupied and occupied[key] > day:
                    output.append(dict(day=day, symbol=symbol, group=group, horizon=h,
                                       status="POSITION_SKIPPED", filled=False, net_return=None))
                    continue
                result = trade(record, h, calendar, reader, costs, slippage=slippage)
                result["group"] = group
                output.append(result)
                if result["filled"]:
                    occupied[key] = result["closed_on"] or (DEV_END if period == "development" else END)
    return output


def path_label(result, calendar, reader):
    """Descriptive only; unlike MAE this can continue after an actual early exit."""
    if not result["filled"] or boundary(result["day"], result["scheduled_exit"]):
        return dict(label=None, missing=[])
    lower = result["fill_price"]-2*result["atr20"]
    upper = result["fill_price"]+2*result["atr20"]
    missing = []
    for session in calendar:
        if session <= result["fill_date"]:
            continue
        if session > result["scheduled_exit"]:
            break
        bar = reader.bar(result["day"], result["symbol"], session)
        if not usable(bar) or bar.unadjustable:
            missing.append(session)
            continue
        lo, hi = (bar.opening, bar.opening) if session == result["scheduled_exit"] else (bar.low, bar.high)
        if lo <= lower or hi >= upper:
            # Missing earlier observations prevent asserting which came first.
            return dict(label=None if missing else ("STOP" if lo <= lower else "UPPER"), missing=missing)
    return dict(label=None if missing else "TIMEOUT", missing=missing)


def benchmark(result, reader):
    if result["status"] != "VALID":
        return dict(return_=None, relative=None, members=0, missing=0)
    members = reader.market_members(result["day"])
    values, missing = [], 0
    for symbol in members:
        entry = reader.benchmark_open(result["day"], symbol, result["fill_date"], result["fill_date"])
        exit_ = reader.benchmark_open(result["day"], symbol, result["closed_on"], result["fill_date"])
        if entry is None or exit_ is None or not all(math.isfinite(v) and v > 0 for v in (entry, exit_)):
            missing += 1
        else:
            values.append(exit_/entry-1)
    mean = sum(values)/len(values) if values else None
    return dict(return_=mean, relative=None if mean is None else result["net_return"]-mean,
                members=len(members), missing=missing,
                convention="Fixed D-known members, fill open to actual-exit-session open; intraday stop endpoint mismatch.")
