"""Sizing and stress loss. Long-only in Phase 1 (entry > stop < target is the only shape the
rulebook and gates assume) -- nothing here computes or accepts a short position.

Costs are computed from the loaded cost config only. Dated circuit-band snapshots
add a fixed-band lock scenario; dynamic ranges and missing snapshots remain explicit.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from src.signals.event_catalogue import build_symbol_history
from src.signals.price_adjustment import adjusted_close, compute_adjustment_factor

from ..lib.costs import CostConfig
from ..lib.rulebook import DeskRulebook
from ..circuit_bands import CircuitBand


def round_trip_cost_inr(price: float, quantity: float, costs: CostConfig, side: str) -> float:
    """`side` is "buy" or "sell" -- stamp duty is buy-side only, depository charges are (in this
    cost model) sell-side only, matching real NSE/CDSL practice; every other charge applies to
    both legs identically."""
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    turnover = price * quantity
    stt = turnover * costs.securities_transaction_tax.rate / 100.0
    exchange = turnover * costs.exchange_transaction_charges.rate / 100.0
    sebi = turnover * costs.sebi_turnover_fee.rate / 100.0
    brokerage = costs.brokerage.rate
    stamp = turnover * costs.stamp_duty.rate / 100.0 if side == "buy" else 0.0
    depository = costs.depository_charges.rate if side == "sell" else 0.0
    gst = (brokerage + exchange + sebi) * costs.gst.rate / 100.0
    return stt + exchange + sebi + brokerage + stamp + depository + gst


def planned_loss_inr(entry: float, stop: float, quantity: float, costs: CostConfig) -> float:
    """Gross per-share loss times quantity, PLUS round-trip costs on both legs (buy at entry,
    sell at stop) -- costs on both sides, per item 7's explicit instruction."""
    gross = abs(entry - stop) * quantity
    return gross + round_trip_cost_inr(entry, quantity, costs, "buy") + round_trip_cost_inr(stop, quantity, costs, "sell")


def realized_pnl_inr(entry: float, exit_price: float, quantity: float,
                      buy_cost_inr: float, sell_cost_inr: float) -> float:
    """The ONE function that computes realized P&L for a closed paper trade -- used for every exit
    type, manual or automatic (stop, target, time, evidence, risk, portfolio), so two identical
    trades always show identical P&L regardless of which trigger closed them (post-STOP-3-plus
    consistency fix). Both `entry` and `exit_price` are ALWAYS the store's raw prices -- costs are
    subtracted here explicitly, never folded into either price beforehand."""
    gross = (exit_price - entry) * quantity
    return gross - buy_cost_inr - sell_cost_inr


def worst_overnight_gap_loss_inr(conn, symbol: str, as_of_date: str, quantity: float, lookback_sessions: int) -> float | None:
    """The largest adverse (downward) overnight gap -- close(t) to adjusted open(t+1) -- over the
    trailing `lookback_sessions`, expressed as an INR loss on `quantity` shares at TODAY's price
    scale (the gap's own percentage size, applied to `quantity` at the CURRENT close, not at the
    historical price level, so this is a forward-looking risk estimate, not a historical dollar
    figure). Returns None if there isn't enough history to compute even one gap.
    """
    hist = build_symbol_history(conn, symbol)
    days = hist.trading_days
    if as_of_date not in days:
        return None
    idx = days.index(as_of_date)
    start_idx = max(0, idx - lookback_sessions)
    if start_idx >= idx:
        return None

    current_close_row = hist.price_row_as_of(as_of_date, as_of_date)
    if current_close_row is None:
        return None
    current_close = current_close_row["close_price"] * hist.cum_factor_up_to(as_of_date)

    worst_pct = 0.0
    for i in range(start_idx, idx):
        d0, d1 = days[i], days[i + 1]
        try:
            close0 = adjusted_close(conn, symbol, d0, as_of_date)
            row1 = hist.price_row_as_of(d1, as_of_date)
            if row1 is None:
                continue
            factor1 = compute_adjustment_factor(conn, symbol, d1, as_of_date)
            open1 = row1["open_price"] / factor1
        except Exception:
            continue  # an unadjustable window inside this trailing scan is skipped, not fatal to the whole computation
        if close0 <= 0:
            continue
        gap_pct = (open1 - close0) / close0
        worst_pct = min(worst_pct, gap_pct)  # most negative = worst

    if worst_pct >= 0:
        return 0.0
    return abs(worst_pct) * current_close * quantity


