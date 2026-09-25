"""Constraint 3/4: the demo's RUNTIME code (demo/Home.py, demo/pages/*, demo/lib/*) must never
reference the production store -- neither its path nor the machinery (get_settings/get_connection)
that resolves to it by default. The one deliberate exception is demo/build_demo_store.py, whose
entire job is to read production ONCE (read-only) to build the demo's own copy -- documented in its
own module docstring, not silently exempted here.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_RUNTIME_FILES = (
    [PROJECT_ROOT / "demo" / "Home.py", PROJECT_ROOT / "demo" / "ui.py"]
    + sorted((PROJECT_ROOT / "demo" / "pages").glob("*.py"))
    + sorted((PROJECT_ROOT / "demo" / "lib").glob("*.py"))
)

FORBIDDEN_PATTERNS = [
    re.compile(r"data[/\\]processed"),
    re.compile(r"praman\.db\b"),
    re.compile(r"\bget_settings\s*\("),
    re.compile(r"from\s+src\.bitemporal\.connection\s+import"),
    re.compile(r"\bget_connection\s*\("),
]

_TRIPLE_QUOTED_RE = re.compile(r'""".*?"""', re.DOTALL)
_COMMENT_RE = re.compile(r"#.*$", re.MULTILINE)


def _strip_prose(text: str) -> str:
    """Removes docstrings and comments before scanning for forbidden patterns -- this test checks
    what the demo's code DOES, not whether its own documentation is permitted to name the
    production path it explains staying away from (several docstrings in demo/lib/ do exactly
    that, by design)."""
    return _COMMENT_RE.sub("", _TRIPLE_QUOTED_RE.sub("", text))


class NoProductionPathReferenceTest(unittest.TestCase):
    def test_demo_runtime_files_never_reference_production_store(self):
        self.assertGreater(len(DEMO_RUNTIME_FILES), 5, "Expected to find demo runtime files -- check the glob paths.")
        offenders = []
        for path in DEMO_RUNTIME_FILES:
            code_only = _strip_prose(path.read_text(encoding="utf-8"))
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(code_only):
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)}: matched {pattern.pattern!r}")
        self.assertEqual(offenders, [], "Demo runtime code references the production store:\n" + "\n".join(offenders))

    def test_build_demo_store_is_the_one_documented_exception(self):
        build_script = PROJECT_ROOT / "demo" / "build_demo_store.py"
        self.assertTrue(build_script.exists())
        text = build_script.read_text(encoding="utf-8")
        self.assertIn("get_settings", text)
        self.assertIn("mode=ro", text, "build_demo_store.py must open production read-only.")


if __name__ == "__main__":
    unittest.main()
