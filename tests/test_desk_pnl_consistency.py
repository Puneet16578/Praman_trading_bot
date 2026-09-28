"""Post-STOP-3-plus consistency fix: ONE price/cost treatment for every fill, and ONE P&L function
(desk/risk/officer.py:realized_pnl_inr) for every exit type -- manual close or automatic stop. Before
this fix, only manual closes netted cost into the recorded price; two identical trades could show
different P&L purely depending on which mechanism closed them, and a stop-out looked artificially
cheaper than it really was.
"""
from __future__ import annotations
import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db

from desk.journal import store as jstore
from desk.lib.connection import get_desk_connection
from desk.lib.costs import load_active_cost_config
from desk.lib.store import ProductionStoreMissingError, get_live_connection
from desk.monitor import run_monitor
from desk.paper.close import close_approved_trade
from desk.risk.officer import realized_pnl_inr, round_trip_cost_inr

from tests.desk_fixtures import copy_symbol_rows

_PRODUCTION_STORE_EXISTS = True
try:
    get_live_connection().close()
except ProductionStoreMissingError:
    _PRODUCTION_STORE_EXISTS = False

SCRATCH_PRAMAN_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_pnl_consistency_praman.sqlite"
SCRATCH_DESK_DB = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_pnl_consistency_desk.sqlite"


def _utc(date_str: str, hour: int = 12) -> datetime:
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, hour, tzinfo=timezone.utc)


@unittest.skipUnless(_PRODUCTION_STORE_EXISTS, "Real Praman production store not found.")
class SameTradeManualVsStopProducesIdenticalPnlTest(unittest.TestCase):
    """Test 1: the same trade, closed manually and by a stop, at the same fill price, produces
    identical P&L."""

    def setUp(self):
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()
        prod = get_live_connection()
        self.scratch_praman = get_connection(str(SCRATCH_PRAMAN_DB))
        init_db(self.scratch_praman)
        copy_symbol_rows(prod, self.scratch_praman, "AXISBANK")
        prod.close()
        self.desk_conn = get_desk_connection(SCRATCH_DESK_DB)
        try:
            self.costs = load_active_cost_config().costs
        except Exception as exc:
            self.skipTest(f"Active cost config not loadable: {exc}")
        # Trade A's manual close and trade B's stop-close must use the SAME cost config for the
        # P&L comparison to be meaningful -- `run_monitor` self-loads the active one internally, so
        # this test uses that same active config throughout rather than a separate test fixture.

        rows = self.scratch_praman.execute(
            "SELECT DISTINCT event_date FROM bhavcopy WHERE symbol='AXISBANK' AND event_date > ? ORDER BY event_date LIMIT 1",
            ("2021-10-27",),
        ).fetchall()
        self.d, self.d_plus_1 = "2021-10-27", rows[0]["event_date"]

        self.entry, self.quantity = 750.0, 66.0
        # Trade A -- manually closed below. Trade B is opened later, once trade A's real fill price
        # is known, so its stop can be set to that SAME real price exactly.
        jstore.open_paper_trade(self.desk_conn, trade_id="AXISBANK:100", decision_id=None,
                                 event_date=self.d, price=self.entry, quantity=self.quantity,
                                 stop=1.0, target=10000.0,
                                 buy_cost_inr=round_trip_cost_inr(self.entry, self.quantity, self.costs, "buy"),
                                 cost_config_hash="test-cost-hash")

    def tearDown(self):
        self.scratch_praman.close()
        self.desk_conn.close()
        for p in (SCRATCH_PRAMAN_DB, SCRATCH_DESK_DB):
            if p.exists():
                p.unlink()

    def test_manual_close_and_stop_close_at_the_same_price_give_identical_pnl(self):
        # Trade A: manual close, issued on D -- fills at D+1's real open, at the SAME cost config
        # (the active one) `run_monitor` will use for trade B below.
        result_a = close_approved_trade(self.scratch_praman, self.desk_conn, "AXISBANK:100",
                                         reason="manual exit", costs=self.costs,
                                         cost_config_hash="active", now=_utc(self.d))
        real_price = result_a.price
        self.assertEqual(result_a.event_date, self.d_plus_1)

        # Trade B: an IDENTICAL position, opened with its stop set to that SAME real price exactly
        # -- a real, not fabricated, price coincidence (AXISBANK's own real D+1 open), then closed
        # by running the REAL `desk monitor` stop-check, not a hand-rolled reimplementation of it.
        jstore.open_paper_trade(self.desk_conn, trade_id="AXISBANK:200", decision_id=None,
                                 event_date=self.d, price=self.entry, quantity=self.quantity,
                                 stop=real_price, target=10000.0,
                                 buy_cost_inr=round_trip_cost_inr(self.entry, self.quantity, self.costs, "buy"),
                                 cost_config_hash="active")

        report = run_monitor(self.scratch_praman, self.desk_conn, self.d_plus_1)
        exits = [e for e in report["exits_triggered"] if e["trade_id"] == "AXISBANK:200"]
        self.assertEqual(len(exits), 1, f"Expected trade B's engineered stop to fire: {report}")
        self.assertAlmostEqual(exits[0]["price"], real_price, places=6)

        # Both trades' OPEN/CLOSE rows now exist -- compute P&L via the ONE shared function for each.
        def _pnl(trade_id):
            opened = self.desk_conn.execute(
                "SELECT * FROM paper_trade_events WHERE trade_id = ? AND event_type = 'OPEN'", (trade_id,)
            ).fetchone()
            closed = self.desk_conn.execute(
                "SELECT * FROM paper_trade_events WHERE trade_id = ? AND event_type = 'CLOSE'", (trade_id,)
            ).fetchone()
            return realized_pnl_inr(entry=opened["price"], exit_price=closed["price"], quantity=self.quantity,
                                     buy_cost_inr=opened["buy_cost_inr"], sell_cost_inr=closed["sell_cost_inr"])

        pnl_a, pnl_b = _pnl("AXISBANK:100"), _pnl("AXISBANK:200")
        self.assertAlmostEqual(pnl_a, pnl_b, places=6,
                                msg=f"Manual close P&L ({pnl_a}) must equal stop-close P&L ({pnl_b}) at the same price.")


