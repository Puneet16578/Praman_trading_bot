"""Section 8, enforced by grep, not intention: no UPDATE statement against any registered
bitemporal fact table may exist anywhere in src/. A restatement is always a new INSERT with a
later knowledge_date; if this test ever needs an allowlist entry to pass, that is the bug, not
the test.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path

from src.bitemporal.schema import BITEMPORAL_TABLES

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"

class NoUpdateOnFactTablesTest(unittest.TestCase):
    def test_no_update_statement_targets_a_fact_table(self):
        violations = []
        for path in SRC_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for table_name in BITEMPORAL_TABLES:
                if re.search(rf"\bUPDATE\s+[\"']?{re.escape(table_name)}\b", text, re.IGNORECASE):
                    violations.append(f"{path.relative_to(SRC_ROOT.parent)}: UPDATE against '{table_name}'")
        self.assertEqual(violations, [], f"Found UPDATE statement(s) against fact table(s): {violations}")

class IngestionNeverOpensConnectionDirectlyTest(unittest.TestCase):
    """Every write must go through src/bitemporal/store.py. An ingestion module that opens its own
    sqlite3 connection bypasses the store's shape validation entirely (P2-001/P2-002). Importing
    `sqlite3` purely for a `Connection` type annotation is fine and expected; actually calling
    `.connect(` is the bypass this test forbids.
    """
    def test_no_ingestion_module_opens_a_connection(self):
        ingestion_root = SRC_ROOT / "ingestion"
        violations = []
        for path in ingestion_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "sqlite3.connect(" in text or ".connect(\":memory:\")" in text:
                violations.append(str(path.relative_to(SRC_ROOT.parent)))
        self.assertEqual(violations, [], f"src/ingestion/ must never open its own connection -- found in: {violations}")

if __name__ == "__main__":
    unittest.main()
