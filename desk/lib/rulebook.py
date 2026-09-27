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

import yaml
from pydantic import BaseModel, Field, ValidationError

from .versioned_config import (
    VersionedConfigError, resolve_active_version, require_git_clean_and_tracked, sha256_lf_normalized,
)

RULEBOOK_DIR = Path(__file__).resolve().parents[2] / "rulebook"
ACTIVE_POINTER_PATH = RULEBOOK_DIR / "ACTIVE"


class RiskLimits(BaseModel):
    capital_allocated_inr: float = Field(..., gt=0)
    risk_per_trade_pct: float = Field(..., gt=0, le=100)
    max_open_risk_pct: float = Field(..., gt=0, le=100, description="On STRESS loss, not planned loss")
    max_per_stock_pct: float = Field(..., gt=0, le=100)
    max_per_sector_pct: float = Field(..., gt=0, le=100)
    monthly_drawdown_brake_pct: float = Field(..., gt=0, le=100)


class LiquidityLimits(BaseModel):
    max_order_pct_of_adv: float = Field(..., gt=0, le=100, description="Order value as a share of average daily turnover")
    stressed_volume_factor: float = Field(..., gt=0, le=1, description="Assumed fraction of ADV actually available under stress")
    max_days_to_exit_stressed: float = Field(..., gt=0)


class SurveillanceExclusions(BaseModel):
    exclude_trade_for_trade_series: bool
    max_asm_stage: str | None = Field(None, description="Highest tolerated ASM stage; null means any ASM stage vetoes")
    exclude_gsm: bool


class BehaviouralBrakes(BaseModel):
    max_g7_overrides_per_month: int = Field(..., ge=0)
    consecutive_loss_brake_count: int = Field(..., ge=1)
    stress_loss_lookback_sessions: int = Field(..., ge=1, description="Trailing window for the worst overnight gap used in stress loss")


class InferenceRuleThresholds(BaseModel):
    thresholds: dict[str, float] = Field(default_factory=dict)


class RequiredEvidenceDimensions(BaseModel):
    required: list[str] = Field(..., min_length=1)


class PaperToLiveCriteria(BaseModel):
    min_paper_trades: int = Field(..., ge=1)
    min_paper_trade_days: int = Field(..., ge=1)
    max_rule_violations: int = Field(..., ge=0)


class DeskRulebook(BaseModel):
    version: str
    dated: str
    risk: RiskLimits
    liquidity: LiquidityLimits
    surveillance_exclusions: SurveillanceExclusions
    behavioural_brakes: BehaviouralBrakes
    inference_rules: InferenceRuleThresholds
    required_evidence_dimensions: RequiredEvidenceDimensions
    paper_to_live_criteria: PaperToLiveCriteria


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
