"""The Desk's cost model: every rate the risk officer needs to compute planned loss including
costs, typed, sourced, and dated -- never hardcoded in code. Same versioning/hashing discipline as
the rulebook (desk/lib/versioned_config.py) for the same reason: every decision records this
config's hash too, since planned loss (and therefore sizing) depends on it.

Every rate is TO_VERIFY until the user confirms it against their broker's actual charge list --
`status` is part of the schema, not a comment, so "has this been confirmed" is a queryable fact,
not something a reader has to notice in prose.
"""
from __future__ import annotations
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

from .versioned_config import (
    VersionedConfigError, resolve_active_version, require_git_clean_and_tracked, sha256_lf_normalized,
)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
ACTIVE_POINTER_PATH = CONFIG_DIR / "COSTS_ACTIVE"


class RateWithProvenance(BaseModel):
    rate: float = Field(..., ge=0)
    unit: str = Field(..., description='e.g. "pct_of_turnover", "pct_of_value", "flat_inr_per_order"')
    source: str
    as_of_date: str
    status: Literal["TO_VERIFY", "CONFIRMED"]


class SlippageBucket(BaseModel):
    liquidity_bucket: str
    slippage_pct: float = Field(..., ge=0)
    source: str
    as_of_date: str
    status: Literal["TO_VERIFY", "CONFIRMED"]


class CostConfig(BaseModel):
    version: str
    dated: str
    securities_transaction_tax: RateWithProvenance
    stamp_duty: RateWithProvenance
    exchange_transaction_charges: RateWithProvenance
    sebi_turnover_fee: RateWithProvenance
    gst: RateWithProvenance
    depository_charges: RateWithProvenance
    brokerage: RateWithProvenance
    slippage_by_liquidity_bucket: list[SlippageBucket] = Field(..., min_length=1)


class LoadedCostConfig(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    costs: CostConfig
    version_file: str
    sha256: str


def load_active_cost_config() -> LoadedCostConfig:
    active_path = resolve_active_version(ACTIVE_POINTER_PATH, CONFIG_DIR)
    require_git_clean_and_tracked(active_path)

    raw = yaml.safe_load(active_path.read_text(encoding="utf-8"))
    try:
        costs = CostConfig.model_validate(raw)
    except ValidationError as exc:
        raise VersionedConfigError(f"{active_path} failed schema validation:\n{exc}") from exc

    return LoadedCostConfig(costs=costs, version_file=active_path.name, sha256=sha256_lf_normalized(active_path))
