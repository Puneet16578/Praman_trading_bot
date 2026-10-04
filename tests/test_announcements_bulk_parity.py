"""Offline replay of the approved live, single-week parity probe."""
import copy
import json
from pathlib import Path
import unittest
from scripts.probe_announcements_bulk import compare


class BulkParityTest(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((Path(__file__).parent/'fixtures/announcements_bulk_week.json').read_text(encoding='utf-8'))

    def test_live_week_matches_each_sampled_symbol_on_all_persisted_fields(self):
        results = compare(self.payload['bulk'], self.payload['per_symbol'])
        self.assertEqual(set(results), {'RELIANCE', 'TCS', 'KOTAKBANK'})
        for symbol, result in results.items():
            self.assertGreater(result['per_symbol'], 0, symbol)
            self.assertTrue(result['equal'], (symbol, result))

    def test_missing_row_and_changed_description_are_detected(self):
        for mutation in ('missing', 'changed'):
            bulk = copy.deepcopy(self.payload['bulk'])
            symbol = bulk[0]['symbol']
            if mutation == 'missing':
                bulk.pop(0)
            else:
                bulk[0]['attchmntText'] = 'Deliberately altered parity fixture'
            self.assertFalse(compare(bulk, self.payload['per_symbol'])[symbol]['equal'])
