"""P8-010 fix: ISIN identity resolution. `fetch_isin_snapshot` is tested against a fake
`bhavcopy_save` callable (real network fetch is not exercised by the fixture-based test suite,
same convention as corporate_actions.py's own real-fetch functions) covering both the legacy and
UDiFF column-name schemas this project's own historical ISIN map was built from.
"""
from __future__ import annotations
import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.ingestion.nse_market_data.isin_mapping import (
    build_symbol_groups, fetch_isin_snapshot, merge_isin_snapshots,
)


def _write_csv(tmpdir: str, fieldnames: list[str], rows: list[dict]) -> str:
    path = Path(tmpdir) / "bhav.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


class FetchIsinSnapshotTest(unittest.TestCase):
    def test_legacy_schema(self):
        def fake_bhavcopy_save(dt, dest, skip_if_present=True):
            return _write_csv(dest, ["SYMBOL", "SERIES", "ISIN"], [
                {"SYMBOL": "HEG", "SERIES": "EQ", "ISIN": "INE545A01024"},
                {"SYMBOL": "RELIANCE", "SERIES": "EQ", "ISIN": "INE002A01018"},
                {"SYMBOL": "SOMEBOND", "SERIES": "N1", "ISIN": "INE999X09999"},  # non-EQ, excluded
            ])
        result = fetch_isin_snapshot(date(2023, 6, 15), bhavcopy_save=fake_bhavcopy_save)
        self.assertEqual(result, {"HEG": "INE545A01024", "RELIANCE": "INE002A01018"})

    def test_udiff_schema(self):
        def fake_bhavcopy_save(dt, dest, skip_if_present=True):
            return _write_csv(dest, ["TckrSymb", "SctySrs", "ISIN"], [
                {"TckrSymb": "HEGAM", "SctySrs": "EQ", "ISIN": "INE545A01024"},
                {"TckrSymb": "TCS", "SctySrs": "EQ", "ISIN": "INE467B01029"},
            ])
        result = fetch_isin_snapshot(date(2026, 9, 22), bhavcopy_save=fake_bhavcopy_save)
        self.assertEqual(result, {"HEGAM": "INE545A01024", "TCS": "INE467B01029"})

    def test_blank_isin_or_symbol_skipped(self):
        def fake_bhavcopy_save(dt, dest, skip_if_present=True):
            return _write_csv(dest, ["SYMBOL", "SERIES", "ISIN"], [
                {"SYMBOL": "", "SERIES": "EQ", "ISIN": "INE000000000"},
                {"SYMBOL": "NOISIN", "SERIES": "EQ", "ISIN": ""},
            ])
        result = fetch_isin_snapshot(date(2023, 6, 15), bhavcopy_save=fake_bhavcopy_save)
        self.assertEqual(result, {})


class MergeIsinSnapshotsTest(unittest.TestCase):
    def test_later_snapshot_wins_on_conflict(self):
        older = {"HEG": "INE545A01024", "STABLE": "INE111A01011"}
        newer = {"HEG": "INE545A01024", "HEGAM": "INE545A01024"}
        merged = merge_isin_snapshots([older, newer])
        self.assertEqual(merged, {"HEG": "INE545A01024", "STABLE": "INE111A01011", "HEGAM": "INE545A01024"})

    def test_empty_list_returns_empty_map(self):
        self.assertEqual(merge_isin_snapshots([]), {})


class BuildSymbolGroupsTest(unittest.TestCase):
    def test_rename_pair_grouped_together(self):
        isin_map = {"HEG": "INE545A01024", "HEGAM": "INE545A01024", "TCS": "INE467B01029"}
        groups = build_symbol_groups(isin_map)
        self.assertEqual(sorted(groups["HEG"]), ["HEG", "HEGAM"])
        self.assertEqual(sorted(groups["HEGAM"]), ["HEG", "HEGAM"])
        self.assertEqual(groups["TCS"], ["TCS"])

    def test_three_way_rename_chain_grouped_together(self):
        isin_map = {"A": "INE1", "B": "INE1", "C": "INE1"}
        groups = build_symbol_groups(isin_map)
        self.assertEqual(sorted(groups["A"]), ["A", "B", "C"])
        self.assertEqual(sorted(groups["B"]), ["A", "B", "C"])
        self.assertEqual(sorted(groups["C"]), ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
