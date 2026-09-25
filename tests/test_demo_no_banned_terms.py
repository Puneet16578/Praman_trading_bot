"""Constraint 6 (no verdicts): runs the existing banned-term lint (src/agent/banned_terms.py, not
a demo-specific reimplementation) over every static string this demo renders, plus every claim's
text from a couple of real generated reports. This demo authors no new narrative text of its own
(page code is UI labels/captions only) -- this test exists to catch the case where it accidentally
did, or where a source constant it reuses somehow changed underneath it.
"""
from __future__ import annotations
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.banned_terms import lint_text
from src.classification.event_classifier import (
    BASELINE_COMPARISON_NOTE, DISCRIMINATIVE_POWER_NOTE, GROUNDED_LIMITATION_NOTE,
    INDISTINGUISHABLE_PAIR_NOTE, PROVENANCE_NOTE,
)

_ST_STRING_RE = re.compile(r'st\.(?:write|caption|markdown|info|warning|error|success|title|subheader)\(\s*(f?)("""(?:.*?)"""|"(?:[^"\\]|\\.)*"|f?\'(?:[^\'\\]|\\.)*\')', re.DOTALL)


class StaticNotesCleanTest(unittest.TestCase):
    def test_classifier_notes_are_lint_clean(self):
        for name, text in (
            ("PROVENANCE_NOTE", PROVENANCE_NOTE),
            ("DISCRIMINATIVE_POWER_NOTE", DISCRIMINATIVE_POWER_NOTE),
            ("BASELINE_COMPARISON_NOTE", BASELINE_COMPARISON_NOTE),
            ("GROUNDED_LIMITATION_NOTE", GROUNDED_LIMITATION_NOTE),
            ("INDISTINGUISHABLE_PAIR_NOTE", INDISTINGUISHABLE_PAIR_NOTE),
        ):
            violations = lint_text(text)
            self.assertEqual(violations, [], f"{name} failed the banned-term lint: {violations}")


class DemoStaticStringsCleanTest(unittest.TestCase):
    """Scans every literal string passed to a Streamlit display call in demo/pages/*.py and
    demo/Home.py -- these are the only strings this demo's own code authors."""

    def test_every_static_display_string_is_lint_clean(self):
        offenders = []
        files = [PROJECT_ROOT / "demo" / "Home.py"] + sorted((PROJECT_ROOT / "demo" / "pages").glob("*.py"))
        for path in files:
            text = path.read_text(encoding="utf-8")
            for m in _ST_STRING_RE.finditer(text):
                literal = m.group(2).strip('"\'')
                violations = lint_text(literal)
                if violations:
                    offenders.append((str(path.relative_to(PROJECT_ROOT)), literal[:80], violations))
        self.assertEqual(offenders, [], f"Static UI strings failed the banned-term lint: {offenders}")


class RealReportClaimsCleanTest(unittest.TestCase):
    """Real generated reports' claim text -- guarded, needs the demo store."""

    def test_two_real_reports_claims_are_lint_clean(self):
        from demo.lib import store

        if not store.DEMO_DB_PATH.exists():
            self.skipTest(f"Demo store not found at {store.DEMO_DB_PATH}. Run demo/build_demo_store.py.")

        from src.agent.orchestrator import MultiAgentOrchestrator

        store.patch_reference_data_paths()
        conn = store.get_demo_connection()
        try:
            orch = MultiAgentOrchestrator()
            for symbol, event_date in (("AXISBANK", "2021-10-27"), ("GSPL", "2020-03-24")):
                report = orch.run_for_event(conn, symbol, event_date)
                for claim in report.accepted_claims:
                    violations = lint_text(claim["text"])
                    self.assertEqual(violations, [], f"{symbol}/{event_date} claim {claim['claim_id']} failed lint: {violations}")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
