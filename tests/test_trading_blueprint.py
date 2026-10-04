"""Blueprint extraction is reproducible and never touches the hand-maintained amendments."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import scripts.extract_trading_blueprint as extract


class TradingBlueprintTest(unittest.TestCase):
    def test_render_is_deterministic_and_complete(self):
        first, second = extract.render(), extract.render()
        self.assertEqual(first, second)
        for n in range(1, 14):
            self.assertRegex(first, rf'(?m)^## {n}\. ')
        self.assertIn('| A1 | Paper trading |', first)
        self.assertIn('| Stale or inconsistent market data | NO NEW TRADES |', first)
        self.assertIn('PRAMAN - DAILY DECISION DESK', first)

    def test_regeneration_preserves_amendments(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'TRADING_BLUEPRINT.md'
            out.write_text('stale body\n' + extract.AMENDMENTS_MARKER + '\n\n## Praman amendments\nkept\n', encoding='utf-8')
            with patch.object(extract, 'OUTPUT', out), patch('builtins.print'):
                extract.main()
            text = out.read_text(encoding='utf-8')
            self.assertNotIn('stale body', text)
            self.assertTrue(text.endswith(extract.AMENDMENTS_MARKER + '\n\n## Praman amendments\nkept\n'))

    def test_committed_document_matches_pdf_and_has_amendments(self):
        committed = extract.OUTPUT.read_text(encoding='utf-8')
        body = committed[:committed.index(extract.AMENDMENTS_MARKER)]
        self.assertIn(extract.render(), body)
        tail = committed[committed.index(extract.AMENDMENTS_MARKER):]
        for text in ('LONG only', '2019-10-01 to 2024-12-31', '2026-09-16', '2027-06-01',
                     'explicit approval', 'SEBI', 'T10 - Limited automation'):
            self.assertIn(text, tail)


if __name__ == '__main__':
    unittest.main()
