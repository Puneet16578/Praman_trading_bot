"""Orchestrates G1-G8. EVERY gate is evaluated on EVERY assessment -- no short-circuiting -- and the
final state is DERIVED from the full set of eight results afterward, by the same priority order as
before (G1/G2 -> INSUFFICIENT; G3 -> RESEARCH_REQUIRED; G4-G6 -> VETO, final; G7 -> VETO unless a
logged override; G8 -> WATCH if incomplete; otherwise ELIGIBLE). This is a deliberate change from an
earlier version that stopped at the first failing gate: with short-circuiting, a trade-for-trade
stock with an UNKNOWN delivery dimension showed INSUFFICIENT (from G2) with no record that G4 would
ALSO have vetoed it -- silently hiding information later phases' shadow policies (and a human
reviewing the decision record) need. EXPIRED remains a distinct pre-check: a thesis whose horizon has
already lapsed with no trade ever opened is reported as EXPIRED without running the gate suite at
all, since there is no live decision left to evaluate.
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

ADV_LOOKBACK_SESSIONS = 60
_CURRENT_MAP = object()


@dataclass
class AssessmentResult:
    state: str
    gate_results: dict[str, GateResult]
    evidence_bundle: EvidenceBundle | None
    position_size: float | None = None
    stress_loss: StressLossResult | None = None
    as_of_is_live: bool = True
    isin_map_built_at: str | None = None

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


def _derive_state(gate_results: dict[str, GateResult], g7_override_reason: str | None) -> str:
    """The priority mapping, applied to an already-COMPLETE set of eight gate results -- this
    function does not run anything, it only reads results computed elsewhere."""
    if gate_results["G1"].result == FAIL or gate_results["G2"].result == FAIL:
        return INSUFFICIENT
    if gate_results["G3"].result == FAIL:
        return RESEARCH_REQUIRED
    if gate_results["G4"].result == FAIL or gate_results["G5"].result == FAIL or gate_results["G6"].result == FAIL:
        return VETO
    if gate_results["G7"].result == FAIL and not g7_override_reason:
        return VETO
    if gate_results["G8"].result == FAIL:
        return WATCH
    return ELIGIBLE


def run_assessment(conn, desk_conn, *, symbol: str, as_of_date: str, sector: str | None,
                    thesis: dict | None, rulebook: DeskRulebook, costs: CostConfig,
                    g7_override_reason: str | None = None,
                    symbol_to_sector: dict[str, str] | None = None,
                    isin_map_built_at=_CURRENT_MAP) -> AssessmentResult:
    from desk.paper.open import is_as_of_live
    if isin_map_built_at is _CURRENT_MAP:
        from shared.isin_map_metadata import verified_built_at
        isin_map_built_at = verified_built_at()

    as_of_live = is_as_of_live(conn, as_of_date)

    has_trade_history = thesis is not None and _thesis_has_any_trade(desk_conn, thesis)
    if thesis is not None and is_expired(thesis, as_of_date, has_trade_history):
        return AssessmentResult(state=EXPIRED, gate_results={}, evidence_bundle=None, as_of_is_live=as_of_live,
                                isin_map_built_at=isin_map_built_at)

    bundle = assemble_evidence_bundle(conn, symbol, as_of_date, sector)
    gate_results: dict[str, GateResult] = {}

    # Every gate below is evaluated unconditionally -- none of them depend on an EARLIER gate's
    # PASS/FAIL result to run (G3/G4 read the evidence bundle directly; G5/G6 depend only on
    # whether a THESIS was supplied, not on G1-G4's outcome; G7/G8 depend on the journal/thesis
    # only). Deriving the state from the complete set afterward, via _derive_state(), is what makes
    # "record every gate's result every time" possible.
    gate_results["G1"] = g1_data_quality(conn, symbol, as_of_date, isin_map_built_at=isin_map_built_at)
    gate_results["G2"] = g2_evidence_sufficiency(bundle, rulebook)
    gate_results["G3"] = g3_structural_integrity(bundle)
    gate_results["G4"] = g4_surveillance(conn, symbol, as_of_date, bundle, rulebook)

    position_size = None
    stress_loss = None
    if thesis is not None:
        entry, stop = thesis["planned_entry"], thesis["planned_stop"]
        open_risk_used = _open_risk_used_inr(desk_conn)
        capital_at_stock, capital_at_sector = _capital_at_stock_and_sector(desk_conn, symbol, sector, symbol_to_sector)

        position_size = compute_position_size(entry, stop, rulebook, open_risk_used, capital_at_stock, capital_at_sector)

        if position_size == 0:
            # Fix 1 (post-STOP-3 review): NSE trades in whole shares. compute_position_size already
            # floors to a whole share after every cap; if that floors to 0, a single share already
            # exceeds the tightest cap (the per-trade risk budget itself, or whatever open-risk/
            # per-stock/per-sector room is left) -- there is no valid order to size stress loss or
            # liquidity against, so this is a stated G6 FAIL (-> VETO via the priority mapping),
            # never a silent size-zero PASS.
            stress_loss = None
            gate_results["G5"] = GateResult("G5", UNKNOWN, ("Position size is 0 whole shares -- no order to check liquidity for.",))
            gate_results["G6"] = GateResult("G6", FAIL, (
                "Position size floors to 0 whole shares after risk/budget caps -- a single share "
                "already exceeds the allowed risk-per-trade, open-risk, per-stock, or per-sector budget.",
            ))
        else:
            stress_loss = compute_stress_loss(conn, symbol, as_of_date, entry, stop, position_size, costs, rulebook)
            planned = planned_loss_inr(entry, stop, position_size, costs)

            _adv_shares, adv_turnover = _average_daily_volume_and_turnover(conn, symbol, as_of_date, ADV_LOOKBACK_SESSIONS)
            gate_results["G5"] = g5_liquidity(
                order_value_inr=position_size * entry, avg_daily_turnover_inr=adv_turnover, rulebook=rulebook,
            )
            gate_results["G6"] = g6_risk(
                planned_loss_inr=planned, stress_loss_inr=stress_loss.stress_loss_inr,
                open_risk_used_inr=open_risk_used, capital_at_stock_inr=capital_at_stock + position_size * entry,
                capital_at_sector_inr=capital_at_sector + position_size * entry, rulebook=rulebook,
            )
    else:
        gate_results["G5"] = GateResult("G5", UNKNOWN, ("No thesis supplied.",))
        gate_results["G6"] = GateResult("G6", UNKNOWN, ("No thesis supplied.",))

    gate_results["G7"] = g7_behavioural(
        recent_g7_overrides_this_month=_g7_overrides_this_month(desk_conn, as_of_date),
        consecutive_losses=_consecutive_losses(desk_conn),
        monthly_drawdown_pct=_monthly_drawdown_pct(desk_conn, rulebook, as_of_date),
        rulebook=rulebook,
    )
    gate_results["G8"] = g8_thesis_completeness(thesis)

    state = _derive_state(gate_results, g7_override_reason)
    return AssessmentResult(state=state, gate_results=gate_results, evidence_bundle=bundle,
                             position_size=position_size, stress_loss=stress_loss, as_of_is_live=as_of_live,
                             isin_map_built_at=isin_map_built_at)


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
    """`recorded_at` is UTC; `as_of_date` is an NSE (IST) date. Compare months in IST, or an
    override between 00:00 and 05:30 IST on the 1st counts toward the previous month (P8-018)."""
    from datetime import datetime
    from shared.market_time import market_date

    month_prefix = as_of_date[:7]
    rows = desk_conn.execute(
        "SELECT recorded_at FROM journal_events WHERE event_type = 'G7_OVERRIDE'"
    ).fetchall()
    return sum(1 for r in rows
               if market_date(datetime.fromisoformat(r["recorded_at"])).isoformat()[:7] == month_prefix)


def _closed_trade_pnl_inr(desk_conn, close_row) -> float | None:
    """The ONE realized-P&L computation (desk/risk/officer.py:realized_pnl_inr), applied to one
    CLOSE row and its matching OPEN row -- used by both functions below, so a trade's classification
    as a loss (or its contribution to drawdown) never depends on a raw price comparison that ignores
    quantity or cost (post-STOP-3-plus consistency fix). Returns None if the OPEN row is missing
    (should not happen for a real CLOSE, but never silently treated as a zero-P&L trade)."""
    from desk.risk.officer import realized_pnl_inr

    opened = desk_conn.execute(
        "SELECT price, quantity, buy_cost_inr FROM paper_trade_events WHERE trade_id = ? AND event_type = 'OPEN'",
        (close_row["trade_id"],),
    ).fetchone()
    if opened is None:
        return None
    return realized_pnl_inr(
        entry=opened["price"], exit_price=close_row["price"], quantity=opened["quantity"],
        buy_cost_inr=opened["buy_cost_inr"] or 0.0, sell_cost_inr=close_row["sell_cost_inr"] or 0.0,
    )


def _consecutive_losses(desk_conn) -> int:
    rows = desk_conn.execute(
        """SELECT pte.* FROM paper_trade_events pte
           WHERE event_type = 'CLOSE' ORDER BY event_id DESC"""
    ).fetchall()
    count = 0
    for row in rows:
        pnl = _closed_trade_pnl_inr(desk_conn, row)
        if pnl is None:
            continue
        if pnl < 0:
            count += 1
        else:
            break
    return count


def _monthly_drawdown_pct(desk_conn, rulebook: DeskRulebook, as_of_date: str) -> float:
    month_prefix = as_of_date[:7]
    rows = desk_conn.execute(
        """SELECT pte.* FROM paper_trade_events pte
           WHERE event_type = 'CLOSE' AND event_date LIKE ?""",
        (f"{month_prefix}%",),
    ).fetchall()
    realized = 0.0
    for row in rows:
        pnl = _closed_trade_pnl_inr(desk_conn, row)
        if pnl is None:
            continue
        realized += pnl
    capital = rulebook.risk.capital_allocated_inr
    return max(0.0, -100.0 * realized / capital) if capital > 0 else 0.0
