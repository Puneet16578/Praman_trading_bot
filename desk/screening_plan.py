"""Frozen event-close research plan and separate next-session execution observations."""
from __future__ import annotations

import math
from dataclasses import asdict

from src.bitemporal.guard import latest_as_of
from src.signals.price_adjustment import compute_adjustment_factor
from desk.gates.engine import run_assessment
from desk.gates.checks import g5_liquidity, g6_risk
from desk.risk.officer import planned_loss_inr


def decision_plan(conn, symbol: str, as_of: str, *, stop_multiple: float = 2.0) -> dict:
    """Twenty arithmetic true ranges on one adjustment basis, using 21 actual sessions."""
    rows = sorted((r for r in latest_as_of(conn, "bhavcopy", as_of, symbol=symbol, series="EQ")
                   if r["event_date"] <= as_of), key=lambda r: r["event_date"])[-21:]
    if len(rows) != 21 or rows[-1]["event_date"] != as_of:
        raise ValueError("ATR20 requires 21 visible EQ sessions ending on the event date.")
    adjusted = []
    for row in rows:
        factor = compute_adjustment_factor(conn, symbol, row["event_date"], as_of)
        values = [row[name] / factor for name in ("high_price", "low_price", "close_price")]
        if not all(math.isfinite(v) and v > 0 for v in values) or values[0] < values[1]:
            raise ValueError("Invalid adjusted OHLC in the ATR window.")
        adjusted.append(values)
    true_ranges = [max(high-low, abs(high-adjusted[i-1][2]), abs(low-adjusted[i-1][2]))
                   for i, (high, low, _) in enumerate(adjusted) if i]
    atr = sum(true_ranges) / 20
    price = adjusted[-1][2]
    stop = price - stop_multiple * atr
    if not math.isfinite(stop_multiple) or stop_multiple <= 0 or not 0 < stop < price:
        raise ValueError("The fixed ATR plan has no valid positive stop below the decision price.")
    return {"decision_price": price, "atr20": atr, "stop_level": stop,
            "stop_multiple": stop_multiple, "atr_dates": [r["event_date"] for r in rows],
            "entry_convention": "EVENT_CLOSE_DECISION_NEXT_SESSION_OPEN_EXECUTION"}


def screen_event(conn, desk_conn, symbol, event_date, rulebook, costs, *, isin_map_built_at=None):
    """Use the existing gate orchestrator; a missing plan cannot become a pass."""
    from src.signals.price_adjustment import UnadjustableWindowError
    try:
        plan = decision_plan(conn, symbol, event_date, stop_multiple=rulebook.screening.stop_multiple)
        thesis = {"planned_entry": plan["decision_price"], "planned_stop": plan["stop_level"]}
    except (ValueError, UnadjustableWindowError):
        plan = {"plan_error": "ATR20 unavailable, unadjustable, or invalid positive stop."}
        thesis = None
    assessment = run_assessment(conn, desk_conn, symbol=symbol, as_of_date=event_date,
                                sector=None, thesis=thesis, rulebook=rulebook, costs=costs,
                                isin_map_built_at=isin_map_built_at, screening=True)
    plan["quantity"] = int(assessment.position_size or 0)
    plan["stress"] = asdict(assessment.stress_loss) if assessment.stress_loss else None
    plan["portfolio_assumption"] = "Independent research candidate; empty hypothetical portfolio."
    # Retain the exact ADV denominator used by the decision gate for fill-time flagging.
    from desk.gates.engine import _average_daily_volume_and_turnover, ADV_LOOKBACK_SESSIONS
    _, plan["adv_turnover"] = _average_daily_volume_and_turnover(conn, symbol, event_date, ADV_LOOKBACK_SESSIONS)
    return plan, assessment


def execution_observation(conn, symbol, event_date, as_of, plan, rulebook, costs):
    """Return None while awaiting the next market session; never substitute a later fill."""
    dates = conn.execute("SELECT DISTINCT event_date FROM bhavcopy WHERE event_date>? "
                         "AND event_date<=? AND knowledge_date<=? ORDER BY event_date LIMIT 1",
                         (event_date, as_of, as_of)).fetchall()
    if not dates:
        return None
    session = dates[0][0]
    result = {"execution_date": session, "knowledge_date": as_of,
              "quantity": plan["quantity"], "decision_price": plan.get("decision_price"),
              "stop_level": plan.get("stop_level"), "fill": None,
              "gap_inr": None, "gap_pct": None, "immediate_gap_through": False,
              "cap_breaches": [], "status": "NO_FILL", "reason": ""}
    if not plan["quantity"]:
        result["reason"] = "No positive whole-share quantity in the frozen decision."
        return result
    rows = latest_as_of(conn, "bhavcopy", as_of, symbol=symbol, event_date=session)
    rows = sorted((r for r in rows if r["series"] in ("EQ", "BE", "BZ")),
                  key=lambda r: ("EQ", "BE", "BZ").index(r["series"]))
    if not rows or not rows[0]["open_price"] or rows[0]["open_price"] <= 0:
        result["reason"] = "No usable opening price for the security on the next market session; cause unverified."
        return result
    fill = rows[0]["open_price"]
    quantity, stop, decision = plan["quantity"], plan["stop_level"], plan["decision_price"]
    result.update(status="FILLED", fill=fill, gap_inr=fill-decision,
                  gap_pct=100*(fill/decision-1), immediate_gap_through=fill <= stop)
    # Reprice only the fixed decision scenarios: do not consume post-decision volatility.
    loss = plan["stress"]
    planned = planned_loss_inr(fill, min(stop, fill), quantity, costs)
    stress = max(planned, loss["floor_component_inr"] * fill/decision,
                 (loss["worst_gap_component_inr"] or 0) * fill/decision,
                 (loss["locked_circuit_loss_inr"] or 0) * fill/decision)
    risk = g6_risk(planned, stress, 0, fill*quantity, fill*quantity, rulebook)
    result["cap_breaches"].extend(risk.reasons)
    if planned > rulebook.risk.capital_allocated_inr * rulebook.risk.risk_per_trade_pct / 100:
        result["cap_breaches"].append("Fill exceeds per-trade planned-risk cap.")
    liquidity = g5_liquidity(order_value_inr=fill*quantity, avg_daily_turnover_inr=plan["adv_turnover"], rulebook=rulebook)
    result["cap_breaches"].extend(liquidity.reasons)
    return result
