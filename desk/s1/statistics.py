"""Fixed S1 family, sample minimums, block inference and descriptive measures."""
from collections import Counter
from bisect import bisect_right
import numpy as np

from desk.s1.inputs import HORIZONS, GROUPS, DEV_END, END, START
from desk.t1.bootstrap import block_draws, multiplicities

FAMILY = (("a", 1), ("b", 1), ("a", 3), ("b", 3))
SEED, DRAWS, BLOCK, MIN_USABLE = 20261001, 2000, 20, 1900


def period_calendar(calendar, period, horizon):
    if horizon not in HORIZONS or period not in ("development", "2025"):
        raise ValueError("Unregistered period or horizon.")
    lo, hi = (START, DEV_END) if period == "development" else ("2025-01-01", END)
    return [d for i, d in enumerate(calendar) if lo <= d <= hi
            and i+1+horizon < len(calendar) and calendar[i+1+horizon] <= hi]


def describe(rows):
    valid = [r for r in rows if r["status"] == "VALID"]
    values = np.array([r["net_return"] for r in valid])
    gains, losses = values[values > 0], values[values < 0]
    missing = sum(r["status"] == "MISSING" for r in rows)
    denominator = len(valid)+missing
    severe = [r["severe_loss"] for r in valid if r.get("severe_loss") is not None]
    maes = [r["mae"] for r in valid if r.get("mae") is not None]
    relative = [r["benchmark"]["relative"] for r in valid
                if r.get("benchmark", {}).get("relative") is not None]
    return dict(status_counts=dict(Counter(r["status"] for r in rows)), valid=len(valid),
        distinct_dates=len({r["day"] for r in valid}), missing=missing, filled_denominator=denominator,
        missing_rate=missing/denominator if denominator else None,
        mean=float(values.mean()) if len(values) else None,
        median=float(np.median(values)) if len(values) else None,
        hit_rate=float((values > 0).mean()) if len(values) else None,
        profit_factor=float(gains.sum()/-losses.sum()) if len(gains) and len(losses) else "undefined",
        payoff_ratio=float(gains.mean()/-losses.mean()) if len(gains) and len(losses) else "undefined",
        gains=len(gains), losses=len(losses),
        stop_out_rate=sum(r.get("reason") == "STOP" for r in valid)/len(valid) if valid else None,
        mean_mae=float(np.mean(maes)) if maes else None, mae_coverage=len(maes),
        mean_benchmark_relative=float(np.mean(relative)) if relative else None, benchmark_coverage=len(relative),
        severe_loss_rate=float(np.mean(severe)) if severe else None, severe_loss_coverage=len(severe),
        fill_at_or_below_stop=sum(r.get("fill_at_or_below_stop", False) for r in valid),
        gap_through_stops=sum(r.get("gap_through_stop", False) for r in valid),
        delayed_exits=sum(r.get("exit_delayed", False) for r in valid),
        parsed_dividend_record_holds=sum(bool(r.get("dividend_sessions")) for r in rows),
        dividend_coverage_unknown_holds=sum(bool(r.get("dividend_unknown_sessions")) for r in rows),
        dividend_coverage_note="Parsed record/book-closure dates only; not a complete ex-dividend calendar. "
                               "No match is UNKNOWN; dividends receive no return credit.",
        circuit_delayed_holds=sum(bool(r.get("circuit_delays")) for r in rows),
        missing_bar_holds=sum(bool(r.get("missing_sessions")) for r in rows),
        path_labels=dict(Counter(r.get("path", {}).get("label") or "UNKNOWN" for r in rows if r.get("filled"))))


def adequate(stats):
    return stats["valid"] >= 100 and stats["distinct_dates"] >= 30 and \
        stats["missing_rate"] is not None and stats["missing_rate"] <= .05


def group_draws(rows, calendar, weights):
    pos = {d: i for i, d in enumerate(calendar)}
    count, sums, missing = (np.zeros(len(calendar)) for _ in range(3))
    for r in rows:
        if r["day"] not in pos:
            if r["status"] in ("VALID", "MISSING"):
                raise ValueError("Outcome present on a purged date.")
            continue
        j = pos[r["day"]]
        if r["status"] == "VALID":
            count[j] += 1
            sums[j] += r["net_return"]
        elif r["status"] == "MISSING":
            missing[j] += 1
    n, total, miss = weights @ count, weights @ sums, weights @ missing
    distinct = (weights > 0).astype(np.int32) @ (count > 0).astype(np.int32)
    rate = np.divide(miss, n+miss, out=np.ones_like(n), where=n+miss > 0)
    usable = (n >= 100) & (distinct >= 30) & (rate <= .05)
    means = np.divide(total, n, out=np.full(len(n), np.nan), where=n > 0)
    reasons = dict(valid_trades_below_100=int((n < 100).sum()),
                   distinct_dates_below_30=int((distinct < 30).sum()),
                   missing_above_5pct=int((rate > .05).sum()))
    return means, usable, reasons


