"""The copyable thesis loads and satisfies the assessment/journal input contract."""
import sqlite3
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.gates.checks import PASS, g8_thesis_completeness, is_expired
from desk.journal.store import get_thesis, record_thesis
from desk.lib.schema import init_desk_db


class ThesisTemplateTest(unittest.TestCase):
    def test_template_parses_and_can_be_recorded(self):
        path = Path(__file__).resolve().parents[1] / "theses" / "_template.yaml"
        # Exact loader used by desk.cli.cmd_assess (there is no thesis model).
        thesis = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(g8_thesis_completeness(thesis).result, PASS)
        self.assertIsInstance(thesis["evidence_cutoff"], str)
        self.assertIsInstance(thesis["horizon"], str)
        self.assertFalse(is_expired(thesis, thesis["evidence_cutoff"], False))
        self.assertLess(thesis["planned_stop"], thesis["planned_entry"])
        self.assertLess(thesis["planned_entry"], thesis["planned_target"])
        for hypothesis in thesis["hypotheses"]:
            for field in ("statement", "test", "monitor"):
                self.assertTrue(hypothesis[field])
        with sqlite3.connect(":memory:") as conn:
            conn.row_factory = sqlite3.Row
            init_desk_db(conn)
            # Catches missing journal-required fields that G8 does not check.
            thesis_id = record_thesis(conn, symbol="AXISBANK", **thesis)
            saved = get_thesis(conn, thesis_id)
            for field, value in thesis.items():
                self.assertEqual(saved[field], value, field)


if __name__ == "__main__":
    unittest.main()
