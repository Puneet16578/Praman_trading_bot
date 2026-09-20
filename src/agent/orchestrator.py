"""MultiAgentOrchestrator -- ported (adapted, not imported) from InsightForge's
MultiAgentOrchestrator._run() (src/agent/multi_agent/orchestrator.py in the InsightForge tree):
plan -> dispatch -> synthesize. Praman's version is a single deterministic pass, not
InsightForge's round-based incremental-follow-up loop -- Praman has one question type and a fixed
five-role roster, so there is nothing for an incremental round to discover that the fixed plan
didn't already cover; InsightForge's round/gap-driven machinery exists for open-ended questions
this project doesn't ask.

Sequence: Supervisor.plan() -> dispatch Market Microstructure / Disclosure / Surveillance (each
through the authorization gate, mcp/tools.py) -> Adversary verifies every claim -> Synthesis
renders the final, fully deterministic EventReport. No LLM provider is called anywhere in this
path -- there is no optional narrative step to wire one into (synthesis.py's own docstring), so
"deterministic operation must be complete with NO LLM configured, byte-identical structure with/
without a provider" holds trivially and completely, not merely as a mode this module falls back
to.
"""
from __future__ import annotations

from dataclasses import asdict

from .adversary import AdversaryAgent
from .budgets import BudgetConfig, BudgetTracker
from .models import EventReport
from .reference_data import load_thresholds, lookup_catalogue_reference
from .specialists import DisclosureAgent, MarketMicrostructureAgent, SurveillanceAgent
from .supervisor import Supervisor
from .synthesis import SynthesisAgent

class MultiAgentOrchestrator:
    """One instance may generate any number of reports -- `run_for_event` allocates a FRESH
    BudgetTracker on every call, deliberately not shared across calls. A shared, orchestrator-
    lifetime budget would mean report N's tool-call allowance depends on how many reports were
    generated before it on the same instance -- report 4 silently starved by reports 1-3's usage,
    with no error surfaced, just quietly degraded evidence. Each report's bound is per-report, by
    design, matching how the roster spec describes the budget (bounding ONE investigation's tool
    use, not a whole session's)."""

    def __init__(self, budget_config: BudgetConfig | None = None):
        self.budget_config = budget_config
        self.supervisor = Supervisor()
        self.adversary = AdversaryAgent()
        self.synthesizer = SynthesisAgent()

    def run_for_event(self, conn, symbol: str, event_date: str) -> EventReport:
        budget = BudgetTracker(self.budget_config) if self.budget_config else BudgetTracker()
        agents = self.supervisor.plan()
        results = {}
        agents_used = []
        agent_errors: list[str] = []
        for agent in agents:
            result = agent.run(conn, symbol, event_date, budget)
            results[type(agent)] = result
            agents_used.append(result.role)
            if result.status == "ERROR":
                agent_errors.append(f"{result.role} agent could not complete: {'; '.join(result.errors)}")

        microstructure_result = results[MarketMicrostructureAgent]
        disclosure_result = results[DisclosureAgent]
        surveillance_result = results[SurveillanceAgent]

        all_claims = microstructure_result.claims + disclosure_result.claims + surveillance_result.claims
        accepted, findings = self.adversary.verify(all_claims)
        agents_used.append(self.adversary.ROLE)

        accepted_ids = {c.claim_id for c in accepted}
        rejected = [c for c in all_claims if c.claim_id not in accepted_ids]

        accepted_microstructure = [c for c in microstructure_result.claims if c.claim_id in accepted_ids]
        accepted_disclosure = [c for c in disclosure_result.claims if c.claim_id in accepted_ids]
        accepted_surveillance = [c for c in surveillance_result.claims if c.claim_id in accepted_ids]

        catalogue_reference = lookup_catalogue_reference(symbol, event_date)
        thresholds = load_thresholds()

        report = self.synthesizer.render(
            symbol=symbol, event_date=event_date,
            microstructure_claims=accepted_microstructure, disclosure_claims=accepted_disclosure,
            surveillance_claims=accepted_surveillance, rejected=rejected,
            catalogue_reference=catalogue_reference, thresholds=thresholds,
            agents_used=agents_used + [self.synthesizer.ROLE],
            tool_calls_used=budget.total_tool_calls, agent_errors=agent_errors,
        )
        report.adversary_findings = [asdict(f) for f in findings]
        return report
