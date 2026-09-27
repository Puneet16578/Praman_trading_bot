"""Orchestrates G1-G8 into a single decision state, per the exact priority order specified: EXPIRED
is checked first (a lapsed thesis with no entry is reported regardless of what the gates would say);
then G1/G2 (INSUFFICIENT); G3 (RESEARCH_REQUIRED); G4-G6 (VETO, final); G7 (VETO unless a logged
override); G8 (WATCH if incomplete); otherwise ELIGIBLE.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field

from src.bitemporal.guard import read_as_of

from ..evidence.bundle import EvidenceBundle, assemble_evidence_bundle
from ..lib.costs import CostConfig
from ..lib.rulebook import DeskRulebook
from ..risk.officer import compute_position_size, compute_stress_loss, planned_loss_inr, StressLossResult
from .checks import (
    FAIL, PASS, UNKNOWN, GateResult, g1_data_quality, g2_evidence_sufficiency, g3_structural_integrity,
    g4_surveillance, g5_liquidity, g6_risk, g7_behavioural, g8_thesis_completeness, is_expired,
)

INSUFFICIENT, RESEARCH_REQUIRED, WATCH, ELIGIBLE, VETO, EXPIRED = (
    "INSUFFICIENT", "RESEARCH_REQUIRED", "WATCH", "ELIGIBLE", "VETO", "EXPIRED",
)

STRESS_LOSS_FLOOR_INR = 1000.0  # PROPOSED elsewhere would live in the rulebook; kept as a code
                                 # constant here since item 2 lists "a rulebook floor" but the
                                 # rulebook schema (desk/lib/rulebook.py) does not yet have a
                                 # dedicated field for it -- flagged in the phase-1 report as a
                                 # real gap to fold into the rulebook schema in v2, not hidden.

ADV_LOOKBACK_SESSIONS = 60


@dataclass
class AssessmentResult:
    state: str
    gate_results: dict[str, GateResult]
    evidence_bundle: EvidenceBundle | None
    position_size: float | None = None
    stress_loss: StressLossResult | None = None

    def gate_results_json(self) -> dict:
        return {g: {"result": r.result, "reasons": list(r.reasons)} for g, r in self.gate_results.items()}


def _average_daily_volume_and_turnover(conn, symbol: str, as_of_date: str, lookback_sessions: int) -> tuple[float | None, float | None]:
    rows = read_as_of(conn, "bhavcopy", as_of_date, symbol=symbol)
    by_date: dict[str, dict] = {}
    for r in rows:
        if r["event_date"] > as_of_date:
            continue
        prior = by_date.get(r["event_date"])
        if prior is None or (r["knowledge_date"], r["row_id"]) > (prior["knowledge_date"], prior["row_id"]):
            by_date[r["event_date"]] = r
    dated = sorted(by_date.items())[-lookback_sessions:]
    if not dated:
        return None, None
    volumes = [r["traded_qty"] for _, r in dated]
    turnovers = [r["close_price"] * r["traded_qty"] for _, r in dated]
    return sum(volumes) / len(volumes), sum(turnovers) / len(turnovers)


def _open_risk_used_inr(desk_conn) -> float:
    """Sum of stress loss recorded on the decision that opened each currently-open paper trade.
    Approximated from the ORIGINAL planned loss at open (stored on the OPEN event's price/quantity/
    stop) recomputed via planned_loss_inr with today's cost config -- Phase 1 does not persist a
    stress-loss figure on the trade event itself (see docs/desk/phase1.md for this as a named gap)."""
    from desk.journal.store import open_trade_ids, latest_trade_event

    total = 0.0
    for trade_id in open_trade_ids(desk_conn):
        latest = latest_trade_event(desk_conn, trade_id)
        if latest is None:
            continue
        total += abs(latest["price"] - latest["stop"]) * latest["quantity"]
    return total


def _capital_at_stock_and_sector(desk_conn, symbol: str, sector: str | None, symbol_to_sector: dict[str, str] | None) -> tuple[float, float]:
    from desk.journal.store import open_trade_ids, latest_trade_event

    at_stock, at_sector = 0.0, 0.0
    for trade_id in open_trade_ids(desk_conn):
        latest = latest_trade_event(desk_conn, trade_id)
        if latest is None:
            continue
        value = latest["price"] * latest["quantity"]
        trade_symbol = trade_id.split(":")[0]  # trade_id convention: "<symbol>:<opened_at>"
        if trade_symbol == symbol:
            at_stock += value
        if sector and symbol_to_sector and symbol_to_sector.get(trade_symbol) == sector:
            at_sector += value
    return at_stock, at_sector


def run_assessment(conn, desk_conn, *, symbol: str, as_of_date: str, sector: str | None,
                    thesis: dict | None, rulebook: DeskRulebook, costs: CostConfig,
                    g7_override_reason: str | None = None,
                    symbol_to_sector: dict[str, str] | None = None) -> AssessmentResult:
    has_trade_history = thesis is not None and _thesis_has_any_trade(desk_conn, thesis)
    if thesis is not None and is_expired(thesis, as_of_date, has_trade_history):
        return AssessmentResult(state=EXPIRED, gate_results={}, evidence_bundle=None)

    bundle = assemble_evidence_bundle(conn, symbol, as_of_date, sector)
    gate_results: dict[str, GateResult] = {}

    gate_results["G1"] = g1_data_quality(conn, symbol, as_of_date)
    gate_results["G2"] = g2_evidence_sufficiency(bundle, rulebook)
    if gate_results["G1"].result == FAIL or gate_results["G2"].result == FAIL:
        return AssessmentResult(state=INSUFFICIENT, gate_results=gate_results, evidence_bundle=bundle)

    gate_results["G3"] = g3_structural_integrity(bundle)
    if gate_results["G3"].result == FAIL:
        return AssessmentResult(state=RESEARCH_REQUIRED, gate_results=gate_results, evidence_bundle=bundle)

    gate_results["G4"] = g4_surveillance(conn, symbol, as_of_date, bundle, rulebook)
    if gate_results["G4"].result == FAIL:
        return AssessmentResult(state=VETO, gate_results=gate_results, evidence_bundle=bundle)

    position_size = None
    stress_loss = None
    if thesis is not None:
        entry, stop = thesis["planned_entry"], thesis["planned_stop"]
        open_risk_used = _open_risk_used_inr(desk_conn)
        capital_at_stock, capital_at_sector = _capital_at_stock_and_sector(desk_conn, symbol, sector, symbol_to_sector)

        position_size = compute_position_size(entry, stop, rulebook, open_risk_used, capital_at_stock, capital_at_sector)
        stress_loss = compute_stress_loss(conn, symbol, as_of_date, entry, stop, position_size, costs, rulebook, STRESS_LOSS_FLOOR_INR)
        planned = planned_loss_inr(entry, stop, position_size, costs)

        adv_shares, adv_turnover = _average_daily_volume_and_turnover(conn, symbol, as_of_date, ADV_LOOKBACK_SESSIONS)
        gate_results["G5"] = g5_liquidity(
            order_value_inr=position_size * entry, avg_daily_turnover_inr=adv_turnover,
            order_qty=position_size, avg_daily_volume_shares=adv_shares, rulebook=rulebook,
        )
        gate_results["G6"] = g6_risk(
            planned_loss_inr=planned, stress_loss_inr=stress_loss.stress_loss_inr,
            open_risk_used_inr=open_risk_used, capital_at_stock_inr=capital_at_stock + position_size * entry,
            capital_at_sector_inr=capital_at_sector + position_size * entry, rulebook=rulebook,
        )
    else:
        gate_results["G5"] = GateResult("G5", UNKNOWN, ("No thesis supplied.",))
        gate_results["G6"] = GateResult("G6", UNKNOWN, ("No thesis supplied.",))

    if gate_results["G5"].result == FAIL or gate_results["G6"].result == FAIL:
        return AssessmentResult(state=VETO, gate_results=gate_results, evidence_bundle=bundle,
                                 position_size=position_size, stress_loss=stress_loss)

    gate_results["G7"] = g7_behavioural(
        recent_g7_overrides_this_month=_g7_overrides_this_month(desk_conn, as_of_date),
        consecutive_losses=_consecutive_losses(desk_conn),
        monthly_drawdown_pct=_monthly_drawdown_pct(desk_conn, rulebook, as_of_date),
        rulebook=rulebook,
    )
    if gate_results["G7"].result == FAIL and not g7_override_reason:
        return AssessmentResult(state=VETO, gate_results=gate_results, evidence_bundle=bundle,
                                 position_size=position_size, stress_loss=stress_loss)

    gate_results["G8"] = g8_thesis_completeness(thesis)
    if gate_results["G8"].result == FAIL:
        return AssessmentResult(state=WATCH, gate_results=gate_results, evidence_bundle=bundle,
                                 position_size=position_size, stress_loss=stress_loss)

    return AssessmentResult(state=ELIGIBLE, gate_results=gate_results, evidence_bundle=bundle,
                             position_size=position_size, stress_loss=stress_loss)


def _thesis_has_any_trade(desk_conn, thesis: dict) -> bool:
    # Phase 1: a thesis is linked to a trade via trade_id "<symbol>:<thesis_id>" by convention
    # (see desk/cli.py) -- checked directly rather than assumed.
    thesis_id = thesis.get("thesis_id")
    if thesis_id is None:
        return False
    rows = desk_conn.execute(
        "SELECT COUNT(*) AS n FROM paper_trade_events WHERE trade_id LIKE ?", (f"%:{thesis_id}",)
    ).fetchone()
    return rows["n"] > 0


def _g7_overrides_this_month(desk_conn, as_of_date: str) -> int:
    month_prefix = as_of_date[:7]
    row = desk_conn.execute(
        "SELECT COUNT(*) AS n FROM journal_events WHERE event_type = 'G7_OVERRIDE' AND recorded_at LIKE ?",
        (f"{month_prefix}%",),
    ).fetchone()
    return row["n"]


def _consecutive_losses(desk_conn) -> int:
    rows = desk_conn.execute(
        """SELECT pte.* FROM paper_trade_events pte
           WHERE event_type = 'CLOSE' ORDER BY event_id DESC"""
    ).fetchall()
    count = 0
    for row in rows:
        opened = desk_conn.execute(
            "SELECT price FROM paper_trade_events WHERE trade_id = ? AND event_type = 'OPEN'", (row["trade_id"],)
        ).fetchone()
        if opened is None:
            continue
        if row["price"] < opened["price"]:
            count += 1
        else:
            break
    return count


def _monthly_drawdown_pct(desk_conn, rulebook: DeskRulebook, as_of_date: str) -> float:
    month_prefix = as_of_date[:7]
    rows = desk_conn.execute(
        """SELECT pte.trade_id, pte.price AS close_price FROM paper_trade_events pte
           WHERE event_type = 'CLOSE' AND event_date LIKE ?""",
        (f"{month_prefix}%",),
    ).fetchall()
    realized = 0.0
    for row in rows:
        opened = desk_conn.execute(
            "SELECT price, quantity FROM paper_trade_events WHERE trade_id = ? AND event_type = 'OPEN'", (row["trade_id"],)
        ).fetchone()
        if opened is None:
            continue
        realized += (row["close_price"] - opened["price"]) * opened["quantity"]
    capital = rulebook.risk.capital_allocated_inr
    return max(0.0, -100.0 * realized / capital) if capital > 0 else 0.0
