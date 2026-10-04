"""The Desk's rulebook: every risk, liquidity, exclusion, and behavioural limit the gates and risk
officer enforce, typed and validated, never hardcoded in code. Loaded by version -- see
rulebook/ACTIVE -- and identified by the SHA-256 of its LF-normalized content
(desk/lib/versioned_config.py), which every decision records so `desk replay` can prove it ran
against the exact same rulebook.

Values are proposed by Claude, marked PROPOSED with a one-line reason each, and are not binding
until the user approves or changes them (STOP 2, docs/desk/DESIGN.md's own working procedure) --
this module validates SHAPE and TYPE, never picks or defends a specific number.
"""
from __future__ import annotations
from pathlib import Path
import re
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator, AliasChoices

from .versioned_config import (
    VersionedConfigError, resolve_active_version, require_git_clean_and_tracked, sha256_lf_normalized,
)

RULEBOOK_DIR = Path(__file__).resolve().parents[2] / "rulebook"
ACTIVE_POINTER_PATH = RULEBOOK_DIR / "ACTIVE"


class RiskLimits(BaseModel):
    circuit_lock_days: int = Field(2, ge=1, description="Fixed-band locked-exit scenario; user-approved Phase A default")
    capital_allocated_inr: float = Field(..., gt=0)
    risk_per_trade_pct: float = Field(..., gt=0, le=100)
    max_open_risk_pct: float = Field(..., gt=0, le=100, description="On STRESS loss, not planned loss")
    max_per_stock_pct: float = Field(..., gt=0, le=100)
    max_per_sector_pct: float = Field(..., gt=0, le=100)
    monthly_drawdown_brake_pct: float = Field(..., gt=0, le=100)
    stress_loss_floor_pct_of_position: float = Field(
        ..., gt=0, le=100,
        description="Stress loss floor as a % of position VALUE (entry x quantity), replacing a "
                    "fixed rupee floor -- a fixed rupee number means nothing across capital sizes "
                    "and was a hardcoded constant in code, which the constitution forbids.",
    )


class LiquidityLimits(BaseModel):
    max_order_pct_of_adv: float = Field(..., gt=0, le=100, description="Order value as a share of average daily turnover")
    stressed_volume_factor: float = Field(..., gt=0, le=1, description="Assumed fraction of ADV actually available under stress")
    participation_pct_of_stressed_volume: float = Field(
        ..., gt=0, le=100,
        description="You cannot BE the entire stressed-volume pool without moving the market "
                    "against yourself -- days-to-exit assumes you only take this share of the "
                    "already-stressed daily volume. days_to_exit = order_value / "
                    "(participation_pct/100 * stressed_volume_factor * avg_daily_turnover).",
    )
    max_days_to_exit_stressed: float = Field(..., gt=0)


class SurveillanceExclusions(BaseModel):
    exclude_trade_for_trade_series: bool
    max_asm_stage: str | None = Field(None, description="Highest tolerated ASM stage; null means any ASM stage vetoes")
    exclude_gsm: bool

    @field_validator("max_asm_stage")
    @classmethod
    def _reject_non_null_stage_for_now(cls, value: str | None) -> str | None:
        if value is not None:
            raise ValueError(
                f"max_asm_stage={value!r} is not supported yet -- stage-ordering logic (deciding "
                "whether a given ASM stage is 'within' a tolerated ceiling) does not exist in "
                "Phase 1. Rejected at LOAD time, not deferred to a NotImplementedError mid-"
                "assessment. Only null (any ASM stage vetoes) is accepted until that logic is built."
            )
        return value


class BehaviouralBrakes(BaseModel):
    max_g7_overrides_per_month: int = Field(..., ge=0)
    consecutive_loss_brake_count: int = Field(..., ge=1)
    stress_loss_lookback_sessions: int = Field(..., ge=1, description="Trailing window for the worst overnight gap used in stress loss")


class InferenceRuleThresholds(BaseModel):
    thresholds: dict[str, float] = Field(default_factory=dict)


class RequiredEvidenceDimensions(BaseModel):
    required: list[str] = Field(..., min_length=1)


