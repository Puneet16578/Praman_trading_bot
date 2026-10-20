import unittest
from copy import deepcopy
from unittest.mock import Mock

from desk.s1.rehearsal import outcomes_sealed, rehearse
from desk.s1.reader import RealReader, OutcomeReadRefused
from desk.lib.costs import load_active_cost_config
from tests.test_s1_execution import record, dates


class RehearsalTest(unittest.TestCase):
    def test_aliases_and_database_opens_fail(self):
        import sqlite3
        from desk import outcome_firewall
        from desk.t1_outcome import reader as t1_reader
        conn = Mock()
        reader = RealReader(conn, conn, "2024-12-31", authorized=True)
        captured = reader.bar
        with outcomes_sealed():
            for action in (lambda: captured("2024-01-01", "A", "2024-01-02"),
                           lambda: sqlite3.connect(":memory:"),
                           lambda: outcome_firewall.require_outcome_access("2024-01-01"),
                           lambda: t1_reader.read_adverse20(None, None, None)):
                with self.assertRaises(OutcomeReadRefused):
                    action()
        conn.execute.assert_not_called()

    def test_seeded_rehearsal_deterministic_without_real_data(self):
        artifact = dict(records=[record()], calendars={"s1": dates()}, summary={"tercile_boundaries": [2, 3]})
        costs = load_active_cost_config().costs
        a = rehearse(deepcopy(artifact), costs, sensitivities=False)
        b = rehearse(deepcopy(artifact), costs, sensitivities=False)
        self.assertTrue(a["real_reader_block_verified"])
        self.assertEqual(a["real_outcome_reads"], 0)
        self.assertEqual(a["primary"], b["primary"])
        self.assertEqual(a["synthetic_bar_calls"], b["synthetic_bar_calls"])
