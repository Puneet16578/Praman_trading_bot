import unittest
from copy import deepcopy
from desk.s1.evaluation import evaluate_inputs, sensitivity_inputs, omit_crowded_dates
from desk.s1.sensitivities import VARIANTS
from desk.s1.reader import seal_real_reads, RealReader, OutcomeReadRefused
from desk.lib.costs import load_active_cost_config
from tests.test_s1_execution import record, dates, FakeReader, Bar


class EvaluationTest(unittest.TestCase):
    def test_composition_synthetic_only_and_descriptives_do_not_change_verdict(self):
        cal = dates()
        artifact = dict(records=[record()], calendars={"s1": cal}, summary={"tercile_boundaries": [2, 3]})
        reader = FakeReader({d: Bar(100, 104, 99, 102) for d in cal})
        with seal_real_reads():
            out = evaluate_inputs(artifact, reader, load_active_cost_config().costs,
                                  random_labels=lambda _: -.02)
        self.assertTrue(out["synthetic"])
        self.assertEqual([t["horizon"] for t in out["tests"]], [1, 3])
        self.assertTrue(all(t["verdict"] == "INCONCLUSIVE" for t in out["tests"]))
        self.assertTrue(all(r["net_return"] == -.02 for r in out["records"] if r["status"] == "VALID"))
        self.assertIn("drop_tercile", out["breakdowns"]["unexplained/h1"])

    def test_sensitivity_single_change_primary_unchanged(self):
        r = record()
        r["exclusions"]["unexplained"] = ["unstable_ratio", "active_asm"]
        artifact = {"records": [r]}
        original = deepcopy(artifact)
        got = sensitivity_inputs(artifact, "include_unstable")
        self.assertEqual(got["records"][0]["exclusions"]["unexplained"], ["active_asm"])
        self.assertEqual(artifact, original)
        self.assertEqual(len(VARIANTS), 8)
        with self.assertRaises(ValueError):
            sensitivity_inputs(artifact, "choose_winning_horizon")

    def test_crowded_date_all_ties(self):
        a, b, c = record(), record(day="2024-01-02"), record(day="2025-01-02")
        retained, omitted = omit_crowded_dates([a, b, c])
        self.assertEqual(retained, [])
        self.assertEqual(len(omitted), 3)

    def test_state_reader_sealed_before_loading_panel(self):
        from unittest.mock import Mock
        reader = RealReader(Mock(), Mock(), "2024-12-31", authorized=True)
        with seal_real_reads(), self.assertRaises(OutcomeReadRefused):
            reader.market_states("2024-01-01", "A")

    def test_frozen_filing_variants_keep_18h_primary_unchanged(self):
        from unittest.mock import Mock, patch
        from desk.s1.sensitivities import enrich
        r = record()
        r.update(market=0, peer_status="KNOWN", peer_share=0, previous_close=100, eligible=True,
                 gates=dict(g3=False, g5="PASS", asm=False), limit_g5="PASS")
        artifact = dict(records=[r], calendars={"observed": dates()}, meta={"category_map": {"X": "Material news"}})
        late = dict(seq_id="1", category="X", description="", sort_timestamp=r["day"]+" 18:00:01",
                    knowledge_date=r["day"])
        conn = Mock()
        conn.execute.side_effect = [[late], []]
        before = deepcopy(r["exclusions"])
        with patch("desk.s1.inputs.stream_context", return_value=[(r["day"], {"symbol": "A"}, r)]):
            enrich(conn, artifact, [])
        self.assertEqual(r["exclusions"], before)
        self.assertIn("material", r["sensitivity_exclusions"]["cutoff_2359"]["unexplained"])
        self.assertNotIn("material", r["sensitivity_exclusions"]["lookback_1"]["unexplained"])
