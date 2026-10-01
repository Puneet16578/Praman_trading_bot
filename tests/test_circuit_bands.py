"""Real NSE band data, bitemporal visibility, append-only storage, and loss scenarios."""
import json
import contextlib
import io
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from types import SimpleNamespace

from desk.circuit_bands import CircuitBand, band_as_of, ingest_report, parse_report
from desk.lib.schema import init_desk_db
from desk.lib.costs import load_active_cost_config
from desk.lib.rulebook import load_active_rulebook
from desk.replay import get_desk_replay_connection
from desk.risk.officer import compute_stress_loss

FIXTURE = Path(__file__).parent / "fixtures/circuit_bands/nse_20260930_sample.csv"
PROVENANCE = json.loads((FIXTURE.parent / "provenance.json").read_text(encoding="utf-8"))
PUBLISHED = datetime.fromisoformat(PROVENANCE["published_at"])
RECORDED = datetime.fromisoformat("2026-09-30T18:00:00+05:30")


class CircuitBandTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        init_desk_db(self.conn)
        self.content = FIXTURE.read_bytes()

    def ingest(self):
        return ingest_report(self.conn, self.content, report_date="2026-09-30",
                             published_at=PUBLISHED, recorded_at=RECORDED)

    def test_real_five_percent_band_locked_loss_and_largest_stress(self):
        self.ingest()
        band = band_as_of(self.conn, "A2ZINFRA", "2026-09-30")
        real_row = next(row for row in parse_report(self.content) if row["symbol"] == "A2ZINFRA")
        self.assertEqual(band.percent, 5)
        rulebook = load_active_rulebook().rulebook
        with patch("desk.risk.officer.worst_overnight_gap_loss_inr", return_value=0):
            loss = compute_stress_loss(None, "A2ZINFRA", "2026-09-30", 100, 99, 10,
                                       load_active_cost_config().costs, rulebook, circuit_band=band)
        expected = 100 * 10 * real_row["band_pct"] / 100 * rulebook.risk.circuit_lock_days
        self.assertEqual(loss.locked_circuit_loss_inr, expected)
        self.assertEqual(loss.stress_loss_inr, max(expected, loss.planned_loss_component_inr,
                                                 loss.floor_component_inr, loss.worst_gap_component_inr))

    def test_real_derivatives_stock_is_dynamic_not_a_fixed_ten_percent_band(self):
        self.ingest()
        band = band_as_of(self.conn, "RELIANCE", "2026-09-30")
        self.assertEqual(band.kind, "DYNAMIC")
        self.assertIsNone(band.percent)
        self.assertIn("DYNAMIC operating range", band.label())
        with patch("desk.risk.officer.worst_overnight_gap_loss_inr", return_value=0):
            loss = compute_stress_loss(None, "RELIANCE", "2026-09-30", 100, 99, 10,
                                       load_active_cost_config().costs, load_active_rulebook().rulebook,
                                       circuit_band=band)
        self.assertIsNone(loss.locked_circuit_loss_inr)
        self.assertIn("can flex", loss.circuit_band_caveat)

    def test_missing_date_is_unknown_no_backward_or_forward_filling(self):
        self.ingest()
        for day in ("2019-10-01", "2026-09-29", "2026-10-01"):
            self.assertEqual(band_as_of(self.conn, "A2ZINFRA", day).kind, "UNKNOWN")

    def test_later_knowledge_correction_does_not_leak_into_earlier_read(self):
        self.ingest()
        revised = self.content.replace(b",5,", b",10,")
        ingest_report(self.conn, revised, report_date="2026-09-30",
                      published_at=datetime.fromisoformat("2026-10-01T18:00:00+05:30"),
                      recorded_at=datetime.fromisoformat("2026-10-02T00:00:00+05:30"))
        self.assertEqual(band_as_of(self.conn, "A2ZINFRA", "2026-09-30").percent, 5)
        self.assertEqual(band_as_of(self.conn, "A2ZINFRA", "2026-10-02", report_date="2026-09-30").percent, 10)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM circuit_bands").fetchone()[0], 4)

    def test_append_only_and_duplicate_safe(self):
        self.assertEqual(self.ingest(), 2)
        self.assertEqual(self.ingest(), 0)
        for sql in ("UPDATE circuit_bands SET band_pct=20", "DELETE FROM circuit_bands"):
            with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                self.conn.execute(sql)

    def test_forty_percent_band_is_preserved(self):
        rows = parse_report(self.content.replace(b",5,", b",40,"))
        self.assertEqual(next(row["band_pct"] for row in rows if row["symbol"] == "A2ZINFRA"), 40)

    def test_html_nan_duplicate_and_empty_reports_are_refused(self):
        for content in (b"<html>Error</html>", self.content.replace(b",5,", b",nan,"),
                        self.content + self.content.splitlines(keepends=True)[1],
                        self.content.splitlines(keepends=True)[0]):
            with self.subTest(content=content[:40]), self.assertRaises(ValueError):
                parse_report(content)

    def test_later_recorded_at_is_hidden_by_existing_desk_replay_views(self):
        self.ingest()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "desk.sqlite"
            dest = sqlite3.connect(path)
            try:
                self.conn.backup(dest)
            finally:
                dest.close()
            replay = get_desk_replay_connection(path, "2026-09-30T12:00:00+00:00")
            try:
                self.assertEqual(band_as_of(replay, "A2ZINFRA", "2026-09-30").kind, "UNKNOWN")
            finally:
                replay.close()

    def test_cli_zero_share_plan_prints_na_losses_without_crashing(self):
        from desk.cli import cmd_assess
        from desk.gates.engine import AssessmentResult
        self.ingest()
        result = AssessmentResult("VETO", {}, None, position_size=0, stress_loss=None)
        output = io.StringIO()
        with patch("desk.cli.get_live_connection", return_value=Mock()), \
                patch("desk.cli.get_desk_connection", return_value=self.conn), \
                patch("desk.cli.run_assessment", return_value=result), \
                patch("desk.cli.max_recorded_at", return_value="2026-09-30T00:00:00+00:00"), \
                patch("desk.cli.jstore.record_decision", return_value=1), \
                contextlib.redirect_stdout(output):
            cmd_assess(SimpleNamespace(symbol="A2ZINFRA", as_of="2026-09-30", thesis=None))
        self.assertIn("position_size=0.00", output.getvalue())
        self.assertIn("5% fixed", output.getvalue())
        self.assertIn("planned_stop_loss=N/A stress_loss=N/A locked_circuit_loss=N/A", output.getvalue())


if __name__ == "__main__":
    unittest.main()