class PaperToLiveCriteria(BaseModel):
    """ALL of these must hold before live use per the rulebook's own approved criteria -- checked
    together, not any subset. A "rule violation" is acting against the rulebook WITHOUT a logged
    override; a logged G7 override is a separate, explicitly-permitted event and is not counted
    here (see behavioural_brakes.max_g7_overrides_per_month for that limit instead)."""
    min_paper_trades: int = Field(..., ge=1)
    min_paper_trade_days: int = Field(..., ge=1)
    max_unlogged_rule_violations: int = Field(..., ge=0)
    max_open_risk_budget_breaches: int = Field(..., ge=0)
    require_exit_trigger_on_every_closed_trade: bool


class ScreeningConvention(BaseModel):
    stop_multiple: float = Field(2.0, gt=0, validation_alias=AliasChoices('screening_stop_atr_multiple', 'stop_multiple'),
                                description="Fixed research stop distance in ATR20 units")


class OperationalGate(BaseModel):
    min_calendar_days: int = Field(..., ge=1)
    min_closed_paper_trades: int = Field(..., ge=1)
    max_unlogged_rule_violations: int = Field(..., ge=0)
    max_open_risk_budget_breaches: int = Field(..., ge=0)
    require_recorded_exit_on_every_trade: bool
    max_open_high_severity_defects: int = Field(..., ge=0)


class EdgeConfidenceGate(BaseModel):
    min_logged_opportunities: int = Field(..., ge=1)
    min_distinct_market_regimes: int = Field(..., ge=2)
    require_out_of_sample_evaluation: bool
    require_positive_expectancy_after_costs: bool
    bootstrap_confidence_level: float = Field(..., gt=0, lt=1)
    bootstrap_lower_bound_must_exceed: float
    require_equal_weighted_market_comparison: bool
    require_neighbouring_parameter_stability: bool


class DeskRulebook(BaseModel):
    version: str
    dated: str
    risk: RiskLimits
    liquidity: LiquidityLimits
    surveillance_exclusions: SurveillanceExclusions
    behavioural_brakes: BehaviouralBrakes
    inference_rules: InferenceRuleThresholds
    required_evidence_dimensions: RequiredEvidenceDimensions
    paper_to_live_criteria: PaperToLiveCriteria | None = None
    operational_gate: OperationalGate | None = None
    edge_confidence_gate: EdgeConfidenceGate | None = None
    screening: ScreeningConvention = Field(default_factory=ScreeningConvention)
    automation_level: Literal['A0', 'A1', 'A2', 'A3', 'A4'] = Field(
        'A0', description="Highest automation the Desk may perform (docs/desk/TRADING_BLUEPRINT.md "
                          "section 8, amendment 4). Versions before v3 predate the field and mean A0.")

    @model_validator(mode='after')
    def validate_gate_versions(self):
        found = re.fullmatch(r'v(\d+)', self.version)
        number = int(found[1]) if found else 0
        if number >= 2:
            if self.paper_to_live_criteria is not None or self.operational_gate is None or self.edge_confidence_gate is None:
                raise ValueError(f'{self.version} requires the two new gates and forbids paper_to_live_criteria.')
        elif self.paper_to_live_criteria is None:
            raise ValueError('Legacy versions require paper_to_live_criteria.')
        if number >= 3 and 'automation_level' not in self.model_fields_set:
            raise ValueError(f'{self.version} must state automation_level explicitly.')
        return self


class LoadedRulebook(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    rulebook: DeskRulebook
    version_file: str
    sha256: str


def load_active_rulebook() -> LoadedRulebook:
    """Refuses to return anything (raises VersionedConfigError) if: the ACTIVE pointer or the
    version file it names is untracked or has uncommitted changes, or the file fails schema
    validation. Never returns a partially-valid rulebook."""
    active_path = resolve_active_version(ACTIVE_POINTER_PATH, RULEBOOK_DIR)
    require_git_clean_and_tracked(active_path)

    raw = yaml.safe_load(active_path.read_text(encoding="utf-8"))
    try:
        rulebook = DeskRulebook.model_validate(raw)
    except ValidationError as exc:
        raise VersionedConfigError(f"{active_path} failed schema validation:\n{exc}") from exc

    return LoadedRulebook(rulebook=rulebook, version_file=active_path.name, sha256=sha256_lf_normalized(active_path))
