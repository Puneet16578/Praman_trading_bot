"""The outcome boundary has one owner; callers must invoke it."""
from pathlib import Path
import re
import unittest


class SingleFirewallTest(unittest.TestCase):
    def test_no_second_desk_boundary(self):
        root = Path(__file__).resolve().parents[1]
        paths = list((root / 'desk').rglob('*.py')) + list((root / 'scripts').glob('desk_*.py'))
        violations = []
        for path in paths:
            if path.name == 'outcome_firewall.py':
                continue
            if re.search(r'2026-09-16|2026\s*,\s*9\s*,\s*16', path.read_text(encoding='utf-8')):
                violations.append(str(path.relative_to(root)))
        self.assertEqual(violations, [])
        self.assertFalse((root / 'desk/outcomes.py').exists())
