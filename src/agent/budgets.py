"""Bounds for a Phase 7c event report -- ported from InsightForge's BudgetTracker/MultiAgentConfig
(src/agent/multi_agent/budgets.py), scaled down to what Praman's fixed, single-question-type
roster actually needs. Praman has no coordination rounds, delegation chains, or incremental
follow-up tasks (InsightForge's roster is open-ended and question-driven; Praman's is a fixed
five-agent pipeline run once per event) -- only the two bounds that still apply carry over:
per-agent and total tool-call budgets, so a bug in a specialist agent cannot call a tool in an
unbounded loop.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field

@dataclass(frozen=True)
class BudgetConfig:
    max_total_tool_calls: int = int(os.getenv("PRAMAN_AGENT_MAX_TOTAL_TOOL_CALLS", "12"))
    max_agent_tool_calls: int = int(os.getenv("PRAMAN_AGENT_MAX_AGENT_TOOL_CALLS", "6"))

    def __post_init__(self) -> None:
        if min(self.max_total_tool_calls, self.max_agent_tool_calls) < 1:
            raise ValueError("Agent tool-call budgets must be positive.")

def get_budget_config() -> BudgetConfig:
    return BudgetConfig()

class BudgetTracker:
    """Mutable per-report counters, checked before every tool call via
    src/mcp/tools.py:authorize_tool_call()."""

    def __init__(self, config: BudgetConfig | None = None):
        self.config = config or get_budget_config()
        self.total_tool_calls = 0
        self.per_agent_tool_calls: dict[str, int] = {}

    def can_call_tool(self, role: str) -> bool:
        return (self.total_tool_calls < self.config.max_total_tool_calls
                and self.per_agent_tool_calls.get(role, 0) < self.config.max_agent_tool_calls)

    def register_tool_call(self, role: str) -> None:
        self.total_tool_calls += 1
        self.per_agent_tool_calls[role] = self.per_agent_tool_calls.get(role, 0) + 1
