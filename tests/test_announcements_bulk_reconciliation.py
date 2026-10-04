"""Offline captured evidence: renames must not hide changed or missing content."""
import copy
import json
from pathlib import Path
import unittest

from scripts.probe_announcements_bulk import compare
from scripts.reconcile_announcements_bulk import rename_match


class BulkReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parent / 'fixtures' /
            'announcements_bulk_reconciliation.json').read_text(encoding='utf-8'))

    def test_all_five_stored_announcements_have_one_exact_rename_counterpart(self):
        self.assertEqual(len(self.data['stored_renames']), 5)
        for stored in self.data['stored_renames']:
            matches = [raw for raw in self.data['bulk_renames']
                       if rename_match(stored, raw, self.data['old_symbol_isins'])]
            self.assertEqual(len(matches), 1, stored['seq_id'])
            self.assertEqual(matches[0]['symbol'],
                             {'HEG': 'HEGAM', 'SANGINITA': 'AGASTYAEN'}[stored['symbol']])

    def test_same_id_does_not_excuse_changed_content_date_or_identity(self):
        stored = self.data['stored_renames'][0]
        raw = next(r for r in self.data['bulk_renames'] if r['seq_id'] == stored['seq_id'])
        for field, replacement in [('attchmntText', 'Revised content'), ('desc', 'Different category'),
                                   ('sort_date', '2026-09-06 23:59:59'), ('seq_id', 'different'),
                                   ('sm_isin', 'different'), ('symbol', stored['symbol'])]:
            with self.subTest(field=field):
                mutated = copy.deepcopy(raw)
                mutated[field] = replacement
                self.assertFalse(rename_match(stored, mutated, self.data['old_symbol_isins']))
        self.assertFalse(rename_match(stored, raw, {}))

    def test_bulk_only_scope_samples_match_live_per_symbol_captures(self):
        results = compare(self.data['bulk_scope_samples'], self.data['per_symbol'])
        self.assertEqual({s: r['per_symbol'] for s, r in results.items()}, {'HMT': 6, 'MELSTAR': 9})
        self.assertTrue(all(r['equal'] for r in results.values()), results)
