"""Fixture tests for src/mcp/tools.py's authorization gate -- every specialist agent's tool call
must pass through authorize_tool_call()/call_tool(), fail-closed on any of: unregistered tool,
wrong role, not in the task's own allowlist, or exhausted budget."""
from __future__ import annotations
import unittest

from src.agent.budgets import BudgetConfig, BudgetTracker
from src.bitemporal.connection import get_connection, init_db
from src.mcp.tools import (
    ROLE_DISCLOSURE, ROLE_MARKET_MICROSTRUCTURE, authorize_tool_call, call_tool,
)

class AuthorizeToolCallTest(unittest.TestCase):
    def setUp(self):
        self.budget = BudgetTracker(BudgetConfig(max_total_tool_calls=3, max_agent_tool_calls=2))

    def test_unregistered_tool_rejected(self):
        result = authorize_tool_call(role=ROLE_MARKET_MICROSTRUCTURE, tool_name="not_a_real_tool",
                                      task_allowed_tools=[], budget=self.budget)
        self.assertFalse(result.allowed)
        self.assertIn("not a registered tool", result.reason)

    def test_wrong_role_rejected(self):
        result = authorize_tool_call(role=ROLE_DISCLOSURE, tool_name="get_market_microstructure",
                                      task_allowed_tools=[], budget=self.budget)
        self.assertFalse(result.allowed)
        self.assertIn("not authorized", result.reason)

    def test_correct_role_allowed(self):
        result = authorize_tool_call(role=ROLE_MARKET_MICROSTRUCTURE, tool_name="get_market_microstructure",
                                      task_allowed_tools=[], budget=self.budget)
        self.assertTrue(result.allowed)

    def test_not_in_task_allowlist_rejected(self):
        result = authorize_tool_call(role=ROLE_MARKET_MICROSTRUCTURE, tool_name="get_market_microstructure",
                                      task_allowed_tools=["some_other_tool"], budget=self.budget)
        self.assertFalse(result.allowed)
        self.assertIn("not among the tools authorized for this specific task", result.reason)

    def test_per_agent_budget_exhaustion_fails_closed(self):
        self.budget.register_tool_call(ROLE_MARKET_MICROSTRUCTURE)
        self.budget.register_tool_call(ROLE_MARKET_MICROSTRUCTURE)  # now at max_agent_tool_calls=2
        result = authorize_tool_call(role=ROLE_MARKET_MICROSTRUCTURE, tool_name="get_market_microstructure",
                                      task_allowed_tools=[], budget=self.budget)
        self.assertFalse(result.allowed)
        self.assertIn("budget exhausted", result.reason)

    def test_total_budget_exhaustion_fails_closed_even_for_a_fresh_role(self):
        self.budget.register_tool_call(ROLE_MARKET_MICROSTRUCTURE)
        self.budget.register_tool_call(ROLE_DISCLOSURE)
        self.budget.register_tool_call(ROLE_DISCLOSURE)  # total now at max_total_tool_calls=3
        result = authorize_tool_call(role=ROLE_MARKET_MICROSTRUCTURE, tool_name="get_market_microstructure",
                                      task_allowed_tools=[], budget=self.budget)
        self.assertFalse(result.allowed)

class CallToolTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)
        self.budget = BudgetTracker()

    def test_unauthorized_call_raises_permission_error_not_silently_skipped(self):
        with self.assertRaises(PermissionError):
            call_tool(conn=self.conn, role=ROLE_DISCLOSURE, tool_name="get_market_microstructure",
                      task_allowed_tools=[], budget=self.budget, symbol="ABC", event_date="2024-01-01")

    def test_authorized_call_registers_against_budget(self):
        from src.mcp.tools import has_announcement_coverage
        self.assertFalse(self.budget.per_agent_tool_calls.get(ROLE_DISCLOSURE, 0))
        call_tool(conn=self.conn, role=ROLE_DISCLOSURE, tool_name="has_announcement_coverage",
                  task_allowed_tools=["has_announcement_coverage"], budget=self.budget, symbol="ABC")
        self.assertEqual(self.budget.per_agent_tool_calls[ROLE_DISCLOSURE], 1)

if __name__ == "__main__":
    unittest.main()
