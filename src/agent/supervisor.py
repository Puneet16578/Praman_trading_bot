"""Deterministic routing -- ported from InsightForge's Supervisor.plan() (a fixed dict keyed by
question_type, src/agent/multi_agent/supervisor.py in the InsightForge tree). Praman has exactly
one question type ("classify and evidence this event"), so the plan collapses to one fixed
dispatch order rather than a dict keyed by question type -- there is nothing to route BETWEEN,
only a fixed sequence to run. Kept as its own module anyway (not inlined into the orchestrator)
so the roster and its order are named and testable on their own, matching the roster
specification's explicit "Supervisor: deterministic routing" entry.
"""
from __future__ import annotations

from .specialists import DisclosureAgent, MarketMicrostructureAgent, SurveillanceAgent

class Supervisor:
    ROLE = "SUPERVISOR"

    def plan(self) -> list:
        """Fixed, deterministic dispatch order -- Market Microstructure, Disclosure, Surveillance.
        No dependency between them (each reads only from the store), so order here reflects
        report presentation order, not a data dependency."""
        return [MarketMicrostructureAgent(), DisclosureAgent(), SurveillanceAgent()]
