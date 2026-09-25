"""Verifier -- every claim behind the report selected on the Event Browser page, its check
type(s), and result; plus a live "tamper with a claim" demonstration. Tampering happens on a
FRESH, separate in-memory copy of the specialist agents' own claims (dataclasses.replace, never
mutating the claims backing the page-1 report) and nothing is ever written anywhere."""
from __future__ import annotations
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from demo import ui
from demo.lib.anonymize import build_symbol_map, company_names_for_event, mask_value
from demo.lib.cutoff import redact_post_cutoff
from demo.lib.store import get_demo_connection
from src.agent.adversary import AdversaryAgent
from src.agent.budgets import BudgetTracker
from src.agent.orchestrator import MultiAgentOrchestrator
from src.agent.specialists import DisclosureAgent, MarketMicrostructureAgent, SurveillanceAgent

st.set_page_config(page_title="Verifier -- Praman demo", layout="wide")
ui.inject_theme()
ui.page_header("✅", "Verifier", "Every claim behind a report, its verification tier, and result.")

anonymise = st.session_state.get("anonymise", False)
symbol = st.session_state.get("last_report_symbol")
event_date = st.session_state.get("last_report_event_date")

if not symbol:
    st.info("Pick an event on the Event Browser page first.")
    st.stop()

label = build_symbol_map([symbol])[symbol] if anonymise else symbol
st.caption(f"Showing claims for {label} / {event_date}")

conn = get_demo_connection()
try:
    report = MultiAgentOrchestrator().run_for_event(conn, symbol, event_date)
    names = company_names_for_event(conn, symbol, event_date) if anonymise else []

    def render(d):
        return mask_value(redact_post_cutoff(d), symbol, label, names) if anonymise else redact_post_cutoff(d)

    st.markdown("### Accepted claims")
    st.json([render(c) for c in report.accepted_claims])

    if report.rejected_claims:
        st.markdown("### Rejected claims")
        st.json([render(c) for c in report.rejected_claims])

    st.markdown("### Full adversary findings (every check, every claim)")
    st.json([render(f) for f in report.adversary_findings])

    st.divider()
    st.markdown("## Tamper with a claim")
    st.caption("Overrides a claim's displayed value in an in-memory copy only, then re-runs the "
               "real Adversary against it. Nothing is written anywhere.")

    budget = BudgetTracker()
    live_claims = []
    for agent in (MarketMicrostructureAgent(), DisclosureAgent(), SurveillanceAgent()):
        result = agent.run(conn, symbol, event_date, budget)
        live_claims.extend(result.claims)

    numeric_claims = [c for c in live_claims if isinstance(c.cited_value, (int, float)) and not isinstance(c.cited_value, bool)]
    if not numeric_claims:
        st.info("No numeric claim available to tamper with for this event.")
    else:
        options = {c.claim_id.rsplit(":", 1)[-1]: c for c in numeric_claims}
        pick = st.selectbox("Claim to tamper with", list(options.keys()))
        chosen = options[pick]
        st.write(f"Real cited value: `{chosen.cited_value}`")
        fake_value = st.number_input("Override with", value=float(chosen.cited_value) + 1.0)

        if st.button("Tamper and re-verify"):
            tampered = dataclasses.replace(chosen, cited_value=fake_value, verification={})
            accepted, findings = AdversaryAgent().verify([tampered])
            was_accepted = tampered.claim_id in {c.claim_id for c in accepted}
            if was_accepted:
                st.error("Unexpected: the tampered claim was ACCEPTED. This should not happen for a numeric mismatch.")
            else:
                st.success("The Adversary REJECTED the tampered claim, as expected.")
            st.json([dataclasses.asdict(f) for f in findings])
finally:
    conn.close()
