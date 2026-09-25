"""Event Browser -- pick a real catalogued event (or search a symbol/date range) and see its full,
live-generated evidence report. Every note/caveat rendered is taken verbatim from EventReport --
nothing here composes new narrative text (CLAUDE.md invariant 12 / this demo's constraint 6)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from demo import ui
from demo.lib import catalogue
from demo.lib.anonymize import build_symbol_map, company_names_for_event, mask_value
from demo.lib.cutoff import DEMO_DATA_CUTOFF, cutoff_as_date, redact_post_cutoff
from demo.lib.store import get_demo_connection
from src.agent.orchestrator import MultiAgentOrchestrator

st.set_page_config(page_title="Event Browser -- Praman demo", layout="wide")
ui.inject_theme()
ui.page_header("\U0001F4C2", "Event Browser", f"Only events on or before {DEMO_DATA_CUTOFF} exist in this demo's own store.")

anonymise = st.session_state.get("anonymise", False)

tab_filter, tab_search = st.tabs(["Filter the catalogue", "Search a symbol / date range"])

selected = None

with tab_filter:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_from = st.date_input("From", value=None, max_value=cutoff_as_date(), key="f_from")
    with col2:
        date_to = st.date_input("To", value=None, max_value=cutoff_as_date(), key="f_to")
    with col3:
        classification = st.selectbox("Classification", [""] + catalogue.known_classifications())
    with col4:
        cap_band = st.selectbox("Cap band", [""] + catalogue.known_cap_bands())

    rows = catalogue.filter_rows(
        event_date_from=str(date_from) if date_from else None,
        event_date_to=str(date_to) if date_to else None,
        classification=classification or None,
        cap_band=cap_band or None,
    )
    st.write(f"{len(rows)} matching events" + (" (showing first 200)" if len(rows) > 200 else ""))
    display_rows = rows[:200]
    if display_rows:
        symbol_map = build_symbol_map([r["symbol"] for r in display_rows]) if anonymise else {}
        options = {
            f"{symbol_map.get(r['symbol'], r['symbol'])} / {r['event_date']} / {r['classification']}": r
            for r in display_rows
        }
        pick = st.selectbox("Pick an event", [""] + list(options.keys()))
        if pick:
            selected = options[pick]

with tab_search:
    sym_query = st.text_input("Symbol (exact, e.g. RELIANCE)").strip().upper()
    if sym_query:
        events = catalogue.symbol_events(sym_query)
        if not events:
            st.info(f"No catalogued events for {sym_query} in this demo's store.")
        else:
            st.write(f"{len(events)} catalogued event(s) for {sym_query}:")
            for r in events:
                st.write(f"- {r['event_date']} -- {r['classification']} ({r['cap_band']})")

        st.markdown("**Check a specific date not in the list above:**")
        check_date = st.date_input("Date to check", value=None, max_value=cutoff_as_date(), key="check_date")
        if check_date:
            check_date_s = str(check_date)
            match = next((r for r in events if r["event_date"] == check_date_s), None)
            if match:
                st.success(f"{sym_query} on {check_date_s} IS catalogued -- select it from the filter tab.")
            else:
                st.warning(f"{sym_query} on {check_date_s} is NOT in this project's event catalogue.")
                conn = get_demo_connection()
                try:
                    from src.bitemporal.guard import read_as_of
                    from src.signals.event_catalogue import build_symbol_history

                    actions = read_as_of(conn, "corporate_actions", DEMO_DATA_CUTOFF, symbol=sym_query)
                    nearby = [a for a in actions if abs(
                        (int(a["event_date"].replace("-", "")) - int(check_date_s.replace("-", "")))
                    ) < 20]
                    if nearby:
                        st.write("Corporate action(s) near this date (why a move here may be excluded, not shown, as a structural break):")
                        for a in nearby:
                            st.write(f"- {a['action_type']} ex-date {a['event_date']}, tier `{a['confidence_tier']}`")
                    else:
                        st.write("No corporate action near this date -- the date may simply not have qualified "
                                 "as a catalogued event (does not clear this project's z-score/volume thresholds).")
                finally:
                    conn.close()

if selected:
    symbol, event_date = selected["symbol"], selected["event_date"]
    st.divider()
    st.subheader(f"Report: {symbol} / {event_date}")

    conn = get_demo_connection()
    try:
        report = MultiAgentOrchestrator().run_for_event(conn, symbol, event_date)
        report_dict = redact_post_cutoff(report.to_dict())

        display_symbol = symbol
        if anonymise:
            label = build_symbol_map([symbol])[symbol]
            names = company_names_for_event(conn, symbol, event_date)
            report_dict = mask_value(report_dict, symbol, label, names)
            display_symbol = label

        title_col, badge_col = st.columns([4, 1])
        with title_col:
            st.markdown(f"### {display_symbol} / {event_date}")
        with badge_col:
            ui.classification_badge(report_dict["classification"])
        st.markdown(f"Disclosure tier: **{report_dict['disclosure_tier']}**")

        for note in report_dict["classification_notes"]:
            st.info(note)

        st.markdown("#### Signals (microstructure)")
        st.json(report_dict["microstructure"])

        st.markdown("#### Disclosure")
        st.json(report_dict["disclosure"])

        st.markdown("#### Surveillance")
        st.json(report_dict["surveillance"])

        if report_dict["gaps"]:
            st.markdown("#### What could not be determined")
            for g in report_dict["gaps"]:
                st.warning(g)

        if report_dict["rejected_claims"]:
            st.markdown("#### Claims rejected by the Adversary (excluded from the evidence above)")
            st.json(report_dict["rejected_claims"])

        with st.expander("Provenance / measured discriminative power / baseline comparison (verbatim, every report)"):
            st.write(report_dict["provenance_note"])
            st.write(report_dict["discriminative_power_note"])
            st.write(report_dict["baseline_comparison_note"])

        st.session_state["last_report_symbol"] = symbol
        st.session_state["last_report_event_date"] = event_date
    finally:
        conn.close()
