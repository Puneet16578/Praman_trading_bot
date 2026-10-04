"""G1-G8, each returning a GateResult (PASS/FAIL/UNKNOWN + reasons). Deviation from the plan's
file-per-gate layout, noted plainly rather than silently: G1-G8 live together here as separate,
individually-testable functions, with desk/gates/engine.py doing only orchestration -- given the
size of everything else in Phase 1, nine near-empty files bought less than they cost.

G1 is deliberately narrower than its one-line spec description ("no date-mismatch warning in the
latest ingestion log"): logs/weekly_ingest.log is a mutable, git-ignored, append-only text file
outside the bitemporal store. Reading it would make `desk replay` non-reproducible in exactly the
way the whole point of Desk invariant D6 forbids -- the log can differ, or not exist, between when
a decision was made and when it's replayed, for reasons that have nothing to do with the store
itself. G1 checks the recorded ISIN map build timestamp against the store's trading calendar,
and checks what the store itself can prove: the requested date is a real,
populated trading day, and the target symbol has no gap on a date the wider market actually traded.
Reinstating a mutable-log-derived check would need Praman itself to persist ingestion-quality
signals as bitemporal rows (a Praman schema change, out of scope for the Desk) -- named here as a
real, deferred gap, not silently dropped.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.bitemporal.guard import read_as_of

from ..evidence.bundle import EvidenceBundle
from ..evidence.coverage import CoverageReport, compute_coverage
from ..evidence.types import Fact
from ..lib.rulebook import DeskRulebook

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"


@dataclass(frozen=True)
class GateResult:
    gate: str
    result: str
    reasons: tuple[str, ...] = field(default_factory=tuple)


def g1_data_quality(conn, symbol: str, as_of_date: str, gap_check_calendar_days: int = 10,
                    *, isin_map_built_at: str | None = None) -> GateResult:
    # NULL belongs to legacy decisions. New decisions record a timestamp or an empty
    # string (unavailable metadata), so a missing companion fails closed.
    if isin_map_built_at is not None:
        from shared.isin_map_metadata import MAX_AGE_TRADING_DAYS, trading_days_since_build
        try:
            age = trading_days_since_build(conn, isin_map_built_at, as_of_date)
        except (ValueError, TypeError):
            return GateResult("G1", FAIL, ("ISIN map build time is unavailable or unverified.",))
        if age > MAX_AGE_TRADING_DAYS:
            return GateResult("G1", FAIL, (f"ISIN map is {age} trading days old (limit {MAX_AGE_TRADING_DAYS}).",))
    market_rows = conn.execute(
        "SELECT COUNT(*) AS n FROM bhavcopy WHERE event_date = ? AND knowledge_date <= ?", (as_of_date, as_of_date)
    ).fetchone()["n"]
    if market_rows == 0:
        return GateResult("G1", FAIL, (f"No bhavcopy data at all for {as_of_date} -- the store has not ingested this date.",))

    symbol_row = conn.execute(
        "SELECT COUNT(*) AS n FROM bhavcopy WHERE event_date = ? AND symbol = ? AND knowledge_date <= ?", (as_of_date, symbol, as_of_date)
    ).fetchone()["n"]
    if symbol_row == 0:
        return GateResult("G1", FAIL, (f"No bhavcopy row for {symbol} on {as_of_date}, though other symbols traded that day.",))

    as_of = date.fromisoformat(as_of_date)
    window_start = (as_of - timedelta(days=gap_check_calendar_days)).isoformat()
    market_dates = {
        r["event_date"] for r in conn.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? AND event_date <= ? AND knowledge_date <= ?",
            (window_start, as_of_date, as_of_date),
        )
    }
    symbol_dates = {
        r["event_date"] for r in conn.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date > ? AND event_date <= ? AND symbol = ? AND knowledge_date <= ?",
            (window_start, as_of_date, symbol, as_of_date),
        )
    }
    missing = sorted(market_dates - symbol_dates)
    if missing:
        return GateResult("G1", FAIL, (f"{symbol} has no bhavcopy row on {missing}, dates the wider market traded.",))
    return GateResult("G1", PASS)


def g2_evidence_sufficiency(bundle: EvidenceBundle, rulebook: DeskRulebook, *, screening: bool = False) -> GateResult:
    coverage = compute_coverage(bundle)
    required = [d for d in rulebook.required_evidence_dimensions.required
                if not (screening and d == 'sector')]
    missing = [d for d in required if not coverage.is_present(d)]
    if missing:
        return GateResult("G2", FAIL, tuple(f"Required dimension {d!r} is UNKNOWN, not a Fact." for d in missing))
    return GateResult("G2", PASS, ("Sector is not applicable to independent mechanical research candidates.",) if screening else ())


def g3_structural_integrity(bundle: EvidenceBundle) -> GateResult:
    ev = bundle.corporate_actions
    if not isinstance(ev, Fact):
        return GateResult("G3", UNKNOWN, (ev.detail,))
    if ev.claim.cited_value:
        return GateResult("G3", FAIL, (ev.claim.text,))
    return GateResult("G3", PASS)


def g4_surveillance(conn, symbol: str, as_of_date: str, bundle: EvidenceBundle, rulebook: DeskRulebook) -> GateResult:
    ev = bundle.surveillance
    if not isinstance(ev, Fact):
        return GateResult("G4", UNKNOWN, (ev.detail,))

    reasons = []
    if rulebook.surveillance_exclusions.exclude_trade_for_trade_series:
        rows = read_as_of(conn, "bhavcopy", as_of_date, symbol=symbol, event_date=as_of_date)
        series = {r["series"] for r in rows}
        trade_for_trade = series & {"BE", "BZ"}
        if trade_for_trade:
            reasons.append(f"{symbol} trades in series {sorted(trade_for_trade)} (trade-for-trade), excluded by the rulebook.")

    asm_stage, gsm_stage = ev.claim.cited_value
    # max_asm_stage is validated at rulebook LOAD time now (desk/lib/rulebook.py's
    # SurveillanceExclusions field_validator rejects any non-null value outright) -- a rulebook
    # object reaching this function is therefore guaranteed to have max_asm_stage=None, so the
    # only real rule here is "any ASM stage vetoes."
    if asm_stage is not None:
        reasons.append(f"{symbol} is under ASM (stage {asm_stage}) as of {as_of_date}; rulebook tolerates no ASM stage.")
    if rulebook.surveillance_exclusions.exclude_gsm and gsm_stage is not None:
        reasons.append(f"{symbol} is under GSM (stage {gsm_stage}) as of {as_of_date}; excluded by the rulebook.")

    if reasons:
        return GateResult("G4", FAIL, tuple(reasons))
    return GateResult("G4", PASS)


def g5_liquidity(order_value_inr: float | None, avg_daily_turnover_inr: float | None,
                  rulebook: DeskRulebook) -> GateResult:
    """days_to_exit = order_value / (participation_pct/100 * stressed_volume_factor *
    avg_daily_turnover) -- you cannot BE the entire stressed-volume pool without moving the market
    against yourself, so days-to-exit assumes you only take `participation_pct` of the already-
    stressed daily turnover, not all of it. (Previously computed from raw share volume alone,
    without a participation assumption -- for an order already capped at ~1% of ADV by the check
    above, that made this specific cap unable to ever bind; participation_pct closes that gap.)
    """
    if order_value_inr is None or avg_daily_turnover_inr is None:
        return GateResult("G5", UNKNOWN, ("No candidate order size to check -- supply a thesis with a planned entry/stop.",))
    if avg_daily_turnover_inr <= 0:
        return GateResult("G5", UNKNOWN, ("Average daily turnover is not computable (insufficient trailing history).",))

    reasons = []
    order_pct_of_adv = 100.0 * order_value_inr / avg_daily_turnover_inr
    if order_pct_of_adv > rulebook.liquidity.max_order_pct_of_adv:
        reasons.append(f"Order is {order_pct_of_adv:.2f}% of average daily turnover, exceeding the {rulebook.liquidity.max_order_pct_of_adv}% cap.")

    achievable_daily_turnover = (
        rulebook.liquidity.participation_pct_of_stressed_volume / 100.0
        * rulebook.liquidity.stressed_volume_factor
        * avg_daily_turnover_inr
    )
    days_to_exit = order_value_inr / achievable_daily_turnover if achievable_daily_turnover > 0 else float("inf")
    if days_to_exit > rulebook.liquidity.max_days_to_exit_stressed:
        reasons.append(f"Exiting under stressed volume at {rulebook.liquidity.participation_pct_of_stressed_volume}% "
                        f"participation would take {days_to_exit:.1f} sessions, exceeding the "
                        f"{rulebook.liquidity.max_days_to_exit_stressed}-session cap.")

    if reasons:
        return GateResult("G5", FAIL, tuple(reasons))
    return GateResult("G5", PASS)


def g6_risk(planned_loss_inr: float | None, stress_loss_inr: float | None, open_risk_used_inr: float,
            capital_at_stock_inr: float, capital_at_sector_inr: float, rulebook: DeskRulebook) -> GateResult:
    if planned_loss_inr is None or stress_loss_inr is None:
        return GateResult("G6", UNKNOWN, ("No candidate trade to size -- supply a thesis with a planned entry/stop.",))

    capital = rulebook.risk.capital_allocated_inr
    reasons = []
    max_per_trade = capital * rulebook.risk.risk_per_trade_pct / 100.0
    if planned_loss_inr > max_per_trade:
        reasons.append("Planned loss including both-side costs exceeds the per-trade risk cap.")
    max_open_risk = capital * rulebook.risk.max_open_risk_pct / 100.0
    if open_risk_used_inr + stress_loss_inr > max_open_risk:
        reasons.append(f"Adding this trade's stress loss (Rs {stress_loss_inr:,.0f}) to open risk already used "
                        f"(Rs {open_risk_used_inr:,.0f}) would exceed the open-risk budget (Rs {max_open_risk:,.0f}).")

    max_per_stock = capital * rulebook.risk.max_per_stock_pct / 100.0
    if capital_at_stock_inr > max_per_stock:
        reasons.append(f"Capital at this stock (Rs {capital_at_stock_inr:,.0f}) would exceed the per-stock cap (Rs {max_per_stock:,.0f}).")

    max_per_sector = capital * rulebook.risk.max_per_sector_pct / 100.0
    if capital_at_sector_inr > max_per_sector:
        reasons.append(f"Capital at this sector (Rs {capital_at_sector_inr:,.0f}) would exceed the per-sector cap (Rs {max_per_sector:,.0f}).")

    if reasons:
        return GateResult("G6", FAIL, tuple(reasons))
    return GateResult("G6", PASS)


def g7_behavioural(recent_g7_overrides_this_month: int, consecutive_losses: int, monthly_drawdown_pct: float,
                    rulebook: DeskRulebook) -> GateResult:
    reasons = []
    if recent_g7_overrides_this_month >= rulebook.behavioural_brakes.max_g7_overrides_per_month:
        reasons.append(f"{recent_g7_overrides_this_month} G7 overrides already logged this month (limit {rulebook.behavioural_brakes.max_g7_overrides_per_month}).")
    if consecutive_losses >= rulebook.behavioural_brakes.consecutive_loss_brake_count:
        reasons.append(f"{consecutive_losses} consecutive losing trades (brake at {rulebook.behavioural_brakes.consecutive_loss_brake_count}).")
    if monthly_drawdown_pct >= rulebook.risk.monthly_drawdown_brake_pct:
        reasons.append(f"Monthly drawdown {monthly_drawdown_pct:.2f}% has crossed the {rulebook.risk.monthly_drawdown_brake_pct}% brake.")
    if reasons:
        return GateResult("G7", FAIL, tuple(reasons))
    return GateResult("G7", PASS)


def g8_thesis_completeness(thesis: dict | None) -> GateResult:
    if thesis is None:
        return GateResult("G8", FAIL, ("No thesis supplied.",))
    required = ("hypotheses", "invalidation_conditions", "exit_price", "exit_time", "exit_evidence",
                "exit_risk", "exit_portfolio", "horizon")
    missing = [f for f in required if not thesis.get(f)]
    if missing:
        return GateResult("G8", FAIL, tuple(f"Thesis missing {f!r}." for f in missing))
    return GateResult("G8", PASS)


def is_expired(thesis: dict | None, as_of_date: str, has_open_or_past_trade: bool) -> bool:
    if thesis is None or has_open_or_past_trade:
        return False
    return thesis["horizon"] < as_of_date
