"""Defensive guard, added as a preventive measure -- NOT a bug fix (verified directly: no signal
or script module currently references `prev_close`; `scripts/compute_close_to_close.py`'s
close_to_close_60d is computed via `_return()`, event_catalogue.py's corporate-action-adjusted,
bitemporally-correct return function, and touches `prev_close` nowhere).

The reasoning for adding this test anyway: `prev_close` is NSE's own raw, UNADJUSTED previous
close (provenance only -- see the module note above BHAVCOPY in src/bitemporal/schema.py). A
docstring next to a hazardous field is not a guard; it only prevents a mistake if a future reader
actually reads it before writing code. Enforced here by grep instead, the same pattern
test_no_update_on_fact_tables.py already uses for Section 8 -- a real, checkable regression test
rather than a comment someone has to remember.

Legitimate references are narrowly allowlisted: the schema's own declaration
(src/bitemporal/schema.py) and the ingestion module that stores it as raw provenance
(src/ingestion/nse_market_data/bhavcopy.py). Every other module under src/ or scripts/ that needs
a previous-close value must derive it from the as-of, corporate-action-adjusted price series
(Section 11) -- never from this column. If this test ever needs a new allowlist entry to pass,
that new reference is very likely the bug, not the test.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
SCRIPTS_ROOT = ROOT / "scripts"

ALLOWLISTED_FILES = {
    SRC_ROOT / "bitemporal" / "schema.py",
    SRC_ROOT / "ingestion" / "nse_market_data" / "bhavcopy.py",
}

PREV_CLOSE_PATTERN = re.compile(r"\bprev_close\b")

class NoRawPrevCloseOutsideAllowlistTest(unittest.TestCase):
    def test_no_signal_or_script_module_references_prev_close(self):
        violations = []
        for root in (SRC_ROOT, SCRIPTS_ROOT):
            for path in root.rglob("*.py"):
                if path in ALLOWLISTED_FILES:
                    continue
                text = path.read_text(encoding="utf-8")
                if PREV_CLOSE_PATTERN.search(text):
                    violations.append(str(path.relative_to(ROOT)))
        self.assertEqual(violations, [],
            f"Found reference(s) to the raw, unadjusted prev_close field outside its allowlisted "
            f"declaration/ingestion sites: {violations}. A previous-close value for any signal or "
            f"return calculation must come from the as-of, corporate-action-adjusted price series "
            f"(Section 11), never from this column.")

    def test_allowlist_entries_still_exist_and_still_reference_the_field(self):
        """If either allowlisted file stops mentioning prev_close (e.g. the column were removed),
        this test should be revisited rather than silently keep passing on a stale allowlist."""
        for path in ALLOWLISTED_FILES:
            self.assertTrue(path.exists(), f"Allowlisted file no longer exists: {path}")
            self.assertRegex(path.read_text(encoding="utf-8"), PREV_CLOSE_PATTERN)

if __name__ == "__main__":
    unittest.main()
