"""Fixture tests for current_surveillance_state(). Real-data confirmation (the 4 real
knowledge_date>event_date rows) lives alongside the event-catalogue real-data guard, since this
helper exists specifically because that ordering guarantee does NOT hold for surveillance_flags.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.store import write_facts
from src.signals.surveillance_state import current_surveillance_state, build_surveillance_timeline

def make_flag(symbol, mechanism, action_type, event_date, knowledge_date, from_stage=None, to_stage=None, source_circular="SURV1", details=None):
    return {
        "symbol": symbol, "mechanism": mechanism, "action_type": action_type,
        "from_stage": from_stage, "to_stage": to_stage, "event_date": event_date,
        "knowledge_date": knowledge_date, "source_circular": source_circular, "details": details,
        "source_file": source_circular,
    }

class CurrentSurveillanceStateTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_absent_mechanism_not_in_result(self):
        state = current_surveillance_state(self.conn, "NEVERFLAGGED", "2025-01-01")
        self.assertEqual(state, {})

    def test_entry_then_visible_at_that_stage(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
        ])
        state = current_surveillance_state(self.conn, "ABC", "2024-06-01")
        self.assertEqual(state, {"ASM_LT": "I"})

    def test_exit_maps_to_none_not_absent(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
            make_flag("ABC", "ASM_LT", "EXIT", "2024-02-05", "2024-02-04"),
        ])
        state = current_surveillance_state(self.conn, "ABC", "2024-06-01")
        self.assertEqual(state, {"ASM_LT": None})
        self.assertIn("ASM_LT", state)  # distinct from never having been flagged

    def test_stage_change_updates_stage(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
            make_flag("ABC", "ASM_LT", "STAGE_CHANGE", "2024-02-05", "2024-02-04", from_stage="I", to_stage="II"),
        ])
        self.assertEqual(current_surveillance_state(self.conn, "ABC", "2024-01-10")["ASM_LT"], "I")
        self.assertEqual(current_surveillance_state(self.conn, "ABC", "2024-06-01")["ASM_LT"], "II")

    def test_not_yet_effective_transition_not_shown(self):
        """knowledge_date has passed but event_date (w.e.f.) hasn't yet -- must not show as
        effective early."""
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "GSM", "ENTRY", "2024-03-10", "2024-03-08", to_stage="I"),
        ])
        state = current_surveillance_state(self.conn, "ABC", "2024-03-09")  # after knowledge, before effect
        self.assertEqual(state, {})

    def test_invisible_before_knowledge_date_even_if_event_date_already_passed(self):
        """The inverted-ordering case (event_date < knowledge_date, the real anomaly found in
        production data) -- must stay invisible until knowledge_date regardless of event_date."""
        write_facts(self.conn, "surveillance_flags", [
            make_flag("WEIRD", "GSM", "ENTRY", "2025-02-11", "2026-02-10", to_stage="IV"),
        ])
        self.assertEqual(current_surveillance_state(self.conn, "WEIRD", "2025-06-01"), {})  # after event_date, before knowledge_date
        self.assertEqual(current_surveillance_state(self.conn, "WEIRD", "2026-02-10")["GSM"], "IV")  # visible immediately once known

    def test_independent_mechanisms_tracked_separately(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
            make_flag("ABC", "GSM", "ENTRY", "2024-02-05", "2024-02-04", to_stage="II"),
        ])
        state = current_surveillance_state(self.conn, "ABC", "2024-06-01")
        self.assertEqual(state, {"ASM_LT": "I", "GSM": "II"})

class SurveillanceTimelineTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_no_entries_returns_none(self):
        timeline = build_surveillance_timeline(self.conn, "NEVERFLAGGED")
        self.assertIsNone(timeline.first_entry_after("2024-01-01"))

    def test_entry_finds_first_entry_strictly_after_date(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
        ])
        timeline = build_surveillance_timeline(self.conn, "ABC")
        entry = timeline.first_entry_after("2024-01-01")
        self.assertEqual(entry["event_date"], "2024-01-05")
        self.assertIsNone(timeline.first_entry_after("2024-01-05"))  # not strictly after
        self.assertIsNone(timeline.first_entry_after("2024-06-01"))

    def test_earliest_of_multiple_entries_across_mechanisms(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "GSM", "ENTRY", "2024-03-01", "2024-02-28", to_stage="II"),
            make_flag("ABC", "ASM_ST", "ENTRY", "2024-01-10", "2024-01-09", to_stage="I"),
        ])
        timeline = build_surveillance_timeline(self.conn, "ABC")
        entry = timeline.first_entry_after("2024-01-01")
        self.assertEqual(entry["event_date"], "2024-01-10")
        self.assertEqual(entry["mechanism"], "ASM_ST")

    def test_exit_and_stage_change_rows_excluded_from_entries(self):
        write_facts(self.conn, "surveillance_flags", [
            make_flag("ABC", "ASM_LT", "ENTRY", "2024-01-05", "2024-01-04", to_stage="I"),
            make_flag("ABC", "ASM_LT", "STAGE_CHANGE", "2024-02-05", "2024-02-04", from_stage="I", to_stage="II"),
            make_flag("ABC", "ASM_LT", "EXIT", "2024-03-05", "2024-03-04"),
        ])
        timeline = build_surveillance_timeline(self.conn, "ABC")
        self.assertEqual(len(timeline.entries), 1)
        self.assertEqual(timeline.entries[0]["event_date"], "2024-01-05")

if __name__ == "__main__":
    unittest.main()
