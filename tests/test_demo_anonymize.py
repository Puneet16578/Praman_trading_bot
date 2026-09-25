"""Constraint 6 (anonymise toggle), fully: tickers are not the only identifier -- disclosure text
names the company too. Pure-logic tests always run; the real end-to-end check (AXISBANK 2021-10-27
with the toggle on contains neither the symbol nor the company name anywhere) is guarded on the
demo store existing.
"""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from demo.lib.anonymize import build_symbol_map, extract_company_name, mask_text, mask_value


class BuildSymbolMapTest(unittest.TestCase):
    def test_stable_sorted_assignment(self):
        m = build_symbol_map(["RELIANCE", "AXISBANK", "GSPL"])
        self.assertEqual(m, {"AXISBANK": "STOCK_A", "GSPL": "STOCK_B", "RELIANCE": "STOCK_C"})

    def test_deterministic_across_calls(self):
        self.assertEqual(build_symbol_map(["B", "A"]), build_symbol_map(["A", "B"]))

    def test_beyond_26_symbols_uses_double_letters(self):
        symbols = [f"SYM{i:03d}" for i in range(30)]
        m = build_symbol_map(symbols)
        self.assertEqual(len(set(m.values())), 30)
        self.assertIn("STOCK_AA", m.values())


class ExtractCompanyNameTest(unittest.TestCase):
    def test_real_axisbank_template(self):
        text = "Axis Bank Limited has informed the Exchange regarding 'RE-APPOINTMENT OF AMITABH CHAUDHRY...'"
        self.assertEqual(extract_company_name(text), "Axis Bank Limited")

    def test_submitted_variant(self):
        text = "Axis Bank Limited has submitted to the Exchange, the financial results..."
        self.assertEqual(extract_company_name(text), "Axis Bank Limited")

    def test_non_template_text_returns_none(self):
        text = "Significant movement in price has been observed in Bpl Limited."
        self.assertIsNone(extract_company_name(text))

    def test_empty_returns_none(self):
        self.assertIsNone(extract_company_name(""))
        self.assertIsNone(extract_company_name(None))


class MaskTextTest(unittest.TestCase):
    def test_masks_symbol_case_insensitive(self):
        self.assertEqual(mask_text("axisbank moved 5%", "AXISBANK", "STOCK_A"), "STOCK_A moved 5%")

    def test_masks_company_name_every_occurrence(self):
        text = "Axis Bank Limited has informed the Exchange regarding AXIS BANK LIMITED ( THE BANK )."
        out = mask_text(text, "AXISBANK", "STOCK_A", ["Axis Bank Limited"])
        self.assertNotIn("axis bank", out.lower())
        self.assertIn("STOCK_A", out)

    def test_mask_value_walks_nested_structure(self):
        value = {"claims": [{"text": "AXISBANK reported strong results, Axis Bank Limited said."}]}
        out = mask_value(value, "AXISBANK", "STOCK_A", ["Axis Bank Limited"])
        self.assertNotIn("AXISBANK", out["claims"][0]["text"])
        self.assertNotIn("Axis Bank Limited", out["claims"][0]["text"])


class RealEndToEndAnonymizeTest(unittest.TestCase):
    def test_axisbank_report_fully_anonymised(self):
        from demo.lib import store

        if not store.DEMO_DB_PATH.exists():
            self.skipTest(f"Demo store not found at {store.DEMO_DB_PATH}. Run demo/build_demo_store.py.")

        from demo.lib.anonymize import company_names_for_event
        from src.agent.orchestrator import MultiAgentOrchestrator

        store.patch_reference_data_paths()
        conn = store.get_demo_connection()
        try:
            symbol, event_date = "AXISBANK", "2021-10-27"
            report = MultiAgentOrchestrator().run_for_event(conn, symbol, event_date)
            names = company_names_for_event(conn, symbol, event_date)
            self.assertIn("Axis Bank Limited", names, "Expected the real template name to be extracted.")

            label = build_symbol_map([symbol])[symbol]
            masked = mask_value(report.to_dict(), symbol, label, names)
            serialized = json.dumps(masked).upper()

            self.assertNotIn("AXISBANK", serialized)
            self.assertNotIn("AXIS BANK", serialized)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