def intervals(draws, mask):
    usable = draws[mask & np.isfinite(draws)]
    return dict(usable_draws=len(usable),
        family_interval=np.quantile(usable, [.00625, .99375], method="linear").tolist() if len(usable) else None,
        descriptive_95=np.quantile(usable, [.025, .975], method="linear").tolist() if len(usable) else None)


def consistency(rows, period):
    bins = ("2021", "2022", "2023", "2024") if period == "development" else ("H1", "H2")
    cells = {}
    for key in bins:
        part = [r for r in rows if r["status"] == "VALID" and
                (r["day"].startswith(key) if period == "development" else
                 ("H1" if r["day"][5:7] <= "06" else "H2") == key)]
        mean = float(np.mean([r["net_return"] for r in part])) if part else None
        cells[key] = dict(n=len(part), mean=mean, positive=len(part) >= 30 and mean > 0)
    if period == "2025" and any(c["n"] < 30 for c in cells.values()):
        state = "INCONCLUSIVE"
    else:
        required = 3 if period == "development" else 2
        state = "PASS" if sum(c["positive"] for c in cells.values()) >= required else "FAIL"
    return dict(state=state, cells=cells)


def evaluate(rows, calendar, period, horizon):
    dates = period_calendar(calendar, period, horizon)
    selected = [r for r in rows if r["horizon"] == horizon and
                (r["day"] <= DEV_END if period == "development" else r["day"] > DEV_END)]
    groups = {g: [r for r in selected if r["group"] == g] for g in GROUPS}
    stats = {g: describe(rs) for g, rs in groups.items()}
    if len(dates) >= BLOCK:
        weights = multiplicities(block_draws(len(dates), BLOCK, DRAWS, SEED), len(dates))
        computed = {g: group_draws(rs, dates, weights) for g, rs in groups.items()}
    else:
        computed = {g: (np.full(DRAWS, np.nan), np.zeros(DRAWS, dtype=bool),
                       {"calendar_shorter_than_block": DRAWS}) for g in GROUPS}
    u, e = computed["unexplained"], computed["explained"]
    a, b = intervals(u[0], u[1]), intervals(u[0]-e[0], u[1] & e[1])
    a["estimate"] = stats["unexplained"]["mean"]
    b["estimate"] = (stats["unexplained"]["mean"]-stats["explained"]["mean"]
                     if all(s["mean"] is not None for s in stats.values()) else None)
    for key, test, enough in (("a", a, adequate(stats["unexplained"])),
                              ("b", b, all(adequate(s) for s in stats.values()))):
        test["state"] = ("INCONCLUSIVE" if not enough or test["usable_draws"] < MIN_USABLE else
                         "PASS" if test["estimate"] >= .0025 and test["family_interval"][0] > 0 else "FAIL")
    c = consistency(groups["unexplained"], period)
    verdict = ("INCONCLUSIVE" if "INCONCLUSIVE" in (a["state"], c["state"]) else
               "PASS" if a["state"] == c["state"] == "PASS" else "FAIL")
    label = {"PASS": "LABEL SHOWN", "FAIL": "NOT SHOWN", "INCONCLUSIVE": "INCONCLUSIVE"}[b["state"]]
    return dict(period=period, horizon=horizon, family=[list(x) for x in FAMILY], calendar_dates=len(dates),
        seed=SEED, draws=DRAWS, block=BLOCK, groups=stats, a=a, b=b, c=c, verdict=verdict, label=label,
        label_statement=None if label == "LABEL SHOWN" else "The rebound is not shown to depend on the drop being unexplained.",
        unusable_reasons={g: computed[g][2] for g in GROUPS})


def breakdowns(rows, tercile_boundaries):
    output = {}
    for name in ("year", "turnover_band", "drop_tercile", "V1", "V2", "V3"):
        groups = {}
        for r in rows:
            if name == "year":
                key = r["day"][:4]
            elif name == "turnover_band":
                key = str(r.get(name, "UNKNOWN"))
            elif name == "drop_tercile":
                z = r.get("zscore_60d")
                key = str(bisect_right(tercile_boundaries, abs(z))+1) if z is not None and len(tercile_boundaries) == 2 else "UNKNOWN"
            else:
                key = str(r.get("market_states", {}).get(name, "UNKNOWN"))
            groups.setdefault(key, []).append(r)
        output[name] = {k: describe(rs) for k, rs in sorted(groups.items())}
    return output
