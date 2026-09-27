"""Epistemic wrapper around Praman's existing EvidenceClaim/AdversaryAgent -- the Desk composes
with them, it does not build a second verifier. Four types, each enforced by its own constructor so
a malformed one cannot be built at all, not merely flagged after the fact:

- Fact: a claim about what IS -- must reference a real source record and, if it carries a `verify`
  closure, must already have been run through the real AdversaryAgent (its `verification` dict is
  populated). A Fact never asserts something the Adversary hasn't had a chance to check.
- Inference: a claim DERIVED from facts by a named rule -- must cite at least one Fact id and a
  rule_id. The rule_id's THRESHOLDS live in the rulebook (never hardcoded in code); this class only
  enforces that some rule_id was named, not that it resolves in a live registry -- Phase 1 defines
  no inference rules yet (later phases add them), so nothing in Phase 1 actually constructs an
  Inference; the constructor is exercised only by its own tests until then.
- Hypothesis: a claim about what MIGHT explain something -- must name an observable test, per the
  Desk's own purpose (CONSTITUTION item 3 in docs/desk/DESIGN.md: gates, not scores; a hypothesis
  with no way to check it is not evidence of anything).
- Unknown: an explicit gap, tagged with WHY it's unknown (epistemic/measurement/execution/model/
  aleatoric) -- gap detection produces these, never a silent None.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.agent.models import EvidenceClaim

UNCERTAINTY_CATEGORIES = frozenset({"epistemic", "measurement", "execution", "model", "aleatoric"})


class EpistemicTypeError(ValueError):
    """Raised by any of the four constructors below when a required field is missing or invalid --
    a distinct exception type so callers can catch "this evidence object is malformed" specifically,
    not any ValueError."""


@dataclass(frozen=True)
class Fact:
    claim: EvidenceClaim

    def __post_init__(self) -> None:
        if not self.claim.source:
            raise EpistemicTypeError(
                f"Fact for claim {self.claim.claim_id!r} has no source record -- a Fact must "
                "reference where it came from (table, business key, knowledge_date/recorded_at)."
            )
        if self.claim.verify is not None and not self.claim.verification:
            raise EpistemicTypeError(
                f"Fact for claim {self.claim.claim_id!r} carries a verify closure but has not been "
                "run through AdversaryAgent().verify() -- a Fact cannot assert something the "
                "Adversary hasn't had the chance to check."
            )


@dataclass(frozen=True)
class Inference:
    statement: str
    fact_ids: tuple[str, ...]
    rule_id: str

    def __post_init__(self) -> None:
        if not self.fact_ids:
            raise EpistemicTypeError(f"Inference {self.statement!r} cites no Fact id.")
        if not self.rule_id:
            raise EpistemicTypeError(f"Inference {self.statement!r} cites no rule_id.")


@dataclass(frozen=True)
class Hypothesis:
    statement: str
    observable_test: str

    def __post_init__(self) -> None:
        if not self.observable_test:
            raise EpistemicTypeError(f"Hypothesis {self.statement!r} names no observable test.")


@dataclass(frozen=True)
class Unknown:
    dimension: str
    uncertainty_category: str
    detail: str

    def __post_init__(self) -> None:
        if self.uncertainty_category not in UNCERTAINTY_CATEGORIES:
            raise EpistemicTypeError(
                f"Unknown for dimension {self.dimension!r} has uncertainty_category "
                f"{self.uncertainty_category!r}, not one of {sorted(UNCERTAINTY_CATEGORIES)}."
            )
