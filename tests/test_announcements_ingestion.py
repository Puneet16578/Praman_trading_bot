"""Phase 7: corporate-announcement cache ingestion. Fixture data shaped exactly like the real
response sampled from the live endpoint (RELIANCE, confirmed field names and a real row) --
network-free.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.ingestion.nse_market_data.announcements import build_announcement_rows, cluster_announcements_into_events, ingest_symbol_announcements

def real_shaped_row(**overrides) -> dict:
    row = {
        "an_dt": "11-Sep-2026 18:18:50", "attFileSize": "234.08 KB",
        "attchmntFile": "https://nsearchives.nseindia.com/corporate/kavinavora_11092026180518_SE_11092026.pdf",
        "attchmntText": "Please note that the Company executives will be participating in the Institutional Investors' Meeting.",
        "bflag": None, "csvName": None, "desc": "Analysts/Institutional Investor Meet/Con. Call Updates",
        "difference": "00:00:01", "dt": "11092026181850", "exchdisstime": "11-Sep-2026 18:18:51",
        "fileSize": "234.08 KB", "hasXbrl": True, "old_new": None, "orgid": None,
        "seq_id": "106779189", "smIndustry": "Refineries", "sm_isin": "INE002A01018",
        "sm_name": "Reliance Industries Limited", "sort_date": "2026-09-11 18:18:50", "symbol": "RELIANCE",
    }
    row.update(overrides)
    return row

class BuildAnnouncementRowsTest(unittest.TestCase):
    def test_real_shaped_row_mapped_correctly(self):
        rows = build_announcement_rows("RELIANCE", [real_shaped_row()], "test.json")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["symbol"], "RELIANCE")
        self.assertEqual(row["event_date"], "2026-09-11")
        self.assertEqual(row["knowledge_date"], "2026-09-11")
        self.assertEqual(row["seq_id"], "106779189")
        self.assertEqual(row["category"], "Analysts/Institutional Investor Meet/Con. Call Updates")
        self.assertIn("Institutional Investors", row["description"])
        self.assertEqual(row["sort_timestamp"], "2026-09-11 18:18:50")

    def test_row_missing_seq_id_skipped_not_fabricated(self):
        rows = build_announcement_rows("RELIANCE", [real_shaped_row(seq_id=None)], "test.json")
        self.assertEqual(rows, [])

    def test_row_missing_sort_date_skipped_not_fabricated(self):
        rows = build_announcement_rows("RELIANCE", [real_shaped_row(sort_date=None)], "test.json")
        self.assertEqual(rows, [])

    def test_multiple_desc_categories_all_kept(self):
        """Unlike corporate_actions.py's bonus/split-only filter, every category is stored."""
        rows = build_announcement_rows("RELIANCE", [
            real_shaped_row(seq_id="1", desc="Bonus"),
            real_shaped_row(seq_id="2", desc="Board Meeting Intimation"),
            real_shaped_row(seq_id="3", desc="Dividend"),
        ], "test.json")
        self.assertEqual({r["category"] for r in rows}, {"Bonus", "Board Meeting Intimation", "Dividend"})

def ann_row(symbol="X", category="Bonus", sort_timestamp="2022-06-18 21:46:26", description=None):
    return {"symbol": symbol, "category": category, "sort_timestamp": sort_timestamp, "description": description}

