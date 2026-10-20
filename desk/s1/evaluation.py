"""S1 evaluation composition. Real invocation requires separate user approval.

This module opens no store and has no command-line entry point. Rehearsal passes
a synthetic reader. Descriptive states/labels never enter population or verdicts.
"""
from collections import Counter
from desk.s1 import execution as E, statistics as S
from desk.s1.inputs import GROUPS, HORIZONS, DEV_END, END


def evaluate_inputs(artifact, reader, costs, *, period="development", slippage=.0015, random_labels=None):
    if period not in ("development", "2025"):
        raise ValueError("Unregistered period.")
    records = [r for r in artifact["records"] if
               (r["day"] <= DEV_END if period == "development" else DEV_END < r["day"] <= END)]
    calendar = artifact["calendars"]["s1"]
    results = E.run(records, calendar, reader, costs, slippage=slippage)
    for r in results:
        r["market_states"] = reader.market_states(r["day"], r["symbol"])
        if r.get("filled"):
            r["path"] = E.path_label(r, calendar, reader)
        if r["status"] == "VALID":
            r["benchmark"] = E.benchmark(r, reader)
            if random_labels is not None:
                # Rehearsal only: replacement independent of synthetic prices.
                r["net_return"] = float(random_labels(r))
                r["benchmark"]["relative"] = r["net_return"]-(r["benchmark"]["return_"] or 0.)
                r["severe_loss"] = (None if r["fill_at_or_below_stop"] else
                                    r["net_return"] < -1.5*r["planned_net_loss"])
    bounds = artifact["summary"]["tercile_boundaries"]
    return dict(period=period, synthetic=random_labels is not None,
        tests=[S.evaluate(results, calendar, period, h) for h in HORIZONS],
        breakdowns={f"{g}/h{h}": S.breakdowns([r for r in results if r["group"] == g and r["horizon"] == h], bounds)
                    for g in GROUPS for h in HORIZONS},
        records=results, slippage=slippage,
        shared_inputs="Selection, ATR, market/peer measures and returns share price anchors. "
                      "Filing coverage and liquidity select a non-random population; this is not a causal comparison.")


def omit_crowded_dates(records):
    """One registered sensitivity: omit ALL tied most-crowded dates per year.

    Counts the pooled primary population; rerun chronology after omitting.
    """
    counts = Counter(r["day"] for r in records if any(not r["exclusions"][g] for g in GROUPS))
    maxima = {}
    for day, n in counts.items():
        maxima[day[:4]] = max(maxima.get(day[:4], 0), n)
    omitted = {d for d, n in counts.items() if n == maxima[d[:4]]}
    return [r for r in records if r["day"] not in omitted], sorted(omitted)


def sensitivity_inputs(artifact, variant):
    """Only frozen input variants may change the population; never outcome-based selection."""
    # Provenance and plans are immutable inputs. Copy only the event containers
    # and exclusion lists this sensitivity can change, not the large audit trail.
    out = dict(artifact, records=[dict(r, exclusions={g: list(v) for g, v in r["exclusions"].items()})
                                  for r in artifact["records"]])
    if variant == "omit_crowded_dates":
        out["records"], out["omitted_dates"] = omit_crowded_dates(out["records"])
    elif variant == "include_unstable":
        for r in out["records"]:
            for g in GROUPS:
                r["exclusions"][g] = [x for x in r["exclusions"][g] if x != "unstable_ratio"]
    elif variant in ("cutoff_0900", "cutoff_2359", "lookback_1", "lookback_10", "peer_overlap_120"):
        for r in out["records"]:
            r["exclusions"] = r["sensitivity_exclusions"][variant]
    else:
        raise ValueError("Unregistered input sensitivity.")
    return out


def evaluate_sensitivities(artifact, reader, costs, *, period, random_labels=None):
    from desk.s1.sensitivities import VARIANTS
    output = {}
    for variant in VARIANTS:
        inputs = artifact if variant == "exit_slippage_040" else sensitivity_inputs(artifact, variant)
        output[variant] = evaluate_inputs(inputs, reader, costs, period=period,
            slippage=.004 if variant == "exit_slippage_040" else .0015, random_labels=random_labels)
    return output
