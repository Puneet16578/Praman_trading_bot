"""Shared, directly-constructed (not file-loaded) rulebook/cost fixtures for gate/officer/engine
tests -- the real rulebook/cost config are deliberately left uncommitted until STOP 2 approval
(tests/test_desk_rulebook_integrity.py confirms the loader correctly refuses them right now), so
gate-logic tests construct a DeskRulebook/CostConfig object directly instead of going through the
file+git loader at all.
"""
from __future__ import annotations

from src.bitemporal.schema import BITEMPORAL_TABLES

from desk.lib.costs import CostConfig
from desk.lib.rulebook import DeskRulebook
from desk.lib.store import PRAMAN_FACT_TABLES


def copy_symbol_rows(prod_conn, scratch_conn, symbol: str, *, through_event_date: str | None = None) -> None:
    """Copies one real symbol's rows, across every Praman fact table, from a live/production
    connection into a fresh scratch Praman-schema store -- so tests get REAL, working data
    (build_symbol_history, get_disclosure_window, etc. all behave normally) without needing a full
    multi-GB store copy.

    `through_event_date`, when given, excludes any row with `event_date` after it (for a table that
    HAS an event_date column) -- used to simulate "this date hasn't been ingested yet" with REAL
    data that already exists in production, rather than fabricating a not-yet-real future date."""
    for table in PRAMAN_FACT_TABLES:
        available = {r['name'] for r in prod_conn.execute(f'PRAGMA table_info({table})')}
        if not available:  # optional additive table absent from an older source store
            continue
        cols = sorted((BITEMPORAL_TABLES[table].columns - {"row_id"}) & available)
        if through_event_date is not None and "event_date" in cols:
            rows = prod_conn.execute(
                f"SELECT {', '.join(cols)} FROM {table} WHERE symbol = ? AND event_date <= ?",
                (symbol, through_event_date),
            ).fetchall()
        else:
            rows = prod_conn.execute(f"SELECT {', '.join(cols)} FROM {table} WHERE symbol = ?", (symbol,)).fetchall()
        if not rows:
            continue
        placeholders = ", ".join("?" for _ in cols)
        scratch_conn.executemany(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            [tuple(r[c] for c in cols) for r in rows],
        )
    scratch_conn.commit()


def make_test_rulebook(**overrides) -> DeskRulebook:
    base = {
        "version": "test", "dated": "2026-01-01",
        "risk": {"capital_allocated_inr": 500000, "risk_per_trade_pct": 1, "max_open_risk_pct": 5,
                  "max_per_stock_pct": 10, "max_per_sector_pct": 25, "monthly_drawdown_brake_pct": 6,
                  "stress_loss_floor_pct_of_position": 10},
        "liquidity": {"max_order_pct_of_adv": 1, "stressed_volume_factor": 0.25,
                       "participation_pct_of_stressed_volume": 10, "max_days_to_exit_stressed": 3},
        "surveillance_exclusions": {"exclude_trade_for_trade_series": True, "max_asm_stage": None, "exclude_gsm": True},
        "behavioural_brakes": {"max_g7_overrides_per_month": 2, "consecutive_loss_brake_count": 3, "stress_loss_lookback_sessions": 252},
        "inference_rules": {"thresholds": {}},
        "required_evidence_dimensions": {"required": ["price", "volume", "delivery", "disclosures", "surveillance", "sector"]},
        "paper_to_live_criteria": {"min_paper_trades": 30, "min_paper_trade_days": 90,
                                     "max_unlogged_rule_violations": 0, "max_open_risk_budget_breaches": 0,
                                     "require_exit_trigger_on_every_closed_trade": True},
    }
    base.update(overrides)
    return DeskRulebook.model_validate(base)


def make_test_costs(**overrides) -> CostConfig:
    base = {
        "version": "test", "dated": "2026-01-01",
        "securities_transaction_tax": {"rate": 0.1, "unit": "pct", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "stamp_duty": {"rate": 0.015, "unit": "pct", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "exchange_transaction_charges": {"rate": 0.00297, "unit": "pct", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "sebi_turnover_fee": {"rate": 0.0001, "unit": "pct", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "gst": {"rate": 18, "unit": "pct", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "depository_charges": {"rate": 13.5, "unit": "flat", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "brokerage": {"rate": 0, "unit": "flat", "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"},
        "slippage_by_liquidity_bucket": [{"liquidity_bucket": "high", "slippage_pct": 0.05, "source": "x", "as_of_date": "2026-01-01", "status": "TO_VERIFY"}],
    }
    base.update(overrides)
    return CostConfig.model_validate(base)


COMPLETE_AXISBANK_THESIS = {
    "hypotheses": [{"statement": "Bank rerates on strong results", "test": "next quarter margin expansion", "monitor": "quarterly results"}],
    "drivers": ["sector tailwind"],
    "invalidation_conditions": ["stop hit", "thesis-breaking news"],
    "exit_price": "target/stop hit", "exit_time": "60 sessions", "exit_evidence": "thesis invalidated",
    "exit_risk": "G6 breach", "exit_portfolio": "better opportunity elsewhere",
    "horizon": "2021-12-31", "planned_entry": 750.0, "planned_stop": 700.0, "planned_target": 820.0,
    "sector": "Financials",
}