class ClusterAnnouncementsIntoEventsTest(unittest.TestCase):
    def test_real_shape_nine_row_burst_collapses_to_one_event(self):
        """Real ADANIENT case, 2022-06-18: 9 rows of the same regulatory disclosure category
        within 11 minutes, all with no captured description text -- must collapse to exactly 1
        event (both-blank description is the "no info to distinguish" case, decided by
        category+time alone)."""
        timestamps = ["21:46:26", "21:50:10", "21:50:50", "21:52:10", "21:53:05", "21:54:36", "21:54:45", "21:55:58", "21:57:17"]
        rows = [ann_row(symbol="ADANIENT", category="Disclosure under SEBI Takeover Regulations",
                         sort_timestamp=f"2022-06-18 {t}") for t in timestamps]
        events = cluster_announcements_into_events(rows)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0]), 9)

    def test_kitex_shaped_correction_still_collapses(self):
        """A near-identical correction (KITEX's real "2:2"->"2:1" typo fix, Phase 3) must still
        collapse -- high similarity, same category, close in time."""
        rows = [
            ann_row(sort_timestamp="2020-01-01 10:00:00", description="The Board has approved a Bonus issue in the ratio of 2:2."),
            ann_row(sort_timestamp="2020-01-01 10:00:38", description="The Board has approved a Bonus issue in the ratio of 2:1."),
        ]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 1)

    def test_real_different_reliance_pair_does_not_collapse(self):
        """Real RELIANCE case: two genuinely different investor-meeting notices, same category,
        4 minutes apart -- must NOT collapse (0.883 similarity, below the 0.95 gate) even though
        category+time alone would have merged them."""
        rows = [
            ann_row(category="Analysts/Institutional Investor Meet/Con. Call Updates", sort_timestamp="2023-11-09 22:55:16",
                    description="Please note that the Company executives will be participating in the Institutional Investors' Meeting organised by Morgan Stanley."),
            ann_row(category="Analysts/Institutional Investor Meet/Con. Call Updates", sort_timestamp="2023-11-09 22:59:28",
                    description="Please note that the Company executives will be participating in the Institutional Investors' Meeting- Non-Deal Roadshow."),
        ]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 2)

    def test_both_descriptions_blank_falls_back_to_category_and_time(self):
        rows = [ann_row(sort_timestamp="2022-06-18 10:00:00", description=None),
                ann_row(sort_timestamp="2022-06-18 10:05:00", description="")]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 1)

    def test_gap_just_over_one_hour_stays_two_events(self):
        rows = [ann_row(sort_timestamp="2022-06-18 10:00:00"), ann_row(sort_timestamp="2022-06-18 11:00:01")]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 2)

    def test_gap_exactly_one_hour_collapses_to_one_event(self):
        rows = [ann_row(sort_timestamp="2022-06-18 10:00:00"), ann_row(sort_timestamp="2022-06-18 11:00:00")]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 1)

    def test_different_category_same_day_stays_separate_events(self):
        """A same-day Bonus announcement and a same-day Dividend announcement are two real,
        distinct disclosures -- must NOT collapse even though they're close in time."""
        rows = [ann_row(category="Bonus", sort_timestamp="2022-06-18 10:00:00"),
                ann_row(category="Dividend", sort_timestamp="2022-06-18 10:05:00")]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 2)

    def test_different_symbol_same_category_and_time_stays_separate_events(self):
        rows = [ann_row(symbol="A", sort_timestamp="2022-06-18 10:00:00"),
                ann_row(symbol="B", sort_timestamp="2022-06-18 10:00:00")]
        self.assertEqual(len(cluster_announcements_into_events(rows)), 2)

    def test_row_count_vs_event_count_differ_when_clustered(self):
        rows = [ann_row(sort_timestamp="2022-06-18 10:00:00"), ann_row(sort_timestamp="2022-06-18 10:05:00")]
        events = cluster_announcements_into_events(rows)
        self.assertEqual(sum(len(e) for e in events), len(rows), "every row must still be accounted for")
        self.assertEqual(len(events), 1)
        self.assertNotEqual(len(events), len(rows), "event count must differ from row count when clustered")

class IngestSymbolAnnouncementsTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_writes_through_the_store_and_is_readable_as_of(self):
        result = ingest_symbol_announcements(self.conn, "RELIANCE", [real_shaped_row()], "test.json")
        self.assertEqual(result.inserted, 1)
        rows = read_as_of(self.conn, "corporate_announcements", "2099-01-01", symbol="RELIANCE")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["seq_id"], "106779189")

    def test_idempotent_on_seq_id(self):
        ingest_symbol_announcements(self.conn, "RELIANCE", [real_shaped_row()], "test.json")
        result2 = ingest_symbol_announcements(self.conn, "RELIANCE", [real_shaped_row()], "test.json")
        self.assertEqual(result2.inserted, 0)
        self.assertEqual(result2.skipped_duplicate, 1)

    def test_empty_list_writes_nothing(self):
        result = ingest_symbol_announcements(self.conn, "RELIANCE", [], "test.json")
        self.assertEqual(result.inserted, 0)

if __name__ == "__main__":
    unittest.main()
