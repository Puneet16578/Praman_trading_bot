"""Deterministic report renderer -- the Synthesis agent. Every structural section (evidence
lists, classification, gaps, provenance note) is built directly from data; there is no
narrative-text hook a provider could use to suppress or override any of it (CLAUDE.md invariant 12
+ the explicit acceptance criterion: "deterministic operation must be complete with NO LLM
configured, byte-identical structure with/without a provider"). This module never calls a
provider at all -- there is nothing an optional narrative summary could add that isn't already
invariant-12-bounded structured fact, so none is wired in; the orchestrator's determinism test
(`OrchestratorDeterminismTest.test_two_runs_of_the_same_event_are_byte_identical`,
tests/test_orchestrator.py -- corrected citation, was previously misnamed in this docstring as a
separate test_orchestrator_determinism.py file that does not exist) runs this same path twice and
diffs the result to hold that guarantee, not merely assert it. Confirmed directly (P8-003,
docs/DEFECT_REGISTER.md): zero LLM-provider-calling code exists anywhere under src/ as of this
note -- this is not merely a design intention, it is the verified, current state of the whole
pipeline. See CLAUDE.md's "LLM narrative scope" note for the standing policy this establishes for
any future work that adds one.
"""
from __future__ import annotations

from ..classification.event_classifier import (
    BASELINE_COMPARISON_NOTE, ClassificationThresholds, DISCRIMINATIVE_POWER_NOTE, GROUNDED,
    GROUNDED_LIMITATION_NOTE, INDISTINGUISHABLE_PAIR, INDISTINGUISHABLE_PAIR_NOTE,
    PROVENANCE_NOTE, classify_event, momentum_is_high,
)
from .models import EventReport, EvidenceClaim

def _find(claims: list[EvidenceClaim], claim_id_suffix: str) -> EvidenceClaim | None:
    for c in claims:
        if c.claim_id.endswith(claim_id_suffix):
            return c
    return None

class SynthesisAgent:
    ROLE = "SYNTHESIS"

    def render(
        self, *, symbol: str, event_date: str,
        microstructure_claims: list[EvidenceClaim], disclosure_claims: list[EvidenceClaim],
        surveillance_claims: list[EvidenceClaim], rejected: list[EvidenceClaim],
        catalogue_reference: dict | None, thresholds: ClassificationThresholds,
        agents_used: list[str], tool_calls_used: int, agent_errors: list[str] | None = None,
    ) -> EventReport:
        gaps: list[str] = list(agent_errors or [])
        disclosure_agent_failed = any("DISCLOSURE agent could not complete" in e for e in gaps)

        return_20d_claim = _find(microstructure_claims, ":return_20d")
        abs_return_20d = abs(return_20d_claim.cited_value) if return_20d_claim else None
        if return_20d_claim is None:
            gaps.append("20-session return could not be determined (insufficient trailing history or a structural break in the window).")

        cap_band = catalogue_reference["cap_band"] if catalogue_reference else None
        same_date_event_count = catalogue_reference["same_date_event_count"] if catalogue_reference else None
        if catalogue_reference is None:
            gaps.append("This event is not in this project's catalogue -- cap-band and co-movement context are unavailable.")

        momentum_high = momentum_is_high(abs_return_20d, cap_band, thresholds) if cap_band else None

        no_coverage_claim = _find(disclosure_claims, ":no_coverage")
        tier_claim = _find(disclosure_claims, ":disclosure_tier")
        if disclosure_agent_failed:
            # The Disclosure agent itself errored (e.g. a tool call was denied or raised) -- this
            # must NEVER be read as "checked, found nothing" or "has coverage." Conservative
            # default: treat exactly like unknown coverage, the same safe fallback used when the
            # symbol genuinely has no cached announcement data.
            has_coverage = False
            disclosure_tier = "UNKNOWN_COVERAGE"
        else:
            has_coverage = no_coverage_claim is None
            if not has_coverage:
                gaps.append("No cached announcement data exists for this symbol -- disclosure coverage could not be checked.")
            disclosure_tier = tier_claim.cited_value if tier_claim else ("UNKNOWN_COVERAGE" if not has_coverage else "NONE")

        classification, _is_isolated = classify_event(
            disclosure_tier=disclosure_tier, has_coverage=has_coverage, momentum_high=momentum_high,
            same_date_event_count=same_date_event_count, thresholds=thresholds,
        )
        classification_notes: list[str] = []
        if classification in INDISTINGUISHABLE_PAIR:
            classification_notes.append(INDISTINGUISHABLE_PAIR_NOTE)
        if classification == GROUNDED:
            classification_notes.append(GROUNDED_LIMITATION_NOTE)

        def section(claims: list[EvidenceClaim]) -> dict:
            return {c.claim_id.rsplit(":", 1)[-1]: {"text": c.text, "value": c.cited_value} for c in claims}

        accepted_all = microstructure_claims + disclosure_claims + surveillance_claims
        accepted_dicts = [
            {"claim_id": c.claim_id, "agent_role": c.agent_role, "text": c.text,
             "cited_value": c.cited_value, "source": c.source, "verification": dict(c.verification)}
            for c in accepted_all
        ]
        rejected_dicts = [{"claim_id": c.claim_id, "agent_role": c.agent_role, "text": c.text} for c in rejected]
        if rejected:
            gaps.append(f"{len(rejected)} claim(s) failed independent verification and were excluded from this report -- see rejected_claims.")

        return EventReport(
            symbol=symbol, event_date=event_date, classification=classification,
            classification_notes=classification_notes, discriminative_power_note=DISCRIMINATIVE_POWER_NOTE,
            baseline_comparison_note=BASELINE_COMPARISON_NOTE,
            disclosure_tier=disclosure_tier,
            microstructure=section(microstructure_claims), disclosure=section(disclosure_claims),
            surveillance=section(surveillance_claims),
            accepted_claims=accepted_dicts, rejected_claims=rejected_dicts,
            gaps=gaps, provenance_note=PROVENANCE_NOTE,
            agents_used=agents_used, tool_calls_used=tool_calls_used,
        )