class RoundTripAtUnchangedPriceLosesExactlyTheConfiguredCostTest(unittest.TestCase):
    """Test 2: a Rs 50,000 round trip at an UNCHANGED price loses exactly the committed config's
    round-trip cost -- the Rs 126.58 already verified in tests/test_desk_cost_round_trip.py."""

    PRICE, QUANTITY = 500.0, 100.0  # turnover = Rs 50,000, matching test_desk_cost_round_trip.py

    def setUp(self):
        try:
            self.costs = load_active_cost_config().costs
        except Exception as exc:
            self.skipTest(f"Active cost config not loadable: {exc}")

    def test_unchanged_price_round_trip_loses_exactly_the_round_trip_cost(self):
        buy_cost = round_trip_cost_inr(self.PRICE, self.QUANTITY, self.costs, "buy")
        sell_cost = round_trip_cost_inr(self.PRICE, self.QUANTITY, self.costs, "sell")
        pnl = realized_pnl_inr(entry=self.PRICE, exit_price=self.PRICE, quantity=self.QUANTITY,
                                buy_cost_inr=buy_cost, sell_cost_inr=sell_cost)
        # Price didn't move, so gross is exactly 0 -- P&L is exactly minus the round-trip cost.
        self.assertAlmostEqual(pnl, -(buy_cost + sell_cost), places=6)
        self.assertAlmostEqual(pnl, -126.5806, places=4)


class NoCodePathWritesACostAdjustedFillPriceTest(unittest.TestCase):
    """Test 3: grep-style guard. The exact bug this fix reverses had a variable named `net_price`
    (a gross price minus a cost, divided by quantity) fed into `price=` at the fill site -- these
    literal patterns must never reappear anywhere under desk/paper/ or desk/monitor.py."""

    FILES = (
        Path(__file__).resolve().parents[1] / "desk" / "paper" / "open.py",
        Path(__file__).resolve().parents[1] / "desk" / "paper" / "close.py",
        Path(__file__).resolve().parents[1] / "desk" / "monitor.py",
        Path(__file__).resolve().parents[1] / "desk" / "journal" / "store.py",
    )
    FORBIDDEN_LITERALS = ("net_price", "adjusted_fill_price", "cost_adjusted_price")
    # A price variable ending in a subtraction of a cost variable, or division by quantity applied
    # to a cost before being subtracted from a price -- the exact shape of the reverted bug.
    FORBIDDEN_PATTERNS = (
        re.compile(r"price\s*=\s*\w*(gross|fill)_price\s*-"),
        re.compile(r"-\s*\(?\s*(sell|buy)_cost_inr\s*/\s*quantity"),
    )

    def test_no_forbidden_cost_adjusted_price_pattern_anywhere(self):
        offenders = []
        for path in self.FILES:
            text = path.read_text(encoding="utf-8")
            for literal in self.FORBIDDEN_LITERALS:
                if literal in text:
                    offenders.append(f"{path.name}: contains {literal!r}")
            for pattern in self.FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    offenders.append(f"{path.name}: matches forbidden pattern {pattern.pattern!r}")
        self.assertEqual(offenders, [], "Cost-adjusted fill price pattern found:\n" + "\n".join(offenders))

    def test_every_recorded_fill_price_assignment_uses_a_raw_price_variable(self):
        """Positive check, not just an absence-of-badness one: every `price=` keyword argument in
        the fill sites is one of the known-raw identifiers computed directly from the store (never
        a cost-derived one)."""
        raw_identifiers = {"fill_price", "gross_price", "stop_fill.price", "price", "adjusted_open"}
        # \b anchors on whole-word "price" so this does NOT also match the tail of an internal
        # assignment like "fill_price = row[...]" (no word boundary between "_" and "p" there).
        assignment_re = re.compile(r"\bprice\s*=\s*([A-Za-z_][A-Za-z0-9_.\[\]\"']*)")
        for path in (Path(__file__).resolve().parents[1] / "desk" / "paper" / "open.py",
                     Path(__file__).resolve().parents[1] / "desk" / "paper" / "close.py"):
            text = path.read_text(encoding="utf-8")
            found = assignment_re.findall(text)
            self.assertTrue(found, f"No price= assignment found in {path.name} -- test itself may be stale.")
            for value in found:
                self.assertIn(value, raw_identifiers,
                               f"{path.name}: price=... assigned from {value!r}, not a known-raw identifier.")


if __name__ == "__main__":
    unittest.main()
