"""Acceptance test 8 -- the forward-window firewall (Desk invariant D7): the Desk must never
import an outcome-label-computing module, or reference an outcome-label field name, anywhere.
Confirmed by direct grep before writing this test: every outcome-label computation in this repo
lives in exactly three scripts/ files, nowhere under src/ -- a clean, checkable boundary.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESK_DIR = PROJECT_ROOT / "desk"

FORBIDDEN_IMPORTS = (
    "scripts.compute_outcome_labels",
    "scripts.compute_outcome_labels_relative",
    "scripts.phase8_robustness_relabel_t0",
)
FORBIDDEN_LITERALS = (
    "collapsed_90d", "relative_t0_primary", "forward_return_", "compute_t0_relative", "collapsed_t0",
)


class DeskNeverComputesOutcomeLabelsTest(unittest.TestCase):
    def test_no_forbidden_imports_or_literals_anywhere_under_desk(self):
        offenders = []
        for path in DESK_DIR.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_IMPORTS:
                if forbidden in text:
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)}: imports {forbidden!r}")
            for literal in FORBIDDEN_LITERALS:
                if literal in text:
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)}: contains {literal!r}")
        self.assertEqual(offenders, [], "desk/ references outcome-label computation:\n" + "\n".join(offenders))

    def test_outcome_label_computation_is_confined_to_exactly_these_scripts(self):
        """Sanity check on the premise the test above relies on: if a future defect fix moves
        outcome-label computation into src/, this firewall test's own FORBIDDEN_IMPORTS list would
        silently stop covering it. Re-confirms the boundary is still where it was when this test
        was written."""
        pattern = re.compile(r"collapsed_90d|relative_t0_primary|forward_return_|compute_t0_relative")
        hits = set()
        for path in (PROJECT_ROOT / "src").rglob("*.py"):
            if pattern.search(path.read_text(encoding="utf-8")):
                hits.add(str(path.relative_to(PROJECT_ROOT)))
        self.assertEqual(hits, set(), f"Outcome-label logic has moved into src/: {hits} -- update the firewall test's coverage.")


if __name__ == "__main__":
    unittest.main()
