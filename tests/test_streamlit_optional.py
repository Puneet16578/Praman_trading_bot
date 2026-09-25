"""Constraint 5 (optional dependency): streamlit is gated out of the core project the way FastAPI
was gated in InsightForge -- it lives only in requirements-demo.txt, never requirements.txt, and
nothing under src/ or scripts/ may import it. demo/lib/* must also be importable without it, since
that is what lets tests/test_demo_cutoff_redaction.py, tests/test_demo_readonly_guard.py, etc. run
as part of THIS SAME suite regardless of whether streamlit happens to be installed.

The real, operational proof (this project's own verification-honesty rule: never claim untested
coverage) is running `pytest tests/` in an environment with streamlit NOT installed and pasting the
result -- done and reported alongside this commit, not merely asserted by this file.
"""
from __future__ import annotations
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

_STREAMLIT_IMPORT_RE = re.compile(r"^\s*(import\s+streamlit|from\s+streamlit\b)", re.MULTILINE)


class StreamlitNotAPipelineDependencyTest(unittest.TestCase):
    def test_src_never_imports_streamlit(self):
        offenders = self._scan(PROJECT_ROOT / "src")
        self.assertEqual(offenders, [], f"streamlit imported under src/: {offenders}")

    def test_scripts_never_imports_streamlit(self):
        offenders = self._scan(PROJECT_ROOT / "scripts")
        self.assertEqual(offenders, [], f"streamlit imported under scripts/: {offenders}")

    def test_demo_lib_never_imports_streamlit(self):
        offenders = self._scan(PROJECT_ROOT / "demo" / "lib")
        self.assertEqual(offenders, [], f"streamlit imported under demo/lib/: {offenders}")

    def test_requirements_txt_does_not_list_streamlit(self):
        text = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("streamlit", text)

    def test_requirements_demo_txt_lists_a_pinned_streamlit(self):
        text = (PROJECT_ROOT / "requirements-demo.txt").read_text(encoding="utf-8")
        self.assertRegex(text, r"streamlit==\d+\.\d+\.\d+")

    def _scan(self, root: Path) -> list[str]:
        offenders = []
        for path in root.rglob("*.py"):
            if _STREAMLIT_IMPORT_RE.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        return offenders


class DemoLibImportableTest(unittest.TestCase):
    """These imports succeed regardless of whether streamlit happens to be installed in THIS
    environment -- the source-level guarantee above is what makes that true unconditionally, not
    this test (which cannot prove an absence by itself if streamlit IS installed here)."""

    def test_cutoff_importable(self):
        import demo.lib.cutoff  # noqa: F401

    def test_store_importable(self):
        import demo.lib.store  # noqa: F401

    def test_anonymize_importable(self):
        import demo.lib.anonymize  # noqa: F401

    def test_catalogue_importable(self):
        import demo.lib.catalogue  # noqa: F401

    def test_findings_importable(self):
        import demo.lib.findings  # noqa: F401


if __name__ == "__main__":
    unittest.main()
