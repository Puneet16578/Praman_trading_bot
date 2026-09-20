"""Typed contracts for the Phase 7c agent layer -- ported (adapted, not imported) from
InsightForge's AgentTask/AgentTaskResult/EvidenceConflict pattern
(src/agent/multi_agent/models.py in the InsightForge tree). Praman's roster and question shape are
narrower than InsightForge's (one question type -- "classify and evidence this event" -- run once
per event, not an open-ended investigation), so this module keeps only what that shape needs:
no DelegationRequest/coordination-round machinery, no checkpoint/resume state.

EvidenceClaim is the one piece with no InsightForge equivalent: it carries a `verify` closure so
the Adversary agent (adversary.py) can mechanically re-derive `cited_value` from the store and
compare, rather than trusting the specialist's own arithmetic. A claim that fails verification is
dropped before it ever reaches Synthesis -- CLAUDE.md's verification-honesty requirement enforced
structurally, not by convention.

Two independent verification tiers, not one (src/agent/derivation_check.py has the full rationale):
`verify` re-runs the SAME derivation function the claim's value came from (TRANSCRIPTION -- proves
the claim wasn't mistyped) and `derivation_verify` recomputes it via a SEPARATE, independently
written code path against raw bhavcopy rows (DERIVATION -- proves the shared formula itself is
correct, for a seeded ~20% sample of eligible claims). A claim's `verification` dict records what
each tier actually found, for the report to state per claim rather than assert blanket coverage.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class EvidenceClaim:
    claim_id: str
    agent_role: str
    text: str                                  # human-readable claim -- banned-term-linted before output
    cited_value: Any                           # the specific fact/number this claim asserts
    source: str                                # human description of provenance (table/computation)
    verify: Callable[[], Any] | None = None    # TRANSCRIPTION: zero-arg, re-run the same derivation fn; None = nothing to check
    derivation_verify: Callable[[], Any] | None = None  # DERIVATION: zero-arg, independent second implementation; None = not yet implemented for this claim type
    window_description: str | None = None      # e.g. "10 sessions" -- checked against the canonical constant
    canonical_window: str | None = None        # what the window SHOULD be, for the Adversary's cherry-pick check
    verification: dict[str, str] = field(default_factory=dict)  # populated by the Adversary: {"transcription": "PASS"/"FAIL"/"NOT_APPLICABLE", "derivation": "PASS"/"FAIL"/"NOT_SAMPLED"/"NOT_APPLICABLE"}

@dataclass
class AdversaryFinding:
    claim_id: str
    check: str        # "conclusion_language" / "window" / "transcription" / "derivation"
    verdict: str       # "PASS" / "FAIL" (transcription/window/conclusion_language) or additionally "NOT_APPLICABLE" / "NOT_SAMPLED" (derivation)
    detail: str

@dataclass
class AgentTaskResult:
    role: str
    status: str                                    # "OK" / "ERROR"
    claims: list[EvidenceClaim] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

@dataclass
class EventReport:
    """The final, fully-deterministic output of one orchestrator run. Every field here is plain
    data (no callables) -- this is what gets serialized/rendered, after Adversary verification has
    already dropped anything that failed. `to_dict()` must be stable/order-independent for the
    determinism test (tests/test_orchestrator_determinism.py) to compare two runs byte-for-byte."""
    symbol: str
    event_date: str
    classification: str
    classification_notes: list[str]    # rendered at the point of classification, never a footnote -- see event_classifier.INDISTINGUISHABLE_PAIR_NOTE / GROUNDED_LIMITATION_NOTE. A list because more than one can apply to the same class (e.g. GROUNDED gets both).
    discriminative_power_note: str     # the Phase 6 0.611-0.70 held-out ceiling, unconditionally attached next to every classification, not only in the general provenance disclaimer
    baseline_comparison_note: str      # Phase 8 placeholder -- no baseline exists yet; named explicitly so its absence isn't mistaken for a favorable comparison
    disclosure_tier: str
    microstructure: dict[str, Any]
    disclosure: dict[str, Any]
    surveillance: dict[str, Any]
    accepted_claims: list[dict[str, Any]]
    rejected_claims: list[dict[str, Any]]       # what the Adversary caught -- never silently dropped from the record
    gaps: list[str]                              # "what could not be determined"
    provenance_note: str
    agents_used: list[str]
    tool_calls_used: int
    adversary_findings: list[dict[str, Any]] = field(default_factory=list)  # full pass/fail audit trail, every check on every claim

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol, "event_date": self.event_date,
            "classification": self.classification, "classification_notes": self.classification_notes,
            "discriminative_power_note": self.discriminative_power_note,
            "baseline_comparison_note": self.baseline_comparison_note,
            "disclosure_tier": self.disclosure_tier,
            "microstructure": self.microstructure, "disclosure": self.disclosure,
            "surveillance": self.surveillance,
            "accepted_claims": self.accepted_claims, "rejected_claims": self.rejected_claims,
            "gaps": self.gaps, "provenance_note": self.provenance_note,
            "agents_used": self.agents_used, "tool_calls_used": self.tool_calls_used,
            "adversary_findings": self.adversary_findings,
        }
