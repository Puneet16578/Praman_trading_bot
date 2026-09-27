"""Acceptance test 6: a real historical gap through a stop fills at the open, not the stop.
RELIANCE/2023-07-20 (the real Jio Financial demerger day): real open 2580.0, real close 2619.85,
previous close 2841.85 -- a stop at 2700 (between the open and the previous close) is a real gap,
not touched intraday from above.
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.paper.execution import check_stop_on_session

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class GapThroughStopTest(unittest.TestCase):
    def test_real_gap_fills_at_the_open_not_the_stop(self):
        conn = get_live_connection()
        try:
            fill = check_stop_on_session(conn, "RELIANCE", "2023-07-20", stop=2700.0, as_of="2023-07-20")
            self.assertIsNotNone(fill)
            self.assertEqual(fill.kind, "stop_gap")
            self.assertAlmostEqual(fill.price, 2580.0)
            self.assertNotAlmostEqual(fill.price, 2700.0)
        finally:
            conn.close()

    def test_a_stop_only_touched_intraday_fills_at_the_stop_itself(self):
        """Contrast case, the real next session (2023-07-21: open 2609.0, low 2523.6): a stop of
        2550 sits BELOW the real open (no gap) but ABOVE the real low (touched intraday) -- must
        fill at the stop itself, not the open."""
        conn = get_live_connection()
        try:
            fill = check_stop_on_session(conn, "RELIANCE", "2023-07-21", stop=2550.0, as_of="2023-07-21")
            self.assertIsNotNone(fill)
            self.assertEqual(fill.kind, "stop_touch")
            self.assertAlmostEqual(fill.price, 2550.0)
        finally:
            conn.close()

    def test_a_stop_never_reached_produces_no_fill(self):
        conn = get_live_connection()
        try:
            fill = check_stop_on_session(conn, "RELIANCE", "2023-07-20", stop=2000.0, as_of="2023-07-20")
            self.assertIsNone(fill)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
