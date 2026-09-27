"""Per-dimension coverage report for an EvidenceBundle -- what G2 (evidence sufficiency) reads."""
from __future__ import annotations
from dataclasses import dataclass

from .bundle import EvidenceBundle
from .types import Fact, Unknown


@dataclass(frozen=True)
class CoverageReport:
    present: tuple[str, ...]
    unknown: tuple[str, ...]

    def is_present(self, dimension: str) -> bool:
        return dimension in self.present


def compute_coverage(bundle: EvidenceBundle) -> CoverageReport:
    present, unknown = [], []
    for dimension, evidence in bundle.dimensions().items():
        (present if isinstance(evidence, Fact) else unknown).append(dimension)
    return CoverageReport(present=tuple(sorted(present)), unknown=tuple(sorted(unknown)))