@dataclass
class StressLossResult:
    stress_loss_inr: float
    planned_loss_component_inr: float
    worst_gap_component_inr: float | None
    floor_component_inr: float
    circuit_band_caveat: str = "Circuit band UNKNOWN; locked-circuit loss is unavailable."
    locked_circuit_loss_inr: float | None = None
    circuit_band: CircuitBand = CircuitBand()


def compute_stress_loss(conn, symbol: str, as_of_date: str, entry: float, stop: float, quantity: float,
                         costs: CostConfig, rulebook: DeskRulebook,
                         circuit_band: CircuitBand | None = None) -> StressLossResult:
    """Floor is now `stress_loss_floor_pct_of_position` (rulebook), not a hardcoded rupee constant
    -- a fixed rupee floor means nothing across different capital sizes, and hardcoding it in code
    is exactly what the constitution's "gates, not scores; nothing invented" discipline forbids."""
    planned = planned_loss_inr(entry, stop, quantity, costs)
    gap_loss = worst_overnight_gap_loss_inr(conn, symbol, as_of_date, quantity, rulebook.behavioural_brakes.stress_loss_lookback_sessions)
    position_value = entry * quantity
    floor = position_value * rulebook.risk.stress_loss_floor_pct_of_position / 100.0
    components = [planned, floor] + ([gap_loss] if gap_loss is not None else [])
    band = circuit_band or CircuitBand()
    locked = None
    if band.kind == "FIXED":
        locked = position_value * band.percent / 100.0 * rulebook.risk.circuit_lock_days
        components.append(locked)
        caveat = f"Fixed-band scenario: band x {rulebook.risk.circuit_lock_days} lock days; not an exit guarantee."
    elif band.kind == "DYNAMIC":
        caveat = "Dynamic operating range can flex; no fixed-band locked-circuit loss is asserted."
    else:
        caveat = "Circuit band UNKNOWN; locked-circuit loss is unavailable."
    return StressLossResult(
        stress_loss_inr=max(components),
        planned_loss_component_inr=planned,
        worst_gap_component_inr=gap_loss,
        floor_component_inr=floor,
        locked_circuit_loss_inr=locked,
        circuit_band=band,
        circuit_band_caveat=caveat,
    )


def compute_position_size(entry: float, stop: float, rulebook: DeskRulebook,
                           open_risk_used_inr: float, capital_at_stock_inr: float,
                           capital_at_sector_inr: float) -> float:
    """Size = risk per trade / (entry - stop), then capped by whatever budget is left in the
    open-risk, per-stock, and per-sector limits (never negative -- a fully-used budget caps size to
    zero, it does not go negative and it is not the risk officer's job to say VETO; G6 does that).

    Floored to a whole share AFTER every cap is applied (Fix 1, post-STOP-3 review) -- NSE equity
    trades in whole shares, so a raw/capped size of e.g. 66.67 must become 66, never a number the
    exchange itself would reject. Flooring only at the very end (not on each intermediate cap) means
    every downstream consumer -- planned loss, stress loss, G5's order value, G6's capital-at-stock
    addition -- automatically sees the same final integer quantity, with no separate rounding step
    to keep in sync. If the floored result is 0 (a single share already exceeds the tightest cap),
    the caller (desk/gates/engine.py) reports this as a G6 FAIL, not a silent size-zero PASS."""
    per_share_risk = abs(entry - stop)
    if per_share_risk <= 0:
        raise ValueError("entry and stop must differ -- cannot size a position with zero per-share risk.")

    capital = rulebook.risk.capital_allocated_inr
    risk_budget_inr = capital * rulebook.risk.risk_per_trade_pct / 100.0
    raw_size = risk_budget_inr / per_share_risk

    open_risk_room = max(0.0, capital * rulebook.risk.max_open_risk_pct / 100.0 - open_risk_used_inr)
    size_from_open_risk = open_risk_room / per_share_risk

    stock_room = max(0.0, capital * rulebook.risk.max_per_stock_pct / 100.0 - capital_at_stock_inr)
    size_from_stock_cap = stock_room / entry if entry > 0 else 0.0

    sector_room = max(0.0, capital * rulebook.risk.max_per_sector_pct / 100.0 - capital_at_sector_inr)
    size_from_sector_cap = sector_room / entry if entry > 0 else 0.0

    capped = max(0.0, min(raw_size, size_from_open_risk, size_from_stock_cap, size_from_sector_cap))
    return float(math.floor(capped))
